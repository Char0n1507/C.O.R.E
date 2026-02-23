import streamlit as st
import pandas as pd
import os
import plotly.express as px
import sys

# Path Setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)
from core.database_enterprise import EnterpriseDatabase

st.set_page_config(
    page_title="Network Geography | C.O.R.E. SOC",
    page_icon="🌍",
    layout="wide",
)

# Sentinel Professional Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #02040a;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }
    
    .header-bar {
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid #30363d;
    }
    
    .header-bar h1 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #f0f6fc !important;
        letter-spacing: -0.02em !important;
    }
    
    .map-box {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 5px;
    }

    .data-table-box {
        margin-top: 2rem;
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-bar">
        <h1>Geospatial Threat Matrix</h1>
        <p style='color:#8b949e; font-size:0.8rem; margin:2px 0 0 0;'>Regional Heat-Mapping and Origin-Point Clustering</p>
    </div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=2)
def load_data():
    try:
        db = EnterpriseDatabase()
        alerts = db.get_recent_alerts(limit=1000)
        df = pd.DataFrame(alerts)
        if not df.empty:
            df = df[(df['lat'] != 0.0) | (df['alpha_3'] != '')]
            df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce').fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # Aggregation
    map_data = df.groupby(['alpha_3', 'country']).size().reset_index(name='Incursions')
    
    st.markdown("<div class='map-box'>", unsafe_allow_html=True)
    # Map
    fig = px.choropleth(map_data, 
                        locations="alpha_3", 
                        color="Incursions", 
                        hover_name="country", 
                        color_continuous_scale="reds",
                        template="plotly_dark",
                        projection="natural earth")
    
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#30363d",
            landcolor="#161b22",
            bgcolor='rgba(0,0,0,0)',
            lakecolor="#0d1117"
        ),
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", color="#f0f6fc", size=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Forensic Feed
    st.markdown("<div class='data-table-box'>", unsafe_allow_html=True)
    st.markdown("<p style='color:#f0f6fc; font-weight:600; font-size:0.85rem; margin-bottom:1rem;'>Regional Incident Stream</p>", unsafe_allow_html=True)
    feed = df[['timestamp', 'ip', 'country', 'city', 'risk_score', 'analysis']].copy()
    feed['timestamp'] = pd.to_datetime(feed['timestamp'], origin='unix', unit='s', errors='coerce')
    feed.columns = ['Time', 'Source', 'Region', 'City', 'Risk', 'Analysis']
    
    st.dataframe(
        feed.sort_values('Time', ascending=False).head(15), 
        use_container_width=True,
        hide_index=True
    )
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Awaiting regional telemetry signatures...")
