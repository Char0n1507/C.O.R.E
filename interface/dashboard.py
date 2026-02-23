import streamlit as st
import sqlite3
import pandas as pd
import time
import os
import altair as alt
import requests

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

import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from core.database_enterprise import EnterpriseDatabase

DB_PATH = os.path.join(PROJECT_ROOT, "soc_agent.db")

@st.cache_data(ttl=1)
def load_data():
    try:
        db = EnterpriseDatabase()
        alerts = db.get_recent_alerts(limit=500)
        df = pd.DataFrame(alerts)
        if not df.empty:
            # Convert epoch timestamp string (origin unix) to readable datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], origin='unix', unit='s', errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame()

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state.get("password", "") == "admin": # Basic auth for PoC
            st.session_state["password_correct"] = True
            try:
                del st.session_state["password"]
            except KeyError:
                pass
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
    # Authentication removed for easier testing
    
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
    
    # Check AI config
    use_llm = False
    provider = "none"
    ollama_url = "http://localhost:11434"
    ollama_model = "llama3"
    api_key = os.getenv("GOOGLE_API_KEY")

    try:
        import yaml
        with open(os.path.join(os.path.dirname(DB_PATH), "config.yaml"), "r") as f:
            core_config = yaml.safe_load(f)
            analyzer_config = core_config.get("analyzer", {})
            use_llm = analyzer_config.get("use_llm", False)
            provider = analyzer_config.get("provider", "none")
            ollama_url = analyzer_config.get("ollama_url", "http://localhost:11434")
            ollama_model = analyzer_config.get("ollama_model", "llama3")
    except:
        pass

    tab1, tab2, tab3 = st.tabs(["📊 Live Events", "💬 AI Threat Hunter", "🗺️ Threat Landscape"])
    
    with tab1:
        df = load_data()
        
        if not df.empty:
            # Apply filters
            # Ensure risk_score is numeric
            df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce').fillna(0)
            filtered_df = df[df['risk_score'] >= min_risk]
            
            # --- Top KPIs ---
            col1, col2, col3, col4 = st.columns(4)
            
            # Fetch real total count bypassing the 500 limit display query
            try:
                real_total = EnterpriseDatabase().get_stats()['total']
            except:
                real_total = len(filtered_df)
                
            critical_alerts = len(filtered_df[filtered_df['risk_score'] >= 90])
            high_alerts = len(filtered_df[(filtered_df['risk_score'] >= 70) & (filtered_df['risk_score'] < 90)])
            medium_alerts = len(filtered_df[(filtered_df['risk_score'] >= 50) & (filtered_df['risk_score'] < 70)])
            
            col1.metric("Total Events Detected", int(real_total))
            
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

    with tab3:
        st.markdown("### 🗺️ MITRE ATT&CK Kill-Chain Analysis")
        st.markdown("Enterprise view of active threats mapped to MITRE tactics and techniques.")
        
        df = load_data()
        if not df.empty and 'mitre_tactic' in df.columns:
            # Filter unknowns for a cleaner MITRE view
            mitre_df = df[(df['mitre_tactic'] != 'Unknown') & (df['mitre_tactic'].notna())]
            
            if not mitre_df.empty:
                col_m1, col_m2 = st.columns(2)
                
                with col_m1:
                    tactic_counts = mitre_df['mitre_tactic'].value_counts().reset_index()
                    tactic_counts.columns = ['Tactic', 'Alert Count']
                    
                    chart_tactic = alt.Chart(tactic_counts).mark_bar(cornerRadiusEnd=4).encode(
                        x=alt.X('Alert Count:Q'),
                        y=alt.Y('Tactic:N', sort='-x'),
                        color=alt.Color('Tactic:N', legend=None, scale=alt.Scale(scheme='tableau10')),
                        tooltip=['Tactic', 'Alert Count']
                    ).properties(height=350, title="Top Active Tactics in Kill-Chain")
                    
                    st.altair_chart(chart_tactic, use_container_width=True)
                    
                with col_m2:
                    tech_counts = mitre_df['mitre_technique'].value_counts().reset_index()
                    tech_counts.columns = ['Technique', 'Alert Count']
                    
                    chart_tech = alt.Chart(tech_counts.head(10)).mark_arc(innerRadius=50).encode(
                        theta="Alert Count:Q",
                        color=alt.Color("Technique:N", scale=alt.Scale(scheme='category20b')),
                        tooltip=['Technique', 'Alert Count']
                    ).properties(height=350, title="Top Threat Techniques Detected")
                    
                    st.altair_chart(chart_tech, use_container_width=True)
                    
                st.markdown("### 🔴 MITRE Threat Feed")
                mitre_display = mitre_df[['timestamp', 'mitre_tactic', 'mitre_technique', 'risk_score', 'analysis']].copy()
                mitre_display = mitre_display.sort_values(by='timestamp', ascending=False)
                
                def highlight_tactic(val):
                    return 'background-color: #3d1414;' if val != 'Unknown' else ''
                    
                st.dataframe(mitre_display.style.map(highlight_tactic, subset=['mitre_tactic']), use_container_width=True, hide_index=True)
            else:
                st.info("No active MITRE mappings detected yet. Wait for a recognizable threat.")
        else:
            st.info("Waiting for MITRE-enriched data from the C.O.R.E. Engine...")

    with tab2:
        st.markdown("### 🤖 Ask C.O.R.E. About Your Data")
        if auto_refresh:
             st.warning("⚠️ **Note:** Please uncheck 'Live Feed (Auto-Refresh)' in the sidebar while chatting, otherwise the page will refresh and interrupt your typing!")
             
        st.markdown("Type a natural language query like: *'Show me all critical alerts from yesterday'* or *'How many times did IP 185.224.128.84 attack?'*")
        
        if not use_llm:
            st.error("AI engine is currently disabled in config.yaml. Please enable Gemini or Ollama to use the Threat Hunter.")
        else:
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "dataframe" in message:
                        st.dataframe(message["dataframe"], use_container_width=True)

            if prompt := st.chat_input("Ask a threat intelligence query..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Analyzing intent and generating SQL query..."):
                        sql_query = None
                        error_msg = None
                        
                        system_prompt = f"""
                        You are a strict SQL query generator for a SOC analyst dashboard.
                        You must convert the user's natural language request into a valid SQLite SQL query.
                        Table Name: alerts
                        
                        Schema:
                        id INTEGER PRIMARY KEY
                        timestamp TEXT (Unix Timestamp in seconds)
                        source TEXT (e.g., /var/log/auth.log)
                        risk_score INTEGER (0-100)
                        analysis TEXT 
                        action TEXT (e.g., 'Block IP', 'Monitor')
                        raw_content TEXT (The raw log line)
                        country TEXT
                        city TEXT
                        ip TEXT
                        mitre_tactic TEXT
                        mitre_technique TEXT
                        
                        RULES:
                        1. Return ONLY the raw SQL query.
                        2. Do NOT wrap the query in markdown code blocks like ```sql.
                        3. Do NOT add any preamble or explanation.
                        4. Example: SELECT * FROM alerts WHERE risk_score > 90 LIMIT 10;
                        
                        User Request: {prompt}
                        """
                        
                        try:
                            if provider == "gemini":
                                import google.generativeai as genai
                                if not api_key:
                                    raise ValueError("Google API Key not found. Cannot use Gemini.")
                                genai.configure(api_key=api_key)
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                resp = model.generate_content(system_prompt)
                                sql_query = resp.text.strip().replace("```sql", "").replace("```", "").strip()
                            elif provider == "ollama":
                                headers = {'Content-Type': 'application/json'}
                                data = {"model": ollama_model, "prompt": system_prompt, "stream": False}
                                resp = requests.post(f"{ollama_url}/api/generate", headers=headers, json=data, timeout=30)
                                resp.raise_for_status()
                                sql_query = resp.json().get("response", "").strip().replace("```sql", "").replace("```", "").strip()
                        except Exception as e:
                            error_msg = f"Failed to generate query: {str(e)}"
                            
                        if sql_query and not error_msg:
                            st.markdown(f"**Execution:** `{sql_query}`")
                            try:
                                if not sql_query.upper().lstrip().startswith("SELECT"):
                                    st.error("For safety reasons, only SELECT SQL queries are allowed in the Threat Hunter.")
                                else:
                                    db = EnterpriseDatabase()
                                    conn = db._get_conn()
                                    rows = conn.run(sql_query)
                                    columns = [col['name'] for col in conn.columns]
                                    conn.close()
                                    
                                    result_df = pd.DataFrame(rows, columns=columns)
                                    
                                    if not result_df.empty and 'timestamp' in result_df.columns:
                                        try:
                                            result_df['timestamp'] = pd.to_datetime(result_df['timestamp'], origin='unix', unit='s', errors='coerce')
                                        except:
                                            pass
                                        
                                        st.dataframe(result_df, use_container_width=True)
                                        st.caption(f"Found {len(result_df)} specific results matching your criteria.")
                                        st.session_state.messages.append({
                                            "role": "assistant", 
                                            "content": f"**Executed SQL:** `{sql_query}`", 
                                            "dataframe": result_df
                                        })
                            except Exception as e:
                                st.error(f"Database Query Failed: {str(e)}")
                                st.session_state.messages.append({"role": "assistant", "content": f"Failed executing query {sql_query}: {str(e)}"})
                        else:
                            st.error(error_msg or "Failed to generate query.")
                            st.session_state.messages.append({"role": "assistant", "content": error_msg or "Failed to generate query."})

    # if auto_refresh:
    #     time.sleep(2)
    #     st.rerun()

if __name__ == "__main__":
    main()
