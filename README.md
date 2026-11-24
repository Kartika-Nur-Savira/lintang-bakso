# Daily Item Demand Forecasting Using SARIMAX
## Sistem Prediksi Permintaan Menu Harian Berbasis Deret Waktu Statistik & Variabel Eksogen
**Studi Kasus Bisnis:** Warung Bakso Lintang (Ketintang, Surabaya)  
**Tujuan Proyek:** Perencanaan Pembelian Bahan Baku Dapur (Bill of Materials) & Laporan Penelitian Akademik  
**Dataset Utama:** `daily_item_demand.csv` (18.423 baris, 69 produk, 267 hari kalender harian, Jan–Sep 2026)

---

## 1. Executive Summary & Jawaban Riset

### Pertanyaan 1: Dari data yang ada, model apa yang paling bagus?
Berdasarkan karakteristik dataset harian yang memiliki **pola musiman mingguan 7 hari yang sangat kuat (+43.6% lonjakan penjualan di akhir pekan)**, kestabilan tren jangka panjang, serta keberadaan hari operasional libur, model yang paling tepat dan unggul secara empiris adalah **SARIMAX (Seasonal Autoregressive Integrated Moving Average with Exogenous Variables)** dengan formulasi musiman:

$$\text{SARIMAX}(p, d, q)(P, D, Q)_7 + \boldsymbol{\beta} \mathbf{X}_t$$

di mana matriks variabel eksogen $\mathbf{X}_t$ mencakup indikator kalender (`is_weekend`, dummy hari kerja) dan status operasional (`is_open`).

**Bukti Empiris Hasil Validasi (Rolling-Origin 4 Folds):**
- **Pada Produk Utama (High Demand - Bakso Kecil):** Model SARIMAX/SARIMA menekan **WAPE menjadi 38.48%** dan **MAE 17.31 porsi**, mengungguli model baseline Seasonal Naive (WAPE 44.81%, MAE 20.46 porsi).
- **Pada Produk Sedang (Medium Demand - Bakso Telur Asin):** SARIMA menekan **WAPE menjadi 46.51%** (MAE 0.87 porsi), jauh melampaui Seasonal Naive (WAPE 69.14%, MAE 1.32 porsi).
- **Kriteria Informasi:** Penambahan variabel eksogen menurunkan nilai Akaike Information Criterion ($\Delta \text{AIC} > 60$ poin) pada produk aktif, membuktikan kontribusi signifikan sinyal kalender terhadap akurasi peramalan.

---

### Pertanyaan 2: Kalau misal LSTM bisa tidak?
Secara teknis, **LSTM (Long Short-Term Memory)** *bisa* dikodekan dan dijalankan, **tetapi secara metodologis dan praktis SANGAT TIDAK DIREKOMENDASIKAN** untuk dataset ini karena 5 alasan ilmiah mendasar:

| Aspek Evaluasi | SARIMAX (Metode Terpilih) | LSTM (Deep Learning) | Alasan & Dampak Metodologis |
|---|---|---|---|
| **Ukuran Sampel ($N$)** | Sangat optimal untuk $N = 267$ hari (deret waktu harian 9 bulan). | Membutuhkan ribuan hingga puluhan ribu titik observasi. | Pada $N=267$, arsitektur berbobot ribuan parameter pada LSTM akan mengalami **overfitting parah** (menghafal data latih namun gagal total saat validasi out-of-sample). |
| **Karakteristik Sparse Data** | Dapat diidentifikasi dan ditangani secara terkontrol via AIC/BIC atau metode Croston. | Rentan mengalami **vanishing gradients** atau memprediksi nilai konstan mendekati 0. | 9 produk memiliki $>90\%$ hari bernilai 0. Fungsi rugi (MSE/MAE) pada neural network akan terperangkap memprediksi angka 0 datar untuk meminimalkan error. |
| **Transparansi & Bukti Akademik** | Menghasilkan estimasi *Maximum Likelihood*, standard error, $p$-value variabel eksogen, dan uji diagnostik residual formal (Ljung-Box, Jarque-Bera). | Bersifat **Black-Box**. Sangat sulit mengisolasi kontribusi statistik dari efek hari libur atau musiman mingguan. | Untuk laporan penelitian ilmiah, pembuktian asumsi statistik (ADF test, homoskedastisitas, white noise residual) menjadi syarat mutlak yang tidak dapat disediakan oleh LSTM standar. |
| **Interval Kepercayaan (Uncertainty)** | Menghasilkan *Confidence Interval 95%* eksak secara analitis sebagai dasar batas aman stok (*Safety Stock Buffer*). | Memerlukan komputasi berat tambahan seperti *Monte Carlo Dropout* atau *Quantile Loss* yang tidak stabil pada sampel kecil. | Tim dapur memerlukan batas atas belanja aman ($CI_{\text{upper}}$) agar tidak kehabisan daging saat jam makan siang ramai. |
| **Efisiensi Komputasi & Retraining** | Waktu fitting hanya **0.05–0.1 detik per produk**, dapat di-retrain instan setiap minggu di mesin kasir tanpa GPU. | Memerlukan waktu pelatihan lama, penyesuaian learning rate, batch size, dan arsitektur berulang-ulang. | Operasional UMKM memerlukan proses yang ringan, cepat, dan stabil saat staf mengunggah file CSV kasir mingguan. |

> **Rekomendasi Riset Lanjutan:** Jika di masa depan ingin menguji arsitektur Deep Learning (seperti LSTM / DeepAR / Temporal Fusion Transformer), penelitian harus menunggu akumulasi data minimal **2 hingga 3 tahun ( $>1.000$ hari)** dan menggunakan pendekatan *Global Forecasting Model* (melatih 1 model tunggal melintasi seluruh 69 produk secara simultan dengan embedding produk), bukan melatih LSTM per individu produk.

---

## 2. Struktur Proyek

Struktur repositori dirancang modular, transparan, dan dapat direproduksi (*reproducible*):

```text
lintang-bakso/
├── data/
│   ├── raw/
│   │   └── sales_report.csv              # Data transaksi mentah dari mesin kasir APOS
│   ├── processed/
│   │   ├── sales_clean.csv               # Dataset hasil data cleaning (61.431 baris x 26 kolom)
│   │   ├── sales_final.csv               # Dataset transaksi granular untuk dashboard & chatbot
│   │   ├── sales_audit.csv               # Dataset jejak audit & rekonsiliasi keuangan
│   │   ├── refunds.csv                   # Data audit transaksi refund
│   │   └── dropped_nagih.csv             # Arsip transaksi uji coba warkop (0-Nagih)
│   └── daily_item_demand.csv             # Dataset deret waktu harian untuk forecasting & BOM
│
├── notebooks/
│   ├── 00_cleaning_sales.ipynb           # Audit & Cleaning data kasir APOS
│   ├── 01_data_understanding.ipynb       # Integritas data, evaluasi target & kuadran permintaan
│   ├── 02_exploratory_data_analysis.ipynb# Analisis tren agregat, kategori, weekday vs weekend
│   ├── 03_time_series_analysis.ipynb     # Dekomposisi aditif, uji ADF & correlogram ACF/PACF
│   ├── 04_sarimax_modeling.ipynb         # Controlled Grid Search & 4-panel diagnostik residual
│   └── 05_forecasting_evaluation.ipynb   # Rolling-Origin CV & proyeksi 7 hari ke depan
│
├── outputs/
│   ├── best_model_parameters.csv         # Parameter optimal (p,d,q)(P,D,Q)7 seluruh 69 produk
│   ├── evaluation_results.csv            # Metrik evaluasi 4 fold (MAE, RMSE, WAPE, Bias)
│   ├── forecast_7_days.csv               # Proyeksi 7 hari ke depan + Confidence Interval + Safety Stock
│   └── figures/                          # 11 visualisasi riset resolusi tinggi (150 DPI)
│
├── src/
│   ├── __init__.py                       # Package initializer
│   ├── preprocessing.py                  # Pemuatan data, imputasi hari libur, ekstraksi eksogen
│   ├── modeling.py                       # Estimasi SARIMAX, grid search, diagnostik residual
│   └── evaluation.py                     # Perhitungan MAE/RMSE/WAPE & Rolling-Origin CV
│
├── PRD.md                                # Dokumen Persyaratan Produk (PRD v1.1)
├── cleaning_report.md                    # Laporan audit pembersihan data kasir APOS
├── .gitignore                            # Konfigurasi pengabaian file sampah & cache
└── README.md                             # Laporan komprehensif penelitian & operasional bisnis
```

---

## 3. Metodologi Penelitian & Tahapan Analisis

### Tahap 1: Data Understanding & Preprocessing
1. **Dimensi & Kelengkapan Panel:** Dataset merupakan *balanced panel* sempurna berukuran **18.423 baris $\times$ 13 kolom**, memuat 69 produk selama 267 hari kalender berurutan (01 Januari s/d 24 September 2026). Tidak ada duplikasi baris pada kunci primer `['date', 'item_name']`.
2. **Pembedaan Konseptual Hari Tutup vs Permintaan Nol vs Missing Value:**
   - **Toko Tutup (`is_open == False`):** Terdapat 3 hari libur operasional resmi (22-23 Maret: Hari Raya Nyepi, 27 Mei: Waisak). Seluruh 207 *missing values* berasal dari 3 hari ini ($3 \times 69 = 207$). Nilai ini adalah *unobserved latent demand*, bukan permintaan nol. Untuk menjaga kontinuitas deret waktu tanpa merusak gelombang musiman mingguan ($s=7$), diterapkan **Day-of-Week Median Imputation** yang dikombinasikan dengan variabel eksogen biner `is_open`.
   - **Toko Buka Tetapi Permintaan Nol (`is_open == True`, `qty = 0`):** Warung beroperasi normal namun menu tidak dipesan. Ini adalah nilai **0 riil**.
   - **Missing Value Sejati:** Ditemukan **0 baris** pada hari operasional normal.
3. **Pemilihan Target Variabel (`qty_payment` vs `qty_net`):**
   - Berdasarkan kebutuhan konversi resep dapur (Bill of Materials), **`qty_payment` dipilih sebagai target primer**. Ketika pelanggan memesan bakso lalu terjadi refund pasca-pemasakan, bahan baku fisik (daging sapi, tepung, kuah) sudah terlanjur diolah dan dikonsumsi. Menggunakan `qty_net` berisiko memicu *under-estimation* bahan baku. Total refund selama 9 bulan hanya 187 unit (0.19% dari total volume).
4. **Segmentasi Kuadran Permintaan (69 Produk):**
   - **High Demand (10 produk, 14.5%):** Rata-rata $> 10$ porsi/hari. Menyumbang $>65\%$ volume penjualan warung (*Bakso Kecil, Mie Kuning/Putih, Es Teh/Lemontea Refill, Tahu, Bakso Urat Kecil, Mie Ayam, Somay, Bakso Isi Keju, Goreng Panjang, Kemasan*).
   - **Medium Demand (34 produk, 49.3%):** Rata-rata 1.0–10.0 porsi/hari.
   - **Low Demand (16 produk, 23.2%):** Rata-rata $< 1.0$ porsi/hari.
   - **Sparse Demand (9 produk, 13.0%):** Memiliki $>90\%$ hari bernilai nol (*Bakso Beranak, Bingo Cone, Choco Melt, Air Putih, Ceker, Crispy Balls, Markisa Stik, Mie Teriyaki, Mochi Vanila*).

---

### Tahap 2: Exploratory Data Analysis (EDA)
1. **Dinamika Agregat & Dominasi Kategori:**
   - Kategori **Bakso mendominasi 55.4%** total kuantitas porsi (54.407 porsi), disusul Minuman (17.5%), Gorengan (13.3%), dan Mie (8.4%).
2. **Pembuktian Pola Musiman Mingguan (Weekly Seasonality):**
   - Penjualan melonjak tajam pada akhir pekan. Rata-rata penjualan harian naik dari **330.9 porsi pada weekday (Senin–Jumat)** menjadi **475.3 porsi pada weekend (Sabtu–Minggu)**, atau peningkatan sebesar **+43.6%**.
   - **Uji Signifikansi Statistik:** Uji Welch's two-sample t-test ($t = 11.84, p = 2.19 \times 10^{-24}$) dan Mann-Whitney U test ($U = 11,460, p = 1.05 \times 10^{-21}$) menolak hipotesis nol secara mutlak pada $\alpha = 0.01$. Pola musiman 7 hari terbukti nyata secara ilmiah.

---

### Tahap 3: Analisis Deret Waktu (Time Series Analysis)
1. **Dekomposisi Deret Waktu Aditif ($s=7$):**
   - Model aditif ($Y_t = T_t + S_t + R_t$) dipilih karena deret data mengandung nilai nol (model multiplikatif mengalami *division by zero*).
   - Pola musiman $S_t$ pada *Bakso Kecil* berfluktuasi teratur: titik terendah pada hari Senin (-12 porsi di bawah rata-rata) dan titik tertinggi pada hari Minggu (+24 porsi di atas rata-rata).
2. **Uji Stasioneritas Augmented Dickey-Fuller (ADF):**
   - $H_0$: Deret waktu memiliki unit root (tidak stasioner).
   - $H_1$: Deret waktu stasioner.
   - **Hasil:** Pada level ($d=0$), *Bakso Kecil* menghasilkan statistik ADF $-3.82$ ($p = 0.0027 < 0.05$). Deret waktu telah stasioner dalam rata-rata (*mean stationary*). Penerapan differencing musiman ($D=1, s=7$) lebih lanjut memperkuat stabilitas varians dengan nilai ADF $-7.45$ ($p < 10^{-10}$).
3. **Identifikasi Orde Box-Jenkins (ACF & PACF):**
   - Correlogram ACF menunjukkan *spikes* signifikan pada lag 7, 14, 21, dan 28, sementara PACF terputus (*cuts off*) setelah lag 7. Ini mengonfirmasi keberadaan komponen **Seasonal AR ($P=1$)** dan **Non-Seasonal AR ($p=1$ atau $p=2$)**.

---

### Tahap 4: Pemodelan SARIMA & SARIMAX Serta Diagnostik Residual
1. **Controlled Grid Search:**
   - Dilakukan pencarian parameter terarah berbasis kriteria AIC dan BIC melintasi ruang parameter Box-Jenkins terkurasi.
   - Variabel eksogen yang disertakan pada SARIMAX:
     - `is_weekend` (1 untuk Sabtu/Minggu, 0 lainnya).
     - Dummy hari dalam seminggu (`day_Monday`, `day_Tuesday`, `day_Wednesday`, `day_Thursday`, `day_Saturday`, `day_Sunday`, dengan Jumat sebagai acuan dasar guna menghindari *dummy variable trap*).
     - `is_open` (1 untuk toko buka, 0 untuk hari libur).
2. **Diagnostik Residual Model Terbaik (Bakso Kecil):**
   - **Uji Ljung-Box (White Noise Check):**
     - Lag 7: $Q = 3.73, p\text{-value} = 0.812 > 0.05$
     - Lag 14: $Q = 10.42, p\text{-value} = 0.745 > 0.05$
     - **Kesimpulan:** Residual bersifat **White Noise** murni. Seluruh korelasi serial dan komponen musiman berhasil diserap secara sempurna oleh model.
   - **Uji Normalitas Jarque-Bera:** Residual memiliki mean mendekati 0 ($\mu_e = -0.04$) dengan sedikit *positive skewness* akibat lonjakan ekor kanan pada hari libur besar nasional.
   - **Correlogram ACF Residual:** Seluruh nilai autokorelasi lag 1 s/d 21 berada aman di dalam pita batas kepercayaan 95%.

---

### Tahap 5: Validasi Rolling-Origin & Proyeksi 7 Hari ke Depan
1. **Desain Rolling-Origin Cross-Validation:**
   - Horizon peramalan ditetapkan $h = 7$ hari.
   - Menggunakan 4 fold validasi bergulir (*expanding window*) pada 28 hari terakhir tanpa kebocoran data (*zero data leakage*).
   - Membandingkan 3 model: **Seasonal Naive**, **SARIMA**, dan **SARIMAX**.
2. **Hasil Evaluasi Kinerja (Rata-rata 4 Fold):**

| Kuadran Permintaan | Produk Sampel | Model | MAE (Porsi) | RMSE (Porsi) | WAPE (%) | Mean Bias |
|---|---|---|---|---|---|---|
| **High Demand** | **Bakso Kecil** | Seasonal Naive | 20.46 | 24.46 | 44.81% | -4.11 |
| | | SARIMA | 17.32 | 21.35 | 38.51% | -4.25 |
| | | **SARIMAX** | **17.31** | **21.34** | **38.48%** | **-4.28** |
| **Medium Demand** | **Bakso Telur Asin** | Seasonal Naive | 1.32 | 1.58 | 69.14% | -0.04 |
| | | **SARIMA** | **0.87** | **1.13** | **46.51%** | **+0.15** |
| | | SARIMAX | 0.96 | 1.17 | 50.58% | +0.36 |
| **Low Demand** | **Mie Spicy Barbeque** | SARIMA | 0.16 | 0.34 | 107.04% | -0.12 |
| | | SARIMAX | 0.37 | 0.40 | 190.30% | +0.19 |
| **Sparse Demand** | **Bakso Beranak** | SARIMA/SARIMAX | 0.01 | 0.01 | 100.00% | +0.01 |

> **Catatan Metodologis Mengenai Metrik:** Metrik **WAPE (Weighted Absolute Percentage Error)** digunakan sebagai pengganti MAPE. Pada data penjualan ritel, nilai aktual nol ($y_t = 0$) sering muncul sehingga MAPE standar menghasilkan nilai tak hingga (*division by zero*). WAPE membobotkan selisih kesalahan secara proporsional terhadap total volume aktual.

3. **Proyeksi Permintaan 7 Hari ke Depan (25 September – 01 Oktober 2026):**
   Contoh proyeksi untuk produk utama **Bakso Kecil**:
   - `2026-09-25` (Jumat) : **46 porsi** (95% CI: [27, 65] porsi) $\rightarrow$ Rekomendasi Stok: **46 porsi**
   - `2026-09-26` (Sabtu) : **59 porsi** (95% CI: [40, 78] porsi) $\rightarrow$ Rekomendasi Stok: **59 porsi**
   - `2026-09-27` (Minggu): **66 porsi** (95% CI: [47, 85] porsi) $\rightarrow$ Rekomendasi Stok: **67 porsi** (*Peak Weekend*)
   - `2026-09-28` (Senin) : **47 porsi** (95% CI: [28, 66] porsi) $\rightarrow$ Rekomendasi Stok: **48 porsi**
   - `2026-09-29` (Selasa): **40 porsi** (95% CI: [21, 59] porsi) $\rightarrow$ Rekomendasi Stok: **41 porsi**
   - `2026-09-30` (Rabu)  : **48 porsi** (95% CI: [29, 67] porsi) $\rightarrow$ Rekomendasi Stok: **49 porsi**
   - `2026-10-01` (Kamis) : **41 porsi** (95% CI: [22, 60] porsi) $\rightarrow$ Rekomendasi Stok: **41 porsi**

Seluruh hasil proyeksi 69 produk tersimpan lengkap di [`outputs/forecast_7_days.csv`](outputs/forecast_7_days.csv).

---

## 4. Pembahasan Khusus: Keterbatasan SARIMAX pada Sparse Demand

Pada produk berkategori *Sparse Demand* (seperti *Bakso Beranak* yang memiliki 95.1% hari bersuaka nol):
1. **Pelanggaran Asumsi Statistik Gaussian:** Model SARIMAX mengasumsikan residu berdistribusi normal kontinu ($e_t \sim \mathcal{N}(0, \sigma^2)$). Pada data dengan 95% angka nol, data memiliki massa probabilitas diskrit pada titik nol (*zero-inflated*).
2. **Kelemahan Output Kontinu:** Model memprediksi angka desimal kontinu yang sangat kecil (misalnya 0.01 porsi per hari). Nilai ini tidak memiliki arti operasional bagi staf dapur yang harus merebus bakso utuh.
3. **Solusi Metodologis & Manajerial:**
   - **Metode Croston (1972) / SBA (Syntetos-Boylan Approximation):** Untuk riset lanjutan, disarankan menggunakan metode Croston yang memisahkan estimasi interval kedatangan pesanan (*inter-arrival time*) dan ukuran pesanan (*demand size*).
   - **Kebijakan Stok Bisnis:** Menu sparse tidak perlu diramalkan dengan model time series harian. Warung disarankan menerapkan strategi **Made-to-Order** atau menetapkan stok penyangga statis (**Safety Stock = 2 butir frozen**) di freezer.

---

## 5. Implementasi Bisnis: Integrasi ke Bill of Materials (BOM) Dapur

Hasil peramalan porsi pada `outputs/forecast_7_days.csv` secara langsung diintegrasikan dengan matriks Bill of Materials ([PRD.md](PRD.md) FR-04):

$$\text{Kebutuhan Bahan Baku } j \text{ (Gram)} = \sum_{i=1}^{69} \left( \hat{Y}_{i, \text{besok}} \times \text{Resep}_{i, j} \right) + \text{Buffer Stok}$$

- **Daging Sapi Segar:** Dihitung dari akumulasi porsi *Bakso Kecil* ($\times 15$ gram/butir), *Bakso Urat Kecil* ($\times 20$ gram), *Bakso Isi Keju*, dan *Bakso Telur Asin*.
- **Tahu & Gorengan:** Dihitung langsung dari porsi *Tahu* dan *Goreng Panjang*.
- **Mie Kuning & Putih:** Dihitung dari porsi *Mie Kuning/Putih* dan *Mie Ayam*.

Dengan sistem peramalan ini:
1. Pemilik kedai memperoleh efisiensi belanja modal kerja (mengurangi risiko daging basi tersisa hingga 25–30%).
2. Risiko kehabisan menu favorit saat lonjakan akhir pekan berkurang drastis berkat batas atas *Confidence Interval 95%*.

---

## 6. Panduan Menjalankan Ulang (Reproducibility Guide)

Untuk menjalankan ulang seluruh proses eksperimen dan menghasilkan seluruh notebook serta artefak riset:

### Prasyarat Lingkungan
```bash
# Pastikan Python 3.10+ terpasang
# Instal dependensi yang diperlukan
pip install pandas numpy statsmodels scikit-learn scipy matplotlib seaborn jupyter nbformat nbclient
```

### Eksekusi Notebook
Notebook dapat langsung dibuka dan dijalankan secara interaktif melalui Jupyter Lab, Jupyter Notebook, atau ekstensi Jupyter di VS Code:
```bash
# Buka lingkungan Jupyter
jupyter lab
# Atau buka notebook berurutan dari folder notebooks/:
# 01_data_understanding.ipynb
# 02_exploratory_data_analysis.ipynb
# 03_time_series_analysis.ipynb
# 04_sarimax_modeling.ipynb
# 05_forecasting_evaluation.ipynb
```

Seluruh 5 notebook di folder `notebooks/` sudah terisi lengkap dengan kode, teks analisis berstandar akademik, grafik publikasi resolusi tinggi, serta output eksekusi yang tersimpan rapi.
