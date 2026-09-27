import threading

from passage import codex_brain


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
