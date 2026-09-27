import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.RLock()

def now():
    return datetime.now(timezone.utc).isoformat()

def uid(prefix=''):
    return prefix + uuid.uuid4().hex[:12]

def db_path():
    return Path(os.environ.get('PASSAGE_DB', str(ROOT / 'data' / 'passage.db')))

@contextmanager
def transaction():
    with LOCK:
        path = db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, timeout=20)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def init():
    with transaction() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('CREATE TABLE IF NOT EXISTS objects (kind TEXT, id TEXT, body TEXT NOT NULL, PRIMARY KEY(kind,id))')
        c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, action TEXT, subject TEXT, detail TEXT)')

def put(kind, obj, conn=None):
    obj = dict(obj)
    obj.setdefault('id', uid())
    def write(c):
        c.execute('INSERT INTO objects VALUES (?,?,?) ON CONFLICT(kind,id) DO UPDATE SET body=excluded.body',
                  (kind, obj['id'], json.dumps(obj, ensure_ascii=False)))
    if conn is not None:
        write(conn)
    else:
        with transaction() as c:
            write(c)
    return obj

def get(kind, identifier, conn=None):
    def read(c):
        row = c.execute('SELECT body FROM objects WHERE kind=? AND id=?', (kind, str(identifier))).fetchone()
        return json.loads(row[0]) if row else None
    if conn is not None:
        return read(conn)
    with transaction() as c:
        return read(c)

def all_of(kind):
    with transaction() as c:
        return [json.loads(r[0]) for r in c.execute('SELECT body FROM objects WHERE kind=? ORDER BY rowid', (kind,))]

def event(action, subject='', detail=''):
    with transaction() as c:
        c.execute('INSERT INTO events(at,action,subject,detail) VALUES(?,?,?,?)', (now(), action, subject, detail))

def events(limit=80):
    with transaction() as c:
        return [dict(r) for r in c.execute('SELECT * FROM events ORDER BY id DESC LIMIT ?', (limit,))]

def remove(kind, identifier):
    with transaction() as c:
        c.execute('DELETE FROM objects WHERE kind=? AND id=?', (kind, identifier))
