import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide", page_title="GS Credit Operations Portal")
st.title("🛡️ Institutional Credit Risk & Settlement Control Console")
st.caption("Goldman Sachs Operations Division — Core Transaction Integrity Monitor")

# Unified Data Loading Mechanism
def load_pipeline_data():
    # Attempt connection via live PostgreSQL environment
    try:
        conn = psycopg2.connect(dbname="credit_ops_db", user="postgres", password="your_actual_password_here", host="localhost", port="5432")
        query = """
            SELECT rp.counterparty_id, rp.legal_entity_name, rp.sector, rp.risk_rating_tier, 
                   rp.exception_status, sl.pending_trade_volume_millions, sl.exposure_at_default_millions, sl.settlement_status
            FROM counterparty_risk_profiles rp
            JOIN operational_settlement_logs sl ON rp.counterparty_id = sl.counterparty_id;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        st.sidebar.success("Database Status: Connected to Live PostgreSQL Engine")
        return df
    except Exception:
        # Seamlessly fallback to the Mock flat file database
        st.sidebar.warning("Database Status: Running on Secure Mock File Storage")
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        MOCK_FILE_PATH = os.path.join(SCRIPT_DIR, 'data', 'mock_database_records.csv')
        
        if os.path.exists(MOCK_FILE_PATH):
            return pd.read_csv(MOCK_FILE_PATH)
        else:
            return pd.DataFrame()

df = load_pipeline_data()

if not df.empty:
    # Aggregated KPI Summary Metrics Cards
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Active Counterparties", len(df['counterparty_id'].unique()))
    m2.metric("Total Exposure at Risk", f"${df['exposure_at_default_millions'].sum():.2f}M")
    exceptions_count = len(df[df['exception_status'].astype(str).str.contains('CRITICAL')])
    m3.metric("Critical Policy Exception Flags", exceptions_count, delta=f"{exceptions_count} Flags Active", delta_color="inverse")
    
    st.markdown("---")
    
    # Left Viewport: Settlement Queue Ledger Table / Right Viewport: Analytical Charts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Centralized Clearing & Trade Settlement Queue")
        
        def highlight_settlement(val):
            return 'background-color: #FFD2D2; color: #9C0006' if val == 'HOLD_FOR_COLLATERAL' else 'background-color: #D2FFD2; color: #006100'
            
        st.dataframe(df.style.applymap(highlight_settlement, subset=['settlement_status']), use_container_width=True)
        
    with col2:
        st.subheader("📊 Exposure Distribution by Risk Tier")
        tier_chart = df.groupby('risk_rating_tier')['exposure_at_default_millions'].sum()
        
        fig, ax = plt.subplots(figsize=(5, 4))
        tier_chart.plot(kind='bar', color='#1e3d59', ax=ax)
        ax.set_ylabel("Exposure (Millions USD)")
        ax.set_xlabel("Internal Credit Rating Tier")
        plt.xticks(rotation=0)
        st.pyplot(fig)
else:
    st.info("👋 Welcome to the GS Operations Portal! Please execute your data extraction backend to populate pipeline data fields.")
    st.code("python3 scripts/excel_extractor.py")
