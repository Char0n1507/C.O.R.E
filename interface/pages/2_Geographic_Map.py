import streamlit as st
import sqlite3
import pandas as pd
import os
import plotly.express as px

st.set_page_config(
    page_title="Threat Map | C.O.R.E. SOC",
    page_icon="🌍",
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

st.title("🌍 Global Threat Monitor")
st.markdown("Live Geo-IP Mapping of active cyber attacks against your infrastructure.")

# Get path relative to this script
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "soc_agent.db")

@st.cache_data(ttl=2)
def load_data():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Only pull rows where we have valid location data
            return pd.read_sql_query("SELECT ip, country, city, risk_score, alpha_3 FROM alerts WHERE lat != 0.0 OR lon != 0.0 ORDER BY id DESC LIMIT 500", conn)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # Aggregate data logically: count amount of attacks per country
    map_data = df.groupby(['alpha_3', 'country']).size().reset_index(name='Attack Count')
    
    # Generate Map using Plotly Express
    fig = px.choropleth(map_data, 
                        locations="alpha_3", 
                        color="Attack Count", 
                        hover_name="country", 
                        color_continuous_scale="Reds",
                        title="Attacks by Origin Country")
    
    # Configure map style for dark mode
    fig.update_layout(
        geo=dict(bgcolor='#0b0f19', lakecolor='#0f172a', coastlinecolor='#38bdf8'),
        paper_bgcolor='#0b0f19',
        font_color='#f8fafc'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw Data
    st.markdown("### Latest Geolocated Threats")
    st.dataframe(df.head(10), use_container_width=True)
else:
    st.info("No incoming geographic threats detected yet! Wait for an external IP attack.")
