import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from src.ingestion import DataIngestionPipeline
from src.engine import RiskScoringEngine
from src.llm_analyzer import LLMRenewalAnalyzer

load_dotenv()

st.set_page_config(page_title="Contentstack Renewal Intelligence Engine", layout="wide")

st.title("🔮 Contentstack Renewal Intelligence Engine")
st.markdown("Automated quantitative metric tracking and AI-synthesized CSM account playbooks.")
st.markdown("---")

# 1. Securely cache data layers
@st.cache_data
def process_data_snapshots():
    pipeline = DataIngestionPipeline(raw_data_dir="data/raw", processed_data_dir="data/processed")
    pipeline.run_pipeline()
    engine = RiskScoringEngine(processed_data_dir="data/processed")
    return engine.compute_risk_matrix(), pipeline.csm_notes, pipeline.changelog

# Pre-initialize dataframes
df_matrix = pd.DataFrame()
raw_csm_notes = ""
raw_changelog = ""

try:
    df_matrix, raw_csm_notes, raw_changelog = process_data_snapshots()
except Exception as e:
    st.error(f"❌ Core Data Pipeline Failed to Initialize: {str(e)}")

if not df_matrix.empty:
    # Coerce text dates from accounts.csv cleanly into pandas datetime objects
    df_matrix['contract_end_date'] = pd.to_datetime(df_matrix['contract_end_date'])
    current_date = pd.to_datetime("2026-06-14")
    df_matrix['days_to_renewal'] = (df_matrix['contract_end_date'] - current_date).dt.days
    
    # Isolate accounts whose contract terms expire within the next 90 days
    display_df = df_matrix[df_matrix['days_to_renewal'] <= 90].copy()
    
    # Sidebar Filtering Controls for Interactivity
    st.sidebar.header("🎯 Dashboard Controls")
    csm_list = ["All CSMs"] + list(display_df['csm_name'].unique())
    selected_csm = st.sidebar.selectbox("Filter Matrix by CSM Assignd", csm_list)
    
    if selected_csm != "All CSMs":
        display_df = display_df[display_df['csm_name'] == selected_csm]

    # Render summary indicator metric cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Contracts Renewing (90 Days)", len(display_df))
    col2.metric("High Risk Scenarios", len(display_df[display_df['quantitative_risk_tier'] == 'High']))
    col3.metric("Medium Risk Scenarios", len(display_df[display_df['quantitative_risk_tier'] == 'Medium']))
    
    st.subheader("📋 Impending Account Renewal Risk Matrix")
    st.dataframe(
        display_df[[
            'account_id', 'account_name', 'arr', 'plan_tier', 'csm_name',
            'days_to_renewal', 'usage_mom_change', 'high_sev_tickets', 
            'nps_score', 'quantitative_risk_tier'
        ]],
        use_container_width=True
    )
    
    # 🌟 NEW INTERACTIVE LAYER: Focus Account Strategic Brief Generator
    st.markdown("---")
    st.subheader("🔮 Generative AI Renewal Intelligence")
    st.markdown("Select an at-risk account below to trigger the LLM and analyze hidden text patterns against product telemetry.")
    
    account_selection = st.selectbox(
        "Choose an account to synthesize:", 
        options=display_df['account_name'].unique()
    )
    
    if account_selection:
        account_row = display_df[display_df['account_name'] == account_selection].iloc[0].to_dict()
        
        if st.button(f"Generate Playbook for {account_selection}"):
            with st.spinner("Synthesizing multi-modal telemetry trends and unstructured sentiment cues..."):
                # Initialize your LLM engine layer
                analyzer = LLMRenewalAnalyzer()
                
                # Extract tailored notes matching this entity name
                csm_context = analyzer.extract_relevant_csm_notes(account_selection, raw_csm_notes)
                
                # Fetch structured schema brief from Gemini
                brief = analyzer.generate_account_brief(account_row, csm_context, raw_changelog)
                
                # Render the structured results elegantly in the UI
                st.success("Analysis Complete!")
                
                b1, b2 = st.columns([1, 2])
                with b1:
                    st.metric("Integrated Final Risk Tier", brief.get("final_integrated_risk_tier", "N/A"))
                with b2:
                    st.markdown(f"**Root Cause Vector:** {brief.get('root_cause_analysis')}")
                
                st.info(f"💡 **Non-Obvious Structural Insight:** {brief.get('non_obvious_insight')}")
                
                st.markdown("### 📋 Prioritized Action Items Playbook")
                for action in brief.get("recommended_actions", []):
                    st.markdown(f"- {action}")
                    
else:
    st.warning("⚠️ Waiting for data pipelines to stabilize.")