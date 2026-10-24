import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st

import os
import numpy as np
import pandas as pd

# ====== 1. LOAD DATA ======
PATH_RAW = "data/raw/Macroeconomic_and_Financial__IndonesiaGlobal_Markets_.csv"
PATH_OUT = "data/processed/data_clean.csv"

df = pd.read_csv(PATH_RAW, parse_dates=["Date"])
df = df.sort_values("Date").drop_duplicates(subset="Date").reset_index(drop=True)
print("Ukuran awal:", df.shape)

price_cols = ["OIL", "GOLD", "USDIDR", "SP500", "IHSG", "VIX"]

# ====== 2. HAPUS BARIS KOSONG (hari libur global, mis. 2010-01-01) ======
market_cols = ["OIL", "GOLD", "SP500", "IHSG", "VIX"]
df = df.dropna(subset=market_cols, how="all").reset_index(drop=True)

# ====== 3. DETEKSI & PERBAIKI OUTLIER USDIDR ======
# Nilai yang menyimpang >5% dari median 11 hari sekitarnya dianggap error
med = df["USDIDR"].rolling(window=11, center=True, min_periods=3).median()
outlier_mask = (df["USDIDR"] / med - 1).abs() > 0.05

print("\nOutlier USDIDR yang diperbaiki:")
print(df.loc[outlier_mask, ["Date", "USDIDR"]].to_string())

df["USDIDR_outlier"] = outlier_mask
df.loc[outlier_mask, "USDIDR"] = np.nan
df["USDIDR"] = df["USDIDR"].interpolate(method="linear")

# ====== 4. TANDAI HARI LIBUR BURSA ======
# Harga identik dengan hari sebelumnya = hasil forward fill saat bursa tutup
df["IHSG_holiday"] = df["IHSG"].diff() == 0
df["US_holiday"] = df["SP500"].diff() == 0

# ====== 5. HITUNG RETURN ======
for c in ["IHSG", "SP500", "USDIDR", "GOLD"]:
    df[f"{c}_ret"] = np.log(df[c]).diff()      # log return

df["OIL_chg"] = df["OIL"].diff()               # selisih biasa (harga minyak pernah negatif)
df["VIX_chg"] = df["VIX"].diff()

# Return hari libur = NaN (bukan 0 palsu)
df.loc[df["IHSG_holiday"], "IHSG_ret"] = np.nan
df.loc[df["US_holiday"], ["SP500_ret", "VIX_chg"]] = np.nan

# ====== 6. VARIABEL KEBIJAKAN ======
df["BI_rate_chg"] = df["BI_rate"].diff().fillna(0)
df["BI_event"] = df["BI_rate_chg"] != 0        # True pada hari BI Rate berubah
df["US_rate_chg"] = df["US_rate"].diff().fillna(0)
df["spread_BI_US"] = df["BI_rate"] - df["US_rate"]

# ====== 7. LAG DATA AS (zona waktu: IHSG tutup sebelum AS buka) ======
df["SP500_ret_lag1"] = df["SP500_ret"].shift(1)
df["VIX_lag1"] = df["VIX"].shift(1)

# ====== 8. SIMPAN ======
os.makedirs(os.path.dirname(PATH_OUT), exist_ok=True)
df.to_csv(PATH_OUT, index=False)

# ====== 9. RINGKASAN ======
print("\nUkuran akhir:", df.shape)
print("Rentang tanggal:", df["Date"].min().date(), "->", df["Date"].max().date())
print("Hari libur IHSG:", df["IHSG_holiday"].sum(), "| Hari libur AS:", df["US_holiday"].sum())
print("Jumlah perubahan BI Rate:", df["BI_event"].sum())
print("\nMissing value per kolom:")
print(df.isna().sum()[lambda s: s > 0])