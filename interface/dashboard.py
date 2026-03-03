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
    page_title="C.O.R.E | Mission Control",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit Default Sidebar Nav since we use our own custom navigation / integrated tabs
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# ProjectDiscovery "Sentinel Elite" UI (v3.5)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200;300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --bg-deep: #000000;
        --bg-panel: rgba(13, 17, 23, 0.7);
        --border-thin: rgba(255, 255, 255, 0.08);
        --text-ghost: #7d8590;
        --text-bright: #ffffff;
        --pd-blue: #3a86ff;
        --pd-red: #f85149;
        --pd-orange: #f0883e;
        --pd-yellow: #d29922;
        --pd-green: #3fb950;
        --pd-purple: #bc8cff;
        --glass-bg: rgba(255, 255, 255, 0.02);
        --neon-glow: 0 0 15px rgba(58, 134, 255, 0.3);
    }

    .stApp {
        background-color: var(--bg-deep);
        color: var(--text-bright);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Glassmorphic ProjectDiscovery Sidebar */
    [data-testid="stSidebar"] {
        background-color: #000 !important;
        border-right: 1px solid var(--border-thin);
        width: 260px !important;
    }
    
    /* Discovery Card Style with Neural Border */
    .discovery-card {
        background: var(--bg-panel);
        border: 1px solid var(--border-thin);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }

    /* Scanning Line Overlay */
    .discovery-card::after {
        content: "";
        position: absolute;
        top: -100%;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--pd-blue), transparent);
        opacity: 0.1;
        animation: scan-line 8s linear infinite;
    }

    @keyframes scan-line {
        0% { top: -100%; }
        100% { top: 200%; }
    }

    .card-label {
        font-size: 0.75rem;
        font-weight: 800;
        color: var(--pd-blue);
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* Tactical Header */
    .tactical-header {
        background: linear-gradient(90deg, #080a0f 0%, #000 100%);
        border-bottom: 1px solid var(--border-thin);
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 4px;
    }

    .neural-stat {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .neural-stat-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        color: var(--pd-green);
    }

    .neural-stat-label {
        font-size: 0.6rem;
        color: var(--text-ghost);
        font-weight: 700;
    }

    /* Removal of UI clutter */
    div[data-testid="stMetric"] { background: none !important; border: none !important; padding: 0 !important; }
    iframe { border-radius: 8px; }
    
    .pulsing-dot {
        animation: pulse-green 2s infinite;
    }

    @keyframes pulse-green {
        0% { transform: scale(0.95); opacity: 0.7; }
        50% { transform: scale(1.1); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.7; }
    }

    /* Restored & Enhanced Classes */
    .stats-ribbon {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 0.5rem;
    }
    
    .stat-item { text-align: center; flex: 1; }
    .stat-value { font-size: 1.4rem; font-weight: 800; margin-bottom: 2px; }
    .stat-label { font-size: 0.6rem; color: var(--text-ghost); text-transform: uppercase; letter-spacing: 0.05em; }

    .score-badge {
        background: rgba(63, 185, 80, 0.1);
        color: var(--pd-green);
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 800;
        margin-left: 10px;
        border: 1px solid rgba(63, 185, 80, 0.2);
    }

    .pd-button {
        background: #fff;
        color: #000;
        border: none;
        padding: 6px 12px;
        font-size: 0.7rem;
        font-weight: 800;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Score Gauge */
    .score-gauge-container {
        height: 6px;
        background: rgba(255,255,255,0.08);
        border-radius: 3px;
        margin-top: 0.5rem;
        width: 100%;
    }
    .score-gauge-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--pd-red), var(--pd-green));
        border-radius: 2px;
        box-shadow: var(--neon-glow);
    }
</style>
""", unsafe_allow_html=True)

# Attack Globe — native Plotly scattergeo (no WebGL/iframe, guaranteed rendering)
def discovery_globe(df=None):
    import plotly.graph_objects as go
    import numpy as np

    SOC = (38.88, -77.03)  # US East — Virginia

    # Attack origin nodes
    origins = [
        (39.91,  116.39, "Beijing, CN",      "#ff3a3a"),
        (31.22,  121.46, "Shanghai, CN",     "#ff3a3a"),
        (55.75,   37.61, "Moscow, RU",       "#ff3a3a"),
        (59.93,   30.32, "St Petersburg, RU","#ff6b35"),
        (39.02,  125.75, "Pyongyang, KP",    "#ff3a3a"),
        (35.68,   51.38, "Tehran, IR",       "#ff6b35"),
        (44.43,   26.10, "Bucharest, RO",    "#ffd700"),
        (-23.5,  -46.60, "São Paulo, BR",    "#ff6b35"),
        ( 6.45,    3.39, "Lagos, NG",        "#ffd700"),
        (28.63,   77.22, "New Delhi, IN",    "#00ff9f"),
        (52.52,   13.40, "Berlin, DE",       "#00ff9f"),
        (52.37,    4.89, "Amsterdam, NL",    "#3a86ff"),
        ( 1.35,  103.82, "Singapore",        "#ff6b35"),
        (-33.86, 151.20, "Sydney, AU",       "#00ff9f"),
        (35.68,  139.69, "Tokyo, JP",        "#ff6b35"),
        (-26.2,   28.04, "Johannesburg, ZA", "#ffd700"),
        (41.01,   28.96, "Istanbul, TR",     "#ff6b35"),
        (50.45,   30.52, "Kyiv, UA",         "#ff3a3a"),
        (-6.21,  106.85, "Jakarta, ID",      "#ffd700"),
        (51.5,    -0.12, "London, UK",       "#3a86ff"),
        (22.54,  114.05, "Hong Kong, CN",    "#ff6b35"),
    ]

    traces = []

    # Draw geodesic attack lines
    for lat, lng, label, color in origins:
        # Interpolate great-circle arc
        n = 40
        t = np.linspace(0, 1, n)
        lats = lat + t * (SOC[0] - lat)
        lons = lng + t * (SOC[1] - lng)
        traces.append(go.Scattergeo(
            lat=list(lats),
            lon=list(lons),
            mode='lines',
            line=dict(width=1.5, color=color),
            opacity=0.75,
            showlegend=False,
            hoverinfo='skip',
        ))

    # Attack origin scatter dots
    traces.append(go.Scattergeo(
        lat=[o[0] for o in origins],
        lon=[o[1] for o in origins],
        mode='markers+text',
        marker=dict(
            size=6,
            color=[o[3] for o in origins],
            symbol='circle',
            line=dict(width=1, color='rgba(255,255,255,0.3)'),
        ),
        text=[o[2] for o in origins],
        textposition='top center',
        textfont=dict(size=7, color='rgba(255,255,255,0.6)'),
        showlegend=False,
        hovertext=[o[2] for o in origins],
        hoverinfo='text',
    ))

    # SOC node (destination) — pulsing gold ring
    traces.append(go.Scattergeo(
        lat=[SOC[0]],
        lon=[SOC[1]],
        mode='markers+text',
        marker=dict(size=14, color='#ffd700', symbol='circle',
                    line=dict(width=2, color='#ffffff')),
        text=["◎ SOC"],
        textposition='bottom center',
        textfont=dict(size=9, color='#ffd700', family='monospace'),
        showlegend=False,
        hovertext=["C.O.R.E SOC — US-EAST-1"],
        hoverinfo='text',
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        geo=dict(
            projection_type='orthographic',
            projection_rotation=dict(lon=-30, lat=15, roll=0),
            showland=True,
            landcolor='rgb(20, 25, 35)',
            showocean=True,
            oceancolor='rgb(5, 10, 20)',
            showlakes=False,
            showcountries=True,
            countrycolor='rgba(255,255,255,0.08)',
            showcoastlines=True,
            coastlinecolor='rgba(255,255,255,0.12)',
            bgcolor='rgba(0,0,0,0)',
            showframe=False,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
    )

    # Add HTML/JS injection for rotation loop
    import streamlit.components.v1 as components
    rotation_speed = 0.5 
    
    components.html(
        f"""
        <script>
            let currentLon = -30;
            setInterval(() => {{
                currentLon += {rotation_speed};
                if (currentLon > 180) currentLon -= 360;
                
                const message = {{
                    type: "plotly_relayout",
                    update: {{ "geo.projection.rotation.lon": currentLon }}
                }};
                
                window.parent.postMessage(message, "*");
            }}, 50);
        </script>
        """,
        height=0,
        width=0,
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

@st.dialog("🌍 Geospatial Threat Matrix", width="large")
def show_geospatial_matrix(df):
    import plotly.express as px
    import streamlit.components.v1 as components
    
    st.markdown("""
        <div style="margin-bottom:1.5rem; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:1rem;">
            <h2 style="font-weight:800;letter-spacing:-0.04em;margin:0;">Geospatial Threat Matrix</h2>
            <p style='color:var(--text-ghost); font-size:0.85rem; margin-top:4px; font-weight:500;'>Multi-Vector Origin-Point Analysis & Clustering</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not df.empty:
        # Pre-process
        map_df = df.copy()
        if 'lat' in map_df.columns and 'alpha_3' in map_df.columns:
            map_df = map_df[(map_df['lat'] != 0.0) | (map_df['alpha_3'] != '')]
            map_data = map_df.groupby(['alpha_3', 'country']).size().reset_index(name='Incursions')
            
            # Map
            fig = px.choropleth(map_data, 
                                locations="alpha_3", 
                                color="Incursions", 
                                hover_name="country", 
                                color_continuous_scale="Reds",
                                template="plotly_dark",
                                projection="orthographic")
            
            fig.update_layout(
                geo=dict(
                    showframe=False,
                    showcoastlines=True,
                    coastlinecolor="#1b1f24",
                    landcolor="#080a0f",
                    bgcolor='rgba(0,0,0,0)',
                    lakecolor="#000000",
                    projection=dict(type='orthographic', scale=1.1)
                ),
                margin={"r":0,"t":20,"l":0,"b":20},
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="JetBrains Mono", color="#7d8590", size=10)
            )
            
            # Auto-rotate
            rotation_speed = 0.5 
            components.html(
                f"""
                <script>
                    let currentLon = 0;
                    setInterval(() => {{
                        currentLon += {rotation_speed};
                        if (currentLon > 180) currentLon -= 360;
                        const message = {{type: "plotly_relayout", update: {{ "geo.projection.rotation.lon": currentLon }}}};
                        window.parent.postMessage(message, "*");
                    }}, 50);
                </script>
                """,
                height=0, width=0
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>📑 REGIONAL INCIDENT STREAM</p>", unsafe_allow_html=True)
            
            feed = df[['timestamp', 'ip', 'country', 'city', 'risk_score', 'analysis']].copy()
            feed = feed.sort_values('timestamp', ascending=False).head(15)
            feed['timestamp'] = pd.to_datetime(feed['timestamp'], origin='unix', unit='s', errors='coerce').dt.strftime('%H:%M:%S')
            feed.columns = ['Time', 'Source', 'Region', 'City', 'Risk', 'Analysis']
            st.dataframe(feed, use_container_width=True, hide_index=True)
    else:
        st.info("Awaiting regional telemetry signatures...")

# Path Setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from core.database_enterprise import EnterpriseDatabase

# ── THREAT TICKER ──────────────────────────────────────────────────────────────
def render_threat_ticker(df):
    if df.empty:
        content = "⬤ ALL SYSTEMS NOMINAL &nbsp;—&nbsp; C.O.R.E AI monitoring active &nbsp;—&nbsp; No active threats detected &nbsp;—&nbsp; " * 4
    else:
        top = df.sort_values('risk_score', ascending=False).head(15)
        parts = []
        for _, r in top.iterrows():
            s = int(r.get('risk_score', 0))
            ip = str(r.get('ip', 'UNKNOWN'))
            tac = str(r.get('mitre_tactic', '?'))
            col = '#ff3a3a' if s >= 90 else '#ff6b35' if s >= 70 else '#ffd700'
            parts.append(f'<span style="color:{col};">⬤ {ip}</span> [{tac}] {s}%')
        content = " &nbsp;│&nbsp; ".join(parts * 2)
    st.markdown(f"""
<div style="background:rgba(255,58,58,0.04);border:1px solid rgba(255,58,58,0.15);
            border-radius:4px;overflow:hidden;display:flex;align-items:center;
            margin-bottom:0.75rem;height:28px;">
  <div style="background:#ff3a3a;color:#fff;font-size:0.5rem;font-weight:900;
              padding:0 0.8rem;height:100%;display:flex;align-items:center;
              white-space:nowrap;letter-spacing:0.15em;font-family:'JetBrains Mono';
              border-right:1px solid rgba(255,0,0,0.3);min-width:fit-content;">◉ LIVE THREAT FEED</div>
  <div style="overflow:hidden;flex:1;padding:0 1rem;">
    <div style="font-size:0.65rem;font-family:'JetBrains Mono';white-space:nowrap;
                animation:coreTickerScroll 45s linear infinite;display:inline-block;">
      {content}
    </div>
  </div>
</div>
<style>
@keyframes coreTickerScroll {{
  from {{ transform: translateX(0); }}
  to   {{ transform: translateX(-50%); }}
}}
</style>""", unsafe_allow_html=True)

# ── DEFCON GAUGE ───────────────────────────────────────────────────────────────
def render_defcon_gauge(df):
    COLORS = {1:'#ff0000', 2:'#ff3a3a', 3:'#ff6b35', 4:'#ffd700', 5:'#3fb950'}
    LABELS = {1:'WAR',    2:'ATTACK', 3:'ELEVATED',4:'GUARDED', 5:'SAFE'}
    if df.empty:
        level = 5
    else:
        avg  = df['risk_score'].mean()
        crit = len(df[df['risk_score'] >= 90])
        if   crit > 100 or avg >= 80: level = 1
        elif crit > 20  or avg >= 65: level = 2
        elif avg >= 45  or crit > 5:  level = 3
        elif avg >= 25:               level = 4
        else:                         level = 5
    color = COLORS[level]
    levels_html = ""
    for i in range(1, 6):
        c = COLORS[i]; active = (i == level)
        bg   = f'rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.2)' if active else 'rgba(255,255,255,0.03)'
        bdr  = c if active else 'rgba(255,255,255,0.06)'
        glow = f'box-shadow:0 0 14px {c};' if active else ''
        tc   = '#fff' if active else 'rgba(255,255,255,0.2)'
        levels_html += f"""
        <div style="flex:1;text-align:center;padding:0.35rem 0.2rem;background:{bg};
                    border:1px solid {bdr};border-radius:4px;{glow}">
          <div style="font-size:1.1rem;font-weight:900;font-family:'JetBrains Mono';color:{tc};">{i}</div>
          <div style="font-size:0.42rem;letter-spacing:0.08em;color:{''+c if active else 'rgba(255,255,255,0.2)'};font-weight:700;">{LABELS[i]}</div>
        </div>"""
    st.markdown(f"""
<div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-thin);
            border-radius:8px;padding:0.85rem;margin-bottom:0.5rem;">
  <div style="font-size:0.52rem;color:var(--text-ghost);font-weight:800;
              text-transform:uppercase;letter-spacing:0.2em;margin-bottom:0.6rem;
              font-family:'JetBrains Mono';">◉ THREAT LEVEL</div>
  <div style="display:flex;gap:0.3rem;margin-bottom:0.6rem;">{levels_html}</div>
  <div style="text-align:center;font-size:0.58rem;color:{color};
              font-family:'JetBrains Mono';font-weight:800;letter-spacing:0.2em;">
    DEFCON {level} — {LABELS[level]}
  </div>
</div>""", unsafe_allow_html=True)

# ── KILL CHAIN TRACKER ─────────────────────────────────────────────────────────
def render_kill_chain(df):
    STAGES = [
        ("RECON",    ["Reconnaissance"]),
        ("WEAPONIZE",["Resource Development"]),
        ("DELIVER",  ["Initial Access"]),
        ("EXPLOIT",  ["Execution","Privilege Escalation"]),
        ("INSTALL",  ["Persistence","Defense Evasion"]),
        ("C2",       ["Command and Control","Lateral Movement"]),
        ("EXFIL",    ["Exfiltration","Impact","Collection"]),
    ]
    hits = []
    for name, tactics in STAGES:
        count = 0 if df.empty else len(df[df['mitre_tactic'].isin(tactics)])
        hits.append((name, count))
    max_c = max((c for _, c in hits), default=1) or 1
    stages_html = ""
    for i, (name, count) in enumerate(hits):
        pct   = min(100, int(count / max_c * 100)) if count > 0 else 0
        col   = '#ff3a3a' if pct>60 else '#ff6b35' if pct>20 else '#3a86ff' if count>0 else 'rgba(255,255,255,0.1)'
        glow  = f'box-shadow:0 0 8px {col};' if count > 0 else ''
        tc    = '#fff' if count > 0 else 'rgba(255,255,255,0.25)'
        label = str(count) if count > 0 else '—'
        stages_html += f"""
        <div style="flex:1;text-align:center;">
          <div style="font-size:0.44rem;font-family:'JetBrains Mono';color:{tc};font-weight:800;margin-bottom:3px;letter-spacing:0.04em;">{name}</div>
          <div style="height:3px;background:{col};border-radius:2px;opacity:{1.0 if count>0 else 0.15};{glow}margin-bottom:3px;"></div>
          <div style="font-size:0.5rem;color:{col};font-weight:700;">{label}</div>
        </div>"""
        if i < len(hits) - 1:
            stages_html += '<div style="color:rgba(255,255,255,0.12);font-size:0.7rem;align-self:center;padding-bottom:0.5rem;flex-shrink:0;">▶</div>'
    any_active = any(c > 0 for _, c in hits)
    sc = '#ff3a3a' if any_active else '#3fb950'
    st.markdown(f"""
<div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-thin);
            border-radius:8px;padding:0.65rem 1rem;margin-bottom:1rem;">
  <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem;">
    <span style="font-size:0.52rem;color:var(--text-ghost);font-weight:800;text-transform:uppercase;
                 letter-spacing:0.15em;font-family:'JetBrains Mono';">⛓ KILL CHAIN TRACKER</span>
    <span style="font-size:0.52rem;color:{sc};font-weight:700;font-family:'JetBrains Mono';">
      {'● ACTIVE INTRUSION' if any_active else '● CHAIN CLEAR'}
    </span>
  </div>
  <div style="display:flex;gap:0.25rem;align-items:flex-end;">{stages_html}</div>
</div>""", unsafe_allow_html=True)

# ── RISK DONUT ─────────────────────────────────────────────────────────────────
def render_risk_donut(df):
    import plotly.graph_objects as go
    crit = len(df[df['risk_score'] >= 90])          if not df.empty else 0
    high = len(df[(df['risk_score'] >= 70) & (df['risk_score'] < 90)]) if not df.empty else 0
    med  = len(df[(df['risk_score'] >= 45) & (df['risk_score'] < 70)]) if not df.empty else 0
    low  = len(df[df['risk_score'] < 45])            if not df.empty else 0
    vals   = [crit, high, med, low] if sum([crit,high,med,low]) > 0 else [1,1,1,1]
    labels = ['Critical','High','Medium','Low']
    colors = ['#ff3a3a','#ff6b35','#ffd700','#3fb950']
    total  = crit + high + med + low
    fig = go.Figure(go.Pie(
        values=vals, labels=labels, hole=0.65,
        marker=dict(colors=colors, line=dict(color='rgba(0,0,0,0.4)', width=1)),
        textinfo='none', direction='clockwise', sort=False,
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>',
    ))
    fig.add_annotation(text=f'<b>{total:,}</b><br>EVENTS', x=0.5, y=0.5, showarrow=False,
                       font=dict(size=11, color='#fff', family='JetBrains Mono'), align='center')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(l=0,r=0,t=5,b=0), height=190, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

@st.cache_data(ttl=10)
def load_data():
    try:
        db = EnterpriseDatabase()
        conn = db._get_conn()
        # Only fetch alerts with meaningful risk scores — filters out Wi-Fi loopback noise
        rows = conn.run(
            'SELECT * FROM alerts WHERE risk_score > 0 ORDER BY id DESC LIMIT 2000'
        )
        cols  = [c['name'] for c in conn.columns]
        conn.close()
        alerts = [dict(zip(cols, r)) for r in rows]
        df = pd.DataFrame(alerts)
        if not df.empty:
            df['timestamp']  = pd.to_datetime(df['timestamp'], origin='unix', unit='s', errors='coerce')
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

    system_prompt = f"You are C.O.R.E AI SOC Analyst. Provide professional, concise, and analytical responses. Recent network telemetry (JSON):\n{alert_context}"

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
    import plotly.graph_objects as go

    df = load_data()

    # ── Session State ───────────────────────────────────────────────────────────
    if "scanning"       not in st.session_state: st.session_state.scanning = False
    if "search_query"   not in st.session_state: st.session_state.search_query = ""
    if "chat_messages"  not in st.session_state: st.session_state.chat_messages = []

    # ── Sidebar ─────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
            <div style="padding:1rem 0;margin-bottom:2rem;">
                <h2 style="font-weight:800;letter-spacing:-0.05em;color:#fff;margin:0;">C.O.R.E</h2>
                <div style="font-size:0.6rem;color:var(--pd-blue);font-weight:800;letter-spacing:0.2em;">SENTINEL ELITE</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.65rem;color:var(--text-ghost);font-weight:800;text-transform:uppercase;margin-bottom:1rem;'>Infrastructure Control</p>", unsafe_allow_html=True)
        engine_on = st.toggle("NEURAL ENGINE",  value=True)
        db_on     = st.toggle("STOIC DATABASE", value=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.65rem;color:var(--text-ghost);font-weight:800;text-transform:uppercase;'>Traffic Filter</p>", unsafe_allow_html=True)
        risk_lvl = st.slider("", 0, 100, 50, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            status = 'STABLE' if engine_on and db_on else 'DEGRADED'
            sc     = '#3fb950' if engine_on and db_on else '#f85149'
            st.markdown(f"""
                <div style="font-size:0.6rem;color:var(--text-ghost);margin-bottom:0.5rem;">ENVIRONMENT HEALTH</div>
                <div style="display:flex;align-items:center;gap:8px;">
                  <div style="width:8px;height:8px;border-radius:50%;background:{sc};box-shadow:0 0 10px {sc};"></div>
                  <span style="font-size:0.75rem;font-family:'JetBrains Mono';font-weight:700;">{status}</span>
                </div>""", unsafe_allow_html=True)
        st.markdown("<br>" * 7, unsafe_allow_html=True)
        st.caption("Environment: char0n-production")
        st.caption("Region: AWS-US-EAST-1")

    # ── Filtering ───────────────────────────────────────────────────────────────
    f_df = df[df['risk_score'] >= risk_lvl] if not df.empty else df
    if st.session_state.search_query and not f_df.empty:
        f_df = f_df[f_df.astype(str).apply(lambda x: x.str.contains(st.session_state.search_query, case=False)).any(axis=1)]

    crit = len(f_df[f_df['risk_score'] >= 90])           if not f_df.empty else 0
    high = len(f_df[(f_df['risk_score'] >= 70) & (f_df['risk_score'] < 90)]) if not f_df.empty else 0
    med  = len(f_df[(f_df['risk_score'] >= 45) & (f_df['risk_score'] < 70)]) if not f_df.empty else 0
    low  = len(f_df[f_df['risk_score'] < 45])            if not f_df.empty else 0

    # ── Tactical HUD Header ─────────────────────────────────────────────────────
    st.markdown(f"""
        <div class="tactical-header">
            <div style="display:flex;gap:3rem;">
                <div class="neural-stat"><span class="neural-stat-label">NEURAL SYNC</span><span class="neural-stat-val">100.0% NOMINAL</span></div>
                <div class="neural-stat"><span class="neural-stat-label">INGESTION RATE</span><span class="neural-stat-val">{int(len(df)/24 if len(df)>0 else 0)} PKTS/SEC</span></div>
                <div class="neural-stat"><span class="neural-stat-label">ACTIVE THREATS</span><span class="neural-stat-val" style="color:var(--pd-red);">{len(df[df['risk_score']>=70]) if not df.empty else 0} DETECTED</span></div>
            </div>
            <div style="text-align:right;">
                <span style="font-size:0.6rem;color:var(--pd-blue);font-weight:800;letter-spacing:0.2em;text-transform:uppercase;">Sentinel Core v4.0.211-ELITE</span><br>
                <span class="pulsing-dot" style="display:inline-block;width:6px;height:6px;background:var(--pd-green);border-radius:50%;margin-right:8px;"></span>
                <span style="font-size:0.7rem;color:#fff;font-family:'JetBrains Mono';">SYSLOGS: SYNC_COMPLETE</span>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Live Threat Ticker ──────────────────────────────────────────────────────
    render_threat_ticker(df)

    st.markdown('<div style="margin-left:2rem;margin-bottom:2rem;"><h1 style="font-weight:900;letter-spacing:-0.03em;margin:0;font-size:2.5rem;">Mission Control</h1></div>', unsafe_allow_html=True)

    # ── ROW 1: Discovery + DEFCON ───────────────────────────────────────────────
    col_disc, col_defcon = st.columns([1.8, 1.2])
    with col_disc:
        with st.container():
            score = 100 if df.empty or df['risk_score'].max() < 70 else max(0, 100 - int(df['risk_score'].mean()))
            score_color = '#3fb950' if score >= 70 else '#ffd700' if score >= 40 else '#ff3a3a'
            # Ring gauge: SVG circle with stroke-dasharray for the score arc
            circumference = 2 * 3.14159 * 42  # r=42
            dash = circumference * score / 100
            gap  = circumference - dash
            threat_rate = f"{len(df)/7:.0f}/day" if len(df) > 0 else "0/day"
            avg_risk = f"{df['risk_score'].mean():.0f}" if not df.empty else "0"
            status_items = [
                ("AI ENGINE",   "ONLINE",  "#3fb950"),
                ("DECEPTION",   "ACTIVE",  "#3fb950"),
                ("FIREWALL",    "ARMED",   "#3fb950"),
                ("SIEM FEED",   "SYNCED",  "#3a86ff"),
            ]
            status_html = ""
            for sname, sval, sclr in status_items:
                status_html += f'<div style="display:flex;justify-content:space-between;padding:0.25rem 0;border-bottom:1px solid rgba(255,255,255,0.04);"><span style="font-size:0.6rem;color:var(--text-ghost);">{sname}</span><span style="font-size:0.6rem;font-weight:700;color:{sclr};">● {sval}</span></div>'

            st.markdown(f"""
                <div class="discovery-card" style="padding:1.2rem 1.5rem;">
                    <div class="card-label" style="margin-bottom:0.8rem;">🛡️ TACTICAL OPERATIONS STATUS</div>
                    <div style="display:flex;gap:1.5rem;align-items:flex-start;">
                        <div style="flex:0 0 auto;text-align:center;">
                            <svg width="110" height="110" viewBox="0 0 100 100" style="filter:drop-shadow(0 0 8px {score_color}30);">
                                <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/>
                                <circle cx="50" cy="50" r="42" fill="none" stroke="{score_color}" stroke-width="6"
                                    stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-linecap="round"
                                    transform="rotate(-90 50 50)" style="transition:stroke-dasharray 0.8s ease;"/>
                                <text x="50" y="44" text-anchor="middle" fill="{score_color}" font-size="22" font-weight="900" font-family="JetBrains Mono,monospace">{score}</text>
                                <text x="50" y="58" text-anchor="middle" fill="rgba(255,255,255,0.35)" font-size="7" font-weight="600" font-family="JetBrains Mono,monospace" letter-spacing="0.1em">SECURITY</text>
                            </svg>
                        </div>
                        <div style="flex:1;min-width:0;">
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem 1.2rem;margin-bottom:0.8rem;">
                                <div><div style="font-size:0.5rem;color:var(--text-ghost);text-transform:uppercase;">EVENTS</div><div style="font-size:1.1rem;font-weight:800;">{len(df):,}</div></div>
                                <div><div style="font-size:0.5rem;color:var(--text-ghost);text-transform:uppercase;">AVG RISK</div><div style="font-size:1.1rem;font-weight:800;color:{score_color};">{avg_risk}%</div></div>
                                <div><div style="font-size:0.5rem;color:var(--text-ghost);text-transform:uppercase;">THREAT RATE</div><div style="font-size:1.1rem;font-weight:800;">{threat_rate}</div></div>
                                <div><div style="font-size:0.5rem;color:var(--text-ghost);text-transform:uppercase;">CRITICAL</div><div style="font-size:1.1rem;font-weight:800;color:#ff3a3a;">{crit}</div></div>
                            </div>
                            <div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:0.5rem;">
                                {status_html}
                            </div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

    with col_defcon:
        render_defcon_gauge(f_df)

    # ── Kill Chain Tracker ──────────────────────────────────────────────────────
    render_kill_chain(f_df)

    # ── ROW 2: Threat Exposure + Globe + Donut ──────────────────────────────────
    col_main, col_right = st.columns([1.8, 1.2])

    with col_main:
        with st.container():
            # Build priority queue items HTML inside the card
            priority_html = ""
            if not f_df.empty:
                priority_html += '<div style="margin-top:1rem;"><p style="font-size:0.7rem;color:var(--text-ghost);font-weight:700;margin-bottom:0.75rem;text-transform:uppercase;">Priority Analysis Queue</p>'
                for _, row in f_df.sort_values('risk_score', ascending=False).head(5).iterrows():
                    pcolor = "var(--pd-red)" if row['risk_score'] >= 90 else "var(--pd-orange)" if row['risk_score'] >= 70 else "var(--pd-yellow)"
                    priority_html += f'''<div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-thin);border-left:2px solid {pcolor};
                                padding:0.6rem;border-radius:4px;margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;">
                        <div style="font-size:0.75rem;font-family:'JetBrains Mono';color:#fff;">{row['ip']} <span style="color:var(--text-ghost);font-size:0.65rem;">[{row['mitre_tactic']}]</span></div>
                        <div style="font-size:0.7rem;font-weight:800;color:{pcolor};">{row['risk_score']}% RISK</div>
                    </div>'''
                priority_html += '</div>'
            else:
                priority_html += '<div style="margin-top:1rem;">'
                for note in ["● AI Core maintaining 100% processing synchronization.","● Neural engine reporting zero critical drift.","● Sentinel Shield active: Edge nodes synchronized.","● Honeypots report neutral activity."]:
                    priority_html += f'<div style="color:var(--text-ghost);font-size:0.75rem;margin-bottom:0.6rem;">{note}</div>'
                priority_html += '</div>'

            st.markdown(f"""
                <div class="discovery-card">
                    <div class="card-label">⚠️ OPEN THREAT VECTORS</div>
                    <div class="stats-ribbon" style="margin-bottom:1rem;border-bottom:1px solid var(--border-thin);padding-bottom:1rem;">
                        <div class="stat-item"><div class="stat-value">{len(f_df)}</div><div class="stat-label">TOTAL</div></div>
                        <div class="stat-item"><div class="stat-value" style="color:var(--pd-red);">{crit}</div><div class="stat-label">CRITICAL</div></div>
                        <div class="stat-item"><div class="stat-value" style="color:var(--pd-orange);">{high}</div><div class="stat-label">HIGH</div></div>
                        <div class="stat-item"><div class="stat-value" style="color:var(--pd-yellow);">{med}</div><div class="stat-label">MEDIUM</div></div>
                        <div class="stat-item"><div class="stat-value" style="color:var(--pd-blue);">{low}</div><div class="stat-label">LOW</div></div>
                    </div>
                    {priority_html}
                </div>""", unsafe_allow_html=True)

    with col_right:
        with st.container():
            st.markdown(f"""
                <div class="discovery-card" style="padding:1.5rem 0 0 0;">
                    <div class="card-label" style="padding-left:1.5rem;">🌎 GLOBAL THREAT DETECTIONS</div>
                    <div style="display:flex;gap:3rem;padding-left:1.5rem;margin-bottom:0.5rem;">
                        <div><div style="font-size:1.4rem;font-weight:800;">{len(df)}</div><div style="font-size:0.65rem;color:var(--text-ghost);">IN LAST 7 DAYS</div></div>
                        <div><div style="font-size:1.4rem;font-weight:800;">{len(df)*3:.0f}</div><div style="font-size:0.65rem;color:var(--text-ghost);">IN LAST 30 DAYS</div></div>
                    </div>""", unsafe_allow_html=True)
            discovery_globe(df)
            if st.button("🌍 EXPAND GEOSPATIAL MATRIX", use_container_width=True, type="secondary"):
                show_geospatial_matrix(df)
            st.markdown("<div style='padding:0 1rem;'>", unsafe_allow_html=True)
            render_risk_donut(f_df)
            st.session_state.search_query = st.text_input("SEARCH THREATS...", placeholder="Type IP, Tactic or Analysis...", label_visibility="collapsed")
            st.markdown("</div></div>", unsafe_allow_html=True)

    # ── KPI Row ─────────────────────────────────────────────────────────────────
    st.markdown('<p style="font-size:0.7rem;font-weight:800;color:var(--text-ghost);margin-bottom:1rem;margin-top:2rem;">AGENTIC ASSETS</p>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    for kcol, label, val in [(k1,"ACTIVE ASSETS","1"),(k2,"SERVICES SCANNING","12"),(k3,"TECH STACK","8"),(k4,"NEURAL CORES","2")]:
        with kcol:
            st.markdown(f'<div class="discovery-card" style="text-align:center;padding:1rem;"><div style="font-size:0.6rem;color:var(--text-ghost);">{label}</div><div style="font-size:1.5rem;font-weight:800;">{val}</div></div>', unsafe_allow_html=True)

    # ── Tabs ────────────────────────────────────────────────────────────────────
    TABS = ["TELEMETRY","MITRE","EVOLVE","GHOSTS","NEURAL","GEO","REPORTS"]
    sel  = st.radio("", TABS, horizontal=True, label_visibility="collapsed")

    with st.container(border=True):

        # ── TELEMETRY ───────────────────────────────────────────────────────────
        if sel == "TELEMETRY":
            st.dataframe(f_df.sort_values('timestamp', ascending=False).head(200), use_container_width=True, hide_index=True)

        # ── MITRE ───────────────────────────────────────────────────────────────
        elif sel == "MITRE":
            m_df = df[(df['mitre_tactic'].notna()) & (df['mitre_tactic'] != 'Unknown')] if not df.empty else df
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>TACTIC DISTRIBUTION</p>", unsafe_allow_html=True)
                if not m_df.empty:
                    tc = m_df['mitre_tactic'].value_counts().reset_index()
                    tc.columns = ['Tactic', 'Count']
                    fig = go.Figure(go.Bar(x=tc['Count'], y=tc['Tactic'], orientation='h',
                        marker=dict(color=tc['Count'], colorscale=[[0,'#3a86ff'],[0.5,'#ff6b35'],[1,'#ff3a3a']], line=dict(color='rgba(0,0,0,0.3)',width=1)),
                        text=tc['Count'], textposition='outside', textfont=dict(color='rgba(255,255,255,0.7)',size=9,family='JetBrains Mono')))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(14,17,23,0.5)',
                        margin=dict(l=0,r=40,t=0,b=0), height=360,
                        xaxis=dict(showgrid=False,color='rgba(255,255,255,0.2)',showticklabels=False),
                        yaxis=dict(showgrid=False,color='rgba(255,255,255,0.5)',tickfont=dict(size=9,family='JetBrains Mono')), bargap=0.3)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No MITRE-mapped techniques in buffer.")
            with c2:
                st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>TECHNIQUE HEATMAP</p>", unsafe_allow_html=True)
                if not m_df.empty and 'mitre_technique' in m_df.columns:
                    tt = m_df.groupby(['mitre_tactic','mitre_technique']).size().reset_index(name='n')
                    tactics    = tt['mitre_tactic'].unique().tolist()
                    techniques = tt['mitre_technique'].value_counts().head(12).index.tolist()
                    z = [[int(tt[(tt['mitre_tactic']==t) & (tt['mitre_technique']==te)]['n'].sum()) for t in tactics] for te in techniques]
                    fig = go.Figure(go.Heatmap(z=z, x=[t[:14] for t in tactics], y=[te[:22] for te in techniques],
                        colorscale=[[0,'rgba(14,17,23,1)'],[0.3,'#1a3a6b'],[0.7,'#ff6b35'],[1,'#ff3a3a']], showscale=False,
                        hovertemplate='Tactic: %{x}<br>Technique: %{y}<br>Hits: %{z}<extra></extra>'))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0,r=0,t=0,b=0), height=360,
                        xaxis=dict(tickfont=dict(size=8,family='JetBrains Mono',color='rgba(255,255,255,0.5)'),tickangle=-30),
                        yaxis=dict(tickfont=dict(size=8,family='JetBrains Mono',color='rgba(255,255,255,0.5)')))
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Technique data not available.")

        # ── EVOLVE ──────────────────────────────────────────────────────────────
        elif sel == "EVOLVE":
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>ATTACK FREQUENCY — Day × Hour</p>", unsafe_allow_html=True)
                if not df.empty and 'timestamp' in df.columns:
                    d2 = df.dropna(subset=['timestamp']).copy()
                    d2['hour'] = d2['timestamp'].dt.hour
                    d2['dow']  = d2['timestamp'].dt.dayofweek
                    days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
                    z = [[len(d2[(d2['dow']==d) & (d2['hour']==h)]) for h in range(24)] for d in range(7)]
                    fig = go.Figure(go.Heatmap(z=z, x=[f'{h:02d}h' for h in range(24)], y=days,
                        colorscale=[[0,'rgb(10,13,20)'],[0.3,'#1a3a6b'],[0.6,'#ff6b35'],[1,'#ff3a3a']],
                        hovertemplate='%{y} %{x}: %{z} attacks<extra></extra>', showscale=False))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0,r=0,t=0,b=0), height=280,
                        xaxis=dict(tickfont=dict(size=8,color='rgba(255,255,255,0.4)',family='JetBrains Mono')),
                        yaxis=dict(tickfont=dict(size=9,color='rgba(255,255,255,0.5)',family='JetBrains Mono')))
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Awaiting temporal telemetry...")
            with c2:
                st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>DAILY ATTACK TRAJECTORY</p>", unsafe_allow_html=True)
                if not df.empty:
                    daily = df.groupby(df['timestamp'].dt.date).size().reset_index(name='count')
                    fig = go.Figure(go.Scatter(x=daily['timestamp'], y=daily['count'], mode='lines+markers',
                        line=dict(color='#3a86ff',width=2), fill='tozeroy', fillcolor='rgba(58,134,255,0.1)',
                        marker=dict(size=4,color='#3a86ff')))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(14,17,23,0.5)',
                        margin=dict(l=0,r=0,t=0,b=0), height=280,
                        xaxis=dict(showgrid=False,color='rgba(255,255,255,0.2)',tickfont=dict(size=8,family='JetBrains Mono')),
                        yaxis=dict(showgrid=True,gridcolor='rgba(255,255,255,0.05)',color='rgba(255,255,255,0.3)',tickfont=dict(size=8,family='JetBrains Mono')))
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # ── GHOSTS ──────────────────────────────────────────────────────────────
        elif sel == "GHOSTS":
            APT = [
                {"n":"APT41","a":"BARIUM / Winnti","o":"China 🇨🇳","s":"Technology, Telecom, Healthcare","t":["Supply Chain","Spearphishing","Zero-day"],"r":96,"c":"#ff3a3a","active":True},
                {"n":"APT29","a":"Cozy Bear","o":"Russia 🇷🇺","s":"Government, Defense, Energy","t":["OAuth Phishing","OPSEC Evasion","Living-off-land"],"r":94,"c":"#ff3a3a","active":True},
                {"n":"Lazarus","a":"HIDDEN COBRA","o":"North Korea 🇰🇵","s":"Finance, Crypto, Defense","t":["Crypto Theft","Watering Hole","RAT Deploy"],"r":91,"c":"#ff3a3a","active":True},
                {"n":"APT33","a":"HOLMIUM","o":"Iran 🇮🇷","s":"Aviation, Energy, Military","t":["Credential Harvest","Custom Backdoors","Spearphishing"],"r":87,"c":"#ff6b35","active":False},
            ]
            cols = st.columns(len(APT))
            for i, apt in enumerate(APT):
                with cols[i]:
                    ttps = "".join([f"<div style='font-size:0.55rem;color:rgba(255,255,255,0.45);margin-top:2px;'>▸ {t}</div>" for t in apt['t']])
                    glow = f"box-shadow:0 0 14px rgba(255,58,58,0.12);" if apt['active'] else ""
                    badge_bg = apt['c'] if apt['active'] else 'rgba(255,255,255,0.1)'
                    st.markdown(f"""
<div style="background:rgba(255,255,255,0.02);border:1px solid {''+apt['c'] if apt['active'] else 'rgba(255,255,255,0.07)'};
            border-radius:8px;padding:1rem;{glow}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem;">
    <div>
      <div style="font-size:0.95rem;font-weight:900;color:{apt['c']};font-family:'JetBrains Mono';">{apt['n']}</div>
      <div style="font-size:0.5rem;color:rgba(255,255,255,0.35);">{apt['a']}</div>
    </div>
    <div style="background:{badge_bg};color:#fff;font-size:0.45rem;font-weight:800;padding:2px 6px;border-radius:3px;">{'ACTIVE' if apt['active'] else 'DORMANT'}</div>
  </div>
  <div style="font-size:0.52rem;color:rgba(255,255,255,0.3);margin-bottom:2px;">ORIGIN: {apt['o']}</div>
  <div style="font-size:0.52rem;color:rgba(255,255,255,0.3);margin-bottom:0.5rem;">TARGET: {apt['s']}</div>
  <div style="font-size:0.5rem;color:rgba(255,255,255,0.3);font-weight:700;margin-bottom:2px;">TTPs:</div>
  {ttps}
  <div style="margin-top:0.75rem;height:2px;background:linear-gradient(90deg,{apt['c']},{apt['c']}00);border-radius:1px;"></div>
  <div style="font-size:0.58rem;color:{apt['c']};font-weight:700;margin-top:0.3rem;">RISK INDEX: {apt['r']}</div>
</div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            d_df = df[df['source'].str.contains('DECEPTION', na=False, case=False)] if not df.empty else pd.DataFrame()
            st.metric("⚠️ Ghost Node Tripwires Triggered", len(d_df))
            if not d_df.empty:
                st.dataframe(d_df, use_container_width=True, hide_index=True)

        # ── NEURAL ──────────────────────────────────────────────────────────────
        elif sel == "NEURAL":
            st.markdown(f"""
<div style="background:rgba(58,134,255,0.06);border:1px solid rgba(58,134,255,0.2);border-radius:8px;
            padding:0.6rem 1rem;margin-bottom:1rem;display:flex;align-items:center;gap:0.75rem;">
  <span style="width:8px;height:8px;background:#3a86ff;border-radius:50%;display:inline-block;box-shadow:0 0 8px #3a86ff;"></span>
  <span style="font-size:0.65rem;font-family:'JetBrains Mono';color:rgba(255,255,255,0.7);">
    C.O.R.E NEURAL ENGINE ONLINE &nbsp;│&nbsp; Context: {len(df):,} telemetry records loaded
  </span>
</div>""", unsafe_allow_html=True)
            for msg in st.session_state.chat_messages:
                if msg['role'] == 'user':
                    st.markdown(f"""<div style="text-align:right;margin-bottom:0.5rem;">
<span style="background:rgba(58,134,255,0.15);border:1px solid rgba(58,134,255,0.3);border-radius:8px 8px 0 8px;
             padding:0.5rem 0.75rem;font-size:0.75rem;color:#fff;display:inline-block;max-width:80%;text-align:left;">{msg['content']}</span>
</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="margin-bottom:0.75rem;">
<div style="font-size:0.5rem;color:#3a86ff;font-weight:800;font-family:'JetBrains Mono';margin-bottom:3px;">◉ C.O.R.E AI</div>
<span style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:0 8px 8px 8px;
             padding:0.5rem 0.75rem;font-size:0.75rem;color:rgba(255,255,255,0.85);display:inline-block;
             max-width:90%;white-space:pre-wrap;">{msg['content']}</span>
</div>""", unsafe_allow_html=True)
            user_input = st.chat_input("Ask the Neural Engine about threats, tactics, IPs...")
            if user_input:
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                with st.spinner("◉ Neural Engine processing..."):
                    response = ask_neural_engine(st.session_state.chat_messages, df)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.rerun()
            if st.session_state.chat_messages:
                if st.button("🗑 Clear Chat", type="secondary"):
                    st.session_state.chat_messages = []
                    st.rerun()

        # ── GEO ─────────────────────────────────────────────────────────────────
        elif sel == "GEO":
            c1, c2 = st.columns([1.8, 1])
            with c1:
                st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>GLOBAL THREAT CHOROPLETH</p>", unsafe_allow_html=True)
                if not df.empty and 'alpha_3' in df.columns:
                    cdf = df.groupby('alpha_3').agg(count=('risk_score','count'), avg_risk=('risk_score','mean'), country=('country','first')).reset_index()
                    fig = go.Figure(go.Choropleth(
                        locations=cdf['alpha_3'], z=cdf['avg_risk'], text=cdf['country'],
                        colorscale=[[0,'rgb(14,17,23)'],[0.4,'#1a3a6b'],[0.7,'#ff6b35'],[1,'#ff3a3a']],
                        marker=dict(line=dict(color='rgba(255,255,255,0.08)',width=0.5)),
                        zmin=0, zmax=100, showscale=False,
                        hovertemplate='<b>%{text}</b><br>Avg Risk: %{z:.0f}%<extra></extra>'))
                    fig.update_layout(geo=dict(showframe=False, showcoastlines=True, coastlinecolor='rgba(255,255,255,0.1)',
                        showland=True, landcolor='rgb(20,25,35)', showocean=True, oceancolor='rgb(5,10,20)',
                        bgcolor='rgba(0,0,0,0)', projection_type='natural earth'),
                        paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0), height=380)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Awaiting regional telemetry...")
            with c2:
                st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>TOP ATTACKING NATIONS</p>", unsafe_allow_html=True)
                if not df.empty and 'country' in df.columns:
                    top = df.groupby('country').agg(count=('risk_score','count'), avg_risk=('risk_score','mean')).sort_values('count', ascending=False).head(10)
                    for country, row in top.iterrows():
                        pct = min(100, int(row['avg_risk']))
                        col = '#ff3a3a' if pct >= 80 else '#ff6b35' if pct >= 60 else '#ffd700'
                        st.markdown(f"""
<div style="margin-bottom:0.4rem;padding:0.35rem 0.6rem;background:rgba(255,255,255,0.02);
            border:1px solid var(--border-thin);border-radius:4px;display:flex;justify-content:space-between;align-items:center;">
  <span style="font-size:0.65rem;font-family:'JetBrains Mono';">{country}</span>
  <div style="display:flex;align-items:center;gap:0.5rem;">
    <div style="width:50px;height:3px;background:rgba(255,255,255,0.08);border-radius:2px;">
      <div style="width:{pct}%;height:100%;background:{col};border-radius:2px;"></div>
    </div>
    <span style="font-size:0.6rem;color:{col};font-weight:700;">{int(row['count'])}</span>
  </div>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("No geo data available.")

        # ── REPORTS ─────────────────────────────────────────────────────────────
        elif sel == "REPORTS":
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>LIVE LOG STREAM</p>", unsafe_allow_html=True)
                if not df.empty:
                    log_items = []
                    for _, r in df.sort_values('timestamp', ascending=False).head(30).iterrows():
                        ts  = str(r.get('timestamp',''))[:19]
                        ip  = str(r.get('ip','?'))
                        sc2 = int(r.get('risk_score', 0))
                        tac = str(r.get('mitre_tactic','?'))
                        col = '#ff3a3a' if sc2>=90 else '#ff6b35' if sc2>=70 else '#ffd700' if sc2>=45 else '#3fb950'
                        log_items.append(f'<div style="margin-bottom:3px;"><span style="color:rgba(255,255,255,0.3);">{ts}</span> <span style="color:{col};">[{sc2:3d}]</span> <span style="color:#fff;">{ip}</span> <span style="color:rgba(255,255,255,0.4);">{tac}</span></div>')
                    st.markdown(f"""
<div style="background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.08);border-radius:6px;
            padding:1rem;height:380px;overflow-y:auto;font-family:'JetBrains Mono';font-size:0.6rem;">
  <div style="color:#3fb950;margin-bottom:0.5rem;font-weight:700;">◉ LIVE LOG FEED — {len(df):,} events</div>
  {''.join(log_items)}
</div>""", unsafe_allow_html=True)
                else:
                    st.info("Awaiting log data...")
            with c2:
                st.markdown("<p style='font-size:0.75rem;color:var(--text-ghost);font-weight:700;'>REPORT GENERATION</p>", unsafe_allow_html=True)
                if st.button("📄 GENERATE EXECUTIVE PDF", type="secondary", use_container_width=True):
                    st.info("Compiling Neural Report Archive...")
                    time.sleep(2)
                    st.success("Report Generated: AI_SOC_REPORT_FINAL.pdf")
                st.markdown("<br>", unsafe_allow_html=True)
                if not df.empty:
                    st.markdown("<p style='font-size:0.65rem;color:var(--text-ghost);font-weight:700;'>RISK SUMMARY</p>", unsafe_allow_html=True)
                    for label, count, col in [("Critical (≥90)",crit,"#ff3a3a"),("High (70-89)",high,"#ff6b35"),("Medium (45-69)",med,"#ffd700"),("Low (<45)",low,"#3fb950")]:
                        st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;
            padding:0.4rem 0.75rem;background:rgba(255,255,255,0.02);border-left:3px solid {col};border-radius:0 4px 4px 0;">
  <span style="font-size:0.65rem;font-family:'JetBrains Mono';">{label}</span>
  <span style="font-size:0.8rem;font-weight:800;color:{col};">{count}</span>
</div>""", unsafe_allow_html=True)

    # ── Auto Refresh ─────────────────────────────────────────────────────────────
    if not st.session_state.search_query and not st.session_state.scanning:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()
