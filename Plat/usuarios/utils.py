# usuarios/utils.py
import importlib
from django.conf import settings

def session_key_exists(session_key):
    if not session_key:
        return False
    try:
        engine = importlib.import_module(settings.SESSION_ENGINE)
        SessionStore = engine.SessionStore
        store = SessionStore(session_key=session_key)
        store.load()
        return True
    except Exception:
        return False
