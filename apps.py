import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st

print("NumPy:", np.__version__)
print("Pandas:", pd.__version__)
print("Semua library berhasil di-import!")


import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Data Understanding",
    page_icon="📊",
    layout="wide"
)

st.title("Data Understanding")
st.subheader("Dataset Makroekonomi dan Keuangan Indonesia")

# Mengunggah dataset
file = st.file_uploader(
    "Unggah file CSV",
    type=["csv"]
)

if file is None:
    st.info("Silakan unggah dataset CSV terlebih dahulu.")
    st.stop()

df = pd.read_csv(file)

# Mengubah kolom tanggal
if "Date" in df.columns:
    df["Date"] = pd.to_datetime(
        df["Date"], errors="coerce"
    )

# 1. Gambaran umum dataset
st.header("1. Gambaran Umum Dataset")

col1, col2, col3 = st.columns(3)

col1.metric("Jumlah Baris", df.shape[0])
col2.metric("Jumlah Kolom", df.shape[1])
col3.metric("Data Duplikat", int(df.duplicated().sum()))

st.write("Lima data pertama:")
st.dataframe(df.head(), use_container_width=True)

# 2. Struktur data
st.header("2. Struktur Data")

struktur = pd.DataFrame({
    "Nama Kolom": df.columns,
    "Tipe Data": [str(df[c].dtype) for c in df.columns],
    "Data Terisi": [df[c].notna().sum() for c in df.columns],
    "Data Kosong": [df[c].isna().sum() for c in df.columns]
})

st.dataframe(struktur, use_container_width=True)

# 3. Missing values
st.header("3. Pemeriksaan Missing Values")

missing = pd.DataFrame({
    "Kolom": df.columns,
    "Jumlah Kosong": df.isna().sum().values,
    "Persentase Kosong (%)": (
        df.isna().mean().values * 100
    ).round(2)
})

st.dataframe(missing, use_container_width=True)

data_kosong = missing[
    missing["Jumlah Kosong"] > 0
]

if not data_kosong.empty:
    st.bar_chart(
        data_kosong.set_index("Kolom")["Jumlah Kosong"]
    )
else:
    st.success("Tidak ada nilai kosong.")

# 4. Statistik deskriptif
st.header("4. Statistik Deskriptif")

data_numerik = df.select_dtypes(
    include="number"
)

if not data_numerik.empty:
    st.dataframe(
        data_numerik.describe().T,
        use_container_width=True
    )

# 5. Distribusi data
st.header("5. Distribusi Variabel")

if not data_numerik.empty:
    variabel = st.selectbox(
        "Pilih variabel",
        data_numerik.columns
    )

    fig, ax = plt.subplots()

    data_numerik[variabel].dropna().hist(
        bins=30, ax=ax
    )

    ax.set_title(f"Distribusi {variabel}")
    ax.set_xlabel(variabel)
    ax.set_ylabel("Frekuensi")

    st.pyplot(fig)
    plt.close(fig)

# 6. Tren data
st.header("6. Tren Variabel")

if "Date" in df.columns and not data_numerik.empty:
    pilihan = st.selectbox(
        "Pilih variabel untuk tren",
        data_numerik.columns,
        key="pilihan_tren"
    )

    tren = df[["Date", pilihan]].dropna()
    tren = tren.sort_values("Date")

    if not tren.empty:
        st.line_chart(
            tren.set_index("Date")[pilihan]
        )

# 7. Korelasi antarvariabel
st.header("7. Korelasi Antarvariabel")

if len(data_numerik.columns) >= 2:
    korelasi = data_numerik.corr()

    fig, ax = plt.subplots(figsize=(10, 7))

    gambar = ax.imshow(
        korelasi,
        vmin=-1,
        vmax=1,
        aspect="auto"
    )

    ax.set_xticks(range(len(korelasi.columns)))
    ax.set_xticklabels(
        korelasi.columns,
        rotation=45,
        ha="right"
    )

    ax.set_yticks(range(len(korelasi.columns)))
    ax.set_yticklabels(korelasi.columns)

    ax.set_title("Matriks Korelasi")
    fig.colorbar(gambar, ax=ax)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# 8. Kesimpulan
st.header("8. Kesimpulan Awal")

st.write(f"Jumlah baris: {len(df)}")
st.write(f"Jumlah kolom: {len(df.columns)}")
st.write(
    f"Jumlah data duplikat: {df.duplicated().sum()}"
)
st.write(
    f"Jumlah seluruh nilai kosong: {df.isna().sum().sum()}"
)

if "Date" in df.columns and df["Date"].notna().any():
    st.write(
        f"Periode data: {df['Date'].min().date()} "
        f"sampai {df['Date'].max().date()}"
    )

st.caption(
    "Data Understanding dilakukan sebelum Data Preparation."
)
