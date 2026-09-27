"""Google OpenID Connect sign-in for local Passage accounts."""
import hmac
import secrets
import time
from urllib.parse import urlencode, urlparse

import httpx
from google.auth.exceptions import GoogleAuthError
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from . import auth, integrations, store

router = APIRouter(prefix='/api/auth/google')
STATE_COOKIE = 'passage_google_state'
ACCOUNT_TYPES = {'lab', 'researcher', 'company'}


def configuration():
    client_id = integrations.env('GOOGLE_CLIENT_ID').strip()
    secret = integrations.env('GOOGLE_CLIENT_SECRET').strip()
    public_url = integrations.env('PASSAGE_PUBLIC_URL', 'http://127.0.0.1:8088').rstrip('/')
    parsed = urlparse(public_url)
    if not client_id or not secret or parsed.scheme not in {'https', 'http'} or not parsed.netloc:
        raise HTTPException(503, 'La connexion Google n’est pas configurée sur cette installation.')
    if parsed.scheme != 'https' and parsed.hostname not in {'127.0.0.1', 'localhost'}:
        raise HTTPException(503, 'La connexion Google publique exige HTTPS.')
    return client_id, secret, public_url


def callback_url(public_url):
    return public_url + '/api/auth/google/callback'


@router.get('/start')
def start(request: Request, account_type: str = 'company', link: bool = False):
    client_id, _, public_url = configuration()
    if account_type not in ACCOUNT_TYPES:
        raise HTTPException(422, 'Profil de compte invalide.')
    if request.url.scheme + '://' + request.url.netloc != public_url:
        raise HTTPException(409, 'Ouvrez Passage avec son adresse publique configurée avant de lancer Google.')
    user, _ = auth.authenticate(request)
    if link and not user:
        raise HTTPException(401, 'Connectez-vous à Passage avant d’associer Google.')
    state = secrets.token_urlsafe(32)
    store.put('google_login_state', {'id': auth.digest(state), 'expires': time.time() + 600,
                                      'account_type': account_type,
                                      'link_user_id': user['id'] if link else ''})
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
        'client_id': client_id, 'redirect_uri': callback_url(public_url),
        'response_type': 'code', 'scope': 'openid email profile', 'state': state})
    response = RedirectResponse(url, status_code=303)
    response.set_cookie(STATE_COOKIE, state, max_age=600, httponly=True,
                        secure=public_url.startswith('https:'), samesite='lax', path='/api/auth/google')
    response.headers['Cache-Control'] = 'no-store'
    return response


def verify_id_token(raw, client_id):
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import id_token
    return id_token.verify_oauth2_token(raw, GoogleRequest(), client_id)


def exchange(code, client_id, secret, public_url):
    try:
        response = httpx.post('https://oauth2.googleapis.com/token', data={
            'code': code, 'client_id': client_id, 'client_secret': secret,
            'redirect_uri': callback_url(public_url), 'grant_type': 'authorization_code'}, timeout=20)
        response.raise_for_status()
        token = response.json().get('id_token', '')
        if not token:
            raise ValueError('ID token absent')
        return verify_id_token(token, client_id)
    except (httpx.HTTPError, GoogleAuthError, ValueError) as exc:
        raise HTTPException(502, 'La vérification Google a échoué. Réessayez la connexion.') from exc


def failure(reason):
    response = RedirectResponse('/?google=' + reason, status_code=303)
    response.delete_cookie(STATE_COOKIE, path='/api/auth/google')
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.get('/callback')
def callback(request: Request, state: str = '', code: str = '', error: str = ''):
    client_id, secret, public_url = configuration()
    cookie = request.cookies.get(STATE_COOKIE, '')
    if not state or not cookie or not hmac.compare_digest(state, cookie):
        return failure('state')
    saved = store.get('google_login_state', auth.digest(state))
    if not saved or saved['expires'] < time.time():
        return failure('expired')
    store.remove('google_login_state', saved['id'])
    if error or not code:
        return failure('cancelled')
    claims = exchange(code, client_id, secret, public_url)
    subject = str(claims.get('sub') or '')
    email = str(claims.get('email') or '').strip().casefold()
    verified = claims.get('email_verified') in (True, 'true')
    if not subject or not email or '@' not in email or not verified:
        return failure('identity')
    with store.transaction() as conn:
        users = store.all_of('user')
        linked = next((row for row in users if row.get('google_sub') == subject), None)
        by_email = next((row for row in users if row['email'] == email), None)
        linking = saved.get('link_user_id', '')
        if linking:
            current, _ = auth.authenticate(request)
            if not current or current['id'] != linking or current['email'] != email or (linked and linked['id'] != linking):
                return failure('link')
            user = current
        elif linked:
            user = linked
        elif by_email:
            # Google is authoritative for personal Gmail addresses. Other existing local
            # accounts require an explicit link from an authenticated Passage session.
            if email.split('@')[-1] not in {'gmail.com', 'googlemail.com'} or by_email.get('google_sub'):
                return failure('link')
            user = by_email
        else:
            role = saved['account_type'] if users or integrations.env('PASSAGE_PUBLIC_SIGNUP') == '1' else 'admin'
            user = {'id': store.uid('usr_'), 'email': email,
                    'name': str(claims.get('name') or email.split('@')[0])[:80],
                    'role': role, 'account_type': saved['account_type'],
                    'created_at': store.now()}
        user['google_sub'] = subject
        store.put('user', user, conn)
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    store.put('session', {'id': auth.digest(token), 'user_id': user['id'], 'csrf': csrf,
                          'expires': time.time() + 86400})
    response = RedirectResponse('/', status_code=303)
    response.set_cookie(auth.COOKIE, token, max_age=86400, httponly=True,
                        secure=public_url.startswith('https:'), samesite='strict', path='/')
    response.delete_cookie(STATE_COOKIE, path='/api/auth/google')
    response.headers['Cache-Control'] = 'no-store'
    store.event('Compte Google connecté à Passage', user['id'])
    return response
