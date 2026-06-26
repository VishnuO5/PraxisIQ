import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os

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
EXCEL = os.path.join(BASE, "Patient_Data.xlsx")


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
        ],
        label_visibility="collapsed"
    )

    st.markdown(f"""
        <div class='side-footer'>
            <div class='side-stat'><b>959</b> patients &nbsp;·&nbsp; <b>4,603</b> visits</div>
            <div class='side-stat'><b>300</b> reviews &nbsp;·&nbsp; 7 labeled categories</div>
            <div class='side-stat'>Model: <b>Qwen2.5 7B</b> · Ollama (local)</div>
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

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Patients",    "959",   "6-year real dataset",             ACCENT)
    kpi(c2, "Retention Rate",    "81.9%", "786 returning patients",          EMERALD)
    kpi(c3, "At-Risk Patients",  "173",   "Never returned after first visit", ROSE)
    kpi(c4, "Total Visits",      "4,603", "Avg. 4.8 visits / patient",       CYAN)

    c5, c6, c7, c8 = st.columns(4)
    kpi(c5, "Reviews Analyzed",  "300",   "7 categories labeled",                  VIOLET)
    kpi(c6, "LLM Accuracy",      "86.7%", "Qwen2.5 · Prompt V2 (hold-out)",        ACCENT)
    kpi(c7, "Burst Events",      "7",     "Review spikes flagged",                  AMBER)
    kpi(c8, "High-Risk Reviews", "12%",   "36 Treatment complaints flagged",        ROSE)

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

    c1, c2, c3 = st.columns(3)
    kpi(c1, "Returned Patients",  str(returned_f), f"{ret_rate_f}% retention rate",             EMERALD)
    kpi(c2, "One-Time Patients",  str(onetime_f),  f"{round(onetime_f/total_f*100,1) if total_f>0 else 0}% churn rate", ROSE)
    kpi(c3, "At-Risk Patients",   str(at_risk_f),  "Single visit, never returned",               AMBER)

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
        "Treatment and Communication complaints cluster strongly in the 1–2 star range, "
        "while Positive reviews dominate the 4–5 star range. "
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
    kpi(c3, "Complaint Rate",   f"{neg_rate_f}%",        f"{complaint_f} complaint reviews",                        ROSE)
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

    # Queue counts from pipeline output
    P1_COUNT = 34    # Critical
    P2_COUNT = 111   # High
    P3_COUNT = 29    # Medium

    capacity_per_hour = (60 / mins_per_case) * num_analysts

    p1_hours = round(P1_COUNT / capacity_per_hour, 1)
    p2_hours = round((P1_COUNT + P2_COUNT) / capacity_per_hour, 1)
    p3_hours = round((P1_COUNT + P2_COUNT + P3_COUNT) / capacity_per_hour, 1)

    p1_sla_ok  = p1_hours <= 4
    p2_sla_ok  = p2_hours <= 24

    kc1, kc2, kc3, kc4 = st.columns(4)
    kpi(kc1, "Analyst Capacity",   f"{round(capacity_per_hour, 1)}/hr", f"{num_analysts} analyst{'s' if num_analysts > 1 else ''} · {mins_per_case} min/case", ACCENT)
    kpi(kc2, "P1 Clear Time",      f"{p1_hours}h",  f"34 Critical cases · SLA: 4h",   EMERALD if p1_sla_ok else ROSE)
    kpi(kc3, "P1+P2 Clear Time",   f"{p2_hours}h",  f"145 cases · SLA: 24h",          EMERALD if p2_sla_ok else AMBER)
    kpi(kc4, "Full Queue Clear",   f"{p3_hours}h",  f"174 total cases (P1+P2+P3)",    CYAN)

    sim_chart_col, sim_verdict_col = st.columns(2)
    with sim_chart_col:

        tier_df = pd.DataFrame({
            "Tier":  ["P1 — Critical\n(34 cases)", "P2 — High\n(111 cases)", "P3 — Medium\n(29 cases)"],
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

    RISK_MAP = {
        "Treatment":     "High Risk",
        "Communication": "Needs Review",
        "Waiting Time":  "Needs Review",
        "Pricing":       "Needs Review",
        "Staff":         "Needs Review",
        "Neutral":       "Safe",
        "Positive":      "Safe",
    }
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
    kpi(c1, "Safe Content", f"{safe_pct}%",  f"{safe_count} reviews",              EMERALD)
    kpi(c2, "Needs Review", f"{needs_pct}%", f"{needs_review_count} reviews",       AMBER)
    kpi(c3, "High Risk",    f"{high_pct}%",  f"{high_risk_count} reviews flagged",  ROSE)
    kpi(c4, "Burst Events", "7",             "Anomalous spikes detected",           ACCENT)

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
    section("Content Policy Enforcement Map", "Category → Action → Escalation Path")
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
                <td style='padding:10px 14px;color:{TEXT_MED};'>Senior Analyst → Clinic Operations Lead</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};background:rgba(255,255,255,0.01);'>
                <td style='padding:10px 14px;color:{ACCENT};font-weight:700;'>Communication</td>
                <td style='padding:10px 14px;'><span style='background:rgba(242,179,61,0.12);color:{AMBER};border:1px solid rgba(242,179,61,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>NEEDS REVIEW</span></td>
                <td style='padding:10px 14px;color:{AMBER};font-weight:600;'>High (P2) if Rating ≤ 2<br>Medium (P3) if Rating = 3</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>&lt; 24 hours</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Queue for human review · No auto-action<br><span style='color:{ROSE};font-size:10.5px;'>LLM recall 44% — high false negative risk</span></td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Human Reviewer → Queue Manager</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};'>
                <td style='padding:10px 14px;color:{AMBER};font-weight:700;'>Waiting Time</td>
                <td style='padding:10px 14px;'><span style='background:rgba(242,179,61,0.12);color:{AMBER};border:1px solid rgba(242,179,61,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>NEEDS REVIEW</span></td>
                <td style='padding:10px 14px;color:{AMBER};font-weight:600;'>High (P2) if Rating ≤ 2<br>Medium (P3) if Rating ≥ 3</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>&lt; 24 hours</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Queue for ops review · Aggregate trend alert if &gt; 3/month</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Ops Analyst → Scheduling Team</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};background:rgba(255,255,255,0.01);'>
                <td style='padding:10px 14px;color:#E8954B;font-weight:700;'>Pricing</td>
                <td style='padding:10px 14px;'><span style='background:rgba(242,179,61,0.12);color:{AMBER};border:1px solid rgba(242,179,61,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>NEEDS REVIEW</span></td>
                <td style='padding:10px 14px;color:{AMBER};font-weight:600;'>High (P2) if Rating ≤ 2</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>&lt; 24 hours</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Flag for billing audit · Escalate if 1-star</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Finance Reviewer → Practice Manager</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};'>
                <td style='padding:10px 14px;color:{VIOLET};font-weight:700;'>Staff</td>
                <td style='padding:10px 14px;'><span style='background:rgba(242,179,61,0.12);color:{AMBER};border:1px solid rgba(242,179,61,0.28);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>NEEDS REVIEW</span></td>
                <td style='padding:10px 14px;color:{AMBER};font-weight:600;'>Medium (P3)</td>
                <td style='padding:10px 14px;color:{TEXT_HI};font-weight:600;'>Weekly batch</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Queue for human review · No auto-action<br><span style='color:{ROSE};font-size:10.5px;'>LLM recall 53% — route all to human</span></td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>HR Reviewer → Department Head</td>
            </tr>
            <tr style='border-bottom:1px solid {BORDER_SOFT};background:rgba(255,255,255,0.01);'>
                <td style='padding:10px 14px;color:{SLATE};font-weight:700;'>Neutral</td>
                <td style='padding:10px 14px;'><span style='background:rgba(61,220,140,0.10);color:{EMERALD};border:1px solid rgba(61,220,140,0.25);padding:2px 8px;border-radius:12px;font-weight:700;font-size:10.5px;'>SAFE</span></td>
                <td style='padding:10px 14px;color:{TEXT_LOW};font-weight:600;'>Low (P4)</td>
                <td style='padding:10px 14px;color:{TEXT_MED};font-weight:600;'>Monthly review</td>
                <td style='padding:10px 14px;color:{TEXT_MED};'>Log and archive · No escalation</td>
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
            Communication and Staff categories are <b style='color:{AMBER}'>never auto-actioned</b> due to LLM recall dropping below 55% on these classes.
            All items in these categories go to human review regardless of rating.
            This is a deliberate false-negative minimization choice — the cost of a missed escalation
            outweighs the cost of excess human review volume.
        </span>
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
        f"Treatment reviews rated 1–2 stars are auto-escalated to Critical/P1. Staff and Neutral categories — "
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
            f"4 burst events, and 36 Treatment complaints that cluster at 1–2 stars. These are genuine "
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
    kpi(c1, "Final Accuracy", "86.7%", "Prompt V2 · 90 hold-out reviews", EMERALD)
    kpi(c2, "Precision",      "84.4%", "Weighted average",                 ACCENT)
    kpi(c3, "Recall",         "78.6%", "Weighted average",                 CYAN)
    kpi(c4, "F1 Score",       "79.5%", "Weighted average",                 VIOLET)

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
    section("Sample Predictions vs. Ground Truth")
    preds = load_csv('llm_predictions.csv')
    if not preds.empty:
        preds['Correct'] = preds['Label'] == preds['Prediction']
        preds['Match']   = preds['Correct'].map({True: '✓', False: '✗'})
        display_cols = ['Review_Text','Label','Prediction','Match']
        available    = [c for c in display_cols if c in preds.columns]
        st.dataframe(preds[available].head(20), width='stretch', height=350)

        correct = preds['Correct'].sum()
        total   = len(preds)
        finding(
            "Sample Evaluation Result",
            f"<b style='color:{EMERALD}'>{correct}</b> correct out of {total} reviewed &nbsp;·&nbsp; "
            f"Sample accuracy: <b style='color:{ACCENT}'>{round(correct / total * 100, 1)}%</b>"
        )
    else:
        st.info("Run llm_evaluation_final.py to generate predictions CSV.")