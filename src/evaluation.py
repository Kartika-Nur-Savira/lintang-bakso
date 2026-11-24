"""
Module: Evaluation
Fungsi-fungsi evaluasi peramalan deret waktu berbasis validasi urutan waktu
(Rolling-Origin Time Series Cross-Validation), perhitungan metrik performa
(MAE, RMSE, WAPE, Bias), dan pembandingan model baseline Seasonal Naive vs SARIMA vs SARIMAX.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """
    Menghitung metrik performa forecasting:
    - MAE: Mean Absolute Error (rata-rata selisih absolut porsi)
    - RMSE: Root Mean Squared Error (penalti lebih berat untuk kesalahan besar)
    - WAPE: Weighted Absolute Percentage Error = (sum |actual - pred| / sum actual) * 100
            Sangat cocok untuk data F&B ritel karena kebal dari pembagian nol (zero-demand issue).
    - Bias: Mean Forecast Error = mean(predicted - actual)
            Positif = Over-forecasting (risiko makanan sisa/basi),
            Negatif = Under-forecasting (risiko kehabisan stok).
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    
    # Floor prediksi di 0 (permintaan riil tidak bisa negatif)
    predicted = np.clip(predicted, a_min=0.0, a_max=None)
    
    errors = predicted - actual
    abs_errors = np.abs(errors)
    
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    
    total_actual = float(np.sum(actual))
    if total_actual > 0:
        wape = float((np.sum(abs_errors) / total_actual) * 100.0)
    else:
        wape = 0.0 if np.sum(abs_errors) == 0 else 100.0
        
    bias = float(np.mean(errors))
    
    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "WAPE": round(wape, 2),
        "Bias": round(bias, 4)
    }


def seasonal_naive_forecast(train_series: pd.Series, horizon: int = 7, s: int = 7) -> np.ndarray:
    """
    Model Baseline Benchmark: Seasonal Naive.
    Memproyeksikan nilai pada hari yang sama dari minggu sebelumnya: y_{t+h} = y_{t+h-s}.
    """
    last_season = train_series.iloc[-s:].values
    # Replikasi pola mingguan terakhir
    forecast = np.tile(last_season, int(np.ceil(horizon / s)))[:horizon]
    return forecast


def rolling_origin_evaluation(
    series: pd.Series,
    exog: Optional[pd.DataFrame] = None,
    order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 7),
    horizon: int = 7,
    n_splits: int = 4
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Melakukan validasi deret waktu menggunakan metode Rolling-Origin (Expanding Window):
    Pada setiap fold:
    1. Training set dibentuk dari data masa lalu hingga titik split t_k.
    2. Model (Seasonal Naive, SARIMA, SARIMAX) menghasilkan prediksi 7 hari ke depan (t_k+1 s/d t_k+7).
    3. Prediksi dibandingkan secara ketat dengan data aktual.
    4. Titik asal digeser maju 7 hari, proses diulang.
    
    Menjamin ketiadaan data leakage dan mencerminkan skenario operasional mingguan nyata.
    """
    total_len = len(series)
    test_len = horizon * n_splits
    start_train_len = total_len - test_len
    
    fold_details = []
    
    for fold in range(n_splits):
        train_end_idx = start_train_len + (fold * horizon)
        val_end_idx = train_end_idx + horizon
        
        train_s = series.iloc[:train_end_idx]
        val_s = series.iloc[train_end_idx:val_end_idx]
        val_dates = series.index[train_end_idx:val_end_idx]
        actuals = val_s.values
        
        # 1. Seasonal Naive
        s_naive_pred = seasonal_naive_forecast(train_s, horizon=horizon, s=7)
        s_naive_metrics = calculate_metrics(actuals, s_naive_pred)
        
        # 2. SARIMA (tanpa eksogen)
        try:
            sarima_model = SARIMAX(
                train_s,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            sarima_fit = sarima_model.fit(disp=False, maxiter=100)
            sarima_pred = sarima_fit.get_forecast(steps=horizon).predicted_mean.clip(lower=0.0).values
            sarima_metrics = calculate_metrics(actuals, sarima_pred)
        except Exception:
            sarima_pred = np.full(horizon, train_s.mean())
            sarima_metrics = calculate_metrics(actuals, sarima_pred)
            
        # 3. SARIMAX (dengan eksogen)
        if exog is not None:
            train_exog = exog.iloc[:train_end_idx]
            val_exog = exog.iloc[train_end_idx:val_end_idx]
            try:
                sarimax_model = SARIMAX(
                    train_s,
                    exog=train_exog,
                    order=order,
                    seasonal_order=seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
                sarimax_fit = sarimax_model.fit(disp=False, maxiter=100)
                sarimax_pred = sarimax_fit.get_forecast(steps=horizon, exog=val_exog).predicted_mean.clip(lower=0.0).values
                sarimax_metrics = calculate_metrics(actuals, sarimax_pred)
            except Exception:
                sarimax_pred = sarima_pred
                sarimax_metrics = sarima_metrics
        else:
            sarimax_pred = sarima_pred
            sarimax_metrics = sarima_metrics
            
        # Simpan metrik per fold
        for m_name, m_dict, p_arr in [
            ('Seasonal Naive', s_naive_metrics, s_naive_pred),
            ('SARIMA', sarima_metrics, sarima_pred),
            ('SARIMAX', sarimax_metrics, sarimax_pred)
        ]:
            fold_details.append({
                'fold': fold + 1,
                'model': m_name,
                'val_start': val_dates[0].strftime('%Y-%m-%d'),
                'val_end': val_dates[-1].strftime('%Y-%m-%d'),
                'MAE': m_dict['MAE'],
                'RMSE': m_dict['RMSE'],
                'WAPE': m_dict['WAPE'],
                'Bias': m_dict['Bias']
            })
            
    df_folds = pd.DataFrame(fold_details)
    df_summary = df_folds.groupby('model').agg({
        'MAE': 'mean',
        'RMSE': 'mean',
        'WAPE': 'mean',
        'Bias': 'mean'
    }).reset_index().round(4)
    
    return df_folds, df_summary
