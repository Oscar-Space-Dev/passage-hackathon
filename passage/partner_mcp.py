"""Official remote MCP servers: per-user OAuth, discovery and explicit tool grants."""
import asyncio
import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import httpx
from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider
from mcp.client.auth.utils import (build_protected_resource_metadata_discovery_urls,
    build_oauth_authorization_server_metadata_discovery_urls, credentials_match_issuer,
    validate_metadata_issuer)
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken, OAuthMetadata, ProtectedResourceMetadata
from . import auth, integrations, store

SERVICES = {'dust': {'name': 'Dust', 'url': 'https://dust.tt/mcp'},
            'dust-eu': {'name': 'Dust Europe', 'url': 'https://eu.dust.tt/mcp'},
            'pipelex': {'name': 'Pipelex', 'url': 'https://mcp.pipelex.com/mcp'}}
CATALOG_TOOLS = {'dust': 'list_agents', 'dust-eu': 'list_agents',
                 'pipelex': 'pipelex_list_methods'}
KNOWN_READ_ONLY = {'dust': {'identity', 'list_agents'},
                   'dust-eu': {'identity', 'list_agents'},
                   'pipelex': {'pipelex_list_methods', 'pipelex_show_method',
                               'pipelex_run_status', 'pipelex_run_results'}}
FLOWS = {}
LOCK = threading.RLock()
router = APIRouter(prefix='/api/mcp')

def public_result(value):
    """Keep tool data, excluding transport/UI metadata and embedded telemetry tokens."""
    if isinstance(value, dict):
        return {k: public_result(v) for k, v in value.items() if k != '_meta'}
    if isinstance(value, list):
        return [public_result(v) for v in value]
    return value

def pipelex_run_id(result):
    """Read a durable run ID from tool data without treating tool prose as instructions."""
    candidates = set()
    def inspect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('run_id', 'runId') and isinstance(item, str):
                    candidates.add(item.strip())
                elif key != '_meta':
                    inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
        elif isinstance(value, str):
            try:
                decoded = json.loads(value)
            except ValueError:
                decoded = None
            if decoded is not None and decoded != value:
                inspect(decoded)
            for match in re.finditer(r'(?i)\b(?:run[_ -]?id\s*[:=]|run\s+started\s*:)\s*`?([a-z0-9][a-z0-9_-]{5,127})', value):
                candidates.add(match.group(1))
    inspect(result)
    valid = [value for value in candidates if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{5,127}', value)]
    return valid[0] if len(valid) == 1 else ''

def dust_conversation_id(result):
    """Extract only an unambiguous conversation ID from a creation response."""
    candidates = set()
    def inspect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('conversationId', 'conversation_id') and isinstance(item, str):
                    candidates.add(item.strip())
                elif key == 'conversation' and isinstance(item, dict):
                    identifier = item.get('id')
                    if isinstance(identifier, str):
                        candidates.add(identifier.strip())
                    inspect(item)
                elif key != '_meta':
                    inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
        elif isinstance(value, str):
            try:
                decoded = json.loads(value)
            except ValueError:
                decoded = None
            if decoded is not None and decoded != value:
                inspect(decoded)
            for match in re.finditer(r'(?i)\bconversation[_ -]?id\s*[:=]\s*`?([a-z0-9][a-z0-9_-]{5,127})', value):
                candidates.add(match.group(1))
    inspect(result)
    valid = [value for value in candidates if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{5,127}', value)]
    return valid[0] if len(valid) == 1 else ''


def dust_conversation_page(result):
    """Extract IDs and titles for exact-match recovery, discarding all other fields."""
    data = result.get('structuredContent') if isinstance(result, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get('conversations'), list):
        blocks = result.get('content', []) if isinstance(result, dict) else []
        data = next((parsed for block in blocks if isinstance(block, dict) and block.get('type') == 'text'
                     for parsed in [parse_json_object(block.get('text', ''))]
                     if parsed is not None and isinstance(parsed.get('conversations'), list)), None)
    if not isinstance(data, dict):
        raise integrations.IntegrationError('Liste des conversations Dust illisible ; vérifiez la conversation dans Dust.')
    items = []
    for entry in data['conversations'][:25]:
        if not isinstance(entry, dict):
            continue
        title = entry.get('title')
        identifier = entry.get('sId') or entry.get('conversationId') or entry.get('id')
        if isinstance(title, str) and isinstance(identifier, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{5,127}', identifier):
            items.append({'title': title, 'id': identifier})
    cursor = data.get('nextCursor') or data.get('lastValue')
    if data.get('hasMore') is False or not isinstance(cursor, str) or not cursor:
        cursor = None
    return items, cursor


def dust_message_count(result):
    """Count known messages without promoting transport text to an agent answer."""
    data = result.get('structuredContent') if isinstance(result, dict) else None
    if not isinstance(data, dict) or 'messages' not in data:
        blocks = result.get('content', []) if isinstance(result, dict) else []
        data = next((parsed for block in blocks if isinstance(block, dict) and block.get('type') == 'text'
                     for parsed in [parse_json_object(block.get('text', ''))]
                     if parsed is not None and 'messages' in parsed), None)
    if not isinstance(data, dict):
        return None
    messages = data['messages']
    if isinstance(messages, str):
        if not messages.strip():
            return 0
        try:
            messages = json.loads(messages)
        except ValueError:
            return None
    return len(messages) if isinstance(messages, list) else None

def catalog_items(service, result):
    """Extract catalogue records; ignore tool prose and instructions around them."""
    lines = [item.get('text', '') for item in result.get('content', []) if item.get('type') == 'text']
    if service in ('dust', 'dust-eu'):
        for text in lines:
            try:
                agents = json.loads(text).get('agents', [])
            except (ValueError, AttributeError):
                continue
            if isinstance(agents, list):
                return [{'id': str(item.get('id',''))[:120], 'name': str(item.get('name',''))[:120],
                         'description': str(item.get('description',''))[:2000]}
                        for item in agents[:50] if isinstance(item,dict) and item.get('name')]
        return []
    pattern = re.compile(r'^\s*-\s*\*\*(.*?)\*\*\s*[—–-]\s*(.*?)\s*\(method_id:\s*`([^`]+)`\)\s*$')
    records = []
    for text in lines:
        for line in text.splitlines():
            match = pattern.match(line)
            if match:
                records.append({'id': match.group(3)[:120], 'name': match.group(1)[:120],
                                'description': match.group(2)[:2000]})
            if len(records) >= 50:
                return records
    return records


def pipelex_method_signature(result):
    """Extract only the method contract, not instructions embedded in tool prose."""
    blocks = result.get('content', []) if isinstance(result, dict) else []
    raw = '\n'.join(block.get('text', '') for block in blocks
                    if isinstance(block, dict) and block.get('type') == 'text')
    signature = re.search(r'(?m)^##\s+Signature\s*\n\s*`([^`\n]{1,500})`', raw)
    template = re.search(r'(?ms)^##\s+Inputs template\s*\n\s*```json\s*\n(.*?)^\s*```', raw)
    if not signature or not template:
        raise integrations.IntegrationError('Signature Pipelex illisible. Consultez la méthode dans Pipelex.')
    try:
        inputs = json.loads(template.group(1))
    except ValueError:
        raise integrations.IntegrationError('Modèle d’entrées Pipelex illisible. Consultez la méthode dans Pipelex.')
    if not isinstance(inputs, dict):
        raise integrations.IntegrationError('Modèle d’entrées Pipelex invalide.')
    return {'signature': signature.group(1), 'inputs': inputs}


def pipelex_lifecycle(result):
    """Read the structured status fields; never infer completion from tool prose."""
    data = result.get('structuredContent') if isinstance(result, dict) else None
    if not isinstance(data, dict):
        blocks = result.get('content', []) if isinstance(result, dict) else []
        data = next((parsed for block in blocks if isinstance(block, dict) and block.get('type') == 'text'
                     for parsed in [parse_json_object(block.get('text', ''))] if parsed is not None), None)
    if not isinstance(data, dict):
        return None
    state = data.get('run_status')
    if state not in {'PENDING', 'STARTED', 'RUNNING', 'COMPLETED', 'FAILED',
                     'CANCELLED', 'TERMINATED', 'TIMED_OUT'}:
        return None
    retry = data.get('retry_after_seconds')
    retry = retry if isinstance(retry, (int, float)) and not isinstance(retry, bool) and 0 <= retry <= 3600 else None
    return {'run_status': state, 'is_terminal': data.get('is_terminal') is True,
            'degraded': data.get('degraded') is True, 'retry_after_seconds': retry}


def parse_json_object(text):
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None

def cipher():
    env_key = os.environ.get('PASSAGE_ENCRYPTION_KEY')
    if env_key:
        return Fernet(env_key.encode())
    if store.remote_enabled():
        raise RuntimeError('PASSAGE_ENCRYPTION_KEY est requis avec une base distante.')
    path = store.db_path().parent / 'runtime' / 'oauth.key'
    with LOCK:
        path.parent.mkdir(exist_ok=True, parents=True)
        if not path.exists():
            with path.open('xb') as output:
                output.write(Fernet.generate_key())
            path.chmod(0o600)
        return Fernet(path.read_bytes())

class Storage:
    def __init__(self, user_id, service):
        self.key = user_id + ':' + service
        self.generation = (store.get('mcp_generation', self.key) or {}).get('value',0)

    def read(self):
        row = store.get('oauth_secret', self.key)
        return json.loads(cipher().decrypt(row['encrypted'].encode())) if row else {}

    def write(self, name, value):
        with LOCK:
            if (store.get('mcp_generation', self.key) or {}).get('value',0)!=self.generation:
                raise integrations.IntegrationError('Cette connexion a été annulée.')
            content = self.read()
            content[name] = value.model_dump(mode='json')
            if name=='tokens':
                content['expires_at'] = time.time()+value.expires_in if value.expires_in is not None else None
            store.put('oauth_secret', {'id': self.key, 'encrypted': cipher().encrypt(json.dumps(content).encode()).decode()})

    async def get_tokens(self):
        content = self.read()
        value = content.get('tokens')
        if value and content.get('expires_at') is not None:
            value['expires_in'] = max(0, int(content['expires_at']-time.time()))
        return OAuthToken.model_validate(value) if value else None

    async def set_tokens(self, tokens):
        self.write('tokens', tokens)

    async def get_client_info(self):
        value = self.read().get('client')
        return OAuthClientInformationFull.model_validate(value) if value else None

    async def set_client_info(self, client_info):
        self.write('client', client_info)

def service_spec(service):
    if service not in SERVICES:
        raise HTTPException(404, 'Service MCP inconnu.')
    return SERVICES[service]

def read_only(service, tool, definition=None):
    return (tool in KNOWN_READ_ONLY.get(service, set()) or
            ((definition or {}).get('annotations') or {}).get('readOnlyHint') is True)

def link(user_id, service):
    return store.get('mcp_link', user_id+':'+service) or {'id': user_id+':'+service, 'service': service, 'tools': [], 'allowed_tools': [], 'connected': False}

class ResumingOAuthProvider(OAuthClientProvider):
    """Restore expiration and validated discovery before the SDK refreshes saved tokens.

    The current MCP SDK loads tokens without restoring their expiry or discovery
    context; an expired saved token then receives 401 and starts a new login.
    """
    async def _initialize(self):
        await super()._initialize()
        if not self.context.current_tokens:
            return
        self.context.update_token_expiry(self.context.current_tokens)
        if not self.context.can_refresh_token():
            return
        async with httpx.AsyncClient(timeout=20) as discovery:
            for url in build_protected_resource_metadata_discovery_urls(None, self.context.server_url):
                response = await discovery.get(url)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                resource = ProtectedResourceMetadata.model_validate(response.json())
                await self._validate_resource_match(resource)
                self.context.protected_resource_metadata = resource
                self.context.auth_server_url = self._select_authorization_server([str(u) for u in resource.authorization_servers])
                break
            else:
                raise integrations.IntegrationError('Métadonnées OAuth indisponibles ; reconnectez le service.')
            issuer = self._expected_issuer()
            if not credentials_match_issuer(self.context.client_info, issuer, self.context.client_metadata_url):
                raise integrations.IntegrationError('Le serveur d’autorisation a changé ; reconnectez le service.')
            for url in build_oauth_authorization_server_metadata_discovery_urls(self.context.auth_server_url, self.context.server_url):
                response = await discovery.get(url)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                metadata = OAuthMetadata.model_validate(response.json())
                validate_metadata_issuer(metadata, issuer)
                self.context.oauth_metadata = metadata
                break
            else:
                raise integrations.IntegrationError('Métadonnées de renouvellement introuvables ; reconnectez le service.')

async def exchange(user_id, service, tool=None, arguments=None, flow=None):
    spec = service_spec(service)
    async def redirect(url):
        if flow is None:
            raise integrations.IntegrationError('Reconnectez ce service MCP dans Connexions.')
        flow.update(status='awaiting_login', authorization_url=url, expected_state=parse_qs(urlparse(url).query).get('state', [''])[0])
    async def callback():
        while time.time()<flow['expires']:
            if flow.get('callback'):
                return flow['callback']
            await asyncio.sleep(.2)
        raise integrations.IntegrationError('La connexion OAuth a expiré. Relancez-la.')
    provider = ResumingOAuthProvider(server_url=spec['url'], storage=Storage(user_id, service),
        client_metadata=OAuthClientMetadata(client_name='Passage', redirect_uris=[integrations.env('PASSAGE_PUBLIC_URL', 'http://127.0.0.1:8088').rstrip('/')+'/api/mcp/oauth/callback'],
            token_endpoint_auth_method='none', grant_types=['authorization_code','refresh_token'], response_types=['code']),
        redirect_handler=redirect, callback_handler=callback if flow else None)
    async with httpx.AsyncClient(auth=provider, timeout=httpx.Timeout(30, read=300)) as client:
        async with streamable_http_client(spec['url'], http_client=client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                if tool:
                    connection = link(user_id, service)
                    if not connection['connected'] or tool not in connection['allowed_tools']:
                        raise integrations.IntegrationError('Outil MCP non autorisé pour ce compte.')
                    result = await session.call_tool(tool, arguments or {})
                    if result.isError:
                        raise integrations.IntegrationError('Le service MCP a signalé un échec ; vérifiez le résultat dans le service avant de réessayer une écriture.')
                    return public_result(result.model_dump(mode='json', by_alias=True))
                tools = []
                cursor = None
                for _ in range(20):
                    page = await session.list_tools(cursor=cursor)
                    tools.extend(t.model_dump(mode='json', by_alias=True) for t in page.tools)
                    cursor = page.nextCursor
                    if not cursor:
                        break
                with LOCK:
                    if flow is not None and flow['expires']<time.time():
                        raise integrations.IntegrationError('Cette connexion a expiré ou a été annulée.')
                    connection = link(user_id, service)
                    names = {t['name'] for t in tools}
                    connection.update(connected=True, tools=tools, checked_at=store.now(), allowed_tools=[n for n in connection['allowed_tools'] if n in names])
                    store.put('mcp_link', connection)
                return connection

def invoke(user_id, service, tool=None, arguments=None):
    timeout = 45 if tool in KNOWN_READ_ONLY.get(service, set()) else 330
    try:
        return asyncio.run(asyncio.wait_for(exchange(user_id, service, tool, arguments), timeout))
    except TimeoutError as exc:
        if timeout == 45:
            raise integrations.IntegrationError(
                'La lecture MCP a dépassé 45 secondes. Réessayez ou reconnectez le service.') from exc
        raise

def available(user_id):
    return [{**spec, **link(user_id, name)} for name,spec in SERVICES.items()]

@router.get('/services')
def services():
    return available(auth.current()['id'])

@router.get('/pipelex/research-method')
def research_method():
    path = Path(__file__).resolve().parents[1] / 'methods' / 'recherche_doctorale.mthds'
    return FileResponse(path, media_type='application/octet-stream',
                        filename='passage-recherche-doctorale.mthds')

@router.get('/{service}/catalog')
def catalog(service: str):
    service_spec(service)
    tool = CATALOG_TOOLS[service]
    connection = link(auth.current()['id'], service)
    if not connection['connected'] or tool not in connection['allowed_tools']:
        raise HTTPException(403, 'Autorisez l’outil de catalogue dans Connexions avant de le consulter.')
    definition = next((item for item in connection['tools'] if item['name']==tool), None)
    if not definition or not read_only(service, tool, definition):
        raise HTTPException(403, 'Cet outil ne peut pas être appelé comme lecture de catalogue.')
    try:
        result = invoke(auth.current()['id'], service, tool, {})
        return {'service': service, 'tool': tool, 'items': catalog_items(service, result)}
    except Exception as exc:
        raise HTTPException(502, integrations.safe_error(exc))

@router.post('/{service}/connect')
def connect(service: str):
    service_spec(service)
    user_id = auth.current()['id']
    flow_id = secrets.token_urlsafe(20)
    flow = {'id': flow_id, 'user_id': user_id, 'service': service, 'status': 'connecting', 'expires': time.time()+900}
    with LOCK:
        existing = next((f for f in FLOWS.values() if f['user_id']==user_id and f['service']==service
                         and f['status'] in ('connecting','awaiting_login','exchanging') and f['expires']>time.time()),None)
        if existing:
            return {'id': existing['id'], 'status':existing['status']}
        for identifier in list(FLOWS):
            if FLOWS[identifier]['expires'] < time.time():
                del FLOWS[identifier]
        FLOWS[flow_id] = flow
    def work():
        try:
            asyncio.run(asyncio.wait_for(exchange(user_id, service, flow=flow), 930))
            flow.update(status='connected')
        except Exception as exc:
            flow.update(status='failed', error=integrations.safe_error(exc))
    threading.Thread(target=work, daemon=True, name='passage-oauth').start()
    return {'id': flow_id, 'status': flow['status']}

@router.get('/flows/{identifier}')
def flow_status(identifier: str):
    flow = FLOWS.get(identifier)
    if not flow or flow['user_id'] != auth.current()['id']:
        raise HTTPException(404, 'Connexion introuvable.')
    return {k: flow[k] for k in ['id','service','status','authorization_url','error'] if k in flow}

@router.get('/oauth/callback')
def oauth_callback(state: str = '', code: str = '', error: str = ''):
    with LOCK:
        flow = next((f for f in FLOWS.values() if f.get('expected_state') and secrets.compare_digest(f['expected_state'], state)
                     and f['expires']>time.time() and f['status']=='awaiting_login'), None)
        if not flow:
            raise HTTPException(400, 'État OAuth invalide ou expiré.')
        if error or not code:
            flow.update(status='failed', error='Connexion refusée par le fournisseur.', expires=0)
        else:
            flow.update(status='exchanging', callback=(code,state))
    return HTMLResponse('<!doctype html><meta charset="utf-8"><title>Passage — connexion</title><h1>Retour dans Passage</h1><p>Vous pouvez revenir à votre fenêtre Passage pour suivre la connexion.</p><a href="/">Ouvrir Passage</a>', headers={'Referrer-Policy':'no-referrer', 'Cache-Control':'no-store'})

@router.put('/{service}/tools')
def grant(service: str, body: dict):
    service_spec(service)
    row = link(auth.current()['id'], service)
    names = body.get('allowed_tools', [])
    if not isinstance(names,list) or any(not isinstance(n,str) or n not in {t['name'] for t in row['tools']} for n in names):
        raise HTTPException(422, 'Choisissez des outils découverts sur ce serveur.')
    row['allowed_tools'] = list(dict.fromkeys(names))
    store.put('mcp_link', row)
    return row

@router.post('/{service}/disconnect')
def disconnect(service: str):
    service_spec(service)
    key = auth.current()['id']+':'+service
    with LOCK:
        generation = (store.get('mcp_generation', key) or {}).get('value',0)
        store.put('mcp_generation', {'id':key,'value':generation+1})
        for flow in FLOWS.values():
            if flow['user_id']==auth.current()['id'] and flow['service']==service:
                flow.update(expires=0, status='failed', error='Connexion annulée.')
        store.remove('oauth_secret', key)
        store.remove('mcp_link', key)
    return {'ok': True}
