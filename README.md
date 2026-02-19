# 🛡️ C.O.R.E. Enterprise AI SOC Agent

This project is a fully-functional, AI-driven Security Operations Center (SOC) agent designed to automate detection, analysis, and response. It features stateful behavioral analytics (UEBA), interactive graph-based attack visualization, deception technology (honeypots), active firewall response, and Geo-IP Threat mapping.

## 🌟 Key Features Built

1. **Intelligence Engine & Analyzer**: Ingests system logs in real-time. Features a fallback rule-based engine and the ability to integrate Google Gemini Pro for Deep AI Analysis.
2. **UEBA (User & Entity Behavior Analytics)**: A sliding-window stateful memory module that tracks repeated failure patterns (e.g., stopping a slow brute-force attack without alerting on every single typo).
3. **Deception Technology (Active Honeypot)**: Runs a fake FTP server to instantly single out network scanners and attackers with zero false positives.
4. **Autonomous Response**: Integrates directly with Linux `iptables` to actively drop network connections of high-risk IP addresses the moment an attack is confirmed.
5. **Interactive Dashboard & SOAR**: 
    - **Live Feed**: A dark-mode, glowing Streamlit dashboard featuring live KPI metrics.
    - **Kill Chain Graph**: A NetworkX/PyVis interactive drag-and-drop web mapping Attacker IPs ➔ Targeted Users ➔ Triggered ALerts.
    - **Geo-IP Threat Map**: Automatically looks up attacking IP origins and plots them on a global Choropleth map using Plotly.

---

## 🚀 Getting Started

Follow these instructions to clone and run the agent on your own Linux machine.

### 1. Requirements & Setup
Ensure you have Python 3 installed.
```bash
# 1. Clone the repository
git clone <your-repo-link>
cd AI_SOC_Agent

# 2. Create and activate a Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt
```

### 2. Configuration
The project is centralized around a highly configurable `config.yaml` file. 

Feel free to edit `config.yaml` to specify which log files to monitor (e.g., `/var/log/auth.log`) and configure the risk threshold for Autonomous IP Blocking.

**Important**: For the Autonomous Active Response blocking to work, your user needs explicit passwordless `sudo` privileges for the `iptables` append command. To set this up:
1. `sudo visudo -f /etc/sudoers.d/ai_soc_agent`
2. Add this line: `<your_username> ALL=(root) NOPASSWD: /usr/sbin/iptables -A INPUT -s [0-9.]* -j DROP -m comment --comment SOC Agent*`

*(If you skip this, the agent will just print an error that it lacks permissions to block the IP, but the rest of the detection pipeline will still work).*

### 3. Run the complete SOC Environment!

You will need to open **3 separate terminal windows** (ensure your `venv` is activated in all of them!).

**Terminal 1: Start the Core Agent**
```bash
source venv/bin/activate
python main.py
```

**Terminal 2: Start the Streamlit Dashboard UI**
```bash
source venv/bin/activate
streamlit run interface/dashboard.py
```
*Note: Navigate to `http://localhost:8501`. The default operator password is **`admin`**.*

**Terminal 3: Start the Threat Simulator & Honeypot**
*(This will generate fake malicious log entries so you can see the dashboard in action!)*
```bash
source venv/bin/activate

# Start the Honeypot (runs a fake FTP server on port 2121)
python modules/deception/honeypot.py &

# Run the Threat Simulator
python simulator.py
```

## 🛠️ Tech Stack
*   **Backend Engine**: Python (AsyncIO)
*   **Database**: SQLite (Automated table migrations included)
*   **Visualizations**: Streamlit, Plotly, PyVis (NetworkX)
*   **Enrichment**: ip2geotools
*   **Active Response**: Linux iptables
