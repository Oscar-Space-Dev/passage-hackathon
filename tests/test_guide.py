import time
import threading
import json

from passage import codex_brain, integrations, projects, store


def action(kind, **fields):
    row = dict(kind=kind, label=kind, project_id='', name='', objective='', context='',
               agent_ids=[], source_ids=[], type_id='', brief='', task_id='', agent_id='', message='',
               research_kind='', note_title='', note_content='', thesis_id='', service='', tool='',
               arguments_json='', diagram_id='', diagram_title='', target='')
    row.update(fields)
    return row


def test_guide_requires_approval_and_executes_real_project_actions(client, monkeypatch):
    class Brain:
        def complete(self, model, prompt, context, schema):
            assert context['messages'][-1]['text'] == 'Je prépare une revue de littérature.'
            return {'reply': 'Je peux préparer votre espace de travail.', 'profile': 'L’utilisateur prépare une revue de littérature.', 'questions': [], 'human_steps': [], 'actions': [
                action('create_project', label='Créer le projet', name='Ma recherche',
                       objective='Préparer une revue de littérature sur la question étudiée.'),
                action('create_task', label='Ouvrir la revue', project_id='new',
                       type_id='r1-literature', brief='Lire et classer le corpus de ma revue de littérature.'),
            ]}, {'actual_model': 'gpt-6-luna'}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    answer = client.post('/api/guide/messages', json={'text': 'Je prépare une revue de littérature.'})
    assert answer.status_code == 200, answer.text
    plan = answer.json()['plan']
    assert plan['status'] == 'pending' and len(plan['actions']) == 2
    assert 'revue de littérature' in client.get('/api/guide').json()['profile']
    assert not store.all_of('project')
    assert not store.all_of('work_item')

    approved = client.post('/api/guide/plans/' + plan['id'] + '/approve')
    assert approved.status_code == 200, approved.text
    for _ in range(100):
        state = client.get('/api/guide').json()
        if state['plan']['status'] not in ('running', 'pending'):
            break
        time.sleep(.02)
    assert state['plan']['status'] == 'completed', state
    assert len(state['plan']['results']) == 2
    assert len(store.all_of('project')) == 1
    assert len(store.all_of('work_item')) == 1
    assert client.post('/api/guide/plans/' + plan['id'] + '/approve').status_code == 409


def test_guide_rejects_unowned_project_in_model_plan(client, monkeypatch):
    class Brain:
        calls = 0
        def complete(self, *_):
            self.calls += 1
            return {'reply': 'Je vais le faire.', 'profile': '', 'questions': [], 'human_steps': [], 'actions': [
                action('set_objective', project_id='prj_foreign',
                       objective='Un autre objectif de recherche détaillé.')
            ]}, {}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': []})
    brain = Brain()
    monkeypatch.setattr(codex_brain, 'client', lambda _: brain)
    result = client.post('/api/guide/messages', json={'text': 'Change l’objectif de ce projet.'})
    assert result.status_code == 200
    assert result.json()['plan'] is None
    assert 'plan fiable' in result.json()['message']['text']
    assert brain.calls == 2
    assert not store.all_of('guide_plan')


def wait_plan(client, terminal):
    for _ in range(150):
        plan = client.get('/api/guide').json()['plan']
        if plan and plan['status'] in terminal:
            return plan
        time.sleep(.02)
    raise AssertionError('Le plan n’a pas atteint son état attendu.')


def test_marguerite_creates_v4_agent_only_after_approval_and_keeps_it_private(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Thèse personnelle', 'objective': 'Produire une revue critique de mes articles.'}).json()
    spec = {
        'name': 'Revue critique', 'role': 'research_task',
        'mandate': 'Lire les articles fournis et rédiger une synthèse critique sourcée.',
        'skill': ('1. Cadrer le corpus et la question.\n2. Vérifier les sources.\n'
                  '3. Proposer un plan à valider.\n4. Rédiger avec citations.\n'
                  '5. Vérifier les affirmations et limites.\n6. Livrer le brouillon pour relecture.'),
        'context': 'Revue de littérature de la thèse, limitée aux articles du projet.',
        'trigger': 'Demande de revue critique sur une tâche R1 du projet.',
        'reads': 'Articles attachés à la tâche et notes que le doctorant autorise.',
        'boundaries': 'Le doctorant choisit le corpus et valide les interprétations.',
        'checkpoint': 'Faire valider le plan puis la synthèse avant tout usage dans la thèse.',
        'deliverables': 'Brouillon sourcé avec incertitudes et pistes de vérification.',
        'tools': ['work.read'], 'work_specialties': ['r1-literature'],
        'provider': 'codex', 'model': 'auto', 'engine': 'direct',
    }

    class Brain:
        def complete(self, *_):
            return {'reply': 'Je propose de créer ce spécialiste puis de le tester.',
                    'profile': '', 'questions': [], 'human_steps': [],
                    'actions': [action('create_agent', label='Créer Revue critique',
                        project_id=project['id'], arguments_json=json.dumps(spec, ensure_ascii=False))]
                    }, {'actual_model': 'gpt-6-luna'}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': []})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    proposed = client.post('/api/guide/messages', json={
        'text': 'Crée un agent pour ma revue de littérature.', 'project_id': project['id']})
    assert proposed.status_code == 200, proposed.text
    plan = proposed.json()['plan']
    assert plan['status'] == 'pending'
    assert not [a for a in store.all_of('agent') if a.get('owner_id')]
    assert client.post('/api/guide/plans/' + plan['id'] + '/approve').status_code == 200
    finished = wait_plan(client, {'completed', 'failed'})
    assert finished['status'] == 'completed', finished
    agent_id = finished['results'][0]['result']['agent_id']
    agent = store.get('agent', agent_id)
    assert agent['creator_version'].startswith('super-skill-creator-v4')
    assert agent['active'] and agent['provider'] == 'codex' and agent['owner_id']
    assert agent_id in client.get('/api/projects/' + project['id']).json()['agent_ids']
    assert client.get('/api/agents/' + agent_id + '/export/pipelex').status_code == 200

    from fastapi.testclient import TestClient
    from passage.main import app
    with TestClient(app) as outsider:
        outsider.post('/api/auth/register', json={
            'email': 'other@example.test', 'name': 'Autre personne',
            'password': 'test-password-456', 'account_type': 'researcher'})
        assert outsider.get('/api/agents/' + agent_id).status_code == 404
        assert outsider.get('/api/agents/' + agent_id + '/export/pipelex').status_code == 404
        assert agent_id not in [a['id'] for a in outsider.get('/api/state').json()['agents']]


def test_marguerite_refuses_incomplete_agent_without_saving(client, monkeypatch):
    class Brain:
        def complete(self, *_):
            return {'reply': 'Je vais créer un agent.', 'profile': '', 'questions': [],
                    'human_steps': [], 'actions': [action('create_agent', arguments_json=json.dumps({
                        'name': 'Agent vague', 'role': 'research_task',
                        'mandate': 'Faire toutes les tâches de recherche à ma place.',
                        'skill': 'Un skill sans contrôle ni étapes.'}))]}, {}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': []})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    result = client.post('/api/guide/messages', json={'text': 'Crée un agent vague.'})
    assert result.status_code == 200
    assert result.json()['plan'] is None
    assert not [a for a in store.all_of('agent') if a.get('owner_id')]


def test_marguerite_uses_selected_project_and_records_note_with_agent_provenance(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Projet sélectionné', 'objective': 'Préparer un protocole expérimental documenté.'}).json()
    task = client.post('/api/work/projects/'+project['id'], json={
        'type_id': 'r1-experiment-design', 'brief': 'Comparer deux conditions et leurs témoins.'}).json()

    class Brain:
        def complete(self, model, prompt, context, schema):
            assert context['selected_project_id'] == project['id']
            assert context['current_view'] == 'work'
            assert any(w['id'] == task['id'] for w in context['tasks'])
            return {'reply': 'Je peux consigner votre méthode dans le travail existant.',
                'profile': '', 'questions': [], 'human_steps': ['Valider le protocole avant l’essai.'],
                'actions': [action('add_task_note', label='Consigner la méthode', project_id=project['id'],
                    task_id=task['id'], note_title='Méthode envisagée',
                    note_content='Comparer les conditions A et B avec un témoin.')]
            }, {'actual_model': model}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    result = client.post('/api/guide/messages', json={
        'text': 'Consigne ma méthode dans cette tâche.', 'project_id': project['id'], 'view': 'work'})
    assert result.status_code == 200, result.text
    plan = result.json()['plan']
    assert plan['human_steps'] == ['Valider le protocole avant l’essai.']
    assert not store.all_of('work_entry')
    assert client.post('/api/guide/plans/'+plan['id']+'/approve').status_code == 200
    finished = wait_plan(client, {'needs_review'})
    assert finished['results'][0]['status'] == 'done'
    entries = store.all_of('work_entry')
    assert len(entries) == 1 and entries[0]['origin'] == 'marguerite'
    assert entries[0]['work_id'] == task['id']


def test_marguerite_follows_real_background_mission_before_claiming_completion(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Mission en cours', 'objective': 'Examiner un besoin de recherche concret.'}).json()
    release = threading.Event()

    class Brain:
        def complete(self, model, prompt, context, schema):
            return {'reply': 'Je vais lancer la mission après votre validation.', 'profile': '',
                'questions': [], 'human_steps': [], 'actions': [action('start_mission',
                    label='Lancer la mission', project_id=project['id'],
                    message='Examiner le besoin et produire un dossier sourcé.')]
            }, {'actual_model': model}

    def mission(*_):
        assert release.wait(4)
        return {'status': 'completed'}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    monkeypatch.setattr(projects, 'coordinate', mission)
    proposed = client.post('/api/guide/messages', json={
        'text': 'Lance une mission sur ce projet.', 'project_id': project['id']}).json()['plan']
    assert client.post('/api/guide/plans/'+proposed['id']+'/approve').status_code == 200
    running = wait_plan(client, {'awaiting_runs'})
    assert running['results'][0]['status'] == 'running'
    release.set()
    finished = wait_plan(client, {'completed'})
    assert finished['results'][0]['status'] == 'succeeded'
    assert finished['results'][0]['run_status'] == 'succeeded'


def test_marguerite_runs_bounded_battery_calculation_after_approval(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Calcul thermique', 'objective': 'Calculer une évolution thermique de batterie.'}).json()
    parameters = {'current_a': 10, 'resistance_ohm': .2, 'heat_capacity_j_per_k': 1000,
        'cooling_w_per_k': 2, 'ambient_c': 20, 'initial_c': 20, 'duration_s': 60, 'step_s': 1}

    class Brain:
        def complete(self, model, prompt, context, schema):
            return {'reply': 'Je peux lancer le modèle thermique avec vos huit paramètres.',
                'profile': '', 'questions': [], 'human_steps': ['Comparer la courbe à des mesures.'],
                'actions': [action('compute_battery', label='Calculer la courbe',
                    project_id=project['id'], arguments_json=json.dumps(parameters))]
            }, {'actual_model': model}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    proposed = client.post('/api/guide/messages', json={
        'text': 'Calcule avec les paramètres fournis.', 'project_id': project['id']}).json()['plan']
    assert not store.all_of('research')
    assert client.post('/api/guide/plans/'+proposed['id']+'/approve').status_code == 200
    finished = wait_plan(client, {'needs_review'})
    artifact = store.get('research', finished['results'][0]['result']['research_id'])
    assert artifact['status'] == 'computed'
    assert artifact['simulation']['parameters'] == parameters


def test_marguerite_rejects_unconnected_mcp_tool(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Outils externes', 'objective': 'Lire le catalogue des services connectés.'}).json()

    class Brain:
        def complete(self, model, prompt, context, schema):
            return {'reply': 'Je vais appeler le service.', 'profile': '', 'questions': [],
                'human_steps': [], 'actions': [action('mcp_call', project_id=project['id'],
                    service='dust', tool='outil_non_accorde', arguments_json='{}')]
            }, {'actual_model': model}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    result = client.post('/api/guide/messages', json={
        'text': 'Utilise Dust.', 'project_id': project['id']})
    assert result.status_code == 200
    assert result.json()['plan'] is None
    assert not store.all_of('approval')


def test_marguerite_repairs_invalid_plan_before_presenting_it(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Projet réel', 'objective': 'Préparer une note de recherche sur le sujet.'}).json()

    class Brain:
        calls = 0
        def complete(self, model, prompt, context, schema):
            self.calls += 1
            if self.calls == 1:
                return {'reply': 'Je propose une action.', 'profile': '', 'questions': [],
                    'human_steps': [], 'actions': [action('set_objective', project_id='prj_invente',
                        objective='Préparer la note de recherche avec des preuves.')]
                }, {'actual_model': model}
            assert 'plan_correction' in context
            return {'reply': 'Je corrige en visant le projet existant.', 'profile': '',
                'questions': [], 'human_steps': [], 'actions': [action('set_objective',
                    project_id=project['id'], objective='Préparer la note de recherche avec des preuves.')]
            }, {'actual_model': model}

    brain = Brain()
    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: brain)
    proposed = client.post('/api/guide/messages', json={
        'text': 'Précise cet objectif.', 'project_id': project['id']})
    assert proposed.status_code == 200, proposed.text
    assert brain.calls == 2
    assert proposed.json()['plan']['actions'][0]['project_id'] == project['id']
    assert store.get('project', project['id'])['objective'] != 'Préparer la note de recherche avec des preuves.'


def test_marguerite_creates_a_real_editable_diagram_after_approval(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Processus', 'objective': 'Documenter un processus de recherche.'}).json()
    task = client.post('/api/work/projects/'+project['id'], json={
        'type_id': 'r1-experiment-design', 'brief': 'Décrire les étapes du protocole expérimental.'}).json()

    class Brain:
        def complete(self, model, prompt, context, schema):
            return {'reply': 'Je peux ouvrir un schéma dans cette tâche.', 'profile': '',
                'questions': [], 'human_steps': ['Dessiner les étapes et les flèches dans le schéma.'],
                'actions': [action('create_diagram', label='Créer le schéma',
                    project_id=project['id'], task_id=task['id'],
                    diagram_title='Protocole à dessiner')]}, {'actual_model': model}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    proposed = client.post('/api/guide/messages', json={
        'text': 'Prépare un schéma pour mon protocole.', 'project_id': project['id']}).json()['plan']
    assert not store.all_of('work_diagram')
    assert client.post('/api/guide/plans/'+proposed['id']+'/approve').status_code == 200
    finished = wait_plan(client, {'needs_review'})
    diagram_id = finished['results'][0]['result']['diagram_id']
    fetched = client.get('/api/work/tasks/'+task['id']+'/diagrams/'+diagram_id)
    assert fetched.status_code == 200 and fetched.json()['title'] == 'Protocole à dessiner'
    assert fetched.json()['elements'] == []


def test_marguerite_refuses_formalization_of_empty_diagram(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Processus', 'objective': 'Formaliser un processus de recherche.'}).json()
    task = client.post('/api/work/projects/'+project['id'], json={
        'type_id': 'r1-experiment-design', 'brief': 'Décrire les étapes du protocole expérimental.'}).json()
    diagram = client.post('/api/work/tasks/'+task['id']+'/diagrams', json={
        'title': 'Schéma encore vide'}).json()

    class Brain:
        def complete(self, model, prompt, context, schema):
            return {'reply': 'Je vais formaliser ce schéma.', 'profile': '', 'questions': [],
                'human_steps': [], 'actions': [action('formalize_diagram',
                    label='Formaliser', project_id=project['id'], task_id=task['id'],
                    diagram_id=diagram['id'], target='protocol')]}, {'actual_model': model}

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    result = client.post('/api/guide/messages', json={
        'text': 'Formalise mon schéma.', 'project_id': project['id']})
    assert result.status_code == 200 and result.json()['plan'] is None


def test_marguerite_formalizes_existing_drawing_and_tracks_document(client, monkeypatch):
    project = client.post('/api/projects', json={
        'name': 'Processus', 'objective': 'Formaliser un processus de recherche.'}).json()
    task = client.post('/api/work/projects/'+project['id'], json={
        'type_id': 'r1-experiment-design', 'brief': 'Décrire les étapes du protocole expérimental.'}).json()
    base = '/api/work/tasks/'+task['id']+'/diagrams'
    created = client.post(base, json={'title': 'Processus témoin'}).json()
    saved = client.put(base+'/'+created['id'], json={'title': created['title'],
        'expected_version': 1, 'elements': [
            {'id': 'node-1', 'type': 'rectangle'},
            {'id': 'label-1', 'type': 'text', 'containerId': 'node-1', 'text': 'Préparer le témoin'}]}).json()
    agent_id = project['coordinator_id']

    class Brain:
        def complete(self, model, prompt, context, schema):
            assert any(d['id'] == created['id'] and d['step_count'] == 1
                       for d in context['diagrams'])
            return {'reply': 'Je peux formaliser ce dessin.', 'profile': '',
                'questions': [], 'human_steps': ['Relire le protocole produit.'],
                'actions': [action('formalize_diagram', label='Produire le protocole',
                    project_id=project['id'], task_id=task['id'], diagram_id=created['id'],
                    agent_id=agent_id, target='protocol')]}, {'actual_model': model}

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        assert context['graph']['nodes'][0]['label'] == 'Préparer le témoin'
        return ({'purpose': 'Préparer un essai témoin.', 'steps': [
            {'node_id': 'node-1', 'action': 'Préparer le témoin', 'inputs': [],
             'outputs': ['témoin'], 'checks': ['Vérifier le lot']}],
             'assumptions': [], 'ambiguities': [], 'validation': ['Relire le protocole']},
            {'input_tokens': 10})

    monkeypatch.setattr(codex_brain, 'configured', lambda: True)
    monkeypatch.setattr(codex_brain, 'models', lambda: {'models': [{'model': 'gpt-6-luna'}]})
    monkeypatch.setattr(codex_brain, 'client', lambda _: Brain())
    monkeypatch.setattr(integrations, 'direct', direct)
    proposed = client.post('/api/guide/messages', json={
        'text': 'Formalise ce dessin.', 'project_id': project['id']}).json()['plan']
    assert proposed['status'] == 'pending' and saved['version'] == 2
    assert client.post('/api/guide/plans/'+proposed['id']+'/approve').status_code == 200
    finished = wait_plan(client, {'needs_review'})
    assert finished['results'][0]['run_status'] == 'succeeded'
    document_id = finished['results'][0]['outcome']['document_id']
    document = client.get('/api/work/tasks/'+task['id']+'/documents/'+document_id)
    assert document.status_code == 200
    assert 'Préparer le témoin' in document.json()['content']
