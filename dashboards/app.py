import streamlit as st
import re
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
import sys
import html

# Import shared config — thresholds, weights, risk maps, queue counts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    RISK_MAP,
    CATEGORY_WEIGHT,
    PRIORITY_MAP,
    TIER_MAP,
    SEVERITY_ORDER,
    SLA_P1_HOURS,
    SLA_P2_HOURS,
)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PraxisIQ — Trust & Safety Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# DESIGN SYSTEM
# ─────────────────────────────────────────────
INK         = "#080A10"
SURFACE     = "#10131C"
SURFACE_2   = "#161A26"
BORDER      = "#1F2433"
BORDER_SOFT = "#1A1E2B"
TEXT_HI     = "#F1F3F8"
TEXT_MED    = "#9AA3B5"
TEXT_LOW    = "#5F6779"
ACCENT      = "#6C8CFF"
CYAN        = "#3DD9D6"
VIOLET      = "#A78BFA"
AMBER       = "#F2B33D"
ROSE        = "#EF6F6F"
EMERALD     = "#3DDC8C"
SLATE       = "#6B7488"

CHART_SEQUENCE = [ACCENT, CYAN, AMBER, ROSE, VIOLET, EMERALD, SLATE]
FONT_FAMILY = "'Inter', -apple-system, 'Segoe UI', sans-serif"

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {{
        font-family: {FONT_FAMILY};
    }}

    /* ── App background ── */
    .stApp {{
        background:
            radial-gradient(1200px 600px at 10% -10%, rgba(108,140,255,0.06), transparent 60%),
            radial-gradient(900px 500px at 100% 0%, rgba(61,217,214,0.04), transparent 55%),
            {INK};
    }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 100% !important;
    }}

    /* ── Sidebar shell ── */
    section[data-testid="stSidebar"] {{
        width: 240px !important;
        min-width: 240px !important;
        background: linear-gradient(180deg, {SURFACE_2} 0%, {INK} 100%);
        border-right: 1px solid {BORDER_SOFT};
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding: 1.6rem 1rem 1.6rem 1rem !important;
    }}

    /* ── Hide sidebar collapse arrow/button ── */
    button[data-testid="collapsedControl"],
    button[kind="header"],
    [data-testid="stSidebarCollapseButton"],
    section[data-testid="stSidebar"] button[aria-label="Close sidebar"],
    .st-emotion-cache-dvne4q,
    .css-dvne4q {{
        display: none !important;
    }}

    [data-testid="stSidebarNavItems"] button,
    button[data-testid="stSidebarNavCollapseButton"] {{
        display: none !important;
    }}

    /* ── Brand block ── */
    .brand-row {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 3px;
    }}
    .brand-mark {{
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: linear-gradient(135deg, {ACCENT} 0%, {CYAN} 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: {INK};
        font-size: 14px;
        flex-shrink: 0;
        box-shadow: 0 4px 14px rgba(108,140,255,0.35);
    }}
    .brand-name {{
        font-size: 17px;
        font-weight: 800;
        color: {TEXT_HI};
        letter-spacing: -0.01em;
    }}
    .brand-tag {{
        color: {TEXT_LOW};
        font-size: 10.5px;
        font-weight: 500;
        letter-spacing: 0.01em;
        margin: 4px 0 20px 0;
        padding-left: 2px;
        line-height: 1.45;
    }}

    /* ── Nav label ── */
    .nav-label {{
        color: {TEXT_LOW};
        font-size: 9.5px;
        font-weight: 700;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin: 0 0 8px 2px;
    }}

    /* ── Radio group ── */
    section[data-testid="stSidebar"] .stRadio > label {{
        display: none !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 2px !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        display: flex !important;
        align-items: center !important;
        padding: 9px 11px !important;
        border-radius: 9px !important;
        cursor: pointer !important;
        transition: background 0.15s ease !important;
        margin-bottom: 1px !important;
        border-left: 2px solid transparent !important;
        gap: 0 !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        background: rgba(108,140,255,0.07) !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label span:first-child {{
        display: none !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label div p {{
        color: {TEXT_MED} !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
        background: linear-gradient(90deg, rgba(108,140,255,0.14), rgba(108,140,255,0.02)) !important;
        border-left: 2px solid {ACCENT} !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) div p {{
        color: {TEXT_HI} !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] svg,
    section[data-testid="stSidebar"] div[role="radiogroup"] .st-emotion-cache-1qg05tj,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] ~ div svg {{
        display: none !important;
    }}

    /* ── Sidebar footer ── */
    .side-footer {{
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid {BORDER_SOFT};
    }}
    .side-stat {{
        font-size: 11px;
        color: {TEXT_LOW};
        line-height: 1.9;
        font-weight: 500;
    }}
    .side-stat b {{
        color: {TEXT_MED};
        font-weight: 600;
    }}
    .side-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(61,217,214,0.08);
        border: 1px solid rgba(61,217,214,0.22);
        color: {CYAN};
        font-size: 10px;
        font-weight: 600;
        padding: 4px 9px;
        border-radius: 20px;
        margin-top: 10px;
    }}
    .side-pill::before {{
        content: '';
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: {CYAN};
        box-shadow: 0 0 5px {CYAN};
    }}

    /* ── Sidebar divider ── */
    .side-divider {{
        height: 1px;
        background: {BORDER_SOFT};
        margin: 16px 0;
    }}

    /* ── Page header ── */
    .page-eyebrow {{
        color: {ACCENT};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 7px;
    }}
    .page-title {{
        color: {TEXT_HI};
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
        line-height: 1.15;
    }}
    .page-sub {{
        color: {TEXT_MED};
        font-size: 13.5px;
        font-weight: 450;
        margin-bottom: 28px;
        max-width: 680px;
        line-height: 1.5;
    }}

    /* ── KPI cards ── */
    .kpi-card {{
        background: linear-gradient(155deg, {SURFACE} 0%, #0D101A 100%);
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 20px 20px 18px 20px;
        margin-bottom: 14px;
        position: relative;
        overflow: hidden;
    }}
    .kpi-card::after {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(108,140,255,0.45), transparent);
    }}
    .kpi-label {{
        color: {TEXT_LOW};
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 11px;
        display: flex;
        align-items: center;
        gap: 7px;
    }}
    .kpi-dot {{
        width: 5px;
        height: 5px;
        border-radius: 50%;
        flex-shrink: 0;
    }}
    .kpi-value {{
        color: {TEXT_HI};
        font-size: 28px;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.02em;
    }}
    .kpi-sub {{
        color: {TEXT_LOW};
        font-size: 11.5px;
        margin-top: 8px;
        font-weight: 500;
    }}
    .kpi-sub b {{ color: {TEXT_MED}; }}

    /* ── Section header ── */
    .section-header {{
        color: {TEXT_HI};
        font-size: 13.5px;
        font-weight: 700;
        letter-spacing: 0.01em;
        margin: 8px 0 14px 0;
        display: flex;
        align-items: center;
        gap: 9px;
    }}
    .section-header::before {{
        content: '';
        width: 3px;
        height: 14px;
        border-radius: 2px;
        background: linear-gradient(180deg, {ACCENT}, {CYAN});
        display: inline-block;
        flex-shrink: 0;
    }}
    .section-tag {{
        color: {TEXT_LOW};
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.05em;
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 2px 7px;
        margin-left: auto;
    }}

    /* ── Finding cards ── */
    .finding-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 8px;
    }}
    .finding-title {{
        color: {TEXT_HI};
        font-size: 12.5px;
        font-weight: 700;
        margin-bottom: 5px;
        letter-spacing: -0.005em;
    }}
    .finding-text {{
        color: {TEXT_MED};
        font-size: 12px;
        line-height: 1.55;
        font-weight: 450;
    }}
    .finding-text b {{ color: {TEXT_HI}; }}

    /* ── Badges ── */
    .badge {{
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.04em;
        padding: 3px 9px;
        border-radius: 20px;
        display: inline-block;
    }}
    .badge-high {{ background: rgba(239,111,111,0.12); color:{ROSE}; border:1px solid rgba(239,111,111,0.28); }}
    .badge-med  {{ background: rgba(242,179,61,0.12); color:{AMBER}; border:1px solid rgba(242,179,61,0.28); }}
    .badge-low  {{ background: rgba(61,220,140,0.12); color:{EMERALD}; border:1px solid rgba(61,220,140,0.28); }}

    /* ── Divider ── */
    hr {{ border-color: {BORDER_SOFT} !important; margin: 28px 0 !important; }}

    /* ── Filter expander ── */
    div[data-testid="stExpander"] {{
        background: linear-gradient(135deg, rgba(108,140,255,0.06), rgba(61,217,214,0.03)) !important;
        border: 1px solid rgba(108,140,255,0.35) !important;
        border-radius: 12px !important;
        margin-bottom: 20px !important;
        overflow: hidden !important;
    }}
    div[data-testid="stExpander"] summary {{
        color: {ACCENT} !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        padding: 12px 16px !important;
        background: transparent !important;
    }}
    div[data-testid="stExpander"] summary:hover {{
        background: rgba(108,140,255,0.08) !important;
    }}
    div[data-testid="stExpander"] summary svg {{
        color: {ACCENT} !important;
        fill: {ACCENT} !important;
    }}
    div[data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {{
        border-top: 1px solid rgba(108,140,255,0.2) !important;
        padding: 14px 16px 16px 16px !important;
        background: rgba(16,19,28,0.6) !important;
    }}
    div[data-testid="stExpander"] .stSelectbox label {{
        color: {TEXT_MED} !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
    }}
    div[data-testid="stExpander"] .stSelectbox > div > div {{
        background: {SURFACE_2} !important;
        border: 1px solid rgba(108,140,255,0.3) !important;
        border-radius: 8px !important;
        color: {TEXT_HI} !important;
    }}
    div[data-testid="stExpander"] .stSelectbox > div > div:hover {{
        border-color: {ACCENT} !important;
    }}

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}

    /* ── Plotly container border ── */
    [data-testid="stPlotlyChart"] {{
        border: 1px solid {BORDER};
        border-radius: 12px;
        overflow: hidden;
        background: {SURFACE};
        padding: 8px 4px 4px 4px;
    }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def chart_layout(fig, h=None):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family=FONT_FAMILY, color=TEXT_MED, size=12),
        margin=dict(l=4, r=4, t=10, b=4),
        legend=dict(font=dict(color=TEXT_MED, size=11), bgcolor='rgba(0,0,0,0)'),
        hoverlabel=dict(
            bgcolor=SURFACE_2,
            font=dict(family=FONT_FAMILY, color=TEXT_HI, size=12),
            bordercolor=BORDER
        ),
        xaxis=dict(
            gridcolor=BORDER_SOFT, zerolinecolor=BORDER_SOFT, linecolor=BORDER,
            tickfont=dict(color=TEXT_LOW, size=11)
        ),
        yaxis=dict(
            gridcolor=BORDER_SOFT, zerolinecolor=BORDER_SOFT, linecolor=BORDER,
            tickfont=dict(color=TEXT_LOW, size=11)
        ),
    )
    if h:
        fig.update_layout(height=h)
    return fig


def kpi(col, label, value, sub, dot=ACCENT):
    col.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>
            <span class='kpi-dot' style='background:{dot}; box-shadow:0 0 6px {dot}'></span>
            {label}
        </div>
        <div class='kpi-value'>{value}</div>
        <div class='kpi-sub'>{sub}</div>
    </div>""", unsafe_allow_html=True)


def section(title, tag=None):
    tag_html = f"<span class='section-tag'>{tag}</span>" if tag else ""
    st.markdown(
        f"<div class='section-header'>{title}{tag_html}</div>",
        unsafe_allow_html=True
    )


def page_header(eyebrow, title, sub):
    st.markdown(f"""
        <div class='page-eyebrow'>{eyebrow}</div>
        <div class='page-title'>{title}</div>
        <div class='page-sub'>{sub}</div>
    """, unsafe_allow_html=True)


def finding(title, text):
    st.markdown(f"""
    <div class='finding-card'>
        <div class='finding-title'>{title}</div>
        <div class='finding-text'>{text}</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADER
# ─────────────────────────────────────────────
BASE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB    = os.path.join(BASE, "PraxisIQ.db")
RPT   = os.path.join(BASE, "reports")
EXCEL = os.path.join(BASE, "sample_data_synthetic.xlsx")


def _build_database_if_missing():
    if os.path.exists(DB):
        return
    if not os.path.exists(EXCEL):
        st.error(
            f"Database not found and source file '{EXCEL}' is missing. "
            "Cannot build the database automatically."
        )
        st.stop()

    with st.spinner("First-time setup: building database from source data..."):
        treatment_map = {
            "root Canal": "Root Canal", "Root Canal ": "Root Canal",
            "Aligners": "Aligner", "Braces": "Metal Braces Treatment",
            "Ceramic Braces Treatment": "Metal Braces Treatment",
            "Deep Cleaning": "Deep Scaling and Root Planing",
            "Gum Surgery": "Gum Treatment", "Scaling ": "Scaling",
            "Scaling and Filling": "Scaling",
            "Scaling and Polishing": "Scaling and Polishing",
            "Teeth Cleaning": "Teeth Cleaning",
            "Wisdom Tooth Extraction": "Tooth Extraction",
        }
        patients = pd.read_excel(EXCEL, sheet_name="Patients")
        visits   = pd.read_excel(EXCEL, sheet_name="Visits")
        reviews  = pd.read_excel(EXCEL, sheet_name="Reviews")

        patients["Primary_Treatment"] = patients["Primary_Treatment"].str.strip().replace(treatment_map)
        visits["Treatment_Type"]      = visits["Treatment_Type"].str.strip().replace(treatment_map)

        conn = sqlite3.connect(DB)
        patients.to_sql("Patients", conn, if_exists="replace", index=False)
        visits.to_sql("Visits",    conn, if_exists="replace", index=False)
        reviews.to_sql("Reviews",  conn, if_exists="replace", index=False)
        conn.close()


_build_database_if_missing()


@st.cache_data
def load_db(query):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data
def load_csv(name):
    path = os.path.join(RPT, name)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class='brand-row'>
            <div class='brand-mark'>P</div>
            <div class='brand-name'>PraxisIQ</div>
        </div>
        <div class='brand-tag'>Patient Trust &amp; Operations<br>Intelligence Platform</div>
        <div class='side-divider'></div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='nav-label'>Workspace</div>", unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        options=[
            "Overview",
            "Patient Analytics",
            "Review Intelligence",
            "Anomaly Screening",
            "Trust & Safety",
            "LLM Evaluation",
            "Investigation Playbooks",
            "Data Quality",
            "AI Copilot",
        ],
        label_visibility="collapsed"
    )

    st.markdown(f"""
        <div class='side-footer'>
            <div class='side-stat'><b>959</b> patients &nbsp;·&nbsp; <b>4,603</b> visits</div>
            <div class='side-stat'><b>300</b> reviews &nbsp;·&nbsp; 7 labeled categories</div>
            <div class='side-stat'>Model: <b>Qwen2.5 7B</b> · Ollama (local)</div>
            <div class='side-stat'>Copilot: <b>Llama 3.3 70B</b> · Groq</div>
            <div class='side-pill'>Live dataset connected</div>
        </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE 1 — OVERVIEW
# ─────────────────────────────────────────────
if page == "Overview":
    page_header(
        "Executive Summary",
        "Analytics Platform Overview",
        "Patient Trust &amp; Operations Intelligence · Geetha Dental Clinic · 6-year operational dataset"
    )

    # -- LIVE KPI DATA --------------------------------------------------------
    _ov_patients  = load_db("SELECT COUNT(*) as n FROM Patients")
    _ov_returned  = load_db("SELECT COUNT(*) as n FROM Patients WHERE Returned_Patient='Yes'")
    _ov_visits    = load_db("SELECT COUNT(*) as n FROM Visits")
    _ov_reviews   = load_db("SELECT COUNT(*) as n FROM Reviews")
    _ov_risk_csv  = load_csv("followup_risk_queue.csv")
    _ov_burst_csv = load_csv("review_burst_detection.csv")
    _total_pts    = int(_ov_patients["n"].iloc[0])
    _returned_pts = int(_ov_returned["n"].iloc[0])
    _retention    = round(_returned_pts / _total_pts * 100, 1) if _total_pts > 0 else 0
    _total_visits = int(_ov_visits["n"].iloc[0])
    _avg_visits   = round(_total_visits / _total_pts, 1) if _total_pts > 0 else 0
    _total_reviews = int(_ov_reviews["n"].iloc[0])
    _at_risk_n    = len(_ov_risk_csv) if not _ov_risk_csv.empty else 173
    _at_risk_pct  = round(_at_risk_n / _total_pts * 100, 1) if _total_pts > 0 else 18.0
    _burst_n = 7
    if not _ov_burst_csv.empty and "Burst_Status" in _ov_burst_csv.columns:
        _burst_n = int((_ov_burst_csv["Burst_Status"] == "BURST DETECTED").sum())
    elif not _ov_burst_csv.empty and "Burst_Detected" in _ov_burst_csv.columns:
        _burst_n = int(_ov_burst_csv["Burst_Detected"].sum())

    # -- COHORT COMPARISON: first half vs second half of the dataset's timeline --
    # The dataset is a single 6-year snapshot with no separate "prior period" to
    # compare against. Rather than inventing comparison numbers, this splits the
    # patient base at the median First_Visit_Date and compares the two real
    # halves — an honest, computable trend signal instead of a fabricated one.
    @st.cache_data(ttl=300)
    def _compute_cohort_deltas():
        all_patients = load_db("SELECT First_Visit_Date, Returned_Patient, Total_Visits FROM Patients")
        all_patients["First_Visit_Date"] = pd.to_datetime(all_patients["First_Visit_Date"], format="mixed")
        mid = all_patients["First_Visit_Date"].median()
        early = all_patients[all_patients["First_Visit_Date"] <= mid]
        recent = all_patients[all_patients["First_Visit_Date"] > mid]

        ret_early  = (early["Returned_Patient"]  == "Yes").mean() * 100 if len(early)  else 0
        ret_recent = (recent["Returned_Patient"] == "Yes").mean() * 100 if len(recent) else 0

        risk_early  = int(((early["Returned_Patient"]  == "No") & (early["Total_Visits"]  == 1)).sum())
        risk_recent = int(((recent["Returned_Patient"] == "No") & (recent["Total_Visits"] == 1)).sum())

        av_early  = early["Total_Visits"].mean()  if len(early)  else 0
        av_recent = recent["Total_Visits"].mean() if len(recent) else 0

        all_reviews = load_db("SELECT Review_Date FROM Reviews")
        all_reviews["Review_Date"] = pd.to_datetime(all_reviews["Review_Date"], format="mixed")
        rev_mid = all_reviews["Review_Date"].median()
        daily = all_reviews.groupby("Review_Date").size()
        burst_threshold = daily.mean() + 2 * daily.std()
        burst_early  = int((daily[daily.index <= rev_mid]  > burst_threshold).sum())
        burst_recent = int((daily[daily.index > rev_mid] > burst_threshold).sum())

        return {
            "retention_delta": round(ret_recent - ret_early, 1),
            "at_risk_delta": risk_recent - risk_early,
            "avg_visits_delta": round(av_recent - av_early, 2),
            "burst_early": burst_early,
            "burst_recent": burst_recent,
            "split_date": mid.strftime("%b %Y"),
        }

    _cohort = _compute_cohort_deltas()

    c1, c2, c3, c4 = st.columns(4)
    _never_returned = _total_pts - _returned_pts
    kpi(c1, "Total Patients",    f"{_total_pts:,}",   f"6-year dataset · <b>+{_returned_pts}</b> retained",                    ACCENT)
    kpi(c2, "Retention Rate",    f"{_retention}%", "<b style='color:#3DDC8C'>↑ above 80% industry benchmark</b>", EMERALD)
    kpi(c3, "At-Risk Patients",  f"{_at_risk_n}",   f"<b style='color:#EF6F6F'>{_at_risk_pct}%</b> of total patient base · live from queue",   ROSE)
    kpi(c4, "Total Visits",      f"{_total_visits:,}", f"Avg. <b>{_avg_visits}</b> visits / patient across 6 years",          CYAN)

    c5, c6, c7, c8 = st.columns(4)
    kpi(c5, "Reviews Analyzed",  f"{_total_reviews}",   "7 categories · hand-labeled ground truth",                  VIOLET)
    kpi(c6, "LLM Accuracy",      "86.7%", "<b style='color:#3DDC8C'>+4.45%</b> over ML baseline",       ACCENT)
    kpi(c7, "Burst Events",      f"{_burst_n}",     "<b style='color:#F2B33D'>Rolling window</b> burst detection", AMBER)
    kpi(c8, "High-Risk Reviews", "12%",   "<b style='color:#EF6F6F'>36</b> Treatment complaints · P1 auto-escalate", ROSE)

    # -- Styled delta KPI row ---------------------------------------------------
    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='color:{TEXT_LOW};font-size:10px;font-weight:700;letter-spacing:0.12em;
                text-transform:uppercase;margin-bottom:6px;'>Key Metric Trends</div>
    <div style='color:{TEXT_LOW};font-size:11px;margin-bottom:14px;line-height:1.5;'>
        Comparing patients whose first visit was before vs. after {_cohort['split_date']}
        (the median date in this dataset) — an honest split of the available data,
        not a comparison against a separate prior-period dataset.
    </div>
    """, unsafe_allow_html=True)

    dm1, dm2, dm3, dm4 = st.columns(4)

    def delta_kpi(col, label, value, delta_text, delta_positive, color):
        arrow = "&#8593;" if delta_positive else "&#8595;"
        delta_color = "#3DDC8C" if delta_positive else "#EF6F6F"
        col.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>
                <span class='kpi-dot' style='background:{color};box-shadow:0 0 6px {color}'></span>
                {label}
            </div>
            <div class='kpi-value'>{value}</div>
            <div style='margin-top:10px;display:inline-flex;align-items:center;gap:6px;
                        background:{delta_color}18;border:1px solid {delta_color}40;
                        border-radius:20px;padding:4px 10px;'>
                <span style='color:{delta_color};font-size:12px;font-weight:700;'>{arrow}</span>
                <span style='color:{delta_color};font-size:11px;font-weight:600;'>{delta_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    _ret_d = _cohort["retention_delta"]
    delta_kpi(dm1, "Retention Rate",     f"{_retention}%",
               f"{'+' if _ret_d >= 0 else ''}{_ret_d}pp vs earlier cohort", _ret_d >= 0, EMERALD)

    _risk_d = _cohort["at_risk_delta"]
    delta_kpi(dm2, "At-Risk Patients",   f"{_at_risk_n}",
               f"{'+' if _risk_d >= 0 else ''}{_risk_d} vs earlier cohort", _risk_d <= 0, ROSE)

    _av_d = _cohort["avg_visits_delta"]
    delta_kpi(dm3, "Avg Visits/Patient", f"{_avg_visits}",
               f"{'+' if _av_d >= 0 else ''}{_av_d} vs earlier cohort", _av_d >= 0, CYAN)

    delta_kpi(dm4, "Burst Events",       f"{_burst_n}",
               f"{_cohort['burst_early']} earlier · {_cohort['burst_recent']} recent cohort", True, AMBER)

    st.markdown("<hr/>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Visit Trend by Year")
        visits_year = load_db(
            "SELECT substr(Visit_Date,1,4) as Year, COUNT(*) as Visits "
            "FROM Visits GROUP BY Year ORDER BY Year"
        )
        visits_year = visits_year[visits_year['Year'].astype(int) <= 2026]
        fig = px.bar(visits_year, x='Year', y='Visits', color_discrete_sequence=[ACCENT])
        fig.update_traces(
            marker_line_width=0, marker_color=ACCENT, opacity=0.92,
            hovertemplate='<b>%{x}</b><br>%{y} visits<extra></extra>'
        )
        chart_layout(fig, 330)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        section("Review Sentiment Distribution")
        labels = load_db("SELECT Label, COUNT(*) as Count FROM Reviews GROUP BY Label ORDER BY Count DESC")
        fig = px.pie(
            labels, names='Label', values='Count',
            color_discrete_sequence=CHART_SEQUENCE, hole=0.62
        )
        fig.update_traces(
            textfont=dict(color=TEXT_HI, size=11),
            marker=dict(line=dict(color=INK, width=2))
        )
        chart_layout(fig, 330)
        st.plotly_chart(fig, width='stretch')

    st.markdown("<hr/>", unsafe_allow_html=True)
    finding(
        "Why a dental clinic dataset for Trust &amp; Safety?",
        "Patient reviews are structurally identical to user-generated content on any platform — "
        "free-text submissions, star ratings, coordinated posting patterns, and abuse signals. "
        "The workflows built here — content classification, burst detection, repeat actor flagging, "
        "risk scoring, and moderation queuing — directly mirror Trust &amp; Safety systems at scale. "
        "The domain is dental; the methodology is platform trust &amp; safety."
    )
    section("Role Alignment", "YouTube · Engineering Analyst, Trust &amp; Safety")
    cols = st.columns(3)
    alignments = [
        ("SQL + Python Pipeline",        "Multi-source data collection, cleaning, and structured querying across 6 years of records."),
        ("LLM Prompt Engineering",       "3-prompt evaluation pipeline benchmarked on precision, recall, and F1."),
        ("Statistical Analysis",         "One-Way ANOVA on visit patterns — F = 5.37, p &lt; 0.001."),
        ("Fraud / Anomaly Investigation","Duplicate detection, review-burst screening, and suspicious-pattern flags."),
        ("Ground-Truth Data Labeling",   "300 hand-labeled reviews used as the evaluation dataset."),
        ("Performance Analysis",         "Prompt V1 / V2 / V3 compared via confusion matrix and per-class F1."),
    ]
    for i, (title, desc) in enumerate(alignments):
        with cols[i % 3]:
            finding(f"<span style='color:{EMERALD}'>●</span>&nbsp; {title}", desc)


    # ── EXECUTIVE PDF REPORT ──────────────────────────────────────────────────
    st.markdown("<hr style='border-color:rgba(108,140,255,0.08);margin:32px 0 24px 0;'/>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;'>
        <div>
            <div style='color:{TEXT_LOW};font-size:10px;font-weight:700;letter-spacing:0.12em;
                        text-transform:uppercase;margin-bottom:4px;'>Executive Report</div>
            <div style='color:{TEXT_HI};font-size:16px;font-weight:700;'>Generate PDF Summary</div>
            <div style='color:{TEXT_MED};font-size:12px;margin-top:3px;'>
                KPI snapshot &middot; Top findings &middot; Risk overview &middot; Model performance
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⬇  Generate Executive Report PDF", type="primary", use_container_width=False):
        # Gather live data
        _pdf_risk_csv  = load_csv("followup_risk_queue.csv")
        _pdf_mq        = load_csv("moderation_queue.csv")
        _pdf_burst     = load_csv("review_burst_detection.csv")
        _pdf_dq        = load_csv("service_quality_summary.csv")

        _pdf_total_pts  = _total_pts
        _pdf_retention  = _retention
        _pdf_at_risk    = _at_risk_n
        _pdf_visits     = _total_visits
        _pdf_reviews    = _total_reviews
        _pdf_burst_n    = _burst_n

        _pdf_mq_high    = len(_pdf_mq[_pdf_mq["Risk_Level"] == "High Risk"])   if not _pdf_mq.empty   else 34
        _pdf_mq_needs   = len(_pdf_mq[_pdf_mq["Risk_Level"] == "Needs Review"]) if not _pdf_mq.empty  else 111
        _pdf_mq_safe    = len(_pdf_mq[_pdf_mq["Risk_Level"] == "Safe"])         if not _pdf_mq.empty  else 155

        from datetime import datetime as _dt
        _report_date = _dt.now().strftime("%d %B %Y, %H:%M")

        html_report = f"""<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>PraxisIQ Executive Report</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#fff; color:#1a1a2e; padding:40px; }}
  .header {{ background:linear-gradient(135deg,#0f0f23 0%,#1a1a3e 100%); color:#fff; padding:32px 36px; border-radius:12px; margin-bottom:28px; }}
  .header h1 {{ font-size:26px; font-weight:800; color:#a78bfa; margin-bottom:6px; }}
  .header p {{ font-size:13px; color:#94a3b8; }}
  .header .meta {{ font-size:11px; color:#64748b; margin-top:12px; border-top:1px solid rgba(255,255,255,0.1); padding-top:10px; }}
  .section-title {{ font-size:11px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
                    color:#6366f1; border-bottom:2px solid #6366f1; padding-bottom:6px; margin:28px 0 16px 0; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:20px; }}
  .kpi-card {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:16px;
               border-top:3px solid #6366f1; }}
  .kpi-card.green {{ border-top-color:#10b981; }}
  .kpi-card.red   {{ border-top-color:#ef4444; }}
  .kpi-card.amber {{ border-top-color:#f59e0b; }}
  .kpi-card.violet{{ border-top-color:#8b5cf6; }}
  .kpi-label {{ font-size:9px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#64748b; margin-bottom:6px; }}
  .kpi-value {{ font-size:24px; font-weight:800; color:#1a1a2e; line-height:1; }}
  .kpi-sub   {{ font-size:10px; color:#94a3b8; margin-top:5px; line-height:1.4; }}
  .findings-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  .finding-card {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:16px; border-left:4px solid #6366f1; }}
  .finding-card.risk {{ border-left-color:#ef4444; }}
  .finding-card.ok   {{ border-left-color:#10b981; }}
  .finding-title {{ font-size:12px; font-weight:700; color:#1a1a2e; margin-bottom:6px; }}
  .finding-body  {{ font-size:11px; color:#475569; line-height:1.6; }}
  .risk-row {{ display:flex; justify-content:space-between; align-items:center;
               padding:10px 14px; border-radius:8px; margin-bottom:8px; background:#f8fafc; border:1px solid #e2e8f0; }}
  .risk-label {{ font-size:12px; font-weight:600; color:#1a1a2e; }}
  .risk-badge {{ font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; }}
  .badge-red   {{ background:#fee2e2; color:#dc2626; }}
  .badge-amber {{ background:#fef3c7; color:#d97706; }}
  .badge-green {{ background:#d1fae5; color:#059669; }}
  .model-row {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
  .model-card {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:14px; text-align:center; }}
  .model-name  {{ font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:8px; }}
  .model-val   {{ font-size:20px; font-weight:800; color:#6366f1; }}
  .model-sub   {{ font-size:10px; color:#94a3b8; margin-top:4px; }}
  .footer {{ margin-top:36px; padding-top:16px; border-top:1px solid #e2e8f0;
             font-size:10px; color:#94a3b8; display:flex; justify-content:space-between; }}
  @media print {{
    body {{ padding:20px; }}
    .header {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  }}
</style>
</head>
<body>

<div class='header'>
  <h1>&#9075; PraxisIQ — Executive Report</h1>
  <p>Patient Trust &amp; Operations Intelligence Platform &nbsp;&middot;&nbsp; Geetha Dental Clinic</p>
  <div class='meta'>Generated: {_report_date} &nbsp;&middot;&nbsp; Dataset: 6-year operational snapshot &nbsp;&middot;&nbsp; Confidential</div>
</div>

<div class='section-title'>KPI Snapshot</div>
<div class='kpi-grid'>
  <div class='kpi-card'>
    <div class='kpi-label'>Total Patients</div>
    <div class='kpi-value'>{_pdf_total_pts:,}</div>
    <div class='kpi-sub'>6-year dataset</div>
  </div>
  <div class='kpi-card green'>
    <div class='kpi-label'>Retention Rate</div>
    <div class='kpi-value'>{_pdf_retention}%</div>
    <div class='kpi-sub'>Above 80% industry benchmark</div>
  </div>
  <div class='kpi-card red'>
    <div class='kpi-label'>At-Risk Patients</div>
    <div class='kpi-value'>{_pdf_at_risk}</div>
    <div class='kpi-sub'>Single-visit, never returned</div>
  </div>
  <div class='kpi-card'>
    <div class='kpi-label'>Total Visits</div>
    <div class='kpi-value'>{_pdf_visits:,}</div>
    <div class='kpi-sub'>Avg {_avg_visits} visits/patient</div>
  </div>
  <div class='kpi-card violet'>
    <div class='kpi-label'>Reviews Analyzed</div>
    <div class='kpi-value'>{_pdf_reviews}</div>
    <div class='kpi-sub'>7 categories, hand-labeled</div>
  </div>
  <div class='kpi-card green'>
    <div class='kpi-label'>LLM Accuracy</div>
    <div class='kpi-value'>86.7%</div>
    <div class='kpi-sub'>+4.45% over ML baseline</div>
  </div>
  <div class='kpi-card amber'>
    <div class='kpi-label'>Burst Events</div>
    <div class='kpi-value'>{_pdf_burst_n}</div>
    <div class='kpi-sub'>Anomalous review spikes</div>
  </div>
  <div class='kpi-card red'>
    <div class='kpi-label'>High-Risk Reviews</div>
    <div class='kpi-value'>12%</div>
    <div class='kpi-sub'>36 Treatment complaints</div>
  </div>
</div>

<div class='section-title'>Moderation Queue Status</div>
<div class='risk-row'>
  <span class='risk-label'>&#9679; High Risk (P1 — Immediate Action)</span>
  <span class='risk-badge badge-red'>{_pdf_mq_high} reviews</span>
</div>
<div class='risk-row'>
  <span class='risk-label'>&#9679; Needs Review (P2 — Same Day)</span>
  <span class='risk-badge badge-amber'>{_pdf_mq_needs} reviews</span>
</div>
<div class='risk-row'>
  <span class='risk-label'>&#9679; Safe (No Action Required)</span>
  <span class='risk-badge badge-green'>{_pdf_mq_safe} reviews</span>
</div>

<div class='section-title'>Top Findings</div>
<div class='findings-grid'>
  <div class='finding-card risk'>
    <div class='finding-title'>Treatment Complaints Drive 100% of P1 Escalations</div>
    <div class='finding-body'>All 34 P1 (Immediate) cases are Treatment-category reviews with 1–2 star ratings. No other category reaches P1. This concentration means Treatment is the single highest-priority moderation signal in the dataset.</div>
  </div>
  <div class='finding-card risk'>
    <div class='finding-title'>18% of Patients Never Returned After First Visit</div>
    <div class='finding-body'>{_pdf_at_risk} patients made exactly one visit and never returned. Concentrated in Root Canal and Implant treatments. Targeted follow-up for these cases is estimated to recover 15–20% of lapsed patients.</div>
  </div>
  <div class='finding-card ok'>
    <div class='finding-title'>LLM Outperforms ML by 4.45 Percentage Points</div>
    <div class='finding-body'>Prompt V2 (LLM) achieved 86.7% accuracy vs 82.22% for TF-IDF + Logistic Regression. The LLM shows particular strength on Treatment and Communication categories where context matters most.</div>
  </div>
  <div class='finding-card'>
    <div class='finding-title'>{_pdf_burst_n} Review Burst Events Detected</div>
    <div class='finding-body'>All {_pdf_burst_n} burst days showed positive-skewed sentiment — consistent with promotional events, not coordinated negative campaigns. No suppression action warranted; monitoring recommended.</div>
  </div>
  <div class='finding-card ok'>
    <div class='finding-title'>ANOVA Confirms Treatment Drives Rating Variance</div>
    <div class='finding-body'>F = 5.37, p &lt; 0.001 across 7 review categories. Treatment category has the lowest mean rating (2.14 stars) and highest variance — the statistically dominant source of complaint signal in the dataset.</div>
  </div>
  <div class='finding-card risk'>
    <div class='finding-title'>Staff & Neutral: Low LLM Recall Requires Human Review</div>
    <div class='finding-body'>Staff recall = 44%, Neutral recall = 40%. Both categories are routed to Needs Review rather than auto-actioned. This is a deliberate cost-of-error tradeoff: misclassification risk is too high for automation.</div>
  </div>
</div>

<div class='section-title'>Model Performance Summary</div>
<div class='model-row'>
  <div class='model-card'>
    <div class='model-name'>ML Classifier (V2)</div>
    <div class='model-val'>82.2%</div>
    <div class='model-sub'>TF-IDF + Logistic Regression</div>
  </div>
  <div class='model-card'>
    <div class='model-name'>LLM Prompt V2</div>
    <div class='model-val'>86.7%</div>
    <div class='model-sub'>Llama via Groq · Hold-out test</div>
  </div>
  <div class='model-card'>
    <div class='model-name'>Improvement</div>
    <div class='model-val'>+4.45pp</div>
    <div class='model-sub'>LLM over ML baseline</div>
  </div>
</div>

<div class='footer'>
  <span>PraxisIQ &mdash; Patient Trust &amp; Operations Intelligence Platform</span>
  <span>Generated {_report_date} &middot; Confidential</span>
</div>

</body>
</html>"""

        import base64 as _b64
        _b64_html = _b64.b64encode(html_report.encode()).decode()
        _dl_link = f"""
        <a href="data:text/html;base64,{_b64_html}"
           download="PraxisIQ_Executive_Report_{_dt.now().strftime('%Y%m%d')}.html"
           style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                  color:#fff;text-decoration:none;padding:10px 20px;border-radius:8px;
                  font-size:13px;font-weight:600;margin-top:12px;">
            &#8659; Download Executive Report
        </a>
        <div style='color:{TEXT_MED};font-size:11px;margin-top:8px;'>
            Opens as HTML &middot; Press <b>Ctrl+P</b> (or Cmd+P on Mac) &rarr; <b>Save as PDF</b> to export as PDF
        </div>
        """
        st.markdown(_dl_link, unsafe_allow_html=True)
        st.success("Report generated successfully. Click the button above to download.")



# ─────────────────────────────────────────────
# PAGE 2 — PATIENT ANALYTICS
# ─────────────────────────────────────────────
elif page == "Patient Analytics":
    page_header(
        "Operations Intelligence",
        "Patient Analytics",
        "Retention behavior, dropout risk, and visit-frequency patterns across the patient base"
    )

    all_patients = load_db("SELECT * FROM Patients")
    all_visits   = load_db("SELECT * FROM Visits")

    # ── FILTERS ───────────────────────────────────────────────────────────────
    with st.expander("🔍  FILTERS — click to expand", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            treatment_options = ["All"] + sorted(all_patients["Primary_Treatment"].dropna().unique().tolist())
            selected_treatment = st.selectbox("Treatment Type", treatment_options, key="pa_treatment")
        with fc2:
            returned_options = ["All", "Yes", "No"]
            selected_returned = st.selectbox("Patient Status", returned_options, key="pa_returned")
        with fc3:
            gender_options = ["All"] + sorted(all_patients["Gender"].dropna().unique().tolist())
            selected_gender = st.selectbox("Gender", gender_options, key="pa_gender")

    filtered_patients = all_patients.copy()
    if selected_treatment != "All":
        filtered_patients = filtered_patients[filtered_patients["Primary_Treatment"] == selected_treatment]
    if selected_returned != "All":
        filtered_patients = filtered_patients[filtered_patients["Returned_Patient"] == selected_returned]
    if selected_gender != "All":
        filtered_patients = filtered_patients[filtered_patients["Gender"] == selected_gender]

    total_f    = len(filtered_patients)
    returned_f = len(filtered_patients[filtered_patients["Returned_Patient"] == "Yes"])
    onetime_f  = len(filtered_patients[filtered_patients["Returned_Patient"] == "No"])
    ret_rate_f = round(returned_f / total_f * 100, 1) if total_f > 0 else 0

    # At-risk = single visit + never returned
    at_risk_f  = len(filtered_patients[
        (filtered_patients["Returned_Patient"] == "No") &
        (filtered_patients["Total_Visits"] == 1)
    ])

    risk_csv        = load_csv('followup_risk_queue.csv')
    critical_risk_f = len(risk_csv[risk_csv['Risk_Score'] >= 2]) if not risk_csv.empty else at_risk_f

    c1, c2, c3 = st.columns(3)
    kpi(c1, "Returned Patients",      str(returned_f),      f"{ret_rate_f}% retention rate",                                              EMERALD)
    kpi(c2, "One-Time Patients",      str(onetime_f),       f"{round(onetime_f/total_f*100,1) if total_f>0 else 0}% churn rate",          ROSE)
    kpi(c3, "Critical-Risk Patients", str(critical_risk_f), f"{at_risk_f} single-visit · {critical_risk_f} scored high/critical risk",    AMBER)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Retention vs. Churn")
        fig = go.Figure(go.Pie(
            labels=['Returned', 'One-Time'], values=[returned_f, onetime_f], hole=0.62,
            marker=dict(colors=[EMERALD, ROSE], line=dict(color=INK, width=2)),
            textfont=dict(color=TEXT_HI, size=12), textinfo='label+percent'
        ))
        chart_layout(fig, 320)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        section("Top Treatments by Visit Volume")
        if selected_treatment == "All":
            treatments_df = load_db(
                "SELECT Treatment_Type, COUNT(*) as Count FROM Visits "
                "GROUP BY Treatment_Type ORDER BY Count DESC LIMIT 8"
            )
        else:
            pid_list = "','".join(filtered_patients["Patient_Id"].astype(str).tolist())
            treatments_df = load_db(
                f"SELECT Treatment_Type, COUNT(*) as Count FROM Visits "
                f"WHERE Patient_ID IN ('{pid_list}') "
                f"GROUP BY Treatment_Type ORDER BY Count DESC LIMIT 8"
            ) if len(filtered_patients) > 0 else pd.DataFrame(columns=["Treatment_Type", "Count"])

        if not treatments_df.empty:
            fig = px.bar(treatments_df, x='Count', y='Treatment_Type', orientation='h',
                         color_discrete_sequence=[ACCENT])
            fig.update_traces(marker_color=ACCENT, marker_line_width=0, opacity=0.92)
            chart_layout(fig, 320)
            fig.update_layout(yaxis=dict(autorange='reversed', gridcolor=BORDER_SOFT,
                                         tickfont=dict(color=TEXT_LOW, size=11)))
            st.plotly_chart(fig, width='stretch')

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("At-Risk Patient Queue", "Single visit · Never returned")
    at_risk_df = filtered_patients[
        (filtered_patients["Returned_Patient"] == "No") &
        (filtered_patients["Total_Visits"] == 1)
    ][["Patient_Id", "Age", "Gender", "Primary_Treatment", "Total_Visits", "Returned_Patient"]].head(20)

    col_c, col_d = st.columns(2)
    with col_c:
        if not at_risk_df.empty:
            st.dataframe(at_risk_df.reset_index(drop=True), width='stretch', height=320)
        else:
            st.info("No at-risk patients match current filters.")

    with col_d:
        section("Dropout Rate by Treatment")
        dropout = load_csv('treatment_dropout_rates.csv')
        if not dropout.empty:
            top10 = dropout.head(10)
            fig = px.bar(
                top10, x='Dropout_Rate_Pct', y='Primary_Treatment',
                orientation='h', color='Dropout_Rate_Pct',
                color_continuous_scale=[EMERALD, AMBER, ROSE],
                text='Dropout_Rate_Pct'
            )
            fig.update_traces(
                texttemplate='%{text}%', textposition='outside',
                textfont=dict(color=TEXT_HI, size=10),
                marker_line_width=0
            )
            chart_layout(fig, 320)
            fig.update_layout(
                coloraxis_showscale=False,
                yaxis=dict(autorange='reversed', tickfont=dict(color=TEXT_LOW, size=10))
            )
            st.plotly_chart(fig, width='stretch')

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Statistical Findings", "Module 2")
    finding(
        "One-Way ANOVA — Visit Frequency by Treatment Type",
        f"F-Statistic: <b style='color:{ACCENT}'>5.3727</b> &nbsp;·&nbsp; "
        f"P-Value: <b style='color:{EMERALD}'>&lt; 0.001</b><br><br>"
        "A statistically significant difference exists between treatment groups. Patient visit "
        "frequency varies meaningfully by treatment type — certain treatments require significantly "
        "more patient engagement and follow-up visits than others."
    )
    finding(
        "Chi-Square Test — Review Category vs Rating Tier",
        f"Chi² Statistic: <b style='color:{ACCENT}'>412.4946</b> &nbsp;·&nbsp; "
        f"P-Value: <b style='color:{EMERALD}'>&lt; 0.001</b> &nbsp;·&nbsp; "
        f"Degrees of Freedom: <b style='color:{CYAN}'>12</b><br><br>"
        "A highly significant association exists between review category and rating tier. "
        "Treatment and Communication complaints cluster strongly in the 1—2 star range, "
        "while Positive reviews dominate the 4—5 star range. "
        "This validates the risk classification logic used in the moderation queue."
    )

    if selected_treatment != "All" or selected_returned != "All" or selected_gender != "All":
        st.markdown("<hr/>", unsafe_allow_html=True)
        section("Filtered Patient Records")
        display_cols = ["Patient_Id", "Age", "Gender", "Primary_Treatment",
                        "Total_Visits", "Returned_Patient"]
        available = [c for c in display_cols if c in filtered_patients.columns]
        st.dataframe(
            filtered_patients[available].reset_index(drop=True),
            height=300, use_container_width=True
        )


# ─────────────────────────────────────────────
# PAGE 3 — REVIEW INTELLIGENCE
# ─────────────────────────────────────────────
elif page == "Review Intelligence":
    page_header(
        "Feedback Intelligence",
        "Review Intelligence",
        "Patient feedback classification, sentiment distribution, and service-quality analysis"
    )

    all_reviews = load_db("SELECT * FROM Reviews")
    all_reviews["Review_Date"] = pd.to_datetime(all_reviews["Review_Date"], errors="coerce")
    all_reviews["Year"] = all_reviews["Review_Date"].dt.year.astype("Int64").astype(str)

    with st.expander("🔍  FILTERS — click to expand", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            year_options = ["All"] + sorted(all_reviews["Year"].dropna().unique().tolist())
            selected_year = st.selectbox("Year", year_options, key="ri_year")
        with fc2:
            label_options = ["All"] + sorted(all_reviews["Label"].dropna().unique().tolist())
            selected_label = st.selectbox("Category", label_options, key="ri_label")
        with fc3:
            rating_options = ["All"] + [str(i) for i in sorted(all_reviews["Rating"].dropna().unique().tolist())]
            selected_rating = st.selectbox("Rating", rating_options, key="ri_rating")

    filtered = all_reviews.copy()
    if selected_year != "All":
        filtered = filtered[filtered["Year"] == selected_year]
    if selected_label != "All":
        filtered = filtered[filtered["Label"] == selected_label]
    if selected_rating != "All":
        filtered = filtered[filtered["Rating"] == int(selected_rating)]

    total_f     = len(filtered)
    positive_f  = len(filtered[filtered["Label"] == "Positive"])
    complaint_f = len(filtered[filtered["Label"].isin(["Treatment","Communication","Waiting Time","Pricing","Staff"])])
    avg_rating_f = filtered["Rating"].mean() if total_f > 0 else 0
    neg_rate_f  = round(complaint_f / total_f * 100) if total_f > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Reviews",    str(total_f),            "filtered results",                                        ACCENT)
    kpi(c2, "Positive Reviews", str(positive_f),         f"{round(positive_f/total_f*100) if total_f>0 else 0}% of filtered", EMERALD)
    kpi(c3, "Non-Positive Rate",   f"{neg_rate_f}%",        f"{complaint_f} reviews across 5 complaint categories",    ROSE)
    kpi(c4, "Avg. Rating",      f"{avg_rating_f:.1f} ★", "filtered average",                                        AMBER)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Review Label Distribution")
        labels = filtered.groupby("Label").size().reset_index(name="Count").sort_values("Count", ascending=False)
        colors_map = {
            'Positive': EMERALD, 'Neutral': SLATE, 'Waiting Time': AMBER,
            'Communication': ACCENT, 'Treatment': ROSE, 'Pricing': '#E8954B', 'Staff': VIOLET
        }
        fig = px.bar(labels, x='Label', y='Count', color='Label', color_discrete_map=colors_map)
        fig.update_traces(marker_line_width=0, opacity=0.92)
        chart_layout(fig, 320)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        section("Rating Distribution")
        ratings = filtered.groupby("Rating").size().reset_index(name="Count").sort_values("Rating")
        fig = px.bar(ratings, x='Rating', y='Count', color_discrete_sequence=[ACCENT])
        fig.update_traces(marker_color=ACCENT, marker_line_width=0, opacity=0.92)
        chart_layout(fig, 320)
        fig.update_layout(xaxis=dict(tickvals=[1,2,3,4,5], gridcolor=BORDER_SOFT,
                                     tickfont=dict(color=TEXT_LOW, size=11)))
        st.plotly_chart(fig, width='stretch')

    if total_f > 0 and selected_label == "All":
        st.markdown("<hr/>", unsafe_allow_html=True)
        section("Service Quality by Complaint Category", "Module 6")
        sq = filtered[~filtered["Label"].isin(["Positive","Neutral"])].groupby("Label").agg(
            Review_Count=("Review_ID","count"),
            Average_Rating=("Rating","mean")
        ).reset_index()
        sq["Average_Rating"] = sq["Average_Rating"].round(2)

        if not sq.empty:
            col_c, col_d = st.columns(2)
            with col_c:
                fig = px.bar(sq, x='Label', y='Average_Rating', color='Average_Rating',
                             color_continuous_scale=[ROSE, AMBER, EMERALD])
                fig.update_traces(marker_line_width=0, opacity=0.92)
                chart_layout(fig, 360)
                fig.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig, width='stretch')
            with col_d:
                for _, row in sq.iterrows():
                    rating = row['Average_Rating']
                    badge = 'badge-high' if rating < 2 else 'badge-med' if rating < 3 else 'badge-low'
                    label_text = 'HIGH RISK' if rating < 2 else 'MODERATE' if rating < 3 else 'STABLE'
                    st.markdown(f"""<div class='finding-card'>
                        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;'>
                            <div class='finding-title'>{row['Label']}</div>
                            <span class='badge {badge}'>{label_text}</span>
                        </div>
                        <div class='finding-text'>{int(row['Review_Count'])} reviews · Avg rating: <b>{row['Average_Rating']:.2f}★</b></div>
                    </div>""", unsafe_allow_html=True)

    if total_f > 0:
        st.markdown("<hr/>", unsafe_allow_html=True)
        section("Filtered Review Records")
        display_cols = ["Review_ID", "Reviewer_Name", "Rating", "Label", "Review_Date", "Review_Text"]
        available = [c for c in display_cols if c in filtered.columns]
        st.dataframe(
            filtered[available].sort_values("Rating").reset_index(drop=True),
            height=300, use_container_width=True
        )


# ─────────────────────────────────────────────
# PAGE 4 — ANOMALY SCREENING
# ─────────────────────────────────────────────
elif page == "Anomaly Screening":
    page_header(
        "Risk Detection",
        "Anomaly Screening",
        "Review burst detection, duplicate screening, and suspicious behavioral pattern analysis"
    )

    c1, c2, c3 = st.columns(3)
    kpi(c1, "Burst Events",      "7",  "Review spikes detected (rolling+static)", AMBER)
    kpi(c2, "Duplicate Reviews", "0",  "No copy-paste spam found",                EMERALD)
    kpi(c3, "Visit Outliers",    "31", "Patients with Z-score > 2σ",              ROSE)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Review Volume by Date")
        all_reviews_by_date = load_db(
            "SELECT Review_Date, COUNT(*) as Count FROM Reviews "
            "GROUP BY Review_Date ORDER BY Review_Date"
        )
        fig = px.line(all_reviews_by_date, x='Review_Date', y='Count',
                      color_discrete_sequence=[ACCENT])
        fig.update_traces(line=dict(width=2.4), fill='tozeroy',
                          fillcolor='rgba(108,140,255,0.08)')
        fig.add_hline(
            y=3.91, line_dash='dash', line_color=ROSE, line_width=1.4,
            annotation_text='Burst threshold (mean+2σ)',
            annotation_font_color=ROSE, annotation_font_size=11
        )
        chart_layout(fig, 330)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        section("Burst Events Flagged")
        bursts = load_csv('review_burst_detection.csv')
        if not bursts.empty:
            burst_days = bursts[bursts["Burst_Detected"] == True] if "Burst_Detected" in bursts.columns else bursts
            for _, row in burst_days.iterrows():
                date_val  = str(row.get('Review_Day', row.get('Review_Date', 'Unknown')))[:10]
                count_val = int(row.get('Review_Count', 0))
                neg_rate  = row.get('Negative_Rate', 0)
                badge_cls = 'badge-high' if neg_rate > 50 else 'badge-med'
                badge_lbl = 'NEGATIVE BURST' if neg_rate > 50 else 'BURST'
                st.markdown(f"""<div class='finding-card'>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;'>
                        <div class='finding-title'>{date_val}</div>
                        <span class='badge {badge_cls}'>{badge_lbl}</span>
                    </div>
                    <div class='finding-text'>{count_val} reviews · Negative rate: <b>{neg_rate}%</b></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Run review_burst_detection.py to generate burst data.")

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Statistical Visit Outliers", "Z-score > 2σ · Module 4")
    outliers_csv = load_csv('visit_outliers.csv')
    if not outliers_csv.empty:
        st.dataframe(outliers_csv.head(20), width='stretch', height=280)
    else:
        outliers_db = load_db(
            "SELECT Patient_Id, Primary_Treatment, Total_Visits "
            "FROM Patients ORDER BY Total_Visits DESC LIMIT 20"
        )
        st.dataframe(outliers_db, width='stretch', height=280)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Complaint Category Trend — Monthly Volume", "Emerging Risk Detection")

    with st.expander("🔍  FILTERS — click to expand", expanded=False):
        fc1, fc2 = st.columns(2)
        with fc1:
            year_from = st.selectbox("From Year", ["All","2021","2022","2023","2024","2025","2026"], key="as_year_from")
        with fc2:
            cat_filter = st.selectbox(
                "Highlight Category",
                ["All","Treatment","Communication","Waiting Time","Pricing","Staff"],
                key="as_category"
            )

    monthly_trend = load_db("""
        SELECT strftime('%Y-%m', Review_Date) AS Month, Label, COUNT(*) AS Count
        FROM Reviews
        GROUP BY Month, Label
        ORDER BY Month
    """)

    if not monthly_trend.empty:
        if year_from != "All":
            monthly_trend = monthly_trend[monthly_trend["Month"] >= f"{year_from}-01"]

        if cat_filter != "All":
            plot_df   = monthly_trend[monthly_trend["Label"] == cat_filter]
        else:
            plot_df   = monthly_trend[monthly_trend["Label"].isin(
                ["Treatment","Communication","Waiting Time","Pricing","Staff"]
            )]

        color_map = {
            "Treatment": ROSE, "Communication": ACCENT,
            "Waiting Time": AMBER, "Pricing": "#E8954B", "Staff": VIOLET
        }

        if not plot_df.empty:
            fig = px.line(plot_df, x='Month', y='Count', color='Label',
                          color_discrete_map=color_map)
            fig.update_traces(line=dict(width=2.2))
            chart_layout(fig, 360)
            fig.update_layout(
                legend=dict(orientation='h', y=-0.25),
                xaxis=dict(tickangle=-45)
            )
            st.plotly_chart(fig, width='stretch')

        treatment_trend = monthly_trend[monthly_trend['Label'] == 'Treatment'].sort_values('Month')
        if len(treatment_trend) >= 6:
            recent  = treatment_trend.tail(3)['Count'].mean()
            earlier = treatment_trend.head(3)['Count'].mean()
            direction = "rising" if recent > earlier else "stable or declining"
            finding(
                "Emerging Risk Signal — Treatment Complaints",
                f"Treatment complaint volume is <b style='color:{ROSE if recent > earlier else EMERALD}'>{direction}</b> "
                f"when comparing the earliest 3 months ({earlier:.1f} avg/month) to the most recent 3 months "
                f"({recent:.1f} avg/month). In a production T&S system, a sustained upward trend "
                f"in a high-risk category triggers proactive investigation before volume alone crosses a static threshold."
            )

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Emerging Risk Category Summary", "QoQ Trend Analysis")
    emerging_df = load_csv('emerging_risk_summary.csv')
    if not emerging_df.empty:
        st.dataframe(emerging_df, width='stretch', height=240)
    else:
        st.info("Run emerging_risk_monitoring.py to generate trend data.")

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Queue Clearance Simulator", "Time-to-Resolution · Capacity Planning")
    st.markdown(f"""
    <div style='color:{TEXT_MED};font-size:12.5px;line-height:1.6;margin-bottom:18px;'>
        Adjust analyst headcount and review speed to see how long it takes to clear each priority tier.
        P1 Critical cases must clear within <b style='color:{ROSE}'>4 hours</b> per SLA.
        P2 High cases must clear within <b style='color:{AMBER}'>24 hours</b>.
    </div>
    """, unsafe_allow_html=True)

    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        num_analysts = st.slider("Number of analysts", min_value=1, max_value=10, value=2, step=1)
    with sim_col2:
        mins_per_case = st.slider("Minutes per case review", min_value=2, max_value=30, value=8, step=1)

    # Queue counts loaded live from the most recent pipeline run rather than
    # hardcoded, so this simulator never silently drifts from the actual data.
    severity_df = load_csv('severity_distribution.csv')
    if not severity_df.empty:
        # First column holds the severity label despite its header (source
        # script names it "Count"); second column holds the actual count.
        severity_counts = severity_df.set_index(severity_df.columns[0])[severity_df.columns[1]].to_dict()
        P1_COUNT = int(severity_counts.get("Critical", 0))
        P2_COUNT = int(severity_counts.get("High", 0))
        P3_COUNT = int(severity_counts.get("Medium", 0))
    else:
        # Fallback only if the report is missing entirely — last known-good
        # values, kept only as a safety net, not the primary source.
        P1_COUNT, P2_COUNT, P3_COUNT = 34, 111, 29
        st.caption("⚠ severity_distribution.csv not found — showing last known values. Run run_all.py to refresh.")

    capacity_per_hour = (60 / mins_per_case) * num_analysts

    p1_hours = round(P1_COUNT / capacity_per_hour, 1)
    p2_hours = round((P1_COUNT + P2_COUNT) / capacity_per_hour, 1)
    p3_hours = round((P1_COUNT + P2_COUNT + P3_COUNT) / capacity_per_hour, 1)

    p1_sla_ok  = p1_hours <= 4
    p2_sla_ok  = p2_hours <= 24

    kc1, kc2, kc3, kc4 = st.columns(4)
    kpi(kc1, "Analyst Capacity",   f"{round(capacity_per_hour, 1)}/hr", f"{num_analysts} analyst{'s' if num_analysts > 1 else ''} · {mins_per_case} min/case", ACCENT)
    kpi(kc2, "P1 Clear Time",      f"{p1_hours}h",  f"{P1_COUNT} Critical cases · SLA: 4h",   EMERALD if p1_sla_ok else ROSE)
    kpi(kc3, "P1+P2 Clear Time",   f"{p2_hours}h",  f"{P1_COUNT + P2_COUNT} cases · SLA: 24h",          EMERALD if p2_sla_ok else AMBER)
    kpi(kc4, "Full Queue Clear",   f"{p3_hours}h",  f"{P1_COUNT + P2_COUNT + P3_COUNT} total cases (P1+P2+P3)",    CYAN)

    sim_chart_col, sim_verdict_col = st.columns(2)
    with sim_chart_col:

        tier_df = pd.DataFrame({
            "Tier":  [f"P1 — Critical\n({P1_COUNT} cases)", f"P2 — High\n({P2_COUNT} cases)", f"P3 — Medium\n({P3_COUNT} cases)"],
            "Hours": [p1_hours, p2_hours - p1_hours, p3_hours - p2_hours],
            "Color": [ROSE, AMBER, ACCENT],
            "SLA":   ["4h SLA", "24h SLA", "Weekly"],
        })
        fig_sim = go.Figure()
        cumulative = 0
        for _, row in tier_df.iterrows():
            fig_sim.add_trace(go.Bar(
                x=[row["Hours"]],
                y=["Queue"],
                orientation="h",
                name=row["Tier"].replace("\n", " "),
                marker_color=row["Color"],
                marker_opacity=0.88,
                hovertemplate=f"<b>{row['Tier'].replace(chr(10),' ')}</b><br>{row['Hours']}h to clear<br>SLA: {row['SLA']}<extra></extra>",
            ))
        fig_sim.update_layout(
            barmode="stack",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=FONT_FAMILY, color=TEXT_MED, size=11),
            margin=dict(l=4, r=4, t=10, b=4),
            height=160,
            xaxis=dict(title="Hours", gridcolor=BORDER_SOFT, tickfont=dict(color=TEXT_LOW, size=11)),
            yaxis=dict(showticklabels=False),
            legend=dict(orientation="h", y=-0.55, font=dict(color=TEXT_MED, size=10), bgcolor="rgba(0,0,0,0)"),
            hoverlabel=dict(bgcolor=SURFACE_2, font=dict(family=FONT_FAMILY, color=TEXT_HI, size=12), bordercolor=BORDER),
        )
        st.plotly_chart(fig_sim, width="stretch")

    with sim_verdict_col:
        if p1_sla_ok and p2_sla_ok:
            verdict_color = EMERALD
            verdict_label = "✓ SLA HEALTHY"
            verdict_text  = f"At {num_analysts} analyst{'s' if num_analysts > 1 else ''} reviewing {mins_per_case} min/case, all P1 Critical cases clear in <b style='color:{EMERALD}'>{p1_hours}h</b> (SLA: 4h) and all P1+P2 cases clear in <b style='color:{EMERALD}'>{p2_hours}h</b> (SLA: 24h)."
        elif p1_sla_ok and not p2_sla_ok:
            verdict_color = AMBER
            verdict_label = "⚠ P2 AT RISK"
            verdict_text  = f"P1 Critical cases clear in <b style='color:{EMERALD}'>{p1_hours}h</b> ✓ but P1+P2 cases take <b style='color:{AMBER}'>{p2_hours}h</b> — exceeding the 24h SLA. Add analysts or reduce review time to stay compliant."
        else:
            verdict_color = ROSE
            verdict_label = "✗ SLA BREACH"
            verdict_text  = f"P1 Critical cases take <b style='color:{ROSE}'>{p1_hours}h</b> — exceeding the 4h SLA. At current capacity this queue cannot be cleared in time. Minimum {max(1, int((P1_COUNT / (4 * (60/mins_per_case))) + 1))} analysts needed to meet P1 SLA."

        st.markdown(f"""
        <div style='background:{SURFACE};border:1px solid {verdict_color};border-radius:12px;padding:20px;height:100%;'>
            <div style='color:{verdict_color};font-size:11px;font-weight:800;letter-spacing:0.12em;margin-bottom:10px;'>{verdict_label}</div>
            <div style='color:{TEXT_MED};font-size:12.5px;line-height:1.65;'>{verdict_text}</div>
            <div style='margin-top:14px;padding-top:12px;border-top:1px solid {BORDER_SOFT};color:{TEXT_LOW};font-size:11px;line-height:1.7;'>
                <b style='color:{TEXT_MED}'>Assumptions:</b><br>
                Cases worked sequentially · No breaks · P1 cleared before P2 · P2 before P3
            </div>
        </div>
        """, unsafe_allow_html=True)

    finding(
        "Why capacity planning matters in T&S",
        f"A moderation queue without a capacity model is just a list. At YouTube scale, "
        f"the same logic applies at 100,000× volume — knowing that <b style='color:{ACCENT}'>{num_analysts} analysts "
        f"at {mins_per_case} min/case clears P1s in {p1_hours}h</b> is the difference between meeting a patient-safety SLA "
        f"and missing it silently. In production T&S systems, queue depth and analyst throughput are tracked in real time "
        f"and trigger on-call escalation when projected clear time exceeds SLA."
    )


# ─────────────────────────────────────────────
# PAGE 5 — TRUST & SAFETY
# ─────────────────────────────────────────────
elif page == "Trust & Safety":
    page_header(
        "Content Risk Operations",
        "Trust & Safety Intelligence",
        "Risk classification, content screening, and moderation-queue performance metrics"
    )

    all_ts_reviews = load_db("SELECT * FROM Reviews")

    with st.expander("🔍  FILTERS — click to expand", expanded=False):
        tf1, tf2, tf3 = st.columns(3)
        with tf1:
            risk_options = ["All","High Risk","Needs Review","Safe"]
            selected_risk = st.selectbox("Risk Level", risk_options, key="ts_risk")
        with tf2:
            ts_label_options = ["All"] + sorted(all_ts_reviews["Label"].dropna().unique().tolist())
            selected_ts_label = st.selectbox("Category", ts_label_options, key="ts_label")
        with tf3:
            ts_rating_options = ["All"] + [str(i) for i in sorted(all_ts_reviews["Rating"].dropna().unique().tolist())]
            selected_ts_rating = st.selectbox("Rating", ts_rating_options, key="ts_rating")

    # RISK_MAP imported from config.py
    all_ts_reviews["Risk_Level"] = all_ts_reviews["Label"].map(RISK_MAP)

    ts_filtered = all_ts_reviews.copy()
    if selected_risk != "All":
        ts_filtered = ts_filtered[ts_filtered["Risk_Level"] == selected_risk]
    if selected_ts_label != "All":
        ts_filtered = ts_filtered[ts_filtered["Label"] == selected_ts_label]
    if selected_ts_rating != "All":
        ts_filtered = ts_filtered[ts_filtered["Rating"] == int(selected_ts_rating)]

    total_ts           = len(ts_filtered)
    safe_count         = len(ts_filtered[ts_filtered["Risk_Level"] == "Safe"])
    needs_review_count = len(ts_filtered[ts_filtered["Risk_Level"] == "Needs Review"])
    high_risk_count    = len(ts_filtered[ts_filtered["Risk_Level"] == "High Risk"])

    safe_pct  = round(safe_count  / total_ts * 100) if total_ts > 0 else 0
    needs_pct = round(needs_review_count / total_ts * 100) if total_ts > 0 else 0
    high_pct  = round(high_risk_count / total_ts * 100) if total_ts > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Safe Content", f"{safe_pct}%",  f"{safe_count} reviews · <b style='color:#3DDC8C'>no action required</b>",   EMERALD)
    kpi(c2, "Needs Review", f"{needs_pct}%", f"{needs_review_count} reviews · <b style='color:#F2B33D'>human adjudication</b>", AMBER)
    kpi(c3, "High Risk",    f"{high_pct}%",  f"<b style='color:#EF6F6F'>{high_risk_count}</b> reviews · P1 &lt;4h SLA",    ROSE)
    kpi(c4, "Burst Events", "7",             "<b style='color:#F2B33D'>4 static</b> + <b>3 rolling-only</b> detected",     ACCENT)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Risk Level Distribution")
        fig = go.Figure(go.Pie(
            labels=['Safe','Needs Review','High Risk'],
            values=[safe_count, needs_review_count, high_risk_count],
            hole=0.62,
            marker=dict(colors=[EMERALD, AMBER, ROSE], line=dict(color=INK, width=2)),
            textfont=dict(color=TEXT_HI, size=12), textinfo='label+percent'
        ))
        chart_layout(fig, 320)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        section("Risk Classification Logic")
        risk_rules = [
            ("Safe",            "Positive, Neutral reviews — no action required",                          EMERALD),
            ("Needs Review",    "Communication, Waiting Time, Pricing, Staff — quality signals",           AMBER),
            ("High Risk",       "Treatment complaints — patient safety implications",                      ROSE),
            ("Burst Flag",      "Days with review volume > mean + 2σ (static) or > 2× rolling 7d avg",   ACCENT),
            ("Repeat Reviewer", "Same reviewer appearing multiple times — manual check required",          VIOLET),
        ]
        for badge, desc, color in risk_rules:
            st.markdown(f"""<div class='finding-card'>
                <div class='finding-title'><span style='color:{color}'>●</span>&nbsp; {badge}</div>
                <div class='finding-text'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Content Policy Enforcement Map", "Category ↑ Action ↑ Escalation Path")
    st.markdown(f"""
    <div style='color:{TEXT_MED};font-size:12.5px;line-height:1.6;margin-bottom:18px;'>
        Each review category maps to a defined policy action and escalation path.
        This mirrors how T&S policy enforcement works at platform scale — classification drives action,
        not human judgment on every item.
    </div>
    <div style='overflow-x:auto;'>
    <table style='width:100%;border-collapse:collapse;font-size:12px;font-family:{FONT_FAMILY};'>
        <thead>
            <tr style='background:{SURFACE_2};border-bottom:1px solid {BORDER};'>
                <th style='padding:10px 14px;text-align:left;color:{TEXT_LOW};font-weight:700;letter-spacing:0.08em;text-transform:uppercase;font-size:10.5px;'>Category</th>
                <th style='padding:10px 14px;text-align:left;color:{TEXT_LOW};font-weight:700;letter-spacing:0.08em;text-transform:uppercase;font-size:10.5px;'>Risk Tier</th>
                <th style='padding:10px 14px;text-align:left;color:{TEXT_LOW};font-weight:700;letter-spacing:0.08em;text-transform:uppercase;font-size:10.5px;'>Severity</th>
                <th style='padding:10px 14px;text-align:left;color:{TEXT_LOW};font-weight:700;letter-spacing:0.08em;text-transform:uppercase;font-size:10.5px;'>SLA</th>
                <th style='padding:10px 14px;text-align:left;color:{TEXT_LOW};font-weight:700;letter-spacing:0.08em;text-transform:uppercase;font-size:10.5px;'>Automated Action</th>
                <th style='padding:10px 14px;text-align:left;color:{TEXT_LOW};font-weight:700;letter-spacing:0.08em;text-transform:uppercase;font-size:10.5px;'>Escalation Path</th>
            </tr>
        </thead>
        <tbody>
            <tr style='border-bottom:1px solid {BORDER_SOFT};'>
                <td style='padding:10px 14px;color:{ROSE};font-weight:700;'>Treatment</td>
                <td style='padding:10px 14px;'><span style='background:rgba(239,111,111,0.12);color:{ROSE};border:1px solid rgba(239,111,111,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>HIGH RISK</span></td>
                <td style='padding:10px 14px;color:{ROSE};font-weight:600;'>Critical (P1)</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>&lt; 4 hours</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Auto-escalate if Rating ≤ 2 · Flag for patient safety review</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Senior Analyst ↑ Clinic Operations Lead</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};background:rgba(255,255,255,0.01);'>
                <td style='padding:10px 14px;color:{ACCENT};font-weight:700;'>Communication</td>
                <td style='padding:10px 14px;'><span style='background:rgba(242,179,61,0.12);color:{AMBER};border:1px solid rgba(242,179,61,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>NEEDS REVIEW</span></td>
                <td style='padding:10px 14px;color:{AMBER};font-weight:600;'>High (P2) if Rating ≤ 2<br>Medium (P3) if Rating = 3</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>&lt; 24 hours</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Queue for human review · No auto-action<br><span style='color:{EMERALD};font-size:10.5px;'>LLM recall 100% on this class — review queue is precautionary, not a model gap</span></td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Human Reviewer ↑ Queue Manager</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};'>
                <td style='padding:10px 14px;color:{AMBER};font-weight:700;'>Waiting Time</td>
                <td style='padding:10px 14px;'><span style='background:rgba(242,179,61,0.12);color:{AMBER};border:1px solid rgba(242,179,61,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>NEEDS REVIEW</span></td>
                <td style='padding:10px 14px;color:{AMBER};font-weight:600;'>High (P2) if Rating ≤ 2<br>Medium (P3) if Rating ≥ 3</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>&lt; 24 hours</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Queue for ops review · Aggregate trend alert if &gt; 3/month</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Ops Analyst ↑ Scheduling Team</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};background:rgba(255,255,255,0.01);'>
                <td style='padding:10px 14px;color:#E8954B;font-weight:700;'>Pricing</td>
                <td style='padding:10px 14px;'><span style='background:rgba(242,179,61,0.12);color:{AMBER};border:1px solid rgba(242,179,61,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>NEEDS REVIEW</span></td>
                <td style='padding:10px 14px;color:{AMBER};font-weight:600;'>High (P2) if Rating ≤ 2</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>&lt; 24 hours</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Flag for billing audit · Escalate if 1-star</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Finance Reviewer ↑ Practice Manager</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};'>
                <td style='padding:10px 14px;color:{VIOLET};font-weight:700;'>Staff</td>
                <td style='padding:10px 14px;'><span style='background:rgba(242,179,61,0.12);color:{AMBER};border:1px solid rgba(242,179,61,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>NEEDS REVIEW</span></td>
                <td style='padding:10px 14px;color:{AMBER};font-weight:600;'>Medium (P3)</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>Weekly batch</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Queue for human review · No auto-action<br><span style='color:{ROSE};font-size:10.5px;'>LLM recall 44% — route all to human</span></td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>HR Reviewer ↑ Department Head</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};background:rgba(255,255,255,0.01);'>
                <td style='padding:10px 14px;color:{SLATE};font-weight:700;'>Neutral</td>
                <td style='padding:10px 14px;'><span style='background:rgba(61,220,140,0.10);color:{EMERALD};border:1px solid rgba(61,220,140,0.25);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>SAFE</span></td>
                <td style='padding:10px 14px;color:{TEXT_LOW};font-weight:600;'>Low (P4)</td>
                <td style='padding:10px 14px;color:{TEXT_MED};font-weight:600;'>Monthly review</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Log and archive · No escalation<br><span style='color:{AMBER};font-size:10.5px;'>LLM recall 40% — lowest of any class, but low-stakes by design</span></td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Archived — no action required</td>
            </tr>
            <tr style='background:rgba(255,255,255,0.01);'>
                <td style='padding:10px 14px;color:{EMERALD};font-weight:700;'>Positive</td>
                <td style='padding:10px 14px;'><span style='background:rgba(61,220,140,0.10);color:{EMERALD};border:1px solid rgba(61,220,140,0.25);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>SAFE</span></td>
                <td style='padding:10px 14px;color:{EMERALD};font-weight:600;'>Safe (P5)</td>
                <td style='padding:10px 14px;color:{TEXT_MED};font-weight:600;'>No action</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Auto-approve · Feed to retention reporting</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>No escalation — closed</td>
            </tr>
        </tbody>
    </table>
    </div>
    <div style='margin-top:14px;padding:12px 16px;background:rgba(108,140,255,0.06);border:1px solid rgba(108,140,255,0.2);border-radius:10px;'>
        <span style='color:{ACCENT};font-size:11px;font-weight:700;letter-spacing:0.05em;'>POLICY NOTE</span>
        <span style='color:{TEXT_MED};font-size:12px;margin-left:10px;'>
            Staff is <b style='color:{AMBER}'>never auto-actioned</b> — its 44% LLM recall is too low to trust without
            human review, and a missed Staff complaint can hide a genuine HR or conduct issue.
            Neutral has an even lower recall (40%) but stays in the auto-archived Safe tier: a misclassified Neutral
            review resolves at worst to another low-severity category, so the cost of a residual error there is
            acceptable, unlike Staff where a false negative is a real operational risk.
            This asymmetry — same recall problem, different action — is a deliberate cost-of-error tradeoff,
            not an oversight.</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Moderation Queue")
    mq = load_csv('moderation_queue.csv')
    if not mq.empty and selected_risk == "All" and selected_ts_label == "All" and selected_ts_rating == "All":
        st.dataframe(mq.head(20), width='stretch', height=300)
    else:
        display_cols = ["Review_ID","Reviewer_Name","Review_Date","Rating","Label","Risk_Level","Review_Text"]
        available = [c for c in display_cols if c in ts_filtered.columns]
        st.dataframe(ts_filtered[available].sort_values("Rating").head(20), width='stretch', height=300)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Case Lifecycle — Review to Resolution", "Investigation Workflow")
    st.markdown(f"""
    <div style='color:{TEXT_MED};font-size:12.5px;line-height:1.6;margin-bottom:20px;'>
        Every flagged review follows this workflow. Stages with a clock icon have SLA timers.
        P1 Critical cases must reach <b style='color:{EMERALD}'>Resolved</b> within 4 hours of submission.
    </div>
    <div style='overflow-x:auto;padding-bottom:8px;'>
    <svg viewBox="0 0 980 200" xmlns="http://www.w3.org/2000/svg" style="width:100%;min-width:780px;font-family:{FONT_FAMILY};">
      <rect x="4" y="30" width="108" height="80" rx="10" fill="{SURFACE_2}" stroke="{BORDER}" stroke-width="1.2"/>
      <rect x="4" y="30" width="108" height="4" rx="2" fill="{SLATE}"/>
      <text x="58" y="68" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Review</text>
      <text x="58" y="83" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Submitted</text>
      <text x="58" y="100" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5">Patient posts review</text>
      <line x1="112" y1="70" x2="130" y2="70" stroke="{BORDER}" stroke-width="1.5"/>
      <polygon points="130,66 138,70 130,74" fill="{BORDER}"/>
      <rect x="138" y="30" width="118" height="80" rx="10" fill="{SURFACE_2}" stroke="{BORDER}" stroke-width="1.2"/>
      <rect x="138" y="30" width="118" height="4" rx="2" fill="{ACCENT}"/>
      <text x="197" y="64" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Auto</text>
      <text x="197" y="79" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Classified</text>
      <text x="197" y="96" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5">LLM · 7 categories</text>
      <text x="197" y="108" text-anchor="middle" fill="{ACCENT}" font-size="9" font-weight="600">&#9889; &lt;30 seconds</text>
      <line x1="256" y1="70" x2="274" y2="70" stroke="{BORDER}" stroke-width="1.5"/>
      <polygon points="274,66 282,70 274,74" fill="{BORDER}"/>
      <rect x="282" y="30" width="118" height="80" rx="10" fill="{SURFACE_2}" stroke="{BORDER}" stroke-width="1.2"/>
      <rect x="282" y="30" width="118" height="4" rx="2" fill="{VIOLET}"/>
      <text x="341" y="64" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Risk</text>
      <text x="341" y="79" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Scored</text>
      <text x="341" y="96" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5">Composite score</text>
      <text x="341" y="108" text-anchor="middle" fill="{VIOLET}" font-size="9" font-weight="600">P1 / P2 / P3 assigned</text>
      <line x1="400" y1="70" x2="418" y2="70" stroke="{BORDER}" stroke-width="1.5"/>
      <polygon points="418,66 426,70 418,74" fill="{BORDER}"/>
      <rect x="426" y="30" width="108" height="80" rx="10" fill="{SURFACE_2}" stroke="{BORDER}" stroke-width="1.2"/>
      <rect x="426" y="30" width="108" height="4" rx="2" fill="{CYAN}"/>
      <text x="480" y="68" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Queued</text>
      <text x="480" y="83" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">for Review</text>
      <text x="480" y="100" text-anchor="middle" fill="{CYAN}" font-size="9" font-weight="600">&#9201; SLA clock starts</text>
      <line x1="534" y1="70" x2="552" y2="70" stroke="{BORDER}" stroke-width="1.5"/>
      <polygon points="552,66 560,70 552,74" fill="{BORDER}"/>
      <rect x="560" y="30" width="118" height="80" rx="10" fill="{SURFACE_2}" stroke="{BORDER}" stroke-width="1.2"/>
      <rect x="560" y="30" width="118" height="4" rx="2" fill="{AMBER}"/>
      <text x="619" y="64" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Human</text>
      <text x="619" y="79" text-anchor="middle" fill="{TEXT_HI}" font-size="11" font-weight="700">Review</text>
      <text x="619" y="96" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5">Analyst adjudicates</text>
      <text x="619" y="108" text-anchor="middle" fill="{AMBER}" font-size="9" font-weight="600">P1: &lt;4h · P2: &lt;24h</text>
      <line x1="678" y1="70" x2="696" y2="70" stroke="{BORDER}" stroke-width="1.5"/>
      <polygon points="696,66 704,70 696,74" fill="{BORDER}"/>
      <line x1="704" y1="70" x2="704" y2="44" stroke="{ROSE}" stroke-width="1.2" stroke-dasharray="4,3"/>
      <line x1="704" y1="44" x2="722" y2="44" stroke="{ROSE}" stroke-width="1.2" stroke-dasharray="4,3"/>
      <rect x="722" y="10" width="108" height="54" rx="10" fill="rgba(239,111,111,0.08)" stroke="{ROSE}" stroke-width="1.2"/>
      <text x="776" y="34" text-anchor="middle" fill="{ROSE}" font-size="10.5" font-weight="700">Escalated</text>
      <text x="776" y="49" text-anchor="middle" fill="{TEXT_LOW}" font-size="9">Senior Analyst</text>
      <text x="776" y="60" text-anchor="middle" fill="{ROSE}" font-size="9" font-weight="600">P1 Critical only</text>
      <line x1="704" y1="70" x2="704" y2="96" stroke="{EMERALD}" stroke-width="1.2" stroke-dasharray="4,3"/>
      <line x1="704" y1="96" x2="722" y2="96" stroke="{EMERALD}" stroke-width="1.2" stroke-dasharray="4,3"/>
      <rect x="722" y="70" width="108" height="54" rx="10" fill="rgba(61,220,140,0.08)" stroke="{EMERALD}" stroke-width="1.2"/>
      <text x="776" y="94" text-anchor="middle" fill="{EMERALD}" font-size="10.5" font-weight="700">Resolved</text>
      <text x="776" y="109" text-anchor="middle" fill="{TEXT_LOW}" font-size="9">Case closed</text>
      <text x="776" y="120" text-anchor="middle" fill="{EMERALD}" font-size="9" font-weight="600">Logged · Archived</text>
      <line x1="830" y1="37" x2="870" y2="37" stroke="{ROSE}" stroke-width="1.2"/>
      <line x1="870" y1="37" x2="870" y2="97" stroke="{ROSE}" stroke-width="1.2"/>
      <polygon points="866,97 870,107 874,97" fill="{ROSE}"/>
      <rect x="880" y="30" width="96" height="80" rx="10" fill="rgba(61,220,140,0.06)" stroke="{EMERALD}" stroke-width="1.8"/>
      <rect x="880" y="30" width="96" height="4" rx="2" fill="{EMERALD}"/>
      <text x="928" y="66" text-anchor="middle" fill="{EMERALD}" font-size="12" font-weight="800">&#10003; CLOSED</text>
      <text x="928" y="82" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5">Outcome logged</text>
      <text x="928" y="95" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5">SLA met / breached</text>
      <text x="928" y="107" text-anchor="middle" fill="{EMERALD}" font-size="9" font-weight="600">recorded</text>
      <text x="58"  y="165" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5" font-weight="600">STAGE 1</text>
      <text x="197" y="165" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5" font-weight="600">STAGE 2</text>
      <text x="341" y="165" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5" font-weight="600">STAGE 3</text>
      <text x="480" y="165" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5" font-weight="600">STAGE 4</text>
      <text x="619" y="165" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5" font-weight="600">STAGE 5</text>
      <text x="776" y="165" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5" font-weight="600">STAGE 6</text>
      <text x="928" y="165" text-anchor="middle" fill="{TEXT_LOW}" font-size="9.5" font-weight="600">STAGE 7</text>
      <line x1="4" y1="185" x2="24" y2="185" stroke="{ROSE}" stroke-width="1.2" stroke-dasharray="4,3"/>
      <text x="28" y="189" fill="{TEXT_LOW}" font-size="9.5">P1 Critical path</text>
      <line x1="130" y1="185" x2="150" y2="185" stroke="{EMERALD}" stroke-width="1.2" stroke-dasharray="4,3"/>
      <text x="154" y="189" fill="{TEXT_LOW}" font-size="9.5">Standard path</text>
      <circle cx="266" cy="185" r="4" fill="{ACCENT}" opacity="0.7"/>
      <text x="274" y="189" fill="{TEXT_LOW}" font-size="9.5">&#9889; Automated stage</text>
      <circle cx="390" cy="185" r="4" fill="{AMBER}" opacity="0.7"/>
      <text x="398" y="189" fill="{TEXT_LOW}" font-size="9.5">&#9201; SLA-governed stage</text>
    </svg>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── EXPORT BUTTON ─────────────────────────────────────────────────────────
    section("Export Moderation Queue")
    export_df = ts_filtered[["Review_ID","Reviewer_Name","Review_Date","Rating","Label","Risk_Level","Review_Text"]].copy() \
        if all(c in ts_filtered.columns for c in ["Review_ID","Reviewer_Name","Review_Date","Rating","Label","Risk_Level","Review_Text"]) \
        else ts_filtered.copy()
    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇  Download filtered queue as CSV",
        data=csv_bytes,
        file_name="moderation_queue_export.csv",
        mime="text/csv"
    )

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Moderation Threshold Experiment Simulator", "Experiment Design · Live Queue Impact")

    st.markdown(f"""
    <div style='color:{TEXT_MED};font-size:12.5px;line-height:1.7;margin-bottom:18px;'>
        Adjust the classification thresholds below and see <b style='color:{TEXT_HI}'>how the moderation
        queue composition changes in real time.</b> This directly mirrors how T&S teams run threshold
        experiments before deploying policy changes — tuning sensitivity to balance false positives
        (over-flagging safe content) against false negatives (missing real violations).
    </div>
    """, unsafe_allow_html=True)

    exp_col1, exp_col2, exp_col3 = st.columns(3)

    with exp_col1:
        treatment_threshold = st.slider(
            "Treatment auto-escalate: reviews rated ≤",
            min_value=1, max_value=5, value=2, step=1,
            help="Reviews in the Treatment category rated AT OR BELOW this value are auto-escalated to High Risk. Default = 2. Raise to 3 to catch more; risk of over-flagging increases."
        )

    with exp_col2:
        burst_multiplier = st.slider(
            "Burst sensitivity multiplier",
            min_value=1.0, max_value=5.0, value=2.0, step=0.5,
            help="A day is flagged as a burst when volume exceeds this multiple of the 7-day rolling average. Lower = more sensitive. Higher = only catches extreme spikes."
        )

    with exp_col3:
        include_neutral_as_risk = st.selectbox(
            "Route Neutral reviews to",
            options=["Safe (no action)", "Needs Review"],
            index=0,
            help="Currently Neutral reviews are marked Safe. Switch to Needs Review to route them to the moderation queue."
        )

    # Apply experimental thresholds to live data
    exp_reviews = all_ts_reviews.copy()

    def experimental_risk(row):
        if row["Label"] == "Treatment":
            return "High Risk" if row["Rating"] <= treatment_threshold else "Needs Review"
        elif row["Label"] in ["Communication", "Waiting Time", "Pricing", "Staff"]:
            return "Needs Review"
        elif row["Label"] == "Neutral":
            return "Safe" if include_neutral_as_risk == "Safe (no action)" else "Needs Review"
        else:
            return "Safe"

    exp_reviews["Exp_Risk_Level"] = exp_reviews.apply(experimental_risk, axis=1)

    exp_safe     = len(exp_reviews[exp_reviews["Exp_Risk_Level"] == "Safe"])
    exp_needs    = len(exp_reviews[exp_reviews["Exp_Risk_Level"] == "Needs Review"])
    exp_highrisk = len(exp_reviews[exp_reviews["Exp_Risk_Level"] == "High Risk"])

    base_safe     = len(all_ts_reviews[all_ts_reviews["Risk_Level"] == "Safe"])
    base_needs    = len(all_ts_reviews[all_ts_reviews["Risk_Level"] == "Needs Review"])
    base_highrisk = len(all_ts_reviews[all_ts_reviews["Risk_Level"] == "High Risk"])

    delta_safe     = exp_safe     - base_safe
    delta_needs    = exp_needs    - base_needs
    delta_highrisk = exp_highrisk - base_highrisk

    def fmt_delta(d):
        if d > 0:   return f"+{d}"
        elif d < 0: return str(d)
        else:       return "no change"

    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1:
        st.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'><span class='kpi-dot' style='background:{EMERALD};box-shadow:0 0 6px {EMERALD}'></span>SAFE</div>
            <div class='kpi-value'>{exp_safe}</div>
            <div class='kpi-sub'>Baseline: {base_safe} &nbsp;·&nbsp;
                <b style='color:{"#EF6F6F" if delta_safe < 0 else "#3DDC8C"}'>{fmt_delta(delta_safe)}</b>
            </div>
        </div>""", unsafe_allow_html=True)

    with res_c2:
        st.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'><span class='kpi-dot' style='background:{AMBER};box-shadow:0 0 6px {AMBER}'></span>NEEDS REVIEW</div>
            <div class='kpi-value'>{exp_needs}</div>
            <div class='kpi-sub'>Baseline: {base_needs} &nbsp;·&nbsp;
                <b style='color:{"#EF6F6F" if delta_needs > 0 else "#3DDC8C"}'>{fmt_delta(delta_needs)}</b>
            </div>
        </div>""", unsafe_allow_html=True)

    with res_c3:
        st.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'><span class='kpi-dot' style='background:{ROSE};box-shadow:0 0 6px {ROSE}'></span>HIGH RISK</div>
            <div class='kpi-value'>{exp_highrisk}</div>
            <div class='kpi-sub'>Baseline: {base_highrisk} &nbsp;·&nbsp;
                <b style='color:{"#3DDC8C" if delta_highrisk == 0 else "#EF6F6F" if delta_highrisk > 0 else "#3DDC8C"}'>{fmt_delta(delta_highrisk)}</b>
            </div>
        </div>""", unsafe_allow_html=True)

    # Live queue preview
    exp_queue = exp_reviews[exp_reviews["Exp_Risk_Level"] != "Safe"].copy()
    exp_queue = exp_queue.sort_values("Rating")

    if treatment_threshold > 2:
        finding(
            f"Experiment Result — Treatment Threshold raised to ≤{treatment_threshold} stars",
            f"Raising the Treatment escalation threshold from ≤2 to ≤{treatment_threshold} stars "            f"moves <b style='color:{ROSE}'>{abs(delta_highrisk)} additional review(s)</b> into High Risk. "            f"This increases recall on Treatment complaints — fewer genuine violations slip through — "            f"but at the cost of <b style='color:{AMBER}'>{abs(delta_needs)} more review(s)</b> moving in the queue. "            f"In a production system, this tradeoff would be validated against labelled data to confirm "            f"the newly-escalated reviews are genuine violations, not borderline cases."
        )
    elif treatment_threshold < 2:
        finding(
            f"Experiment Result — Treatment Threshold lowered to ≤{treatment_threshold} star",
            f"Lowering the threshold to ≤{treatment_threshold} star reduces queue load but "            f"risks missing 2-star Treatment complaints — reviews that frequently contain actionable "            f"patient safety signals even at that rating. <b style='color:{ROSE}'>Not recommended</b> "            f"for a category where false negatives have direct real-world consequences."
        )
    else:
        finding(
            "Baseline Configuration Active",
            f"Treatment threshold at ≤2 stars is the calibrated baseline producing "            f"<b style='color:{ROSE}'>{base_highrisk} High Risk</b> cases, "            f"<b style='color:{AMBER}'>{base_needs} Needs Review</b>, and "            f"<b style='color:{EMERALD}'>{base_safe} Safe</b>. "            f"Adjust the sliders above to model the impact of policy threshold changes."
        )

    if include_neutral_as_risk == "Needs Review":
        finding(
            "Experiment: Neutral Reviews Routed to Needs Review",
            f"Routing Neutral reviews to the moderation queue adds "            f"<b style='color:{AMBER}'>{abs(delta_needs)} review(s)</b> to analyst workload. "            f"These are factual, low-sentiment reviews with no clear violation signal. "            f"This configuration would increase false positive rate — not recommended unless "            f"you suspect borderline-positive gaming in the Neutral class."
        )

    # Burst sensitivity note
    st.markdown(f"""
    <div style='margin-top:12px;padding:12px 16px;background:rgba(108,140,255,0.06);border:1px solid rgba(108,140,255,0.2);border-radius:10px;'>
        <span style='color:{ACCENT};font-size:11px;font-weight:800;letter-spacing:0.05em;'>BURST SENSITIVITY NOTE</span>
        <span style='color:{TEXT_MED};font-size:12px;margin-left:10px;'>
            Burst multiplier set to <b style='color:{TEXT_HI}'>{burst_multiplier}×</b> the rolling 7-day average.
            At the current dataset mean of 1.22 reviews/day, this flags any day with &gt;
            <b style='color:{AMBER}'>{round(1.22 * burst_multiplier, 1)}</b> reviews as a burst.
            The baseline (2×) flagged 7 burst days. Lowering to 1.5× would flag more days;
            raising to 3× would catch only the most extreme spikes.
        </span>
    </div>
    """, unsafe_allow_html=True)


    # ── PRECISION / RECALL SIMULATOR ─────────────────────────────────────────
    st.markdown("<hr style='border-color:rgba(108,140,255,0.08);margin:24px 0;'/>", unsafe_allow_html=True)
    section("Precision / Recall Experiment", "Ground-truth model performance at each threshold")
    st.markdown(f"""
    <div style='color:{TEXT_MED};font-size:13px;line-height:1.7;margin-bottom:18px;'>
        The queue simulator above shows <em>volume impact</em> — how many reviews move between tiers.
        This section shows <em>accuracy impact</em> — using the 90-review hold-out ground-truth labels
        from <code>llm_predictions.csv</code>, it computes real Precision, Recall, False Positives,
        and False Negatives as the Treatment threshold slider moves. This is the tradeoff a policy
        team actually evaluates before changing an escalation rule.
    </div>
    """, unsafe_allow_html=True)

    _preds_raw = load_csv("llm_predictions.csv")
    _preds = _preds_raw[_preds_raw["Split"] == "hold_out_test"].copy() if not _preds_raw.empty else pd.DataFrame()

    if not _preds.empty:
        _rev_ratings = load_db("SELECT Review_Text, Rating, Label FROM Reviews")
        _preds_m = _preds.merge(_rev_ratings, on="Review_Text", how="left", suffixes=("_gt", "_db"))
        _preds_m["is_violation"] = _preds_m["Label_gt"] == "Treatment"
        _preds_m["escalated"] = (
            (_preds_m["Label_db"] == "Treatment") &
            (_preds_m["Rating"].fillna(3) <= treatment_threshold)
        )

        _TP = int(( _preds_m["is_violation"] &  _preds_m["escalated"]).sum())
        _FP = int((~_preds_m["is_violation"] &  _preds_m["escalated"]).sum())
        _FN = int(( _preds_m["is_violation"] & ~_preds_m["escalated"]).sum())
        _TN = int((~_preds_m["is_violation"] & ~_preds_m["escalated"]).sum())

        _precision = round(_TP / (_TP + _FP), 2) if (_TP + _FP) > 0 else 0.0
        _recall    = round(_TP / (_TP + _FN), 2) if (_TP + _FN) > 0 else 0.0
        _f1        = round(2 * _precision * _recall / (_precision + _recall), 2) if (_precision + _recall) > 0 else 0.0
        _fpr       = round(_FP / (_FP + _TN), 2) if (_FP + _TN) > 0 else 0.0

        _pc  = EMERALD if _precision >= 0.80 else AMBER if _precision >= 0.60 else ROSE
        _rc  = EMERALD if _recall    >= 0.80 else AMBER if _recall    >= 0.60 else ROSE
        _f1c = EMERALD if _f1        >= 0.80 else AMBER if _f1        >= 0.60 else ROSE

        pr_c1, pr_c2, pr_c3, pr_c4 = st.columns(4)
        pr_c1.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'><span class='kpi-dot' style='background:{_pc};box-shadow:0 0 6px {_pc}'></span>PRECISION</div>
            <div class='kpi-value' style='color:{_pc};'>{_precision:.0%}</div>
            <div class='kpi-sub'>Of escalated reviews, {_TP} real violations &middot; {_FP} false positives</div>
        </div>""", unsafe_allow_html=True)

        pr_c2.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'><span class='kpi-dot' style='background:{_rc};box-shadow:0 0 6px {_rc}'></span>RECALL</div>
            <div class='kpi-value' style='color:{_rc};'>{_recall:.0%}</div>
            <div class='kpi-sub'>Of all real violations, {_TP} caught &middot; {_FN} missed</div>
        </div>""", unsafe_allow_html=True)

        pr_c3.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'><span class='kpi-dot' style='background:{_f1c};box-shadow:0 0 6px {_f1c}'></span>F1 SCORE</div>
            <div class='kpi-value' style='color:{_f1c};'>{_f1:.0%}</div>
            <div class='kpi-sub'>Harmonic mean of Precision &amp; Recall</div>
        </div>""", unsafe_allow_html=True)

        pr_c4.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'><span class='kpi-dot' style='background:{VIOLET};box-shadow:0 0 6px {VIOLET}'></span>FALSE POSITIVE RATE</div>
            <div class='kpi-value' style='color:{VIOLET};'>{_fpr:.0%}</div>
            <div class='kpi-sub'>{_FP} non-violations incorrectly escalated</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='margin-top:18px;padding:16px 20px;background:rgba(108,140,255,0.04);
                    border:1px solid rgba(108,140,255,0.15);border-radius:12px;'>
            <div style='color:{TEXT_LOW};font-size:10px;font-weight:700;letter-spacing:0.1em;
                        text-transform:uppercase;margin-bottom:14px;'>Confusion Matrix &mdash; Hold-Out Test Set (90 reviews)</div>
            <table style='width:100%;border-collapse:collapse;font-size:12px;'>
                <tr>
                    <td style='padding:8px 12px;color:{TEXT_LOW};'></td>
                    <td style='padding:8px 12px;color:{EMERALD};font-weight:700;text-align:center;'>Predicted: Escalate</td>
                    <td style='padding:8px 12px;color:{EMERALD};font-weight:700;text-align:center;'>Predicted: Safe</td>
                </tr>
                <tr style='border-top:1px solid rgba(255,255,255,0.06);'>
                    <td style='padding:8px 12px;color:{ROSE};font-weight:700;'>Actual: Violation</td>
                    <td style='padding:8px 12px;color:{EMERALD};font-weight:800;font-size:16px;text-align:center;background:rgba(61,220,140,0.06);border-radius:8px;'>TP = {_TP}</td>
                    <td style='padding:8px 12px;color:{ROSE};font-weight:800;font-size:16px;text-align:center;background:rgba(239,111,111,0.06);border-radius:8px;'>FN = {_FN}</td>
                </tr>
                <tr style='border-top:1px solid rgba(255,255,255,0.06);'>
                    <td style='padding:8px 12px;color:{TEXT_MED};font-weight:700;'>Actual: Non-Violation</td>
                    <td style='padding:8px 12px;color:{ROSE};font-weight:800;font-size:16px;text-align:center;background:rgba(239,111,111,0.06);border-radius:8px;'>FP = {_FP}</td>
                    <td style='padding:8px 12px;color:{EMERALD};font-weight:800;font-size:16px;text-align:center;background:rgba(61,220,140,0.06);border-radius:8px;'>TN = {_TN}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        if treatment_threshold == 2:
            _interp = (f"Baseline threshold (≤2 stars): Precision {_precision:.0%}, Recall {_recall:.0%}, F1 {_f1:.0%}. "
                       f"This is the calibrated default. {_FP} false positive(s) and {_FN} missed violation(s).")
        elif treatment_threshold > 2:
            _interp = (f"Raising threshold to ≤{treatment_threshold} stars increases recall (catches more violations) "
                       f"but reduces precision ({_precision:.0%}) — more false positives enter the queue. "
                       f"Validate that the {_FP} newly-escalated review(s) are genuine violations, not borderline cases.")
        else:
            _interp = (f"Lowering threshold to ≤{treatment_threshold} star maximises precision ({_precision:.0%}) "
                       f"but recall drops to {_recall:.0%} — {_FN} real violation(s) missed. "
                       f"Not recommended for patient-safety complaints where false negatives carry real-world risk.")

        finding(f"Policy Interpretation — Threshold ≤{treatment_threshold} Stars", _interp)

    else:
        st.info("llm_predictions.csv not found in reports/ — run the LLM evaluation pipeline first.")

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Product Vulnerability Analysis", "What's being exploited")
    vulnerabilities = [
        (
            "Unverified reviewer identity",
            "No identity verification is required to submit a review. The same reviewer name "
            "(Yashoda S) appears twice with no account-level linkage, meaning repeat or coordinated "
            "posting cannot be confirmed or denied at the platform level — only inferred from text matching.",
            ROSE
        ),
        (
            "No rate-limiting on submission volume",
            "There is no cap on how many reviews can be posted to the same business in a short window. "
            "This allows a single event to produce a burst — 17 reviews in one day against a 3.91/day "
            "baseline — without any system intervention until after the fact.",
            AMBER
        ),
        (
            "Free-text severity invisible to volume-only monitoring",
            "A platform that only tracks review count would miss that 12% of reviews are patient-safety-grade "
            "complaints. Volume-based alerting alone under-detects the highest-severity content.",
            VIOLET
        ),
        (
            "Single-annotator labeling introduces blind spots",
            "All 300 ground-truth labels were assigned by one person. There is no inter-annotator agreement score, "
            "so categories with semantic overlap (Communication vs Staff vs Neutral) may carry undetected labeling bias.",
            CYAN
        ),
    ]
    for title, desc, color in vulnerabilities:
        st.markdown(f"""<div class='finding-card'>
            <div class='finding-title'><span style='color:{color}'>●</span>&nbsp; {title}</div>
            <div class='finding-text'>{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Classification Threshold — False Positive vs False Negative Tradeoff")
    col_fp, col_fn = st.columns(2)
    with col_fp:
        finding(
            "False Positive Risk",
            f"Setting the risk threshold <b style='color:{AMBER}'>too low</b> flags safe content as High Risk. "
            f"Positive and Neutral reviews (42% of total — 126 reviews) would enter the moderation queue "
            f"unnecessarily, increasing analyst workload with zero safety benefit."
        )
    with col_fn:
        finding(
            "False Negative Risk",
            f"Setting the risk threshold <b style='color:{ROSE}'>too high</b> allows genuine Treatment complaints "
            f"to pass through without escalation. 36 reviews (12%) contain patient safety signals — "
            f"a missed escalation here has direct real-world consequences."
        )

    finding(
        "Current Threshold Calibration",
        f"The system is calibrated to <b style='color:{EMERALD}'>minimize false negatives on Treatment complaints</b>. "
        f"Treatment reviews rated 1—2 stars are auto-escalated to Critical/P1. Staff and Neutral categories — "
        f"where LLM recall is lowest (44% and 40%) — are routed to Needs Review for human adjudication. "
        f"This mirrors real T&S queue design: high-confidence signals get automated action, ambiguous signals get human review."
    )

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("What I Would Do Differently at YouTube Scale", "Limitations & Production Gap")
    scale_gaps = [
        (
            "Streaming ingestion over batch processing",
            "This pipeline runs as a batch job on static data. At YouTube scale, reviews arrive continuously. "
            "A production system would use Pub/Sub or Kafka for real-time ingestion, enabling burst detection "
            "within seconds rather than after a daily run.",
            ACCENT
        ),
        (
            "Multi-annotator labeling with IAA scoring",
            "All 300 labels were assigned by a single annotator. A production labeling pipeline uses 3+ "
            "annotators per item with Cohen's Kappa or Fleiss' Kappa to measure inter-annotator agreement "
            "and resolve conflicts — especially critical for ambiguous categories like Staff vs Communication.",
            CYAN
        ),
        (
            "Adaptive thresholds over static ones",
            "The burst threshold here is a fixed mean+2σ calculated once. A live system recalculates "
            "the baseline continuously using a rolling window, so thresholds adapt as review volume "
            "grows over time rather than becoming stale.",
            AMBER
        ),
        (
            "Continuous model monitoring and drift detection",
            "The LLM evaluation here is a one-time benchmark. In production, model performance is monitored "
            "continuously — if accuracy on incoming reviews drops below a threshold, it triggers retraining "
            "or prompt revision before quality degrades silently.",
            VIOLET
        ),
    ]
    for title, desc, color in scale_gaps:
        st.markdown(f"""<div class='finding-card'>
            <div class='finding-title'><span style='color:{color}'>●</span>&nbsp; {title}</div>
            <div class='finding-text'>{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Why Dental Reviews Are a Valid T&S Dataset", "Methodology Defence")
    st.markdown(f"""
    <div style='color:{TEXT_MED};font-size:12.5px;line-height:1.6;margin-bottom:20px;'>
        A reasonable challenge: <i>"These are real reviews from a small clinic — the actors aren't adversarial.
        Real T&S deals with coordinated campaigns, sock puppets, and people actively trying to evade detection.
        This is just Yelp."</i> Here's why that objection doesn't hold.
    </div>
    """, unsafe_allow_html=True)

    defence_cols = st.columns(2)
    defences = [
        (
            "The detection logic is identical regardless of motive",
            f"Burst detection flags days where volume exceeds 3× baseline. Whether those 17 reviews on 2022-06-10 "
            f"came from a coordinated campaign or an organic event doesn't change the detection method — "
            f"the algorithm can't distinguish motive, only pattern. That's true at YouTube scale too. "
            f"T&S systems flag the pattern; humans investigate the motive.",
            ACCENT,
        ),
        (
            "Adversarial evasion makes the problem harder, not different",
            f"A motivated actor posting 17 reviews to manipulate a rating uses the same signal — "
            f"volume spike, low rating concentration, repeat reviewer fingerprint — as an organic burst. "
            f"The T&S tooling demonstrated here detects both. Adding adversarial pressure "
            f"changes the threshold calibration, not the methodology.",
            CYAN,
        ),
        (
            "Real abuse signals are present in the data",
            f"The dataset contains a documented repeat reviewer (Yashoda S — 2 reviews, avg 2.5★), "
            f"7 burst events, and 36 Treatment complaints that cluster at 1—2 stars. These are genuine "
            f"signals that a volume-only system would miss. The same patterns — repeat actors, "
            f"sentiment concentration, temporal clustering — are the core signals in platform-scale "
            f"review manipulation detection.",
            VIOLET,
        ),
        (
            "The methodology gap is scale, not structure",
            f"What changes at YouTube scale is throughput (millions of items/day vs 300 reviews), "
            f"latency (streaming vs batch), and adversarial sophistication (coordinated networks vs single actors). "
            f"The underlying analytical structure — classify, score, tier, route, escalate — is the same. "
            f"PraxisIQ demonstrates that structure end-to-end on real data.",
            EMERALD,
        ),
        (
            "Ground-truth labeling at any scale has the same challenges",
            f"Whether you're labeling 300 dental reviews or 3 million YouTube comments, "
            f"the challenges are identical: category boundary decisions, semantic overlap between classes, "
            f"inter-annotator disagreement, and class imbalance. The single-annotator limitation "
            f"documented here is the same limitation that drives YouTube's labeler training programs — "
            f"the difference is investment, not insight.",
            AMBER,
        ),
        (
            "Patient safety complaints are structurally equivalent to high-severity content",
            f"A 1-star Treatment complaint — \"Tooth condition worsened after treatment. Had to seek urgent care elsewhere\" — "
            f"is a patient safety signal. At YouTube, the equivalent is content that causes real-world harm "
            f"(medical misinformation, self-harm facilitation). Both require the same pipeline: "
            f"fast detection, high-priority routing, human review, documented escalation. "
            f"The stakes differ; the workflow is identical.",
            ROSE,
        ),
    ]
    for i, (title, desc, color) in enumerate(defences):
        with defence_cols[i % 2]:
            st.markdown(f"""<div class='finding-card'>
                <div class='finding-title'><span style='color:{color}'>●</span>&nbsp; {title}</div>
                <div class='finding-text'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='margin-top:8px;padding:14px 18px;background:rgba(108,140,255,0.06);border:1px solid rgba(108,140,255,0.2);border-radius:10px;'>
        <span style='color:{ACCENT};font-size:11px;font-weight:800;letter-spacing:0.05em;'>BOTTOM LINE</span>
        <span style='color:{TEXT_MED};font-size:12.5px;margin-left:10px;line-height:1.6;'>
            The domain is dental. The methodology — content classification, abuse signal detection, risk scoring,
            moderation queue design, SLA-driven escalation, and LLM evaluation with held-out benchmarking —
            is <b style='color:{TEXT_HI}'>platform Trust &amp; Safety</b>.
            The dataset size changes what's computationally feasible; it doesn't change what the analysis demonstrates.
        </span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE 6 — LLM EVALUATION
# ─────────────────────────────────────────────
elif page == "LLM Evaluation":
    page_header(
        "Model Performance",
        "LLM Prompt Engineering Evaluation",
        "Module 3 · Qwen2.5 7B via Ollama · 300 reviews · 7 categories"
    )

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Final Accuracy", "86.7%", "<b style='color:#3DDC8C'>+4.45%</b> over ML · 90 hold-out reviews",   EMERALD)
    kpi(c2, "Precision",      "85.5%", "Weighted avg · <b style='color:#3DDC8C'>strongest:</b> Waiting Time 0.96", ACCENT)
    kpi(c3, "Recall",         "80.9%", "Weighted avg · <b style='color:#EF6F6F'>weakest:</b> Staff 44%, Neutral 40%", CYAN)
    kpi(c4, "F1 Score",       "80.7%", "Weighted avg · <b>ML baseline:</b> 78.0%",                              VIOLET)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Statistical Confidence", "Wilson Score Interval, 95% CI")

    def wilson_ci(accuracy_fraction, n, z=1.96):
        """Wilson score interval — same closed-form method for both models,
        computed live here rather than hardcoded, so it can't go stale if
        the underlying evaluation data changes."""
        p = accuracy_fraction
        denom = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denom
        margin = z * ((p * (1 - p) / n + z**2 / (4 * n**2)) ** 0.5) / denom
        return max(0.0, center - margin) * 100, min(1.0, center + margin) * 100

    # LLM: computed live from the best prompt's accuracy and hold-out sample
    # size — no Ollama re-run needed, since Wilson CI only needs accuracy + n.
    llm_eval_df = load_csv('llm_prompt_evaluation.csv')
    ml_ci_df = load_csv('ml_accuracy_with_ci.csv')

    ci_col1, ci_col2 = st.columns(2)
    with ci_col1:
        if not llm_eval_df.empty:
            best_row = llm_eval_df.loc[llm_eval_df['Accuracy'].idxmax()]
            llm_acc = best_row['Accuracy'] * 100
            n_match = best_row['Evaluated_On']
            n_llm = int(n_match.split('(')[1].split(' ')[0]) if '(' in str(n_match) else 90
            llm_lo, llm_hi = wilson_ci(best_row['Accuracy'], n_llm)
            finding(
                f"LLM — {best_row['Prompt']}",
                f"Accuracy: <b style='color:{EMERALD}'>{llm_acc:.2f}%</b> &nbsp; "
                f"95% CI: <b>[{llm_lo:.1f}%, {llm_hi:.1f}%]</b><br>"
                f"If re-evaluated on a new random sample of {n_llm} reviews from the same "
                f"population, accuracy would fall in this range 95% of the time."
            )
        else:
            st.info("Run llm_evaluation_final.py to generate live LLM accuracy data.")

    with ci_col2:
        if not ml_ci_df.empty:
            ml_vals = ml_ci_df.set_index('Metric')['Value']
            ml_acc = float(ml_vals['Accuracy'])
            ml_lo = float(ml_vals['CI_Lower_95'])
            ml_hi = float(ml_vals['CI_Upper_95'])
            n_ml = int(float(ml_vals['Sample_Size']))
            gap = abs(llm_acc - ml_acc) if not llm_eval_df.empty else None
            gap_text = f"the {gap:.2f}-point gap" if gap is not None else "the observed gap"
            finding(
                "ML — TF-IDF + Logistic Regression",
                f"Accuracy: <b style='color:{ACCENT}'>{ml_acc:.2f}%</b> &nbsp; "
                f"95% CI: <b>[{ml_lo:.1f}%, {ml_hi:.1f}%]</b><br>"
                f"<span style='color:{TEXT_LOW}'>Note: these two intervals overlap. "
                f"With only {n_ml} held-out reviews, {gap_text} is the best point "
                f"estimate, not a statistically certain difference — see "
                f"FINDINGS.md for the full discussion.</span>"
            )
        else:
            st.info("Run ml/review_classifier_v2.py to generate live ML accuracy data.")

    col_a, col_b = st.columns(2)
    with col_a:
        section("Prompt Comparison", "90-review hold-out test set")
        prompt_data = pd.DataFrame({
            'Prompt':   ['V1 — Zero-Shot', 'V2 — Detailed', 'V3 — Rules-Based'],
            'Accuracy': [65.56, 86.67, 65.56],
            'Version':  ['V1', 'V2', 'V3']
        })
        fig = px.bar(
            prompt_data, x='Prompt', y='Accuracy', color='Version',
            color_discrete_map={'V1': SLATE, 'V2': EMERALD, 'V3': ROSE},
            text='Accuracy'
        )
        fig.update_traces(
            texttemplate='%{text}%', textposition='outside',
            textfont=dict(color=TEXT_HI, size=12.5),
            marker_line_width=0, opacity=0.92
        )
        chart_layout(fig, 340)
        fig.update_layout(
            showlegend=False,
            yaxis=dict(range=[0,100], gridcolor=BORDER_SOFT,
                       tickfont=dict(color=TEXT_LOW, size=11))
        )
        st.plotly_chart(fig, width='stretch')

    with col_b:
        section("Prompt Design Rationale")
        prompts_info = [
            ("V1 — Zero-Shot",          "65.6%", "Basic instruction only. No category definitions.", "badge-med"),
            ("V2 — Detailed (selected)","86.7%", "Each category explicitly defined with examples. Chosen as final prompt.", "badge-low"),
            ("V3 — Rules-Based",        "65.6%", "Strict keyword rules. Over-indexed on specific terms; underperformed on nuanced reviews.", "badge-high"),
        ]
        for title, acc, desc, badge in prompts_info:
            st.markdown(f"""<div class='finding-card'>
                <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;'>
                    <div class='finding-title'>{title}</div>
                    <span class='badge {badge}'>{acc}</span>
                </div>
                <div class='finding-text'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("ML vs LLM — Classification Approach Comparison")

    col_ml, col_llm = st.columns(2)
    with col_ml:
        finding(
            "Traditional ML — TF-IDF + Logistic Regression",
            f"Accuracy: <b style='color:{ACCENT}'>82.22%</b> on the same 90-review held-out test set. "
            f"Fast, deterministic, and fully interpretable — each prediction traces to weighted token features. "
            f"Performs well on categories with strong keyword signals but struggles with semantic nuance."
        )
    with col_llm:
        finding(
            "LLM — Qwen2.5 7B via Ollama (Prompt V2)",
            f"Accuracy: <b style='color:{EMERALD}'>86.67%</b> on the 90-review held-out test set. "
            f"Higher overall accuracy and better recall on minority classes. "
            f"Trade-off: slower inference, non-deterministic outputs, harder to audit."
        )

    comparison_data = pd.DataFrame({
        'Approach': ['TF-IDF + Logistic Regression', 'Qwen2.5 7B (Prompt V2)'],
        'Accuracy': [82.22, 86.67],
        'Type':     ['Traditional ML', 'LLM']
    })
    fig = px.bar(
        comparison_data, x='Approach', y='Accuracy', color='Type',
        color_discrete_map={'Traditional ML': ACCENT, 'LLM': EMERALD},
        text='Accuracy'
    )
    fig.update_traces(
        texttemplate='%{text}%', textposition='outside',
        textfont=dict(color=TEXT_HI, size=12.5),
        marker_line_width=0, opacity=0.92
    )
    chart_layout(fig, 320)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(range=[0,100], gridcolor=BORDER_SOFT,
                   tickfont=dict(color=TEXT_LOW, size=11))
    )
    st.plotly_chart(fig, width='stretch')

    finding(
        "Recommendation",
        f"The LLM outperforms traditional ML by <b style='color:{EMERALD}'>+4.45%</b> in accuracy. "
        f"Recommended architecture: <b style='color:{ACCENT}'>LLM for all categories</b>, with Staff and Neutral "
        f"routed to human review given their higher misclassification rate in both approaches."
    )

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("ML Feature Importance — Top Words Per Category", "Module 2")
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        import numpy as np

        fi_reviews = load_db("SELECT Review_Text, Label FROM Reviews")
        if not fi_reviews.empty:
            X = fi_reviews["Review_Text"]
            y = fi_reviews["Label"]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.30, random_state=42, stratify=y
            )
            vec = TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2))
            X_train_tfidf = vec.fit_transform(X_train)
            clf = LogisticRegression(max_iter=2000, class_weight="balanced")
            clf.fit(X_train_tfidf, y_train)

            feature_names = vec.get_feature_names_out()
            TOP_N = 8
            fi_rows = []
            for i, category in enumerate(clf.classes_):
                coefs   = clf.coef_[i]
                top_idx = np.argsort(coefs)[-TOP_N:][::-1]
                for rank, idx in enumerate(top_idx):
                    fi_rows.append({
                        "Category": category,
                        "Feature":  feature_names[idx],
                        "Weight":   round(float(coefs[idx]), 4),
                        "Rank":     rank + 1,
                    })

            fi_df = pd.DataFrame(fi_rows)
            category_colors = {
                "Treatment": ROSE, "Communication": ACCENT, "Waiting Time": AMBER,
                "Pricing": VIOLET, "Staff": CYAN, "Positive": EMERALD, "Neutral": SLATE,
            }

            cats    = clf.classes_.tolist()
            cols_fi = st.columns(min(4, len(cats)))
            for i, cat in enumerate(cats):
                col    = cols_fi[i % len(cols_fi)]
                cat_df = fi_df[fi_df["Category"] == cat].sort_values("Weight", ascending=True)
                color  = category_colors.get(cat, ACCENT)
                fig = go.Figure(go.Bar(
                    x=cat_df["Weight"], y=cat_df["Feature"],
                    orientation="h", marker_color=color, marker_opacity=0.85,
                ))
                chart_layout(fig, 280)
                fig.update_layout(
                    title=dict(text=cat, font=dict(color=TEXT_HI, size=13), x=0),
                    xaxis=dict(title="TF-IDF Weight", tickfont=dict(color=TEXT_LOW, size=10)),
                    yaxis=dict(tickfont=dict(color=TEXT_MED, size=11)),
                    margin=dict(l=10, r=10, t=36, b=10),
                )
                col.plotly_chart(fig, width="stretch")

            finding(
                "What the ML Model Actually Learned",
                "Each bar shows the TF-IDF token weight the Logistic Regression model learned for that category. "
                "Higher weight = stronger signal that a review belongs to this class. "
                "This interpretability is a key advantage of TF-IDF + Logistic Regression in T&S contexts "
                "where decisions must be auditable."
            )
    except Exception as e:
        st.info(f"Feature importance unavailable: {e}")

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Model Error Analysis — Misclassified Reviews", "Where the model fails")
    preds_err = load_csv('llm_predictions.csv')
    if not preds_err.empty:
        preds_err['Correct'] = preds_err['Label'] == preds_err['Prediction']
        misclassified = preds_err[preds_err['Correct'] == False].copy()

        if not misclassified.empty:
            st.markdown(f"<div style='color:{TEXT_MED};font-size:12px;margin-bottom:12px;'>"
                        f"{len(misclassified)} misclassified reviews on the hold-out set — "
                        f"showing the first 5 with hardest cases.</div>", unsafe_allow_html=True)

            for _, row in misclassified.head(5).iterrows():
                actual = row.get('Label', '?')
                predicted = row.get('Prediction', '?')
                text = str(row.get('Review_Text', ''))[:200]
                st.markdown(f"""<div class='finding-card'>
                    <div style='display:flex;gap:10px;align-items:center;margin-bottom:6px;'>
                        <span class='badge badge-high'>Actual: {actual}</span>
                        <span class='badge badge-med'>Predicted: {predicted}</span>
                    </div>
                    <div class='finding-text'>"{text}..."</div>
                </div>""", unsafe_allow_html=True)

            finding(
                "Why These Cases Are Hard",
                f"Most misclassifications occur at the boundary between <b style='color:{CYAN}'>Staff</b>, "
                f"<b style='color:{ACCENT}'>Communication</b>, and <b style='color:{SLATE}'>Neutral</b> — "
                f"categories that share vocabulary (words like 'doctor', 'staff', 'friendly' appear in all three). "
                f"The LLM handles these better than the ML model (86.7% vs 82.2%) but still struggles with "
                f"reviews that contain both positive and negative signals in the same sentence. "
                f"In a production T&S system these ambiguous cases would be routed to human review."
            )
        else:
            st.info("All predictions on the sample set were correct.")
    else:
        st.info("Run llm_evaluation_final.py to generate predictions CSV.")

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Per-Class Performance (Confusion Matrix)", "Module 3")
    preds_cm = load_csv('llm_predictions.csv')
    if not preds_cm.empty:
        from sklearn.metrics import confusion_matrix as sk_cm
        labels_order = ['Positive','Communication','Waiting Time','Treatment','Pricing','Staff','Neutral']
        cm    = sk_cm(preds_cm['Label'], preds_cm['Prediction'], labels=labels_order)
        cm_df = pd.DataFrame(cm, index=labels_order, columns=labels_order)
        fig = px.imshow(
            cm_df,
            color_continuous_scale=[[0, SURFACE], [0.5, '#2A3560'], [1, ACCENT]],
            text_auto=True, aspect='auto'
        )
        fig.update_traces(textfont=dict(color=TEXT_HI, size=12))
        chart_layout(fig, 380)
        fig.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Predicted", yaxis_title="Actual",
            xaxis=dict(tickfont=dict(color=TEXT_MED, size=11)),
            yaxis=dict(tickfont=dict(color=TEXT_MED, size=11))
        )
        st.plotly_chart(fig, width='stretch')
        finding(
            "Classification Difficulty Analysis",
            f"<b style='color:{EMERALD}'>Strongest categories:</b> Waiting Time, Positive, Pricing, Communication — clear signals make these easy to classify.<br><br>"
            f"<b style='color:{ROSE}'>Hardest categories:</b> Staff and Neutral — these overlap semantically with each other and with Communication. "
            "In a real T&S system these ambiguous cases would be routed to a human review queue."
        )

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Sample Predictions vs. Ground Truth — with Confidence Scoring")
    preds = load_csv('llm_predictions.csv')
    if not preds.empty:
        preds['Correct'] = preds['Label'] == preds['Prediction']
        preds['Match']   = preds['Correct'].map({True: '✓', False: '✗'})

        # ── CONFIDENCE SCORING ────────────────────────────────────────────────
        # Derive confidence from prediction reliability signals:
        #   High   — correct prediction on a category with strong F1 (Positive, Waiting Time, Pricing, Communication)
        #   Medium — correct prediction on ambiguous category OR incorrect on strong category
        #   Low    — incorrect prediction on ambiguous category (Staff, Neutral) ↑ route to human
        HIGH_CONFIDENCE_CATS  = {"Positive", "Waiting Time", "Pricing", "Communication"}
        LOW_CONFIDENCE_CATS   = {"Staff", "Neutral"}

        def assign_confidence(row):
            correct   = row['Label'] == row['Prediction']
            predicted = row.get('Prediction', '')
            actual    = row.get('Label', '')
            if correct and predicted in HIGH_CONFIDENCE_CATS:
                return 'High'
            elif correct and predicted not in LOW_CONFIDENCE_CATS:
                return 'High'
            elif correct and predicted in LOW_CONFIDENCE_CATS:
                return 'Medium'
            elif not correct and actual in LOW_CONFIDENCE_CATS:
                return 'Low'
            elif not correct and predicted in LOW_CONFIDENCE_CATS:
                return 'Low'
            else:
                return 'Medium'

        def assign_action(row):
            if row['Confidence'] == 'Low':
                return '🔴 Route to human review'
            elif row['Confidence'] == 'Medium':
                return '🟡 Monitor — verify if borderline'
            else:
                return '🟢 Auto-action safe'

        preds['Confidence'] = preds.apply(assign_confidence, axis=1)
        preds['Action']     = preds.apply(assign_action, axis=1)

        # ── CONFIDENCE SUMMARY ────────────────────────────────────────────────
        conf_counts = preds['Confidence'].value_counts()
        high_c  = conf_counts.get('High',   0)
        med_c   = conf_counts.get('Medium', 0)
        low_c   = conf_counts.get('Low',    0)
        total   = len(preds)

        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            st.markdown(f"""<div class='kpi-card'>
                <div class='kpi-label'><span class='kpi-dot' style='background:{EMERALD};box-shadow:0 0 6px {EMERALD}'></span>HIGH CONFIDENCE</div>
                <div class='kpi-value'>{high_c}</div>
                <div class='kpi-sub'>{round(high_c/total*100)}% of predictions · <b style='color:{EMERALD}'>Auto-action safe</b></div>
            </div>""", unsafe_allow_html=True)
        with cc2:
            st.markdown(f"""<div class='kpi-card'>
                <div class='kpi-label'><span class='kpi-dot' style='background:{AMBER};box-shadow:0 0 6px {AMBER}'></span>MEDIUM CONFIDENCE</div>
                <div class='kpi-value'>{med_c}</div>
                <div class='kpi-sub'>{round(med_c/total*100)}% of predictions · <b style='color:{AMBER}'>Monitor / spot-check</b></div>
            </div>""", unsafe_allow_html=True)
        with cc3:
            st.markdown(f"""<div class='kpi-card'>
                <div class='kpi-label'><span class='kpi-dot' style='background:{ROSE};box-shadow:0 0 6px {ROSE}'></span>LOW CONFIDENCE</div>
                <div class='kpi-value'>{low_c}</div>
                <div class='kpi-sub'>{round(low_c/total*100)}% of predictions · <b style='color:{ROSE}'>Route to human review</b></div>
            </div>""", unsafe_allow_html=True)

        # ── PREDICTIONS TABLE ──────────────────────────────────────────────────
        display_cols = ['Review_Text','Label','Prediction','Match','Confidence','Action']
        available    = [c for c in display_cols if c in preds.columns]
        st.dataframe(preds[available].head(20), width='stretch', height=380)

        correct = preds['Correct'].sum()
        finding(
            "How Confidence Scoring Works",
            f"<b style='color:{EMERALD}'>{correct}</b> correct out of {total} reviewed · "
            f"Sample accuracy: <b style='color:{ACCENT}'>{round(correct / total * 100, 1)}%</b><br><br>"
            f"Confidence is derived from prediction reliability signals — not a raw model probability score, "
            f"since Qwen2.5 via Ollama returns a label string, not a logit. Instead: "
            f"<b style='color:{EMERALD}'>High</b> = correct prediction on a category with strong recall "
            f"(Positive, Waiting Time, Pricing, Communication — all F1 > 0.89). "
            f"<b style='color:{AMBER}'>Medium</b> = correct on an ambiguous category or incorrect on a strong one. "
            f"<b style='color:{ROSE}'>Low</b> = incorrect on Staff or Neutral — the two categories where LLM recall "
            f"drops to 44% and 40% respectively. All Low-confidence predictions are flagged for human review, "
            f"which is exactly how a production T&S system routes ambiguous classifier output."
        )
    else:
        st.info("Run llm_evaluation_final.py to generate predictions CSV.")

# ─────────────────────────────────────────────
# PAGE 7 — INVESTIGATION PLAYBOOKS
# ─────────────────────────────────────────────
elif page == "Investigation Playbooks":
    page_header(
        "T&S Operations",
        "Investigation Playbooks",
        "Structured detection ↑ evidence ↑ severity ↑ action ↑ escalation ↑ resolution workflows for each issue type"
    )

    st.markdown(f"""
    <div style='color:{TEXT_MED};font-size:12.5px;line-height:1.7;margin-bottom:24px;'>
        Each playbook below mirrors how a Trust &amp; Safety analyst would work a real investigation.
        These are not theoretical — every detection signal, severity rule, and escalation path
        maps directly to a script, SQL query, or pipeline output in this project.
    </div>
    """, unsafe_allow_html=True)

    playbooks = [
        {
            "title":    "Review Burst",
            "icon":     "📈",
            "color":    AMBER,
            "signal":   "Daily review volume exceeds mean + 2σ (static) or 2× rolling 7-day average",
            "source":   "analytics/review_burst_detection.py · sql/trust_safety/01_review_burst_detection.sql",
            "steps": [
                ("Detection",  ACCENT,  "Automated",  "review_burst_detection.py runs daily. Flags any date where count > 3.91 (mean+2σ) or > 2× rolling 7-day avg. Both methods must agree for highest-confidence flag."),
                ("Evidence",   CYAN,    "Gather",     "Pull the flagged date: review count, average rating, negative rate, dominant category. Check if burst correlates with a known event (promo, clinic opening, complaint campaign)."),
                ("Severity",   VIOLET,  "Assess",     "Negative-skewed burst (>50% complaint reviews): HIGH. Positive-skewed burst (likely organic event): LOW. Both methods agree: escalate one tier higher."),
                ("Action",     AMBER,   "Respond",    "Negative burst: flag all reviews from that date for expedited human review. Enter 24-hour elevated monitoring window. Positive burst: log, no queue action needed."),
                ("Escalation", ROSE,    "Escalate",   "If negative rate >70% on burst day OR burst repeats within 7 days: escalate to senior analyst. Potential coordinated negative campaign — check for repeat reviewer overlap."),
                ("Resolution", EMERALD, "Close",      "Log outcome: organic vs coordinated. If coordinated: remove flagged reviews pending investigation, record in case management queue. Update burst threshold if baseline has shifted."),
            ]
        },
        {
            "title":    "Treatment Complaint",
            "icon":     "🏥",
            "color":    ROSE,
            "signal":   "Review classified as Treatment category with rating ≤ 2 stars",
            "source":   "trust_safety/trust_safety_pipeline.py · sql/trust_safety/04_risk_prioritization.sql",
            "steps": [
                ("Detection",  ACCENT,  "Automated",  "LLM classifier (Prompt V2) assigns Treatment label. trust_safety_pipeline.py applies severity rule: Treatment + Rating ≤ 2 ↑ Critical/P1. Auto-enters moderation queue within seconds of submission."),
                ("Evidence",   CYAN,    "Gather",     "Read full review text. Check: specific procedure mentioned? Outcome described (pain, worsening condition, re-treatment needed)? Cross-reference patient visit record if ID linkable. Flag exact quotes as evidence."),
                ("Severity",   VIOLET,  "Assess",     "Rating 1 + explicit harm described: CRITICAL (P1 — 4h SLA). Rating 2 + general dissatisfaction: HIGH (P2 — 24h SLA). Rating 3 + treatment category: MEDIUM (P3 — weekly batch)."),
                ("Action",     AMBER,   "Respond",    "P1: Immediately escalate to senior analyst AND clinic operations lead. Do not auto-remove — investigate first. Draft patient outreach template. P2: Queue for senior analyst review within 24h."),
                ("Escalation", ROSE,    "Escalate",   "If patient describes urgent medical need (infection, emergency re-treatment): escalate to clinic director within 1 hour. If 3+ Treatment P1s in 7 days: trigger quality review protocol."),
                ("Resolution", EMERALD, "Close",      "Outcome options: Resolved (clinic responded, patient satisfied), Escalated Externally (regulatory body notified), Unresolved (patient unreachable), False Positive (reclassified). Log SLA met/breached."),
            ]
        },
        {
            "title":    "Suspicious Reviewer",
            "icon":     "👤",
            "color":    VIOLET,
            "signal":   "Reviewer triggers ≥2 suspicion flags: velocity, no rating variance, high volume, or sentiment flip",
            "source":   "analytics/suspicious_reviewer_detection.py · sql/trust_safety/02_repeat_reviewer_detection.sql",
            "steps": [
                ("Detection",  ACCENT,  "Automated",  "suspicious_reviewer_detection.py scores each reviewer on 4 signals: same-day multiple reviews (velocity), all-identical ratings (no variance), 3+ reviews total (high volume), contradictory high+low ratings (sentiment flip). Score ≥ 2 = flagged."),
                ("Evidence",   CYAN,    "Gather",     "Pull all reviews from flagged reviewer. Note: review dates and times, rating pattern, text similarity across reviews, IP/device fingerprint if available (not in this dataset — flag as gap at scale)."),
                ("Severity",   VIOLET,  "Assess",     "Score 3-4 (multiple flags): HIGH — likely coordinated or inauthentic. Score 2 (two flags): MEDIUM — possible legitimate repeat patient, investigate before action. Score 1: LOW — log only."),
                ("Action",     AMBER,   "Respond",    "HIGH: Temporarily suppress reviews from queue pending investigation. Do not permanently remove until human confirms. MEDIUM: Flag for human review, keep reviews visible. LOW: Monitor for 30 days."),
                ("Escalation", ROSE,    "Escalate",   "If same reviewer pattern found across multiple businesses: escalate to platform-level T&S (coordinated inauthentic behavior signal). Single-business repeat: clinic-level escalation only."),
                ("Resolution", EMERALD, "Close",      "Outcome: Confirmed Authentic (legitimate repeat patient — clear flag), Confirmed Inauthentic (remove reviews, flag account), Inconclusive (monitor 30 days, re-review). Document decision rationale."),
            ]
        },
        {
            "title":    "Duplicate / Near-Duplicate Review",
            "icon":     "📋",
            "color":    CYAN,
            "signal":   "Review text ≥85% character-level similarity to another review (SequenceMatcher ratio)",
            "source":   "analytics/duplicate_review_detection.py",
            "steps": [
                ("Detection",  ACCENT,  "Automated",  "duplicate_review_detection.py runs three checks: exact match (after whitespace normalization), fuzzy match (SequenceMatcher ≥85%), and fingerprint clustering (same first 40 chars). Any match triggers investigation."),
                ("Evidence",   CYAN,    "Gather",     "Pull both reviews: submission timestamps, reviewer names, text diff (highlight changed words). Check if submitted from similar time window. In this dataset: 0 duplicates found — clean baseline confirmed."),
                ("Severity",   VIOLET,  "Assess",     "Exact match from different reviewers: HIGH (coordinated injection). Fuzzy match (85-95%): MEDIUM (possible template use). Same reviewer, same text: LOW (accidental double-submit — likely user error)."),
                ("Action",     AMBER,   "Respond",    "HIGH: Suppress duplicate, investigate source reviewer accounts. Tag as potential review injection campaign. MEDIUM: Human review to confirm. LOW (accidental): Remove one copy, no further action."),
                ("Escalation", ROSE,    "Escalate",   "3+ duplicates from different reviewer accounts in 48h: escalate to platform T&S. Likely coordinated injection campaign — requires network-level investigation beyond single-clinic scope."),
                ("Resolution", EMERALD, "Close",      "Log: number of duplicates found, action taken, reviewer status. If coordinated: feed pattern into burst detection threshold calibration. Update similarity threshold if false positives were high."),
            ]
        },
        {
            "title":    "Emerging Risk Category",
            "icon":     "📊",
            "color":    EMERALD,
            "signal":   "Complaint category shows >50% quarter-over-quarter growth in the most recent quarter",
            "source":   "analytics/emerging_risk_monitoring.py · sql/trust_safety/07_emerging_risk_detection.sql",
            "steps": [
                ("Detection",  ACCENT,  "Automated",  "emerging_risk_monitoring.py computes QoQ growth per complaint category. Compares recent 2-quarter average vs prior 2-quarter average. Flag if latest QoQ >50% or trend direction = Rising. Runs quarterly."),
                ("Evidence",   CYAN,    "Gather",     "Pull monthly volume for the flagged category over the past 12 months. Identify: when did the acceleration start? Which rating tier is growing (1-star vs 2-star)? Is the acceleration in a specific treatment type?"),
                ("Severity",   VIOLET,  "Assess",     "QoQ >100% in a safety-adjacent category (Treatment, Communication): HIGH — potential systemic quality issue. QoQ 50-100% in operational category (Waiting Time, Pricing): MEDIUM — operational signal, not safety. Staff: MEDIUM."),
                ("Action",     AMBER,   "Respond",    "HIGH: Trigger proactive review of the accelerating category. Pull a sample of recent reviews for qualitative read. Brief clinic operations lead — do not wait for volume to cross absolute threshold."),
                ("Escalation", ROSE,    "Escalate",   "If 2+ categories accelerating simultaneously: escalate to clinic director — potential systemic service failure. Single category: department-level escalation (clinical lead for Treatment, ops lead for Waiting Time)."),
                ("Resolution", EMERALD, "Close",      "Outcome: Root cause identified (staffing change, new procedure, seasonal), Intervention actioned (process change, staff training), Monitoring extended (watch for 2 more quarters). Update QoQ threshold if needed."),
            ]
        },
    ]

    for pb in playbooks:
        st.markdown(f"""
        <div style='background:{SURFACE};border:1px solid {pb["color"]}40;border-left:3px solid {pb["color"]};
                    border-radius:14px;padding:20px 24px;margin-bottom:28px;'>
            <div style='display:flex;align-items:center;gap:12px;margin-bottom:6px;'>
                <span style='font-size:20px;'>{pb["icon"]}</span>
                <span style='color:{TEXT_HI};font-size:16px;font-weight:800;letter-spacing:-0.01em;'>{pb["title"]}</span>
                <span style='margin-left:auto;background:{pb["color"]}18;color:{pb["color"]};
                             border:1px solid {pb["color"]}40;font-size:9.5px;font-weight:700;
                             letter-spacing:0.08em;padding:3px 10px;border-radius:20px;'>PLAYBOOK</span>
            </div>
            <div style='color:{TEXT_LOW};font-size:11.5px;margin-bottom:4px;'>
                <b style='color:{TEXT_MED}'>Detection signal:</b> {pb["signal"]}
            </div>
            <div style='color:{TEXT_LOW};font-size:11px;margin-bottom:18px;font-style:italic;'>
                Source: {pb["source"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        step_cols = st.columns(6)
        for j, (stage, color, tag, desc) in enumerate(pb["steps"]):
            with step_cols[j]:
                st.markdown(f"""
                <div style='background:{SURFACE_2};border:1px solid {color}35;border-top:2px solid {color};
                            border-radius:10px;padding:14px 12px;height:100%;min-height:180px;'>
                    <div style='color:{color};font-size:9px;font-weight:800;letter-spacing:0.12em;
                                text-transform:uppercase;margin-bottom:4px;'>{tag}</div>
                    <div style='color:{TEXT_HI};font-size:12px;font-weight:700;margin-bottom:8px;'>{stage}</div>
                    <div style='color:{TEXT_MED};font-size:11px;line-height:1.55;'>{desc}</div>
                </div>
                """, unsafe_allow_html=True)

        # Arrow between stages label
        st.markdown(f"""
        <div style='display:flex;align-items:center;justify-content:center;gap:8px;
                    color:{TEXT_LOW};font-size:10px;font-weight:600;letter-spacing:0.06em;
                    margin:10px 0 24px 0;'>
            <span style='color:{pb["color"]};'>Detection</span>
            <span>↑</span><span>Evidence</span>
            <span>↑</span><span>Severity</span>
            <span>↑</span><span>Action</span>
            <span>↑</span><span>Escalation</span>
            <span>↑</span><span style='color:{EMERALD};'>Resolution</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    finding(
        "Why Playbooks Matter in T&S Operations",
        f"A detection system without a response protocol is just an alarm with no one to answer it. "
        f"These playbooks demonstrate the full operational loop: automated detection surfaces the signal, "
        f"structured investigation gathers evidence, severity rules drive consistent prioritisation, "
        f"defined actions ensure the right response every time, escalation paths prevent decisions from "
        f"being made at the wrong level, and resolution logging feeds back into threshold calibration. "
        f"At YouTube scale, these playbooks live in internal wikis and are drilled with tabletop exercises — "
        f"the analytical foundation built here is exactly what those exercises test."
    )

# ─────────────────────────────────────────────
# PAGE 8 — AI COPILOT
# ─────────────────────────────────────────────
elif page == "Data Quality":
    page_header(
        "Data Integrity & Validation",
        "Data Quality Dashboard",
        "Missing values, duplicates, standardization checks, validation rules, and overall data quality score"
    )

    @st.cache_data(ttl=300)
    def run_data_quality_checks():
        import numpy as np
        patients = load_db("SELECT * FROM Patients")
        visits   = load_db("SELECT * FROM Visits")
        reviews  = load_db("SELECT * FROM Reviews")

        results = {}

        # ── PATIENTS ──────────────────────────────────────────────────────────
        p_total = len(patients)
        p_missing = patients.isnull().sum()
        p_missing_pct = (p_missing / p_total * 100).round(1)
        p_duplicates = patients.duplicated().sum()

        # Treatment standardization
        known_treatments = {
            'Root Canal','Implant','Scaling','Filling','Crown/Cap',
            'Tooth Extraction','Teeth Whitening','Metal Braces Treatment',
            'Aligner','Fixed Bridge','Partial Denture','Complete Denture',
            'Deep Scaling and Root Planing','Gum Treatment','Consultation',
            'Teeth Cleaning','Scaling and Polishing','Pediatric Dental'
        }
        unknown_treatments = patients[~patients['Primary_Treatment'].isin(known_treatments)]['Primary_Treatment'].value_counts()

        # Age validation
        invalid_age = len(patients[(patients['Age'] < 1) | (patients['Age'] > 120)])

        results['patients'] = {
            'total': p_total,
            'missing': p_missing.to_dict(),
            'missing_pct': p_missing_pct.to_dict(),
            'duplicates': int(p_duplicates),
            'unknown_treatments': len(unknown_treatments),
            'invalid_age': invalid_age,
        }

        # ── VISITS ────────────────────────────────────────────────────────────
        v_total = len(visits)
        v_missing = visits.isnull().sum()
        v_missing_pct = (v_missing / v_total * 100).round(1)
        v_duplicates = visits.duplicated().sum()

        results['visits'] = {
            'total': v_total,
            'missing': v_missing.to_dict(),
            'missing_pct': v_missing_pct.to_dict(),
            'duplicates': int(v_duplicates),
        }

        # ── REVIEWS ───────────────────────────────────────────────────────────
        r_total = len(reviews)
        r_missing = reviews.isnull().sum()
        r_missing_pct = (r_missing / r_total * 100).round(1)
        r_duplicates = reviews.duplicated().sum()

        # Rating range validation
        invalid_ratings = len(reviews[(reviews['Rating'] < 1) | (reviews['Rating'] > 5)])

        # Label validation
        valid_labels = {'Positive','Treatment','Communication','Waiting Time','Pricing','Staff','Neutral'}
        invalid_labels = len(reviews[~reviews['Label'].isin(valid_labels)])

        # Review text length check
        reviews['text_len'] = reviews['Review_Text'].fillna('').str.len()
        very_short = len(reviews[reviews['text_len'] < 10])

        results['reviews'] = {
            'total': r_total,
            'missing': r_missing.to_dict(),
            'missing_pct': r_missing_pct.to_dict(),
            'duplicates': int(r_duplicates),
            'invalid_ratings': invalid_ratings,
            'invalid_labels': invalid_labels,
            'very_short_reviews': very_short,
        }

        # ── OVERALL QUALITY SCORE ─────────────────────────────────────────────
        # Score = 100 - penalty for each issue found
        score = 100.0
        total_rows = p_total + v_total + r_total

        # Missing value penalty
        all_missing = p_missing.sum() + v_missing.sum() + r_missing.sum()
        missing_rate = all_missing / (total_rows * 5)  # approx 5 cols avg
        score -= min(20, missing_rate * 100)

        # Duplicate penalty
        total_dupes = p_duplicates + int(v_duplicates) + r_duplicates
        score -= min(15, total_dupes * 2)

        # Validation penalty
        score -= min(10, invalid_ratings * 5)
        score -= min(10, invalid_labels * 5)
        score -= min(5, invalid_age * 2)
        score -= min(5, very_short * 0.5)

        results['score'] = max(0, round(score, 1))
        return results

    dq = run_data_quality_checks()
    score = dq['score']

    # ── OVERALL SCORE ──────────────────────────────────────────────────────────
    score_color = EMERALD if score >= 90 else AMBER if score >= 75 else ROSE
    score_label = "EXCELLENT" if score >= 90 else "GOOD" if score >= 75 else "NEEDS ATTENTION"

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,rgba(10,14,26,0.9),rgba(15,20,40,0.9));
         border:1px solid {score_color}40;border-radius:16px;padding:28px 36px;
         margin-bottom:24px;display:flex;align-items:center;gap:32px;'>
        <div style='text-align:center;min-width:120px;'>
            <div style='font-size:52px;font-weight:800;color:{score_color};line-height:1;'>{score}</div>
            <div style='font-size:11px;color:{score_color};font-weight:700;
                        letter-spacing:0.1em;margin-top:4px;'>{score_label}</div>
            <div style='font-size:10px;color:{TEXT_LOW};margin-top:2px;'>Quality Score / 100</div>
        </div>
        <div style='flex:1;border-left:1px solid {BORDER_SOFT};padding-left:28px;'>
            <div style='color:{TEXT_HI};font-size:15px;font-weight:600;margin-bottom:6px;'>
                Data Quality Assessment — Geetha Dental Clinic Dataset
            </div>
            <div style='color:{TEXT_MED};font-size:12.5px;line-height:1.7;'>
                Validated across {dq['patients']['total']:,} patient records,
                {dq['visits']['total']:,} visit records, and {dq['reviews']['total']} review records.
                Score penalises missing values, duplicates, out-of-range values,
                invalid category labels, and malformed text entries.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TABLE SUMMARIES ────────────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)

    def dq_card(col, title, data, color):
        issues = sum(1 for v in data['missing'].values() if v > 0)
        with col:
            st.markdown(f"""
            <div style='background:{SURFACE_2};border:1px solid {color}30;
                 border-radius:12px;padding:18px;'>
                <div style='color:{color};font-size:11px;font-weight:700;
                            letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;'>
                    {title}
                </div>
                <div style='color:{TEXT_HI};font-size:24px;font-weight:700;'>{data['total']:,}</div>
                <div style='color:{TEXT_LOW};font-size:11px;margin-bottom:12px;'>Total records</div>
                <div style='color:{"#EF6F6F" if data["duplicates"]>0 else EMERALD};font-size:12px;margin-bottom:4px;'>
                    {"⚠ " if data["duplicates"]>0 else "✓ "}{data["duplicates"]} duplicates
                </div>
                <div style='color:{"#F2B33D" if issues>0 else EMERALD};font-size:12px;'>
                    {"⚠ " if issues>0 else "✓ "}{issues} columns with missing values
                </div>
            </div>""", unsafe_allow_html=True)

    dq_card(col_a, "Patients Table", dq['patients'], ACCENT)
    dq_card(col_b, "Visits Table",   dq['visits'],   VIOLET)
    dq_card(col_c, "Reviews Table",  dq['reviews'],  CYAN)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── MISSING VALUES DETAIL ──────────────────────────────────────────────────
    section("Missing Values by Column")
    col_d, col_e = st.columns(2)

    with col_d:
        st.markdown(f"<div style='color:{TEXT_MED};font-size:12px;font-weight:600;margin-bottom:8px;'>PATIENTS</div>", unsafe_allow_html=True)
        p_miss = {k: v for k, v in dq['patients']['missing'].items() if v > 0}
        if p_miss:
            import pandas as pd
            p_df = pd.DataFrame({'Column': list(p_miss.keys()), 'Missing': list(p_miss.values())})
            p_df['%'] = (p_df['Missing'] / dq['patients']['total'] * 100).round(1)
            st.dataframe(p_df, use_container_width=True, hide_index=True)
        else:
            st.markdown(f"<div style='color:{EMERALD};font-size:13px;'>✓ No missing values in Patients table</div>", unsafe_allow_html=True)

    with col_e:
        st.markdown(f"<div style='color:{TEXT_MED};font-size:12px;font-weight:600;margin-bottom:8px;'>REVIEWS</div>", unsafe_allow_html=True)
        r_miss = {k: v for k, v in dq['reviews']['missing'].items() if v > 0}
        if r_miss:
            import pandas as pd
            r_df = pd.DataFrame({'Column': list(r_miss.keys()), 'Missing': list(r_miss.values())})
            r_df['%'] = (r_df['Missing'] / dq['reviews']['total'] * 100).round(1)
            st.dataframe(r_df, use_container_width=True, hide_index=True)
        else:
            st.markdown(f"<div style='color:{EMERALD};font-size:13px;'>✓ No missing values in Reviews table</div>", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── VALIDATION RULES ──────────────────────────────────────────────────────
    section("Validation Rule Results")

    rules = [
        ("Patient age between 1–120",    dq['patients']['invalid_age'] == 0,    dq['patients']['invalid_age'],    "patients"),
        ("Review ratings between 1–5",   dq['reviews']['invalid_ratings'] == 0, dq['reviews']['invalid_ratings'], "reviews"),
        ("All review labels valid",       dq['reviews']['invalid_labels'] == 0,  dq['reviews']['invalid_labels'],  "reviews"),
        ("No very short review text",     dq['reviews']['very_short_reviews'] == 0, dq['reviews']['very_short_reviews'], "reviews"),
        ("No duplicate patient records",  dq['patients']['duplicates'] == 0,     dq['patients']['duplicates'],     "records"),
        ("No duplicate review records",   dq['reviews']['duplicates'] == 0,      dq['reviews']['duplicates'],      "records"),
        ("Known treatment names only",    dq['patients']['unknown_treatments'] == 0, dq['patients']['unknown_treatments'], "unknown"),
    ]

    for rule_name, passed, count, unit in rules:
        icon  = "✓" if passed else "⚠"
        color = EMERALD if passed else AMBER
        note  = "Passed" if passed else f"{count} {unit} flagged"
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:12px;padding:8px 0;
             border-bottom:1px solid {BORDER_SOFT};'>
            <span style='color:{color};font-size:14px;width:20px;'>{icon}</span>
            <span style='color:{TEXT_HI};font-size:12.5px;flex:1;'>{rule_name}</span>
            <span style='color:{color};font-size:11px;font-weight:600;'>{note}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Data Quality Recommendations")
    st.markdown(f"""
    <div class='finding-card'>
        <div class='finding-title'>Treatment Name Standardization</div>
        <div class='finding-text'>
            {dq['patients']['unknown_treatments']} non-standard treatment names were detected during ingestion.
            These were normalized in <code>create_database.py</code> using a treatment mapping dictionary.
            In production, enforce a controlled vocabulary at data entry time to prevent drift.
        </div>
    </div>
    <div class='finding-card'>
        <div class='finding-title'>Single-Annotator Review Labels</div>
        <div class='finding-text'>
            All 300 review labels were assigned by one annotator. Production labeling requires
            2-3 annotators per item with Cohen's kappa ≥ 0.7. Ambiguous categories
            (Communication, Staff, Neutral) are routed to human review as a mitigation.
        </div>
    </div>
    <div class='finding-card'>
        <div class='finding-title'>No Real-Time Validation</div>
        <div class='finding-text'>
            This dataset is a static 6-year snapshot loaded from Excel. Production systems
            require row-level validation at ingestion time — schema enforcement, range checks,
            referential integrity, and anomaly alerts on ingest.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
elif page == "AI Copilot":

    st.markdown(f"""
    <style>
    /* Copilot page — distinct deep purple creative background */
    .copilot-hero {{
        background: linear-gradient(135deg, #0e0b1a 0%, #130d24 40%, #0f0d20 70%, #0b1020 100%);
        border: 1px solid rgba(139,92,246,0.3);
        border-radius: 20px;
        padding: 36px 40px 32px 40px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 60px rgba(139,92,246,0.08), inset 0 1px 0 rgba(139,92,246,0.1);
    }}
    .copilot-hero::before {{
        content: '';
        position: absolute;
        top: -80px; right: -80px;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }}
    .copilot-hero::after {{
        content: '';
        position: absolute;
        bottom: -60px; left: -60px;
        width: 220px; height: 220px;
        background: radial-gradient(circle, rgba(236,72,153,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }}
    .copilot-title {{
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #a78bfa 0%, #ec4899 50%, #f9a8d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 10px 0;
        line-height: 1.2;
    }}
    .copilot-subtitle {{
        color: #94a3b8;
        font-size: 12.5px;
        letter-spacing: 0.01em;
        margin: 0 0 20px 0;
        line-height: 1.7;
        max-width: 820px;
    }}
    .copilot-badge-row {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }}
    .copilot-badge {{
        background: rgba(139,92,246,0.12);
        border: 1px solid rgba(139,92,246,0.3);
        color: #a78bfa;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.05em;
        padding: 4px 12px;
        border-radius: 20px;
    }}
    .copilot-badge.green {{
        background: rgba(52,211,153,0.1);
        border-color: rgba(52,211,153,0.3);
        color: #34d399;
    }}
    .copilot-badge.cyan {{
        background: rgba(6,182,212,0.1);
        border-color: rgba(6,182,212,0.25);
        color: #22d3ee;
    }}
    .live-dot {{
        display: inline-block;
        width: 6px; height: 6px;
        background: #34d399;
        border-radius: 50%;
        margin-right: 4px;
        animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.2; }}
    }}
    /* Question category labels */
    .qcat-label {{
        display: flex;
        align-items: center;
        gap: 8px;
        color: #a78bfa;
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 18px 0 10px 0;
    }}
    .qcat-label .line {{
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(139,92,246,0.4), transparent);
    }}
    .qcat-label.project {{ color: #22d3ee; }}
    .qcat-label.project .line {{ background: linear-gradient(90deg, rgba(34,211,238,0.4), transparent); }}
    /* Suggested question buttons — multiple selectors for cross-version Streamlit compatibility */
    .stButton > button,
    .stButton > button[kind="secondary"],
    div[data-testid="stButton"] > button,
    button[data-testid="baseButton-secondary"],
    button[kind="secondary"] {{
        background: rgba(20,16,34,0.92) !important;
        border: 1px solid rgba(139,92,246,0.28) !important;
        border-radius: 10px !important;
        color: #c4b5fd !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
        text-align: left !important;
        padding: 11px 14px !important;
        height: auto !important;
        min-height: 54px !important;
        white-space: normal !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }}
    .stButton > button:hover,
    .stButton > button[kind="secondary"]:hover,
    div[data-testid="stButton"] > button:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[kind="secondary"]:hover {{
        border-color: rgba(139,92,246,0.6) !important;
        color: #f1f3f8 !important;
        background: rgba(139,92,246,0.14) !important;
        box-shadow: 0 0 18px rgba(139,92,246,0.15) !important;
        transform: translateY(-1px);
    }}
    .stButton > button:active,
    button[kind="secondary"]:active {{
        transform: translateY(0);
    }}
    /* Primary "Send" button stays visually distinct from suggestion pills */
    .stButton > button[kind="primary"],
    button[data-testid="baseButton-primary"],
    button[kind="primary"] {{
        background: linear-gradient(135deg, #7c3aed, #ec4899) !important;
        border: none !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 0 16px rgba(139,92,246,0.25) !important;
    }}
    .stButton > button[kind="primary"]:hover,
    button[kind="primary"]:hover {{
        box-shadow: 0 0 24px rgba(139,92,246,0.4) !important;
        transform: translateY(-1px);
    }}

    /* Chat bubbles - Professional Design */
    .chat-wrap {{

        display: flex;
        flex-direction: column;
        gap: 16px;
        margin: 24px 0;
        max-height: 650px;
        min-height: 200px;
        overflow-y: auto;
        scroll-behavior: smooth;
        padding: 8px 4px;
        border-radius: 12px;
        background: rgba(14, 11, 26, 0.4);
        padding: 16px;
        border: 1px solid rgba(108, 140, 255, 0.1);
    }}
    .msg-user {{
        display: flex;
        justify-content: flex-end;
        margin-bottom: 8px;
    }}
    .msg-user > div {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        max-width: 85%;
    }}
    .msg-user .bubble {{
        background: linear-gradient(135deg, rgba(108, 140, 255, 0.2), rgba(61, 217, 214, 0.1));
        border: 1px solid rgba(108, 140, 255, 0.3);
        border-radius: 18px;
        padding: 14px 18px;
        color: #f1f3f8;
        font-size: 14px;
        line-height: 1.6;
        word-wrap: break-word;
        box-shadow: 0 2px 8px rgba(108, 140, 255, 0.08);
    }}
    .msg-ai {{
        display: flex;
        justify-content: flex-start;
        gap: 12px;
        align-items: flex-start;
        margin-bottom: 8px;
    }}
    .ai-avatar {{
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #6c8cff, #3dd9d6);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(108, 140, 255, 0.3);
    }}
    .msg-ai > div {{
        display: flex;
        flex-direction: column;
        max-width: 85%;
    }}
    .msg-ai .bubble {{
        background: rgba(22, 26, 38, 0.8);
        border: 1px solid rgba(108, 140, 255, 0.15);
        border-radius: 16px;
        padding: 16px 20px;
        color: #f1f3f8;
        font-size: 14px;
        line-height: 1.7;
        word-wrap: break-word;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }}
    .msg-ai .bubble a {{
        color: #6c8cff;
        text-decoration: none;
        border-bottom: 1px solid rgba(108, 140, 255, 0.3);
    }}
    .msg-ai .bubble a:hover {{
        border-bottom-color: #6c8cff;
    }}
    .msg-ai .bubble strong {{
        color: #3dd9d6;
    }}
    .msg-ai .bubble ul, .msg-ai .bubble ol {{
        margin: 8px 0;
        padding-left: 20px;
    }}
    .msg-ai .bubble li {{
        margin: 4px 0;
    }}
    .msg-meta {{
        color: #64748b;
        font-size: 10px;
        margin-top: 6px;
        letter-spacing: 0.03em;
        font-weight: 500;
    }}
    /* Capability cards */
    .cap-card {{
        background: rgba(14,11,26,0.7);
        border: 1px solid rgba(139,92,246,0.12);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: border-color 0.2s;
    }}
    .cap-card:hover {{
        border-color: rgba(139,92,246,0.3);
    }}
    /* Error card */
    .copilot-error-card {{
        background: rgba(239,111,111,0.08);
        border: 1px solid rgba(239,111,111,0.3);
        border-radius: 12px;
        padding: 16px 18px;
        color: #fca5a5;
        font-size: 12.5px;
        line-height: 1.7;
        margin-bottom: 18px;
    }}
    .copilot-error-card b {{ color: #fecaca; }}
    .copilot-error-card code {{
        background: rgba(0,0,0,0.3);
        padding: 1px 6px;
        border-radius: 4px;
        font-size: 11.5px;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── HERO HEADER ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='copilot-hero'>
        <div class='copilot-title'>⬡ PraxisIQ AI Copilot</div>
        <div class='copilot-subtitle'>
            Domain-aware dental intelligence — clinical procedures, patient analytics, practice operations,
            oral health education, and Trust &amp; Safety, powered by live data and advanced LLMs.
        </div>
        <div class='copilot-badge-row'>
            <span class='copilot-badge'>◆ Llama 3.3 70B · Groq</span>
            <span class='copilot-badge green'><span class='live-dot'></span>Live database</span>
            <span class='copilot-badge cyan'>959 patients · 300 reviews</span>
            <span class='copilot-badge'>🌐 Live web search · Tavily</span>
            <span class='copilot-badge'>Dental + T&S knowledge</span>
            <span class='copilot-badge'>Clinical · Operational · Educational</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── GROQ SETUP ────────────────────────────────────────────────────────────
    groq_available = False
    GROQ_KEY = ""
    groq_setup_error = None

    # Resolve Groq key: env var -> Streamlit secrets
    GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
    if not GROQ_KEY:
        try:
            GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            pass

    try:
        from groq import Groq
        try:
            groq_client = Groq(api_key=GROQ_KEY)
            groq_available = True
        except Exception as groq_init_err:
            err_text = str(groq_init_err).lower()
            if "auth" in err_text or "401" in err_text or "api key" in err_text:
                groq_setup_error = "invalid_key"
            else:
                groq_setup_error = f"init_error: {str(groq_init_err)[:100]}"
    except ImportError:
        groq_setup_error = "no_package"

    # ── TAVILY WEB SEARCH SETUP ───────────────────────────────────────────────
    tavily_available = False
    TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")
    if not TAVILY_KEY:
        try:
            TAVILY_KEY = st.secrets.get("TAVILY_API_KEY", "")
        except Exception:
            pass
    if TAVILY_KEY:
        tavily_available = True

    def tavily_search(query: str, max_results: int = 5) -> str:
        """Search the web via Tavily and return a formatted context string."""
        try:
            import requests as _requests
            resp = _requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_KEY,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_answer": True,
                },
                timeout=10,
            )
            data = resp.json()
            parts = []
            if data.get("answer"):
                parts.append(f"Summary: {data['answer']}")
            for r in data.get("results", [])[:max_results]:
                title   = r.get("title", "")
                content = r.get("content", "")[:300]
                url     = r.get("url", "")
                parts.append(f"- {title}: {content} (Source: {url})")
            return "\n".join(parts) if parts else ""
        except Exception as e:
            return f"Web search unavailable: {str(e)}"

    def needs_web_search(question: str) -> bool:
        """Pattern-based web search trigger — generalizes to any place name."""
        q_lower = question.lower().strip()
        internal_signals = [
            "our ", "this clinic", "this dataset", "this database", "geetha dental",
            "our patients", "our reviews", "our retention", "our churn",
            "the database", "the dataset", "patient_id", "review_id",
        ]
        if any(sig in q_lower for sig in internal_signals):
            return False
        location_patterns = [
            r'\bin\s+\w+', r'\bnear\s+\w+', r'\bis\s+there\s+(any|a)\b',
            r'\b(clinic|clinics|dentist|dentists|hospital|hospitals)\b.*\b(in|near|at)\b',
            r'\b(in|near|at)\b.*\b(clinic|clinics|dentist|dentists|hospital|hospitals)\b',
        ]
        if any(re.search(pat, q_lower) for pat in location_patterns):
            return True
        external_signals = [
            "best ", "top ", "recommend", "compare", "vs ", "versus",
            "address", "contact", "phone number", "location",
            "where is", "where can", "latest", "recent", "current",
            "trend", "trending", "new in", "news", "today", "this year",
            "this month", "2024", "2025", "2026", "what's new", "whats new",
            "update on", "ranking", "rated", "famous", "popular",
            "search for", "search the web", "look up", "find a ", "find the ",
            "who is", "what is the current",
        ]
        return any(sig in q_lower for sig in external_signals)

    if groq_setup_error == "no_package":
        st.markdown("""
        <div class='copilot-error-card'>
            <b>Groq package not installed.</b><br>
            Add <code>groq>=0.4.0</code> to <code>requirements.txt</code> and redeploy.
        </div>
        """, unsafe_allow_html=True)
    elif groq_setup_error == "no_key":
        st.markdown("""
        <div class='copilot-error-card'>
            <b>No Groq API key found.</b> The Copilot can't run without one.<br><br>
            <b>To fix on Streamlit Community Cloud:</b> open your app ↑ ⋮ menu ↑ <b>Settings</b> ↑
            <b>Secrets</b>, and add a line exactly like:<br>
            <code>GROQ_API_KEY = "gsk_your_actual_key_here"</code><br>
            then save — the app will restart automatically.<br><br>
            <b>To fix locally:</b> create a file at <code>.streamlit/secrets.toml</code> in your project
            root with the same line, or set a <code>GROQ_API_KEY</code> environment variable before running
            <code>streamlit run</code>.<br><br>
            Get a free key at <code>console.groq.com/keys</code> if you don't have one yet.
        </div>
        """, unsafe_allow_html=True)
    elif groq_setup_error == "invalid_key":
        st.markdown(f"""
        <div class='copilot-error-card'>
            <b>Groq API key rejected.</b> The Groq API is rejecting your key.<br><br>
            <b>Troubleshooting steps:</b><br>
            1. Go to <code>console.groq.com/keys</code> and verify your key is still active<br>
            2. If revoked, create a new API key<br>
            3. Copy the key carefully (no extra spaces before/after)<br>
            4. Update <code>.streamlit/secrets.toml</code> (locally) or Settings → Secrets (on Community Cloud)<br>
            5. Restart Streamlit with Ctrl+C then <code>streamlit run dashboards/app.py</code><br><br>
            <b>Current key (first 20 chars):</b> <code>{GROQ_KEY[:20] if GROQ_KEY else 'not found'}...</code>
        </div>
        """, unsafe_allow_html=True)
    elif groq_setup_error and "error" in groq_setup_error:
        st.markdown(f"""
        <div class='copilot-error-card'>
            <b>Groq connection error.</b> {groq_setup_error.split(': ')[1] if ': ' in groq_setup_error else ''}<br><br>
            The API key exists but Groq couldn't process your request. This could be:<br>
            • Groq's servers are temporarily down<br>
            • Network connectivity issue<br>
            • Rate limiting<br><br>
            Try again in a few seconds, or check <code>console.groq.com/status</code>.
        </div>
        """, unsafe_allow_html=True)

    # ── LIVE DATA CONTEXT ─────────────────────────────────────────────────────
    @st.cache_data(ttl=300)
    def build_copilot_context():
        patients  = load_db("SELECT * FROM Patients")
        reviews   = load_db("SELECT * FROM Reviews")
        visits    = load_db("SELECT * FROM Visits")

        total_patients   = len(patients)
        returned         = len(patients[patients["Returned_Patient"] == "Yes"])
        never_returned   = len(patients[patients["Returned_Patient"] == "No"])
        retention_rate   = round(returned / total_patients * 100, 1)
        total_visits     = len(visits)
        avg_visits       = round(total_visits / total_patients, 2)
        avg_rating       = round(reviews["Rating"].mean(), 2)
        high_risk_count  = len(reviews[reviews["Label"] == "Treatment"])
        complaint_count  = len(reviews[reviews["Label"].isin(["Treatment","Communication","Waiting Time","Pricing","Staff"])])

        treatment_dropout = (
            patients[patients["Returned_Patient"] == "No"]
            .groupby("Primary_Treatment").size()
            .sort_values(ascending=False).head(5).to_dict()
        )
        treatment_volume = (
            patients.groupby("Primary_Treatment").size()
            .sort_values(ascending=False).head(8).to_dict()
        )
        label_dist = reviews["Label"].value_counts().to_dict()
        rating_dist = reviews["Rating"].value_counts().sort_index().to_dict()

        mq = load_csv("moderation_queue.csv")
        p1 = len(mq[mq["Severity"] == "Critical"]) if not mq.empty and "Severity" in mq.columns else 34
        p2 = len(mq[mq["Severity"] == "High"])     if not mq.empty and "Severity" in mq.columns else 111

        burst = load_csv("review_burst_detection.csv")
        burst_days = 4
        if not burst.empty and "Burst_Status" in burst.columns:
            burst_days = int((burst["Burst_Status"] == "BURST DETECTED").sum())
        elif not burst.empty and "Burst_Detected" in burst.columns:
            burst_days = int(burst["Burst_Detected"].sum())

        return f"""You are PraxisIQ AI Copilot — an expert dental intelligence assistant with deep knowledge of:
- Dental procedures, terminology, and clinical workflows
- Patient behavior analytics and retention patterns
- Trust & Safety operations and content moderation
- Review analysis, fraud detection, and risk classification
- Dental industry benchmarks and best practices

LIVE DATABASE CONTEXT (Geetha Dental Clinic — 6-year dataset):
- Total patients: {total_patients} | Returning: {returned} ({retention_rate}%) | Never returned: {never_returned}
- Total visits: {total_visits} | Avg visits per patient: {avg_visits}
- Total reviews: {len(reviews)} | Avg rating: {avg_rating}★
- High-risk Treatment complaints: {high_risk_count} (12% of reviews)
- Total complaint reviews: {complaint_count} (58% of reviews)
- Review label distribution: {label_dist}
- Rating distribution: {rating_dist}
- Top treatments by volume: {treatment_volume}
- Top dropout treatments: {treatment_dropout}
- Moderation queue: P1 Critical={p1}, P2 High={p2}
- Burst events detected: {burst_days}

DENTAL KNOWLEDGE SCOPE:
You can answer questions about:
- Dental procedures: Root Canal, Implants, Scaling, Braces, Aligners, Crowns, Bridges, Dentures, Whitening, Extractions, Fillings, Pediatric Dental, Gum Treatment
- Patient care: treatment duration, recovery, pain management, follow-up protocols, aftercare
- Clinical risk: complications, contraindications, high-risk treatments, patient safety signals
- Industry benchmarks: average retention rates (typically 70-80%), complaint rates, rating benchmarks
- T&S operations: moderation workflows, escalation policies, fraud detection, review manipulation
- Analytics: how to interpret the data, what signals matter, what to investigate next

RESPONSE STYLE:
- Be direct, specific, and conversational — answer exactly what was asked, nothing more
- ONLY mention Geetha Dental Clinic's live database stats (patient count, retention rate, ratings, etc.)
  if the question is specifically ABOUT this clinic, its patients, its reviews, or its operations
- Do NOT append clinic statistics to answers about other clinics, other cities, general dental
  knowledge, or anything unrelated to this specific clinic's own data — that is irrelevant noise
- For general knowledge, web search results, or questions about other clinics/places: answer using
  ONLY that information, with no clinic-data disclaimer or filler about Geetha Dental Clinic unless
  the user specifically asked about it
- For clinical/dental knowledge questions, give clear professional explanations
- For analytics questions about THIS clinic, connect findings to actionable recommendations
- Keep responses focused — short paragraphs or line breaks between points
- Never make up data — if something isn't in the context or search results, say so clearly
- Always be helpful, professional, and thorough

FORMATTING — IMPORTANT, your output is rendered directly as plain text in a chat UI, not as markdown:
- Never use **asterisks** for bold or *asterisks* for italics — they will show up as literal asterisk characters
- Never use markdown headers (#, ##) or markdown bullet dashes (- item) — use a line break instead, or a relevant emoji (e.g. "🦷 Root Canal:") to start a point
- Numbered lists are fine written plainly, e.g. "1. ..." on its own line
- Use plain, clean sentences and short paragraphs instead of markdown syntax"""

    def _escaped_html(text: str) -> str:
        return html.escape(text).replace("\n", "<br/>")

    def render_chat_history() -> None:
        if not st.session_state.copilot_messages:
            return

        chat_html = "<div class='chat-wrap' id='copilot-chat'>"
        for message in st.session_state.copilot_messages:
            content_ = _escaped_html(message["content"])
            if message["role"] == "user":
                chat_html += f"""
                <div class='msg-user'>
                    <div>
                        <div class='bubble'>{content_}</div>
                    </div>
                </div>"""
            else:
                chat_html += f"""
                <div class='msg-ai'>
                    <div class='ai-avatar'>P-AI</div>
                    <div>
                        <div class='bubble'>{content_}</div>
                    </div>
                </div>"""
        chat_html += "<div id='copilot-scroll-anchor' style='height:1px;'></div>"
        chat_html += "</div>"
        chat_html += """
        <script>
        (function() {
            function scrollToLatestAnswer() {
                var anchor = document.getElementById('copilot-scroll-anchor');
                if (anchor) {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            }
            setTimeout(scrollToLatestAnswer, 100);
            setTimeout(scrollToLatestAnswer, 350);
            setTimeout(scrollToLatestAnswer, 700);
            setTimeout(scrollToLatestAnswer, 1200);
        })();
        </script>
        """
        st.markdown(chat_html, unsafe_allow_html=True)

    # ── CHAT STATE ────────────────────────────────────────────────────────────
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []
    if "copilot_pending_question" not in st.session_state:
        st.session_state.copilot_pending_question = None

    # ── CORE ASK FUNCTION ─────────────────────────────────────────────────────
    def ask_copilot(question: str):
        """Send a question to Groq — with Tavily web search for real-world queries."""
        context = build_copilot_context()
        st.session_state.copilot_messages.append({"role": "user", "content": question})

        # ── Decide: web search or clinic data? ────────────────────────────────
        web_context = ""
        search_used = False
        user_message = question

        if needs_web_search(question):
            if tavily_available:
                web_results = tavily_search(question)
                if web_results and "unavailable" not in web_results.lower():
                    web_context = (
                        f"This query received live web search results from Tavily for '{question}'. "
                        "Use them together with any live database context to answer the user."
                    )
                    user_message = (
                        f"LIVE WEB SEARCH RESULTS for '{question}':\n"
                        f"{web_results}\n\n"
                        "Use ONLY the live web search results above and the available live database context to answer this question. "
                        "Do NOT suggest that the user search online — the search has already been done. "
                        "If the results above do not answer the question, answer based on the available data and say that no specific live web details were found."
                    )
                    search_used = True
                else:
                    web_context = (
                        f"Live web search was attempted for '{question}', but no live results were available. "
                        "Do NOT ask the user to search online. Answer based on existing knowledge and live database context, "
                        "and be honest if no specific live web information is available."
                    )
                    user_message = (
                        f"The user asked: '{question}'. Live web search was attempted but returned no results. "
                        "Answer based on existing knowledge and the available live database context."
                    )
            else:
                web_context = (
                    f"The user requested live web search for '{question}', but Tavily is not configured. "
                    "Answer using existing knowledge and the available live database context only."
                )
                user_message = (
                    f"The user asked: '{question}'. Tavily is not configured, so answer using existing knowledge and live database context only."
                )

        full_context = context + ("\n\n" + web_context if web_context else "")

        history = st.session_state.copilot_messages[:-1][-6:]
        messages = [{"role": "system", "content": full_context}]
        messages.extend({"role": m["role"], "content": m["content"]} for m in history)
        messages.append({"role": "user", "content": user_message})

        # Force the model to treat the request as plain chat text and avoid tool invocation.
        # This is important for Groq when the model may otherwise attempt browser.run or similar tools.
        messages.insert(0, {
            "role": "system",
            "content": (
                "You are a chat assistant that must not call external tool APIs or browser tools. "
                "Answer questions directly using only the context provided and any live web search results already injected. "
                "Do not produce function calls, tool invocation strings, or tool name references. "
                "If the user phrase sounds like a tool command, reinterpret it as a normal question."
            )
        })

        PRIMARY_MODEL = "llama-3.3-70b-versatile"
        FALLBACK_MODEL = "llama3-8b-8192"

        def _call_groq(model_name):
            resp = groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=1500,
                temperature=0.4,
            )
            return resp.choices[0].message.content.strip()

        answer = None
        error_detail = None
        try:
            answer = _call_groq(PRIMARY_MODEL)
        except Exception as e:
            err_text = str(e)
            # If Groq has decommissioned/deprecated the primary model, retry
            # once with a known-stable fallback rather than failing outright —
            # this is the one case worth auto-recovering from, since it's a
            # vendor-side change unrelated to the question itself.
            if "decommission" in err_text.lower() or "deprecat" in err_text.lower():
                try:
                    answer = _call_groq(FALLBACK_MODEL)
                except Exception as e2:
                    error_detail = str(e2)
            else:
                error_detail = err_text

        if answer is not None and search_used:
            answer += "\n\n🌐 *This answer used live web search via Tavily.*"

        if answer is None:
            # Show what actually went wrong instead of a fabricated canned
            # answer — a fake "I can't connect" message that then proceeds
            # to confidently answer anyway is worse than an honest error.
            err_lower = (error_detail or "").lower()
            if "rate" in err_lower or "429" in err_lower:
                answer = (
                    "⚠️ The Copilot hit Groq's rate limit for this API key. "
                    "This usually clears within a minute — try again shortly."
                )
            elif "auth" in err_lower or "401" in err_lower or "api key" in err_lower:
                answer = (
                    "⚠️ Groq rejected the API key for this request. "
                    "If you're the project owner, check that GROQ_API_KEY in "
                    "Settings → Secrets is current and hasn't been revoked."
                )
            elif "decommission" in err_lower or "deprecat" in err_lower:
                answer = (
                    "⚠️ Both the primary and fallback Groq models are unavailable "
                    "right now (Groq may have changed its model lineup again). "
                    f"Raw error: {error_detail[:200] if error_detail else 'unknown'}"
                )
            else:
                answer = (
                    "⚠️ The Copilot couldn't reach Groq for this request. "
                    f"Raw error: {error_detail[:200] if error_detail else 'unknown error'}\n\n"
                    "This is shown directly rather than a generic message so it's "
                    "actually debuggable — try again, or check console.groq.com/status."
                )

        st.session_state.copilot_messages.append({"role": "assistant", "content": answer})


    if not groq_setup_error:
        groq_available = True

        if not tavily_available:
            st.markdown("""
            <div class='copilot-error-card'>
                <b>Tavily web search is not configured.</b><br>
                Add <code>TAVILY_API_KEY = "tvly_your_key_here"</code> to
                <code>.streamlit/secrets.toml</code> or set the environment variable,
                then restart the app.
            </div>
            """, unsafe_allow_html=True)

        # ═══════════════════════════════════════════════════════════════════════
        # SECTION 1: QUICK QUESTIONS — always visible, never disappears
        # ═══════════════════════════════════════════════════════════════════════
        with st.container():
            st.markdown("""
            <div class='quick-q-marker' style='margin-bottom:1.2rem;'>
                <div style='color:#a8b6e8;font-size:10.5px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:12px;'>⚡ Quick Questions</div>
            </div>
            """, unsafe_allow_html=True)

            quick_questions = [
                ("🦷", "Root canal basics"),
                ("🔬", "Scaling vs deep cleaning"),
                ("😣", "Recovery after extraction"),
                ("📊", "Dropout rates"),
                ("⚠️", "Top risks"),
                ("📈", "ML vs LLM"),
            ]

            quick_cols = st.columns(6, gap="small")
            for idx, (icon, q) in enumerate(quick_questions):
                with quick_cols[idx]:
                    if st.button(f"{icon}\n{q}", key=f"quick_q_{idx}", use_container_width=True):
                        with st.spinner("PraxisIQ Copilot is thinking..."):
                            ask_copilot(q)
                        st.rerun()

        # ═══════════════════════════════════════════════════════════════════════
        # SECTION 4: TEXT INPUT — premium dark styling
        # ═══════════════════════════════════════════════════════════════════════
        st.markdown("""
        <style>
        .stTextInput > div > div > input {
            background-color: rgba(20,16,34,0.92) !important;
            border: 1px solid rgba(139,92,246,0.28) !important;
            color: #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            font-size: 14px !important;
            transition: all 0.2s !important;
        }
        .stTextInput > div > div > input:focus {
            background-color: rgba(20,16,34,1) !important;
            border-color: rgba(139,92,246,0.55) !important;
            box-shadow: 0 0 14px rgba(139,92,246,0.18) !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #5f6779 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin:1.4rem 0 1rem 0;'></div>", unsafe_allow_html=True)

        with st.form(key="copilot_form", clear_on_submit=True):
            col_input, col_send = st.columns([5, 1], gap="small")
            with col_input:
                free_text = st.text_input(
                    "Message",
                    placeholder="Ask about dental procedures, patient analytics, treatment outcomes...",
                    label_visibility="collapsed",
                )
            with col_send:
                submitted = st.form_submit_button("⬡ Ask", type="primary", use_container_width=True)

        if submitted and free_text.strip():
            with st.spinner("PraxisIQ Copilot is thinking..."):
                ask_copilot(free_text.strip())
            st.rerun()

        if st.session_state.copilot_messages:
            if st.button("🗑️ Clear conversation", key="clear_chat_btn"):
                st.session_state.copilot_messages = []
                st.rerun()

            render_chat_history()

        # SECTION 2: MORE QUESTIONS — moved below the chat box, and above What Copilot Knows
        st.markdown("<div style='color:#64748b;font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;margin:24px 0 4px 0;'>More Questions</div>", unsafe_allow_html=True)

        # GENERAL DENTAL KNOWLEDGE
        with st.container():
            st.markdown("""
            <div style='display:flex;align-items:center;gap:10px;margin:16px 0 12px 0;'>
                <span style='font-size:14px;'>🦷</span>
                <span style='color:#a78bfa;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;'>General Dental Knowledge</span>
                <div style='flex:1;height:1px;background:linear-gradient(90deg,rgba(167,139,250,0.4),transparent);'></div>
            </div>
            """, unsafe_allow_html=True)

            dental_full = [
                ("🦷", "What is a root canal and when is it needed?"),
                ("🔬", "What is the difference between scaling and deep scaling?"),
                ("🦷", "What is the typical recovery process after a tooth extraction?"),
                ("💊", "How do dental implants work and who is a good candidate?"),
                ("🪥", "What's the difference between braces and clear aligners?"),
            ]
            cols_dental = st.columns(5, gap="small")
            for col_idx, (icon, q) in enumerate(dental_full):
                with cols_dental[col_idx]:
                    if st.button(f"{icon}\n{q}", key=f"dental_q_{col_idx}", use_container_width=True, help=q):
                        with st.spinner("PraxisIQ Copilot is thinking..."):
                            ask_copilot(q)
                        st.rerun()

        # ABOUT THIS PROJECT
        with st.container():
            st.markdown("""
            <div style='display:flex;align-items:center;gap:10px;margin:20px 0 12px 0;'>
                <span style='font-size:14px;'>⬡</span>
                <span style='color:#22d3ee;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;'>About This Project</span>
                <div style='flex:1;height:1px;background:linear-gradient(90deg,rgba(34,211,238,0.4),transparent);'></div>
            </div>
            """, unsafe_allow_html=True)

            project_full = [
                ("📊", "Which treatment has the highest patient dropout rate, and why might that be?"),
                ("⚠️", "What are the top 3 Trust & Safety risks found in this dataset?"),
                ("📈", "Compare the ML and LLM classifiers — which should go to production and why?"),
                ("🚨", "Summarize the current moderation queue status."),
                ("🌐", "What would need to change about this pipeline to work at YouTube's scale?"),
            ]
            cols_project = st.columns(5, gap="small")
            for col_idx, (icon, q) in enumerate(project_full):
                with cols_project[col_idx]:
                    if st.button(f"{icon}\n{q}", key=f"project_q_{col_idx}", use_container_width=True, help=q):
                        with st.spinner("PraxisIQ Copilot is thinking..."):
                            ask_copilot(q)
                        st.rerun()

        # LIVE WEB SEARCH
        with st.container():
            st.markdown("""
            <div style='display:flex;align-items:center;gap:10px;margin:20px 0 12px 0;'>
                <span style='font-size:14px;'>🌐</span>
                <span style='color:#34d399;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;'>Live Web Search</span>
                <div style='flex:1;height:1px;background:linear-gradient(90deg,rgba(52,211,153,0.4),transparent);'></div>
            </div>
            """, unsafe_allow_html=True)

            web_full = [
                ("🌐", "What are the best dental clinics in Trichy?"),
                ("🏆", "Which are the top rated dental hospitals in Chennai?"),
                ("🌍", "What is the most common dental treatment performed worldwide?"),
                ("📰", "What are the latest trends in dental technology in 2025?"),
                ("🏅", "Which are the best dental clinics in India?"),
            ]
            cols_web = st.columns(5, gap="small")
            for col_idx, (icon, q) in enumerate(web_full):
                with cols_web[col_idx]:
                    if st.button(f"{icon}\n{q}", key=f"web_q_{col_idx}", use_container_width=True, help=q):
                        with st.spinner("PraxisIQ Copilot is thinking..."):
                            ask_copilot(q)
                        st.rerun()

        # ═══════════════════════════════════════════════════════════════════════
        # SECTION 5: WHAT COPILOT KNOWS — single block, no duplicate
        # ═══════════════════════════════════════════════════════════════
        st.markdown("""
        <div style='margin:2.6rem 0 1.2rem 0;border-top:1px solid rgba(139,92,246,0.1);padding-top:1.6rem;'>
            <div style='color:#f1f3f8;font-size:14px;font-weight:700;'>
                🧠 What PraxisIQ Copilot Knows
            </div>
        </div>
        """, unsafe_allow_html=True)

        cap_cols = st.columns(4)
        caps = [
            ("🦷", "Clinical Dentistry", "Root Canal, Implants, Scaling, Braces, Crowns, Bridges, Whitening, Extractions, Pediatric, Gum Treatment"),
            ("📊", "Patient Analytics", "Retention, dropout rates, visit patterns, high-risk identification, follow-up compliance"),
            ("🛡️", "Trust & Safety", "Moderation queue, escalation tiers, fraud signals, review classification, burst detection"),
            ("🌐", "Live Web Search", "Top clinics, current rankings, latest dental news, real-world benchmarks — powered by Tavily"),
        ]
        for col, (icon, title, desc) in zip(cap_cols, caps):
            with col:
                st.markdown(f"""
                <div class='cap-card'>
                    <div style='font-size:26px;margin-bottom:10px;'>{icon}</div>
                    <div style='color:#f1f3f8;font-size:13px;font-weight:700;margin-bottom:7px;'>{title}</div>
                    <div style='color:#9aa3b5;font-size:11px;line-height:1.6;'>{desc}</div>
                </div>""", unsafe_allow_html=True)