"""Adaptateurs explicites. Aucun repli implicite vers une simulation."""
import asyncio
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv
from . import store

SESSION_SECRETS = {}
CONFIGURATION_SNAPSHOT = ContextVar('passage_configuration_snapshot', default=None)

@contextmanager
def configuration_snapshot():
    """Read encrypted installation settings once per operation, never globally."""
    if CONFIGURATION_SNAPSHOT.get() is not None:
        yield
        return
    rows = store.all_of('installation_setting') if store.remote_enabled() or store.db_path().exists() else []
    token = CONFIGURATION_SNAPSHOT.set({row['id']: row for row in rows})
    try:
        yield
    finally:
        CONFIGURATION_SNAPSHOT.reset(token)
SECRET_NAMES = {'OPENAI_API_KEY', 'DUST_API_KEY', 'PIPELEX_API_KEY', 'OSCAR_TOKEN', 'COMPATIBLE_API_KEY', 'GRADIUM_API_KEY', 'LATITUDE_API_KEY'}
SETTING_NAMES = SECRET_NAMES | {'DUST_WORKSPACE_ID', 'DUST_BASE_URL', 'PIPELEX_METHOD_REF', 'COMPATIBLE_BASE_URL',
                                'OSCAR_URL', 'OSCAR_MCP_SCRIPT', 'OSCAR_COMPANY', 'PASSAGE_OSCAR', 'OLLAMA_BASE_URL', 'GRADIUM_VOICE_ID', 'PASSAGE_PUBLIC_URL',
                                'LATITUDE_ENABLED', 'LATITUDE_INGEST_URL', 'LATITUDE_PROJECT_SLUG'}

class IntegrationError(RuntimeError):
    pass

def env(name, default=''):
    load_dotenv(store.ROOT / '.env', override=False)
    if name in SESSION_SECRETS:
        return SESSION_SECRETS[name]
    if store.remote_enabled() or store.db_path().exists():
        snapshot = CONFIGURATION_SNAPSHOT.get()
        row = snapshot.get(name) if snapshot is not None else store.get('installation_setting', name)
        if row:
            from .partner_mcp import cipher
            return cipher().decrypt(row['encrypted'].encode()).decode()
    if name == 'PASSAGE_PUBLIC_URL' and 'PASSAGE_PUBLIC_URL' not in os.environ:
        return os.environ.get('RENDER_EXTERNAL_URL') or default
    return os.environ.get(name, default)

def persist_settings(values):
    from .partner_mcp import cipher
    encryption = cipher()
    with store.transaction() as conn:
        for name, value in values.items():
            store.put('installation_setting', {'id': name, 'encrypted': encryption.encrypt(value.encode()).decode()}, conn)

def safe_error(exc):
    if isinstance(exc, BaseExceptionGroup):
        for inner in exc.exceptions:
            if isinstance(inner, (IntegrationError, BaseExceptionGroup)):
                return safe_error(inner)
        return 'Connexion MCP interrompue. Vérifiez le compte fournisseur et relancez la connexion.'
    if isinstance(exc, IntegrationError):
        return str(exc)
    if isinstance(exc, requests.Timeout):
        return 'Le service a dépassé le délai prévu. Vous pouvez réessayer.'
    if isinstance(exc, requests.RequestException):
        return 'Service réseau inaccessible. Vérifiez la connexion et les paramètres.'
    return 'Traitement interrompu : ' + type(exc).__name__ + '. Vérifiez les données et les paramètres.'

def http(method, url, **kwargs):
    r = requests.request(method, url, timeout=kwargs.pop('timeout', (10, 150)), **kwargs)
    if r.status_code >= 400:
        raise IntegrationError(f'Le service {urlparse(url).hostname} a répondu HTTP {r.status_code}. Vérifiez les accès et le contrat de la requête.')
    try:
        return r.json()
    except ValueError:
        raise IntegrationError('Le service a renvoyé une réponse non JSON.')

def headers(key):
    value = env(key)
    if not value:
        raise IntegrationError(f'Accès manquant : configurez {key} dans Connexions ou .env.')
    return {'Authorization': 'Bearer ' + value, 'Content-Type': 'application/json'}

@configuration_snapshot()
def statuses():
    return {'openai': bool(env('OPENAI_API_KEY')), 'dust': bool(env('DUST_API_KEY') and env('DUST_WORKSPACE_ID')),
            'pipelex': bool(env('PIPELEX_API_KEY')), 'compatible': bool(env('COMPATIBLE_BASE_URL')), 'ollama': True,
            'latitude': bool(env('LATITUDE_ENABLED') == 'on' and env('LATITUDE_API_KEY') and env('LATITUDE_INGEST_URL') and env('LATITUDE_PROJECT_SLUG')),
            'oscar': env('PASSAGE_OSCAR', 'demo'),
            'values': {k: env(k) for k in SETTING_NAMES - SECRET_NAMES},
            'secrets': {k: bool(env(k)) for k in SECRET_NAMES}}

def extract_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
    try:
        return json.loads(text)
    except ValueError:
        raise IntegrationError('Le moteur a renvoyé un texte qui ne respecte pas le contrat JSON. Le résultat précédent est conservé.')

def direct(agent, prompt, context, schema, tool_specs, invoke, trace):
    jinko_usage = None
    if 'jinko.read' in agent.get('tools', []):
        from . import jinko_bridge
        context, jinko_usage = jinko_bridge.enrich(agent, prompt, context,
            lambda instructions, data, contract: _direct(agent, instructions, data, contract, [], None, trace), trace)
    result, usage = _direct(agent, prompt, context, schema, tool_specs, invoke, trace)
    if jinko_usage is not None:
        usage = {**usage, 'jinko': jinko_usage}
    return result, usage


def _direct(agent, prompt, context, schema, tool_specs, invoke, trace):
    if agent['provider'] == 'codex':
        from . import auth, codex_brain
        if agent.get('connector_ids'):
            raise IntegrationError('Le coordinateur Passage pilote les MCP. Retirez les connecteurs directs du spécialiste ChatGPT dans ce POC.')
        trace('Cerveau : compte ChatGPT personnel, accès Codex.')
        return codex_brain.client(auth.current()['id']).complete(agent['model'], prompt, context, schema)
    if agent['provider'] == 'ollama':
        if agent.get('connector_ids'):
            raise IntegrationError('Les outils MCP pilotés par le modèle utilisent OpenAI direct dans ce POC. Les notices autorisées restent disponibles dans le contexte Ollama.')
        response = http('POST', env('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/') + '/api/chat',
                        timeout=(10, 480), json={'model': agent['model'], 'stream': False, 'think': False,
                        'format': schema, 'messages': [{'role': 'system', 'content': prompt},
                          {'role': 'user', 'content': json.dumps(context, ensure_ascii=False)}],
                        'options': {'temperature': 0.1, 'num_ctx': 32768, 'num_predict': 6000}, 'keep_alive': '10m'})
        if response.get('done_reason') == 'length':
            raise IntegrationError('Le modèle local a atteint sa limite de sortie sans terminer le dossier.')
        return extract_json(response['message']['content']), {'input_tokens': response.get('prompt_eval_count'),
               'output_tokens': response.get('eval_count'), 'actual_model': response.get('model'), 'duration_ns': response.get('total_duration')}
    if agent['provider'] == 'compatible':
        if agent.get('connector_ids'):
            raise IntegrationError('Les outils MCP du harnais nécessitent le moteur OpenAI direct dans ce POC. Retirez-les ou changez de moteur.')
        base = env('COMPATIBLE_BASE_URL')
        if not base:
            raise IntegrationError('Configurez COMPATIBLE_BASE_URL pour ce modèle.')
        hdr = {'Content-Type': 'application/json'}
        if env('COMPATIBLE_API_KEY'):
            hdr['Authorization'] = 'Bearer ' + env('COMPATIBLE_API_KEY')
        response = http('POST', base.rstrip('/') + '/chat/completions', headers=hdr,
                        json={'model': agent['model'], 'messages': [{'role': 'system', 'content': prompt},
                              {'role': 'user', 'content': json.dumps(context, ensure_ascii=False)}],
                              'response_format': {'type': 'json_object'}})
        return extract_json(response['choices'][0]['message']['content']), {**response.get('usage', {}), 'actual_model': response.get('model')}
    items = [{'role': 'user', 'content': json.dumps(context, ensure_ascii=False)}]
    usage = {}
    for step in range(agent['max_steps']):
        payload = {'model': agent['model'], 'instructions': prompt, 'input': items, 'store': False,
                   'max_output_tokens': 6000, 'text': {'format': {'type': 'json_schema', 'name': 'passage_report', 'strict': True, 'schema': schema}}}
        if tool_specs and step < agent['max_steps'] - 1:
            payload['tools'] = tool_specs
        response = http('POST', 'https://api.openai.com/v1/responses', headers=headers('OPENAI_API_KEY'), json=payload)
        usage = {**response.get('usage', {}), 'actual_model': response.get('model')}
        if response.get('status') in ('incomplete', 'failed'):
            raise IntegrationError('Réponse du modèle incomplète. Réduisez le corpus ou réessayez.')
        output = response.get('output', [])
        calls = [x for x in output if x.get('type') == 'function_call']
        if not calls:
            parts = [c.get('text', '') for x in output for c in x.get('content', []) if c.get('type') == 'output_text']
            if not parts:
                raise IntegrationError('Le modèle ne fournit pas de résultat exploitable (refus ou réponse vide).')
            return extract_json(''.join(parts)), usage
        items.extend(output)
        for call in calls:
            result = invoke(call['name'], extract_json(call['arguments']))
            trace(f"Outil utilisé : {call['name']}")
            items.append({'type': 'function_call_output', 'call_id': call['call_id'], 'output': json.dumps(result, ensure_ascii=False)})
    raise IntegrationError('Limite d’étapes atteinte sans résultat validé.')

def dust_export(agent, prompt):
    return {'agent': {'handle': 'passage-' + agent['role'] + '-' + agent['id'][-6:], 'description': agent['mandate'],
                      'max_steps_per_run': agent['max_steps'], 'visualization_enabled': False},
            'instructions': prompt, 'generation_settings': {'model_id': agent['model'], 'provider_id': agent['provider'], 'temperature': 0.2},
            'tags': [{'name': 'Passage'}], 'toolset': []}

def dust_base():
    wid = env('DUST_WORKSPACE_ID')
    if not wid:
        raise IntegrationError('Configurez DUST_WORKSPACE_ID.')
    return env('DUST_BASE_URL', 'https://dust.tt').rstrip('/') + '/api/v1/w/' + wid + '/assistant'

def dust_publish(agent, prompt):
    if agent.get('connector_ids'):
        raise IntegrationError('La projection Dust des connecteurs personnalisés doit être configurée dans Dust ; le POC refuse de les ignorer.')
    response = http('POST', dust_base() + '/agent_configurations/import', headers=headers('DUST_API_KEY'), json=dust_export(agent, prompt))
    config = response.get('agentConfiguration') or response.get('configuration') or response
    identifier = config.get('sId') or config.get('id')
    if not identifier:
        raise IntegrationError('Dust a répondu sans identifiant de configuration reconnu.')
    return str(identifier)

def dust_run(agent, context):
    if agent.get('dust_revision') != agent['revision'] or not agent.get('dust_id'):
        raise IntegrationError('Publiez la révision actuelle de cet agent dans Dust depuis l’atelier.')
    response = http('POST', dust_base() + '/conversations', headers=headers('DUST_API_KEY'),
                    json={'message': {'content': json.dumps(context, ensure_ascii=False),
                                      'mentions': [{'configurationId': agent['dust_id']}]},
                          'title': 'Passage — ' + agent['name'], 'blocking': True})
    conversation = response.get('conversation') or response
    texts = []
    def walk(x):
        if isinstance(x, dict):
            if x.get('type') == 'agent_message' and isinstance(x.get('content'), str):
                texts.append(x['content'])
            for value in x.values():
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(x, list):
            for value in x:
                walk(value)
    walk(conversation)
    if not texts:
        raise IntegrationError('Dust n’a pas retourné de message agent terminé dans le délai de l’appel.')
    return extract_json(texts[-1]), {'conversation_id': conversation.get('sId', '')}

def pipelex_run(agent, context):
    ref = agent.get('method_ref') or env('PIPELEX_METHOD_REF')
    if not ref:
        raise IntegrationError('Renseignez la référence de la méthode Pipelex publiée depuis le harnais.')
    response = http('POST', 'https://api.pipelex.com/v1/start', headers=headers('PIPELEX_API_KEY'),
                    json={'method_ref': ref, 'inputs': {'request': json.dumps(context, ensure_ascii=False)}})
    run_id = response.get('pipeline_run_id')
    if not run_id:
        raise IntegrationError('Pipelex n’a pas fourni d’identifiant d’exécution.')
    for _ in range(90):
        r = requests.get(f'https://api.pipelex.com/v1/runs/{run_id}/results', headers=headers('PIPELEX_API_KEY'), timeout=(10, 30))
        if r.status_code in (202, 404, 409):
            time.sleep(2)
            continue
        if r.status_code >= 400:
            raise IntegrationError(f'Pipelex : HTTP {r.status_code}. Exécution distante {run_id}.')
        body = r.json()
        if body.get('status') in ('failed', 'cancelled'):
            raise IntegrationError(f'Pipelex a interrompu l’exécution {run_id}.')
        main = body.get('main_stuff') or (body.get('pipe_output') or {}).get('main_stuff')
        if not main:
            time.sleep(2)
            continue
        content = main.get('content', main) if isinstance(main, dict) else main
        if isinstance(content, dict) and 'text' in content:
            content = content['text']
        return extract_json(content) if isinstance(content, str) else content, {'pipeline_run_id': run_id}
    raise IntegrationError(f'Pipelex est encore en cours. Identifiant distant : {run_id}. Consultez Pipelex avant de relancer.')

async def remote_mcp(connector, tool=None, arguments=None):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    secret = env(connector.get('secret_env', '')) if connector.get('secret_env') else ''
    hdr = {'Authorization': 'Bearer ' + secret} if secret else None
    async with streamablehttp_client(connector['url'], headers=hdr) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if tool:
                if tool not in connector['allowed_tools'] or not connector['enabled']:
                    raise IntegrationError('Outil MCP non autorisé par cette connexion.')
                result = await session.call_tool(tool, arguments or {})
            else:
                result = await session.list_tools()
            return result.model_dump(mode='json', by_alias=True)

def mcp(connector, tool=None, arguments=None):
    return asyncio.run(asyncio.wait_for(remote_mcp(connector, tool, arguments), timeout=45))

def oscar(tool, arguments=None):
    if tool not in {'oscar_projets', 'oscar_contexte', 'oscar_deposer_avis'}:
        raise IntegrationError('Outil Oscar non autorisé.')
    script = env('OSCAR_MCP_SCRIPT')
    if not script or not env('OSCAR_TOKEN'):
        raise IntegrationError('Configurez le chemin du serveur MCP Oscar et son jeton d’agent.')
    child_env = {**os.environ, 'OSCAR_API': env('OSCAR_URL', 'http://127.0.0.1:8000'),
                 'OSCAR_JETON': env('OSCAR_TOKEN'), 'OSCAR_COMPANY': env('OSCAR_COMPANY', '1'), 'OSCAR_SANS_TROUSSEAU': '1', 'PYTHONIOENCODING': 'utf-8'}
    messages = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'Passage', 'version': '0.1'}}},
                {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': tool, 'arguments': arguments or {}}}]
    try:
        process = subprocess.run([sys.executable, script], input='\n'.join(json.dumps(x) for x in messages) + '\n',
                                 text=True, encoding='utf-8', capture_output=True, env=child_env, timeout=70,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        raise IntegrationError('Oscar ne répond pas. Si une note était envoyée, vérifiez sa présence dans Oscar avant un nouvel essai.')
    for line in process.stdout.splitlines():
        try:
            answer = json.loads(line)
        except ValueError:
            continue
        if answer.get('id') == 2:
            result = answer.get('result', {})
            if answer.get('error') or result.get('isError'):
                raise IntegrationError('Oscar a refusé l’appel. Vérifiez le périmètre du jeton et le programme.')
            text = '\n'.join(c.get('text', '') for c in result.get('content', []))
            try:
                return json.loads(text)
            except ValueError:
                return text
    raise IntegrationError('Le serveur MCP Oscar n’a pas renvoyé de réponse exploitable.')
