from alerting import send_alert_email

fake_alerts = [
    {"url": "http://test-phishing-example.com/login", "confidence": 98.5, "status": "online"},
    {"url": "http://another-fake-site.net/verify", "confidence": 91.2, "status": "offline"},
]

result = send_alert_email(fake_alerts, source="Test manuel")
print(result)