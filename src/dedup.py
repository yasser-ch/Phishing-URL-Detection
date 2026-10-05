import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEN_ALERTS_FILE = os.path.join(BASE_DIR, 'data', 'seen_alerts.json')

DEDUP_WINDOW_HOURS = 24


def _load():
    try:
        with open(SEEN_ALERTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data):
    with open(SEEN_ALERTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def filter_new_alerts(urls):
    """Pour chaque URL, détermine si elle est "nouvelle" (jamais vue, ou
    vue il y a plus de DEDUP_WINDOW_HOURS), puis met à jour la mémoire
    persistante avec l'horodatage actuel pour toutes les URLs passées."""
    seen = _load()
    now = datetime.now()
    is_new_map = {}

    for url in urls:
        last_seen_str = seen.get(url)
        if last_seen_str is None:
            is_new_map[url] = True
        else:
            last_seen = datetime.fromisoformat(last_seen_str)
            is_new_map[url] = (now - last_seen) > timedelta(hours=DEDUP_WINDOW_HOURS)
        seen[url] = now.isoformat()

    _save(seen)
    return is_new_map