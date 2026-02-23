import sqlite3
import pandas as pd
from fpdf import FPDF
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "soc_agent.db")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

class PDFReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        # Assuming you have an internet connection or we simply don't use image if it fails
        self.cell(0, 10, 'C.O.R.E. AI SOC - Executive Threat Report', border=False, align='C')
        self.ln(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_daily_report():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    out_path = os.path.join(REPORTS_DIR, f"threat_report_{date_str}.pdf")
    

    try:
        from core.database_enterprise import EnterpriseDatabase
        db = EnterpriseDatabase()
        alerts = db.get_recent_alerts(limit=1000)
        df = pd.DataFrame(alerts)
        
        total_alerts = len(df)
        
        # ensure risk_score is numeric
        df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce').fillna(0)
        critical = len(df[df['risk_score'] >= 90]) if not df.empty else 0
        
        # Tactics
        if not df.empty and 'mitre_tactic' in df.columns:
            tactics = df[(df['mitre_tactic'] != 'Unknown') & (df['mitre_tactic'].notna())]['mitre_tactic'].value_counts().to_dict()
        else:
            tactics = {}
            
        pdf = PDFReport()
        pdf.add_page()
        
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(w=0, h=10, text=f"Report Generated: {date_str}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(w=0, h=10, text="Executive Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('helvetica', '', 12)
        summary_txt = f"Over the recent monitoring period, the C.O.R.E. AI Engine has processed system telemetries and logs. A total of {total_alerts} security events were recorded, out of which {critical} were classified as CRITICAL threats requiring immediate attention."
        pdf.write(6, text=summary_txt)
        pdf.ln(10)
        
        if tactics:
            pdf.set_font('helvetica', 'B', 14)
            pdf.cell(w=0, h=10, text="MITRE ATT&CK Kill-Chain Breakthrough", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font('helvetica', '', 12)
            for tac, count in tactics.items():
                pdf.cell(w=0, h=8, text=f"- {tac}: {count} mapping(s)", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
        
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(w=0, h=10, text="Top 5 Critical Threats", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('helvetica', '', 10)
        
        if critical > 0:
            crit_df = df[df['risk_score'] >= 90].sort_values(by='risk_score', ascending=False).head(5)
            for _, row in crit_df.iterrows():
                tac = row.get('mitre_tactic', 'N/A')
                pdf.set_font('helvetica', 'B', 10)
                pdf.write(6, text=f"[Risk: {row['risk_score']}] Tactic: {tac}")
                pdf.ln(6)
                pdf.set_font('helvetica', '', 10)
                
                analysis_text = row.get('analysis', 'Unknown').encode('latin-1', 'replace').decode('latin-1')
                pdf.write(6, text=f"> {analysis_text}")
                pdf.ln(8)
        else:
            pdf.cell(w=0, h=10, text="No critical threats detected.", new_x="LMARGIN", new_y="NEXT")
            
        pdf.output(out_path)
        print(f"[*] Generated executive PDF report: {out_path}")
        return out_path
    except Exception as e:
        print(f"[!] Error generating report: {e}")
        return None

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    generate_daily_report()
