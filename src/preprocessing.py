"""
Module: Preprocessing
Fungsi-fungsi persiapan data, pembersihan, penanganan hari tutup,
ekstraksi fitur eksogen, dan segmentasi produk untuk forecasting permintaan harian.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List, Optional


def load_raw_data(filepath: str = "data/daily_item_demand.csv") -> pd.DataFrame:
    """
    Memuat dataset harian item demand dan memastikan tipe data sesuai standar.
    """
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    return df


def inspect_dataset_health(df: pd.DataFrame) -> Dict:
    """
    Memeriksa kesehatan dataset: dimensi, kelengkapan tanggal, missing values,
    dan hari ketika toko tutup.
    """
    min_date = df['date'].min()
    max_date = df['date'].max()
    expected_days = (max_date - min_date).days + 1
    actual_days = df['date'].nunique()
    
    closed_dates = df[df['is_open'] == False]['date'].drop_duplicates().sort_values().tolist()
    
    missing_by_col = df.isnull().sum().to_dict()
    duplicates_count = df.duplicated(subset=['date', 'item_name']).sum()
    
    return {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "n_items": df['item_name'].nunique(),
        "min_date": min_date.strftime("%Y-%m-%d"),
        "max_date": max_date.strftime("%Y-%m-%d"),
        "expected_days": expected_days,
        "actual_days": actual_days,
        "is_continuous": expected_days == actual_days,
        "closed_dates": [d.strftime("%Y-%m-%d") for d in closed_dates],
        "closed_count": len(closed_dates),
        "duplicates": duplicates_count,
        "missing_values": missing_by_col
    }


def categorize_demand_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mengelompokkan 69 produk ke dalam 4 kuadran permintaan:
    1. High Demand: Rata-rata penjualan harian > 10 porsi / hari
    2. Medium Demand: Rata-rata 1.0 - 10.0 porsi / hari
    3. Low Demand: Rata-rata < 1.0 porsi / hari (tetapi bukan sparse)
    4. Sparse / Intermittent: Ditandai is_sparse_item=True atau zero demand > 90%
    """
    df_open = df[df['is_open'] == True]
    
    stats = df_open.groupby(['item_name', 'category']).agg(
        total_payment_qty=('qty_payment', 'sum'),
        mean_daily_qty=('qty_payment', 'mean'),
        median_daily_qty=('qty_payment', 'median'),
        std_daily_qty=('qty_payment', 'std'),
        max_daily_qty=('qty_payment', 'max'),
        zero_pct=('qty_payment', lambda x: (x == 0).mean() * 100),
        is_sparse_flag=('is_sparse_item', 'first')
    ).reset_index()
    
    def assign_tier(row):
        if row['is_sparse_flag'] or row['zero_pct'] >= 90.0:
            return 'Sparse Demand'
        elif row['mean_daily_qty'] >= 10.0:
            return 'High Demand'
        elif row['mean_daily_qty'] >= 1.0:
            return 'Medium Demand'
        else:
            return 'Low Demand'
            
    stats['demand_tier'] = stats.apply(assign_tier, axis=1)
    stats = stats.sort_values('total_payment_qty', ascending=False).reset_index(drop=True)
    return stats


def prepare_item_series(
    df: pd.DataFrame, 
    item_name: str, 
    target_col: str = 'qty_payment',
    closed_handling: str = 'day_of_week_median'
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Mengekstrak series target dan matriks fitur eksogen untuk 1 produk spesifik.
    
    Metodologi Penanganan Hari Toko Tutup (is_open == False):
    - Pada hari toko tutup, tidak ada aktivitas penjualan. Permintaan riil pelanggan tidak teramati.
    - Untuk algoritma SARIMAX yang mensyaratkan time series kontinu beraturan tanpa NaN:
      1. Jika closed_handling == 'day_of_week_median': Mengimputasi nilai NaN dengan median
         hari yang sama (misal median hari Minggu untuk tanggal tutup Minggu), sehingga tidak
         merusak pola musiman mingguan (s=7).
      2. Jika closed_handling == 'zero': Mengisi dengan 0 (namun ini dapat memicu bias struktural).
      3. Jika closed_handling == 'linear': Interpolasi linier antara hari sebelum dan sesudah.
      
    Fitur Eksogen:
    - is_weekend (biner 0/1)
    - day_name one-hot encoding (Senin - Sabtu, Minggu sebagai acuan referensi untuk mencegah multicollinearity)
    - is_open (biner 1/0)
    """
    item_df = df[df['item_name'] == item_name].copy()
    item_df = item_df.sort_values('date').set_index('date')
    
    # Target series
    target_series = item_df[target_col].copy()
    
    # Tangani hari tutup jika ada nilai NaN
    if target_series.isnull().any():
        if closed_handling == 'day_of_week_median':
            item_df['dow'] = item_df.index.dayofweek
            dow_medians = item_df[item_df['is_open'] == True].groupby('dow')[target_col].median()
            for idx in target_series[target_series.isnull()].index:
                d = idx.dayofweek
                med_val = dow_medians.get(d, 0.0)
                target_series.loc[idx] = med_val
        elif closed_handling == 'linear':
            target_series = target_series.interpolate(method='time').bfill().ffill()
        elif closed_handling == 'zero':
            target_series = target_series.fillna(0.0)
            
    # Pastikan frekuensi harian eksplisit
    target_series = target_series.asfreq('D')
    
    # Matriks Fitur Eksogen
    exog_df = pd.DataFrame(index=item_df.index)
    exog_df['is_weekend'] = item_df['is_weekend'].astype(int)
    exog_df['is_open'] = item_df['is_open'].astype(int)
    
    # One-hot dummy untuk hari dalam seminggu (drop_first=True untuk mencegah dummy variable trap)
    day_dummies = pd.get_dummies(item_df['day_name'], prefix='day', drop_first=True, dtype=int)
    exog_df = pd.concat([exog_df, day_dummies], axis=1)
    exog_df = exog_df.asfreq('D')
    
    return target_series, exog_df


def generate_future_exog(last_date: pd.Timestamp, horizon: int = 7) -> pd.DataFrame:
    """
    Menghasilkan matriks fitur eksogen untuk horizon prediksi 7 hari ke depan.
    Seluruh fitur ini adalah kalender pasti (known future events), bebas dari data leakage.
    Asumsi: Selama 7 hari ke depan, toko beroperasi normal (is_open = 1).
    """
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon, freq='D')
    future_df = pd.DataFrame(index=future_dates)
    future_df['day_name'] = future_dates.day_name()
    future_df['is_weekend'] = future_dates.dayofweek.isin([5, 6]).astype(int)
    future_df['is_open'] = 1  # Operasional normal ke depan
    
    # One-hot encoding yang identik dengan exog_df historis
    # Kolom hari: Monday, Saturday, Sunday, Thursday, Tuesday, Wednesday (drop_first=Friday)
    # Kita buat dummy eksplisit agar kolom konsisten
    days = ['Monday', 'Saturday', 'Sunday', 'Thursday', 'Tuesday', 'Wednesday']
    for d in days:
        future_df[f'day_{d}'] = (future_df['day_name'] == d).astype(int)
        
    cols_to_keep = ['is_weekend', 'is_open'] + [f'day_{d}' for d in days if f'day_{d}' in future_df.columns]
    return future_df[cols_to_keep]
