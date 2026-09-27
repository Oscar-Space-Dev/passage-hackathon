import concurrent.futures
import copy
import csv
import io
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from . import agents, creator, integrations, sources, store, auth, google_login, projects, partner_mcp, voice, voice_live, voice_codex, codex_brain, workflows, diagrams, latitude, guide
from .schemas import (AgentInput, ConnectorInput, CorrectionInput, DecisionInput, ImportInput,
                      ProgrammeInput, ProposalInput, RunInput, VisibilityInput)
from . import jinko_bridge, teams

POOL = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix='passage')
Role = Annotated[str, Header(alias='X-Passage-Role')]

@asynccontextmanager
async def lifespan(app):
    store.init()
    sources.seed()
    agents.seed()
    for job in store.all_of('run'):
        if job['status'] in ('queued', 'running'):
            job.update(status='interrupted', error='Le serveur a redémarré pendant cette tâche.', ended_at=store.now())
            store.put('run', job)
    for approval in store.all_of('approval'):
        if approval['status']=='sending':
            approval['status']='delivery_unknown'
            store.put('approval',approval)
    for plan in store.all_of('guide_plan'):
        if plan['status']=='running':
            plan['status']='failed'
            plan['results'].append({'index': len(plan['results']), 'label': 'Redémarrage du serveur',
                                    'status': 'failed', 'error': 'Le serveur a redémarré pendant le plan. Vérifiez les actions déjà effectuées.'})
            store.put('guide_plan', plan)
    yield

app = FastAPI(title='Passage — POC', version='0.1.0', lifespan=lifespan)
auth.install(app)
app.include_router(google_login.router)
app.include_router(projects.router)
app.include_router(workflows.router)
app.include_router(diagrams.router)
app.include_router(projects.dialogue_router)
app.include_router(partner_mcp.router)
app.include_router(voice.router)
app.include_router(voice_live.router)
app.include_router(voice_codex.router)
app.include_router(codex_brain.router)
app.include_router(guide.router)
app.include_router(jinko_bridge.router)
app.include_router(teams.router)
STATIC = Path(__file__).parent / 'static'
GRADBOT_ASSETS = Path(__import__('gradbot').__file__).parent / 'js_audio'

def require(role, allowed):
    if role not in allowed:
        raise HTTPException(403, 'Ce profil ne peut pas effectuer cette action dans le POC.')


def require_catalog_editor():
    """The shared catalogue belongs to the installation, not to new lab accounts."""
    if integrations.env('PASSAGE_PUBLIC_SIGNUP') == '1' and auth.current()['role'] != 'admin':
        raise HTTPException(403, 'Le catalogue commun et les réglages du laboratoire sont gérés par l’administrateur.')

def item(kind, identifier):
    result = store.get(kind, identifier)
    if result is None:
        raise HTTPException(404, 'Objet introuvable.')
    return result

def thesis(identifier, role):
    t = item('thesis', identifier)
    if role == 'company' and not t['visible']:
        raise HTTPException(404, 'Cette fiche n’est pas visible dans la bibliothèque.')
    return t

def visible_report(r, role):
    return projects.owned(r) and (role != 'company' or all((store.get('thesis', tid) or {}).get('visible') for tid in r.get('source_ids', [])))

def latest_reports(identifier, role):
    return sorted([r for r in store.all_of('report') if r.get('thesis_id') == identifier and visible_report(r, role)], key=lambda r: r['created_at'], reverse=True)

def update_run(identifier, **fields):
    with store.transaction() as c:
        run = store.get('run', identifier, c)
        run.update(fields)
        store.put('run', run, c)

def start_job(kind, label, fn, owner, metadata=None):
    run = {'id': store.uid('run_'), 'kind': kind, 'label': label, 'status': 'queued', 'created_at': store.now(),
           'ended_at': None, 'owner': owner, 'user_id': (auth.CURRENT_USER.get() or {}).get('id'), 'trace': [], 'result': None, 'error': '', **(metadata or {})}
    store.put('run', run)
    def work():
        started = time.monotonic()
        update_run(run['id'], status='running')
        def trace(message):
            with store.transaction() as c:
                current = store.get('run', run['id'], c)
                current['trace'].append({'at': store.now(), 'message': message})
                store.put('run', current, c)
        try:
            result = fn(trace)
            update_run(run['id'], status='succeeded', result=result, ended_at=store.now(), duration=round(time.monotonic() - started, 2))
        except Exception as exc:
            message = ('Réponse structurée invalide ; aucun dossier enregistré.' if isinstance(exc, ValidationError) else integrations.safe_error(exc))
            update_run(run['id'], status='failed', error=message, ended_at=store.now(), duration=round(time.monotonic() - started, 2))
            store.event('Échec de traitement', label, message)
        try:
            current = store.get('run', run['id'])
            if latitude.export_run(current):
                update_run(run['id'], latitude_export='sent')
        except Exception as exc:
            update_run(run['id'], latitude_export='failed')
            store.event('Export Latitude échoué', run['id'], integrations.safe_error(exc))
    from contextvars import copy_context
    POOL.submit(copy_context().run, work)
    return run

def select_agent(req):
    if req.agent_id:
        agent = item('agent', req.agent_id)
        if agent['role'] != req.role:
            raise HTTPException(422, 'Le rôle de l’agent ne correspond pas à la tâche.')
    else:
        agent = next((a for a in store.all_of('agent') if a['role'] == req.role and a['active']), None)
        if agent is None:
            raise HTTPException(409, 'Aucun agent actif pour ce rôle.')
    return copy.deepcopy(agent)

def prepare(req, role):
    if req.project_id:
        project = projects.get(req.project_id)
        if req.agent_id not in project['agent_ids']:
            raise HTTPException(403, 'Agent non affecté au projet.')
    agent = select_agent(req)
    if req.role == 'rapprochement':
        if not req.problem.strip():
            raise HTTPException(422, 'Décrivez un besoin pour lancer le rapprochement.')
        corpus = [t for t in store.all_of('thesis') if t['visible']]
        notices = sorted(corpus, key=lambda t: agents.rank_score(t, req.problem), reverse=True)[:25]
    else:
        if not req.thesis_id:
            raise HTTPException(422, 'Choisissez une thèse.')
        notices = [thesis(req.thesis_id, role)]
        if req.role == 'incorporation' and not req.problem.strip():
            raise HTTPException(422, 'Décrivez le besoin industriel avant de produire ce dossier.')
    if not notices:
        raise HTTPException(422, 'Aucune thèse visible à analyser. Publiez une fiche depuis le laboratoire.')
    issues = agents.control(agent, live=req.mode == 'live')
    if issues:
        raise HTTPException(409, ' ; '.join(issues))
    return agent, copy.deepcopy(notices)

def perform(req, agent, notices, role, trace):
    history = []
    if req.question:
        previous = [r for r in latest_reports(req.thesis_id, role) if r.get('project_id')==req.project_id and r['role'] == req.role and r['problem'] == req.problem]
        history = [{'question': r.get('question', ''), 'report': r['content']} for r in reversed(previous[:3])]
    content, usage = agents.execute(agent, notices, req.role, req.problem, req.mode, trace, req.question, history, req.project_id)
    report = {'id': store.uid('doc_'), 'role': req.role, 'thesis_id': req.thesis_id, 'problem': req.problem,
              'project_id': req.project_id, 'user_id': auth.current()['id'],
              'question': req.question, 'created_at': store.now(), 'mode': req.mode, 'engine': agent['engine'],
              'model': agent['model'] if req.mode == 'live' else 'Aucun — simulation', 'agent_id': agent['id'], 'agent_name': agent['name'],
              'revision': agent['revision'], 'source_ids': [t['id'] for t in notices], 'sources': [{'id': t['id'], 'url': t['source_url'], 'collected_at': t['collected_at']} for t in notices],
              'content': content, 'usage': usage, 'actual_model': usage.get('actual_model')}
    store.put('report', report)
    store.event('Dossier produit', req.thesis_id or 'Bibliothèque', agent['name'] + ' — ' + ('simulation' if req.mode == 'demo' else agent['engine'] + ' / ' + agent['model']))
    return report

@app.get('/api/health')
def health():
    return {'status': 'ok', 'name': 'Passage', 'version': '0.1.0'}

@app.get('/api/state')
@store.read_snapshot('installation_setting', 'thesis', 'report', 'visit', 'proposal',
                     'settings', 'programme', 'agent', 'project')
@integrations.configuration_snapshot()
def state(role: Role = 'lab'):
    require(role, {'lab', 'researcher', 'company', 'admin'})
    ts = [t for t in store.all_of('thesis') if role != 'company' or t['visible']]
    reports = [r for r in store.all_of('report') if visible_report(r, role)]
    visits = store.all_of('visit')
    summaries = []
    for t in ts:
        brief = sources.public_notice(t)
        brief['has_reading'] = any(r['thesis_id'] == t['id'] and r['role'] == 'lecteur' for r in reports)
        brief['visits'] = sum(v['thesis_id'] == t['id'] for v in visits)
        summaries.append(brief)
    allowed_ids = {t['id'] for t in ts}
    proposals = [p for p in store.all_of('proposal') if p['thesis_id'] in allowed_ids and projects.owned(p)]
    return {'settings': item('settings', 'main'), 'theses': summaries, 'programmes': store.all_of('programme'),
            'proposals': proposals, 'agents': [{**{k:v for k,v in a.items() if auth.current()['role']=='admin' or k not in ('context','memory','skill','connector_ids','dust_id')}, 'control': agents.control(a), 'live_control': agents.control(a, True)} for a in store.all_of('agent') if agents.visible(a, auth.current())],
            'stats': {'lab': sum(t['is_lab'] for t in ts), 'visible': sum(t['visible'] for t in ts),
                      'visits': sum(v['thesis_id'] in allowed_ids for v in visits), 'reports': len(reports),
                      'pending': sum(p['status'] == 'pending' for p in proposals)},
            'events': store.events(15) if auth.current()['role']=='admin' else [], 'oscar_mode': integrations.env('PASSAGE_OSCAR', 'demo')}

@app.get('/api/theses/{identifier}')
def get_thesis(identifier: str, role: Role = 'lab'):
    t = thesis(identifier, role)
    return {'thesis': sources.public_notice(t), 'reports': latest_reports(identifier, role),
            'proposals': [p for p in store.all_of('proposal') if p['thesis_id'] == identifier and projects.owned(p)],
            'visits': len([v for v in store.all_of('visit') if v['thesis_id'] == identifier]),
            'corrections': [c for c in store.all_of('correction') if c['thesis_id'] == identifier]}

@app.post('/api/theses/{identifier}/visit')
def visit(identifier: str, role: Role = 'company'):
    require(role, {'company'})
    thesis(identifier, role)
    store.put('visit', {'id': 'velia:' + identifier, 'company': 'Vélia Mobilité — entreprise fictive', 'thesis_id': identifier, 'at': store.now()})
    return {'ok': True}

@app.patch('/api/theses/{identifier}/visibility')
def visibility(identifier: str, body: VisibilityInput, role: Role = 'lab'):
    require_catalog_editor()
    require(role, {'lab'})
    t = thesis(identifier, role)
    t.update(visible=body.visible, publication_at=store.now(), publication_actor='Directeur — rôle joué dans le POC')
    store.put('thesis', t)
    store.event('Fiche publiée' if body.visible else 'Fiche retirée', identifier, 'Décision humaine dans le POC')
    return sources.public_notice(t)

@app.patch('/api/theses/{identifier}/correction')
def correction(identifier: str, body: CorrectionInput, role: Role = 'researcher'):
    require_catalog_editor()
    require(role, {'researcher', 'lab'})
    t = thesis(identifier, role)
    store.put('correction', {'id': store.uid('corr_'), 'thesis_id': identifier, 'previous': t.get('correction', ''), 'summary': body.summary, 'actor': role, 'at': store.now()})
    t.update(correction=body.summary, correction_at=store.now())
    store.put('thesis', t)
    store.event('Résumé corrigé', identifier, 'Correction humaine conservée séparément du résumé source')
    return sources.public_notice(t)

@app.post('/api/import')
def import_theses(body: ImportInput, role: Role = 'lab'):
    require_catalog_editor()
    require(role, {'lab'})
    return start_job('import', 'Import theses.fr — ' + body.query,
                     lambda trace: sources.import_lab(body.query, body.lab_filter, body.limit, trace), role)

@app.patch('/api/laboratory')
def laboratory(body: dict, role: Role = 'lab'):
    require_catalog_editor()
    require(role, {'lab'})
    settings = item('settings', 'main')
    for key in ['lab_name', 'lab_short', 'city']:
        if key in body:
            if not isinstance(body[key], str) or not 1 <= len(body[key]) <= 180:
                raise HTTPException(422, 'Valeur de laboratoire invalide.')
            settings[key] = body[key]
    store.put('settings', settings)
    store.event('Laboratoire configuré', settings['lab_short'])
    return settings

@app.post('/api/runs')
def create_run(req: RunInput, role: Role = 'lab'):
    require(role, {'lab', 'researcher', 'company', 'admin'})
    if role == 'company' and req.role in ('lecteur', 'opportunite'):
        raise HTTPException(403, 'Ce dossier appartient au parcours laboratoire.')
    agent, notices = prepare(req, role)
    return start_job('agent', agent['name'], lambda trace: perform(req, agent, notices, role, trace), role,
                     {'agent_snapshot': agent, 'source_ids': [t['id'] for t in notices], 'mode': req.mode,
                      'model': agent['model'] if req.mode == 'live' else 'Aucun — simulation', 'engine': agent['engine']})

@app.post('/api/read-batch')
def read_batch(body: dict, role: Role = 'lab'):
    require(role, {'lab'})
    mode = body.get('mode', 'demo')
    done = {r['thesis_id'] for r in store.all_of('report') if r['role'] == 'lecteur' and r['mode'] == mode}
    targets = [t for t in store.all_of('thesis') if t['is_lab'] and t['id'] not in done]
    base = RunInput(role='lecteur', mode=mode, thesis_id=targets[0]['id'] if targets else None)
    agent = select_agent(base)
    issues = agents.control(agent, mode == 'live')
    if issues:
        raise HTTPException(409, ' ; '.join(issues))
    def batch(trace):
        result = {'succeeded': 0, 'failed': 0, 'errors': []}
        for index, t in enumerate(targets):
            trace(f"Lecture {index + 1}/{len(targets)} : {t['title'][:70]}")
            try:
                req = RunInput(role='lecteur', mode=mode, thesis_id=t['id'])
                perform(req, agent, [t], role, trace)
                result['succeeded'] += 1
            except Exception as exc:
                result['failed'] += 1
                result['errors'].append({'id': t['id'], 'message': integrations.safe_error(exc)})
        return result
    return start_job('batch', f'Lecture de {len(targets)} thèses du laboratoire', batch, role,
                     {'agent_snapshot': agent, 'source_ids': [t['id'] for t in targets], 'mode': mode})

@app.get('/api/runs')
def list_runs(role: Role = 'lab'):
    runs = [r for r in store.all_of('run') if projects.owned(r) and (role != 'company' or (r['owner'] == 'company' and visible_report(r, role)))]
    return sorted([{k: v for k, v in r.items() if k not in ['result', 'agent_snapshot']} for r in runs], key=lambda r: r['created_at'], reverse=True)[:100]

@app.get('/api/runs/{identifier}')
def get_run(identifier: str, role: Role = 'lab'):
    r = item('run', identifier)
    if not projects.owned(r):
        raise HTTPException(404, 'Exécution non accessible.')
    if not r.get('project_id') and role == 'company' and (r['owner'] != 'company' or not visible_report(r, role)):
        raise HTTPException(404, 'Exécution non accessible.')
    return r

def markdown(r):
    c = r['content']
    lines = ['# ' + agents.ROLES[r['role']][0] + ' — Passage', '',
             f"Mode : {'SIMULATION — aucun LLM appelé' if r['mode'] == 'demo' else 'Appel réel'}", f"Agent : {r['agent_name']} · révision {r['revision']} · {r['engine']} · {r['model']}",
             'Date : ' + r['created_at'], '', c['summary']]
    for title, value in [('Pourquoi cette thèse', c['fit']), ('Ce qui est documenté', c['demonstrated']),
                         ('À vérifier', c['checks']), ('Contacts', c['contacts']),
                         ('Confiance', c['confidence']), ('Incertitudes', c['uncertainty']),
                         ('Maturité', '\n'.join(c['maturity'].values())), ('Droits', c['rights']),
                         ('Verdict', c['verdict']), ('Application', c['application']), ('Marché', c['market']),
                         ('Travaux proches', c['competition']), ('Étapes', c['steps']), ('Estimations', c['estimates'])]:
        lines += ['', '## ' + title, '', '\n'.join('- ' + v for v in value) if isinstance(value, list) else value]
    lines += ['', '## Sources', ''] + ['- ' + s['url'] + ' (collectée le ' + s['collected_at'] + ')' for s in r['sources']]
    for m in c['matches']:
        lines += ['', f"- {m['thesis_id']} — {m['score']}/100 : {m['reason']}"]
    return '\n'.join(lines)

@app.get('/api/reports/{identifier}/export')
def export_report(identifier: str, role: Role = 'lab'):
    r = item('report', identifier)
    if not visible_report(r, role):
        raise HTTPException(404, 'Dossier non accessible.')
    return Response(markdown(r), media_type='text/markdown', headers={'Content-Disposition': f'attachment; filename="passage-{r["role"]}-{identifier}.md"'})

@app.get('/api/laboratory/export')
def export_lab(role: Role = 'lab'):
    require(role, {'lab'})
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Identifiant', 'Titre', 'Auteur', 'Statut', 'Visible', 'Entreprises distinctes', 'Dossiers'])
    for t in store.all_of('thesis'):
        if t['is_lab']:
            values = [t['id'], t['title'], ', '.join(a['name'] for a in t['authors']), t['status'], str(t['visible']),
                      str(sum(v['thesis_id'] == t['id'] for v in store.all_of('visit'))), str(len(latest_reports(t['id'], 'lab')))]
            writer.writerow(["'" + v if v.startswith(('=', '+', '-', '@')) else v for v in values])
    return Response('\ufeff' + output.getvalue(), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="passage-indicateurs.csv"'})

@app.get('/api/agents/creator/blueprint/{agent_role}')
def agent_blueprint(agent_role: str, role: Role = 'admin'):
    require(role, {'admin'})
    if agent_role not in agents.ROLES:
        raise HTTPException(404, 'Rôle métier inconnu.')
    name, mandate = agents.ROLES[agent_role]
    return {'version': creator.VERSION, 'steps': creator.STEPS,
            'agent': creator.blueprint(agent_role, name, mandate, 'auto')}

@app.post('/api/agents/creator/check')
def check_agent(body: AgentInput, role: Role = 'admin'):
    require(role, {'admin'})
    return {'issues': agents.control(body.model_dump()), 'version': creator.VERSION}

@app.get('/api/agents/{identifier}')
def get_agent(identifier: str, role: Role = 'admin'):
    a = item('agent', identifier)
    if not agents.visible(a, auth.current()):
        raise HTTPException(404, 'Agent introuvable.')
    if role != 'admin' and a.get('owner_id') != auth.current()['id']:
        raise HTTPException(403, 'Administration requise pour ouvrir un agent partagé.')
    return {'agent': a, 'assembled': agents.assembled(a), 'control': agents.control(a), 'live_control': agents.control(a, True),
            'revisions': [r for r in store.all_of('revision') if r['agent_id'] == identifier]}

def save_agent(body, identifier=None):
    previous = store.get('agent', identifier) if identifier else None
    a = body.model_dump()
    if previous and previous.get('creator_version') and not a.get('creator_version'):
        raise HTTPException(422, 'La méthode de création de cet agent ne peut pas être retirée.')
    if a['active'] and (a.get('creator_version') or a['role'] == 'research_task'):
        missing = agents.control(a)
        if missing:
            raise HTTPException(422, 'Agent incomplet : ' + ' ; '.join(missing))
    a.update(id=identifier or store.uid('agent_'), revision=(previous or {}).get('revision', 0) + 1)
    if previous and previous.get('owner_id'):
        a['owner_id'] = previous['owner_id']
    for cid in a['connector_ids']:
        item('connector', cid)
    with store.transaction() as c:
        if a['active'] and a['role'] != 'research_task':
            for other in store.all_of('agent'):
                if (other['role'] == a['role'] and other['id'] != a['id'] and other['active']
                        and other.get('owner_id') == a.get('owner_id')):
                    other['active'] = False
                    store.put('agent', other, c)
        store.put('agent', a, c)
        store.put('revision', {**a, 'id': a['id'] + ':' + str(a['revision']), 'agent_id': a['id'], 'saved_at': store.now()}, c)
    store.event('Harnais enregistré', a['name'], 'Révision ' + str(a['revision']))
    return a

@app.post('/api/agents')
def create_agent(body: AgentInput, role: Role = 'admin'):
    require(role, {'admin'})
    return save_agent(body)

@app.put('/api/agents/{identifier}')
def update_agent(identifier: str, body: AgentInput, role: Role = 'admin'):
    require(role, {'admin'})
    if not agents.visible(store.get('agent', identifier), auth.current()):
        raise HTTPException(404, 'Agent introuvable.')
    return save_agent(body, identifier)

@app.get('/api/agents/{identifier}/export/{target}')
def export_agent(identifier: str, target: str, role: Role = 'admin'):
    a = item('agent', identifier)
    if not agents.visible(a, auth.current()):
        raise HTTPException(404, 'Agent introuvable.')
    if role != 'admin' and a.get('owner_id') != auth.current()['id']:
        raise HTTPException(403, 'Administration requise pour exporter un agent partagé.')
    if target == 'pipelex':
        return Response(agents.method(a), media_type='text/plain', headers={'Content-Disposition': f'attachment; filename="{a["role"]}.mthds"'})
    if target == 'dust':
        return integrations.dust_export(a, agents.assembled(a))
    if target == 'json':
        return {k: v for k, v in a.items() if not k.startswith('dust_')}
    raise HTTPException(404, 'Format inconnu.')

@app.post('/api/agents/{identifier}/publish-dust')
def publish_dust(identifier: str, role: Role = 'admin'):
    require(role, {'admin'})
    a = copy.deepcopy(item('agent', identifier))
    if not agents.visible(a, auth.current()):
        raise HTTPException(404, 'Agent introuvable.')
    def publish(trace):
        trace('Projection de la définition locale dans Dust')
        remote_id = integrations.dust_publish(a, agents.assembled(a))
        with store.transaction() as c:
            current = store.get('agent', identifier, c)
            if current['revision'] == a['revision']:
                current.update(dust_id=remote_id, dust_revision=a['revision'])
                store.put('agent', current, c)
            else:
                raise integrations.IntegrationError('La définition a changé pendant la publication. Agent Dust créé : ' + remote_id + '. Republiez la dernière révision.')
        store.event('Agent publié dans Dust', a['name'], 'Révision ' + str(a['revision']))
        return {'dust_id': remote_id, 'revision': a['revision']}
    return start_job('dust', 'Publication Dust — ' + a['name'], publish, role)

@app.get('/api/connections')
def connections(role: Role = 'admin'):
    require(role, {'admin'})
    return {**integrations.statuses(), 'connectors': store.all_of('connector')}

@app.get('/api/local-models')
def local_models(role: Role = 'admin'):
    require(role, {'admin'})
    try:
        response = integrations.http('GET', integrations.env('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/') + '/api/tags', timeout=(3, 5))
        return {'models': [{'name': m['name'], 'size': m.get('size')} for m in response.get('models', [])]}
    except Exception as exc:
        raise HTTPException(502, integrations.safe_error(exc))

@app.post('/api/connections/settings')
def connection_settings(body: dict, role: Role = 'admin'):
    require(role, {'admin'})
    body = dict(body)
    persist = body.pop('persist_settings', False)
    if not isinstance(persist, bool):
        raise HTTPException(422, 'Choix de conservation invalide.')
    if any(k not in integrations.SETTING_NAMES for k in body):
        raise HTTPException(422, 'Paramètre inconnu.')
    for k, v in body.items():
        if not isinstance(v, str) or len(v) > 4000:
            raise HTTPException(422, 'Valeur invalide.')
        if k.endswith('BASE_URL') or k in ('OSCAR_URL', 'LATITUDE_INGEST_URL'):
            if v and urlparse(v).scheme not in ('http', 'https'):
                raise HTTPException(422, 'Adresse HTTP(S) requise.')
        if k == 'PASSAGE_OSCAR' and v not in ('demo', 'mcp'):
            raise HTTPException(422, 'Mode Oscar invalide.')
        if k == 'LATITUDE_ENABLED' and v not in ('on', 'off'):
            raise HTTPException(422, 'Mode Latitude invalide.')
    if persist:
        integrations.persist_settings(body)
    integrations.SESSION_SECRETS.update(body)
    store.event('Connexions configurées', 'Session locale', 'Valeurs secrètes exclues du journal')
    return integrations.statuses()

@app.post('/api/connectors')
def create_connector(body: ConnectorInput, role: Role = 'admin'):
    require(role, {'admin'})
    if urlparse(body.url).scheme not in ('http', 'https'):
        raise HTTPException(422, 'Adresse HTTP(S) requise.')
    return store.put('connector', {'id': store.uid('mcp_'), **body.model_dump()})

@app.put('/api/connectors/{identifier}')
def update_connector(identifier: str, body: ConnectorInput, role: Role = 'admin'):
    require(role, {'admin'})
    item('connector', identifier)
    if urlparse(body.url).scheme not in ('http', 'https'):
        raise HTTPException(422, 'Adresse HTTP(S) requise.')
    return store.put('connector', {'id': identifier, **body.model_dump()})

@app.post('/api/connectors/{identifier}/test')
def test_connector(identifier: str, role: Role = 'admin'):
    require(role, {'admin'})
    c = item('connector', identifier)
    return start_job('mcp', 'Test MCP — ' + c['name'], lambda trace: integrations.mcp(c), role)

@app.post('/api/programmes')
def create_programme(body: ProgrammeInput, role: Role = 'company'):
    require(role, {'company'})
    if integrations.env('PASSAGE_OSCAR', 'demo') != 'demo':
        raise HTTPException(409, 'La création de programmes reste dans Oscar en mode connecté.')
    return store.put('programme', {'id': store.uid('prog_'), **body.model_dump(), 'source': 'demo', 'company': item('settings', 'main')['company']})

@app.post('/api/programmes/sync')
def sync_programmes(role: Role = 'company'):
    require(role, {'company', 'admin'})
    if integrations.env('PASSAGE_OSCAR', 'demo') != 'mcp':
        return {'mode': 'demo', 'programmes': store.all_of('programme')}
    def work(trace):
        raw = integrations.oscar('oscar_projets')
        rows = raw if isinstance(raw, list) else raw.get('items', raw.get('projects', []))
        for p in rows:
            context = integrations.oscar('oscar_contexte', {'project_id': p['id']})
            store.put('programme', {'id': 'oscar-' + str(p['id']), 'oscar_id': p['id'], 'name': p.get('name') or p.get('nom'),
                                    'description': (context if isinstance(context, str) else json.dumps(context, ensure_ascii=False))[:12000], 'source': 'mcp'})
        return {'count': len(rows)}
    return start_job('oscar', 'Lecture des programmes Oscar', work, role)

@app.post('/api/proposals')
def propose(body: ProposalInput, role: Role = 'company'):
    require(role, {'company'})
    t = thesis(body.thesis_id, role)
    programme = item('programme', body.programme_id)
    report = item('report', body.report_id)
    if report['thesis_id'] != t['id'] or report['role'] != 'incorporation' or not visible_report(report, role):
        raise HTTPException(422, 'Un dossier d’incorporation de cette thèse est requis.')
    with store.transaction() as c:
        existing = next((p for p in store.all_of('proposal') if projects.owned(p) and p['thesis_id'] == t['id'] and p['programme_id'] == programme['id'] and p['status'] != 'rejected'), None)
        if existing:
            return existing
        p = store.put('proposal', {'id': store.uid('prop_'), 'thesis_id': t['id'], 'thesis_title': t['title'], 'programme_id': programme['id'],
                                   'user_id': auth.current()['id'], 'project_id': report.get('project_id'),
                                   'programme_name': programme['name'], 'report_id': report['id'], 'status': 'pending', 'created_at': store.now(),
                                   'note': markdown(report), 'source': programme['source'], 'city': 'Amiens' if t['is_lab'] else 'À confirmer auprès du laboratoire'}, c)
    store.event('Thèse proposée', t['id'], programme['name'])
    return p

@app.post('/api/proposals/{identifier}/decision')
def decide(identifier: str, body: DecisionInput, role: Role = 'company'):
    require(role, {'company'})
    with store.transaction() as c:
        p = store.get('proposal', identifier, c)
        if not p or not projects.owned(p):
            raise HTTPException(404, 'Proposition introuvable.')
        thesis(p['thesis_id'], role)
        if p['status'] == body.decision:
            return p
        if p['status'] != 'pending':
            raise HTTPException(409, 'Une décision a déjà été prise ou sa livraison doit être vérifiée.')
        if body.decision == 'rejected':
            p.update(status='rejected', decided_at=store.now())
            store.put('proposal', p, c)
        else:
            programme = store.get('programme', p['programme_id'], c)
            if programme['source'] == 'mcp':
                p['status'] = 'sending'
                store.put('proposal', p, c)
    if body.decision == 'accepted':
        if p['source'] == 'mcp':
            try:
                result = integrations.oscar('oscar_deposer_avis', {'entity_type': 'Project', 'entity_id': programme['oscar_id'], 'project_id': programme['oscar_id'],
                                                                  'type': 'proposition', 'titre': 'Thèse proposée : ' + p['thesis_title'], 'contenu': p['note']})
                p['remote_result'] = result
            except Exception as exc:
                p.update(status='delivery_unknown', error=integrations.safe_error(exc))
                store.put('proposal', p)
                raise HTTPException(502, p['error'])
        with store.transaction() as c:
            p.update(status='accepted', decided_at=store.now())
            store.put('proposal', p, c)
            store.put('note', {'id': p['id'], 'user_id': p.get('user_id'), 'project_id': p.get('project_id'), 'programme_id': p['programme_id'], 'content': p['note'], 'at': store.now(), 'source': p['source']}, c)
        notes = [n for n in store.all_of('note') if n['source'] == 'demo']
        path = store.db_path().parent / 'notes_demo.json'
        path.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding='utf-8')
    store.event('Proposition acceptée' if body.decision == 'accepted' else 'Proposition refusée', p['thesis_id'], p['programme_name'])
    return p

@app.get('/api/notes')
def notes(role: Role = 'company'):
    require(role, {'company', 'admin'})
    return [n for n in store.all_of('note') if projects.owned(n)]

@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')

app.mount('/static', StaticFiles(directory=STATIC, check_dir=False), name='static')
app.mount('/voice-assets', StaticFiles(directory=GRADBOT_ASSETS), name='voice-assets')
