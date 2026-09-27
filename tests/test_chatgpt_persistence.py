import json
import threading
from types import SimpleNamespace

from passage import codex_brain, store


def credentials(user_id, value):
    path = codex_brain.user_directory(user_id) / 'home' / 'auth.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'tokens': {'refresh_token': value}}))
    return path


def test_encrypted_credentials_survive_cache_loss_and_remain_personal(client, monkeypatch):
    monkeypatch.setattr(codex_brain, 'auth_cache_enabled', lambda: True)
    path = credentials('alice', 'synthetic-refresh-one')
    codex_brain.cache_auth('alice')
    saved = store.get('chatgpt_account', 'alice')
    assert 'synthetic-refresh-one' not in json.dumps(saved)
    assert 'encrypted' in saved
    path.unlink()
    codex_brain.restore_auth('bob')
    assert not (codex_brain.user_directory('bob') / 'home' / 'auth.json').exists()
    codex_brain.restore_auth('alice')
    assert json.loads(path.read_text())['tokens']['refresh_token'] == 'synthetic-refresh-one'
    credentials('alice', 'synthetic-refresh-two')
    codex_brain.cache_auth('alice')
    assert store.get('chatgpt_account', 'alice')['sha256'] != saved['sha256']
    path.unlink()
    codex_brain.restore_auth('alice')
    assert json.loads(path.read_text())['tokens']['refresh_token'] == 'synthetic-refresh-two'


def test_partial_write_preserves_last_valid_credentials(client, monkeypatch):
    monkeypatch.setattr(codex_brain, 'auth_cache_enabled', lambda: True)
    path = credentials('alice', 'synthetic-valid')
    codex_brain.cache_auth('alice')
    saved = store.get('chatgpt_account', 'alice')
    path.write_text('{')
    codex_brain.cache_auth('alice')
    assert store.get('chatgpt_account', 'alice') == saved


def test_hosted_connect_uses_device_code(client, monkeypatch):
    monkeypatch.setenv('RENDER_EXTERNAL_URL', 'https://passage.example.test')
    calls = []
    def login(kind):
        calls.append(kind)
        return {'type': kind}
    monkeypatch.setattr(codex_brain, 'begin_login', login)
    assert client.post('/api/brains/chatgpt/connect').json()['type'] == 'chatgptDeviceCode'
    assert calls == ['chatgptDeviceCode']


def test_disconnect_removes_persisted_access_only_for_current_user(client, monkeypatch):
    monkeypatch.setattr(codex_brain, 'auth_cache_enabled', lambda: True)
    user_id = client.get('/api/auth/status').json()['user']['id']
    path = credentials(user_id, 'synthetic-owner')
    credentials('other', 'synthetic-other')
    codex_brain.cache_auth(user_id)
    codex_brain.cache_auth('other')
    calls = []
    engine = SimpleNamespace(mission_lock=threading.Lock(), login=None,
                             request=lambda method: calls.append(method))
    monkeypatch.setattr(codex_brain, 'client', lambda _: engine)
    engine.mission_lock.acquire()
    assert client.post('/api/brains/chatgpt/disconnect').status_code == 409
    assert store.get('chatgpt_account', user_id)
    engine.mission_lock.release()
    assert client.post('/api/brains/chatgpt/disconnect').status_code == 200
    assert calls == ['account/logout']
    assert not path.exists()
    assert not store.get('chatgpt_account', user_id)
    assert store.get('chatgpt_account', 'other')
    codex_brain.cache_auth(user_id)
    codex_brain.restore_auth(user_id)
    assert not path.exists()
