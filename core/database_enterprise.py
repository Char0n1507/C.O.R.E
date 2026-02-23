import psycopg2
import psycopg2.extras
from datetime import datetime

class EnterpriseDatabase:
    def __init__(self, host="localhost", port=5432, dbname="soc_alerts", user="soc_admin", password="super_secret_password"):
        self.conn_params = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password
        }
        self.init_db()

    def _get_conn(self):
        return psycopg2.connect(**self.conn_params)

    def init_db(self):
        """Create tables if they don't exist in PostgreSQL."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
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
        cursor.close()
        conn.close()

    def save_alert(self, alert_data):
        """Saves an alert dictionary to the PostgreSQL database."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alerts (timestamp, source, risk_score, analysis, action, raw_content, country, city, lat, lon, alpha_3, ip, mitre_tactic, mitre_technique)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
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
        row_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return row_id

    def get_recent_alerts(self, limit=50):
        """Fetch recent alerts for the dashboard."""
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM alerts ORDER BY id DESC LIMIT %s', (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return results
