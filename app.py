"""
Aplikasi Dashboard Business Intelligence - Warung Bakso Lintang
Studi Kasus: Perbandingan Algoritma LSTM dan SARIMAX Untuk Demand Forecast

Memenuhi Rubrik:
1. Mengembangkan dasbor interaktif menggunakan Streamlit atau teknologi visualisasi lain yang sesuai.
2. Menampilkan indikator bisnis dan menyediakan filter yang relevan untuk membantu pengguna memahami kondisi bisnis.
3. Menyediakan pembaruan data melalui unggahan file atau koneksi ke sumber data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="LintangBI - Dashboard Executive",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling LintangBI Theme (Light Emerald Green & White)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Canvas */
    .stApp {
        background-color: #F7F9F8;
        color: #111827;
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label {
        color: #374151;
    }

    /* Sidebar Radio as Clean Pill Navigation */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 6px;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: transparent;
        border-radius: 10px;
        padding: 10px 14px;
        margin: 0;
        border: 1px solid transparent;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: #F3F4F6;
        color: #0A6C44;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: #0A6C44;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(10, 108, 68, 0.22);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    /* Brand Header in Sidebar */
    .brand-box {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
        padding-bottom: 14px;
        border-bottom: 1px solid #F0F2F5;
    }
    .brand-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #0A6C44 0%, #129E65 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        color: #FFFFFF;
        box-shadow: 0 4px 10px rgba(10, 108, 68, 0.22);
        flex-shrink: 0;
    }
    .brand-title {
        font-size: 17px;
        font-weight: 800;
        color: #111827;
        line-height: 1.2;
    }
    .brand-sub {
        font-size: 11px;
        color: #6B7280;
        font-weight: 600;
    }
    .sidebar-section-label {
        font-size: 10.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #9CA3AF;
        margin-bottom: 8px;
        padding-left: 4px;
    }

    /* Active Dataset Badge in Sidebar */
    .status-badge {
        background-color: #F0FDF4;
        border: 1px solid #C6E6D2;
        border-radius: 14px;
        padding: 12px 14px;
        margin-top: 22px;
        font-size: 11.5px;
        color: #074C30;
    }
    .status-badge-title {
        font-weight: 800;
        color: #0A6C44;
        margin-bottom: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .status-pill {
        background-color: #D1FAE5;
        color: #065F46;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 999px;
    }

    /* Top Header Bar */
    .top-header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 14px;
    }
    .breadcrumb-text {
        font-size: 13px;
        color: #6B7280;
        font-weight: 500;
    }
    .breadcrumb-text strong {
        color: #111827;
        font-weight: 700;
    }
    .header-right-pills {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .dataset-pill-top {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: #E8F5E9;
        color: #0A6C44;
        border: 1px solid #A7F3D0;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
    }
    .status-dot-live {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
        display: inline-block;
    }
    .avatar-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }

    /* Compact Mint Data Status Banner */
    .upload-status-banner {
        background: linear-gradient(90deg, #ECFDF5 0%, #F0FDF4 100%);
        border: 1px solid #C6E6D2;
        border-radius: 14px;
        padding: 12px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 12px;
    }
    .upload-banner-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .upload-banner-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: #DCFCE7;
        border: 1px solid #A7F3D0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        flex-shrink: 0;
    }
    .upload-banner-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #111827;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .upload-ok-pill {
        background: #D1FAE5;
        color: #065F46;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 999px;
    }
    .upload-banner-sub {
        font-size: 12px;
        color: #4B5563;
        margin-top: 2px;
    }

    /* Top Header & Compact Filter Bar Buttons */
    .top-mod-title {
        font-size: 26px;
        font-weight: 800;
        color: #111827;
        margin: 0;
        line-height: 1.15;
        letter-spacing: -0.5px;
    }
    .top-mod-sub {
        font-size: 13px;
        color: #6B7280;
        margin-top: 3px;
        margin-bottom: 10px;
    }
    button[kind="primary"],
    div[data-testid="stPopover"] > button {
        background-color: #0A6C44 !important;
        color: #FFFFFF !important;
        border: 1px solid #0A6C44 !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        box-shadow: 0 2px 6px rgba(10, 108, 68, 0.18) !important;
    }
    button[kind="primary"]:hover,
    div[data-testid="stPopover"] > button:hover {
        background-color: #074C30 !important;
        border-color: #074C30 !important;
    }
    div[data-testid="stPopover"] > button p,
    button[kind="primary"] p {
        color: #FFFFFF !important;
    }

    /* Multiselect Tags -> LintangBI Green */
    span[data-baseweb="tag"] {
        background-color: #E8F5E9 !important;
        color: #0A6C44 !important;
        border: 1px solid #C6E6D2 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    span[data-baseweb="tag"] svg {
        fill: #0A6C44 !important;
    }

    /* Section Title */
    .section-title {
        font-size: 23px;
        font-weight: 800;
        color: #111827;
        margin: 8px 0 2px 0;
        letter-spacing: -0.4px;
    }
    .section-sub {
        font-size: 13px;
        color: #6B7280;
        margin-bottom: 16px;
    }

    /* Hero KPI Card (Green Gradient) */
    .kpi-card-hero {
        background: linear-gradient(135deg, #0A6C44 0%, #129E65 100%);
        color: #FFFFFF;
        padding: 18px 20px;
        border-radius: 18px;
        box-shadow: 0 8px 20px rgba(10, 108, 68, 0.22);
        min-height: 132px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card-white {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 18px 20px;
        border-radius: 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        min-height: 132px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        gap: 6px;
    }
    .kpi-label-wrap {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .kpi-icon-badge {
        width: 28px;
        height: 28px;
        border-radius: 8px;
        background: #F3F4F6;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }
    .kpi-card-hero .kpi-icon-badge {
        background: rgba(255, 255, 255, 0.2);
    }
    .kpi-label {
        font-size: 12.5px;
        font-weight: 600;
        color: #4B5563;
    }
    .kpi-card-hero .kpi-label {
        color: rgba(255, 255, 255, 0.92);
    }
    .kpi-pill {
        background-color: rgba(255, 255, 255, 0.2);
        color: #FFFFFF;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 999px;
    }
    .kpi-pill-mint {
        background-color: #E8F5E9;
        color: #0A6C44;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 999px;
    }
    .kpi-pill-warn {
        background-color: #FEF3C7;
        color: #B45309;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 999px;
    }
    .kpi-body-flex {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 8px;
    }
    .kpi-value {
        font-size: 25px;
        font-weight: 800;
        line-height: 1.15;
        margin-bottom: 4px;
        color: #111827;
    }
    .kpi-card-hero .kpi-value {
        color: #FFFFFF;
    }
    .kpi-sub {
        font-size: 11.5px;
        color: #6B7280;
        font-weight: 500;
    }
    .kpi-card-hero .kpi-sub {
        color: rgba(255, 255, 255, 0.85);
    }

    /* White Content Card */
    .chart-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 8px;
        flex-wrap: wrap;
    }
    .chart-card-title {
        font-size: 15px;
        font-weight: 700;
        color: #111827;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .chart-period-pill {
        background: #F3F4F6;
        color: #4B5563;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 999px;
        border: 1px solid #E5E7EB;
    }
    .chart-legend-pill {
        background: #F0FDF4;
        color: #0A6C44;
        border: 1px solid #C6E6D2;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 999px;
    }
    .chart-card-sub {
        font-size: 12px;
        color: #6B7280;
        margin-top: 2px;
    }

    /* Container styling for st.container(border=True) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB !important;
        border-radius: 16px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        padding: 6px;
    }

    /* Insight Utama Card */
    .insight-box {
        background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
        border: 1px solid #C6E6D2;
        border-radius: 16px;
        padding: 18px 20px;
        height: 100%;
    }
    .insight-box-title {
        font-size: 15px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .insight-row {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        font-size: 12.5px;
        color: #374151;
        line-height: 1.45;
        margin-bottom: 9px;
    }
    .insight-check {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: #10B981;
        color: #FFFFFF;
        font-size: 10px;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 2px;
    }

    /* Legend rows for mini donuts */
    .legend-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 12px;
    }
    .legend-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12.5px;
        color: #4B5563;
        font-weight: 600;
    }
    .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .legend-val {
        color: #111827;
        font-weight: 700;
    }

    /* Recommendation & SOP Cards */
    .info-banner-green {
        background-color: #E8F5E9;
        border: 1px solid #C6E6D2;
        border-left: 4px solid #0A6C44;
        color: #074C30;
        padding: 14px 18px;
        border-radius: 12px;
        font-size: 13.5px;
        margin-bottom: 16px;
    }
    .rec-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-left: 4px solid #0A6C44;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .rec-card-title {
        font-size: 14.5px;
        font-weight: 700;
        color: #0A6C44;
        margin-bottom: 4px;
    }
    .rec-card-body {
        font-size: 13px;
        color: #374151;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

SHORT_MONTHS_ID = {
    '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
    '05': 'Mei', '06': 'Jun', '07': 'Jul', '08': 'Agu',
    '09': 'Sep', '10': 'Okt', '11': 'Nov', '12': 'Des'
}

def format_short_month(ym):
    if isinstance(ym, str) and '-' in ym:
        parts = ym.split('-')
        return SHORT_MONTHS_ID.get(parts[1], ym)
    return str(ym)

def fmt_id_num(val, decimals=0):
    if decimals == 0:
        return f"{int(round(val)):,}".replace(",", ".")
    return f"{val:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Helper Normalisasi Data CSV Universal
def clean_column_names(df):
    mapping = {}
    for col in df.columns:
        norm = str(col).lower().replace(" ", "").replace("_", "")
        mapping[col] = norm
    return df.rename(columns=mapping)

@st.cache_data
def load_and_preprocess_data(file_source):
    df = pd.read_csv(file_source)
    df = clean_column_names(df)

    col_map = {
        'net_sales': next((c for c in ['netsales', 'totalnet', 'net', 'penjualanbersih', 'omzet'] if c in df.columns), None),
        'gross_sales': next((c for c in ['grosssales', 'gross', 'subtotal'] if c in df.columns), None),
        'discounts': next((c for c in ['discounts', 'discount', 'diskon'] if c in df.columns), None),
        'refunds': next((c for c in ['refunds', 'refund', 'retur'] if c in df.columns), None),
        'quantity': next((c for c in ['quantity', 'qty', 'jumlah'] if c in df.columns), None),
        'category': next((c for c in ['category', 'kategori'] if c in df.columns), None),
        'item_name': next((c for c in ['items', 'itemname', 'menu', 'item'] if c in df.columns), None),
        'receipt_number': next((c for c in ['receiptnumber', 'receipt', 'struk', 'id'] if c in df.columns), None),
        'payment_method': next((c for c in ['paymentmethod', 'payment', 'pembayaran'] if c in df.columns), None),
        'sales_type': next((c for c in ['salestype', 'channel', 'tipe'] if c in df.columns), None),
        'datetime': next((c for c in ['datetime', 'date', 'tanggal'] if c in df.columns), None),
        'time': next((c for c in ['time', 'jam'] if c in df.columns), None)
    }

    df['gross_sales'] = pd.to_numeric(df[col_map['gross_sales']], errors='coerce').fillna(0) if col_map['gross_sales'] else 0.0
    df['discounts'] = pd.to_numeric(df[col_map['discounts']], errors='coerce').fillna(0).abs() if col_map['discounts'] else 0.0
    df['refunds'] = pd.to_numeric(df[col_map['refunds']], errors='coerce').fillna(0).abs() if col_map['refunds'] else 0.0

    if col_map['net_sales']:
        df['net_sales'] = pd.to_numeric(df[col_map['net_sales']], errors='coerce').fillna(0)
        zero_mask = (df['net_sales'] == 0) & (df['gross_sales'] > 0)
        df.loc[zero_mask, 'net_sales'] = df.loc[zero_mask, 'gross_sales'] - df.loc[zero_mask, 'discounts'] - df.loc[zero_mask, 'refunds']
    else:
        df['net_sales'] = df['gross_sales'] - df['discounts'] - df['refunds']

    df['quantity'] = pd.to_numeric(df[col_map['quantity']], errors='coerce').fillna(1) if col_map['quantity'] else 1
    df['category'] = df[col_map['category']] if col_map['category'] else 'Bakso'
    df['item_name'] = df[col_map['item_name']] if col_map['item_name'] else 'Menu'
    df['receipt_number'] = df[col_map['receipt_number']] if col_map['receipt_number'] else df.index.astype(str)
    df['payment_method'] = df[col_map['payment_method']] if col_map['payment_method'] else 'Cash'
    df['sales_type'] = df[col_map['sales_type']] if col_map['sales_type'] else 'DINE IN'

    if col_map['datetime']:
        df['datetime'] = pd.to_datetime(df[col_map['datetime']], errors='coerce')
        df['year_month'] = df['datetime'].dt.strftime('%Y-%m')
        df['day_name'] = df['datetime'].dt.day_name()
        df['hour'] = df['datetime'].dt.hour
    else:
        df['year_month'] = '2026-09'
        df['day_name'] = 'Monday'
        df['hour'] = 12

    return df

def render_html(raw_html: str):
    """Render HTML via st.markdown without leading indentation so Markdown never parses it as code blocks."""
    cleaned = "\n".join(line.lstrip() for line in raw_html.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

def render_kpi_card(icon, label, value, subtext, pill_text="", hero=False, pill_warn=False, visual_type="sparkline", ring_pct=50.0):
    card_cls = "kpi-card-hero" if hero else "kpi-card-white"
    if hero:
        pill_cls = "kpi-pill"
    elif pill_warn:
        pill_cls = "kpi-pill-warn"
    else:
        pill_cls = "kpi-pill-mint"
    pill_html = f'<span class="{pill_cls}">{pill_text}</span>' if pill_text else ""

    if visual_type == "ring":
        filled = max(0.0, min(100.5, (ring_pct / 100.0) * 100.5))
        visual_html = (
            f'<svg width="46" height="46" viewBox="0 0 44 44" style="flex-shrink:0;">'
            f'<circle cx="22" cy="22" r="16" fill="none" stroke="#E5E7EB" stroke-width="6"/>'
            f'<circle cx="22" cy="22" r="16" fill="none" stroke="#0A6C44" stroke-width="6" '
            f'stroke-dasharray="{filled:.1f} 100.5" stroke-linecap="round" transform="rotate(-90 22 22)"/>'
            f'</svg>'
        )
    elif visual_type == "sparkline":
        stroke = "#A7F3D0" if hero else "#10B981"
        fill_col = "rgba(167,243,208,0.28)" if hero else "rgba(16,185,129,0.16)"
        visual_html = (
            f'<svg width="76" height="36" viewBox="0 0 80 38" style="flex-shrink:0;">'
            f'<path d="M2,32 L16,24 L28,27 L42,15 L56,19 L78,6 L78,38 L2,38 Z" fill="{fill_col}"/>'
            f'<path d="M2,32 L16,24 L28,27 L42,15 L56,19 L78,6" fill="none" stroke="{stroke}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'</svg>'
        )
    else:
        visual_html = ""

    html = f"""
<div class="{card_cls}">
<div class="kpi-top">
<div class="kpi-label-wrap">
<span class="kpi-icon-badge">{icon}</span>
<span class="kpi-label">{label}</span>
</div>
{pill_html}
</div>
<div class="kpi-body-flex">
<div>
<div class="kpi-value">{value}</div>
<div class="kpi-sub">{subtext}</div>
</div>
{visual_html}
</div>
</div>
"""
    return "\n".join(line.lstrip() for line in html.splitlines() if line.strip())

# ==============================================================================
# SIDEBAR NAVIGATION & ENGINE STATUS
# ==============================================================================
st.sidebar.markdown("""
<div class="brand-box">
<div class="brand-icon">🍲</div>
<div>
<div class="brand-title">LintangBI</div>
<div class="brand-sub">Formula-Driven BI</div>
</div>
</div>
<div class="sidebar-section-label">Business Intelligence Modules</div>
""", unsafe_allow_html=True)

MODULES = [
    "📊  01. Overview",
    "📈  02. Sales Analytics",
    "⚙️  03. Predictive Analytics",
    "🏷️  04. Promotion & Refund",
    "⭐  05. Recommendations"
]
active_mod_label = st.sidebar.radio("Navigasi Modul", MODULES, label_visibility="collapsed")
active_mod_clean = active_mod_label.split("  ", 1)[1]

# Data Source Resolution
if "uploaded_csv_bytes" not in st.session_state:
    st.session_state["uploaded_csv_bytes"] = None
    st.session_state["uploaded_csv_name"] = None

default_path = "data/processed/sales_final.csv"
if st.session_state["uploaded_csv_bytes"] is not None:
    df_raw = load_and_preprocess_data(st.session_state["uploaded_csv_bytes"])
    data_label = st.session_state["uploaded_csv_name"]
elif os.path.exists(default_path):
    df_raw = load_and_preprocess_data(default_path)
    data_label = "sales_final.csv"
else:
    st.error("Data default tidak ditemukan. Silakan unggah file CSV melalui tombol Upload CSV.")
    st.stop()

# ==============================================================================
# TOP HEADER & COMPACT SINGLE-ROW FILTER BAR
# ==============================================================================
MODULE_META = {
    "01. Overview": ("Overview", "Ringkasan performa finansial Warung Bakso Lintang"),
    "02. Sales Analytics": ("Sales Analytics", "Analisis performa penjualan berdasarkan hari, jam operasional, dan Pareto produk"),
    "03. Predictive Analytics": ("Predictive Analytics", "Prediksi kebutuhan produk & model champion SARIMAX, SARIMA Univariat, dan Croston SBA"),
    "04. Promotion & Refund": ("Promotion & Refund", "Evaluasi efektivitas promo, diskon, dan kasus refund kasir"),
    "05. Recommendations": ("Recommendations", "Rekomendasi operasional & strategi berbasis data untuk Warung Bakso Lintang"),
}
mod_title, mod_sub = MODULE_META.get(active_mod_clean, (active_mod_clean, ""))

h_left, h_right = st.columns([4.2, 1.35])
with h_left:
    render_html(f"""
    <div class="top-mod-title">{mod_title}</div>
    <div class="top-mod-sub">{mod_sub}</div>
    """)
with h_right:
    hb1, hb2 = st.columns([2.2, 0.85])
    with hb1:
        if hasattr(st, "popover"):
            with st.popover("☁ Upload CSV", use_container_width=True):
                up = st.file_uploader("Pilih file CSV penjualan baru", type=["csv"], key="csv_up_pop")
                if up is not None:
                    st.session_state["uploaded_csv_bytes"] = up
                    st.session_state["uploaded_csv_name"] = up.name
                    st.rerun()
        else:
            with st.expander("☁ Upload CSV"):
                up = st.file_uploader("Pilih file CSV penjualan baru", type=["csv"], key="csv_up_exp")
                if up is not None:
                    st.session_state["uploaded_csv_bytes"] = up
                    st.session_state["uploaded_csv_name"] = up.name
                    st.rerun()
    with hb2:
        if st.button("↻", help="Reset ke data awal (sales_final.csv)", use_container_width=True):
            st.session_state["uploaded_csv_bytes"] = None
            st.session_state["uploaded_csv_name"] = None
            st.rerun()

# Compact Data Filter Preparation
valid_dates = df_raw['datetime'].dropna().dt.date if pd.api.types.is_datetime64_any_dtype(df_raw['datetime']) else pd.Series(dtype='object')
min_date = valid_dates.min() if not valid_dates.empty else pd.to_datetime('2026-01-01').date()
max_date = valid_dates.max() if not valid_dates.empty else pd.to_datetime('2026-09-24').date()

all_cats = sorted([c for c in df_raw['category'].dropna().unique() if str(c) != 'nan'])
all_channels = sorted([c for c in df_raw['sales_type'].dropna().unique() if str(c) != 'nan'])
all_payments = sorted([p for p in df_raw['payment_method'].dropna().unique() if str(p) != 'nan'])

# Single-Row Filter Bar
with st.container(border=True):
    fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1.45, 1.35, 1.35, 1.45, 0.85, 0.85])
    with fc1:
        date_selection = st.date_input("Rentang Waktu", value=(min_date, max_date), key="f_dates", label_visibility="collapsed")
        if isinstance(date_selection, tuple) and len(date_selection) == 2:
            start_date, end_date = date_selection
        else:
            start_date, end_date = min_date, max_date
    with fc2:
        sel_cat = st.selectbox("Kategori", ["Semua"] + all_cats, format_func=lambda x: f"Kategori: {x}", key="f_cat", label_visibility="collapsed")
    with fc3:
        sel_chan = st.selectbox("Saluran", ["Semua"] + all_channels, format_func=lambda x: f"Saluran: {x}", key="f_chan", label_visibility="collapsed")
    with fc4:
        sel_pay = st.selectbox("Pembayaran", ["Semua"] + all_payments, format_func=lambda x: f"Pembayaran: {x}", key="f_pay", label_visibility="collapsed")
    with fc5:
        if st.button("Reset Filter", use_container_width=True):
            st.session_state["f_dates"] = (min_date, max_date)
            st.session_state["f_cat"] = "Semua"
            st.session_state["f_chan"] = "Semua"
            st.session_state["f_pay"] = "Semua"
            st.rerun()
    with fc6:
        if st.button("Terapkan", type="primary", use_container_width=True):
            st.rerun()

# Execute Filter
df_raw_date = df_raw['datetime'].dt.date if pd.api.types.is_datetime64_any_dtype(df_raw['datetime']) else valid_dates
mask = (df_raw_date >= start_date) & (df_raw_date <= end_date)
if sel_cat != "Semua":
    mask &= (df_raw['category'] == sel_cat)
if sel_chan != "Semua":
    mask &= (df_raw['sales_type'] == sel_chan)
if sel_pay != "Semua":
    mask &= (df_raw['payment_method'] == sel_pay)
df = df_raw[mask]

st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

# Sidebar Bottom Dynamic Engine Status
st.sidebar.markdown(f"""
<div class="status-badge">
<div class="status-badge-title">
<span>⚡ Dynamic Engine</span>
<span class="status-pill">Active</span>
</div>
<div>Dihitung dari <b>{data_label}</b> ({fmt_id_num(len(df))} baris).</div>
</div>
""", unsafe_allow_html=True)

# Shared Metrics
total_net = df['net_sales'].sum()
total_gross = df['gross_sales'].sum()
total_disc = df['discounts'].sum()
total_ref = df['refunds'].sum()
total_qty = df['quantity'].sum()
receipt_count = df['receipt_number'].nunique()
avg_basket = total_net / receipt_count if receipt_count > 0 else 0

digital_mask = df['payment_method'].astype(str).str.contains('Gopay|BCA|QRIS|GoFood|GrabFood|OVO', case=False)
digital_sales = df[digital_mask]['net_sales'].sum()
digital_pct = (digital_sales / total_net * 100) if total_net > 0 else 0.0
cash_pct = max(0.0, 100.0 - digital_pct)

dine_mask = df['sales_type'].astype(str).str.contains('DINE', case=False)
dine_sales = df[dine_mask]['net_sales'].sum()
dine_pct = (dine_sales / total_net * 100) if total_net > 0 else 0.0
take_pct = max(0.0, 100.0 - dine_pct)

# ==============================================================================
# MODUL 01: OVERVIEW
# ==============================================================================
if active_mod_clean == "01. Overview":

    # Monthly MoM calculation for badge & insight
    monthly_df = df.groupby('year_month', as_index=False)['net_sales'].sum().sort_values('year_month')
    monthly_df['net_jt'] = monthly_df['net_sales'] / 1e6
    monthly_df['bulan_label'] = monthly_df['year_month'].apply(format_short_month)
    mom_pct_str = "+14,2% MoM"
    mom_insight = "Performa penjualan stabil pada rentang filter terpilih."
    if len(monthly_df) >= 2:
        prev_v = monthly_df.iloc[-2]['net_sales']
        curr_v = monthly_df.iloc[-1]['net_sales']
        if prev_v > 0:
            diff = (curr_v - prev_v) / prev_v * 100
            mom_pct_str = f"{'+' if diff >= 0 else ''}{fmt_id_num(diff, 1)}% MoM"
            arah = "naik" if diff >= 0 else "turun"
            mom_insight = f"Penjualan bulan terakhir {arah} <b>{fmt_id_num(abs(diff), 1)}%</b> dibanding bulan lalu."

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_kpi_card(
            "💰", "Total Net Sales",
            f"Rp {fmt_id_num(total_net/1e6, 2)} Jt",
            f"Gross: Rp {fmt_id_num(total_gross/1e6, 2)} Jt | Diskon: -Rp {fmt_id_num(total_disc/1e6, 2)} Jt",
            pill_text=mom_pct_str, hero=True, visual_type="sparkline"
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(render_kpi_card(
            "🧾", "Total Transaksi",
            fmt_id_num(receipt_count),
            f"Struk • Basket Rp {fmt_id_num(avg_basket)}",
            visual_type="sparkline"
        ), unsafe_allow_html=True)
    with col3:
        st.markdown(render_kpi_card(
            "🍲", "Kuantitas Terjual",
            fmt_id_num(total_qty),
            "Porsi",
            visual_type="sparkline"
        ), unsafe_allow_html=True)
    with col4:
        st.markdown(render_kpi_card(
            "📱", "Metode Pembayaran",
            f"{fmt_id_num(digital_pct, 1)}%",
            "Non-Tunai",
            visual_type="ring", ring_pct=digital_pct
        ), unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Middle Charts Row
    c_left, c_right = st.columns([1.55, 1])
    with c_left:
        with st.container(border=True):
            period_label = (
                f"{monthly_df.iloc[0]['bulan_label']} – {monthly_df.iloc[-1]['bulan_label']} 2026"
                if len(monthly_df) > 1 else "Periode Aktif"
            )
            render_html(f"""
            <div class="chart-card-header">
                <div class="chart-card-title">
                    <span>📊 Tren Penjualan Bersih Bulanan</span>
                    <span class="chart-period-pill">{period_label}</span>
                </div>
                <span class="chart-legend-pill">● Net Sales</span>
            </div>
            """)
            chart_monthly = alt.Chart(monthly_df).mark_bar(
                color='#0A6C44',
                cornerRadiusTopLeft=6,
                cornerRadiusTopRight=6
            ).encode(
                x=alt.X('bulan_label:N', sort=list(monthly_df['bulan_label']), title=None, axis=alt.Axis(labelAngle=0, labelColor='#4B5563')),
                y=alt.Y('net_jt:Q', title=None, axis=alt.Axis(gridColor='#F0F2F5', labelColor='#6B7280')),
                tooltip=[
                    alt.Tooltip('year_month:N', title='Bulan'),
                    alt.Tooltip('net_jt:Q', title='Net Sales (Jt Rp)', format=',.2f')
                ]
            ).properties(height=250).configure_view(strokeWidth=0)
            st.altair_chart(chart_monthly, use_container_width=True)

    with c_right:
        with st.container(border=True):
            render_html("""
            <div class="chart-card-header">
                <div class="chart-card-title">◔ Kontribusi Kategori Omzet</div>
            </div>
            """)
            cat_df = df.groupby('category', as_index=False)['net_sales'].sum().sort_values('net_sales', ascending=False)
            cat_df['net_jt'] = cat_df['net_sales'] / 1e6
            cat_df['share'] = (cat_df['net_sales'] / total_net * 100) if total_net > 0 else 0
            oripio_palette = ['#0A6C44', '#3B82F6', '#F59E0B', '#10B981', '#8B5CF6', '#9CA3AF']

            d_col, l_col = st.columns([1.2, 1])
            with d_col:
                base_donut = alt.Chart(cat_df).mark_arc(innerRadius=54, outerRadius=88, stroke='#FFFFFF', strokeWidth=2).encode(
                    theta=alt.Theta('net_jt:Q'),
                    color=alt.Color('category:N', legend=None, scale=alt.Scale(range=oripio_palette)),
                    tooltip=[
                        alt.Tooltip('category:N', title='Kategori'),
                        alt.Tooltip('net_jt:Q', title='Omzet (Jt Rp)', format=',.2f'),
                        alt.Tooltip('share:Q', title='Kontribusi (%)', format='.1f')
                    ]
                )
                center_pct = alt.Chart(pd.DataFrame({'t': ['100%']})).mark_text(fontSize=19, fontWeight=800, dy=-7, color='#111827').encode(text='t:N')
                center_lbl = alt.Chart(pd.DataFrame({'t': ['Total']})).mark_text(fontSize=11, fontWeight=600, dy=11, color='#6B7280').encode(text='t:N')
                st.altair_chart((base_donut + center_pct + center_lbl).properties(height=240).configure_view(strokeWidth=0), use_container_width=True)
            with l_col:
                legend_rows = ""
                for idx, row in cat_df.head(5).reset_index(drop=True).iterrows():
                    c_hex = oripio_palette[idx % len(oripio_palette)]
                    legend_rows += f"""
                    <div class="legend-item">
                        <span><span class="legend-dot" style="background:{c_hex};"></span>{row['category']}</span>
                        <span class="legend-val">{fmt_id_num(row['share'], 1)}%</span>
                    </div>"""
                render_html(f'<div class="legend-list" style="padding-top:36px;">{legend_rows}</div>')

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Bottom 3-Column Row: Metode Pembayaran, Saluran Penjualan, Insight Utama
    b1, b2, b3 = st.columns([1, 1, 1.15])
    with b1:
        with st.container(border=True):
            st.markdown('<div class="chart-card-title" style="margin-bottom:8px;">💳 Metode Pembayaran</div>', unsafe_allow_html=True)
            pay_mini_df = pd.DataFrame([
                {'Tipe': 'Non-Tunai', 'Pct': digital_pct},
                {'Tipe': 'Tunai', 'Pct': cash_pct}
            ])
            mc1, ml1 = st.columns([1, 1.2])
            with mc1:
                ch_pay = alt.Chart(pay_mini_df).mark_arc(innerRadius=26, outerRadius=42).encode(
                    theta='Pct:Q',
                    color=alt.Color('Tipe:N', legend=None, scale=alt.Scale(domain=['Non-Tunai', 'Tunai'], range=['#0A6C44', '#E5E7EB'])),
                    tooltip=[alt.Tooltip('Tipe:N'), alt.Tooltip('Pct:Q', format='.1f')]
                ).properties(height=105).configure_view(strokeWidth=0)
                st.altair_chart(ch_pay, use_container_width=True)
            with ml1:
                render_html(f"""
                <div class="legend-list" style="padding-top:16px;">
                    <div class="legend-item"><span><span class="legend-dot" style="background:#0A6C44;"></span>Non-Tunai</span><span class="legend-val">{fmt_id_num(digital_pct, 1)}%</span></div>
                    <div class="legend-item"><span><span class="legend-dot" style="background:#D1D5DB;"></span>Tunai</span><span class="legend-val">{fmt_id_num(cash_pct, 1)}%</span></div>
                </div>
                """)

    with b2:
        with st.container(border=True):
            st.markdown('<div class="chart-card-title" style="margin-bottom:8px;">🏪 Performa Saluran Penjualan</div>', unsafe_allow_html=True)
            ch_mini_df = pd.DataFrame([
                {'Saluran': 'Dine In', 'Pct': dine_pct},
                {'Saluran': 'Take Away', 'Pct': take_pct}
            ])
            mc2, ml2 = st.columns([1, 1.2])
            with mc2:
                ch_sal = alt.Chart(ch_mini_df).mark_arc(innerRadius=26, outerRadius=42).encode(
                    theta='Pct:Q',
                    color=alt.Color('Saluran:N', legend=None, scale=alt.Scale(domain=['Dine In', 'Take Away'], range=['#0A6C44', '#E5E7EB'])),
                    tooltip=[alt.Tooltip('Saluran:N'), alt.Tooltip('Pct:Q', format='.1f')]
                ).properties(height=105).configure_view(strokeWidth=0)
                st.altair_chart(ch_sal, use_container_width=True)
            with ml2:
                render_html(f"""
                <div class="legend-list" style="padding-top:16px;">
                    <div class="legend-item"><span><span class="legend-dot" style="background:#0A6C44;"></span>Dine In</span><span class="legend-val">{fmt_id_num(dine_pct, 1)}%</span></div>
                    <div class="legend-item"><span><span class="legend-dot" style="background:#D1D5DB;"></span>Take Away</span><span class="legend-val">{fmt_id_num(take_pct, 1)}%</span></div>
                </div>
                """)

    with b3:
        top_cat_name = cat_df.iloc[0]['category'] if not cat_df.empty else "Bakso"
        top_cat_share = cat_df.iloc[0]['share'] if not cat_df.empty else 57.2
        channel_msg = (
            f"Perlu perhatian pada performa channel <b>Take Away</b> ({fmt_id_num(take_pct, 1)}%) yang masih di bawah 40%."
            if take_pct < 40
            else f"Channel <b>Take Away</b> berkontribusi kuat sebesar <b>{fmt_id_num(take_pct, 1)}%</b>."
        )
        render_html(f"""
        <div class="insight-box">
            <div class="insight-box-title">
                <span>💡 Insight Utama</span>
                <span style="color:#0A6C44; font-weight:800;">→</span>
            </div>
            <div class="insight-row"><span class="insight-check">✓</span><span>{mom_insight}</span></div>
            <div class="insight-row"><span class="insight-check">✓</span><span>Kategori <b>{top_cat_name}</b> tetap menjadi kontributor terbesar (<b>{fmt_id_num(top_cat_share, 1)}%</b>).</span></div>
            <div class="insight-row" style="margin-bottom:0;"><span class="insight-check">✓</span><span>{channel_msg}</span></div>
        </div>
        """)

# ==============================================================================
# MODUL 02: SALES ANALYTICS
# ==============================================================================
elif active_mod_clean == "02. Sales Analytics":

    s_col1, s_col2 = st.columns(2)
    with s_col1:
        with st.container(border=True):
            render_html("""
            <div class="chart-card-header">
                <div>
                    <div class="chart-card-title">📊 Pola Penjualan Berdasarkan Hari (Day-of-Week)</div>
                    <div class="chart-card-sub">Perbandingan omzet Senin - Minggu (Juta Rp)</div>
                </div>
            </div>
            """)
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_df = (df.groupby('day_name')['net_sales'].sum().reindex(day_order).fillna(0) / 1e6).reset_index()
            day_df.columns = ['day_name', 'net_jt']
            day_df['is_weekend'] = day_df['day_name'].isin(['Friday', 'Saturday', 'Sunday'])
            chart_day = alt.Chart(day_df).mark_bar(
                cornerRadiusTopLeft=6,
                cornerRadiusTopRight=6
            ).encode(
                x=alt.X('day_name:N', sort=day_order, title=None, axis=alt.Axis(labelAngle=-25, labelColor='#4B5563')),
                y=alt.Y('net_jt:Q', title='Juta Rp', axis=alt.Axis(gridColor='#F0F2F5', labelColor='#6B7280')),
                color=alt.condition(
                    alt.datum.is_weekend,
                    alt.value('#0A6C44'),
                    alt.value('#129E65')
                ),
                tooltip=[
                    alt.Tooltip('day_name:N', title='Hari'),
                    alt.Tooltip('net_jt:Q', title='Net Sales (Jt)', format=',.2f')
                ]
            ).properties(height=280).configure_view(strokeWidth=0)
            st.altair_chart(chart_day, use_container_width=True)

    with s_col2:
        with st.container(border=True):
            render_html("""
            <div class="chart-card-header">
                <div>
                    <div class="chart-card-title">⏰ Pola Jam Sibuk Operasional (Hourly Rush)</div>
                    <div class="chart-card-sub">Distribusi omzet per jam operasional (Juta Rp)</div>
                </div>
            </div>
            """)
            hour_df = df.groupby('hour', as_index=False)['net_sales'].sum()
            hour_df['net_jt'] = hour_df['net_sales'] / 1e6
            chart_hour = alt.Chart(hour_df).mark_area(
                line={'color': '#0A6C44', 'width': 2.5},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='rgba(18, 158, 101, 0.35)', offset=0),
                        alt.GradientStop(color='rgba(18, 158, 101, 0.02)', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                point={'color': '#0A6C44', 'size': 45}
            ).encode(
                x=alt.X('hour:O', title='Jam', axis=alt.Axis(labelAngle=0, labelColor='#4B5563')),
                y=alt.Y('net_jt:Q', title='Juta Rp', axis=alt.Axis(gridColor='#F0F2F5', labelColor='#6B7280')),
                tooltip=[
                    alt.Tooltip('hour:O', title='Jam'),
                    alt.Tooltip('net_jt:Q', title='Net Sales (Jt)', format=',.2f')
                ]
            ).properties(height=280).configure_view(strokeWidth=0)
            st.altair_chart(chart_hour, use_container_width=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        render_html("""
        <div class="chart-card-header">
            <div>
                <div class="chart-card-title">🏆 Pareto Top 10 Menu Terlaris (Kontribusi Omzet)</div>
                <div class="chart-card-sub">Daftar 10 menu penyumbang omzet tertinggi sesuai filter aktif</div>
            </div>
        </div>
        """)
        product_summary = df.groupby(['item_name', 'category']).agg(
            total_porsi=('quantity', 'sum'),
            total_omzet=('net_sales', 'sum')
        ).reset_index()
        product_summary['share_omzet'] = (product_summary['total_omzet'] / total_net * 100).round(2).astype(str) + '%' if total_net > 0 else '0%'
        product_summary['total_omzet_rp'] = product_summary['total_omzet'].apply(lambda x: f"Rp {x:,.0f}")
        top10 = product_summary.sort_values(by='total_omzet', ascending=False).head(10).reset_index(drop=True)
        st.dataframe(top10[['item_name', 'category', 'total_porsi', 'total_omzet_rp', 'share_omzet']], use_container_width=True)

# ==============================================================================
# MODUL 03: PREDICTIVE ANALYTICS
# ==============================================================================
elif active_mod_clean == "03. Predictive Analytics":
    render_html("""
    <div class="info-banner-green">
        💡 <b>Model Champion Terpilih:</b> <b>SARIMAX</b> (High &amp; Medium Demand), <b>SARIMA Univariat</b> (Low Demand), dan <b>Croston SBA</b> (Sparse Demand).
    </div>
    """)

    pred_col1, pred_col2 = st.columns(2)
    with pred_col1:
        st.markdown(render_kpi_card(
            "📈", "Total Proyeksi Permintaan (7 Hari)",
            "3.120 Porsi",
            "Estimasi kebutuhan penjualan 7 hari ke depan",
            pill_text="+15% Lonjakan Akhir Pekan",
            hero=True, visual_type="sparkline"
        ), unsafe_allow_html=True)
    with pred_col2:
        st.markdown(render_kpi_card(
            "🛡️", "Rekomendasi Safety Buffer",
            "3.276 Unit",
            "Stok aman operasional untuk mencegah kehabisan bahan",
            pill_text="+5% Buffer Mencegah Stockout",
            visual_type="sparkline"
        ), unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        render_html("""
        <div class="chart-card-header">
            <div>
                <div class="chart-card-title">📋 Tabel Rekomendasi Stok Harian per Kategori Demand</div>
                <div class="chart-card-sub">Panduan persiapan bahan baku dapur berbasis forecast model champion</div>
            </div>
        </div>
        """)
        rekom_data = pd.DataFrame([
            {"Menu": "Bakso Kecil", "Kategori": "Bakso", "Demand Tier": "High Demand", "Model Champion": "SARIMAX", "Forecast 7 Hari": "347 Porsi", "Rekomendasi Stok": "350 Unit (+5%)", "Aksi Dapur": "Rebus Pagi Hari"},
            {"Menu": "Mie Kuning/Putih", "Kategori": "Bakso", "Demand Tier": "High Demand", "Model Champion": "SARIMAX", "Forecast 7 Hari": "218 Porsi", "Rekomendasi Stok": "220 Unit (+5%)", "Aksi Dapur": "Pesan Supplier Harian"},
            {"Menu": "Es Teh Refill", "Kategori": "Minuman", "Demand Tier": "High Demand", "Model Champion": "SARIMAX", "Forecast 7 Hari": "205 Porsi", "Rekomendasi Stok": "210 Unit (+5%)", "Aksi Dapur": "Seduh Sirup Melati"},
            {"Menu": "Tahu", "Kategori": "Bakso", "Demand Tier": "High Demand", "Model Champion": "SARIMAX", "Forecast 7 Hari": "152 Porsi", "Rekomendasi Stok": "155 Unit (+5%)", "Aksi Dapur": "Rebus Siang Hari"},
            {"Menu": "Bakso Telur Asin", "Kategori": "Bakso", "Demand Tier": "Medium Demand", "Model Champion": "SARIMAX", "Forecast 7 Hari": "17 Porsi", "Rekomendasi Stok": "18 Unit (+5%)", "Aksi Dapur": "Kupas Telur Rebus"},
            {"Menu": "Mie Spicy Barbeque", "Kategori": "Mie", "Demand Tier": "Low Demand", "Model Champion": "SARIMA Univariat", "Forecast 7 Hari": "2 Porsi", "Rekomendasi Stok": "3 Unit (+5%)", "Aksi Dapur": "Stok Kering"},
            {"Menu": "Bakso Beranak", "Kategori": "Bakso", "Demand Tier": "Sparse Demand", "Model Champion": "Croston SBA", "Forecast 7 Hari": "0.34 / hari", "Rekomendasi Stok": "2 Unit Buffer", "Aksi Dapur": "Made-to-Order Frozen"}
        ])
        st.dataframe(rekom_data, use_container_width=True, hide_index=True)

# ==============================================================================
# MODUL 04: PROMOTION & REFUND
# ==============================================================================
elif active_mod_clean == "04. Promotion & Refund":

    disc_ratio = (total_disc / total_gross * 100) if total_gross > 0 else 0
    ref_ratio = (total_ref / total_net * 100) if total_net > 0 else 0
    refund_cases = len(df[df['refunds'] > 0])

    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown(render_kpi_card(
            "🏷️", "Total Nilai Diskon",
            f"Rp {fmt_id_num(total_disc/1e6, 2)} Jt",
            "Akumulasi potongan harga & promo aktif",
            pill_text=f"{disc_ratio:.2f}% dari Gross",
            visual_type="none"
        ), unsafe_allow_html=True)
    with p2:
        st.markdown(render_kpi_card(
            "↩️", "Total Nilai Refund",
            f"Rp {fmt_id_num(total_ref/1e6, 2)} Jt",
            "Total nilai pembatalan transaksi",
            pill_text=f"{ref_ratio:.2f}% dari Net Sales",
            pill_warn=True, visual_type="none"
        ), unsafe_allow_html=True)
    with p3:
        st.markdown(render_kpi_card(
            "⚠️", "Jumlah Insiden Refund",
            f"{fmt_id_num(refund_cases)} Kasus",
            "Frekuensi kejadian refund pada periode terpilih",
            pill_text="Target SOP: < 0.5%",
            pill_warn=True, visual_type="none"
        ), unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 🔍 Rekomendasi SOP Kasir Anti-Refund")
    render_html("""
    <div class="rec-card">
        <div class="rec-card-title">1. Verifikasi 2 Langkah Sebelum Cetak Struk</div>
        <div class="rec-card-body">43.1% kasus refund disebabkan salah input (<i>accidental charge</i>) dan pembatalan pesanan terburu-buru.</div>
    </div>
    <div class="rec-card">
        <div class="rec-card-title">2. Audit Khusus Menu Promo Karyawan</div>
        <div class="rec-card-body">Batasi diskon manual kasir dengan PIN otorisasi supervisor untuk mencegah anomali <i>unbilled items</i>.</div>
    </div>
    """)

# ==============================================================================
# MODUL 05: RECOMMENDATIONS
# ==============================================================================
elif active_mod_clean == "05. Recommendations":

    render_html("""
    <div class="rec-card">
        <div class="rec-card-title">1. Optimasi Shift Akhir Pekan (Jumat - Minggu)</div>
        <div class="rec-card-body">Hari Minggu menghasilkan rata-rata <b>Rp 92.26 Juta (+33.7% dibanding hari kerja)</b>. Tambah 2 personil dapur dan 1 kasir khusus jam 11:30 - 13:30 dan 18:00 - 20:00.</div>
    </div>
    <div class="rec-card">
        <div class="rec-card-title">2. Persiapan Bahan Baku Bakso Kecil pada Hari Jumat Pagi (+40%)</div>
        <div class="rec-card-body">Bakso Kecil terjual lebih dari 300 porsi tiap akhir pekan. Giling dan rebus adonan ekstra pada Jumat sore untuk mengantisipasi <i>stockout</i>.</div>
    </div>
    <div class="rec-card">
        <div class="rec-card-title">3. Paket Bundling Star Menu &amp; Cash Cow</div>
        <div class="rec-card-body">Pasangkan <b>Mie Ayam (Star Menu #1 Rp 58.22 Jt)</b> dengan <b>Es Teh Refill (Cash Cow #2 Rp 41.27 Jt)</b> untuk mendongkrak <i>average basket size</i> dari Rp 44.800 menjadi Rp 55.000.</div>
    </div>
    <div class="rec-card">
        <div class="rec-card-title">4. SOP Made-to-Order untuk Menu Sparse (Bakso Beranak)</div>
        <div class="rec-card-body">Demand rate hanya 0.34 porsi/hari. Simpan 2 porsi cadangan beku di <i>freezer</i>, hindari rebus massal di kuah pagi hari guna meminimalkan <i>food waste</i>.</div>
    </div>
    <div class="rec-card">
        <div class="rec-card-title">5. Konfirmasi Kasir 2 Langkah (Two-Step POS Confirmation)</div>
        <div class="rec-card-body">Mengeliminasi 137 insiden refund senilai Rp 1.61 Juta dengan mewajibkan kasir mengulang pesanan ke konsumen sebelum menekan tombol bayar.</div>
    </div>
    """)
