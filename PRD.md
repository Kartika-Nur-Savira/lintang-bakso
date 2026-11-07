# Product Requirements Document (PRD)
## Sistem Prediksi Stok & Business Intelligence "Bakso Lintang"

| | |
|---|---|
| **Produk** | Web dashboard prediksi kebutuhan bahan baku dan BI berbasis CSV/XLSX APOS |
| **Versi** | 1.1 (Draft) |
| **Tanggal** | 7 November 2026 |
| **Pengguna utama** | Pemilik (Owner) dan Tim Dapur / Admin |

## Daftar Isi

| No. | Section | Isi |
|---|---|---|
| 01 | Product Overview | Gambaran umum produk, deskripsi, dan solusi yang ditawarkan |
| 02 | Problem Statement | Permasalahan yang ingin diselesaikan |
| 03 | Goals & Objectives | Tujuan dan hasil yang ingin dicapai |
| 04 | Target Users | Segmentasi pengguna dan karakteristiknya |
| 05 | User Stories | Kebutuhan pengguna berdasarkan perspektif mereka |
| 06 | Feature Specification | Daftar fitur, deskripsi, fungsi, dan prioritas |
| 07 | Functional Requirements | Perilaku dan kebutuhan fungsional sistem secara detail |
| 08 | Non-Functional Requirements | Performa, keamanan, usability, scalability, reliability |
| 09 | Project Scope | Batasan pekerjaan: in-scope dan out-of-scope |
| 10 | Success Metrics | Indikator keberhasilan produk |
| 11 | Assumptions & Constraints | Asumsi dan keterbatasan selama pengembangan |

---

## 01. Product Overview

**Bakso Lintang Smart Stock & BI** adalah aplikasi web yang membaca laporan penjualan harian dari mesin kasir APOS (CSV/XLSX), memprediksi penjualan menu untuk hari-hari berikutnya, lalu mengubah prediksi itu menjadi daftar belanja bahan baku untuk esok hari. Aplikasi juga menampilkan tren kuliner dan fluktuasi harga bahan pokok regional dari AI. Pengguna juga dapat bertanya langsung lewat chatbot, misalnya menu apa yang paling laris.

### Solusi yang Ditawarkan

| Komponen | Deskripsi |
|---|---|
| Pengolahan data APOS | Unggah laporan kasir, validasi, dan penyimpanan ke database. |
| Forecasting penjualan | Model *time-series* memprediksi porsi tiap menu, dengan proyeksi 7 hari ke depan. |
| Konversi resep (BOM) | Porsi menu dikonversi menjadi kebutuhan berat bahan baku memakai matriks resep. |
| Dashboard interaktif | Ringkasan omzet, grafik tren, dan Daftar Belanja Besok Pagi. |
| Wawasan pasar | Tren kuliner dan harga pasar dari AI (*Search Grounding*). |
| Chatbot asisten data | Tanya jawab langsung soal penjualan dan tren, misalnya "menu apa yang paling laris?". |

## 02. Problem Statement

| Masalah | Dampak | Respons Produk |
|---|---|---|
| Kebutuhan bahan baku harian dihitung manual oleh tim dapur. | Memakan waktu, rawan salah hitung, berisiko belanja kurang atau berlebih. | Daftar belanja dihitung otomatis dari prediksi penjualan dan BOM. |
| Data transaksi APOS belum dimanfaatkan untuk perencanaan. | Keputusan belanja bergantung pada perkiraan, bukan data historis. | Model forecasting memakai data historis APOS. |
| Tren kuliner dan harga pasar tidak terpantau secara rutin. | Pemilik terlambat menyesuaikan menu dan anggaran belanja. | Panel tren eksternal dan prediksi harga pasar dari AI. |

## 03. Goals & Objectives

**Tujuan utama:** mengembangkan sistem proaktif untuk memprediksi kebutuhan bahan baku harian, memantau tren kuliner eksternal, dan menyajikan dasbor analitik bagi operasional kedai.

| Objective | Hasil yang Ingin Dicapai |
|---|---|
| O1 | Tim dapur memperoleh daftar belanja esok hari tanpa hitung manual. |
| O2 | Prediksi penjualan menu cukup akurat untuk dijadikan dasar belanja. |
| O3 | Owner dapat memantau omzet dan tren penjualan dari satu dasbor. |
| O4 | Owner mendapat wawasan tren kuliner dan harga pasar secara berkala. |
| O5 | Proses unggah data harian sederhana dan dapat dilakukan dari HP maupun laptop. |
| O6 | Pengguna dapat bertanya langsung ke chatbot (misalnya menu terlaris) dan mendapat jawaban dari data, tanpa login. |

## 04. Target Users

| Segmen | Karakteristik | Kebutuhan Utama | Perangkat |
|---|---|---|---|
| Owner | Pengambil keputusan, fokus pada omzet dan arah bisnis, waktu terbatas. | Laporan omzet, grafik tren penjualan, wawasan pasar eksternal. | Laptop / HP |
| Tim Dapur / Admin | Staf operasional, terbiasa dengan tabel mirip Excel, bukan pengguna teknis. | Mengunggah laporan CSV APOS dan melihat daftar belanja harian tanpa hitung manual. | HP / Laptop |

## 05. User Stories

| ID | Sebagai | Saya ingin | Agar |
|---|---|---|---|
| US-01 | Tim Dapur / Admin | mengunggah laporan harian APOS (.csv/.xlsx) | data penjualan terbaru masuk ke sistem. |
| US-02 | Tim Dapur / Admin | melihat Daftar Belanja Besok Pagi | saya bisa belanja bahan baku tanpa menghitung manual. |
| US-03 | Tim Dapur / Admin | diberi tahu jika file yang diunggah tidak valid | saya bisa memperbaikinya sebelum diproses. |
| US-04 | Owner | melihat estimasi omzet dan ringkasan penjualan | saya tahu kondisi usaha secara cepat. |
| US-05 | Owner | melihat grafik penjualan tiap menu 7 hari ke depan | saya bisa merencanakan produksi dan anggaran. |
| US-06 | Owner | melihat tren kuliner dan harga bahan pokok | saya bisa menyesuaikan menu dan harga jual. |
| US-07 | Owner / Tim Dapur | bertanya ke chatbot, misalnya “menu apa yang paling laris?” | saya mendapat jawaban dari data tanpa membuka banyak halaman. |

## 06. Feature Specification

| Fitur | Deskripsi | Fungsi | Prioritas |
|---|---|---|---|
| Upload Center CSV/XLSX | Modul unggah laporan kasir APOS secara berkala. | Membaca, memvalidasi, dan menyimpan data penjualan. | Must |
| Smart Purchasing Forecasting | Daftar belanja bahan baku esok hari otomatis. | Prediksi porsi menu lalu konversi ke berat bahan via BOM. | Must |
| Chatbot Asisten Data | Kolom chat di dasbor untuk bertanya soal penjualan, daftar belanja, dan tren. | Gemini memilih fungsi terdaftar, backend menjalankan query Supabase, hasil dirangkum dalam bahasa Indonesia. | Should |
| Demand & Sales Projections | Grafik tren penjualan menu. | Visualisasi proyeksi 7 hari ke depan, harian dan mingguan. | Should |
| Market Trend Insights | Widget tren kuliner dan harga bahan pokok regional. | Ringkasan dari AI (Gemini, *Search Grounding*). | Should |
| Prediksi Harga Pasar | Perkiraan harga bahan baku. | Mendukung perencanaan anggaran belanja. | Could |

## 07. Functional Requirements

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-01 | Sistem membaca file laporan berformat .csv atau .xlsx dari APOS. | Must |
| FR-02 | Sistem memvalidasi file (format, kolom wajib, tipe data) dan menampilkan pesan kesalahan yang jelas jika gagal. | Must |
| FR-03 | Sistem menyimpan data penjualan yang valid ke database (Supabase). | Must |
| FR-04 | Sistem menghasilkan prediksi porsi tiap menu untuk esok hari dari data historis. | Must |
| FR-05 | Sistem mengonversi porsi menu menjadi berat bahan baku memakai matriks resep (*Bill of Materials*). | Must |
| FR-06 | Sistem menampilkan Daftar Belanja Besok Pagi secara akurat di dasbor. | Must |
| FR-07 | Sistem menampilkan ringkasan metrik: estimasi omzet dan daftar belanja. | Should |
| FR-08 | Sistem menampilkan grafik tren dan proyeksi penjualan menu (7 hari ke depan; harian dan mingguan). | Should |
| FR-09 | Sistem menampilkan ringkasan tren kuliner dan harga pasar dari AI. | Should |
| FR-10 | Chatbot menjawab pertanyaan dari data Supabase lewat fungsi terdaftar (function calling), bukan SQL bebas. | Should |
| FR-11 | Backend memvalidasi parameter dari AI dan membatasi laju permintaan (rate limiting) karena aplikasi tanpa login. | Should |

## 08. Non-Functional Requirements

| Aspek | Kebutuhan | Target Awal (usulan) |
|---|---|---|
| Performa | Dasbor dan daftar belanja tampil cepat; pemrosesan file harian tidak menghambat staf. | Dasbor dimuat < 3 detik; unggah dan prediksi < 1 menit per file harian. |
| Keamanan | Data transaksi aman. Aplikasi tanpa login, sehingga perlindungan bertumpu pada tautan yang tidak dipublikasikan dan pembatasan permintaan. | HTTPS, rate limiting, kunci API hanya di server, query chatbot read-only. |
| Usability | Antarmuka bersih, berbasis tabel mirip Google Sheets/Excel, responsif di HP dan komputer. | Staf dapur dapat memakai tanpa pelatihan panjang. |
| Scalability | Sistem dapat menampung data historis yang terus bertambah. | Database terstruktur (PostgreSQL) dengan layanan cloud yang dapat ditingkatkan. |
| Reliability | Sistem tersedia saat dibutuhkan dan data tidak hilang. | Ketersediaan tinggi pada jam operasional; pencadangan data oleh platform database. |

## 09. Project Scope

| In-Scope | Out-of-Scope (usulan) |
|---|---|
| Pengolahan data penjualan harian dari file CSV/XLSX APOS. | Integrasi langsung (API real-time) dengan mesin APOS. |
| Forecasting porsi menu dan kebutuhan bahan baku (BOM) esok hari. | Pemesanan otomatis ke pemasok. |
| Prediksi harga pasar. | Modul akuntansi dan keuangan lengkap. |
| Tren kuliner eksternal via AI (*Search Grounding*). | Aplikasi mobile native (cukup web responsif). |
| Web dashboard interaktif untuk Owner dan Tim Dapur. | Dukungan multi-cabang. |
| Chatbot asisten data (tanya jawab dari data penjualan). | Login dan hak akses per peran pengguna. |
| — | Manajemen stok (pencatatan stok masuk/keluar, stok opname). |

## 10. Success Metrics

| Metrik | Indikator | Target Awal (usulan) |
|---|---|---|
| Akurasi prediksi | Kesalahan prediksi porsi menu (misalnya MAPE) pada data uji. | Ditetapkan bersama tim Data Science setelah data historis diuji. |
| Efisiensi belanja | Waktu tim dapur menyusun daftar belanja harian. | Turun signifikan dibanding hitung manual. |
| Adopsi | Frekuensi unggah laporan harian. | Laporan diunggah setiap hari operasional. |
| Kepuasan pengguna (UAT) | Daftar Belanja Besok Pagi mudah dibaca oleh tim dapur. | UAT lolos dengan masukan perwakilan kedai. |
| Akurasi chatbot | Jawaban chatbot sesuai data untuk pertanyaan yang didukung. | Cocok dengan hasil query langsung pada uji sampel pertanyaan. |

## 11. Assumptions & Constraints

### Asumsi

- Kedai mengekspor laporan penjualan dari APOS dalam format .csv atau .xlsx secara rutin.
- Data historis penjualan cukup untuk melatih model *time-series*.
- Resep (BOM) tiap menu tersedia dan dapat dimasukkan ke sistem.
- Staf dapur memiliki HP atau laptop dengan akses internet.
- Gemini API dapat diakses untuk analisis tren eksternal.

### Keterbatasan

- Unggah data masih manual, sehingga akurasi prediksi bergantung pada kedisiplinan unggah harian.
- Kualitas prediksi dipengaruhi jumlah dan kualitas data historis.
- Wawasan tren dan harga dari AI bersifat indikatif, bukan data resmi.
- Memakai layanan hosting dan database ringan (Vercel/Netlify, Supabase), sehingga kapasitas mengikuti paket yang dipilih.
- Tanpa login: semua yang memiliki tautan melihat data yang sama, dan tidak ada pembedaan hak akses Owner dan Tim Dapur.
- Chatbot hanya menjawab pertanyaan yang tercakup fungsi terdaftar.
- Tidak ada manajemen stok, sehingga dasbor dan chatbot tidak menampilkan sisa stok.
- Tim pengembang terdiri dari AI Engineer, Data Science, dan Full Stack.