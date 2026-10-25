# 📈 Dashboard Makroekonomi & Pasar Keuangan Indonesia

Dashboard interaktif berbasis **Streamlit** untuk menganalisis hubungan antara indikator makroekonomi (BI Rate, selisih suku bunga BI-AS) dan dinamika pasar keuangan (IHSG, S&P 500, emas, minyak, USD/IDR, VIX) pada periode **2010-2026**.

> Proyek kelompok 2 Pattern

## 👥 Tim
- Talitha Nailal Husna
-Shinta Aprilia
-Ghinanti Farrah Diba
-salma ayu ningtias
-Ricardo Arrofi
-Syaharani Azka Haq
-Aprilia Nurjannah
-Ghifari Naufal Adya Kusumah

---

## 🎯 Tujuan
Menjawab pertanyaan berikut dengan data:
1. Bagaimana kinerja relatif aset keuangan pada periode tertentu?
2. Apakah IHSG mengikuti pergerakan pasar AS, dan apakah hubungannya stabil?
3. Bagaimana reaksi IHSG terhadap perubahan BI Rate?
4. Seberapa besar volatilitas IHSG berubah ketika pasar global panik (VIX tinggi)?
5. Apakah selisih suku bunga BI-AS berhubungan dengan nilai tukar rupiah?

---

## 🗂️ Pemahaman Data (Data Understanding)

**Sumber:** dataset *Daily Multi-Asset Macroeconomic and Financial Time Series (Indonesia/Global Markets)* dari Kaggle.

| Item | Data mentah | Data setelah cleaning (`data_clean.csv`) |
|---|---|---|
| Jumlah baris | 4.277 | 4.276 |
| Jumlah kolom | 10 | 25 |
| Periode | 2010-01-01 s/d 2026-05-29 | 2010-01-04 s/d 2026-05-29 |
| Frekuensi | Harian (hari kerja) | Harian (hari kerja) |

**Variabel utama**

| Kolom | Keterangan |
|---|---|
| `IHSG` | Indeks Harga Saham Gabungan |
| `SP500` | Indeks S&P 500 (pasar saham AS) |
| `GOLD` | Harga emas (USD) |
| `OIL` | Harga minyak mentah (USD) |
| `USDIDR` | Kurs USD terhadap rupiah |
| `VIX` | Indeks volatilitas pasar AS |
| `BI_rate` | Suku bunga acuan Bank Indonesia (%) |
| `US_rate` | Suku bunga acuan The Fed (%) |
| `CPI` | Inflasi Indonesia (%) |

**Kolom turunan hasil cleaning dan feature engineering**
- `IHSG_ret`, `SP500_ret`, `USDIDR_ret`, `GOLD_ret`, `OIL_chg`, `VIX_chg`: return/perubahan harian
- `SP500_ret_lag1`, `VIX_lag1`: nilai hari sebelumnya (menyelaraskan perbedaan zona waktu bursa)
- `BI_rate_chg`, `BI_event`: besar perubahan BI Rate dan penanda tanggal perubahan (48 kejadian)
- `spread_BI_US`: selisih BI Rate dikurangi suku bunga AS
- `USDIDR_outlier`, `IHSG_holiday`, `US_holiday`: penanda data bermasalah dan hari libur bursa

**Temuan saat data understanding dan cleaning**
- Satu baris kosong (2010-01-01, hari libur) dihapus.
- Nilai `USDIDR` yang tidak wajar ditandai/dikoreksi: 888,11 dan 892,0 (kurang satu digit), serta nilai 9.612,45 yang berulang pada Okt-Des 2013. [...sesuaikan dengan metode yang digunakan tim...]
- Nilai yang sama persis dengan hari sebelumnya (isian saat libur bursa) ditandai: 300 hari untuk IHSG dan 151 hari untuk pasar AS. Return pada hari libur dibiarkan kosong agar tidak menjadi return nol palsu.
- Harga minyak **-37,63** (2020-04-20) adalah kejadian nyata (WTI negatif), sehingga dipertahankan.
- `CPI` hanya berubah 17 kali dalam 16 tahun, jadi kemungkinan data tahunan yang diisi ke seluruh hari. Karena itu `CPI` tidak digunakan dalam dashboard.
- `BI_rate` hanya mencatat **perubahan**. Keputusan RDG "tahan" tidak dapat dianalisis, dan tanggalnya kemungkinan tanggal efektif, bukan tanggal pengumuman.
- Perubahan BI Rate **-2,00 pp pada 2016-04-21** kemungkinan efek pergantian metode suku bunga acuan, sehingga dashboard menyediakan opsi untuk mengecualikannya.

---

## 🖥️ Fitur Dashboard

**Filter dan kontrol interaktif**
- Periode cepat: seluruh periode, taper tantrum 2013, COVID-19 (2020), pengetatan global 2022-2023, 2025-sekarang, atau rentang tanggal kustom
- Pilihan aset dan skala logaritmik pada grafik tren
- Kartu KPI (IHSG, USD/IDR, emas, BI Rate, VIX) yang menyesuaikan periode
- Pengaturan jendela rolling, jendela event study, dan batas rezim VIX
- Simulasi investasi dengan modal, tanggal beli, dan tanggal jual yang bebas dipilih
- Unduh data terfilter dalam format CSV

**Tab dan grafik**

| Tab | Grafik | Tujuan |
|---|---|---|
| 📊 Tren Aset | Garis kinerja relatif (awal = 100) | Membandingkan kinerja aset |
| 🔗 Korelasi | Heatmap dan korelasi bergulir | Melihat keeratan dan stabilitas hubungan antar aset |
| 🏦 BI Rate & IHSG | Event study (CAR) | Reaksi IHSG terhadap perubahan BI Rate |
| 🌪️ Rezim VIX | Garis VIX dan boxplot return | Volatilitas IHSG pada kondisi tenang vs panik |
| 💱 Spread & Rupiah | Garis ganda dan scatter | Hubungan selisih suku bunga dengan kurs |
| 💰 Simulasi Investasi | Garis nilai investasi dan tabel hasil | Membandingkan hasil IHSG, emas, S&P 500, dan dolar dalam rupiah |
| 🗂️ Data | Tabel dan unduhan CSV | Eksplorasi data terfilter |

Setiap tab menampilkan **insight otomatis** yang dihitung ulang sesuai filter yang dipilih.

---

## 💡 Ringkasan Insight

Angka berikut berasal dari **seluruh periode** data (kecuali disebutkan lain) dan akan berubah mengikuti filter di dashboard.

1. **Kinerja aset:** pada pilihan aset bawaan (IHSG, S&P 500, emas, USD/IDR), S&P 500 naik paling tinggi (**+569%**), sedangkan USD/IDR naik **+90,5%** (rupiah melemah). Selama pandemi (2020), IHSG anjlok hingga **-37,7%** dari puncaknya dengan titik terendah pada 2020-03-24.
2. **IHSG mengikuti Wall Street dengan jeda satu hari:** korelasi IHSG dengan return S&P 500 hari sebelumnya (**0,29**) lebih kuat daripada hari yang sama (**0,17**). Ini sesuai urutan jam bursa: bursa Indonesia tutup sebelum Wall Street buka. Pada periode COVID-19 pola ini bergeser (lag 1 hari 0,26 vs hari yang sama 0,35), sehingga hubungannya tidak selalu sama.
3. **Hubungan antar aset tidak tetap:** korelasi bergulir 90 hari antara IHSG dan S&P 500 (lag 1 hari) bergerak dari **-0,16 sampai 0,74** (rata-rata 0,27).
4. **Reaksi terhadap BI Rate:** rata-rata abnormal return IHSG selama 5 hari bursa setelah **kenaikan** BI Rate adalah sekitar **-0,49%** (22 kejadian). Hasil setelah penurunan dapat dilihat di dashboard. Jumlah kejadian kecil, sehingga ini indikasi, bukan bukti kausal.
5. **VIX sebagai indikator risiko:** saat VIX hari sebelumnya berada di zona panik (> 25), volatilitas harian IHSG sekitar **2,1 kali** lebih besar daripada zona tenang (≤ 15). Pada 2020 selisihnya mencapai sekitar **3,4 kali**.
6. **Spread suku bunga dan rupiah:** korelasi level antara spread BI-AS dan USD/IDR adalah **-0,77** (spread menyempit cenderung bersamaan dengan rupiah melemah). Namun korelasi pada **perubahan bulanan** hanya **0,15**, sehingga korelasi level kemungkinan dipengaruhi tren yang sama (*spurious*), bukan hubungan sebab-akibat langsung.
7. **Simulasi investasi** (2 Januari 2020 sampai 29 Mei 2026): emas yang dihitung dalam rupiah memberi return total tertinggi (**+289,9%**), sedangkan penurunan sementara terdalam terjadi pada IHSG (**-37,7%**).

---

## ⚠️ Keterbatasan
- Event study memakai tanggal perubahan BI Rate yang kemungkinan tanggal efektif, dan jumlah kejadiannya kecil.
- Korelasi tidak sama dengan sebab-akibat. Hasil di dashboard bersifat deskriptif.
- IHSG yang dipakai adalah indeks harga, sehingga tidak memasukkan dividen.
- Simulasi investasi tidak memperhitungkan biaya transaksi, pajak, dan selisih harga beli-jual. Ini bukan rekomendasi investasi.
- `CPI` tidak dianalisis karena frekuensi aslinya tidak jelas (tampak tahunan).

---

## 🚀 Cara Menjalankan

**Prasyarat:** Python 3.13 

1. **Clone repository**
```bash
   git clone https://github.com/Chytalis/StudyClub_Pattern.git
   cd StudyClub_Pattern
```

2. **Buat dan aktifkan virtual environment**
```bash
   python -m venv venv
   venv\Scripts\activate           # Windows
   source venv/bin/activate        # macOS/Linux
```

3. **Instal dependensi**
```bash
   pip install -r requirements.txt
```

4. **Pastikan `data_clean.csv` berada di folder yang sama dengan `app.py`.**
   Jika file tidak ditemukan, dashboard menyediakan tombol upload di sidebar.

5. **Jalankan aplikasi**
```bash
   streamlit run app.py
```
   Browser akan terbuka otomatis di `http://localhost:8501`.

**Isi `requirements.txt`**
```
streamlit
pandas
numpy
plotly
```

---

## 📁 Struktur Proyek
```
.
├── app.py              # kode dashboard Streamlit
├── data_clean.csv      # dataset hasil cleaning
├── requirements.txt    # dependensi Python
├── notebooks/          # data understanding, cleaning, dan EDA
└── README.md
```

## 🛠️ Teknologi
Python · Streamlit · Pandas · NumPy · Plotly

## 📚 Sumber Data
Dataset *Daily Multi-Asset Macroeconomic and
