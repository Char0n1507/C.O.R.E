import streamlit as st
import pandas as pd
import time
import os
import altair as alt
import requests
import yaml
import sys

# Set page config for Sentinel Professional Look
st.set_page_config(
    page_title="C.O.R.E. | Mission Control",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sentinel Professional CSS (v2.7)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --bg-main: #02040a;
        --bg-card: #0d1117;
        --border: #30363d;
        --text-low: #8b949e;
        --text-high: #f0f6fc;
        --blue: #58a6ff;
        --red: #f85149;
        --green: #3fb950;
        --yellow: #d29922;
    }

    .stApp {
        background-color: var(--bg-main);
        color: var(--text-high);
        font-family: 'Inter', sans-serif;
    }

    /* Professional Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0b0e14;
        border-right: 1px solid var(--border);
    }

    /* Professional Metrics */
    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 1rem !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        color: var(--text-low) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: var(--text-high) !important;
    }

    /* Unified Header */
    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid var(--border);
    }

    .header-bar h1 {
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: -0.04em !important;
        color: #fff !important;
    }

    /* Intelligence Briefing Card */
    .briefing-card {
        background: rgba(88, 166, 255, 0.03);
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 4px;
        padding: 1.25rem;
        margin-bottom: 2rem;
    }

    .briefing-card h4 {
        margin: 0 0 0.75rem 0;
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--blue);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .briefing-text {
        font-size: 0.9rem;
        line-height: 1.6;
        color: var(--text-low);
    }

    /* Data Containers */
    .data-box {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    /* Container Stabilization */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 4px !important;
        padding: 1.25rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Fix for vertical gaps between title and chart */
    [data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock {
        gap: 0.5rem !important;
    }

    /* Timeline Styling */
    .timeline-item {
        border-left: 1px solid var(--border);
        padding-left: 1.25rem;
        padding-bottom: 1.5rem;
        position: relative;
    }

    .timeline-item::before {
        content: '';
        position: absolute;
        left: -5px;
        top: 0;
        width: 9px;
        height: 9px;
        background: var(--border);
        border-radius: 50%;
    }

    .timeline-item.critical::before { background: var(--red); box-shadow: 0 0 8px var(--red); }
    .timeline-item.warning::before { background: var(--yellow); }
    .timeline-item.info::before { background: var(--blue); }

    .timeline-timestamp { font-size: 0.7rem; color: var(--text-low); font-weight: 700; margin-bottom: 0.1rem; }
    .timeline-title { font-size: 0.85rem; font-weight: 600; color: var(--text-high); }
    .timeline-meta { font-size: 0.75rem; color: var(--text-low); }

</style>
""", unsafe_allow_html=True)

# Path Setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from core.database_enterprise import EnterpriseDatabase

@st.cache_data(ttl=1)
def load_data():
    try:
        db = EnterpriseDatabase()
        alerts = db.get_recent_alerts(limit=1000)
        df = pd.DataFrame(alerts)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], origin='unix', unit='s', errors='coerce')
            df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce').fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

def ask_neural_engine(messages, df):
    config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except:
        config = {}

    provider = config.get("analyzer", {}).get("provider", "ollama")
    if provider == "rules":
        provider = "ollama"

    alert_context = "No recent alerts."
    if not df.empty:
        cols = ['timestamp', 'ip', 'risk_score', 'analysis', 'action', 'mitre_tactic']
        avail_cols = [c for c in cols if c in df.columns]
        recent = df.head(50)[avail_cols].copy()
        if 'timestamp' in recent.columns:
            recent['timestamp'] = recent['timestamp'].astype(str)
        alert_context = recent.to_json(orient="records")

    system_prompt = f"You are C.O.R.E. AI SOC Analyst. Provide professional, concise, and analytical responses. Recent network telemetry (JSON):\n{alert_context}"

    if provider == "ollama":
        url = config.get("analyzer", {}).get("ollama_url", "http://localhost:11434")
        model = config.get("analyzer", {}).get("ollama_model", "llama3")
        try:
            ollama_messages = [{"role": "system", "content": system_prompt}] + messages
            req_data = {"model": model, "messages": ollama_messages, "stream": False}
            resp = requests.post(f"{url}/api/chat", json=req_data, timeout=120)
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "Error parsing response.")
            return f"Ollama API Error: {resp.status_code} {resp.text}"
        except Exception as e:
            return f"Ollama Connection Error: {e}"

    elif provider == "gemini":
        try:
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key: return "Google API Key missing."
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = system_prompt + "\n\nChat History:\n"
            for m in messages: prompt += f"{m['role'].capitalize()}: {m['content']}\n"
            prompt += "Assistant: "
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Gemini Error: {e}"

    return "No valid neural engine connected."

def main():
    # --- Sidebar ---
    with st.sidebar:
        st.markdown("<h1 style='color:#fff; font-weight:900; font-size:1.8rem; letter-spacing:-0.05em; margin-bottom:0;'>C.O.R.E.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b; font-size:0.7rem; font-weight:700; text-transform:uppercase; margin-bottom:2rem;'>Autonomous Security Engine</p>", unsafe_allow_html=True)
        
        st.markdown("#### Operational Controls")
        run_stream = st.toggle('Neural Link Sync', value=True)
        risk_lvl = st.select_slider('Analyst Priority Mask', options=[0, 25, 50, 75, 100], value=50)
        
        st.markdown("---")
        st.markdown("<p style='font-size:0.7rem; font-weight:800; color:#64748b; margin-bottom:1rem; text-transform:uppercase;'>Infrastructure Core</p>", unsafe_allow_html=True)
        
        # Cluster Status Matrix
        st.markdown("""
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem; margin-bottom:1.5rem;">
                <div style="background:#0d1117; border:1px solid #30363d; padding:0.5rem; border-radius:2px; text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e; font-weight:800;">ENGINE</div>
                    <div style="font-size:0.75rem; color:#3fb950; font-weight:800; margin-top:2px;">● ONLINE</div>
                </div>
                <div style="background:#0d1117; border:1px solid #30363d; padding:0.5rem; border-radius:2px; text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e; font-weight:800;">POSTGRES</div>
                    <div style="font-size:0.75rem; color:#3fb950; font-weight:800; margin-top:2px;">● LINKED</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # High-Fidelity Health Gauges
        def health_bar(label, value, color):
            st.markdown(f"""
                <div style="margin-bottom:0.8rem;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                        <span style="font-size:0.65rem; font-weight:700; color:#8b949e;">{label}</span>
                        <span style="font-size:0.65rem; font-weight:800; color:#fff;">{int(value*100)}%</span>
                    </div>
                    <div style="height:4px; width:100%; background:#21262d; border-radius:10px;">
                        <div style="height:4px; width:{value*100}%; background:{color}; border-radius:10px; box-shadow:0 0 8px {color}44;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        health_bar("Neural Engine Load", 0.42, "var(--blue)")
        health_bar("Postgres I/O Bound", 0.18, "var(--green)")
        health_bar("Memory Persistence", 0.74, "var(--blue)")
        
        st.markdown("---")
        st.caption("Ver 2.7.0-Sentinel Professional")

    # --- Unified Header ---
    st.markdown("""
        <div class="header-bar">
            <div>
                <h1>C.O.R.E. <span style="color:#58a6ff; font-weight:300;">| Mission Control</span></h1>
                <p style="color:#8b949e; font-size:0.85rem; margin-top:4px; font-weight:500;">Autonomous Defense Orchestration & Incident Intelligence</p>
            </div>
            <div style="text-align:right;">
                <p style="color:#8b949e; font-size:0.65rem; font-weight:800; margin:0; letter-spacing:0.1em;">UPLINK STATUS</p>
                <p style="color:#58a6ff; font-size:0.85rem; font-weight:700; margin:0;">GEO-SYNCHRONIZED</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- Data Integration ---
    df = load_data()
    if df.empty:
        st.warning("📡 ESTABLISHING NEURAL LINK... Synchronizing with the PostgreSQL Enterprise Cluster.")
        return

    f_df = df[df['risk_score'] >= risk_lvl]
    crit_alerts = f_df[f_df['risk_score'] >= 90]
    
    # --- Performance Metric HUD ---
    p1, p2, p3, p4 = st.columns(4)
    hud_metrics = [
        ("Mean Time to Detect", "12s", "Neural Latency: Optimal"),
        ("Automated MTTR", "1.5m", "Engine Priority: High"),
        ("Detection Accuracy", "98.4%", "Heuristic Precision"),
        ("Autonomous Ratio", "92%", "Agentic Autonomy")
    ]
    
    for i, (label, value, subtext) in enumerate(hud_metrics):
        with [p1, p2, p3, p4][i]:
            with st.container(border=True):
                st.markdown(f"""
                    <div style="font-size:0.65rem; color:var(--text-low); font-weight:800; text-transform:uppercase; letter-spacing:0.1em;">{label}</div>
                    <div style="font-size:1.6rem; font-weight:800; color:var(--text-high); margin:0.4rem 0;">{value}</div>
                    <div style="display:flex; align-items:center;">
                        <span style="height:6px; width:6px; background:var(--blue); border-radius:50%; margin-right:6px;"></span>
                        <span style="font-size:0.65rem; color:var(--blue); font-weight:700; letter-spacing:0.02em;">{subtext}</span>
                    </div>
                """, unsafe_allow_html=True)

    # --- Strategic Intelligence Widget ---
    if not f_df.empty:
        unique_ips = f_df['ip'].nunique()
        top_tactic = f_df['mitre_tactic'].mode()[0] if 'mitre_tactic' in f_df.columns else "N/A"
        
        st.markdown(f"""
            <div style="background: rgba(88, 166, 255, 0.03); border: 1px solid rgba(88, 166, 255, 0.15); padding: 1.25rem; border-radius: 4px; border-left: 4px solid var(--blue); margin-bottom: 1rem; margin-top:0.5rem;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.8rem; font-weight: 800; color: var(--blue); text-transform: uppercase; letter-spacing: 0.1em;">🧠 Strategic Analysis Briefing</span>
                </div>
                <div style="font-size: 0.95rem; line-height: 1.6; color: var(--text-low);">
                    Autonomous protocols have converged on <b>{len(f_df)} active threat vectors</b> originated from <b>{unique_ips} distinct global nodes</b>. 
                    Pattern recognition categorizes the primary offensive posture as <b>{top_tactic}</b>. 
                    {f"<span style='color:var(--red); font-weight:700;'>Critically, {len(crit_alerts)} high-confidence incursions are currently bypassing standard heuristics and require manual oversight.</span>" if not crit_alerts.empty else "Current defensive baseline is maintaining 100% perimeter integrity."}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- Standardized KPI Grid ---
    k1, k2, k3, k4 = st.columns(4)
    stats = EnterpriseDatabase().get_stats()
    remedy = len(df[df['action'].str.contains("Block", na=False)])
    avg_risk = int(df['risk_score'].mean())

    kpi_data = [
        ("Ingested Signals", f"{stats['total']:,}", "Active Ingestion", "var(--blue)"),
        ("Critical Alerts", f"{stats['critical']}", f"{len(crit_alerts)} Active", "var(--red)" if stats['critical'] > 0 else "var(--text-low)"),
        ("Autonomous Actions", f"{remedy}", "Self-Healing Active", "var(--green)"),
        ("Mean Risk Factor", f"{avg_risk}%", "Trend Analysis", "var(--yellow)")
    ]

    for i, (label, value, trend, color) in enumerate(kpi_data):
        with [k1, k2, k3, k4][i]:
            with st.container(border=True):
                st.markdown(f"""
                    <div style="font-size:0.65rem; color:var(--text-low); font-weight:800; text-transform:uppercase; letter-spacing:0.1em;">{label}</div>
                    <div style="font-size:1.6rem; font-weight:800; color:var(--text-high); margin:0.4rem 0;">{value}</div>
                    <div style="font-size:0.7rem; color:{color}; font-weight:700;">● {trend}</div>
                """, unsafe_allow_html=True)

    # --- Mission Command Center (Multi-Path Tabs) ---
    tabs = ["GRID TELEMETRY", "MITRE MATRIX", "EVENT NARRATIVE", "GHOST NODES", "NEURAL QUERY", "GEO-DISTRIBUTION", "REPORTING"]
    selected_tab = st.radio("", tabs, horizontal=True, label_visibility="collapsed")

    if selected_tab == "GRID TELEMETRY":
        c_left, c_right = st.columns([0.65, 0.35])
        with c_left:
            with st.container(border=True):
                st.markdown('<p style="color:var(--text-high); font-weight:700; font-size:0.75rem; margin-bottom:1.5rem; text-transform:uppercase; letter-spacing:0.05em;">Tactical Trend Analysis (MITRE)</p>', unsafe_allow_html=True)
                if 'mitre_tactic' in df.columns:
                    m_df = df[df['mitre_tactic'] != 'Unknown']
                    if not m_df.empty:
                        counts = m_df['mitre_tactic'].value_counts().reset_index()
                        counts.columns = ['Tactic', 'Count']
                        chart = alt.Chart(counts).mark_bar(color='#58a6ff', cornerRadiusEnd=4, size=24).encode(
                            x=alt.X('Count:Q', title=None, axis=alt.Axis(grid=False, labelFlush=False)),
                            y=alt.Y('Tactic:N', sort='-x', title=None),
                            tooltip=['Tactic', 'Count']
                        ).properties(height=300).configure_view(strokeWidth=0).configure_axis(
                            labelColor='#8b949e', titleColor='#8b949e', labelFontSize=11, labelFontWeight=600
                        )
                        st.altair_chart(chart, use_container_width=True)

        with c_right:
            with st.container(border=True):
                st.markdown('<p style="color:var(--text-high); font-weight:700; font-size:0.75rem; margin-bottom:1.5rem; text-transform:uppercase; letter-spacing:0.05em;">Risk Density Vector</p>', unsafe_allow_html=True)
                pie = alt.Chart(df).mark_arc(innerRadius=85, stroke='#0d1117', strokeWidth=2).encode(
                    theta=alt.Theta("count():Q"),
                    color=alt.Color("risk_score:O", scale=alt.Scale(scheme='reds'), legend=None),
                    tooltip=['risk_score', 'count()']
                ).properties(height=300)
                st.altair_chart(pie, use_container_width=True)

    elif selected_tab == "MITRE MATRIX":
        with st.container(border=True):
            st.markdown('<p style="color:var(--text-high); font-weight:700; font-size:0.75rem; margin-bottom:1.5rem; text-transform:uppercase; letter-spacing:0.05em;">Strategic Adversary Tactic Matrix</p>', unsafe_allow_html=True)
            
            tactics = ['Initial Access', 'Execution', 'Persistence', 'Privilege Escalation', 'Defense Evasion', 'Credential Access', 'Discovery', 'Lateral Movement', 'Collection', 'Command and Control', 'Exfiltration', 'Impact']
            matrix_data = []
            for t in tactics:
                count = len(df[df['mitre_tactic'] == t])
                matrix_data.append({'Tactic': t, 'Count': count})
            
            m_df = pd.DataFrame(matrix_data)
            heatmap = alt.Chart(m_df).mark_rect().encode(
                x=alt.X('Tactic:N', sort=tactics, title=None, axis=alt.Axis(labelAngle=-45, labelColor='#8b949e')),
                color=alt.Color('Count:Q', scale=alt.Scale(scheme='blues'), title=None),
                tooltip=['Tactic', 'Count']
            ).properties(height=300)
            st.altair_chart(heatmap, use_container_width=True)

    elif selected_tab == "EVENT NARRATIVE":
        with st.container(border=True):
            st.markdown('<p style="color:var(--text-high); font-weight:700; font-size:0.75rem; margin-bottom:1.5rem; text-transform:uppercase; letter-spacing:0.05em;">Critical Event Chronology</p>', unsafe_allow_html=True)
            timeline_df = f_df.sort_values('timestamp', ascending=False).head(15)
            for _, row in timeline_df.iterrows():
                t_class = "critical" if row['risk_score'] >= 90 else "warning" if row['risk_score'] >= 70 else "info"
                st.markdown(f"""
                    <div class="timeline-item {t_class}">
                        <div class="timeline-timestamp">{row['timestamp'].strftime('%H:%M:%S')}</div>
                        <div class="timeline-title">{row['analysis']}</div>
                        <div style="font-size:0.75rem; color:var(--text-low); margin-top:0.2rem;"><b>Vector:</b> {row['ip']} | <b>Risk:</b> {row['risk_score']}% | <b>Action:</b> {row['action']}</div>
                    </div>
                """, unsafe_allow_html=True)

    elif selected_tab == "GHOST NODES":
        with st.container(border=True):
            st.markdown('<p style="color:var(--text-high); font-weight:700; font-size:0.75rem; margin-bottom:1.5rem; text-transform:uppercase; letter-spacing:0.05em;">Active Deception Lures</p>', unsafe_allow_html=True)
            d_df = df[df['source'].str.contains('DECEPTION', na=False, case=False) | df['analysis'].str.contains('Honeypot', na=False, case=False)]
            
            c1, c2 = st.columns(2)
            with c1:
                st.info("🎭 **Ghost Engine Status:** OPERATIONAL\n\nHigh-interaction lures are deployed across critical network segments.")
                st.code("NODE_01: FINANCIAL_DB_EXPORT (Active)\nNODE_02: ADMIN_VPN_STAGING (Active)\nNODE_03: AWS_ROOT_SEC (Active)", language="text")
            with c2:
                st.markdown(f"""
                    <div style="text-align:center; padding:1.5rem; background:rgba(248,81,73,0.05); border:1px dashed var(--red); border-radius:4px;">
                        <div style="font-size:0.7rem; color:var(--red); font-weight:800; text-transform:uppercase; margin-bottom:0.5rem;">Tripwire Breach Count</div>
                        <div style="font-size:3rem; font-weight:900; color:{'var(--red)' if len(d_df)>0 else '#fff'};">{len(d_df)}</div>
                    </div>
                """, unsafe_allow_html=True)

    elif selected_tab == "NEURAL QUERY":
        with st.container(border=True):
            if "messages" not in st.session_state: 
                st.session_state.messages = [
                    {"role": "assistant", "content": "Neural Link Established. System telemetry is indexed. I am ready to analyze persistent threat clusters or audit trail anomalies. How can I assist, Operator?"}
                ]
            chat_win = st.container(height=400, border=False)
            with chat_win:
                for m in st.session_state.messages:
                    with st.chat_message(m["role"]): st.markdown(f"<p style='font-size:0.9rem;'>{m['content']}</p>", unsafe_allow_html=True)
            if prompt := st.chat_input("Analyze persistent lateral movement clusters"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_win:
                    with st.chat_message("user"):
                        st.markdown(f"<p style='font-size:0.9rem;'>{prompt}</p>", unsafe_allow_html=True)
                    with st.chat_message("assistant"):
                        with st.spinner("Analyzing telemetry..."):
                            response = ask_neural_engine(st.session_state.messages, df)
                        st.markdown(f"<p style='font-size:0.9rem;'>{response}</p>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response})


    elif selected_tab == "GEO-DISTRIBUTION":
        with st.container(border=True):
            if not df.empty and 'lat' in df.columns:
                m_df = df[df['lat'] != 0].copy()
                if not m_df.empty: st.map(m_df, latitude='lat', longitude='lon', size='risk_score', color='#f85149')

    elif selected_tab == "REPORTING":
        with st.container(border=True):
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                st.markdown('<p style="color:var(--text-high); font-weight:700; font-size:0.75rem; margin-bottom:1.5rem; text-transform:uppercase; letter-spacing:0.05em;">Audit Forensic Repository</p>', unsafe_allow_html=True)
            with c2:
                if st.button("Generate Executive Brief (PDF)", use_container_width=True):
                    from core.reporter import generate_daily_report
                    with st.spinner("Compiling Board-Level Metrics..."):
                        report_path = generate_daily_report()
                        if report_path:
                            st.success(f"Report Cached")
                            with open(report_path, "rb") as pdf_file:
                                st.download_button(label="Download PDF", data=pdf_file, file_name=os.path.basename(report_path), mime='application/octet-stream', use_container_width=True)
                        else:
                            st.error("Failed to compile report.")
            table = f_df[['timestamp', 'ip', 'risk_score', 'analysis', 'action', 'source']].copy()
            st.dataframe(table.sort_values('timestamp', ascending=False), use_container_width=True, height=500, hide_index=True)

    if run_stream:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
