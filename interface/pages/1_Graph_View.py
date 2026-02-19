import streamlit as st
import sqlite3
import pandas as pd
import os
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import re

st.set_page_config(
    page_title="Graph View | C.O.R.E. SOC",
    page_icon="🕸️",
    layout="wide",
)

# Dark theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: 'Outfit', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🕸️ Threat Knowledge Graph")
st.markdown("Visualizing the Kill Chain across ingested logs.")

# Get path relative to this script
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "soc_agent.db")

@st.cache_data(ttl=2)
def load_data():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query("SELECT * FROM alerts WHERE risk_score > 50 ORDER BY id DESC LIMIT 100", conn)
    except Exception:
        return pd.DataFrame()

def extract_ip(text):
    match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", text)
    return match.group(1) if match else None

def extract_user(text):
    # simple entity extraction based on our simulator
    if "user " in text:
        match = re.search(r"user (\w+)", text)
        if match: return match.group(1)
    for u in ["root", "admin", "guest"]:
        if f"for {u}" in text or f"user {u}" in text: return u
    return "unknown"

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == "admin": 
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

if not check_password():
    st.stop()

df = load_data()

if not df.empty:
    # Build Network Graph
    net = Network(height="600px", width="100%", bgcolor="#0f172a", font_color="#e2e8f0", directed=True)
    G = nx.DiGraph()

    for _, row in df.iterrows():
        raw = row['raw_content']
        ip = extract_ip(raw)
        user = extract_user(raw)
        alert = row['analysis']
        risk = row['risk_score']
        
        if ip:
            # IP Node (Red for attacker)
            G.add_node(ip, title=f"Attacker IP: {ip}", color="#ef4444", shape="dot", size=25)
            
            # The Alert Node
            color_box = "#f59e0b" if risk < 90 else "#ef4444"
            G.add_node(alert, title=f"Alert: {alert} (Risk: {risk})", color=color_box, shape="box")

            if user and user != "unknown":
                # User Node (Yellow for compromised/targeted)
                G.add_node(user, title=f"Target User: {user}", color="#38bdf8", shape="dot", size=20)
                G.add_edge(ip, user, title="Targeted")
                G.add_edge(user, alert, title="Triggered")
            else:
                G.add_edge(ip, alert, title="Triggered")

    net.from_nx(G)
    
    # Save graph to HTML then read and display it via Streamlit components
    html_path = "graph.html"
    net.save_graph(html_path)
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_data = f.read()
        
    components.html(html_data, height=650)
    
else:
    st.info("Not enough threats detected to build a graph yet!")
