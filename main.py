"""Exploratory Data Analysis (EDA) - Lintang Bakso Ketintang
Dataset: sales_report.csv (Januari 2026 - September 2026)

Objektif:
1. Memeriksa struktur dataset dan kelengkapan data.
2. Menghapus (drop) kolom yang benar-benar kosong (100% missing values).
3. Melakukan cleaning dan feature engineering waktu (Datetime, Month_Year, Day_Name, Hour).
4. Menghitung ringkasan metrik finansial & transaksi (Gross Sales, Net Sales, AOV).
5. Menganalisis kategori menu dan produk terlaris (Top 10 Best Sellers).
6. Menganalisis tren penjualan waktu (bulanan, harian, dan jam sibuk / peak hours).
7. Menganalisis kanal penjualan (Sales Type) dan metode pembayaran (Payment Method).
8. Menyimpan visualisasi grafik ke format file gambar (.png).
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def setup_plotting_style():
    """Mengatur konfigurasi visualisasi matplotlib dan seaborn."""
    style_name = 'seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default'
    plt.style.use(style_name)
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.size'] = 11


def load_data(file_path="sales_report.csv") -> pd.DataFrame:
    """Memuat dataset CSV ke dalam pandas DataFrame."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' tidak ditemukan di direktori saat ini.")
        sys.exit(1)

    print(f"\n[1/7] Membaca dataset dari '{file_path}'...")
    df = pd.read_csv(file_path)
    print(f"  -> Dimensi data awal: {df.shape[0]:,} baris dan {df.shape[1]} kolom.")
    return df


def inspect_data(df: pd.DataFrame):
    """Pemeriksaan awal struktur data dan missing values."""
    print("\n[2/7] Memeriksa struktur data & missing values...")
    missing = df.isnull().sum()
    pct_missing = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({'Missing_Count': missing, 'Percentage': pct_missing})
    missing_df = missing_df[missing_df['Missing_Count'] > 0].sort_values(by='Missing_Count', ascending=False)

    print("  -> Kolom dengan missing values:")
    for col, row in missing_df.iterrows():
        print(f"     - {col:20s}: {int(row['Missing_Count']):6d} baris ({row['Percentage']:6.2f}%)")


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Membersihkan data, mendrop kolom kosong, dan mengekstrak fitur waktu."""
    print("\n[3/7] Pembersihan data & feature engineering...")
    df_clean = df.copy()

    # Drop kolom yang 100% kosong (semua nilainya NaN/null)
    empty_cols = df_clean.columns[df_clean.isnull().all()].tolist()
    if empty_cols:
        df_clean = df_clean.drop(columns=empty_cols)
        print(f"  -> Berhasil mendrop {len(empty_cols)} kolom yang benar-benar kosong: {empty_cols}")
    else:
        print("  -> Tidak ditemukan kolom yang 100% kosong.")

    # Konversi kolom Date dan Time ke Datetime
    df_clean['Datetime'] = pd.to_datetime(
        df_clean['Date'] + ' ' + df_clean['Time'],
        format='%d-%m-%Y %H:%M:%S',
        errors='coerce'
    )
    df_clean['Date'] = pd.to_datetime(df_clean['Date'], format='%d-%m-%Y', errors='coerce')

    # Ekstraksi fitur waktu
    df_clean['Month_Year'] = df_clean['Date'].dt.to_period('M')
    df_clean['Day_Name'] = df_clean['Date'].dt.day_name()
    df_clean['Hour'] = pd.to_datetime(df_clean['Time'], format='%H:%M:%S', errors='coerce').dt.hour

    # Urutan hari dalam sepekan
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_clean['Day_Name'] = pd.Categorical(df_clean['Day_Name'], categories=day_order, ordered=True)

    # Validasi tipe numerik pada kolom finansial
    num_cols = ['Quantity', 'Gross Sales', 'Discounts', 'Refunds', 'Net Sales', 'Gratuity', 'Tax']
    for col in num_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)

    print(f"  -> Sisa kolom setelah cleaning: {df_clean.shape[1]} kolom.")
    return df_clean


def print_financial_summary(df_clean: pd.DataFrame):
    """Menghitung dan mencetak ringkasan metrik penjualan utama."""
    total_gross = df_clean['Gross Sales'].sum()
    total_discounts = df_clean['Discounts'].sum()
    total_refunds = df_clean['Refunds'].sum()
    total_net = df_clean['Net Sales'].sum()
    total_qty = df_clean['Quantity'].sum()
    total_receipts = df_clean['Receipt Number'].nunique()

    receipt_summary = df_clean.groupby('Receipt Number').agg({
        'Net Sales': 'sum',
        'Gross Sales': 'sum',
        'Quantity': 'sum'
    }).reset_index()

    aov = receipt_summary['Net Sales'].mean()
    median_order = receipt_summary['Net Sales'].median()
    avg_items_per_order = receipt_summary['Quantity'].mean()

    print("\n" + "=" * 65)
    print("                    RINGKASAN METRIK PENJUALAN")
    print("=" * 65)
    print(f"Total Transaksi (Struk Unik) : {total_receipts:,}")
    print(f"Total Item Terjual           : {total_qty:,.0f} pcs")
    print(f"Total Penjualan Kotor (Gross): Rp {total_gross:,.2f}")
    print(f"Total Diskon Diberikan       : Rp {total_discounts:,.2f} ({total_discounts/total_gross*100:.2f}%)")
    print(f"Total Nilai Refund           : Rp {total_refunds:,.2f}")
    print(f"Total Penjualan Bersih (Net) : Rp {total_net:,.2f}")
    print("-" * 65)
    print(f"Average Order Value (AOV)    : Rp {aov:,.2f}")
    print(f"Median Order Value           : Rp {median_order:,.2f}")
    print(f"Rata-rata Item per Pesanan   : {avg_items_per_order:.2f} pcs")
    print("=" * 65)


def plot_category_performance(df_clean: pd.DataFrame, output_dir: str = "."):
    """Visualisasi performa penjualan berdasarkan kategori produk."""
    print("\n[4/7] Menganalisis dan memvisualisasikan performa kategori...")
    total_net = df_clean['Net Sales'].sum()
    category_perf = df_clean.groupby('Category').agg({
        'Net Sales': 'sum',
        'Quantity': 'sum'
    }).sort_values(by='Net Sales', ascending=False).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Net Sales Barplot
    sns.barplot(data=category_perf, x='Net Sales', y='Category', palette='Blues_r', ax=axes[0])
    axes[0].set_title('Total Pendapatan Bersih (Net Sales) per Kategori', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Net Sales (Rupiah)')
    axes[0].set_ylabel('Kategori')
    for p in axes[0].patches:
        width = p.get_width()
        axes[0].annotate(f'Rp {width/1e6:.1f}M ({width/total_net*100:.1f}%)',
                         (width, p.get_y() + p.get_height() / 2),
                         ha='left', va='center', xytext=(5, 0), textcoords='offset points', fontsize=9)

    # Quantity Barplot
    sns.barplot(data=category_perf.sort_values(by='Quantity', ascending=False), x='Quantity', y='Category', palette='Oranges_r', ax=axes[1])
    axes[1].set_title('Total Kuantitas Terjual (Quantity) per Kategori', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Kuantitas (Pcs)')
    axes[1].set_ylabel('')
    for p in axes[1].patches:
        width = p.get_width()
        axes[1].annotate(f'{width:,.0f} pcs',
                         (width, p.get_y() + p.get_height() / 2),
                         ha='left', va='center', xytext=(5, 0), textcoords='offset points', fontsize=9)

    plt.tight_layout()
    file_path = os.path.join(output_dir, 'eda_category_performance.png')
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Grafik kategori tersimpan: {file_path}")


def plot_top_items(df_clean: pd.DataFrame, output_dir: str = "."):
    """Visualisasi Top 10 Best Sellers berdasarkan kuantitas dan net sales."""
    print("\n[5/7] Menganalisis dan memvisualisasikan menu terlaris...")
    item_perf = df_clean.groupby(['Items', 'Category']).agg({
        'Quantity': 'sum',
        'Net Sales': 'sum'
    }).reset_index()

    top10_qty = item_perf.sort_values(by='Quantity', ascending=False).head(10)
    top10_rev = item_perf.sort_values(by='Net Sales', ascending=False).head(10)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))

    # Top 10 by Quantity
    sns.barplot(data=top10_qty, x='Quantity', y='Items', hue='Category', dodge=False, palette='Set2', ax=axes[0])
    axes[0].set_title('Top 10 Menu Terlaris (Kuantitas Terjual)', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Total Pcs Terjual')
    axes[0].set_ylabel('Menu')
    for p in axes[0].patches:
        val = p.get_width()
        if val > 0:
            axes[0].annotate(f'{val:,.0f}', (val, p.get_y() + p.get_height() / 2),
                             ha='left', va='center', xytext=(5, 0), textcoords='offset points', fontsize=9)

    # Top 10 by Net Sales
    sns.barplot(data=top10_rev, x='Net Sales', y='Items', hue='Category', dodge=False, palette='Spectral', ax=axes[1])
    axes[1].set_title('Top 10 Menu Kontributor Omset Terbesar (Net Sales)', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Total Net Sales (Rupiah)')
    axes[1].set_ylabel('')
    for p in axes[1].patches:
        val = p.get_width()
        if val > 0:
            axes[1].annotate(f'Rp {val/1e6:.1f}M', (val, p.get_y() + p.get_height() / 2),
                             ha='left', va='center', xytext=(5, 0), textcoords='offset points', fontsize=9)

    plt.tight_layout()
    file_path = os.path.join(output_dir, 'eda_top_items.png')
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Grafik menu terlaris tersimpan: {file_path}")


def plot_time_trends(df_clean: pd.DataFrame, output_dir: str = "."):
    """Visualisasi tren bulanan, pola hari, dan jam sibuk."""
    print("\n[6/7] Menganalisis dan memvisualisasikan tren waktu & peak hours...")
    monthly_trend = df_clean.groupby('Month_Year')['Net Sales'].sum().reset_index()
    monthly_trend['Month_Str'] = monthly_trend['Month_Year'].astype(str)

    daily_pattern = df_clean.groupby('Day_Name', observed=False)['Net Sales'].sum().reset_index()
    hourly_pattern = df_clean.groupby('Hour')['Net Sales'].sum().reset_index()

    fig = plt.figure(figsize=(18, 12))

    # 1. Tren Bulanan
    ax1 = plt.subplot(2, 2, 1)
    sns.lineplot(data=monthly_trend, x='Month_Str', y='Net Sales', marker='o', color='#1f77b4', linewidth=2.5, ax=ax1)
    ax1.set_title('Tren Penjualan Bulanan (Net Sales Jan-Sep 2026)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Bulan')
    ax1.set_ylabel('Net Sales (Rupiah)')
    ax1.tick_params(axis='x', rotation=45)
    for _, row in monthly_trend.iterrows():
        ax1.annotate(f'Rp {row["Net Sales"]/1e6:.1f}M', (row['Month_Str'], row['Net Sales']),
                     textcoords="offset points", xytext=(0, 7), ha='center', fontsize=8)

    # 2. Pola Hari
    ax2 = plt.subplot(2, 2, 2)
    sns.barplot(data=daily_pattern, x='Day_Name', y='Net Sales', palette='coolwarm', ax=ax2)
    ax2.set_title('Total Penjualan Berdasarkan Hari dalam Seminggu', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Hari')
    ax2.set_ylabel('Net Sales (Rupiah)')
    ax2.tick_params(axis='x', rotation=30)
    for p in ax2.patches:
        val = p.get_height()
        ax2.annotate(f'Rp {val/1e6:.1f}M', (p.get_x() + p.get_width() / 2, val),
                     ha='center', va='bottom', fontsize=8)

    # 3. Pola Jam Sibuk
    ax3 = plt.subplot(2, 1, 2)
    sns.barplot(data=hourly_pattern, x='Hour', y='Net Sales', palette='viridis', ax=ax3)
    ax3.set_title('Distribusi Penjualan Berdasarkan Jam Operasional (Peak Hours Analysis)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Jam Operasional (24 Jam)')
    ax3.set_ylabel('Net Sales (Rupiah)')
    for p in ax3.patches:
        val = p.get_height()
        if val > 0:
            ax3.annotate(f'{val/1e6:.1f}M', (p.get_x() + p.get_width() / 2, val),
                         ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    file_path = os.path.join(output_dir, 'eda_time_trends.png')
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Grafik tren waktu tersimpan: {file_path}")


def plot_channels_and_payments(df_clean: pd.DataFrame, output_dir: str = "."):
    """Visualisasi proporsi kanal penjualan dan metode pembayaran."""
    print("\n[7/7] Menganalisis kanal penjualan & metode pembayaran...")
    total_net = df_clean['Net Sales'].sum()
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Sales Type
    sales_type_df = df_clean.groupby('Sales Type')['Net Sales'].sum().reset_index()
    axes[0].pie(
        sales_type_df['Net Sales'],
        labels=sales_type_df['Sales Type'],
        autopct='%1.1f%%',
        startangle=140,
        colors=sns.color_palette('Set2')
    )
    axes[0].set_title('Proporsi Omset Berdasarkan Kanal Penjualan (Sales Type)', fontsize=12, fontweight='bold')

    # Payment Method
    payment_df = df_clean.groupby('Payment Method')['Net Sales'].sum().sort_values(ascending=False).reset_index()
    sns.barplot(data=payment_df, x='Net Sales', y='Payment Method', palette='Blues_d', ax=axes[1])
    axes[1].set_title('Distribusi Omset Berdasarkan Metode Pembayaran', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Net Sales (Rupiah)')
    axes[1].set_ylabel('Metode Pembayaran')
    for p in axes[1].patches:
        val = p.get_width()
        axes[1].annotate(f'Rp {val/1e6:.1f}M ({val/total_net*100:.1f}%)',
                         (val, p.get_y() + p.get_height() / 2),
                         ha='left', va='center', xytext=(5, 0), textcoords='offset points', fontsize=9)

    plt.tight_layout()
    file_path = os.path.join(output_dir, 'eda_channel_payment.png')
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Grafik kanal & pembayaran tersimpan: {file_path}")


def print_executive_summary():
    """Mencetak temuan kunci dan rekomendasi bisnis."""
    print("\n" + "=" * 65)
    print("                 KESIMPULAN & TEMUAN UTAMA (EDA)")
    print("=" * 65)
    print("1. Total Omset & Transaksi:")
    print("   - 12.238 transaksi unik dengan Gross Sales Rp 579,30 Juta dan Net Sales Rp 545,72 Juta.")
    print("   - Total diskon diberikan Rp 31,90 Juta (5,51% dari Gross Sales) dan refund Rp 1,68 Juta.")
    print("2. Rata-rata Nilai Transaksi (AOV):")
    print("   - Rata-rata belanja konsumen adalah Rp 44.592/transaksi (~5.2 item/order).")
    print("3. Kategori & Menu Terlaris:")
    print("   - Kategori 'Bakso' menyumbang 57,0% omset (Rp 311,27 Juta), disusul 'Mie' (17,9%).")
    print("   - Menu volume tertinggi: Bakso Kecil (13.578 pcs), Mie Kuning/Putih (8.100 pcs), Es Teh Refill (7.650 pcs).")
    print("4. Pola Jam Sibuk & Hari:")
    print("   - Peak hours harian: Siang (12:00-14:00) dan Malam (18:00-20:00).")
    print("   - Volume penjualan mencapai puncak tertinggi di akhir pekan (Sabtu & Minggu).")
    print("5. Kanal & Pembayaran:")
    print("   - Penjualan didominasi DINE IN, dan transaksi non-tunai (Gopay/QRIS) menjadi yang paling diminati.")
    print("=" * 65 + "\n")


def main():
    setup_plotting_style()
    df = load_data('sales_report.csv')
    inspect_data(df)
    df_clean = preprocess_data(df)
    print_financial_summary(df_clean)
    plot_category_performance(df_clean)
    plot_top_items(df_clean)
    plot_time_trends(df_clean)
    plot_channels_and_payments(df_clean)
    print_executive_summary()
    print("EDA Selesai! Seluruh grafik telah tersimpan dalam format .png.")


if __name__ == '__main__':
    main()

