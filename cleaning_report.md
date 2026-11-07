# Laporan Data Cleaning & Preprocessing Penjualan Bakso Lintang

**Kasus Bisnis:** Warung Bakso Lintang (Ketintang, Surabaya)  
**Dokumen Acuan:** [PRD.md](PRD.md) v1.1 - Sistem Prediksi Stok & Business Intelligence  
**File Input Mentah:** `sales_report.csv`  
**File Output Bersih:** `sales_clean.csv`  
**File Output Refund:** `refunds.csv`  
**File Arsip Dropped Nagih:** `dropped_nagih.csv`  
**Tanggal Eksekusi:** 2026-11-07 20:19:51  

---

## 1. Ringkasan Sebelum vs Sesudah Cleaning

| Metrik | Sebelum Cleaning (Raw) | Dropped (Nagih) | Sesudah Cleaning (Final) | Perubahan Bersih |
|---|---|---|---|---|
| **Jumlah Baris** | 64,327 | 392 | 61,431 | -2,896 (392 Nagih + 2,504 duplikat) |
| **Jumlah Kolom** | 25 | 26 | 26 | +1 kolom (eliminasi 10 kolom redundan/kosong + fitur analitis baru) |
| **Total Gross Sales** | Rp 579,298,500.00 | Rp 1,621,000.00 | Rp 577,677,500.00 | **SAMA PERSIS (Selisih Rp 0.00)** |
| **Total Net Sales** | Rp 545,722,042.59 | Rp 1,393,000.07 | Rp 544,329,042.52 | **SAMA PERSIS (Selisih Rp 0.00)** |
| **Net Sales (Payment)** | Rp 547,304,501.85 | Rp 1,456,000.07 | Rp 545,848,501.78 | **SAMA PERSIS (Selisih Rp 0.00)** |
| **Net Sales (Refund)** | Rp -1,582,459.26 | Rp -63,000.00 | Rp -1,519,459.26 | **SAMA PERSIS (Selisih Rp 0.00)** |

---

## 2. Keputusan Bisnis: Pembuangan "0-Nagih" & Eliminasi Kolom Redundan

1. **Pembuangan Seluruh Struk Kategori "0-Nagih"**:
   - Berdasarkan keputusan Owner, seluruh transaksi kasir yang berkaitan dengan piutang bertanda kategori **"0-Nagih"** diabaikan dari pembukuan omzet operasional warung dan tidak dimasukkan ke dalam model prediksi stok bahan baku.
   - Sebanyak **98 struk** (392 baris: 382 baris kategori `0-Nagih` dan 10 baris menu reguler yang tercatat di struk yang sama) telah dikeluarkan.
   - Seluruh baris yang dikeluarkan tersimpan secara transparan di berkas arsip `dropped_nagih.csv` (Gross: Rp 1,621,000.00, Net: Rp 1,393,000.07) untuk keperluan audit kasir (*no silent drops*).

2. **Penghapusan Kolom Redundan `Date` dan `Time`**:
   - Kolom `Date` dan `Time` **resmi dihapus** karena seluruh informasi tanggal, jam, menit, dan detik telah disatukan secara presisi ke dalam kolom tunggal bertipe `datetime64` (**`Datetime`**).
   - Fitur waktu analitis yang dibutuhkan untuk eksplorasi data (`Year_Month`, `Day_Name`, `Hour`, `Is_Weekend`) telah diekstrak langsung dari `Datetime`, sehingga keberadaan kolom `Date` dan `Time` menjadi redundan.

3. **Penghapusan Kolom Redundan `Item_Flag`**:
   - Kolom `Item_Flag` (yang sebelumnya memetakan *Penagihan*, *Bundle*, dan *Custom Amount*) **resmi dihapus**.
   - Kategori menu sudah $100\%$ bersih dan diwakili secara alami oleh kolom bawaan `Category` (`Bakso`, `Mie`, `Gorengan`, `Minuman`, `Bundle_Package`, `Uncategorized`) tanpa redundansi data.

4. **Perlindungan Privasi Pelanggan**:
   - Nomor handphone pelanggan pada kolom **`Customer` tetap dipertahankan asli** sesuai input kasir tanpa hashing.

---

## 3. Kolom yang Dihapus (Drop) & Catatan Awalan Struk / Kasir

### A. Kolom yang Dihapus:
| Nama Kolom | Status / Karakteristik | Alasan Penghapusan |
|---|---|---|
| `Date` | Redundan dengan `Datetime` | Informasi tanggal sudah tersimpan lengkap di kolom `Datetime` dan fitur `Year_Month`/`Day_Name`. |
| `Time` | Redundan dengan `Datetime` | Informasi jam sudah tersimpan lengkap di kolom `Datetime` dan fitur `Hour`. |
| `Outlet` | Nilai konstan 100% | Hanya berisi 'Lintang Bakso Ketintang', tidak memiliki variansi informasi. |
| `Gratuity` | 100% bernilai 0 | Warung tidak menerapkan kebijakan tip kasir. |
| `Tax` | 100% bernilai 0 | Pajak restoran belum dipungut/diterapkan di sistem kasir. |
| `Collected By` | >99% satu orang | Dilayani oleh kasir 'Risa Yan' (tidak relevan untuk analisis tren menu). |
| `Brand` | 100% redundan | Informasi identik dengan kolom `Category`. |
| `Variant` | 100% kosong (NaN) | Tidak ada data varian di sistem POS. |
| `SKU` | 100% kosong (NaN) | Kode SKU barang tidak diinput oleh kasir. |
| `Served By` | 100% kosong (NaN) | Kolom pelayan tidak digunakan di sistem POS. |

### B. Catatan Awalan Struk (`Receipt Prefix`) & Kasir (`Collected By`):
- **Data Mentah Awal:** Memiliki 4 variasi awalan struk: `3BO` (63.809 baris), `9XT` (385 baris), `4Z7` (126 baris), dan `8AA` (7 baris). Kasir yang tercatat adalah `Risa Yan` (63.809 baris), `Reny Komar` (385 baris), `Nawayoga` (100 baris), `Bakso Mambal` (26 baris), dan `Insan Admin` (7 baris).
- **Hasil Pembuangan Nagih:** Seluruh baris dengan awalan `9XT` (kasir `Reny Komar`) dan `8AA` (kasir `Insan Admin`) **terbukti 100% merupakan transaksi Nagih** sehingga seluruhnya ikut terbuang ke `dropped_nagih.csv`.
- **Kondisi Data Final:** Awalan struk `9XT` dan `8AA` serta kasir `Reny Komar` dan `Insan Admin` **tidak muncul lagi di data bersih final**. Hanya tersisa awalan `3BO` (kasir `Risa Yan`) dan `4Z7` (kasir `Nawayoga` & `Bakso Mambal`).

---

## 4. Distribusi Kategori Menu & Anomali Transaksi

### A. Distribusi Kategori Menu (`Category`)

| Kategori Menu (Category) | Jumlah Baris | Persentase |
|---|---|---|
| `Bakso` | 34,286 | 55.81% |
| `Minuman` | 8,768 | 14.27% |
| `Gorengan` | 8,093 | 13.17% |
| `Mie` | 5,115 | 8.33% |
| `Tambahan` | 3,416 | 5.56% |
| `Ice Cream Aice` | 1,639 | 2.67% |
| `Bundle_Package` | 80 | 0.13% |
| `Uncategorized` | 34 | 0.06% |

- **Bakso, Gorengan, Mie, Minuman, Tambahan**: Menu operasional reguler warung bakso yang akan digunakan untuk pemodelan resep bahan baku dapur ([PRD.md](PRD.md) FR-04).
- **Bundle_Package**: Paket bundling menu makanan + minuman (80 baris).
- **Uncategorized**: Pembayaran nominal manual kasir (34 baris).

### B. Anomaly_Flag (Indikasi Transaksi Khusus)

| Jenis Anomali (Anomaly_Flag) | Jumlah Baris | Persentase |
|---|---|---|
| `None` | 58,125 | 94.62% |
| `Gratis/Diskon Penuh` | 3,298 | 5.37% |
| `Kemungkinan Uji Coba` | 7 | 0.01% |
| `Outlier Gross` | 1 | 0.00% |

- **Outlier Gross (1 baris)**: Transaksi struk `3BOOCW` senilai Rp 500.000 (50 porsi Mie Gebres) yang didiskon 100% oleh diskon owner.
- **Kemungkinan Uji Coba (7 baris)**: Transaksi refund dengan alasan 'trial' atau 'belajar' pada awal setup sistem POS.
- **Gratis/Diskon Penuh (3,298 baris)**: Transaksi pesanan dengan Net Sales Rp 0 akibat diskon karyawan, promo voucher, atau diskon owner.
- **None**: Transaksi penjualan normal tanpa indikasi anomali.

---

## 5. Hasil Validasi Kualitas Data (Data Quality Check)

1. **Konsistensi Formula Finansial**:
   - `Net Sales == Gross Sales - Discounts - Refunds`: **LOLOS** di 100% baris (toleransi selisih <= 0.5).
2. **Integritas Kolom Inti**:
   - Kolom `Datetime`, `Category`, `Items`, `Quantity`, `Gross Sales`, dan `Net Sales` memiliki 0 missing values (**100% lengkap**).
3. **Pembersihan Whitespace**:
   - Seluruh kolom teks telah dibersihkan dari spasi liar di awal dan akhir teks.
4. **Keutuhan Finansial & Rekonsiliasi**:
   - Formula `Raw - Dropped Nagih == Clean Final` terpenuhi secara presisi dengan selisih Rp 0.00.

---

## 6. Keputusan yang Perlu Dikonfirmasi Pemilik Data (Owner)

Pertanyaan terkait kategori `0-Nagih` telah terjawab (dibuang dan diarsipkan). Berikut 4 pertanyaan lanjutan yang memerlukan konfirmasi Owner sebelum pemodelan prediksi stok bahan baku ([PRD.md](PRD.md) FR-04):

1. **Apakah kategori "Uncategorized" (Custom Amount) dihitung sebagai omzet penjualan?**
   - *Temuan*: Terdapat 34 baris transaksi `Uncategorized` dengan total Net Sales Rp 173.000 yang tidak memiliki kuantitas porsi fisik menu bakso.
   - *Rekomendasi*: Dikecualikan dari model peramalan bahan baku dapur (karena tidak ada resep BOM), namun tetap disertakan dalam laporan omzet kasir (BI dashboard).

2. **Apakah baris duplikat memang pesanan batch berbeda dalam satu struk?**
   - *Temuan*: Ditemukan pesanan menu identik berulang dalam satu nomor struk yang sama pada waktu yang sama.
   - *Rekomendasi*: Pendekatan agregasi penjumlahan kuantitas dan nominal (yang telah diterapkan) adalah langkah terbaik agar total konsumsi bahan baku per hari tercatat akurat.

3. **Apakah baris Gross Sales Rp 500.000 adalah transaksi operasional valid?**
   - *Temuan*: Struk `3BOOCW` pada tanggal 4 Maret 2026 mencatat pemesanan 50 porsi Mie Gebres senilai Rp 500.000 dengan diskon 100% ('Discount Owner') sehingga Net Sales = Rp 0.
   - *Rekomendasi*: Transaksi ini valid sebagai pemakaian stok mie dapur (50 porsi terpakai), namun harus dikecualikan dari perhitungan *Average Order Value* (AOV) reguler agar tidak mendistorsi pola belanja pelanggan.

4. **Apa makna operasional dari struk dengan awalan "4Z7" (kasir Nawayoga & Bakso Mambal)?**
   - *Temuan*: Terdapat 34 struk (126 baris awal) dengan awalan struk `4Z7` yang diinput oleh kasir `Nawayoga` (100 baris) dan `Bakso Mambal` (26 baris). Seluruh transaksi ini memiliki Net Sales = Rp 0.
   - *Rekomendasi*: Mohon konfirmasi apakah transaksi ini merupakan pesanan operasional cabang mitra, konsumsi internal karyawan/keluarga, atau transaksi simulasi/training sistem, agar dapat ditentukan apakah dimasukkan ke model prediksi stok atau diarsipkan terpisah.
