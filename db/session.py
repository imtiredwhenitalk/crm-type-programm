import json
import os
import datetime

from db.session import SESSION_FILE

def save_session(username):
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump({'username': username, 'saved_at': datetime.datetime.now().isoformat()}, f)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        saved = datetime.datetime.fromisoformat(data['saved_at'])
        if (datetime.datetime.now() - saved).days < 30:
            return data.get('username')
    except Exception:
        pass
    return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
