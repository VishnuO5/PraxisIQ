
import streamlit as st
import pandas as pd
import plotly.express as px
import dashboard_metrics as dm

st.set_page_config(
    page_title="PraxisIQ Intelligence Platform",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
[data-testid="stAppViewContainer"]{background:#0B1220;}
section[data-testid="stSidebar"]{background:#111827;}
h1,h2,h3{color:white;}
</style>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Command Center",
        "Analytics Intelligence",
        "Trust & Safety Operations",
        "Case Management",
        "AI Copilot"
    ]
)

core = dm.get_core_metrics()

st.title("🧠 PraxisIQ Intelligence Platform")
st.caption("Analytics • Trust & Safety • AI Operations")

if page == "Executive Command Center":
    llm = dm.get_llm_metrics()
    trust = dm.get_trust_safety_metrics()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Patients", f"{core['patients']:,}")
    c2.metric("Visits", f"{core['visits']:,}")
    c3.metric("Reviews", f"{core['reviews']:,}")
    c4.metric("Critical Cases", dm.get_critical_cases())

    st.subheader("AI Performance")
    a1,a2,a3,a4 = st.columns(4)
    a1.metric("Accuracy", f"{llm['Accuracy']*100:.1f}%")
    a2.metric("Precision", f"{llm['Precision']*100:.1f}%")
    a3.metric("Recall", f"{llm['Recall']*100:.1f}%")
    a4.metric("F1 Score", f"{llm['F1 Score']*100:.1f}%")

    left,right = st.columns(2)

    with left:
        df = dm.get_treatment_distribution().head(10)
        fig = px.bar(df,x="Total_Count",y="Treatment_Type",orientation="h",
                     title="Top Treatments")
        st.plotly_chart(fig,use_container_width=True)

    with right:
        risk = dm.get_risk_distribution()
        fig = px.pie(risk,values="Count",names="Risk_Level",
                     title="Risk Distribution")
        st.plotly_chart(fig,use_container_width=True)

elif page == "Analytics Intelligence":
    st.header("Analytics Intelligence")
    trends = dm.get_treatment_trends()
    fig = px.line(
        trends.groupby("Month",as_index=False)["Visit_Count"].sum(),
        x="Month",
        y="Visit_Count",
        title="Treatment Trends"
    )
    st.plotly_chart(fig,use_container_width=True)

elif page == "Trust & Safety Operations":
    st.header("Trust & Safety Operations")
    sev = dm.get_severity_distribution()
    fig = px.bar(sev,x="Severity",y="Count",title="Severity Distribution")
    st.plotly_chart(fig,use_container_width=True)

elif page == "Case Management":
    st.header("Case Management")
    st.dataframe(dm.get_top_cases(),use_container_width=True)

elif page == "AI Copilot":
    st.header("AI Copilot")
    st.info("Gemini-powered copilot integration goes here.")
