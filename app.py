import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =========================
# KONFIGURASI HALAMAN
# =========================
st.set_page_config(
    page_title="Dashboard Kota Depok",
    page_icon="🏙️",
    layout="wide"
)

DATA_PATH = Path(__file__).parent / "dataset_fiskal_97_hipoFull.csv"

# Nama kolom dan label yang lebih mudah dibaca
LABELS = {
    "DBH_PAJAK": "Dana Bagi Hasil Pajak",
    "DBH_SDA": "Dana Bagi Hasil Sumber Daya Alam",
    "DBH_Lainnya": "Dana Bagi Hasil Lainnya",
    "DAU_Grant": "DAU Grant",
    "DAU_Earmark": "DAU Earmark",
    "DAK_Fisik": "DAK Fisik",
    "DAK_Nonfisik": "DAK Nonfisik",
    "PAD": "Pendapatan Asli Daerah (PAD)",
    "ICT": "ICT",
    "bm_pendidikan": "Belanja Modal Pendidikan",
    "bm_kesehatan": "Belanja Modal Kesehatan",
    "bm_perumahan": "Belanja Modal Perumahan",
    "bm_lingkungan": "Belanja Modal Lingkungan",
    "bm_ekonomi": "Belanja Modal Ekonomi",
    "bm_infrastruktur": "Belanja Modal Infrastruktur",
    "bm_pariwisata": "Belanja Modal Pariwisata",
    "bm_perlindungan_sosial": "Belanja Modal Perlindungan Sosial",
    "KEMISKINAN": "Kemiskinan",
    "PENGANGGURAN": "Pengangguran",
    "KETIMPANGAN": "Ketimpangan",
    "IPM": "Indeks Pembangunan Manusia (IPM)",
    "PE": "Pertumbuhan Ekonomi (PE)"
}

FISCAL_COLUMNS = [
    "DBH_PAJAK", "DBH_SDA", "DBH_Lainnya", "DAU_Grant",
    "DAU_Earmark", "DAK_Fisik", "DAK_Nonfisik", "PAD", "ICT",
    "bm_pendidikan", "bm_kesehatan", "bm_perumahan",
    "bm_lingkungan", "bm_ekonomi", "bm_infrastruktur",
    "bm_pariwisata", "bm_perlindungan_sosial"
]

SOCIAL_COLUMNS = ["KEMISKINAN", "PENGANGGURAN", "KETIMPANGAN", "IPM", "PE"]


@st.cache_data
def load_data(path):
    data = pd.read_csv(path)
    data["Kota"] = data["Kota"].astype(str).str.strip()
    data["Tahun"] = pd.to_numeric(data["Tahun"], errors="coerce")
    return data


# =========================
# MEMBACA DAN MEMFILTER DATA
# =========================
st.title("🏙️ Dashboard Fiskal dan Sosial-Ekonomi Kota Depok")
st.caption("Analisis data tahunan Kota Depok berdasarkan dataset yang disediakan.")

if not DATA_PATH.exists():
    st.error(
        "File dataset tidak ditemukan. Pastikan "
        "'dataset_fiskal_97_hipoFull.csv' berada satu folder dengan app.py."
    )
    st.stop()

try:
    df_all = load_data(str(DATA_PATH))
except Exception as exc:
    st.error(f"Dataset gagal dibaca: {exc}")
    st.stop()

# Filter wajib: hanya Kota Depok
df_depok = df_all[
    df_all["Kota"].str.casefold().eq("kota depok".casefold())
].copy()

if df_depok.empty:
    st.error(
        "Data Kota Depok tidak ditemukan. Periksa penulisan nama kota "
        "pada kolom 'Kota' di file CSV."
    )
    st.stop()

df_depok = df_depok.sort_values("Tahun")
numeric_columns = df_depok.select_dtypes(include="number").columns.tolist()
available_fiscal = [c for c in FISCAL_COLUMNS if c in df_depok.columns]
available_social = [c for c in SOCIAL_COLUMNS if c in df_depok.columns]

# =========================
# SIDEBAR / FILTER
# =========================
st.sidebar.header("🔎 Filter Dashboard")
st.sidebar.info("Wilayah dikunci pada Kota Depok.")

years = sorted(df_depok["Tahun"].dropna().astype(int).unique().tolist())
if years:
    year_range = st.sidebar.slider(
        "Pilih rentang tahun",
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(int(min(years)), int(max(years))),
        step=1
    )
    filtered = df_depok[
        df_depok["Tahun"].between(year_range[0], year_range[1])
    ].copy()
else:
    filtered = df_depok.copy()

default_indicator = "PAD" if "PAD" in available_fiscal else (
    available_fiscal[0] if available_fiscal else numeric_columns[0]
)
all_indicators = [c for c in numeric_columns if c not in ["Tahun"]]
indicator_options = all_indicators

selected_indicator = st.sidebar.selectbox(
    "Pilih indikator untuk grafik tren",
    options=indicator_options,
    index=indicator_options.index(default_indicator)
        if default_indicator in indicator_options else 0,
    format_func=lambda x: LABELS.get(x, x.replace("_", " ").title())
)

# =========================
# KARTU RINGKASAN
# =========================
st.subheader("Ringkasan Data Kota Depok")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Jumlah baris terpilih", f"{len(filtered):,}".replace(",", "."))
c2.metric(
    "Periode awal",
    str(int(filtered["Tahun"].min())) if not filtered.empty else "-"
)
c3.metric(
    "Periode akhir",
    str(int(filtered["Tahun"].max())) if not filtered.empty else "-"
)
if "PAD" in filtered.columns and not filtered.empty:
    latest = filtered.sort_values("Tahun").iloc[-1]
    c4.metric("PAD pada tahun terakhir terpilih", f"{latest['PAD']:,.2f}")
else:
    c4.metric("Indikator terpilih", LABELS.get(selected_indicator, selected_indicator))

st.caption(
    "Angka mengikuti nilai dan satuan yang tercantum dalam dataset. "
    "Pastikan satuan setiap indikator dikonfirmasi dari sumber data."
)

# =========================
# GRAFIK TREN
# =========================
st.divider()
st.subheader("📈 Tren Indikator Tahunan")

trend_data = filtered[["Tahun", selected_indicator]].dropna().sort_values("Tahun")
if not trend_data.empty:
    trend_data["Tahun"] = trend_data["Tahun"].astype(int).astype(str)
    fig_trend = px.line(
        trend_data,
        x="Tahun",
        y=selected_indicator,
        markers=True,
        title=f"Tren {LABELS.get(selected_indicator, selected_indicator)} di Kota Depok",
        labels={
            "Tahun": "Tahun",
            selected_indicator: LABELS.get(selected_indicator, selected_indicator)
        },
        template="plotly_white"
    )
    fig_trend.update_layout(
        margin=dict(l=15, r=15, t=60, b=15),
        hovermode="x unified"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.warning("Tidak ada nilai untuk indikator dan rentang tahun yang dipilih.")

# =========================
# GRAFIK KEUANGAN / FISKAL
# =========================
st.divider()
st.subheader("💰 Perbandingan Indikator Fiskal")

fiscal_present = [c for c in available_fiscal if c in filtered.columns]
if fiscal_present and not filtered.empty:
    fiscal_year = st.selectbox(
        "Pilih tahun untuk membandingkan indikator fiskal",
        options=sorted(filtered["Tahun"].dropna().astype(int).unique().tolist()),
        key="fiscal_year"
    )
    one_year = filtered[filtered["Tahun"] == fiscal_year]
    fiscal_long = one_year[fiscal_present].melt(
        var_name="Indikator",
        value_name="Nilai"
    ).dropna()
    fiscal_long["Nama indikator"] = fiscal_long["Indikator"].map(
        lambda x: LABELS.get(x, x)
    )
    fig_fiscal = px.bar(
        fiscal_long.sort_values("Nilai", ascending=False),
        x="Nama indikator",
        y="Nilai",
        title=f"Perbandingan Indikator Fiskal Tahun {fiscal_year}",
        labels={"Nama indikator": "Indikator", "Nilai": "Nilai"},
        template="plotly_white"
    )
    fig_fiscal.update_layout(
        xaxis_tickangle=-35,
        margin=dict(l=15, r=15, t=60, b=100)
    )
    st.plotly_chart(fig_fiscal, use_container_width=True)
else:
    st.info("Kolom fiskal numerik tidak tersedia pada data terpilih.")

# =========================
# INDIKATOR SOSIAL-EKONOMI
# =========================
st.divider()
st.subheader("👥 Indikator Sosial-Ekonomi")

social_present = [c for c in available_social if c in filtered.columns]
if social_present and not filtered.empty:
    chosen_social = st.multiselect(
        "Pilih indikator sosial-ekonomi",
        options=social_present,
        default=[c for c in ["KEMISKINAN", "PENGANGGURAN", "IPM", "PE"]
                 if c in social_present],
        format_func=lambda x: LABELS.get(x, x)
    )
    if chosen_social:
        social_long = filtered[["Tahun"] + chosen_social].melt(
            id_vars="Tahun",
            var_name="Indikator",
            value_name="Nilai"
        ).dropna()
        social_long["Nama indikator"] = social_long["Indikator"].map(
            lambda x: LABELS.get(x, x)
        )
        fig_social = px.line(
            social_long,
            x="Tahun",
            y="Nilai",
            color="Nama indikator",
            markers=True,
            title="Perkembangan Indikator Sosial-Ekonomi",
            labels={"Tahun": "Tahun", "Nilai": "Nilai"},
            template="plotly_white"
        )
        fig_social.update_layout(margin=dict(l=15, r=15, t=60, b=15))
        st.plotly_chart(fig_social, use_container_width=True)
    else:
        st.info("Pilih minimal satu indikator untuk menampilkan grafik.")
else:
    st.info("Kolom sosial-ekonomi tidak tersedia pada data terpilih.")

# =========================
# TABEL DATA
# =========================
st.divider()
st.subheader("📋 Tabel Data Kota Depok")

with st.expander("Tampilkan tabel data", expanded=True):
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇️ Unduh data Kota Depok (CSV)",
        data=csv_bytes,
        file_name="data_kota_depok.csv",
        mime="text/csv"
    )

# =========================
# CATATAN SUMBER
# =========================
st.divider()
st.caption(
    "Sumber data: dataset_fiskal_97_hipoFull.csv yang disediakan pengguna. "
    "Dashboard memfilter kolom Kota menjadi 'Kota Depok'. "
    "Interpretasi indikator perlu mempertimbangkan definisi dan satuan dari sumber asli."
)
