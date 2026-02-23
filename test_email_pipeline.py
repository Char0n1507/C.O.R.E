import asyncio
import time
from core.analyzer import Analyzer

async def run_test():
    print("[*] Instantiating C.O.R.E. AI Analyzer in Local (Ollama) mode...")
    
    # Force use_llm to True and provider to ollama
    analyzer = Analyzer(use_llm=True, provider="ollama")
    
    print("\n--------------------------------------------------------------")
    print("[*] TEST 1: INJECTING KNOWN MALICIOUS EMAIL (VirusTotal Check)")
    print("--------------------------------------------------------------")
    
    malicious_email_log = {
        "source": "imap://security@company.com",
        "timestamp": time.time(),
        "type": "email",
        "content": "EMAIL PARSED: Subject: Urgent Payroll Update | From: HR <hr@example.com> | Body: Please update your payroll info immediately at http://185.224.128.84/login.php to avoid missed payments.",
        "email_data": {
            "subject": "Urgent Payroll Update",
            "from": "HR <hr@example.com>",
            "body": "Please update your payroll info immediately at http://185.224.128.84/login.php to avoid missed payments."
        }
    }
    
    result1 = await analyzer.analyze_log(malicious_email_log)
    print(f"\n[AI Evaluation] Risk Score: {result1['risk_score']}")
    print(f"[AI Evaluation] Action: {result1.get('action')}")
    print(f"[AI Evaluation] Analysis: {result1.get('analysis')}")
    
    print("\n--------------------------------------------------------------")
    print("[*] TEST 2: INJECTING SNEAKY SOCIAL ENGINEERING EMAIL (LLM Threat Hunting)")
    print("--------------------------------------------------------------")
    
    sneaky_email_log = {
        "source": "imap://security@company.com",
        "timestamp": time.time(),
        "type": "email",
        "content": "EMAIL PARSED: Subject: Invoice Attached - Please Process | From: John Doe <ceo.personal123@gmail.com> | Body: Hey, I'm stuck out of the office right now without access to my usual laptop. Can you urgently wire $5,000 to the vendor account attached in this invoice? The client needs it by 5 PM or we lose the contract. - John, CEO",
        "email_data": {
            "subject": "Invoice Attached - Please Process",
            "from": "John Doe <ceo.personal123@gmail.com>",
            "body": "Hey, I'm stuck out of the office right now without access to my usual laptop. Can you urgently wire $5,000 to the vendor account attached in this invoice? The client needs it by 5 PM or we lose the contract. - John, CEO"
        }
    }
    
    result2 = await analyzer.analyze_log(sneaky_email_log)
    print(f"\n[AI Evaluation] Risk Score: {result2['risk_score']}")
    print(f"[AI Evaluation] Action: {result2.get('action')}")
    print(f"[AI Evaluation] Analysis: {result2.get('analysis')}")
    
    print("\n--------------------------------------------------------------")
    print("[*] TEST 3: INJECTING BENIGN/CLEAN EMAIL")
    print("--------------------------------------------------------------")
    
    benign_email_log = {
        "source": "imap://security@company.com",
        "timestamp": time.time(),
        "type": "email",
        "content": "EMAIL PARSED: Subject: Lunch tomorrow? | From: Alice TeamLead <alice@company.com> | Body: Hey just a reminder that the team lunch is at 1 PM tomorrow. See you there!",
        "email_data": {
            "subject": "Lunch tomorrow?",
            "from": "Alice TeamLead <alice@company.com>",
            "body": "Hey just a reminder that the team lunch is at 1 PM tomorrow. See you there!"
        }
    }
    
    result3 = await analyzer.analyze_log(benign_email_log)
    print(f"\n[AI Evaluation] Risk Score: {result3['risk_score']}")
    print(f"[AI Evaluation] Action: {result3.get('action')}")
    print(f"[AI Evaluation] Analysis: {result3.get('analysis')}")

if __name__ == "__main__":
    asyncio.run(run_test())
