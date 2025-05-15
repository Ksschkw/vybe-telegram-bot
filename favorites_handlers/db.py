import json
import os
from threading import Lock

LOCK = Lock()
DB_PATH = os.path.join(os.path.dirname(__file__), 'favorites.json')

def _load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def _save_db(data):
    with LOCK:
        with open(DB_PATH, 'w') as f:
            json.dump(data, f, indent=2)

def get_user_favorites(user_id: int):
    db = _load_db()
    return db.get(str(user_id), {"accounts": [], "tokens": []})

def add_favorite(user_id: int, category: str, address: str):
    db = _load_db()
    favs = db.setdefault(str(user_id), {"accounts": [], "tokens": []})
    if address not in favs[category]:
        favs[category].append(address)
        _save_db(db)
    return favs[category]