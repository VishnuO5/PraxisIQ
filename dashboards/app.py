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

    /* Also target the chevron arrow that appears on sidebar edge */
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

    /* ── Radio group — remove ALL default Streamlit chrome ── */
    /* Hide the outer label "Navigation" */
    section[data-testid="stSidebar"] .stRadio > label {{
        display: none !important;
    }}

    /* Remove gap between radio items */
    section[data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 2px !important;
    }}

    /* Each radio row */
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

    /* Hide the actual radio circle dot */
    section[data-testid="stSidebar"] div[role="radiogroup"] label span:first-child {{
        display: none !important;
    }}

    /* Nav item text */
    section[data-testid="stSidebar"] div[role="radiogroup"] label p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label div p {{
        color: {TEXT_MED} !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
    }}

    /* Active / selected nav item */
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
        background: linear-gradient(90deg, rgba(108,140,255,0.14), rgba(108,140,255,0.02)) !important;
        border-left: 2px solid {ACCENT} !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) div p {{
        color: {TEXT_HI} !important;
    }}

    /* Hide stray SVG arrows/icons that Streamlit injects */
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
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(BASE, "PraxisIQ.db")
RPT  = os.path.join(BASE, "reports")


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
# SIDEBAR  ── clean, fixed, premium nav
# ─────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
        <div class='brand-row'>
            <div class='brand-mark'>P</div>
            <div class='brand-name'>PraxisIQ</div>
        </div>
        <div class='brand-tag'>Patient Trust &amp; Operations<br>Intelligence Platform</div>
        <div class='side-divider'></div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='nav-label'>Workspace</div>", unsafe_allow_html=True)

    # Navigation — hidden label, clean radio buttons
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

    # Footer stats
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
    kpi(c1, "Total Patients",    "959",   "6-year real dataset",      ACCENT)
    kpi(c2, "Retention Rate",    "81.9%", "786 returning patients",   EMERALD)
    kpi(c3, "High-Risk Patients","42",    "Follow-up overdue",        ROSE)
    kpi(c4, "Total Visits",      "4,603", "Avg. 4.8 visits / patient",CYAN)

    c5, c6, c7, c8 = st.columns(4)
    kpi(c5, "Reviews Analyzed",  "300",   "7 categories labeled",     VIOLET)
    kpi(c6, "LLM Accuracy",      "84.3%", "Qwen2.5 · Prompt V2",     ACCENT)
    kpi(c7, "Burst Events",      "4",     "Review spikes flagged",    AMBER)
    kpi(c8, "High-Risk Reviews", "12%",   "36 flagged for review",    ROSE)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    finding(
        "Why a dental clinic dataset for Trust &amp; Safety?",
        "Patient reviews are structurally identical to user-generated content on any platform \u2014 "
        "free-text submissions, star ratings, coordinated posting patterns, and abuse signals. "
        "The workflows built here \u2014 content classification, burst detection, repeat actor flagging, "
        "risk scoring, and moderation queuing \u2014 directly mirror Trust &amp; Safety systems at scale. "
        "The domain is dental; the methodology is platform trust &amp; safety."
    )
    section("Role Alignment", "YouTube · Engineering Analyst, Trust &amp; Safety")
    cols = st.columns(3)
    alignments = [
        ("SQL + Python Pipeline",      "Multi-source data collection, cleaning, and structured querying across 6 years of records."),
        ("LLM Prompt Engineering",     "3-prompt evaluation pipeline benchmarked on precision, recall, and F1."),
        ("Statistical Analysis",       "One-Way ANOVA on visit patterns — F = 5.37, p &lt; 0.001."),
        ("Fraud / Anomaly Investigation","Duplicate detection, review-burst screening, and suspicious-pattern flags."),
        ("Ground-Truth Data Labeling", "300 hand-labeled reviews used as the evaluation dataset."),
        ("Performance Analysis",       "Prompt V1 / V2 / V3 compared via confusion matrix and per-class F1."),
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
        "Retention behavior, follow-up compliance, and visit-frequency patterns across the patient base"
    )

    c1, c2, c3 = st.columns(3)
    kpi(c1, "Returned Patients", "786", "81.9% retention rate",    EMERALD)
    kpi(c2, "One-Time Patients", "173", "18.1% churn rate",        ROSE)
    kpi(c3, "Follow-Up Overdue", "42",  "Requires intervention",   AMBER)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Retention vs. Churn")
        fig = go.Figure(go.Pie(
            labels=['Returned', 'One-Time'], values=[786, 173], hole=0.62,
            marker=dict(colors=[EMERALD, ROSE], line=dict(color=INK, width=2)),
            textfont=dict(color=TEXT_HI, size=12), textinfo='label+percent'
        ))
        chart_layout(fig, 320)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        section("Top Treatments by Visit Volume")
        treatments = load_db(
            "SELECT Treatment_Type, COUNT(*) as Count FROM Visits "
            "GROUP BY Treatment_Type ORDER BY Count DESC LIMIT 8"
        )
        fig = px.bar(treatments, x='Count', y='Treatment_Type', orientation='h',
                     color_discrete_sequence=[ACCENT])
        fig.update_traces(marker_color=ACCENT, marker_line_width=0, opacity=0.92)
        chart_layout(fig, 320)
        fig.update_layout(yaxis=dict(autorange='reversed', gridcolor=BORDER_SOFT,
                                     tickfont=dict(color=TEXT_LOW, size=11)))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Follow-Up Compliance")
    col_c, col_d = st.columns(2)
    high_risk = load_csv('high_risk_patients.csv')
    total_patients = 959
    overdue_count = len(high_risk) if not high_risk.empty else 42
    compliant_count = total_patients - overdue_count

    with col_c:
        followup = pd.DataFrame({
            'Status':       ['Compliant', 'Follow-Up Overdue'],
            'Count':        [compliant_count, overdue_count]
        })
        fig = px.bar(
            followup, x='Status', y='Count', color='Status',
            color_discrete_map={'Compliant': EMERALD, 'Follow-Up Overdue': ROSE},
            text='Count'
        )
        fig.update_traces(marker_line_width=0, opacity=0.92, textposition='outside',
                           textfont=dict(color=TEXT_HI, size=12.5))
        chart_layout(fig, 300)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        section("High-Risk Patient Queue")
        if not high_risk.empty:
            st.dataframe(high_risk.head(15), use_container_width=True, height=300)
        else:
            st.info("Run analytics/followup_risk_analysis.py to generate the high-risk queue.")

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
        f"Chi\u00b2 Statistic: <b style='color:{ACCENT}'>412.4946</b> &nbsp;\u00b7&nbsp; "
        f"P-Value: <b style='color:{EMERALD}'>&lt; 0.001</b> &nbsp;\u00b7&nbsp; "
        f"Degrees of Freedom: <b style='color:{CYAN}'>12</b><br><br>"
        "A highly significant association exists between review category and rating tier. "
        "Treatment and Communication complaints cluster strongly in the 1\u20132 star range, "
        "while Positive reviews dominate the 4\u20135 star range. "
        "This validates the risk classification logic used in the moderation queue."
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

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Reviews",  "300",   "7 labeled categories",   ACCENT)
    kpi(c2, "Positive Reviews","108",  "36% of total",           EMERALD)
    kpi(c3, "Negative Rate",  "58%",   "174 complaint reviews",  ROSE)
    kpi(c4, "Avg. Rating",    "3.1 ★", "Across 300 reviews",     AMBER)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Review Label Distribution")
        labels = load_db("SELECT Label, COUNT(*) as Count FROM Reviews GROUP BY Label ORDER BY Count DESC")
        colors_map = {
            'Positive': EMERALD, 'Neutral': SLATE, 'Waiting Time': AMBER,
            'Communication': ACCENT, 'Treatment': ROSE, 'Pricing': '#E8954B', 'Staff': VIOLET
        }
        fig = px.bar(labels, x='Label', y='Count', color='Label', color_discrete_map=colors_map)
        fig.update_traces(marker_line_width=0, opacity=0.92)
        chart_layout(fig, 320)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        section("Rating Distribution")
        ratings = load_db("SELECT Rating, COUNT(*) as Count FROM Reviews GROUP BY Rating ORDER BY Rating")
        fig = px.bar(ratings, x='Rating', y='Count', color_discrete_sequence=[ACCENT])
        fig.update_traces(marker_color=ACCENT, marker_line_width=0, opacity=0.92)
        chart_layout(fig, 320)
        fig.update_layout(xaxis=dict(tickvals=[1, 2, 3, 4, 5], gridcolor=BORDER_SOFT,
                                     tickfont=dict(color=TEXT_LOW, size=11)))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Service Quality by Complaint Category", "Module 6")
    sq = load_csv('service_quality_analysis.csv')
    if not sq.empty:
        col_c, col_d = st.columns(2)
        with col_c:
            fig = px.bar(sq, x='Label', y='Average_Rating', color='Average_Rating',
                         color_continuous_scale=[ROSE, AMBER, EMERALD])
            fig.update_traces(marker_line_width=0, opacity=0.92)
            chart_layout(fig, 360)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
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
    kpi(c1, "Burst Events",      "4", "Review spikes detected",     AMBER)
    kpi(c2, "Duplicate Reviews", "0", "No copy-paste spam found",   EMERALD)
    kpi(c3, "Repeat Reviewers",  "1", "Flagged for manual review",  ROSE)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Review Volume by Date")
        bursts = load_csv('review_burst_detection.csv')
        all_reviews_by_date = load_db(
            "SELECT Review_Date, COUNT(*) as Count FROM Reviews "
            "GROUP BY Review_Date ORDER BY Review_Date"
        )
        fig = px.line(all_reviews_by_date, x='Review_Date', y='Count',
                      color_discrete_sequence=[ACCENT])
        fig.update_traces(line=dict(width=2.4), fill='tozeroy',
                          fillcolor='rgba(108,140,255,0.08)')
        if not bursts.empty:
            fig.add_hline(
                y=3.67, line_dash='dash', line_color=ROSE, line_width=1.4,
                annotation_text='Burst threshold', annotation_font_color=ROSE,
                annotation_font_size=11
            )
        chart_layout(fig, 330)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        section("Burst Events Flagged")
        if not bursts.empty:
            for _, row in bursts.iterrows():
                st.markdown(f"""<div class='finding-card'>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;'>
                        <div class='finding-title'>{row['Review_Date']}</div>
                        <span class='badge badge-high'>BURST</span>
                    </div>
                    <div class='finding-text'>{int(row['Review_Count'])} reviews on this date · Threshold: 3.67 / day</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Statistical Visit Outliers", "Module 4")
    outliers = load_db("""
        SELECT Patient_Id, Primary_Treatment, Total_Visits
        FROM Patients
        WHERE Total_Visits > (
            SELECT AVG(Total_Visits) + 2 * (
                SELECT AVG((Total_Visits - avg_visits) * (Total_Visits - avg_visits))
                FROM (SELECT AVG(Total_Visits) as avg_visits FROM Patients),
                Patients
            )
            FROM Patients
        )
        ORDER BY Total_Visits DESC
        LIMIT 15
    """)
    if not outliers.empty:
        st.dataframe(outliers, use_container_width=True, height=280)
    else:
        high_visit = load_db(
            "SELECT Patient_Id, Primary_Treatment, Total_Visits "
            "FROM Patients ORDER BY Total_Visits DESC LIMIT 15"
        )
        st.dataframe(high_visit, use_container_width=True, height=280)


# ─────────────────────────────────────────────
# PAGE 5 — TRUST & SAFETY
# ─────────────────────────────────────────────
elif page == "Trust & Safety":
    page_header(
        "Content Risk Operations",
        "Trust & Safety Intelligence",
        "Risk classification, content screening, and moderation-queue performance metrics"
    )

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Safe Content",  "42%", "126 reviews",          EMERALD)
    kpi(c2, "Needs Review",  "46%", "138 reviews",          AMBER)
    kpi(c3, "High Risk",     "12%", "36 reviews flagged",   ROSE)
    kpi(c4, "Burst Events",  "4",   "Anomalous spikes",     ACCENT)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Risk Level Distribution")
        fig = go.Figure(go.Pie(
            labels=['Safe', 'Needs Review', 'High Risk'],
            values=[126, 138, 36],
            hole=0.62,
            marker=dict(colors=[EMERALD, AMBER, ROSE], line=dict(color=INK, width=2)),
            textfont=dict(color=TEXT_HI, size=12),
            textinfo='label+percent'
        ))
        chart_layout(fig, 320)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        section("Risk Classification Logic")
        risk_rules = [
            ("Safe",            "Positive, Neutral reviews — no action required",                           EMERALD),
            ("Needs Review",    "Communication, Waiting Time, Pricing, Staff — quality signals",            AMBER),
            ("High Risk",       "Treatment complaints — patient safety implications",                       ROSE),
            ("Burst Flag",      "Days with review volume greater than 3× the daily average",               ACCENT),
            ("Repeat Reviewer", "Same reviewer appearing multiple times — manual check required",           VIOLET),
        ]
        for badge, desc, color in risk_rules:
            st.markdown(f"""<div class='finding-card'>
                <div class='finding-title'><span style='color:{color}'>●</span>&nbsp; {badge}</div>
                <div class='finding-text'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Moderation Queue")
    mq = load_csv('moderation_queue.csv')
    if not mq.empty:
        st.dataframe(mq.head(20), use_container_width=True, height=300)
    else:
        high_risk_reviews = load_db(
            "SELECT Review_ID, Reviewer_Name, Review_Date, Rating, Label, Review_Text "
            "FROM Reviews WHERE Label = 'Treatment' ORDER BY Rating ASC LIMIT 15"
        )
        st.dataframe(high_risk_reviews, use_container_width=True, height=300)
        st.markdown("<hr/>", unsafe_allow_html=True)
    section("Classification Threshold — False Positive vs False Negative Tradeoff")

    col_fp, col_fn = st.columns(2)

    with col_fp:
        finding(
            "False Positive Risk",
            f"Setting the risk threshold <b style='color:{AMBER}'>too low</b> flags safe content as High Risk. "
            f"In this dataset, Positive and Neutral reviews (42% of total — 126 reviews) would enter the "
            f"moderation queue unnecessarily, increasing analyst workload with zero safety benefit. "
            f"Over-actioning erodes reviewer trust in the system over time."
        )

    with col_fn:
        finding(
            "False Negative Risk",
            f"Setting the risk threshold <b style='color:{ROSE}'>too high</b> allows genuine Treatment complaints "
            f"to pass through without escalation. Given that 36 reviews (12%) contain patient safety signals "
            f"— including reports of pain, procedural failure, and worsened conditions — a missed escalation "
            f"here has direct real-world consequences beyond platform quality."
        )

    finding(
        "Current Threshold Calibration",
        f"The current system is calibrated to <b style='color:{EMERALD}'>minimize false negatives on Treatment complaints</b> "
        f"specifically, given their patient safety implications. Treatment reviews rated 1–2 stars are auto-escalated "
        f"to Critical/P1 regardless of other signals. Communication and Neutral categories — where the LLM "
        f"misclassification rate is highest (10/39 and 6/18 respectively) — are routed to the Needs Review tier "
        f"for human adjudication rather than auto-actioned. This directly mirrors real T&S queue design: "
        f"high-confidence signals get automated action, ambiguous signals get human review."
    )


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
    kpi(c1, "Final Accuracy", "84.3%", "Prompt V2 · 300 reviews",  EMERALD)
    kpi(c2, "Precision",      "84.4%", "Weighted average",          ACCENT)
    kpi(c3, "Recall",         "78.6%", "Weighted average",          CYAN)
    kpi(c4, "F1 Score",       "79.5%", "Weighted average",          VIOLET)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Prompt Comparison", "20-review test")
        prompt_data = pd.DataFrame({
            'Prompt':   ['V1 — Zero-Shot', 'V2 — Detailed', 'V3 — Rules-Based'],
            'Accuracy': [70, 75, 65],
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
            yaxis=dict(range=[0, 100], gridcolor=BORDER_SOFT,
                       tickfont=dict(color=TEXT_LOW, size=11))
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        section("Prompt Design Rationale")
        prompts_info = [
            ("V1 — Zero-Shot",        "70%", "Basic instruction only. No category definitions — model relies on general knowledge.",                               "badge-med"),
            ("V2 — Detailed (selected)","75%","Each category explicitly defined with examples. Reduced ambiguity; chosen as the final prompt.",                   "badge-low"),
            ("V3 — Rules-Based",      "65%", "Strict keyword rules. Over-indexed on specific terms; underperformed on nuanced reviews.",                          "badge-high"),
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
            f"Accuracy: <b style='color:{ACCENT}'>83.3%</b> on 300 reviews. "
            f"Fast, deterministic, and fully interpretable — each prediction traces directly to weighted token features. "
            f"Performs well on categories with strong keyword signals (Treatment, Pricing, Waiting Time) "
            f"but struggles with semantic nuance in Communication and Neutral reviews where the same words "
            f"appear across multiple categories."
        )

    with col_llm:
        finding(
            "LLM — Qwen2.5 7B via Ollama (Prompt V2)",
            f"Accuracy: <b style='color:{EMERALD}'>84.33%</b> on 300 reviews. "
            f"Higher overall accuracy and significantly better recall on minority classes. "
            f"Handles semantic overlap more robustly by reasoning about context rather than token frequency. "
            f"Trade-off: slower inference, non-deterministic outputs, and harder to audit — "
            f"a concern in regulated or high-stakes T&S environments."
        )

    comparison_data = pd.DataFrame({
        'Approach': ['TF-IDF + Logistic Regression', 'Qwen2.5 7B (Prompt V2)'],
        'Accuracy': [83.3, 84.33],
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
        yaxis=dict(range=[0, 100], gridcolor=BORDER_SOFT,
                   tickfont=dict(color=TEXT_LOW, size=11))
    )
    st.plotly_chart(fig, use_container_width=True)

    finding(
        "Recommendation",
        f"The LLM outperforms traditional ML by <b style='color:{EMERALD}'>+1.03%</b> in accuracy "
        f"with meaningfully better recall on semantically ambiguous categories. "
        f"For a production T&S system handling review classification at scale, the recommended architecture is: "
        f"<b style='color:{ACCENT}'>LLM classification for all categories</b>, with Communication and Neutral "
        f"predictions routed to a human review queue given their higher misclassification rate in both approaches."
    )

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Per-Class Performance (Confusion Matrix)", "Module 3")
    preds_cm = load_csv('llm_predictions.csv')
    if not preds_cm.empty:
        from sklearn.metrics import confusion_matrix as sk_cm
        labels_order = ['Positive', 'Communication', 'Waiting Time', 'Treatment', 'Pricing', 'Staff', 'Neutral']
        cm = sk_cm(preds_cm['Label'], preds_cm['Prediction'], labels=labels_order)
        cm_df = pd.DataFrame(cm, index=labels_order, columns=labels_order)
        fig = px.imshow(
            cm_df,
            color_continuous_scale=[[0, SURFACE], [0.5, '#2A3560'], [1, ACCENT]],
            text_auto=True,
            aspect='auto'
        )
        fig.update_traces(textfont=dict(color=TEXT_HI, size=12))
        chart_layout(fig, 380)
        fig.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Predicted",
            yaxis_title="Actual",
            xaxis=dict(tickfont=dict(color=TEXT_MED, size=11)),
            yaxis=dict(tickfont=dict(color=TEXT_MED, size=11))
        )
        st.plotly_chart(fig, use_container_width=True)
        finding(
            "Classification Difficulty Analysis",
            f"<b style='color:{EMERALD}'>Strongest categories:</b> Positive, Pricing, Treatment, Waiting Time \u2014 clear keyword signals make these easy to classify.<br><br>"
            f"<b style='color:{ROSE}'>Hardest categories:</b> Communication and Neutral \u2014 these overlap semantically with each other and with Positive reviews, "
            "causing most misclassifications. In a real Trust &amp; Safety system, these ambiguous cases would be "
            "routed to a human review queue rather than auto-actioned."
        )

    st.markdown("<hr/>", unsafe_allow_html=True)
    section("Sample Predictions vs. Ground Truth")
    preds = load_csv('llm_predictions.csv')
    if not preds.empty:
        preds['Correct'] = preds['Label'] == preds['Prediction']
        preds['Match']   = preds['Correct'].map({True: '✓', False: '✗'})
        display_cols = ['Review_Text', 'Label', 'Prediction', 'Match']
        available = [c for c in display_cols if c in preds.columns]
        st.dataframe(preds[available].head(20), use_container_width=True, height=350)

        correct = preds['Correct'].sum()
        total   = len(preds)
        finding(
            "Sample Evaluation Result",
            f"<b style='color:{EMERALD}'>{correct}</b> correct out of {total} reviewed &nbsp;·&nbsp; "
            f"Sample accuracy: <b style='color:{ACCENT}'>{round(correct / total * 100, 1)}%</b>"
        )
    else:
        st.info("Run llm_evaluation_final.py to generate predictions CSV.")