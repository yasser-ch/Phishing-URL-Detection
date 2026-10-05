from flask import Flask, jsonify, request
from flask_cors import CORS
from detector import run_scan, analyze_single_url
import json
import glob
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

scheduler = None
SCAN_INTERVAL_MINUTES = int(os.getenv('SCAN_INTERVAL_MINUTES', 60))


def list_reports():
    files = glob.glob(os.path.join(DATA_DIR, 'alert_report_*.json'))
    return sorted(files, key=os.path.getctime, reverse=True)


def get_latest_report():
    reports = list_reports()
    if not reports:
        return None
    with open(reports[0], 'r') as f:
        return json.load(f)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'CMRPI Threat Detection API'})


@app.route('/api/report', methods=['GET'])
def get_report():
    report = get_latest_report()
    if not report:
        return jsonify({'error': 'Aucun rapport disponible'}), 404
    return jsonify(report)


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    report = get_latest_report()
    if not report:
        return jsonify({'error': 'Aucun rapport disponible'}), 404
    return jsonify(report['alerts'])


@app.route('/api/summary', methods=['GET'])
def get_summary():
    report = get_latest_report()
    if not report:
        return jsonify({'error': 'Aucun rapport disponible'}), 404
    return jsonify(report['summary'])


@app.route('/api/scan', methods=['POST'])
def scan():
    limit = request.json.get('limit', 100) if request.is_json else 100
    try:
        report = run_scan(limit=limit)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def history():
    reports = list_reports()
    history_data = []
    for path in reports[:20]:
        with open(path, 'r') as f:
            r = json.load(f)
            history_data.append({
                'report_id': r['report_id'],
                'generated_at': r['generated_at'],
                'source': r['source'],
                'summary': r['summary']
            })
    return jsonify(history_data)

@app.route('/api/report/<report_id>', methods=['GET'])
def get_report_by_id(report_id):
    for path in list_reports():
        with open(path, 'r') as f:
            r = json.load(f)
            if r['report_id'] == report_id:
                return jsonify(r)
    return jsonify({'error': 'Rapport introuvable'}), 404


@app.route('/api/analyze', methods=['POST'])
def analyze():
    if not request.is_json:
        return jsonify({'error': 'JSON requis'}), 400

    url = request.json.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL manquante'}), 400

    try:
        result = analyze_single_url(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def scheduled_scan():
    print(f"[SCHEDULER] Scan automatique déclenché — {datetime.now().isoformat()}")
    try:
        report = run_scan(limit=100)
        print(f"[SCHEDULER] Terminé : {report['summary']['malicious_detected']} menace(s) détectée(s)")
    except Exception as e:
        print(f"[SCHEDULER] Erreur : {e}")


def start_scheduler():
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_scan, 'interval', minutes=SCAN_INTERVAL_MINUTES, id='auto_scan')
    scheduler.start()
    print(f"[SCHEDULER] Actif — scan toutes les {SCAN_INTERVAL_MINUTES} minutes")


def get_scheduler_job():
    return scheduler.get_job('auto_scan') if scheduler else None


@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    job = get_scheduler_job()
    if not job:
        return jsonify({'enabled': False, 'interval_minutes': None, 'next_run': None})

    interval_minutes = int(job.trigger.interval.total_seconds() // 60)
    return jsonify({
        'enabled': job.next_run_time is not None,
        'interval_minutes': interval_minutes,
        'next_run': job.next_run_time.isoformat() if job.next_run_time else None
    })


@app.route('/api/scheduler/config', methods=['POST'])
def scheduler_config():
    data = request.json or {}
    enabled = data.get('enabled', True)
    interval_minutes = data.get('interval_minutes')

    if interval_minutes:
        scheduler.reschedule_job('auto_scan', trigger='interval', minutes=interval_minutes)

    if enabled:
        scheduler.resume_job('auto_scan')
    else:
        scheduler.pause_job('auto_scan')

    job = get_scheduler_job()
    return jsonify({
        'enabled': job.next_run_time is not None,
        'interval_minutes': int(job.trigger.interval.total_seconds() // 60),
        'next_run': job.next_run_time.isoformat() if job.next_run_time else None
    })


if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True, port=5000, use_reloader=False)