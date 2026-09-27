import json
import os
import sqlite3
import threading
import time
import copy
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.RLock()
READ_CONNECTION = threading.local()
READ_SNAPSHOT = ContextVar('passage_read_snapshot', default=None)

def now():
    return datetime.now(timezone.utc).isoformat()

def uid(prefix=''):
    return prefix + uuid.uuid4().hex[:12]

def db_path():
    return Path(os.environ.get('PASSAGE_DB', str(ROOT / 'data' / 'passage.db')))

def remote_enabled():
    return bool(os.environ.get('TURSO_DATABASE_URL'))

def connect():
    if remote_enabled():
        url = os.environ['TURSO_DATABASE_URL']
        token = os.environ.get('TURSO_AUTH_TOKEN')
        if not token:
            raise RuntimeError('TURSO_AUTH_TOKEN est requis pour la base distante.')
        if url.startswith('turso://'):
            import turso_serverless
            return turso_serverless.connect(url, auth_token=token)
        if url.startswith('libsql://'):
            import libsql
            return libsql.connect(database=url, auth_token=token)
        raise RuntimeError('TURSO_DATABASE_URL doit utiliser turso:// ou libsql://.')
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def transaction():
    with LOCK:
        conn = connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

@contextmanager
def reader():
    """Independent read connections; never wait behind the process-wide write lock.

    Reuse remote transports only on their owning worker thread. No result or
    authentication cache survives a request. Writes still commit to Turso.
    """
    if not remote_enabled():
        conn = connect()
        try:
            yield conn
        finally:
            conn.close()
        return
    key = (os.environ.get('TURSO_DATABASE_URL'), os.environ.get('TURSO_AUTH_TOKEN'), connect)
    saved = getattr(READ_CONNECTION, 'saved', None)
    if saved and (saved[0] != key or time.monotonic() - saved[2] > 30):
        saved[1].close()
        saved = None
        READ_CONNECTION.saved = None
    conn = saved[1] if saved else connect()
    try:
        yield conn
    except Exception:
        READ_CONNECTION.saved = None
        conn.close()
        raise
    else:
        READ_CONNECTION.saved = (key, conn, time.monotonic())

@contextmanager
def read_snapshot(*kinds):
    """Batch a read-only view's collections in one query, scoped to this call."""
    with reader() as c:
        rows = c.execute('SELECT kind,id,body FROM objects WHERE kind IN (' +
                         ','.join('?' for _ in kinds) + ') ORDER BY rowid', kinds).fetchall()
    collections = {kind: {} for kind in kinds}
    for kind, identifier, body in rows:
        collections[kind][identifier] = json.loads(body)
    token = READ_SNAPSHOT.set((collections, {}))
    try:
        yield
    finally:
        READ_SNAPSHOT.reset(token)

def session_user(identifier):
    """Read session and its current user in a single query (no auth cache)."""
    with reader() as c:
        row = c.execute("SELECT s.body,u.body FROM objects s JOIN objects u "
                        "ON u.kind='user' AND u.id=json_extract(s.body,'$.user_id') "
                        "WHERE s.kind='session' AND s.id=?", (identifier,)).fetchone()
    return (json.loads(row[1]), json.loads(row[0])) if row else (None, None)

def init():
    if os.environ.get('PASSAGE_REQUIRE_REMOTE_DB') == '1' and not remote_enabled():
        raise RuntimeError('Déploiement incomplet : TURSO_DATABASE_URL est requis.')
    if remote_enabled() and not os.environ.get('PASSAGE_ENCRYPTION_KEY'):
        raise RuntimeError('PASSAGE_ENCRYPTION_KEY est requis avec une base distante pour conserver les connexions chiffrées.')
    if remote_enabled():
        try:
            Fernet(os.environ['PASSAGE_ENCRYPTION_KEY'].encode())
        except ValueError as exc:
            raise RuntimeError('PASSAGE_ENCRYPTION_KEY doit être une clé Fernet valide.') from exc
    with transaction() as c:
        if not remote_enabled():
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
    snapshot = READ_SNAPSHOT.get()
    key = (kind, str(identifier))
    if snapshot is not None:
        collections, singles = snapshot
        if kind in collections:
            return copy.deepcopy(collections[kind].get(str(identifier)))
        if key in singles:
            return copy.deepcopy(singles[key])
    with reader() as c:
        value = read(c)
    if snapshot is not None:
        snapshot[1][key] = copy.deepcopy(value)
    return value

def all_of(kind):
    snapshot = READ_SNAPSHOT.get()
    if snapshot is not None and kind in snapshot[0]:
        return copy.deepcopy(list(snapshot[0][kind].values()))
    with reader() as c:
        return [json.loads(r[0]) for r in c.execute('SELECT body FROM objects WHERE kind=? ORDER BY rowid', (kind,)).fetchall()]

def event(action, subject='', detail=''):
    with transaction() as c:
        c.execute('INSERT INTO events(at,action,subject,detail) VALUES(?,?,?,?)', (now(), action, subject, detail))

def events(limit=80):
    with reader() as c:
        return [dict(zip(('id', 'at', 'action', 'subject', 'detail'), r))
                for r in c.execute('SELECT id,at,action,subject,detail FROM events ORDER BY id DESC LIMIT ?', (limit,)).fetchall()]

def remove(kind, identifier):
    with transaction() as c:
        c.execute('DELETE FROM objects WHERE kind=? AND id=?', (kind, identifier))
