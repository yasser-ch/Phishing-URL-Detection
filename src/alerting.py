import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def defang(url):
    """Rend une URL non cliquable tout en restant lisible — remplace
    http(s):// par hxxp(s):// et les points par [.] — pratique standard
    en threat intelligence pour éviter tout clic accidentel sur une
    URL malveillante active."""
    defanged = url.replace('http://', 'hxxp://').replace('https://', 'hxxps://')
    defanged = defanged.replace('.', '[.]')
    return defanged


def build_html_body(alerts, source):
    rows = ""
    for a in alerts[:15]:
        rows += f"""
        <tr>
            <td style="padding:10px 14px;border-bottom:1px solid #14293d;color:#8aaabb;font-size:13px;max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:monospace;">{defang(a['url'])}</td>
            <td style="padding:10px 14px;border-bottom:1px solid #14293d;color:#e24b4a;font-weight:bold;font-size:13px;">{a['confidence']}%</td>
            <td style="padding:10px 14px;border-bottom:1px solid #14293d;color:#7c97ac;font-size:12px;">{a.get('status', 'N/A').upper()}</td>
        </tr>"""

    more_note = ""
    if len(alerts) > 15:
        more_note = f"""<p style="color:#4b6478;font-size:12px;margin-top:10px;">... et {len(alerts) - 15} autre(s) alerte(s) dans le rapport complet.</p>"""

    return f"""
    <html>
    <body style="margin:0;padding:0;background:#070d16;font-family:Courier New,monospace;">
        <div style="max-width:640px;margin:0 auto;padding:30px 20px;">

            <div style="display:flex;align-items:center;margin-bottom:6px;">
                <span style="color:#1d9e75;font-size:13px;letter-spacing:2px;">● CMRPI — THREAT MONITOR</span>
            </div>
            <p style="color:#4b6478;font-size:11px;margin:0 0 24px 0;">{datetime.now().strftime('%d/%m/%Y %H:%M')} · Source : {source}</p>

            <div style="background:#170a0c;border:1px solid #4a1818;border-radius:8px;padding:20px;margin-bottom:24px;">
                <p style="color:#e24b4a;font-size:16px;font-weight:bold;margin:0 0 6px 0;letter-spacing:1px;">
                    ⚠ {len(alerts)} MENACE(S) DÉTECTÉE(S)
                </p>
                <p style="color:#c9d8e8;font-size:13px;margin:0;">
                    Des URLs malveillantes ont été identifiées lors du dernier scan.
                </p>
            </div>

            <table style="width:100%;border-collapse:collapse;background:#0b1522;border:1px solid #14293d;border-radius:8px;overflow:hidden;">
                <thead>
                    <tr>
                        <th style="text-align:left;padding:10px 14px;font-size:10px;color:#3d6558;letter-spacing:1px;border-bottom:1px solid #14293d;">URL</th>
                        <th style="text-align:left;padding:10px 14px;font-size:10px;color:#3d6558;letter-spacing:1px;border-bottom:1px solid #14293d;">CONFIANCE</th>
                        <th style="text-align:left;padding:10px 14px;font-size:10px;color:#3d6558;letter-spacing:1px;border-bottom:1px solid #14293d;">STATUT</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            {more_note}

            <p style="color:#3d6558;font-size:11px;margin-top:28px;text-align:center;">
                Système de détection et d'alerte précoce des cybermenaces — CMRPI
            </p>
        </div>
    </body>
    </html>
    """


def send_alert_email(alerts, source="URLhaus"):
    if not alerts:
        return {"sent": False, "reason": "Aucune alerte à envoyer"}

    subject = f"[CMRPI Threat Alert] {len(alerts)} menace(s) détectée(s)"
    html_body = build_html_body(alerts, source)

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_EMAIL
    msg["To"] = ALERT_RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, ALERT_RECIPIENT, msg.as_string())
        server.quit()
        return {"sent": True, "recipient": ALERT_RECIPIENT}
    except Exception as e:
        return {"sent": False, "reason": str(e)}