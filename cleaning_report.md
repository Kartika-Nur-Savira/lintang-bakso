# Laporan Audit & Dokumentasi Data Cleaning Penjualan Bakso Lintang

**Kasus Bisnis:** Warung Bakso Lintang (Ketintang, Surabaya)  
**Dokumen Acuan:** [PRD.md](PRD.md) v1.1 - Sistem Prediksi Stok & Business Intelligence  
**File Input Mentah:** `sales_report.csv` (64,327 baris x 25 kolom)  
**File Output Bersih:** `sales_clean.csv` (61,431 baris x 27 kolom)  
**File Output Refund:** `refunds.csv` (149 baris)  
**File Arsip Dropped Nagih:** `dropped_nagih.csv` (392 baris)  
**Tanggal Eksekusi:** 2026-11-08 20:39:09  

---

## 1. Ringkasan Sebelum vs Sesudah Cleaning

| Metrik | Data Awal (Raw) | Dikeluarkan (Nagih) | Data Bersih (Final) | Status Rekonsiliasi |
|---|---|---|---|---|
| **Jumlah Baris** | 64,327 | 392 | 61,431 | -2,896 baris (392 Nagih + 2,504 duplikat) |
| **Jumlah Kolom** | 25 | - | 27 | +2 kolom (10 kolom dibuang, 12 fitur baru/standar) |
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

### B. Transaksi Kategori "0-Nagih" (Uji Coba Penjualan Warkop)
- **Kondisi Awal:** Terdapat 98 nomor struk kasir yang memuat item berkategori `0-Nagih` (382 baris menu Nagih seperti '0-Somay', '0-Kecil', dan 10 baris menu bakso reguler yang tercatat pada struk yang sama).
- **Penanganan:** Mengidentifikasi seluruh `Receipt Number` yang mengandung `0-Nagih`, membuang seluruh baris dari struk tersebut, dan menyimpannya ke berkas arsip `dropped_nagih.csv`.
<<<<<<< HEAD
- **Alasan:** Berdasarkan arahan Owner, transaksi ini bukan penjualan makanan/minuman operasional warung, melainkan pencatatan uji coba usaha di warkop dan berdasar arahan dari owner untuk transaksi itu diabaikan saja.
=======
- **Alasan:** Kategori 0-Nagih adalah uji coba penjualan di warkop (21 Feb-13 Mar 2026) yang tidak dilanjutkan, berdasarkan konfirmasi Owner. Karena bukan penjualan operasional warung, seluruh struk terkait dikeluarkan dan diarsipkan di dropped_nagih.csv. Awalan struk 9XT (kasir Reny Komar) dan 8AA (kasir Insan Admin) adalah bagian dari uji coba ini.
>>>>>>> 94d3fce (cleaning dataset)
- **Hasil:** Sebanyak 392 baris (98 struk) berhasil dikeluarkan dan diarsipkan lengkap (Gross: Rp 1,621,000.00, Net: Rp 1,393,000.07). Awalan struk `9XT` (kasir `Reny Komar`) dan `8AA` (kasir `Insan Admin`) otomatis bersih dari data final.

### C. Kolom Tidak Berguna, Redundan, dan Kosong
- **Kondisi Awal:** Terdapat 10 kolom yang tidak memberikan nilai analitis atau 100% bernilai kosong dari sistem kasir (`Outlet`, `Gratuity`, `Tax`, `Collected By`, `Brand`, `Date`, `Time`, `Variant`, `SKU`, `Served By`).
- **Penanganan:** Menghapus seluruh 10 kolom tersebut dari DataFrame (`df.drop(columns=drop_cols)`).
- **Alasan:** Kolom kosong dan konstanta tidak menambah variansi informasi, sedangkan kolom `Date` dan `Time` telah diwakili secara lebih akurat dan terintegrasi oleh kolom tunggal `Datetime`.
- **Hasil:** Struktur tabel lebih ramping dan efisien, menghemat penggunaan memori tanpa kehilangan informasi analitis penting.

### D. Pemisahan dan Standarisasi Transaksi Refund
- **Kondisi Awal:** Terdapat transaksi refund (149 baris sebelum agregasi) yang tercampur di dalam aliran transaksi pembayaran reguler.
- **Penanganan:** Menandai baris refund (`Is_Refund = True`), mengekstrak tipe refund (`Refund_Type` = 'Full' / 'Partial' / 'Tidak Ada') dan nama item asli, memetakan alasan refund ke kategori baku, serta mengekspor data audit refund ke `refunds.csv` sebelum agregasi.
- **Alasan:** Menjaga riwayat audit kasir tetap utuh dan transparan sebelum baris agregasi disatukan.
- **Hasil:** Berkas `refunds.csv` tersimpan rapi (149 baris, Net Sales: Rp -1,519,459.26).
*Catatan: File `refunds.csv` (sebelum agregasi) berisi 149 baris, sedangkan baris refund di `sales_clean.csv` (sesudah agregasi) berisi 137 baris; perbedaan ini wajar karena adanya penggabungan baris refund dengan atribut identik dalam satu struk.*

### E. Baris dengan Atribut Identik Menggunakan Agregasi (Bukan Drop Mentah)
- **Kondisi Awal:** Ditemukan 1,837 baris duplikat persis di semua kolom, dan 2,504 baris berlebih dengan atribut identik (kuantitas/nilai boleh berbeda) dalam satu nomor struk (melibatkan total 4,520 baris).
- **Penanganan:** Mengelompokkan berdasarkan atribut non-metrik dan menjumlahkan metrik kuantitas serta finansial (`Quantity`, `Gross Sales`, `Discounts`, `Refunds`, `Net Sales`), disertai kolom pelacak `Merged_Row_Count`.
- **Alasan:** Diduga pemesanan bertahap (belum dikonfirmasi Owner), seperti pelanggan yang menambah porsi saat makan tanpa membuka struk baru. Jika dibuang mentah menggunakan `drop_duplicates()`, omzet dan kuantitas penjualan riil akan hilang.
- **Hasil:** Sebanyak 2,504 baris berlebih berhasil dirampingkan menjadi baris tunggal teragregasi dengan integritas nominal 100% terjaga (selisih Rp 0,00).

### F. Penandaan Anomali Transaksi (`Anomaly_Flag`)
- **Kondisi Awal:** Terdapat transaksi ekstrem dan transaksi uji coba kasir yang belum memiliki label penanda.
- **Penanganan:** Membuat kolom `Anomaly_Flag` dengan kategori: 'Outlier Gross' (Gross >= Rp 500.000), 'Kemungkinan Uji Coba' (alasan refund trial/belajar), 'Gratis/Diskon Penuh' (Net = 0 pada event Payment), dan 'Normal'. Baris tidak dihapus melainkan hanya ditandai.
- **Alasan:** Memberikan transparansi pada tahap EDA dan permodelan tanpa merusak integritas rekonsiliasi data mentah.
- **Hasil:** Terpetakan 1 baris *Outlier Gross*, 7 baris kemungkinan uji coba kasir, 3,298 baris pesanan gratis/diskon penuh, dan 58,125 baris transaksi berstatus normal.

### G. Standarisasi Teks, Modifier, dan Pembayaran
- **Kondisi Awal:** Kolom `Reason of Refund` memiliki teks bebas tidak seragam, `Modifier Applied` memiliki format multi-value dipisah koma dengan spasi, metode split payment berlabel `Gopay;Cash`, dan terdapat spasi liar. Nilai kosong pada kolom kategorikal belum terstandarisasi.
- **Penanganan:** Memetakan alasan refund ke kategori baku (teks asli disimpan di `Reason_Raw`), memparsing `Modifier Applied` menjadi `Modifier_List` dipisahkan pipa (`|`), menyeragamkan payment method menjadi `Split (Gopay+Cash)`, mengisi nilai kosong pada `Discount Applied` dan `Reason_Raw` dengan label baku `'Tidak Ada'`, serta membersihkan leading/trailing whitespace pada seluruh kolom teks tanpa merusak missing values.
- **Alasan:** Standarisasi label mutlak diperlukan agar proses grouping dan filtering saat EDA tidak terpecah oleh inkonsistensi penulisan dan bebas dari string teks 'nan' atau 'None'.
- **Hasil:** Seluruh kolom kategorikal bersih, seragam, dan bebas spasi liar maupun teks 'nan'/'None'.

### H. Data Identitas Pelanggan (`Customer`)
- **Kondisi Awal:** Kolom `Customer` berisi nomor handphone pelanggan format kasir (`+62...`) dengan awalan tanda kutip tunggal (`'`) dan nilai kosong untuk pelanggan anonim.
- **Penanganan:** Menghapus tanda kutip tunggal di awal nomor HP (`str.lstrip("'")`) hanya pada nilai non-null, dan membiarkan nilai kosong tetap NaN. Nomor HP pelanggan dipertahankan asli atas keputusan pengguna (tanpa hashing).
- **Alasan:** Nomor HP pelanggan dipertahankan asli atas keputusan pengguna (hanya tanda ' di awal dihapus), tanpa hashing, untuk memudahkan penelusuran pelanggan.
- **Hasil:** Sebanyak 37,169 baris nomor HP pelanggan tersimpan utuh (3,523 pelanggan unik) dan 24,262 baris transaksi anonim (kosong) tetap tercatat wajar. *Catatan: File ini memuat nomor HP pelanggan, jadi tidak untuk dipublikasikan.*

---

## 3. Hasil Validasi Mutu Data (Data Quality Check)

1. **Konsistensi Formula Keuangan Kasir:**
   - Pengujian `Net Sales == Gross Sales - Discounts - Refunds` terpenuhi di **100% baris** (toleransi pembulatan <= 0.5).
2. **Kelengkapan Kolom Inti (*Core Completeness*):**
   - Kolom inti (`Datetime`, `Category`, `Items`, `Quantity`, `Gross Sales`, `Net Sales`) memiliki **0 missing values (100% lengkap)**.
3. **Pembersihan Whitespace:**
   - Seluruh kolom teks telah dibersihkan dari spasi liar di awal dan akhir karakter dengan mempertahankan nilai kosong asli.
4. **Bebas dari String 'nan' dan 'None':**
   - Seluruh file ekspor (`sales_clean.csv`, `refunds.csv`, `dropped_nagih.csv`) telah divalidasi tidak memuat string teks 'nan' atau 'None'.
5. **Rekonsiliasi Keuangan (Zero Financial Loss):**
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

- Menu kategori utama (`Bakso`, `Gorengan`, `Mie`, `Minuman`, `Tambahan`) mencakup **97.15%** transaksi, yang akan digunakan sebagai input penyusunan Bill of Materials (BOM) pada model prediksi stok ([PRD.md](PRD.md) FR-04).
- Kategori `Bundle_Package` (80 baris) merupakan paket makanan (Mie Ayam / Paket Bakso), tidak termasuk minuman (contoh: Mie Ayam Juara (11 baris), Mie Ayam Bakso Mantap (11 baris), Paket Bakso Klasik Kecil (8 baris)).
- Kategori `Uncategorized` (34 baris) merupakan Custom Amount (semua item bernama Custom Amount).

### B. Distribusi Indikator Anomali (`Anomaly_Flag`)

| Jenis Anomali (Anomaly_Flag) | Jumlah Baris | Persentase |
|---|---|---|
| `Normal` | 58,125 | 94.62% |
| `Gratis/Diskon Penuh` | 3,298 | 5.37% |
| `Kemungkinan Uji Coba` | 7 | 0.01% |
| `Outlier Gross` | 1 | 0.00% |

---

## 5. Pertanyaan Lanjutan yang Perlu Dikonfirmasi Owner

Berikut adalah 4 poin keputusan operasional yang perlu dikonfirmasi pemilik warung (Owner) sebelum melatih model machine learning:

1. **Status Omzet Menu "Uncategorized" (Custom Amount):**
   - *Fakta:* Terdapat 34 transaksi manual kasir dengan total Net Sales Rp 173,108.88 tanpa keterangan menu fisik (semua item bernama Custom Amount).
   - *Rekomendasi:* Dikecualikan dari model peramalan bahan baku dapur (karena tidak ada resep fisik), tetapi tetap dihitung dalam laporan total omzet kasir.

2. **Pola Pesanan Duplikat dalam Satu Nomor Struk:**
   - *Fakta:* Ditemukan 2,504 baris menu berlebih dengan atribut identik pada struk yang sama dan telah diagregasikan kuantitasnya (melibatkan total 4,520 baris).
   - *Rekomendasi:* Mohon konfirmasi apakah pola ini diduga pemesanan bertahap (*tambah porsi saat makan*) agar pendekatan agregasi yang diterapkan dinyatakan final.

3. **Validitas Transaksi Pesanan Porsi Besar (Gross Rp 500.000):**
   - *Fakta:* Struk `3BOOCW` pada tanggal 4 Maret 2026 mencatat pesanan 50 porsi Mie Gebres senilai Rp 500,000.00 dengan diskon Rp 500,000.00 sehingga Net Sales = Rp 0.00.
   - *Rekomendasi:* Transaksi ini kemungkinan konsumsi 50 porsi; perlu konfirmasi Owner. Selain itu, transaksi ini perlu dikeluarkan saat menghitung *Average Order Value* (AOV) reguler agar tidak mendistorsi statistik keranjang belanja.

4. **Makna Operasional Struk Berawalan "4Z7" (Kasir Nawayoga & Bakso Mambal):**
   - *Fakta:* Terdapat 34 struk (126 baris) berawalan `4Z7` dengan total Gross Sales Rp 838,000.00 dan Net Sales Rp 27,000.00, terdiri dari: kasir `Bakso Mambal` (26 baris, 5 struk, Gross: Rp 181,000.00, Net: Rp 0.00); kasir `Nawayoga` (100 baris, 29 struk, Gross: Rp 657,000.00, Net: Rp 27,000.00).
   - *Rekomendasi:* Mohon konfirmasi apakah transaksi ini merupakan pesanan operasional cabang lain, konsumsi internal, atau uji coba kasir baru, agar dapat ditentukan perlakuan pemodelannya.
