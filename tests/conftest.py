import pytest
from fastapi.testclient import TestClient
from passage import integrations
from passage.main import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('PASSAGE_DB', str(tmp_path / 'test.db'))
    monkeypatch.setattr(integrations, 'load_dotenv', lambda *a, **kw: None)
    for key in integrations.SETTING_NAMES:
        monkeypatch.delenv(key, raising=False)
    integrations.SESSION_SECRETS.clear()
    with TestClient(app) as c:
        registered = c.post('/api/auth/register', json={'email':'admin@example.test', 'name':'Admin test', 'password':'test-password-123'}).json()
        c.headers.update({'X-Passage-CSRF': registered['csrf'], 'X-Passage-Role':'lab'})
        yield c
    integrations.SESSION_SECRETS.clear()
