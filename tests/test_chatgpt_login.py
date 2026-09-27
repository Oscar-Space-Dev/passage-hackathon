import threading

import pytest

from passage import codex_brain, integrations, store


def test_device_login_replaces_browser_flow_and_reuses_pending_code(client, monkeypatch):
    class FakeCodex:
        def __init__(self):
            self.login_lock = threading.Lock()
            self.login = None
            self.login_created_at = 0.0
            self.calls = []

        def request(self, method, params=None, timeout=25):
            self.calls.append((method, params))
            if method == 'account/read':
                return {'account': None}
            if method == 'account/login/cancel':
                return {}
            if method == 'account/login/start':
                kind = params['type']
                return {'type': kind, 'loginId':kind+'-id',
                        'authUrl':'https://chatgpt.com/login',
                        'verificationUrl':'https://auth.openai.com/codex/device',
                        'userCode':'TEST-CODE'}
            raise AssertionError(method)

    fake = FakeCodex()
    monkeypatch.setattr(codex_brain, 'client', lambda _: fake)
    browser = client.post('/api/brains/chatgpt/connect')
    assert browser.status_code == 200 and browser.json()['type'] == 'chatgpt'
    device = client.post('/api/brains/chatgpt/connect-device')
    assert device.status_code == 200 and device.json()['userCode'] == 'TEST-CODE'
    again = client.post('/api/brains/chatgpt/connect-device')
    assert again.status_code == 200 and again.json()['loginId'] == device.json()['loginId']
    assert [method for method, _ in fake.calls].count('account/login/start') == 2
    assert ('account/login/cancel', {'loginId':'chatgpt-id'}) in fake.calls
    renewed = client.post('/api/brains/chatgpt/connect-device?restart=true')
    assert renewed.status_code == 200
    assert [method for method, _ in fake.calls].count('account/login/start') == 3
    assert ('account/login/cancel', {'loginId':'chatgptDeviceCode-id'}) in fake.calls


def test_account_read_restarts_stale_codex_process(monkeypatch):
    user_id = 'routing-test-user'
    key = (str(store.db_path()), user_id)

    class Stale:
        mission_lock = threading.Lock()
        closed = False

        def request(self, method, params=None):
            raise integrations.IntegrationError(
                'Codex ne peut pas traiter account/read : workspace routing discovery failed')

        def close(self):
            self.closed = True

    class Fresh:
        def __init__(self, identifier):
            assert identifier == user_id

        def request(self, method, params=None):
            assert (method, params) == ('account/read', {'refreshToken': False})
            return {'account': {'type': 'chatgpt'}}

    stale = Stale()
    monkeypatch.setattr(codex_brain, 'CodexClient', Fresh)
    codex_brain.CLIENTS[key] = stale
    try:
        engine, account = codex_brain.account_with_reconnect(user_id, stale)
        assert isinstance(engine, Fresh)
        assert stale.closed
        assert account['type'] == 'chatgpt'
        assert codex_brain.CLIENTS[key] is engine
    finally:
        codex_brain.CLIENTS.pop(key, None)


def test_account_read_does_not_restart_on_other_errors(monkeypatch):
    class Failed:
        def request(self, method, params=None):
            raise integrations.IntegrationError('Accès refusé')

    monkeypatch.setattr(codex_brain, 'CodexClient', lambda _: pytest.fail('Unexpected restart'))
    with pytest.raises(integrations.IntegrationError, match='Accès refusé'):
        codex_brain.account_with_reconnect('routing-test-user', Failed())
