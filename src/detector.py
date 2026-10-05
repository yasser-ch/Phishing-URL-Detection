import requests
import json
import os
import re
import sys
import joblib
import pandas as pd
from dedup import filter_new_alerts
from datetime import datetime
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from text_features import url_tokenizer  # noqa: F401 — requis pour désérialiser le modèle TF-IDF

from alerting import send_alert_email
from whitelist import is_whitelisted

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'rf_phishing_model_v3.pkl')
TFIDF_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'tfidf_logreg_model.pkl')
DATA_DIR = os.path.join(BASE_DIR, 'data')

_model = None
_tfidf_model = None
_blacklist = None

IP_PATTERN = re.compile(
    r'^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)

SHORTENER_PATTERN = re.compile(
    r'bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|'
    r'yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|'
    r'short\.to|budurl\.com|ping\.fm|post\.ly|just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|'
    r'doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|lnkd\.in|'
    r'db\.tt|qr\.ae|adf\.ly|bitly\.com|cur\.lv|ity\.im|q\.gs|po\.st|bc\.vc|twitthis\.com|'
    r'u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|prettylinkpro\.com|scrnch\.me|'
    r'filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|link\.zip\.net'
)


def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def get_tfidf_model():
    global _tfidf_model
    if _tfidf_model is None:
        _tfidf_model = joblib.load(TFIDF_MODEL_PATH)
    return _tfidf_model


def is_ip_address(domain):
    host = domain.split(':')[0]
    return int(bool(IP_PATTERN.match(host)))


def has_numeric_label(domain):
    host = domain.split(':')[0]
    return int(any(part.isdigit() for part in host.split('.')))


def has_shortener(url):
    return int(bool(SHORTENER_PATTERN.search(url.lower())))


def extract_features_v3(url):
    try:
        if not url.startswith('http'):
            url = 'http://' + url
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path
    except Exception:
        domain = ''
        path = ''

    suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.free.fr', '.xyz', '.top']
    suspicious_words = ['login', 'secure', 'update', 'verify', 'account',
                        'banking', 'paypal', 'amazon', 'apple', 'microsoft']

    return {
        'length': len(url),
        'num_dots': url.count('.'),
        'num_hyphens': url.count('-'),
        'num_slashes': url.count('/'),
        'num_digits': sum(c.isdigit() for c in url),
        'num_at': url.count('@'),
        'num_percent': url.count('%'),
        'num_question': url.count('?'),
        'num_equal': url.count('='),
        'num_underscore': url.count('_'),
        'has_https': int(url.startswith('https')),
        'has_ip': is_ip_address(domain),
        'has_numeric_label': has_numeric_label(domain),
        'domain_length': len(domain),
        'path_length': len(path),
        'has_suspicious_tld': int(any(url.endswith(tld) or tld + '/' in url for tld in suspicious_tlds)),
        'has_suspicious_word': int(any(word in domain.lower() for word in suspicious_words)),
        'num_subdomains': len(domain.split('.')) - 2 if len(domain.split('.')) > 2 else 0,
        'has_at_in_url': int('@' in url),
        'has_shortener': has_shortener(url),
    }


def predict_ensemble(urls):
    """Combine le modèle structurel (Random Forest v3) et le modèle
    textuel (TF-IDF + LogReg) par moyenne des probabilités — 96.91%
    sur le test set, contre 92% et 94.16% pour chaque modèle seul."""
    rf = get_model()
    tfidf = get_tfidf_model()

    features_struct = pd.DataFrame([extract_features_v3(u) for u in urls])
    proba_rf = rf.predict_proba(features_struct)[:, 1]
    proba_tfidf = tfidf.predict_proba(pd.Series(urls))[:, 1]

    ensemble_proba = (proba_rf + proba_tfidf) / 2
    predictions = (ensemble_proba >= 0.5).astype(int)
    confidences = [max(p, 1 - p) * 100 for p in ensemble_proba]

    return predictions, confidences


def fetch_urlhaus_urls(limit=100):
    response = requests.get(
        "https://urlhaus.abuse.ch/downloads/csv_recent/",
        timeout=30
    )

    urls = []
    raw_data = []

    for line in response.text.split('\n'):
        if line.startswith('#') or line.strip() == '':
            continue
        parts = line.split(',')
        if len(parts) >= 3:
            url = parts[2].strip().strip('"')
            if url.startswith('http'):
                urls.append(url)
                raw_data.append({
                    'url': url,
                    'status': parts[3].strip().strip('"') if len(parts) > 3 else 'unknown'
                })
        if len(urls) >= limit:
            break

    return urls, raw_data


def get_blacklist(force_refresh=False):
    global _blacklist

    if _blacklist is not None and not force_refresh:
        return _blacklist

    urls, _ = fetch_urlhaus_urls(limit=10000)
    _blacklist = set(u.rstrip('/') for u in urls)

    return _blacklist


def analyze_urls(urls, raw_data):
    blacklist = get_blacklist()
    predictions, confidences = predict_ensemble(urls)

    results = []
    for i, url in enumerate(urls):
        normalized = url if url.startswith('http') else 'http://' + url
        normalized = normalized.rstrip('/')
        domain = urlparse(normalized).netloc

        whitelisted, wl_reason = is_whitelisted(domain)
        in_blacklist = normalized in blacklist

        ml_verdict = 'MALICIOUS' if predictions[i] == 1 else 'BENIGN'
        ml_confidence = round(confidences[i], 2)

        if in_blacklist:
            final_verdict = 'MALICIOUS'
            final_confidence = 100.0
            detection_method = 'BLACKLIST'
        elif whitelisted:
            final_verdict = 'BENIGN'
            final_confidence = 100.0
            detection_method = 'WHITELIST'
        else:
            final_verdict = ml_verdict
            final_confidence = ml_confidence
            detection_method = 'MACHINE LEARNING'

        results.append({
            'url': url,
            'prediction': final_verdict,
            'confidence': final_confidence,
            'detection_method': detection_method,
            'status': raw_data[i].get('status', 'unknown'),
            'timestamp': datetime.now().isoformat()
        })

    return results


def run_scan(limit=100):
    urls, raw_data = fetch_urlhaus_urls(limit=limit)
    results = analyze_urls(urls, raw_data)

    malicious = [r for r in results if r['prediction'] == 'MALICIOUS']

    is_new_map = filter_new_alerts([m['url'] for m in malicious])
    for m in malicious:
        m['is_new'] = is_new_map.get(m['url'], True)

    new_malicious = [m for m in malicious if m['is_new']]

    report = {
        'report_id': f"CMRPI-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        'generated_at': datetime.now().isoformat(),
        'source': 'URLhaus - Abuse.ch',
        'summary': {
            'total_analyzed': len(results),
            'malicious_detected': len(malicious),
            'new_malicious_detected': len(new_malicious),
            'benign': len(results) - len(malicious),
            'detection_rate': f"{len(malicious) / len(results) * 100:.1f}%" if results else "0%"
        },
        'alerts': malicious
    }

    if new_malicious:
        email_result = send_alert_email(new_malicious, source='URLhaus - Abuse.ch')
        report['email_alert'] = email_result
    else:
        report['email_alert'] = {'sent': False, 'reason': 'Aucune nouvelle menace (déjà notifiées récemment)'}

    filename = f"alert_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

    return report


def analyze_single_url(url):
    url = url.strip()
    if not url:
        return {'error': 'URL vide'}

    normalized = url if url.startswith('http') else 'http://' + url
    normalized = normalized.rstrip('/')

    domain = urlparse(normalized).netloc

    whitelisted, wl_reason = is_whitelisted(domain)

    blacklist = get_blacklist()
    in_blacklist = normalized in blacklist

    predictions, confidences = predict_ensemble([url])
    ml_confidence = round(confidences[0], 2)
    ml_verdict = 'MALICIOUS' if predictions[0] == 1 else 'BENIGN'

    if in_blacklist:
        final_verdict = 'MALICIOUS'
        final_confidence = 100.0
        detection_method = 'BLACKLIST'
        detail = 'URL présente dans la base URLhaus (IOC connu)'
    elif whitelisted:
        final_verdict = 'BENIGN'
        final_confidence = 100.0
        detection_method = 'WHITELIST'
        detail = f'Domaine vérifié — {wl_reason}'
    else:
        final_verdict = ml_verdict
        final_confidence = ml_confidence
        detection_method = 'MACHINE LEARNING'
        if ml_verdict == 'MALICIOUS':
            detail = 'Menace émergente détectée par analyse prédictive (ensemble structurel + textuel)'
        else:
            detail = 'Aucune menace détectée par le modèle'

    return {
        'url': url,
        'domain': domain,
        'verdict': final_verdict,
        'confidence': final_confidence,
        'detection_method': detection_method,
        'detail': detail,
        'blacklist_hit': in_blacklist,
        'whitelist_hit': whitelisted,
        'whitelist_reason': wl_reason,
        'ml_verdict': ml_verdict,
        'ml_confidence': ml_confidence,
        'features': extract_features_v3(url),
        'analyzed_at': datetime.now().isoformat()
    }