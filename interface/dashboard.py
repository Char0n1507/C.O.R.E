import streamlit as st
import sqlite3
import pandas as pd
import time
import os
import altair as alt

# Set page config
st.set_page_config(
    page_title="C.O.R.E. | AI SOC Analyst Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for glowing metrics and fonts
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Typography */
    .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Metric cards / Glassmorphism */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
        color: #38bdf8;
        font-weight: 700;
        text-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }
    
    /* specific color overrides for critical metrics */
    div[data-testid="stMetric"]:has(div:contains("Critical")) div[data-testid="stMetricValue"] {
        color: #ef4444 !important;
        text-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
    }
    
    div[data-testid="stMetric"]:has(div:contains("High")) div[data-testid="stMetricValue"] {
        color: #f59e0b !important;
        text-shadow: 0 0 20px rgba(245, 158, 11, 0.4);
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "soc_agent.db")

@st.cache_data(ttl=1)
def load_data():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            query = "SELECT * FROM alerts ORDER BY id DESC LIMIT 500"
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                # Convert epoch timestamp to readable datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame()

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == "admin": # Basic auth for PoC
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 C.O.R.E. SOC Authentication")
        st.text_input("Please enter the operator password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 C.O.R.E. SOC Authentication")
        st.text_input("Please enter the operator password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

def main():
    if not check_password():
        return
        
    # --- Sidebar ---
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/security-checked--v1.png", width=60)
        st.title("C.O.R.E. SOC")
        st.markdown("---")
        
        auto_refresh = st.checkbox('Live Feed (Auto-Refresh)', value=True)
        min_risk = st.slider('Minimum Risk Score Filter', 0, 100, 50)
        
        st.markdown("---")
        st.markdown("### System Status")
        st.success("🟢 Core Engine: Online")
        st.success("🟢 Database: Connected")
        
        import yaml
        try:
            with open(os.path.join(os.path.dirname(DB_PATH), "config.yaml"), "r") as f:
                core_config = yaml.safe_load(f)
                use_llm = core_config.get("analyzer", {}).get("use_llm", False)
                provider = core_config.get("analyzer", {}).get("provider", "none")
                
                if use_llm:
                    if provider == "gemini":
                        st.success("🤖 AI Analyst: Gemini Pro (Live)")
                    elif provider == "ollama":
                        st.success("🧠 AI Analyst: Ollama (Offline)")
                else:
                    st.info("🟡 AI Analyst: Disabled (Rules Only)")
        except:
            st.info("🟡 AI Analyst: Status Unknown")

    # --- Main Content ---
    st.title("🛡️ Enterprise Threat Intelligence")
    st.markdown("Real-time monitoring and autonomous response center.")
    
    df = load_data()
    
    if not df.empty:
        # Apply filters
        # Ensure risk_score is numeric
        df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce').fillna(0)
        filtered_df = df[df['risk_score'] >= min_risk]
        
        # --- Top KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        
        total_alerts = len(filtered_df)
        critical_alerts = len(filtered_df[filtered_df['risk_score'] >= 90])
        high_alerts = len(filtered_df[(filtered_df['risk_score'] >= 70) & (filtered_df['risk_score'] < 90)])
        medium_alerts = len(filtered_df[(filtered_df['risk_score'] >= 50) & (filtered_df['risk_score'] < 70)])
        
        col1.metric("Total Events Detected", total_alerts)
        
        # Display delta for critical alerts dynamically
        col2.metric("Critical Threats (90-100)", critical_alerts, delta="Requires Action" if critical_alerts > 0 else "All Clear", delta_color="inverse" if critical_alerts > 0 else "normal")
        col3.metric("High Risks (70-89)", high_alerts)
        col4.metric("Medium Risks (50-69)", medium_alerts)
        
        st.markdown("---")
        
        # --- Visualizations ---
        st.markdown("### Threat Distribution")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Risk score distribution
            if not filtered_df.empty:
                base = alt.Chart(filtered_df).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                    x=alt.X('risk_score:Q', bin=alt.Bin(maxbins=20), title='Risk Score'),
                    y=alt.Y('count():Q', title='Number of Alerts'),
                    color=alt.condition(
                        alt.datum.risk_score >= 80,
                        alt.value('#f85149'),  # Red for high risk
                        alt.value('#58a6ff')   # Blue for lower risk
                    ),
                    tooltip=['count()', 'risk_score']
                ).properties(height=280, title="Alerts by Risk Score").configure_view(strokeOpacity=0)
                st.altair_chart(base, use_container_width=True)
                
        with chart_col2:
            # Top Threat Types
            if 'analysis' in filtered_df.columns and not filtered_df.empty:
                threat_counts = filtered_df['analysis'].value_counts().reset_index()
                threat_counts.columns = ['Threat Type', 'Count']
                
                chart2 = alt.Chart(threat_counts.head(5)).mark_arc(innerRadius=60).encode(
                    theta="Count:Q",
                    color=alt.Color("Threat Type:N", scale=alt.Scale(scheme='set2')),
                    tooltip=['Threat Type', 'Count']
                ).properties(height=280, title="Top Threat Classifications")
                st.altair_chart(chart2, use_container_width=True)

        # --- Threat Feed ---
        st.markdown("### 🔴 Active Threat Feed")
        
        # Format dataframe for display
        display_df = filtered_df[['timestamp', 'risk_score', 'analysis', 'action', 'source', 'raw_content']].copy()
        display_df = display_df.sort_values(by='timestamp', ascending=False)
        
        # Rename columns to look professional
        display_df.columns = ['Timestamp', 'Risk Score', 'Threat Analysis', 'Auto-Action', 'Source Path', 'Raw Event Log']
        
        # Apply pandas styling
        def highlight_risk(val):
            # Check if value is a valid numeric score before styling
            if pd.isna(val) or not isinstance(val, (int, float)):
                return ''
            if val >= 90: return 'color: #ff4b4b; font-weight: bold'
            elif val >= 70: return 'color: #ffa421; font-weight: bold'
            else: return 'color: #3dd56d'

        styled_df = display_df.style.map(highlight_risk, subset=['Risk Score'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
    else:
        st.info("No alerts found in the database yet. Waiting for agents...")

    if auto_refresh:
        time.sleep(2)
        st.rerun()

if __name__ == "__main__":
    main()
