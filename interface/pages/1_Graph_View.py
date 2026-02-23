import streamlit as st
import pandas as pd
import os
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import re
import sys
import json

# Path Setup for Enterprise Logic
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)
from core.database_enterprise import EnterpriseDatabase

st.set_page_config(
    page_title="C.O.R.E. | Intelligence Correlation",
    page_icon="🕸️",
    layout="wide",
)

# Sentinel Professional Theme (High Density, Minimalist)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    .stApp {
        background-color: #02040a;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }
    
    .header-container {
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid #21262d;
    }
    
    .header-container h1 {
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        color: #f0f6fc !important;
        letter-spacing: -0.04em !important;
        margin: 0 !important;
    }
    
    .graph-card {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 6px;
        overflow: hidden;
    }

    .legend-panel {
        display: flex;
        gap: 24px;
        padding: 12px 20px;
        background: #161b22;
        border-bottom: 1px solid #30363d;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #8b949e;
    }
    
    .legend-item { display: flex; align-items: center; gap: 8px; }
    .mark { width: 10px; height: 10px; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("""
<div class="header-container">
    <h1>C.O.R.E. <span style="color:#58a6ff; font-weight:300;">| Intelligence Correlation</span></h1>
    <p style='color:#8b949e; font-size:0.85rem; margin-top:5px; font-weight:500;'>Multi-Vector Incursion Analysis & Relational Intelligence Mapping</p>
</div>
""", unsafe_allow_html=True)

# Legend Section
st.markdown("""
<div class="legend-panel">
    <div class="legend-item"><div class="mark" style="background:#f85149;"></div> Attacker IP</div>
    <div class="legend-item"><div class="mark" style="background:#58a6ff;"></div> Target Entity</div>
    <div class="legend-item"><div class="mark" style="background:#d29922;"></div> MITRE Tactic</div>
    <div class="legend-item"><div class="mark" style="background:#3fb950;"></div> Shield Status</div>
    <div class="legend-item"><div class="mark" style="background:#bc8cff;"></div> Geo Cluster</div>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=2)
def load_data():
    try:
        db = EnterpriseDatabase()
        alerts = db.get_recent_alerts(limit=100)
        df = pd.DataFrame(alerts)
        return df
    except Exception:
        return pd.DataFrame()

def extract_user(text):
    text = str(text).lower()
    for u in ["root", "admin", "system", "administrator"]:
        if f"for {u}" in text or f"user {u}" in text: return u
    return None

df = load_data()

if not df.empty:
    st.markdown("<div class='graph-card'>", unsafe_allow_html=True)
    
    # Pyvis setup with "Sentinel Professional" configuration
    net = Network(height="720px", width="100%", bgcolor="#0d1117", font_color="#c9d1d9", directed=True)
    G = nx.DiGraph()

    # Sentinel Palette (Professional GitHub/Palantir style)
    PALETTE = {
        "IP": {"bg": "#f85149", "border": "#da3633"},
        "TARGET": {"bg": "#58a6ff", "border": "#1f6feb"},
        "TACTIC": {"bg": "#d29922", "border": "#9e6a03"},
        "ACTION": {"bg": "#3fb950", "border": "#238636"},
        "GEO": {"bg": "#bc8cff", "border": "#8957e5"},
        "BASE": {"bg": "#161b22", "border": "#30363d"}
    }

    nodes_added = {}

    for i, row in df.iterrows():
        ip = row['ip']
        country = row['country']
        tactic = row['mitre_tactic'] if row['mitre_tactic'] != 'Unknown' else "Network Exploitation"
        alert = row['analysis']
        risk = row['risk_score']
        action = row['action']
        user = extract_user(row['raw_content'])

        # 1. Country Node (Root Cluster)
        if country and country != "Internal/Private":
            if country not in nodes_added:
                G.add_node(country, label=country, title=f"Region: {country}", 
                           color=PALETTE["GEO"]["bg"], shape="dot", size=15)
                nodes_added[country] = True

        # 2. Attacker Node
        if ip:
            if ip not in nodes_added:
                G.add_node(ip, label=ip, title=f"Source: {ip}", 
                           color=PALETTE["IP"]["bg"], shape="dot", size=12)
                nodes_added[ip] = True
                if country and country != "Internal/Private":
                    G.add_edge(country, ip, color="#30363d", width=1)

            # 3. Alert Vector (The specialized label)
            alert_id = f"alert_{ip}_{hash(alert)}"
            if alert_id not in nodes_added:
                G.add_node(alert_id, label=alert[:25]+"..." if len(alert) > 25 else alert, 
                           title=f"Analysis: {alert}\nScore: {risk}%", 
                           color=PALETTE["BASE"]["bg"], shape="box", 
                           font={"size": 10, "face": "JetBrains Mono", "color": "#f0f6fc"},
                           borderWidth=1, margin=5)
                nodes_added[alert_id] = True
                
                G.add_edge(ip, alert_id, color="#484f58", width=1)
                
                # Link to MITRE Tactic
                if tactic not in nodes_added:
                    G.add_node(tactic, label=tactic.upper(), title="MITRE ATT&CK Tactic", 
                               color=PALETTE["TACTIC"]["bg"], shape="triangle", size=15)
                    nodes_added[tactic] = True
                G.add_edge(alert_id, tactic, color="#30363d", width=1, dash=True)
    
                # 4. Target User
                if user:
                    if user not in nodes_added:
                        G.add_node(user, label=f"@{user}", title=f"Account: {user}", 
                                   color=PALETTE["TARGET"]["bg"], shape="dot", size=10)
                        nodes_added[user] = True
                    G.add_edge(alert_id, user, color="#30363d", width=1, dash=True)

            # 5. Active Block Status
            if "Block" in action:
                block_id = f"block_{ip}"
                if block_id not in nodes_added:
                    G.add_node(block_id, label="SHIELD", title="Firewalk Enforcement: Active", 
                               color=PALETTE["ACTION"]["bg"], shape="hexagon", size=12)
                    nodes_added[block_id] = True
                    G.add_edge(block_id, ip, color="#238636", width=2)

    net.from_nx(G)
    
    # Precise Physics Options for Large Data Clusters
    options = {
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -2000,
                "centralGravity": 0.1,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 0.1
            },
            "solver": "barnesHut",
            "stabilization": {"iterations": 200, "updateInterval": 50}
        },
        "edges": {
            "smooth": {"type": "curvedCW", "roundness": 0.1},
            "color": {"inherit": "from"}
        },
        "interaction": {
            "hover": True,
            "hideEdgesOnDrag": True,
            "multiselect": True
        }
    }
    net.set_options(json.dumps(options))
    
    # Save with custom body CSS to eliminate white margins
    html_path = "graph.html"
    net.save_graph(html_path)
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        html = html.replace("<body", "<body style='margin:0; padding:0; background:#0d1117; overflow:hidden;'")
        html = html.replace("height: 720px;", "height: 720px; background:#0d1117;")
            
    components.html(html, height=730)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Forensic Relationship Table"):
        st.dataframe(df[['timestamp', 'ip', 'analysis', 'risk_score']].head(20), use_container_width=True)

else:
    st.info("System initializing... Aggregating security telemetry for relational mapping.")
