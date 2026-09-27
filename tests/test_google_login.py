from fastapi.testclient import TestClient

from passage import google_login, integrations, store
from passage.main import app


def configured(monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test-client.apps.googleusercontent.com')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'test-secret')
    monkeypatch.setenv('PASSAGE_PUBLIC_URL', 'http://127.0.0.1:8088')


def test_google_signup_uses_verified_subject_and_selected_profile(client, monkeypatch):
    configured(monkeypatch)
    with TestClient(app, base_url='http://127.0.0.1:8088') as visitor:
        started = visitor.get('/api/auth/google/start?account_type=researcher', follow_redirects=False)
        assert started.status_code == 303
        assert 'scope=openid+email+profile' in started.headers['location']
        state = visitor.cookies.get(google_login.STATE_COOKIE)
        monkeypatch.setattr(google_login, 'exchange', lambda *args: {
            'sub': 'google-person-123', 'email': 'researcher@example.test',
            'email_verified': True, 'name': 'Researcher'})
        result = visitor.get('/api/auth/google/callback', params={'state': state, 'code': 'fake-code'},
                             follow_redirects=False)
        assert result.status_code == 303
        user = visitor.get('/api/auth/status').json()['user']
        assert user['role'] == 'researcher'
        assert user['account_type'] == 'researcher'
        assert user['google_linked'] is True
        assert store.get('user', user['id'])['google_sub'] == 'google-person-123'
        replay = visitor.get('/api/auth/google/callback', params={'state': state, 'code': 'fake-code'},
                             follow_redirects=False)
        assert replay.headers['location'] == '/?google=state'


def test_google_existing_workspace_email_requires_explicit_link(client, monkeypatch):
    configured(monkeypatch)
    monkeypatch.setattr(google_login, 'exchange', lambda *args: {
        'sub': 'google-admin-123', 'email': 'admin@example.test',
        'email_verified': True, 'name': 'Admin test'})
    with TestClient(app, base_url='http://127.0.0.1:8088') as visitor:
        started = visitor.get('/api/auth/google/start', follow_redirects=False)
        state = visitor.cookies.get(google_login.STATE_COOKIE)
        assert started.status_code == 303
        refused = visitor.get('/api/auth/google/callback', params={'state': state, 'code': 'fake-code'},
                              follow_redirects=False)
        assert refused.headers['location'] == '/?google=link'
        assert visitor.get('/api/auth/status').json()['user'] is None
    with TestClient(app, base_url='http://127.0.0.1:8088') as owner:
        owner.post('/api/auth/login', json={
            'email': 'admin@example.test', 'password': 'test-password-123'})
        started = owner.get('/api/auth/google/start?link=true&account_type=lab', follow_redirects=False)
        assert started.status_code == 303
        state = owner.cookies.get(google_login.STATE_COOKIE)
        linked = owner.get('/api/auth/google/callback', params={'state': state, 'code': 'fake-code'},
                           follow_redirects=False)
        assert linked.status_code == 303
        assert owner.get('/api/auth/status').json()['user']['google_linked'] is True


def test_public_registration_chooses_profile_without_admin_access(client):
    with TestClient(app) as visitor:
        response = visitor.post('/api/auth/register', json={
            'email': 'lab-new@example.test', 'name': 'Lab new',
            'password': 'strong-password-123', 'account_type': 'lab'})
        assert response.status_code == 200
        assert response.json()['user']['role'] == 'lab'
        assert response.json()['user']['account_type'] == 'lab'


def test_public_preview_first_account_is_not_admin(tmp_path, monkeypatch):
    monkeypatch.setenv('PASSAGE_DB', str(tmp_path / 'public-preview.db'))
    monkeypatch.setenv('PASSAGE_PUBLIC_SIGNUP', '1')
    monkeypatch.setattr(integrations, 'load_dotenv', lambda *a, **kw: None)
    with TestClient(app) as visitor:
        response = visitor.post('/api/auth/register', json={
            'email': 'first@example.test', 'name': 'First tester',
            'password': 'strong-password-123', 'account_type': 'researcher'})
        assert response.status_code == 200
        assert response.json()['user']['role'] == 'researcher'
        assert visitor.get('/api/auth/users').status_code == 403
