import pg8000.native
from datetime import datetime

class EnterpriseDatabase:
    def __init__(self, host="localhost", port=5433, dbname="soc_alerts", user="soc_admin", password="super_secret_password"):
        self.conn_params = {
            "host": host,
            "port": port,
            "database": dbname,
            "user": user,
            "password": password
        }
        self.init_db()

    def _get_conn(self):
        return pg8000.native.Connection(**self.conn_params)

    def init_db(self):
        """Create tables if they don't exist in PostgreSQL."""
        conn = self._get_conn()
        conn.run('''
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
        conn.close()

    def save_alert(self, alert_data):
        """Saves an alert dictionary to the PostgreSQL database."""
        conn = self._get_conn()
        res = conn.run('''
            INSERT INTO alerts (timestamp, source, risk_score, analysis, action, raw_content, country, city, lat, lon, alpha_3, ip, mitre_tactic, mitre_technique)
            VALUES (:timestamp, :source, :risk_score, :analysis, :action, :raw_content, :country, :city, :lat, :lon, :alpha_3, :ip, :mitre_tactic, :mitre_technique)
            RETURNING id
        ''', 
            timestamp=alert_data.get('timestamp'),
            source=alert_data.get('source'),
            risk_score=alert_data.get('risk_score'),
            analysis=alert_data.get('analysis'),
            action=alert_data.get('action', 'Monitor'),
            raw_content=alert_data.get('raw_content'),
            country=alert_data.get('country'),
            city=alert_data.get('city'),
            lat=alert_data.get('lat'),
            lon=alert_data.get('lon'),
            alpha_3=alert_data.get('alpha_3'),
            ip=alert_data.get('ip'),
            mitre_tactic=alert_data.get('mitre_tactic', 'Unknown'),
            mitre_technique=alert_data.get('mitre_technique', 'Unknown')
        )
        conn.close()
        return res[0][0]

    def get_recent_alerts(self, limit=50):
        """Fetch recent alerts for the dashboard."""
        conn = self._get_conn()
        # pg8000 native run returns a list of lists, and .columns provides column names
        rows = conn.run('SELECT * FROM alerts ORDER BY id DESC LIMIT :limit', limit=limit)
        columns = [col['name'] for col in conn.columns]
        results = [dict(zip(columns, row)) for row in rows]
        conn.close()
        return results

    def get_stats(self):
        """Get high-level stats."""
        conn = self._get_conn()
        total = conn.run('SELECT COUNT(*) FROM alerts')[0][0]
        critical = conn.run('SELECT COUNT(*) FROM alerts WHERE risk_score > 80')[0][0]
        conn.close()
        return {"total": total, "critical": critical}
