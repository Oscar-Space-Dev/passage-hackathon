"""Regression gates for remote reads without caching permissions or user data."""
import concurrent.futures
import json

from passage import auth, store


def test_state_query_budget_and_project_listing(client, monkeypatch):
    statements = []
    original = store.connect
    def traced():
        conn = original()
        conn.set_trace_callback(statements.append)
        return conn
    monkeypatch.setattr(store, 'connect', traced)
    assert client.get('/api/state').status_code == 200
    selects = [sql for sql in statements if sql.startswith('SELECT')]
    # Session/user join, collection batch, optional ChatGPT account, admin events.
    assert len(selects) <= 4
    statements.clear()
    assert client.get('/api/projects').status_code == 200
    assert len([sql for sql in statements if sql.startswith('SELECT')]) == 2
    assert store.READ_SNAPSHOT.get() is None


def test_permission_changes_and_logout_take_effect_immediately(client):
    user = client.get('/api/auth/status').json()['user']
    record = store.get('user', user['id'])
    record['role'] = 'researcher'
    store.put('user', record)
    assert client.get('/api/auth/users').status_code == 403
    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/state').status_code == 401


def test_remote_reader_reuses_transport_but_reads_fresh_data(monkeypatch, tmp_path):
    import libsql
    path = str(tmp_path / 'remote.db')
    opened = []
    def connect():
        conn = libsql.connect(path)
        opened.append(conn)
        return conn
    monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://test')
    monkeypatch.setattr(store, 'connect', connect)
    writer = libsql.connect(path)
    writer.execute('CREATE TABLE objects (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))')
    writer.execute('INSERT INTO objects VALUES (?,?,?)', ('user', 'one', json.dumps({'id':'one', 'role':'admin'})))
    writer.commit()
    assert store.get('user', 'one')['role'] == 'admin'
    writer.execute('UPDATE objects SET body=?', (json.dumps({'id':'one', 'role':'researcher'}),))
    writer.commit()
    assert store.get('user', 'one')['role'] == 'researcher'
    assert len(opened) == 1
    writer.close()
    opened[0].close()
    store.READ_CONNECTION.saved = None


def test_reader_does_not_wait_for_unrelated_write_lock(monkeypatch, tmp_path):
    monkeypatch.setenv('PASSAGE_DB', str(tmp_path / 'db.sqlite'))
    monkeypatch.delenv('TURSO_DATABASE_URL', raising=False)
    store.init()
    store.put('project', {'id': 'one'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        with store.LOCK:
            future = executor.submit(store.get, 'project', 'one')
            assert future.result(timeout=1) == {'id': 'one'}


def test_snapshot_does_not_leak_mutation_or_survive_operation(client):
    store.put('project', {'id':'snapshot', 'name':'first'})
    with store.read_snapshot('project'):
        store.get('project', 'snapshot')['name'] = 'unsaved'
        assert store.get('project', 'snapshot')['name'] == 'first'
    store.put('project', {'id':'snapshot', 'name':'second'})
    with store.read_snapshot('project'):
        assert store.get('project', 'snapshot')['name'] == 'second'
