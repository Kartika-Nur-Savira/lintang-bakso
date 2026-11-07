# Laporan Audit & Dokumentasi Data Cleaning Penjualan Bakso Lintang

**Kasus Bisnis:** Warung Bakso Lintang (Ketintang, Surabaya)  
**Dokumen Acuan:** [PRD.md](PRD.md) v1.1 - Sistem Prediksi Stok & Business Intelligence  
**File Input Mentah:** `sales_report.csv` (64,327 baris x 25 kolom)  
**File Output Bersih:** `sales_clean.csv` (61,431 baris x 26 kolom)  
**File Output Refund:** `refunds.csv` (149 baris)  
**File Arsip Dropped Nagih:** `dropped_nagih.csv` (392 baris)  
**Tanggal Eksekusi:** 2026-11-07 20:29:37  

---

## 1. Ringkasan Sebelum vs Sesudah Cleaning

| Metrik | Data Awal (Raw) | Dikeluarkan (Nagih) | Data Bersih (Final) | Status Rekonsiliasi |
|---|---|---|---|---|
| **Jumlah Baris** | 64,327 | 392 | 61,431 | -2,896 baris (392 Nagih + 2,504 duplikat) |
| **Jumlah Kolom** | 25 | 26 | 26 | +1 kolom (8 kolom dibuang, 9 fitur baru/standar) |
| **Total Gross Sales** | Rp 579,298,500.00 | Rp 1,621,000.00 | Rp 577,677,500.00 | **SAMA PERSIS (Selisih Rp 0.00)** |
| **Total Net Sales** | Rp 545,722,042.59 | Rp 1,393,000.07 | Rp 544,329,042.52 | **SAMA PERSIS (Selisih Rp 0.00)** |
| **Net Sales (Payment)** | Rp 547,304,501.85 | Rp 1,456,000.07 | Rp 545,848,501.78 | **SAMA PERSIS (Selisih Rp 0.00)** |
| **Net Sales (Refund)** | Rp -1,582,459.26 | Rp -63,000.00 | Rp -1,519,459.26 | **SAMA PERSIS (Selisih Rp 0.00)** |

---

## 2. Matriks Penanganan Data Cleaning (Kondisi Awal, Penanganan, Alasan, dan Hasil)

Berikut adalah dokumentasi terstruktur untuk setiap isu kualitas data yang ditemukan:

### A. Penyatuan dan Standarisasi Tanggal & Waktu
- **Kondisi Awal:** Kolom tanggal (`Date`) dan jam (`Time`) terpisah sebagai string dengan format lokal (`DD-MM-YYYY` dan `HH:MM:SS`), belum bertipe datetime presisi.
- **Penanganan:** Menggabungkan keduanya menjadi satu kolom tunggal **`Datetime`** bertipe `datetime64[ns]`, kemudian mengekstrak 4 atribut waktu analitis (`Year_Month`, `Day_Name`, `Hour`, `Is_Weekend`). Kolom `Date` dan `Time` mentah dilepas.
- **Alasan:** Format timestamp presisi dibutuhkan sebagai dasar urutan deret waktu pada model peramalan kebutuhan bahan baku dapur ([PRD.md](PRD.md) FR-04), dan mempermudah analisis pola operasional jam sibuk tanpa redundansi data.
- **Hasil:** 1 kolom timestamp presisi (`Datetime`) dan 4 fitur waktu siap pakai untuk eksplorasi tren bisnis.

### B. Transaksi Kategori "0-Nagih" (Piutang Kasir)
- **Kondisi Awal:** Terdapat 98 nomor struk kasir yang memuat item berkategori `0-Nagih` (382 baris menu Nagih seperti '0-Somay', '0-Kecil', dan 10 baris menu bakso reguler yang tercatat pada struk yang sama).
- **Penanganan:** Mengidentifikasi seluruh `Receipt Number` yang mengandung `0-Nagih`, membuang seluruh baris dari struk tersebut, dan menyimpannya ke berkas arsip `dropped_nagih.csv`.
- **Alasan:** Berdasarkan arahan Owner, transaksi ini bukan penjualan makanan/minuman operasional warung, melainkan pencatatan penagihan piutang/titipan uang antar kasir, sehingga akan mendistorsi prediksi konsumsi bahan baku dapur jika diikutsertakan.
- **Hasil:** Sebanyak 392 baris (98 struk) berhasil dikeluarkan dan diarsipkan lengkap (Gross: Rp 1,621,000.00, Net: Rp 1,393,000.07). Awalan struk `9XT` (kasir `Reny Komar`) dan `8AA` (kasir `Insan Admin`) otomatis bersih dari data final.

### C. Kolom Tidak Berguna, Redundan, dan Kosong
- **Kondisi Awal:** Terdapat 8 kolom yang tidak memberikan nilai analitis atau 100% bernilai kosong dari sistem kasir.
- **Penanganan:** Menghapus 8 kolom tersebut dari dataset (`Outlet`, `Gratuity`, `Tax`, `Collected By`, `Brand`, `Variant`, `SKU`, `Served By`).
- **Alasan:**
  - `Outlet`: Bernilai konstan 100% ('Lintang Bakso Ketintang').
  - `Gratuity` & `Tax`: 100% bernilai 0 (tidak ada tip dan belum menerapkan pajak restoran).
  - `Collected By`: >99% dilayani oleh kasir yang sama ('Risa Yan').
  - `Brand`: Redundan dengan kolom `Category` ('Unbranded' / 'Aice').
  - `Variant`, `SKU`, `Served By`: 100% bernilai kosong (NaN) di seluruh baris.
- **Hasil:** Dataset menjadi ringkas dan hemat memori tanpa menghilangkan informasi esensial apa pun.

### D. Baris Transaksi Refund (`Event Type == "Refund"`)
- **Kondisi Awal:** Terdapat 149 baris pengembalian dana riil dengan format kolom `Items` tercampur teks sistem ('Full Refund for: <struk> - <nama item>').
- **Penanganan:** Menambahkan penanda boolean `Is_Refund = True`, mengekstrak tipe refund ke `Refund_Type` ('Full' atau 'Partial'), membersihkan teks di kolom `Items` sehingga kembali ke nama menu aslinya, serta menyalin riwayatnya ke `refunds.csv`.
- **Alasan:** Transaksi refund adalah pengurang omzet yang sah secara pembukuan kasir (nilai Quantity dan Net Sales negatif memang fakta riil refund), sehingga tidak boleh dihapus melainkan harus diaudit secara jelas.
- **Hasil:** 149 baris refund tersimpan rapi dan terstandarisasi di `refunds.csv` (Total Net Refund: Rp -1,519,459.26), dan nama menu aslinya dapat dianalisis.

### E. Transaksi Duplikat Identik dalam Satu Struk
- **Kondisi Awal:** Ditemukan 4.520 baris transaksi (2.504 baris berlebih) yang memiliki kesamaan nilai identik pada seluruh kolom identitas di dalam nomor struk yang sama.
- **Penanganan:** Melakukan agregasi (group by seluruh kolom non-metrik, lalu menjumlahkan kolom numerik `Quantity`, `Gross Sales`, `Discounts`, `Refunds`, dan `Net Sales`), serta menambahkan kolom `Merged_Row_Count`.
- **Alasan:** Duplikasi dalam satu nomor struk bukan kesalahan sistem, melainkan pemesanan menu yang sama secara bertahap (*batch ordering*) oleh meja pelanggan. Jika dihapus mentah (*drop_duplicates*), jumlah porsi terjual dan omzet riil akan hilang.
- **Hasil:** Sebanyak 2.504 baris berlebih berhasil dirampingkan. Validasi ketat (`assert`) membuktikan nilai Gross Sales dan Net Sales sebelum vs sesudah agregasi **SAMA PERSIS (selisih Rp 0,00)**.

### F. Penandaan Anomali Transaksi (`Anomaly_Flag`)
- **Kondisi Awal:** Terdapat beberapa transaksi dengan nilai atau pola yang tidak lazim (porsi pesanan sangat besar, kata kunci uji coba kasir, dan pesanan bernilai Rp 0).
- **Penanganan:** Menambahkan kolom `Anomaly_Flag` (`Outlier Gross`, `Kemungkinan Uji Coba`, `Gratis/Diskon Penuh`, `None`) tanpa menghapus baris data.
- **Alasan:** Memberikan transparansi analitis agar analis data dapat menyaring atau mengecualikan transaksi ekstrem saat melatih model machine learning.
- **Hasil:** Terdeteksi 1 baris *Outlier Gross* (struk `3BOOCW`, 50 porsi Mie Gebres diskon 100% oleh owner senilai Rp 500.000), 7 baris refund uji coba (*trial* kasir), dan 3.298 baris pesanan gratis/diskon penuh.

### G. Standarisasi Teks, Modifier, dan Pembayaran
- **Kondisi Awal:** Kolom `Reason of Refund` memiliki teks bebas tidak seragam, `Modifier Applied` memiliki format multi-value dipisah koma dengan spasi, metode split payment berlabel `Gopay;Cash`, dan terdapat spasi liar.
- **Penanganan:** Memetakan alasan refund ke 8 kategori baku (teks asli disimpan di `Reason_Raw`), memparsing `Modifier Applied` menjadi `Modifier_List` dipisahkan pipa (`|`), menyeragamkan payment method menjadi `Split (Gopay+Cash)`, serta membersihkan leading/trailing whitespace pada seluruh kolom teks.
- **Alasan:** Standarisasi label mutlak diperlukan agar proses grouping dan filtering saat EDA tidak terpecah oleh inkonsistensi penulisan.
- **Hasil:** Seluruh kolom kategorikal bersih, seragam, dan bebas spasi liar.

### H. Data Identitas Pelanggan (`Customer`)
- **Kondisi Awal:** Kolom `Customer` berisi nomor handphone pelanggan format kasir (`+62...`) dan nilai kosong untuk pelanggan anonim.
- **Penanganan:** Mempertahankan kolom `Customer` apa adanya sesuai data asli kasir tanpa dilakukan hashing SHA-256.
- **Alasan:** Sesuai instruksi pengguna untuk memudahkan penelusuran riwayat pelanggan dan analisis retensi pelanggan (*repeat orders*).
- **Hasil:** 38.551 nomor handphone pelanggan tersimpan utuh dan 25.384 transaksi anonim tetap tercatat wajar.

---

## 3. Hasil Validasi Mutu Data (Data Quality Check)

1. **Konsistensi Formula Keuangan Kasir:**
   - Pengujian `Net Sales == Gross Sales - Discounts - Refunds` terpenuhi di **100% baris** (toleransi pembulatan <= 0.5).
2. **Kelengkapan Kolom Inti (*Core Completeness*):**
   - Kolom inti (`Datetime`, `Category`, `Items`, `Quantity`, `Gross Sales`, `Net Sales`) memiliki **0 missing values (100% lengkap)**.
3. **Pembersihan Whitespace:**
   - Seluruh kolom teks telah dibersihkan dari spasi liar di awal dan akhir karakter.
4. **Rekonsiliasi Keuangan (Zero Financial Loss):**
   - Formula `Total Raw - Total Dropped (Nagih) == Total Bersih Final` terpenuhi secara matematis dengan **selisih Rp 0,0000** baik pada Gross Sales maupun Net Sales.

---

## 4. Distribusi Data Bersih Final

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

- Menu kategori utama (`Bakso`, `Gorengan`, `Mie`, `Minuman`, `Tambahan`) mencakup **97,16%** transaksi, yang akan digunakan sebagai input penyusunan Bill of Materials (BOM) pada model prediksi stok ([PRD.md](PRD.md) FR-04).
- Kategori `Bundle_Package` (80 baris) merupakan pesanan paket makanan + minuman.
- Kategori `Uncategorized` (34 baris) merupakan transaksi nominal manual kasir.

### B. Distribusi Indikator Anomali (`Anomaly_Flag`)

| Jenis Anomali (Anomaly_Flag) | Jumlah Baris | Persentase |
|---|---|---|
| `None` | 58,125 | 94.62% |
| `Gratis/Diskon Penuh` | 3,298 | 5.37% |
| `Kemungkinan Uji Coba` | 7 | 0.01% |
| `Outlier Gross` | 1 | 0.00% |

---

## 5. Pertanyaan Lanjutan yang Perlu Dikonfirmasi Owner

Berikut adalah 4 poin keputusan operasional yang perlu dikonfirmasi pemilik warung (Owner) sebelum melatih model machine learning:

1. **Status Omzet Menu "Uncategorized" (Custom Amount):**
   - *Fakta:* Terdapat 34 transaksi manual kasir dengan total Net Sales Rp 173.000 tanpa keterangan menu fisik.
   - *Rekomendasi:* Dikecualikan dari model peramalan bahan baku dapur (karena tidak ada resep fisik), tetapi tetap dihitung dalam laporan total omzet kasir.

2. **Pola Pesanan Duplikat dalam Satu Nomor Struk:**
   - *Fakta:* Ditemukan 2.504 baris menu yang diinput berulang pada struk yang sama dan telah diagregasikan kuantitasnya.
   - *Rekomendasi:* Mohon konfirmasi apakah pola ini memang pesanan bertahap (*tambah porsi saat makan*) agar pendekatan agregasi yang diterapkan dinyatakan final.

3. **Validitas Transaksi Pesanan Porsi Besar (Gross Rp 500.000):**
   - *Fakta:* Struk `3BOOCW` pada tanggal 4 Maret 2026 mencatat pesanan 50 porsi Mie Gebres senilai Rp 500.000 dengan diskon 100% ('Discount Owner') sehingga Net Sales = Rp 0.
   - *Rekomendasi:* Transaksi ini valid sebagai konsumsi 50 porsi mie fisik dari dapur, namun perlu dikeluarkan saat menghitung *Average Order Value* (AOV) reguler agar tidak mendistorsi statistik keranjang belanja.

4. **Makna Operasional Struk Berawalan "4Z7" (Kasir Nawayoga & Bakso Mambal):**
   - *Fakta:* Terdapat 34 struk (126 baris) berawalan `4Z7` yang diinput oleh kasir `Nawayoga` (100 baris) dan `Bakso Mambal` (26 baris) dengan nilai Net Sales = Rp 0.
   - *Rekomendasi:* Mohon konfirmasi apakah transaksi ini merupakan pesanan operasional cabang lain, konsumsi internal, atau uji coba kasir baru, agar dapat ditentukan perlakuan pemodelannya.
