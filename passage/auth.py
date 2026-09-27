"""Local accounts, opaque sessions and server-enforced roles."""
import hashlib
import hmac
import secrets
import time
from contextvars import ContextVar
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from . import integrations, store

CURRENT_USER = ContextVar('passage_user', default=None)
COOKIE = 'passage_session'
ROLES = {'admin', 'lab', 'researcher', 'company'}
router = APIRouter(prefix='/api/auth')

class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)
    name: str = Field(default='', max_length=80)
    account_type: str = Field(default='company', max_length=30)

def public(user):
    return {**{k: user[k] for k in ('id', 'email', 'name', 'role')},
            'account_type': user.get('account_type', 'lab' if user['role'] == 'admin' else user['role']),
            'google_linked': bool(user.get('google_sub'))}

def current():
    user = CURRENT_USER.get()
    if not user:
        raise HTTPException(401, 'Connectez-vous pour continuer.')
    return user

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600000)
    return salt + ':' + derived.hex()

def authenticate(request):
    raw = request.cookies.get(COOKIE, '')
    session = store.get('session', digest(raw)) if raw else None
    if not session or session['expires'] < time.time():
        return None, None
    return store.get('user', session['user_id']), session

def issue(user, request):
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    store.put('session', {'id': digest(token), 'user_id': user['id'], 'csrf': csrf, 'expires': time.time()+86400})
    response = JSONResponse({'user': public(user), 'csrf': csrf})
    response.set_cookie(COOKIE, token, max_age=86400, httponly=True, secure=request.url.scheme=='https', samesite='strict', path='/')
    response.headers['Cache-Control'] = 'no-store'
    return response

def throttle(request, email):
    key = digest((request.client.host if request.client else '') + ':' + email)
    with store.transaction() as conn:
        row = store.get('auth_attempt', key, conn) or {'id': key, 'times': []}
        row['times'] = [t for t in row['times'] if t > time.time()-300]
        if len(row['times']) >= 10:
            raise HTTPException(429, 'Trop de tentatives. Réessayez dans cinq minutes.')
        row['times'].append(time.time())
        store.put('auth_attempt', row, conn)

@router.get('/status')
def status(request: Request):
    user, session = authenticate(request)
    return {'setup_required': not bool(store.all_of('user')), 'user': public(user) if user else None,
            'csrf': session['csrf'] if user else None,
            'google_enabled': bool(integrations.env('GOOGLE_CLIENT_ID')
                                   and integrations.env('GOOGLE_CLIENT_SECRET'))}

@router.post('/register')
def register(body: Credentials, request: Request):
    email = body.email.strip().casefold()
    if '@' not in email or len(body.password)<12 or not body.name.strip() or body.account_type not in {'lab', 'researcher', 'company'}:
        raise HTTPException(422, 'Nom, email et mot de passe de 12 caractères minimum requis.')
    throttle(request, email)
    hashed = password_hash(body.password)
    with store.transaction() as conn:
        users = store.all_of('user')
        if any(u['email']==email for u in users):
            raise HTTPException(409, 'Un compte existe déjà avec cet email.')
        user = store.put('user', {'id': store.uid('usr_'), 'email': email, 'name': body.name.strip(),
                    'role': body.account_type if users or integrations.env('PASSAGE_PUBLIC_SIGNUP') == '1' else 'admin',
                    'account_type': body.account_type,
                    'password_hash': hashed, 'created_at': store.now()}, conn)
    store.event('Compte local créé', user['id'])
    return issue(user, request)

@router.post('/login')
def login(body: Credentials, request: Request):
    email = body.email.strip().casefold()
    throttle(request, email)
    user = next((u for u in store.all_of('user') if u['email']==email), None)
    saved = user.get('password_hash') if user else None
    saved = saved or ('00'*16+':'+'00'*32)
    valid = hmac.compare_digest(password_hash(body.password, saved.split(':')[0]), saved)
    if not user or not valid:
        raise HTTPException(401, 'Email ou mot de passe incorrect.')
    return issue(user, request)

@router.post('/logout')
def logout(request: Request):
    store.remove('session', digest(request.cookies.get(COOKIE, '')))
    response = JSONResponse({'ok': True})
    response.delete_cookie(COOKIE, path='/')
    return response

@router.get('/users')
def users():
    if current()['role']!='admin':
        raise HTTPException(403, 'Administration requise.')
    return [public(u) for u in store.all_of('user')]

@router.patch('/users/{identifier}')
def change_role(identifier: str, body: dict):
    if current()['role']!='admin':
        raise HTTPException(403, 'Administration requise.')
    role = body.get('role')
    if role not in ROLES or identifier==current()['id']:
        raise HTTPException(422, 'Rôle invalide ou modification de votre propre rôle.')
    user = store.get('user', identifier)
    if not user:
        raise HTTPException(404, 'Compte introuvable.')
    user['role'] = role
    store.put('user', user)
    store.event('Rôle du compte modifié', identifier, role)
    return public(user)

def install(app):
    app.include_router(router)

    @app.middleware('http')
    async def session_guard(request: Request, call_next):
        if not request.url.path.startswith('/api/'):
            return await call_next(request)
        # No cross-origin state changes, including login. No CORS wildcard is used.
        origin = request.headers.get('origin')
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin:
            if urlparse(origin).netloc != request.url.netloc:
                return JSONResponse({'detail': 'Origine de requête refusée.'}, status_code=403)
        public_route = request.url.path in {'/api/health', '/api/auth/status', '/api/auth/login', '/api/auth/register',
                                            '/api/auth/google/start', '/api/auth/google/callback', '/api/mcp/oauth/callback'}
        user, session = authenticate(request)
        if not public_route and not user:
            return JSONResponse({'detail': 'Connectez-vous pour continuer.'}, status_code=401)
        if not public_route and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            supplied = request.headers.get('x-passage-csrf', '')
            if not hmac.compare_digest(supplied, session['csrf']):
                return JSONResponse({'detail': 'Session expirée ou vérification de requête manquante.'}, status_code=403)
        if user:
            chosen = request.headers.get('x-passage-role', user['role'])
            effective = chosen if user['role']=='admin' and chosen in ROLES else user['role']
            request.scope['headers'] = [(k,v) for k,v in request.scope['headers'] if k.lower()!=b'x-passage-role']
            request.scope['headers'].append((b'x-passage-role', effective.encode()))
        token = CURRENT_USER.set(user)
        try:
            response = await call_next(request)
            response.headers['Cache-Control'] = 'no-store'
            return response
        finally:
            CURRENT_USER.reset(token)
