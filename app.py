# app.py
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ------------------------------------------------------------------
# KONFIGURASI HALAMAN
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Makro & Pasar Keuangan Indonesia",
    page_icon="📈",
    layout="wide",
)
sns.set_theme(style="whitegrid")

DATA_PATH = "data_clean.csv"


# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
@st.cache_data
def load_data(src):
    df = pd.read_csv(src, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df


if os.path.exists(DATA_PATH):
    df_all = load_data(DATA_PATH)
else:
    up = st.file_uploader("Upload data_clean.csv", type="csv")
    if up is None:
        st.info("Letakkan data_clean.csv di folder yang sama dengan app.py, atau upload di sini.")
        st.stop()
    df_all = load_data(up)

# ------------------------------------------------------------------
# SIDEBAR (FILTER)
# ------------------------------------------------------------------
st.sidebar.header("⚙️ Filter")
min_d, max_d = df_all["Date"].min().date(), df_all["Date"].max().date()
date_range = st.sidebar.date_input(
    "Rentang tanggal", value=(min_d, max_d), min_value=min_d, max_value=max_d
)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = date_range
else:
    start, end = min_d, max_d

df = df_all[(df_all["Date"].dt.date >= start) & (df_all["Date"].dt.date <= end)].copy()
if len(df) < 60:
    st.warning("Data terlalu sedikit pada rentang ini. Perlebar rentang tanggal.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.caption(f"Jumlah observasi: **{len(df):,}** hari")

# ------------------------------------------------------------------
# HEADER & KPI
# ------------------------------------------------------------------
st.title("📈 Dashboard Makro & Pasar Keuangan Indonesia")
st.caption(f"Periode {start} s/d {end} · IHSG, S&P 500, USD/IDR, Emas, Minyak, VIX, Suku Bunga")

first, last = df.iloc[0], df.iloc[-1]
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("IHSG", f"{last['IHSG']:,.0f}", f"{(last['IHSG']/first['IHSG']-1)*100:+.1f}%")
k2.metric("USD/IDR", f"{last['USDIDR']:,.0f}", f"{(last['USDIDR']/first['USDIDR']-1)*100:+.1f}%")
k3.metric("S&P 500", f"{last['SP500']:,.0f}", f"{(last['SP500']/first['SP500']-1)*100:+.1f}%")
k4.metric("VIX (rata-rata)", f"{df['VIX'].mean():.1f}")
k5.metric("Spread BI–US", f"{last['spread_BI_US']:.2f} poin",
          f"{last['spread_BI_US']-first['spread_BI_US']:+.2f}")

tab0, tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 Overview", "🔍 Insight 1", "🔍 Insight 2", "🔍 Insight 3", "🗂️ Data"]
)

# ==================================================================
# TAB 0 — OVERVIEW (Visualisasi 1: Indeks ternormalisasi)
# ==================================================================
with tab0:
    st.subheader("Visualisasi 1 — Kinerja Relatif Aset (Basis 100)")
    options = ["IHSG", "SP500", "USDIDR", "GOLD", "OIL"]
    chosen = st.multiselect("Pilih aset", options, default=["IHSG", "SP500", "USDIDR", "GOLD"])
    if chosen:
        base = df.set_index("Date")[chosen]
        norm = base / base.iloc[0] * 100
        fig = px.line(norm, labels={"value": "Indeks (awal periode = 100)", "variable": "Aset"})
        fig.update_layout(hovermode="x unified", height=450, legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Catatan: harga minyak sempat negatif pada 20 April 2020, sehingga indeks OIL "
            "bisa terlihat ekstrem pada periode tersebut."
        )
    else:
        st.info("Pilih minimal satu aset.")

# ==================================================================
# TAB 1 — INSIGHT 1: Korelasi level vs return (Visualisasi 2 & 3)
# ==================================================================
with tab1:
    st.subheader("Insight 1 — Korelasi harga (level) menyesatkan dibanding korelasi return")

    level_cols = ["IHSG", "SP500", "USDIDR", "GOLD", "OIL", "VIX", "spread_BI_US"]
    ret_cols = ["IHSG_ret", "SP500_ret", "USDIDR_ret", "GOLD_ret", "OIL_chg", "VIX_chg"]

    corr_level = df[level_cols].corr()
    corr_ret = df[ret_cols].dropna().corr()

    st.markdown("**Visualisasi 2 — Heatmap korelasi: level vs return**")
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    sns.heatmap(corr_level, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1,
                ax=axes[0], cbar=False)
    axes[0].set_title("Korelasi LEVEL harga (terlihat sangat kuat)")
    sns.heatmap(corr_ret, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1,
                ax=axes[1])
    axes[1].set_title("Korelasi RETURN harian (jauh lebih lemah)")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("**Visualisasi 3 — Scatter return harian IHSG vs S&P 500**")
    sc = df.dropna(subset=["IHSG_ret", "SP500_ret"])
    beta, intercept = np.polyfit(sc["SP500_ret"], sc["IHSG_ret"], 1)
    fig2, ax = plt.subplots(figsize=(8, 5))
    sns.regplot(data=sc, x="SP500_ret", y="IHSG_ret",
                scatter_kws={"alpha": 0.25, "s": 12},
                line_kws={"color": "crimson"}, ax=ax)
    ax.set_xlabel("Return harian S&P 500")
    ax.set_ylabel("Return harian IHSG")
    ax.set_title(f"Beta IHSG terhadap S&P 500 ≈ {beta:.2f}")
    st.pyplot(fig2)
    plt.close(fig2)

    c_level = corr_level.loc["IHSG", "SP500"]
    c_ret = corr_ret.loc["IHSG_ret", "SP500_ret"]
    st.success(
        f"**Insight:** korelasi level IHSG–S&P 500 sebesar **{c_level:.2f}**, tetapi korelasi "
        f"return harian hanya **{c_ret:.2f}**. Kuatnya hubungan harga sebagian besar berasal dari "
        f"tren naik jangka panjang yang sama, bukan dari pergerakan harian yang searah. "
        f"Untuk analisis risiko atau pemodelan, gunakan return, bukan harga mentah."
    )

# ==================================================================
# TAB 2 — INSIGHT 2: VIX vs risiko IHSG (Visualisasi 4)
# ==================================================================
with tab2:
    st.subheader("Insight 2 — Saat VIX tinggi, volatilitas IHSG ikut melonjak")

    d = df.dropna(subset=["IHSG_ret", "VIX"]).copy()
    d["Regim VIX"] = pd.qcut(
        d["VIX"], 4, labels=["Q1 (rendah)", "Q2", "Q3", "Q4 (tinggi)"]
    )
    agg = (
        d.groupby("Regim VIX", observed=True)
        .agg(vol=("IHSG_ret", "std"), mean_ret=("IHSG_ret", "mean"), n=("IHSG_ret", "size"))
        .reset_index()
    )
    agg["vol"] *= 100
    agg["mean_ret"] *= 100

    st.markdown("**Visualisasi 4 — Volatilitas & rata-rata return IHSG per kuartil VIX**")
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Volatilitas harian IHSG (%)", "Rata-rata return harian IHSG (%)"),
    )
    fig.add_trace(go.Bar(x=agg["Regim VIX"], y=agg["vol"], marker_color="#E4572E",
                         text=agg["vol"].round(2), textposition="outside", name="Volatilitas"),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=agg["Regim VIX"], y=agg["mean_ret"],
                         marker_color=np.where(agg["mean_ret"] >= 0, "#2E86AB", "#A23B72"),
                         text=agg["mean_ret"].round(3), textposition="outside", name="Return"),
                  row=1, col=2)
    fig.update_layout(height=430, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    v_low, v_high = agg["vol"].iloc[0], agg["vol"].iloc[-1]
    r_high = agg["mean_ret"].iloc[-1]
    st.success(
        f"**Insight:** pada kuartil VIX tertinggi, volatilitas harian IHSG sekitar "
        f"**{v_high:.2f}%**, dibanding **{v_low:.2f}%** pada kuartil terendah, atau sekitar "
        f"**{v_high/v_low:.1f}x lipat**. Rata-rata return pada kondisi VIX tinggi adalah "
        f"**{r_high:.3f}%** per hari. VIX bisa dipakai sebagai indikator peringatan dini "
        f"risiko di pasar saham Indonesia."
    )

# ==================================================================
# TAB 3 — INSIGHT 3: Spread suku bunga vs USDIDR (Visualisasi 5)
# ==================================================================
with tab3:
    st.subheader("Insight 3 — Menyempitnya spread BI–US berjalan seiring melemahnya Rupiah")

    st.markdown("**Visualisasi 5 — USD/IDR vs spread suku bunga BI–US**")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df["Date"], y=df["USDIDR"], name="USD/IDR",
                             line=dict(color="#1f77b4")), secondary_y=False)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["spread_BI_US"], name="Spread BI–US (poin)",
                             line=dict(color="#ff7f0e")), secondary_y=True)
    fig.update_yaxes(title_text="USD/IDR", secondary_y=False)
    fig.update_yaxes(title_text="Spread BI–US (poin)", secondary_y=True)
    fig.update_layout(height=450, hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

    corr_sp = df["spread_BI_US"].corr(df["USDIDR"])
    sp_first, sp_last = df["spread_BI_US"].iloc[0], df["spread_BI_US"].iloc[-1]
    fx_first, fx_last = df["USDIDR"].iloc[0], df["USDIDR"].iloc[-1]
    st.success(
        f"**Insight:** korelasi spread BI–US dengan USD/IDR adalah **{corr_sp:.2f}** (negatif). "
        f"Pada periode terpilih spread bergerak dari **{sp_first:.2f}** ke **{sp_last:.2f}** poin, "
        f"sementara USD/IDR dari **{fx_first:,.0f}** ke **{fx_last:,.0f}**. Selisih imbal hasil yang "
        f"menipis mengurangi daya tarik aset rupiah. Ini hubungan asosiasi pada level, "
        f"bukan bukti sebab-akibat, karena faktor lain seperti inflasi dan arus modal ikut berperan."
    )

# ==================================================================
# TAB 4 — DATA
# ==================================================================
with tab4:
    st.subheader("Data terfilter")
    st.dataframe(df, use_container_width=True, height=400)
    st.download_button(
        "⬇️ Unduh CSV (hasil filter)",
        df.to_csv(index=False).encode("utf-8"),
        file_name="data_filtered.csv",
        mime="text/csv",
    )
    st.subheader("Statistik deskriptif")
    st.dataframe(df.describe().T, use_container_width=True)