import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_path="soc_agent.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    source TEXT,
                    risk_score INTEGER,
                    analysis TEXT,
                    action TEXT,
                    raw_content TEXT,
                    country TEXT,
                    city TEXT,
                    lat REAL,
                    lon REAL,
                    alpha_3 TEXT,
                    ip TEXT,
                    mitre_tactic TEXT,
                    mitre_technique TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_alert(self, alert_data):
        """Saves an alert dictionary to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (timestamp, source, risk_score, analysis, action, raw_content, country, city, lat, lon, alpha_3, ip, mitre_tactic, mitre_technique)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_data.get('timestamp'),
                alert_data.get('source'),
                alert_data.get('risk_score'),
                alert_data.get('analysis'),
                alert_data.get('action', 'Monitor'),
                alert_data.get('raw_content'),
                alert_data.get('country'),
                alert_data.get('city'),
                alert_data.get('lat'),
                alert_data.get('lon'),
                alert_data.get('alpha_3'),
                alert_data.get('ip'),
                alert_data.get('mitre_tactic', 'Unknown'),
                alert_data.get('mitre_technique', 'Unknown')
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_alerts(self, limit=50):
        """Fetch recent alerts for the dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM alerts ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self):
        """Get high-level stats."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM alerts')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM alerts WHERE risk_score > 80')
            critical = cursor.fetchone()[0]
            
            return {"total": total, "critical": critical}
