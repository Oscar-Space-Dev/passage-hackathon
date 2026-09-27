import time
import tomllib

from passage import integrations, latitude, store


def task_for(client):
    project = client.post('/api/projects', json={
        'name': 'Projet protocole',
        'objective': 'Définir un protocole expérimental traçable.'}).json()
    task = client.post('/api/work/projects/'+project['id'], json={
        'type_id': 'r1-experiment-design', 'brief': 'Comparer deux conditions avec contrôles et mesures.'})
    assert task.status_code == 200, task.text
    return project, task.json()


def scene():
    return [
        {'id': 'step-a', 'type': 'rectangle'},
        {'id': 'label-a', 'type': 'text', 'containerId': 'step-a', 'text': 'Préparer témoins'},
        {'id': 'step-b', 'type': 'diamond'},
        {'id': 'label-b', 'type': 'text', 'containerId': 'step-b', 'text': 'Signal exploitable ?'},
        {'id': 'arrow-a', 'type': 'arrow', 'startBinding': {'elementId': 'step-a'},
         'endBinding': {'elementId': 'step-b'}},
    ]


def wait(client, run_id):
    for _ in range(80):
        run = client.get('/api/runs/'+run_id).json()
        if run['status'] not in ('queued', 'running'):
            return run
        time.sleep(.05)
    raise AssertionError('Formalisation encore en cours')


def test_diagram_versions_conflict_and_safe_export(client):
    _, task = task_for(client)
    base = '/api/work/tasks/'+task['id']+'/diagrams'
    created = client.post(base, json={'title': 'Essai témoin'})
    assert created.status_code == 200, created.text
    did = created.json()['id']
    saved = client.put(base+'/'+did, json={'title': 'Essai témoin',
        'expected_version': 1, 'elements': scene(), 'app_state': {'viewBackgroundColor': '#fff'}})
    assert saved.status_code == 200, saved.text
    assert saved.json()['version'] == 2
    assert len(client.get(base+'/'+did+'/versions').json()) == 2
    assert client.put(base+'/'+did, json={'title': 'Autre', 'expected_version': 1,
        'elements': scene()}).status_code == 409
    assert client.put(base+'/'+did, json={'title': 'Autre', 'expected_version': 2,
        'elements': [{'id': 'image', 'type': 'image'}]}).status_code == 422
    exported = client.get(base+'/'+did+'/export')
    assert exported.status_code == 200
    assert exported.json()['type'] == 'excalidraw'
    assert exported.json()['files'] == {}
    assert len(client.get('/api/work/tasks/'+task['id']).json()['diagrams']) == 1


def test_agent_formalizes_saved_graph_as_reviewable_documents(client, monkeypatch):
    project, task = task_for(client)
    agent_id = project['coordinator_id']
    base = '/api/work/tasks/'+task['id']+'/diagrams'
    created = client.post(base, json={'title': 'Protocole mesuré'}).json()
    diagram = client.put(base+'/'+created['id'], json={'title': created['title'],
        'expected_version': 1, 'elements': scene()}).json()

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        assert context['graph']['nodes'][0]['label'] == 'Préparer témoins'
        assert context['graph']['edges'][0]['to'] == 'step-b'
        return ({'purpose': 'Préparer un essai comparatif.', 'steps': [
            {'node_id': 'step-a', 'action': 'Préparer témoins', 'inputs': [],
             'outputs': ['témoins'], 'checks': ['Vérifier les lots']},
            {'node_id': 'step-b', 'action': 'Vérifier le signal', 'inputs': ['témoins'],
             'outputs': ['décision'], 'checks': ['Définir le seuil']}],
            'assumptions': ['Seuil à fixer'], 'ambiguities': ['Branche non dessinée'],
            'validation': ['Relire avec le directeur']}, {'input_tokens': 20})

    monkeypatch.setattr(integrations, 'direct', direct)
    for target, expected_format in [('protocol', 'markdown'), ('pipelex', 'mthds')]:
        response = client.post(base+'/'+created['id']+'/formalize', json={
            'agent_id': agent_id, 'target': target, 'expected_version': diagram['version']})
        assert response.status_code == 200, response.text
        run = wait(client, response.json()['id'])
        assert run['status'] == 'succeeded', run
        doc = client.get('/api/work/tasks/'+task['id']+'/documents/'+run['result']['document_id']).json()
        assert doc['format'] == expected_format
        assert doc['source_entry_id']
        entry = store.get('work_entry', doc['source_entry_id'])
        assert entry['diagram_version'] == 2
        assert entry['diagram_sha256'] == diagram['sha256']
        if target == 'protocol':
            assert 'Branche non dessinée' in doc['content']
            assert 'step-a → step-b' in doc['content']
        else:
            parsed = tomllib.loads(doc['content'])
            assert parsed['pipe'][parsed['main_pipe']]['type'] == 'PipeLLM'
            assert 'REPLACE_WITH_APPROVED_MODEL' in doc['content']


def test_latitude_export_is_metadata_only(client, monkeypatch):
    calls = []
    monkeypatch.setattr(integrations, 'env', lambda name, default='': {
        'LATITUDE_ENABLED': 'on', 'LATITUDE_INGEST_URL': 'http://127.0.0.1:3002',
        'LATITUDE_PROJECT_SLUG': 'passage', 'LATITUDE_API_KEY': 'secret-token',
    }.get(name, default))

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return type('Response', (), {'status_code': 202})()

    monkeypatch.setattr(latitude.requests, 'post', post)
    assert latitude.export_run({'id': 'run_test', 'kind': 'diagram_formalize',
        'status': 'succeeded', 'created_at': '2026-09-26T12:00:00+00:00',
        'ended_at': '2026-09-26T12:00:01+00:00', 'work_id': 'work_1',
        'result': {'secret': 'PRIVATE PROMPT'}})
    assert calls[0][0] == 'http://127.0.0.1:3002/v1/traces'
    assert calls[0][1]['headers']['X-Latitude-Project'] == 'passage'
    assert 'PRIVATE PROMPT' not in str(calls[0][1]['json'])
