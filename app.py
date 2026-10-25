from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ======================================================================
# KONFIGURASI HALAMAN
# ======================================================================
st.set_page_config(
    page_title="Dashboard Makro & Pasar Keuangan Indonesia",
    page_icon="📈",
    layout="wide",
)

DATA_FILE = "data/clean/data_clean.csv"
REQUIRED = [
    "Date", "OIL", "GOLD", "USDIDR", "SP500", "IHSG", "VIX", "BI_rate",
    "IHSG_ret", "SP500_ret", "SP500_ret_lag1", "USDIDR_ret", "GOLD_ret",
    "OIL_chg", "VIX_chg", "BI_rate_chg", "BI_event", "spread_BI_US", "VIX_lag1",
]
LABEL = {
    "IHSG": "IHSG", "SP500": "S&P 500", "GOLD": "Emas (USD)",
    "OIL": "Minyak (USD)", "USDIDR": "USD/IDR", "VIX": "VIX",
}
TEMPLATE = "plotly_white"


def show(fig):
    """Tampilkan grafik Plotly (kompatibel dengan berbagai versi Streamlit)."""
    fig.update_layout(template=TEMPLATE, margin=dict(l=10, r=10, t=50, b=10))
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


# ======================================================================
# LOAD DATA
# ======================================================================
@st.cache_data(show_spinner=False)
def load_data(source):
    d = pd.read_csv(source, parse_dates=["Date"])
    return d.sort_values("Date").reset_index(drop=True)


try:
    df = load_data(DATA_FILE)
except FileNotFoundError:
    up = st.sidebar.file_uploader("Upload data_clean.csv", type="csv")
    if up is None:
        st.title("📈 Dashboard Makro & Pasar Keuangan Indonesia")
        st.warning(
            f"File `{DATA_FILE}` tidak ditemukan di folder yang sama dengan app.py. "
            "Letakkan file di folder tersebut atau upload lewat sidebar."
        )
        st.stop()
    df = load_data(up)

missing_cols = [c for c in REQUIRED if c not in df.columns]
if missing_cols:
    st.error(f"Kolom berikut tidak ada di file: {missing_cols}. Gunakan data hasil cleaning.")
    st.stop()

min_d, max_d = df["Date"].min().date(), df["Date"].max().date()

# ======================================================================
# SIDEBAR (FILTER INTERAKTIF)
# ======================================================================
st.sidebar.title("⚙️ Filter Dashboard")

PRESET = {
    "Seluruh periode": (min_d, max_d),
    "Taper tantrum 2013": (date(2013, 5, 1), date(2013, 12, 31)),
    "COVID-19 (2020)": (date(2020, 1, 1), date(2020, 12, 31)),
    "Pengetatan global 2022-2023": (date(2022, 1, 1), date(2023, 12, 31)),
    "2025 - sekarang": (date(2025, 1, 1), max_d),
}
pilihan = st.sidebar.selectbox("Periode cepat", list(PRESET) + ["Kustom"])

if pilihan == "Kustom":
    rentang = st.sidebar.date_input(
        "Rentang tanggal", value=(min_d, max_d), min_value=min_d, max_value=max_d
    )
    if not isinstance(rentang, (tuple, list)) or len(rentang) != 2:
        st.info("Pilih tanggal awal dan tanggal akhir pada sidebar.")
        st.stop()
    start, end = rentang
else:
    start, end = PRESET[pilihan]
start, end = max(start, min_d), min(end, max_d)

pilih_aset = st.sidebar.multiselect(
    "Aset pada grafik tren",
    options=list(LABEL),
    default=["IHSG", "SP500", "GOLD", "USDIDR"],
    format_func=lambda x: LABEL[x],
)
pakai_log = st.sidebar.checkbox("Skala logaritmik (grafik tren)", value=False)

st.sidebar.caption(f"Data tersedia: {min_d} s/d {max_d}")

fdf = df[(df["Date"] >= pd.Timestamp(start)) & (df["Date"] <= pd.Timestamp(end))].copy()
if len(fdf) < 30:
    st.warning("Rentang terlalu pendek (minimal sekitar 30 hari bursa). Perlebar rentang tanggal.")
    st.stop()

# ======================================================================
# HEADER + KPI
# ======================================================================
st.title("📈 Dashboard Makroekonomi & Pasar Keuangan Indonesia")
st.caption(
    f"Periode terpilih: **{start}** s/d **{end}** ({len(fdf):,} hari bursa) · "
    "Aset: IHSG, S&P 500, emas, minyak, USD/IDR, VIX · Makro: BI Rate, selisih suku bunga BI-AS"
)


def chg_pct(col):
    return (fdf[col].iloc[-1] / fdf[col].iloc[0] - 1) * 100


k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("IHSG", f"{fdf['IHSG'].iloc[-1]:,.0f}", f"{chg_pct('IHSG'):+.1f}%")
k2.metric("USD/IDR", f"{fdf['USDIDR'].iloc[-1]:,.0f}", f"{chg_pct('USDIDR'):+.1f}%", delta_color="inverse")
k3.metric("Emas (USD)", f"{fdf['GOLD'].iloc[-1]:,.0f}", f"{chg_pct('GOLD'):+.1f}%")
k4.metric(
    "BI Rate", f"{fdf['BI_rate'].iloc[-1]:.2f}%",
    f"{fdf['BI_rate'].iloc[-1] - fdf['BI_rate'].iloc[0]:+.2f} pp", delta_color="off",
)
k5.metric(
    "VIX", f"{fdf['VIX'].iloc[-1]:.1f}",
    f"{fdf['VIX'].iloc[-1] - fdf['VIX'].iloc[0]:+.1f}", delta_color="inverse",
)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Tren Aset", "🔗 Korelasi", "🏦 BI Rate & IHSG", "🌪️ Rezim VIX",
    "💱 Spread & Rupiah", "💰 Simulasi Investasi", "🗂️ Data",
])

# ======================================================================
# TAB 1 - TREN ASET (dinormalisasi)
# ======================================================================
with tab1:
    st.subheader("Perbandingan Kinerja Aset (awal periode = 100)")
    if not pilih_aset:
        st.info("Pilih minimal satu aset pada sidebar.")
    else:
        base = fdf.set_index("Date")[pilih_aset]
        norm = (base / base.iloc[0] * 100).rename(columns=LABEL)
        fig = px.line(norm, labels={"value": "Indeks (awal = 100)", "Date": "Tanggal", "variable": "Aset"})
        fig.update_yaxes(type="log" if pakai_log else "linear")
        fig.update_layout(hovermode="x unified", title="Pergerakan relatif aset")
        show(fig)

        perf = (norm.iloc[-1] - 100).sort_values(ascending=False)
        ihsg = fdf.set_index("Date")["IHSG"]
        dd = ihsg / ihsg.cummax() - 1
        st.info(
            f"💡 **Insight:** Pada periode ini **{perf.index[0]}** memberi perubahan tertinggi "
            f"({perf.iloc[0]:+.1f}%), sedangkan **{perf.index[-1]}** terendah ({perf.iloc[-1]:+.1f}%). "
            f"Penurunan terdalam IHSG dari puncaknya mencapai **{dd.min() * 100:.1f}%** "
            f"(titik terendah {dd.idxmin().date()}). "
            "Catatan: kenaikan USD/IDR berarti rupiah melemah."
        )

# ======================================================================
# TAB 2 - KORELASI
# ======================================================================
with tab2:
    st.subheader("Korelasi Return Harian")
    RET = {
        "IHSG_ret": "IHSG", "SP500_ret": "S&P500 (hari sama)", "SP500_ret_lag1": "S&P500 (lag 1 hari)",
        "USDIDR_ret": "USD/IDR", "GOLD_ret": "Emas", "OIL_chg": "Minyak (Δ)", "VIX_chg": "VIX (Δ)",
    }
    corr = fdf[list(RET)].rename(columns=RET).corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
    fig.update_layout(title="Matriks korelasi (return/perubahan harian)")
    show(fig)

    c_lag = fdf["IHSG_ret"].corr(fdf["SP500_ret_lag1"])
    c_same = fdf["IHSG_ret"].corr(fdf["SP500_ret"])
    if abs(c_lag) > abs(c_same):
        kalimat = (
            "korelasi IHSG dengan return S&P 500 **hari sebelumnya** lebih kuat daripada hari yang sama. "
            "Ini wajar karena bursa Indonesia tutup sebelum Wall Street buka, sehingga IHSG baru merespons "
            "pergerakan AS keesokan harinya."
        )
    else:
        kalimat = "korelasi IHSG dengan S&P 500 hari yang sama sama kuat atau lebih kuat daripada dengan lag 1 hari."
    st.info(
        f"💡 **Insight:** Pada periode ini korelasi IHSG–S&P 500 (lag 1 hari) = **{c_lag:.2f}**, "
        f"hari yang sama = **{c_same:.2f}**; {kalimat}"
    )

    st.markdown("#### Korelasi bergulir (rolling): apakah hubungan berubah dari waktu ke waktu?")
    r1, r2 = st.columns(2)
    PAIR = {
        "SP500_ret_lag1": "S&P 500 (lag 1 hari)", "SP500_ret": "S&P 500 (hari sama)",
        "USDIDR_ret": "USD/IDR", "GOLD_ret": "Emas", "VIX_chg": "VIX (Δ)",
    }
    xcol = r1.selectbox("Bandingkan IHSG dengan", list(PAIR), format_func=lambda x: PAIR[x])
    win = r2.slider("Jendela rolling (hari bursa)", 30, 250, 90, step=10)
    pair = fdf[["Date", "IHSG_ret", xcol]].dropna().reset_index(drop=True)
    if len(pair) > win:
        pair["rolling"] = pair["IHSG_ret"].rolling(win).corr(pair[xcol])
        fig = px.line(pair, x="Date", y="rolling", labels={"rolling": "Korelasi", "Date": "Tanggal"})
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(title=f"Korelasi {win} hari: IHSG vs {PAIR[xcol]}")
        show(fig)
        rc = pair["rolling"].dropna()
        st.info(
            f"💡 **Insight:** Korelasi bergulir berkisar **{rc.min():.2f} s/d {rc.max():.2f}** "
            f"(rata-rata {rc.mean():.2f}). Hubungan antar aset tidak tetap; "
            "nilainya bergeser mengikuti kondisi pasar."
        )
    else:
        st.info("Periode terlalu pendek untuk jendela rolling ini. Perkecil jendela atau perlebar periode.")

# ======================================================================
# TAB 3 - EVENT STUDY BI RATE
# ======================================================================
with tab3:
    st.subheader("Reaksi IHSG terhadap Perubahan BI Rate (Event Study)")
    e1, e2 = st.columns(2)
    k = e1.slider("Jendela pengamatan (hari bursa sebelum/sesudah)", 1, 10, 5)
    excl = e2.checkbox("Kecualikan perubahan anomali (|Δ| ≥ 1 pp, mis. pergantian metode 2016)", value=True)

    ev = df[df["BI_event"] & df["Date"].between(pd.Timestamp(start), pd.Timestamp(end))]
    if excl:
        ev = ev[ev["BI_rate_chg"].abs() < 1]

    ret = df["IHSG_ret"].fillna(0).to_numpy()
    mu = df["IHSG_ret"].mean()
    rows, paths = [], {"Kenaikan": [], "Penurunan": []}
    for idx, r in ev.iterrows():
        if idx - k < 0 or idx + k >= len(df):
            continue
        ar = ret[idx - k: idx + k + 1] - mu  # abnormal return harian
        jenis = "Kenaikan" if r["BI_rate_chg"] > 0 else "Penurunan"
        paths[jenis].append(np.cumsum(ar))
        rows.append({
            "Tanggal": r["Date"].date(), "Jenis": jenis,
            "Δ BI Rate (pp)": r["BI_rate_chg"], "BI Rate (%)": r["BI_rate"],
            "CAR sebelum (%)": ar[:k].sum() * 100, "CAR sesudah (%)": ar[k:].sum() * 100,
        })

    if not rows:
        st.info("Tidak ada perubahan BI Rate pada periode terpilih. Perlebar rentang tanggal di sidebar.")
    else:
        fig = go.Figure()
        for jenis, arrs in paths.items():
            if arrs:
                fig.add_trace(go.Scatter(
                    x=list(range(-k, k + 1)), y=np.mean(arrs, axis=0) * 100,
                    mode="lines+markers", name=f"{jenis} (n={len(arrs)})",
                ))
        fig.add_vline(x=0, line_dash="dash", line_color="gray")
        fig.add_hline(y=0, line_color="lightgray")
        fig.update_layout(
            title="Rata-rata cumulative abnormal return IHSG di sekitar tanggal perubahan BI Rate",
            xaxis_title="Hari relatif terhadap perubahan (0 = tanggal perubahan)",
            yaxis_title="CAR (%)", hovermode="x unified",
        )
        show(fig)

        tbl = pd.DataFrame(rows)
        g = tbl.groupby("Jenis")["CAR sesudah (%)"].agg(["mean", "count"])
        teks = "; ".join(
            f"setelah **{j.lower()}** (n={int(r['count'])}) rata-rata **{r['mean']:+.2f}%**" for j, r in g.iterrows()
        )
        st.info(
            f"💡 **Insight:** Rata-rata abnormal return IHSG selama {k} hari bursa setelah perubahan: {teks}. "
            "Jumlah kejadian kecil, jadi baca sebagai indikasi, bukan bukti kausal."
        )
        with st.expander("Lihat tabel setiap kejadian"):
            st.dataframe(tbl.round(3), hide_index=True)

# ======================================================================
# TAB 4 - REZIM VIX
# ======================================================================
with tab4:
    st.subheader("Volatilitas IHSG pada Berbagai Rezim VIX")
    lo, hi = st.slider("Batas rezim VIX (tenang | normal | panik)", 10, 40, (15, 25))
    v = fdf[["Date", "IHSG_ret", "VIX_lag1", "VIX"]].dropna().copy()
    lab = [f"Tenang (≤{lo})", f"Normal ({lo}-{hi})", f"Panik (>{hi})"]
    v["Rezim"] = pd.cut(v["VIX_lag1"], [-np.inf, lo, hi, np.inf], labels=lab)
    v["Return IHSG (%)"] = v["IHSG_ret"] * 100

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.line(fdf, x="Date", y="VIX", labels={"Date": "Tanggal"})
        fig.add_hline(y=lo, line_dash="dot", line_color="green")
        fig.add_hline(y=hi, line_dash="dot", line_color="red")
        fig.update_layout(title="Indeks VIX dan batas rezim")
        show(fig)
    with col_b:
        fig = px.box(v, x="Rezim", y="Return IHSG (%)", color="Rezim", points=False,
                     category_orders={"Rezim": lab})
        fig.update_layout(title="Sebaran return harian IHSG per rezim", showlegend=False)
        show(fig)

    ringkas = v.groupby("Rezim", observed=True)["IHSG_ret"].agg(
        Hari="count", Rata2_Return_Harian="mean", Volatilitas_Harian="std"
    )
    ringkas["Hari Turun (%)"] = v.groupby("Rezim", observed=True)["IHSG_ret"].apply(lambda s: (s < 0).mean() * 100)
    ringkas["Rata2_Return_Harian"] *= 100
    ringkas["Volatilitas_Harian"] *= 100
    st.dataframe(ringkas.round(3).rename(columns={
        "Rata2_Return_Harian": "Rata-rata return harian (%)", "Volatilitas_Harian": "Volatilitas harian (%)"}))

    if lab[0] in ringkas.index and lab[2] in ringkas.index:
        rasio = ringkas.loc[lab[2], "Volatilitas_Harian"] / ringkas.loc[lab[0], "Volatilitas_Harian"]
        st.info(
            f"💡 **Insight:** Saat VIX hari sebelumnya berada di rezim panik, volatilitas harian IHSG "
            f"sekitar **{rasio:.1f}x** lebih besar daripada rezim tenang. "
            "VIX dapat dipakai sebagai indikator awal risiko pasar domestik."
        )
    else:
        st.info("Salah satu rezim tidak muncul pada periode ini. Ubah batas VIX atau perlebar periode.")

# ======================================================================
# TAB 5 - SPREAD BI vs US & RUPIAH
# ======================================================================
with tab5:
    st.subheader("Selisih Suku Bunga BI–AS dan Nilai Tukar Rupiah")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=fdf["Date"], y=fdf["spread_BI_US"], name="Spread BI−AS (pp)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=fdf["Date"], y=fdf["USDIDR"], name="USD/IDR"), secondary_y=True)
    fig.update_yaxes(title_text="Spread (pp)", secondary_y=False)
    fig.update_yaxes(title_text="USD/IDR", secondary_y=True)
    fig.update_layout(title="Spread suku bunga vs USD/IDR", hovermode="x unified")
    show(fig)

    sc = fdf.copy()
    sc["Tahun"] = sc["Date"].dt.year
    fig = px.scatter(sc, x="spread_BI_US", y="USDIDR", color="Tahun", opacity=0.6,
                     labels={"spread_BI_US": "Spread BI−AS (pp)", "USDIDR": "USD/IDR"},
                     color_continuous_scale="Viridis")
    fig.update_layout(title="Hubungan spread dan USD/IDR (warna = tahun)")
    show(fig)

    c_level = fdf["spread_BI_US"].corr(fdf["USDIDR"])
    bulanan = fdf.groupby(fdf["Date"].dt.to_period("M"))[["spread_BI_US", "USDIDR"]].last().diff().dropna()
    c_chg = bulanan["spread_BI_US"].corr(bulanan["USDIDR"]) if len(bulanan) >= 6 else np.nan
    if np.isnan(c_chg):
        tambahan = "Periode terlalu pendek untuk menghitung korelasi perubahan bulanan."
    elif abs(c_chg) < 0.2:
        tambahan = (
            f"Namun korelasi pada **perubahan bulanan** hanya **{c_chg:.2f}**, jadi korelasi level kemungkinan "
            "dipengaruhi tren yang sama (spurious), bukan hubungan sebab-akibat langsung."
        )
    else:
        tambahan = f"Korelasi pada **perubahan bulanan** juga **{c_chg:.2f}**, sehingga hubungan ini cukup konsisten."
    if c_level <= -0.3:
        arah = "spread menyempit cenderung bersamaan dengan rupiah melemah"
    elif c_level >= 0.3:
        arah = "spread melebar cenderung bersamaan dengan rupiah melemah"
    else:
        arah = "hubungan level keduanya lemah"
    st.info(
        f"💡 **Insight:** Korelasi level spread vs USD/IDR = **{c_level:.2f}** ({arah}). " + tambahan
    )

# ======================================================================
# TAB 6 - SIMULASI INVESTASI
# ======================================================================
with tab6:
    st.subheader("Simulasi: Jika Dulu Berinvestasi di Aset Ini...")
    s1, s2, s3 = st.columns(3)
    modal = s1.number_input("Modal awal (Rp)", min_value=100_000, value=10_000_000, step=1_000_000)
    d_buy_default = min(max(date(2020, 1, 2), min_d), max_d)
    buy = s2.date_input("Tanggal beli", value=d_buy_default, min_value=min_d, max_value=max_d)
    sell = s3.date_input("Tanggal jual", value=max_d, min_value=min_d, max_value=max_d)

    if buy >= sell:
        st.warning("Tanggal jual harus setelah tanggal beli.")
    else:
        sim = df[(df["Date"] >= pd.Timestamp(buy)) & (df["Date"] <= pd.Timestamp(sell))]
        aset = pd.DataFrame({
            "IHSG": sim["IHSG"].values,
            "Emas (dalam Rp)": (sim["GOLD"] * sim["USDIDR"]).values,
            "S&P 500 (dalam Rp)": (sim["SP500"] * sim["USDIDR"]).values,
            "Dolar AS": sim["USDIDR"].values,
        }, index=sim["Date"].values)
        nilai = aset / aset.iloc[0] * modal

        fig = px.line(nilai, labels={"value": "Nilai investasi (Rp)", "index": "Tanggal", "variable": "Aset"})
        fig.update_layout(title="Pertumbuhan nilai investasi", hovermode="x unified")
        show(fig)

        tahun = max((sim["Date"].iloc[-1] - sim["Date"].iloc[0]).days / 365.25, 1e-9)
        hasil = pd.DataFrame({
            "Nilai akhir (Rp)": nilai.iloc[-1],
            "Return total (%)": (nilai.iloc[-1] / modal - 1) * 100,
            "Return per tahun (%)": ((nilai.iloc[-1] / modal) ** (1 / tahun) - 1) * 100,
            "Penurunan maksimum (%)": (nilai / nilai.cummax() - 1).min() * 100,
        })
        st.dataframe(hasil.round(1).style.format({
            "Nilai akhir (Rp)": "{:,.0f}", "Return total (%)": "{:+.1f}",
            "Return per tahun (%)": "{:+.1f}", "Penurunan maksimum (%)": "{:.1f}"}))

        terbaik = hasil["Return total (%)"].idxmax()
        terburuk_dd = hasil["Penurunan maksimum (%)"].idxmin()
        st.info(
            f"💡 **Insight:** Dari {buy} sampai {sell}, aset dengan return tertinggi adalah **{terbaik}** "
            f"({hasil.loc[terbaik, 'Return total (%)']:+.1f}%), sedangkan penurunan sementara terdalam "
            f"terjadi pada **{terburuk_dd}** ({hasil.loc[terburuk_dd, 'Penurunan maksimum (%)']:.1f}%). "
            "Aset dalam dolar ikut dipengaruhi pergerakan kurs."
        )
        st.caption(
            "Simulasi historis sederhana: tidak memasukkan dividen, biaya transaksi, pajak, maupun selisih "
            "harga beli-jual. Ini bukan rekomendasi investasi."
        )

# ======================================================================
# TAB 7 - DATA
# ======================================================================
with tab7:
    st.subheader("Data pada Periode Terpilih")
    st.dataframe(fdf, hide_index=True)
    st.download_button(
        "⬇️ Unduh data terfilter (CSV)",
        fdf.to_csv(index=False).encode("utf-8"),
        file_name="data_terfilter.csv",
        mime="text/csv",
    )
    with st.expander("Statistik deskriptif"):
        st.dataframe(fdf.drop(columns="Date").describe().T)

with st.expander("ℹ️ Catatan metodologi"):
    st.markdown(
        """
- **Return** dihitung dari perubahan harga harian; hari libur bursa dibiarkan kosong (NaN) agar tidak menghasilkan return nol palsu.
- **Event study:** *abnormal return* = return IHSG dikurangi rata-rata return harian seluruh data; CAR adalah akumulasinya.
  Tanggal perubahan BI Rate di data kemungkinan tanggal efektif, bukan tanggal pengumuman RDG.
- **Korelasi level** (harga/spread) rentan menyesatkan pada data time series; gunakan korelasi return atau perubahan.
- Data hanya mencatat **perubahan** BI Rate, sehingga keputusan RDG "tahan" tidak dapat dianalisis.
        """
    )
