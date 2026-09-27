import base64
import io
import time

from fastapi.testclient import TestClient
from docx import Document
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from passage import integrations, projects, store, work_catalog, workflows
from passage.main import app


def project(client):
    response = client.post('/api/projects', json={
        'name': 'Thèse essais', 'objective': 'Concevoir et documenter des essais pour une thèse.'})
    assert response.status_code == 200, response.text
    return response.json()['id']


def answer_worksheet(client, identifier):
    task = client.get('/api/work/tasks/'+identifier).json()
    answers = {question['code']: 'Cadrage vérifié : '+question['title']
               for question in task['definition']['worksheet_questions']}
    response = client.put('/api/work/tasks/'+identifier+'/worksheet', json={
        'expected_revision': task['revision'], 'answers': answers})
    assert response.status_code == 200, response.text
    return response.json()


def verified_step(client, identifier, index, done=True):
    return client.post('/api/work/tasks/'+identifier+'/steps', json={
        'index': index, 'done': done,
        'note': ('Étape '+str(index+1)+' contrôlée sur le dossier de test.'
                 if done else 'Étape rouverte pour corriger le dossier de test.')})


def finish_simple_task(client, project_id, type_id, brief, content):
    created = client.post('/api/work/projects/'+project_id, json={
        'type_id': type_id, 'brief': brief}).json()
    identifier = created['id']
    answer_worksheet(client, identifier)
    posted = client.post('/api/work/tasks/'+identifier+'/entries', json={
        'kind': 'deliverable', 'title': created['definition']['output'],
        'content': content})
    assert posted.status_code == 200, posted.text
    for index in range(len(created['definition']['steps'])):
        assert verified_step(client, identifier, index).status_code == 200
    completed = client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Livrable relu pour cet essai de parcours.'})
    assert completed.status_code == 200, completed.text
    return completed.json()['task']


def wait_run(client, run_id):
    for _ in range(50):
        row = client.get('/api/runs/'+run_id).json()
        if row['status'] not in ('queued', 'running'):
            return row
        time.sleep(0.05)
    raise AssertionError('Agent still running after the bounded test wait')


def test_every_r1_r3_task_has_a_user_and_agent_path(client):
    rows = client.get('/api/work/catalog')
    assert rows.status_code == 200
    assert len(rows.json()) == 32
    assert {r['persona'] for r in rows.json()} == {'R1', 'R2', 'R3'}
    assert len({r['id'] for r in rows.json()}) == 32
    for row in rows.json():
        assert len(row['steps']) >= 4
        assert row['inputs'] and row['output'] and row['agent_work'] and row['human_gate']
        assert len(row['worksheet_questions']) == 3
        assert [question['code'] for question in row['worksheet_questions']] == ['q1', 'q2', 'q3']
        assert row['register']['title']
        assert [column['code'] for column in row['register']['columns']] == ['c1', 'c2', 'c3', 'c4']
        assert len(row['playbook']) == len(row['steps']) == 4
        for index, play in enumerate(row['playbook']):
            assert play['index'] == index and play['human_action'] == row['steps'][index]
            assert play['agent_help'] and play['evidence']
            assert play['tool'] in work_catalog.STEP_TOOLS
            assert isinstance(play['external'], bool)


def test_register_rows_are_versioned_and_agent_suggestions_need_human_adoption(client, monkeypatch):
    pid = project(client)
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-literature',
        'brief': 'Lire plusieurs articles sur le vieillissement des cellules.'}).json()
    work_id = created['id']
    base = '/api/work/tasks/'+work_id
    values = {'c1': 'Article A · DOI à vérifier', 'c2': 'Résultat thermique',
              'c3': 'Petit échantillon', 'c4': 'Pertinent pour la question'}
    posted = client.post(base+'/records', json={
        'expected_revision': created['revision'], 'values': values})
    assert posted.status_code == 200, posted.text
    record = posted.json()['record']
    assert record['version'] == 1 and record['history'][0]['values'] == values
    changed_values = {**values, 'c3': 'Effectif et incertitude à vérifier'}
    changed = client.put(base+'/records/'+record['id'], json={
        'expected_revision': posted.json()['task']['revision'],
        'expected_version': 1, 'values': changed_values, 'active': True})
    assert changed.status_code == 200, changed.text
    assert changed.json()['record']['version'] == 2
    assert [v['values'] for v in changed.json()['record']['history']] == [values, changed_values]
    assert client.put(base+'/records/'+record['id'], json={
        'expected_revision': changed.json()['task']['revision'],
        'expected_version': 1, 'values': values, 'active': True}).status_code == 409
    agent_id = client.get('/api/projects/'+pid).json()['coordinator_id']

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        assert context['records'][0]['values']['c3'] == changed_values['c3']
        assert context['type']['register']['title'] == 'Fiches de lecture'
        assert 'record_suggestions' in schema['required']
        return ({'content': 'Fiche de lecture proposée pour un second article.',
                 'worksheet_q1': '', 'worksheet_q2': '', 'worksheet_q3': '',
                 'record_suggestions': [['Article B', 'Résultat électrochimique',
                                         'Méthode à relire', 'Comparaison utile']],
                 'source_ids': [], 'file_ids': [], 'assumptions': [],
                 'checks': ['Lire la publication complète'],
                 'limitations': ['Source non vérifiée'], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    delegated = client.post(base+'/delegate', json={'agent_id': agent_id})
    assert delegated.status_code == 200, delegated.text
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
    current = client.get(base).json()
    proposal = next(item for item in current['entries'] if item['kind'] == 'agent_draft')
    assert proposal['record_suggestions'][0]['c1'] == 'Article B'
    adopted_values = {**proposal['record_suggestions'][0], 'c3': 'Méthode relue par le doctorant'}
    adopted = client.post(base+'/records', json={
        'expected_revision': current['revision'], 'values': adopted_values,
        'source_entry_id': proposal['id'], 'suggestion_index': 0})
    assert adopted.status_code == 200, adopted.text
    assert adopted.json()['record']['source_entry_id'] == proposal['id']
    assert adopted.json()['record']['values']['c3'] == 'Méthode relue par le doctorant'
    assert client.post(base+'/records', json={
        'expected_revision': adopted.json()['task']['revision'], 'values': values,
        'source_entry_id': proposal['id'], 'suggestion_index': 1}).status_code == 422
    archived = client.put(base+'/records/'+record['id'], json={
        'expected_revision': adopted.json()['task']['revision'],
        'expected_version': 2, 'values': changed_values, 'active': False})
    assert archived.status_code == 200, archived.text
    assert not archived.json()['record']['active']
    other = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-literature',
        'brief': 'Un autre corpus du même projet pour vérifier les droits.'}).json()
    foreign_proof = client.post('/api/work/tasks/'+other['id']+'/entries', json={
        'kind': 'evidence', 'title': 'Preuve étrangère',
        'content': 'Cette pièce appartient à une autre tâche.'}).json()['entry']
    denied = client.put(base+'/records/'+adopted.json()['record']['id'], json={
        'expected_revision': archived.json()['task']['revision'],
        'expected_version': 1, 'values': adopted_values, 'active': True,
        'evidence_entry_id': foreign_proof['id']})
    assert denied.status_code == 422
    proof = client.post(base+'/entries', json={
        'kind': 'evidence', 'title': 'Note de lecture',
        'content': 'Lecture et méthode du second article vérifiées par le doctorant.'}).json()['entry']
    current = client.get(base).json()
    evidenced = client.put(base+'/records/'+adopted.json()['record']['id'], json={
        'expected_revision': current['revision'], 'expected_version': 1,
        'values': adopted_values, 'active': True,
        'evidence_entry_id': proof['id']})
    assert evidenced.status_code == 200, evidenced.text
    assert evidenced.json()['record']['evidence_entry_id'] == proof['id']
    assert 'Article B' in client.get(base+'/export.md').text
    assert proof['id'] in client.get(base+'/export.md').text
    assert 'Ligne proposée 1' in client.get(base+'/export.md').text


def test_every_task_has_a_specific_editable_deliverable_template(client):
    for definition in work_catalog.TASKS:
        draft = workflows.deliverable_template({
            'type_id': definition['id'], 'brief': 'Situation propre au projet de recherche.',
            'worksheet': {}, 'steps_done': []})
        assert draft['title'] == definition['output']
        assert draft['format'] == 'markdown'
        assert all(question['title'] in draft['content']
                   for question in definition['worksheet_questions'])
        assert all(step in draft['content'] for step in definition['steps'])
        assert definition['register']['title'] in draft['content']
        assert definition['human_gate'] in draft['content']
    pid = project(client)
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-hypotheses',
        'brief': 'Comparer plusieurs causes possibles de la dégradation.'}).json()
    template = client.get('/api/work/tasks/'+created['id']+'/template')
    assert template.status_code == 200
    assert 'Hypothèses concurrentes' in template.json()['content']


def test_task_worksheet_is_versioned_exported_and_passed_to_agent(client, monkeypatch):
    pid = project(client)
    agent_id = client.get('/api/projects/'+pid).json()['coordinator_id']
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-hypotheses',
        'brief': 'Comparer des hypothèses scientifiques sur la dégradation des batteries.'}).json()
    work_id = created['id']
    base = '/api/work/tasks/'+work_id
    questions = created['definition']['worksheet_questions']
    assert 'Hypothèses concurrentes' in questions[1]['title']
    answers = {'q1': 'Quelle variable explique la dégradation ?',
               'q2': 'Hypothèse thermique et hypothèse électrochimique.',
               'q3': 'Comparer les signatures en température contrôlée.'}
    saved = client.put(base+'/worksheet', json={
        'expected_revision': created['revision'], 'answers': answers})
    assert saved.status_code == 200, saved.text
    assert saved.json()['worksheet'] == answers
    assert saved.json()['worksheet_history'][0]['answers'] == answers
    assert saved.json()['worksheet_history'][0]['revision'] == saved.json()['revision']
    assert client.put(base+'/worksheet', json={
        'expected_revision': created['revision'], 'answers': answers}).status_code == 409
    assert client.put(base+'/worksheet', json={
        'expected_revision': saved.json()['revision'],
        'answers': {**answers, 'extra': 'Unexpected'}}).status_code == 422
    revised_answers = {**answers, 'q3': 'Mesurer des signatures en température contrôlée et répéter.'}
    revised = client.put(base+'/worksheet', json={
        'expected_revision': saved.json()['revision'], 'answers': revised_answers})
    assert revised.status_code == 200, revised.text
    assert [version['answers'] for version in revised.json()['worksheet_history']] == [answers, revised_answers]
    exported = client.get(base+'/export.md')
    assert exported.status_code == 200
    assert answers['q2'] in exported.text
    assert answers['q3'] in exported.text
    assert 'Historique des réponses' in exported.text

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        assert context['worksheet'] == revised_answers
        assert 'réponses manquantes' in prompt
        assert {'worksheet_q1', 'worksheet_q2', 'worksheet_q3'} <= set(schema['required'])
        assert schema['additionalProperties'] is False
        return ({'content': 'Proposition d’hypothèses à relire.',
                 'worksheet_q1': 'Question reformulée par l’agent.',
                 'worksheet_q2': 'Deux mécanismes concurrents à comparer.',
                 'worksheet_q3': '',
                 'source_ids': [], 'file_ids': [], 'assumptions': [],
                 'checks': [], 'limitations': [], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    delegated = client.post(base+'/delegate', json={'agent_id': agent_id})
    assert delegated.status_code == 200, delegated.text
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
    current = client.get(base).json()
    proposal = next(entry for entry in current['entries'] if entry['kind'] == 'agent_draft')
    assert proposal['worksheet_proposals']['q2'] == 'Deux mécanismes concurrents à comparer.'
    adopted_answers = {**revised_answers, 'q2': proposal['worksheet_proposals']['q2']}
    adopted = client.put(base+'/worksheet', json={
        'expected_revision': current['revision'], 'answers': adopted_answers,
        'source_entry_id': proposal['id']})
    assert adopted.status_code == 200, adopted.text
    assert adopted.json()['worksheet_history'][-1]['source_entry_id'] == proposal['id']
    assert client.put(base+'/worksheet', json={
        'expected_revision': adopted.json()['revision'], 'answers': adopted_answers,
        'source_entry_id': 'entry_unknown'}).status_code == 422


def test_completion_requires_task_specific_answers(client):
    pid = project(client)
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-literature',
        'brief': 'Classer des articles pertinents pour la revue de littérature.'}).json()
    identifier = created['id']
    assert client.post('/api/work/tasks/'+identifier+'/entries', json={
        'kind': 'deliverable', 'title': 'Bibliographie commentée',
        'content': 'Synthèse des articles apportés par le doctorant.'}).status_code == 200
    for index in range(4):
        assert verified_step(client, identifier, index).status_code == 200
    refused = client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Corpus relu.'})
    assert refused.status_code == 422
    assert created['definition']['worksheet_questions'][0]['title'] in refused.text
    answer_worksheet(client, identifier)
    accepted = client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Corpus relu.'})
    assert accepted.status_code == 200, accepted.text


def test_linked_approved_result_reaches_agent_and_reopens_downstream_task(client, monkeypatch):
    pid = project(client)
    source = finish_simple_task(
        client, pid, 'r1-literature',
        'Classer les articles autorisés sur le vieillissement des cellules.',
        'Synthèse validée : trois études donnent des résultats divergents sur la température.')
    target = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-state-art',
        'brief': 'Construire une synthèse des contradictions de la littérature.'}).json()
    target_id = target['id']
    wrong = client.put('/api/work/tasks/'+target_id+'/linked-sources', json={
        'expected_revision': target['revision'], 'source_task_ids': [target_id]})
    assert wrong.status_code == 422
    other_pid = project(client)
    foreign = client.post('/api/work/projects/'+other_pid, json={
        'type_id': 'r1-literature', 'brief': 'Corpus d’un autre projet sans lien avec cette synthèse.'}).json()
    assert client.put('/api/work/tasks/'+target_id+'/linked-sources', json={
        'expected_revision': target['revision'],
        'source_task_ids': [foreign['id']]}).status_code == 422
    linked = client.put('/api/work/tasks/'+target_id+'/linked-sources', json={
        'expected_revision': target['revision'], 'source_task_ids': [source['id']]})
    assert linked.status_code == 200, linked.text
    assert linked.json()['linked_sources_status'][0]['current']
    assert source['approved_entry_id'] == linked.json()['linked_sources'][0]['entry_id']
    assert source['id'] in client.get('/api/work/tasks/'+target_id+'/export.md').text

    agent_id = client.get('/api/projects/'+pid).json()['coordinator_id']
    seen = {}

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        seen['sources'] = context['linked_sources']
        assert 'versions acceptées' in prompt
        return ({'content': 'Synthèse critique proposée à partir du livrable lié.',
                 'source_ids': [], 'file_ids': [], 'assumptions': [],
                 'checks': ['Comparer les articles originaux'],
                 'limitations': ['Synthèse non vérifiée'], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    delegated = client.post('/api/work/tasks/'+target_id+'/delegate', json={'agent_id': agent_id})
    assert delegated.status_code == 200, delegated.text
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
    assert seen['sources'][0]['entry_id'] == source['approved_entry_id']
    assert 'trois études' in seen['sources'][0]['excerpt']
    answer_worksheet(client, target_id)
    for index in range(len(target['definition']['steps'])):
        assert verified_step(client, target_id, index).status_code == 200
    completed = client.post('/api/work/tasks/'+target_id+'/complete', json={
        'decision': 'accept', 'note': 'Synthèse relue par le doctorant.'})
    assert completed.status_code == 200, completed.text
    source_current = client.get('/api/work/tasks/'+source['id']).json()
    cycle = client.put('/api/work/tasks/'+source['id']+'/linked-sources', json={
        'expected_revision': source_current['revision'], 'source_task_ids': [target_id]})
    assert cycle.status_code == 422
    changed = client.patch('/api/work/tasks/'+source['id'], json={
        'title': source['title'],
        'brief': 'Classer de nouveaux articles et reprendre la synthèse validée.'})
    assert changed.status_code == 200
    reopened = client.get('/api/work/tasks/'+target_id).json()
    assert reopened['status'] == 'in_progress'
    assert reopened['approved_entry_id'] is None
    assert not reopened['linked_sources_status'][0]['current']
    assert client.post('/api/work/tasks/'+target_id+'/delegate',
                       json={'agent_id': agent_id}).status_code == 422
    assert client.post('/api/work/tasks/'+target_id+'/complete', json={
        'decision': 'accept', 'note': 'Ancienne synthèse.'}).status_code == 422


def test_linked_source_access_is_required_before_target_is_shared(client):
    pid = project(client)
    source = finish_simple_task(
        client, pid, 'r1-literature',
        'Conserver une synthèse privée de publications confidentielles.',
        'Résumé privé des publications du laboratoire.')
    target = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-state-art',
        'brief': 'Préparer une synthèse générale pour un autre collaborateur.'}).json()
    linked = client.put('/api/work/tasks/'+target['id']+'/linked-sources', json={
        'expected_revision': target['revision'], 'source_task_ids': [source['id']]})
    assert linked.status_code == 200
    with TestClient(app) as reviewer:
        registered = reviewer.post('/api/auth/register', json={
            'email': 'link-reviewer@example.test', 'name': 'Relecteur',
            'password': 'test-password-123'}).json()
        reviewer.headers.update({'X-Passage-CSRF': registered['csrf']})
        refused = client.post('/api/work/tasks/'+target['id']+'/share', json={
            'email': 'link-reviewer@example.test', 'role': 'reviewer'})
        assert refused.status_code == 422
        assert reviewer.get('/api/work/tasks/'+target['id']).status_code == 404
        assert reviewer.get('/api/work/tasks/'+source['id']).status_code == 404
        other_target = client.post('/api/work/projects/'+pid, json={
            'type_id': 'r1-state-art',
            'brief': 'Autre synthèse ouverte au collaborateur pour un test de droits.'}).json()
        assert client.post('/api/work/tasks/'+other_target['id']+'/share', json={
            'email': 'link-reviewer@example.test', 'role': 'reviewer'}).status_code == 200
        assert client.put('/api/work/tasks/'+other_target['id']+'/linked-sources', json={
            'expected_revision': other_target['revision'],
            'source_task_ids': [source['id']]}).status_code == 422
        assert client.post('/api/work/tasks/'+source['id']+'/share', json={
            'email': 'link-reviewer@example.test', 'role': 'reviewer'}).status_code == 200
        assert client.post('/api/work/tasks/'+target['id']+'/share', json={
            'email': 'link-reviewer@example.test', 'role': 'reviewer'}).status_code == 200
        visible = reviewer.get('/api/work/tasks/'+target['id']).json()
        assert visible['linked_sources'] == []
        assert visible['linked_sources_status'][0]['title'] == source['title']
        assert source['title'] in reviewer.get(
            '/api/work/tasks/'+target['id']+'/export.md').text
        assert reviewer.get('/api/work/tasks/'+source['id']).status_code == 200


def test_linked_document_uses_the_accepted_immutable_version(client, monkeypatch):
    pid = project(client)
    source = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-writing',
        'brief': 'Rédiger une section de thèse à utiliser dans l’état de l’art.'}).json()
    source_id = source['id']
    answer_worksheet(client, source_id)
    document = client.post('/api/work/tasks/'+source_id+'/documents', json={
        'title': 'Section validée', 'format': 'markdown',
        'content': 'Version scientifique approuvée : effet thermique mesuré.'}).json()['document']
    assert client.post('/api/work/tasks/'+source_id+'/documents/'+document['id']+'/submit').status_code == 200
    for index in range(4):
        assert verified_step(client, source_id, index).status_code == 200
    assert client.post('/api/work/tasks/'+source_id+'/complete', json={
        'decision': 'accept', 'note': 'Section vérifiée.'}).status_code == 200
    target = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-state-art',
        'brief': 'Construire une synthèse à partir de la section validée.'}).json()
    assert client.put('/api/work/tasks/'+target['id']+'/linked-sources', json={
        'expected_revision': target['revision'],
        'source_task_ids': [source_id]}).status_code == 200
    agent_id = client.get('/api/projects/'+pid).json()['coordinator_id']

    def direct(_brain, _prompt, context, *_args):
        linked = context['linked_sources'][0]
        assert linked['excerpt'] == 'Version scientifique approuvée : effet thermique mesuré.'
        assert linked['content_sha256'] == document['sha256']
        return ({'content': 'Synthèse proposée.', 'source_ids': [], 'file_ids': [],
                 'assumptions': [], 'checks': [], 'limitations': [], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    started = client.post('/api/work/tasks/'+target['id']+'/delegate', json={'agent_id': agent_id})
    assert started.status_code == 200, started.text
    assert wait_run(client, started.json()['run']['id'])['status'] == 'succeeded'


def test_confidential_linked_result_needs_source_agent_clearance(client):
    pid = project(client)
    source = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r3-peer-review',
        'brief': 'Rédiger un avis confidentiel pour une revue scientifique.'}).json()
    source_id = source['id']
    answer_worksheet(client, source_id)
    proof = client.post('/api/work/tasks/'+source_id+'/entries', json={
        'kind': 'evidence', 'title': 'Confirmation de soumission',
        'content': 'La revue a accusé réception de l’avis signé.'}).json()['entry']
    client.post('/api/work/tasks/'+source_id+'/entries', json={
        'kind': 'deliverable', 'title': 'Avis scientifique',
        'content': 'Avis confidentiel conservé par le relecteur.'})
    for index in range(4):
        assert verified_step(client, source_id, index).status_code == 200
    assert client.post('/api/work/tasks/'+source_id+'/checkpoints', json={
        'code': 'review_submitted',
        'statement': 'Je confirme que cet avis a été remis à la revue.',
        'occurred_at': '2026-09-26',
        'evidence_entry_id': proof['id']}).status_code == 200
    assert client.post('/api/work/tasks/'+source_id+'/complete', json={
        'decision': 'accept', 'note': 'Avis signé et remis.'}).status_code == 200
    target = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r3-manuscripts',
        'brief': 'Préparer une analyse interne à partir de l’avis existant.'}).json()
    assert client.put('/api/work/tasks/'+target['id']+'/linked-sources', json={
        'expected_revision': target['revision'],
        'source_task_ids': [source_id]}).status_code == 200
    agent_id = client.get('/api/projects/'+pid).json()['coordinator_id']
    denied = client.post('/api/work/tasks/'+target['id']+'/delegate',
                         json={'agent_id': agent_id})
    assert denied.status_code == 422
    assert 'Usage de l’IA autorisé' in denied.text


def test_every_catalog_task_can_reach_review_and_human_completion(client, monkeypatch):
    pid = project(client)
    agent = store.get('agent', client.get('/api/projects/'+pid).json()['coordinator_id'])

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        assert context['type']['id'] in work_catalog.BY_ID
        return ({'content': 'Proposition à vérifier pour '+context['type']['title'],
                 'source_ids': [], 'file_ids': [], 'assumptions': [],
                 'checks': ['Contrôle humain du livrable'],
                 'limitations': ['Aucune action externe effectuée'],
                 'next_steps': ['Faire relire']}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    with TestClient(app) as reviewer:
        registered = reviewer.post('/api/auth/register', json={
            'email': 'matrix-reviewer@example.test', 'name': 'Directeur de thèse',
            'password': 'test-password-123'}).json()
        reviewer.headers.update({'X-Passage-CSRF': registered['csrf']})
        assert client.patch('/api/auth/users/'+registered['user']['id'],
                            json={'role': 'lab'}).status_code == 200

        for definition in work_catalog.TASKS:
            created = client.post('/api/work/projects/'+pid, json={
                'type_id': definition['id'],
                'brief': 'Parcours réel du travail '+definition['title']+' à documenter.'})
            assert created.status_code == 200, definition['id']+' '+created.text
            work_id = created.json()['id']
            answer_worksheet(client, work_id)
            agent_gates = [item for item in definition['checkpoints'] if item['before'] == 'agent']
            if agent_gates:
                evidence = client.post('/api/work/tasks/'+work_id+'/entries', json={
                    'kind': 'evidence', 'title': 'Règle de partage vérifiée',
                    'content': 'Règle de confidentialité communiquée au responsable du test.'})
                assert evidence.status_code == 200, definition['id']
                for gate in agent_gates:
                    attested = client.post('/api/work/tasks/'+work_id+'/checkpoints', json={
                        'code': gate['code'], 'statement': 'Je confirme le périmètre autorisé pour ce dossier de test.',
                        'occurred_at': '2026-09-26',
                        'evidence_entry_id': evidence.json()['entry']['id']})
                    assert attested.status_code == 200, definition['id']+' '+attested.text
            delegated = client.post('/api/work/tasks/'+work_id+'/delegate',
                                    json={'agent_id': agent['id']})
            assert delegated.status_code == 200, definition['id']+' '+delegated.text
            assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
            for index in range(len(definition['steps'])):
                checked = verified_step(client, work_id, index)
                assert checked.status_code == 200, definition['id']
            done_gates = [item for item in definition['checkpoints'] if item['before'] == 'done']
            if done_gates:
                evidence = client.post('/api/work/tasks/'+work_id+'/entries', json={
                    'kind': 'evidence', 'title': 'Trace de l’action externe',
                    'content': 'Preuve déclarée de l’action hors Passage pour le test du parcours.'})
                assert evidence.status_code == 200, definition['id']
                for gate in done_gates:
                    attested = client.post('/api/work/tasks/'+work_id+'/checkpoints', json={
                        'code': gate['code'], 'statement': 'Je confirme cette action externe et relie sa pièce dans la tâche.',
                        'occurred_at': '2026-09-26',
                        'evidence_entry_id': evidence.json()['entry']['id']})
                    assert attested.status_code == 200, definition['id']+' '+attested.text
            if definition['requires_peer_review']:
                shared = client.post('/api/work/tasks/'+work_id+'/share', json={
                    'email': 'matrix-reviewer@example.test', 'role': 'reviewer'})
                assert shared.status_code == 200, definition['id']
                approved = reviewer.post('/api/work/tasks/'+work_id+'/review', json={
                    'decision': 'approve', 'note': 'Version relue pour le test du parcours.'})
                assert approved.status_code == 200, definition['id']
            completed = client.post('/api/work/tasks/'+work_id+'/complete', json={
                'decision': 'accept', 'note': 'Livrable vérifié par le responsable.'})
            assert completed.status_code == 200, definition['id']+' '+completed.text
            assert completed.json()['task']['status'] == 'done'


def test_external_action_requires_scoped_human_attestation(client):
    pid = project(client)
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-experiment-run',
        'brief': 'Réaliser puis documenter un essai selon le protocole approuvé.'}).json()
    work_id = created['id']
    answer_worksheet(client, work_id)
    client.post('/api/work/tasks/'+work_id+'/entries', json={
        'kind': 'deliverable', 'title': 'Compte rendu',
        'content': 'Paramètres et observations fournis par le responsable.'})
    for index in range(4):
        assert verified_step(client, work_id, index).status_code == 200
    before = client.post('/api/work/tasks/'+work_id+'/complete', json={
        'decision': 'accept', 'note': 'Essai relu.'})
    assert before.status_code == 422
    assert 'Essai réalisé' in before.text
    evidence = client.post('/api/work/tasks/'+work_id+'/entries', json={
        'kind': 'evidence', 'title': 'Relevé daté',
        'content': 'Fichier de mesures vérifié par l’expérimentateur.'}).json()['entry']
    assert client.post('/api/work/tasks/'+work_id+'/checkpoints', json={
        'code': 'experiment_performed', 'statement': 'Essai réalisé selon le protocole ce jour-là.',
        'occurred_at': '2026-09-26', 'evidence_entry_id': 'entry_outra'}).status_code == 422
    attested = client.post('/api/work/tasks/'+work_id+'/checkpoints', json={
        'code': 'experiment_performed',
        'statement': 'J’ai réalisé l’essai et relié son relevé daté à cette tâche.',
        'occurred_at': '2026-09-26', 'evidence_entry_id': evidence['id']})
    assert attested.status_code == 200, attested.text
    assert attested.json()['task']['checkpoints'][0]['valid']
    assert client.post('/api/work/tasks/'+work_id+'/complete', json={
        'decision': 'accept', 'note': 'Essai relu.'}).status_code == 200
    revised = client.patch('/api/work/tasks/'+work_id, json={
        'title': created['title'],
        'brief': 'Réaliser puis documenter un essai selon le protocole approuvé et révisé.'})
    assert revised.status_code == 200
    assert not revised.json()['checkpoints'][0]['valid']
    assert client.post('/api/work/tasks/'+work_id+'/complete', json={
        'decision': 'accept', 'note': 'Essai relu.'}).status_code == 422


def test_confidential_review_requires_current_clearance_before_agent(client, monkeypatch):
    pid = project(client)
    agent_id = client.get('/api/projects/'+pid).json()['coordinator_id']
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r3-peer-review',
        'brief': 'Préparer une évaluation confidentielle selon la politique de la revue.'}).json()
    work_id = created['id']
    base = '/api/work/tasks/'+work_id
    denied = client.post(base+'/delegate', json={'agent_id': agent_id})
    assert denied.status_code == 422
    assert 'Usage de l’IA' in denied.text
    policy = client.post(base+'/entries', json={'kind': 'evidence',
        'title': 'Politique éditoriale',
        'content': 'Le recours à un modèle est autorisé pour les extraits remis dans ce test.'}).json()['entry']
    assert client.post(base+'/checkpoints', json={
        'code': 'agent_clearance',
        'statement': 'La revue autorise l’utilisation de cet agent pour les extraits joints.',
        'occurred_at': '2026-09-26', 'evidence_entry_id': policy['id']}).status_code == 200
    client.post(base+'/entries', json={'kind': 'note', 'title': 'Nouveau contexte',
        'content': 'Un nouvel extrait serait transmis.'})
    assert client.post(base+'/delegate', json={'agent_id': agent_id}).status_code == 422

    def direct(*_args):
        return ({'content': 'Questions critiques proposées.', 'source_ids': [],
                 'file_ids': [], 'assumptions': [], 'checks': [],
                 'limitations': [], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    assert client.post(base+'/checkpoints', json={
        'code': 'agent_clearance',
        'statement': 'La politique couvre maintenant le dossier et les extraits actualisés.',
        'occurred_at': '2026-09-26', 'evidence_entry_id': policy['id']}).status_code == 200
    delegated = client.post(base+'/delegate', json={'agent_id': agent_id})
    assert delegated.status_code == 200, delegated.text
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'


def test_multiple_task_specialists_can_join_team_and_only_run_their_specialties(client, monkeypatch):
    pid = project(client)
    client.headers['X-Passage-Role'] = 'admin'
    blueprint = client.get('/api/agents/creator/blueprint/research_task')
    assert blueprint.status_code == 200, blueprint.text
    base = blueprint.json()['agent']

    def create_specialist(name, task_id):
        body = {key: value for key, value in base.items() if key not in ('id', 'revision')}
        body.update(name=name, trigger='Quand une tâche du projet est confiée.',
                    reads='Pièces, notes et sources autorisées de la tâche.',
                    boundaries='Le chercheur valide les faits et le livrable.',
                    checkpoint='Relecture du brouillon avant toute décision.',
                    deliverables='Proposition sourcée avec limites et vérifications.',
                    context='Recherche doctorale et collaboration de laboratoire.',
                    work_specialties=[task_id], active=True)
        response = client.post('/api/agents', json=body)
        assert response.status_code == 200, response.text
        return response.json()

    code = create_specialist('Agent code', 'r1-code')
    writing = create_specialist('Agent manuscrit', 'r1-writing')
    assert code['active'] and writing['active']
    assert 'work.read' in code['tools']

    roster = client.get('/api/projects/'+pid).json()['agent_ids']
    added = client.patch('/api/projects/'+pid+'/team', json={
        'agent_ids': roster+[code['id'], writing['id']]})
    assert added.status_code == 200, added.text
    assert {code['id'], writing['id']} <= set(added.json()['agent_ids'])
    assert client.patch('/api/projects/'+pid+'/team', json={
        'agent_ids': [code['id']]}).status_code == 422

    task_id = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-code', 'brief': 'Développer un script de traitement des mesures.'}).json()['id']
    wrong = client.post('/api/work/tasks/'+task_id+'/delegate', json={'agent_id': writing['id']})
    assert wrong.status_code == 422

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        assert brain['id'] == code['id']
        assert context['type']['id'] == 'r1-code'
        assert 'Contexte métier :\nRecherche doctorale' in prompt
        assert 'Point de contrôle :\nRelecture du brouillon' in prompt
        assert 'Sources autorisées :\nPièces, notes et sources' in prompt
        return ({'content': 'Programme proposé avec tests à exécuter.', 'source_ids': [],
                 'file_ids': [], 'assumptions': [], 'checks': ['Exécuter les tests'],
                 'limitations': ['Code non exécuté'], 'next_steps': ['Revoir les résultats']}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    delegated = client.post('/api/work/tasks/'+task_id+'/delegate', json={'agent_id': code['id']})
    assert delegated.status_code == 200, delegated.text
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
    assert client.get('/api/runs/'+delegated.json()['run']['id']).json()['agent_snapshot']['id'] == code['id']
    assert client.get('/api/work/tasks/'+task_id).json()['entries'][-1]['actor_id'] == code['id']


def test_agent_revises_the_latest_draft_with_human_feedback(client, monkeypatch):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-writing', 'brief': 'Rédiger une section sur les mesures thermiques.'}).json()['id']
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')
    calls = []

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        calls.append(context)
        if len(calls) == 1:
            assert context['revision_request'] is None
            return ({'content': 'La température monte dans tous les essais.',
                     'source_ids': [], 'file_ids': [], 'assumptions': [],
                     'checks': [], 'limitations': ['Aucune valeur vérifiée'], 'next_steps': []}, {})
        assert context['revision_request']['source_content'] == 'La température monte dans tous les essais.'
        assert 'Précise les essais' in context['revision_request']['feedback']
        return ({'content': 'Les données fournies ne permettent pas de conclure sur tous les essais.',
                 'revision_summary': 'Conclusion trop générale retirée.',
                 'source_ids': [], 'file_ids': [], 'assumptions': [], 'checks': [],
                 'limitations': ['Mesures à joindre'], 'next_steps': ['Vérifier les données']}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    first = client.post('/api/work/tasks/'+identifier+'/delegate', json={'agent_id': agent['id']})
    assert first.status_code == 200, first.text
    assert wait_run(client, first.json()['run']['id'])['status'] == 'succeeded'
    current = client.get('/api/work/tasks/'+identifier).json()
    original = current['entries'][-1]
    feedback = 'Précise les essais observés et retire la généralisation sans preuve.'
    request = {'agent_id': agent['id'], 'source_entry_id': original['id'],
               'expected_revision': current['revision'], 'instruction': feedback}
    assert client.post('/api/work/tasks/'+identifier+'/delegate', json={
        **request, 'expected_revision': current['revision']-1}).status_code == 409
    assert client.post('/api/work/tasks/'+identifier+'/delegate', json={
        **request, 'source_entry_id': 'entry_autre'}).status_code == 422
    assert client.post('/api/work/tasks/'+identifier+'/delegate', json={
        **request, 'instruction': 'court'}).status_code == 422
    revised = client.post('/api/work/tasks/'+identifier+'/delegate', json=request)
    assert revised.status_code == 200, revised.text
    assert wait_run(client, revised.json()['run']['id'])['status'] == 'succeeded'
    current = client.get('/api/work/tasks/'+identifier).json()
    draft = current['entries'][-1]
    assert len(calls) == 2
    assert draft['revises_entry_id'] == original['id']
    assert draft['instruction'] == feedback
    assert draft['revision_summary'] == 'Conclusion trop générale retirée.'
    assert '-La température monte' in draft['revision_diff']
    assert '+Les données fournies' in draft['revision_diff']
    assert feedback in client.get('/api/work/tasks/'+identifier+'/export.md').text


def test_focused_delegation_supports_external_steps_across_r1_r2_r3(client, monkeypatch):
    pid = project(client)
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')
    cases = [('r1-experiment-run', 1), ('r2-jobs', 3), ('r3-funding', 2)]
    observed = []

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        focus = context['focus_step']
        observed.append((context['type']['id'], focus['index']))
        assert focus['external'] and 'action hors de Passage reste humaine' in prompt
        return ({'content': 'Préparation et contrôles proposés, sans action externe déclarée.',
                 'source_ids': [], 'file_ids': [], 'assumptions': [],
                 'checks': ['Demander une preuve humaine'],
                 'limitations': ['Action non exécutée'], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    for type_id, focus in cases:
        created = client.post('/api/work/projects/'+pid, json={
            'type_id': type_id, 'brief': 'Préparer et vérifier cette étape avec une équipe de recherche.'}).json()
        identifier = created['id']
        assert client.post('/api/work/tasks/'+identifier+'/delegate', json={
            'agent_id': agent['id'], 'focus_step': 4}).status_code == 422
        started = client.post('/api/work/tasks/'+identifier+'/delegate', json={
            'agent_id': agent['id'], 'focus_step': focus,
            'expected_revision': created['revision']})
        assert started.status_code == 200, started.text
        assert wait_run(client, started.json()['run']['id'])['status'] == 'succeeded'
        drafted = client.get('/api/work/tasks/'+identifier).json()['entries'][-1]
        assert drafted['focus_step'] == focus
        assert created['definition']['steps'][focus] in client.get(
            '/api/work/tasks/'+identifier+'/export.md').text
    assert observed == cases


def test_project_coordinator_can_open_and_delegate_a_catalog_task(client, monkeypatch):
    pid = project(client)
    agent = store.get('agent', client.get('/api/projects/'+pid).json()['coordinator_id'])
    decisions = []

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        if prompt == projects.PROMPT:
            assert len(context['work_catalog']) == 32
            decisions.append(context['work_items'])
            if len(decisions) == 1:
                return ({
                    'action': 'work', 'explanation': 'Préparer un brouillon de manuscrit',
                    'text': 'Rédiger une section de thèse sur les résultats fournis.',
                    'agent_id': agent['id'], 'thesis_id': '', 'service': '', 'tool': '',
                    'arguments_json': '{"type_id":"r1-writing","work_id":"","focus_step":2}'}, {})
            return ({
                'action': 'answer', 'explanation': '',
                'text': 'La tâche est ouverte et le brouillon de l’agent est en cours.',
                'agent_id': '', 'thesis_id': '', 'service': '', 'tool': '',
                'arguments_json': '{}'}, {})
        assert context['focus_step']['index'] == 2
        assert 'source' in context['focus_step']['evidence'].lower() or 'passages' in context['focus_step']['evidence'].lower()
        return ({
            'content': 'Plan de section à vérifier avec les sources.',
            'source_ids': [], 'file_ids': [], 'assumptions': [],
            'checks': ['Contrôler les figures'], 'limitations': ['Pas de soumission'],
            'next_steps': ['Faire relire']}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    started = client.post('/api/projects/'+pid+'/chat', json={
        'message': 'Confie à un agent une tâche pour rédiger ma thèse.', 'mode': 'live'})
    assert started.status_code == 200, started.text
    assert wait_run(client, started.json()['id'])['status'] == 'succeeded'
    items = client.get('/api/work/projects/'+pid).json()
    assert len(items) == 1 and items[0]['type_id'] == 'r1-writing'
    assert len(decisions) == 2 and decisions[1][0]['id'] == items[0]['id']
    assert wait_run(client, items[0]['run_id'])['status'] == 'succeeded'
    drafted = client.get('/api/work/tasks/'+items[0]['id']).json()['entries'][-1]
    assert drafted['kind'] == 'agent_draft' and drafted['focus_step'] == 2


def test_coordinator_opens_confidential_task_without_dispatching_agent(client, monkeypatch):
    pid = project(client)
    agent_id = client.get('/api/projects/'+pid).json()['coordinator_id']

    def direct(*_args):
        return ({'action': 'work', 'explanation': 'Préparer une grille confidentielle',
                 'text': 'Préparer une évaluation scientifique du dossier confidentiel.',
                 'agent_id': agent_id, 'thesis_id': '', 'service': '', 'tool': '',
                 'arguments_json': '{"type_id":"r3-peer-review","work_id":""}'}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    run = client.post('/api/projects/'+pid+'/chat', json={
        'message': 'Ouvre une relecture scientifique et demande un brouillon à mon agent.',
        'mode': 'live'})
    assert run.status_code == 200, run.text
    result = wait_run(client, run.json()['id'])
    assert result['status'] == 'succeeded'
    assert result['result']['status'] == 'awaiting_clearance'
    items = client.get('/api/work/projects/'+pid).json()
    assert len(items) == 1 and items[0]['status'] == 'todo'
    assert not items[0]['entries']
    conversation = client.get('/api/projects/'+pid).json()['messages']
    assert 'Usage de l’IA autorisé' in conversation[-1]['text']


def test_coordinator_redacts_uncleared_confidential_task_content(client, monkeypatch):
    pid = project(client)
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r3-peer-review',
        'title': 'Manuscrit CONFIDENTIEL-ALPHA',
        'brief': 'Dossier de revue confidentiel avec résultats à ne pas transmettre.'}).json()
    work_id = created['id']
    client.post('/api/work/tasks/'+work_id+'/entries', json={
        'kind': 'evidence', 'title': 'Politique de revue',
        'content': 'Extrait CONFIDENTIEL-BETA à ne pas donner au coordinateur.'})
    seen = {}

    def direct(_brain, _prompt, context, *_args):
        seen['items'] = context['work_items']
        return ({'action': 'answer', 'explanation': '', 'text': 'Un dossier attend un contrôle.',
                 'agent_id': '', 'thesis_id': '', 'service': '', 'tool': '',
                 'arguments_json': '{}'}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    started = client.post('/api/projects/'+pid+'/chat', json={
        'message': 'Quel est le statut de mes tâches ?', 'mode': 'live'})
    assert started.status_code == 200
    assert wait_run(client, started.json()['id'])['status'] == 'succeeded'
    entry = seen['items'][0]
    assert entry['id'] == work_id
    assert entry['title'] == 'Dossier à accès contrôlé'
    assert entry['latest_entry'] == ''
    assert entry['agent_clearance_required']


def test_manual_work_requires_deliverable_and_checked_steps(client):
    pid = project(client)
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-experiment-run',
        'brief': 'Essai sur les cellules à 10 A avec protocole approuvé.'})
    assert created.status_code == 200, created.text
    work = created.json()
    assert work['status'] == 'todo'
    assert len(client.get('/api/projects/'+pid).json()['work_items']) == 1
    identifier = work['id']
    assert client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Essai terminé'}).status_code == 422
    evidence = client.post('/api/work/tasks/'+identifier+'/entries', json={
        'kind': 'evidence', 'title': 'Mesures brutes',
        'content': 'Essai réalisé le 26/09 ; série conservée dans le laboratoire.'})
    assert evidence.status_code == 200, evidence.text
    assert client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Essai terminé'}).status_code == 422
    result = client.post('/api/work/tasks/'+identifier+'/entries', json={
        'kind': 'deliverable', 'title': 'Compte rendu',
        'content': 'Paramètres, incidents et mesures à faire vérifier.'})
    assert result.status_code == 200
    answer_worksheet(client, identifier)
    for index in range(len(work_catalog.BY_ID['r1-experiment-run']['steps'])):
        assert verified_step(client, identifier, index).status_code == 200
    attested = client.post('/api/work/tasks/'+identifier+'/checkpoints', json={
        'code': 'experiment_performed',
        'statement': 'Je confirme avoir réalisé cet essai et conservé les mesures brutes.',
        'occurred_at': '2026-09-26', 'evidence_entry_id': evidence.json()['entry']['id']})
    assert attested.status_code == 200, attested.text
    accepted = client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Compte rendu vérifié par le doctorant.'})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()['task']['status'] == 'done'
    assert accepted.json()['task']['approved_entry_id'] == result.json()['entry']['id']
    exported = client.get('/api/work/tasks/'+identifier+'/export.md')
    assert exported.status_code == 200
    assert 'Livrable accepté dans Passage' in exported.text
    assert 'Compte rendu' in exported.text and 'Mesures brutes' in exported.text
    reopened = verified_step(client, identifier, 0, False)
    assert reopened.json()['status'] == 'in_progress'
    assert reopened.json()['approved_entry_id'] is None
    for index in range(len(work_catalog.BY_ID['r1-experiment-run']['steps'])):
        assert verified_step(client, identifier, index).status_code == 200
    assert client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Mesures relues après correction.'}).status_code == 422
    assert client.post('/api/work/tasks/'+identifier+'/checkpoints', json={
        'code': 'experiment_performed',
        'statement': 'Je confirme de nouveau cet essai et ses mesures après correction.',
        'occurred_at': '2026-09-26', 'evidence_entry_id': evidence.json()['entry']['id']}).status_code == 200
    again = client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Mesures relues après correction.'})
    assert again.status_code == 200
    revision = again.json()['task']['revision']
    same = client.post('/api/work/tasks/'+identifier+'/steps', json={'index': 0, 'done': True})
    assert same.json()['status'] == 'done'
    assert same.json()['revision'] == revision


def test_step_checks_are_human_traces_bound_to_current_task_material(client):
    pid = project(client)
    first = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-writing', 'brief': 'Rédiger et vérifier la section résultats de la thèse.'}).json()
    other = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-writing', 'brief': 'Rédiger une autre section indépendante de la thèse.'}).json()
    identifier = first['id']
    document = client.post('/api/work/tasks/'+identifier+'/documents', json={
        'title': 'Résultats', 'format': 'markdown',
        'content': 'Première version avec mesures à relire.'}).json()['document']
    foreign = client.post('/api/work/tasks/'+other['id']+'/entries', json={
        'kind': 'evidence', 'title': 'Preuve étrangère', 'content': 'Dossier distinct.'}).json()['entry']
    endpoint = '/api/work/tasks/'+identifier+'/steps'
    assert client.post(endpoint, json={'index': 0, 'done': True}).status_code == 422
    assert client.post(endpoint, json={
        'index': 0, 'done': True, 'note': 'Je confirme cette étape sur le document.',
        'proof_kind': 'entry', 'proof_id': foreign['id']}).status_code == 422
    before = client.get('/api/work/tasks/'+identifier).json()
    checked = client.post(endpoint, json={
        'index': 0, 'done': True, 'note': 'J’ai relu les valeurs et la source citée.',
        'proof_kind': 'document', 'proof_id': document['id'],
        'expected_revision': before['revision']})
    assert checked.status_code == 200, checked.text
    assert checked.json()['step_checks'][0]['current']
    assert checked.json()['step_checks'][0]['record']['actor_id']
    assert client.post(endpoint, json={
        'index': 1, 'done': True, 'note': 'J’ai relu la deuxième étape.',
        'expected_revision': before['revision']}).status_code == 409
    changed = client.put('/api/work/tasks/'+identifier+'/documents/'+document['id'], json={
        'title': 'Résultats', 'format': 'markdown',
        'content': 'Deuxième version avec valeurs corrigées.', 'expected_version': 1})
    assert changed.status_code == 200, changed.text
    assert changed.json()['task']['step_checks'][0]['checked']
    assert not changed.json()['task']['step_checks'][0]['current']
    refreshed = client.post(endpoint, json={
        'index': 0, 'done': True, 'note': 'J’ai relu les valeurs corrigées de la version deux.',
        'proof_kind': 'document', 'proof_id': document['id']})
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()['step_checks'][0]['current']
    history = refreshed.json()['step_check_history']
    assert len(history) == 2 and history[0]['proof_version'] == 1
    assert history[1]['proof_version'] == 2


def test_team_agent_draft_is_bound_to_task_and_requires_human_validation(client, monkeypatch):
    pid = project(client)
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r3-funding', 'brief': 'Préparer une candidature de financement de notre équipe.'}).json()['id']
    calls = []

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        calls.append((brain['id'], context['task_id'], tools, context['type']['id']))
        return ({'content': 'Plan du dossier et risques à instruire.', 'source_ids': [], 'file_ids': [],
                 'assumptions': ['Budget à chiffrer'], 'checks': ['Vérifier les critères de l’appel'],
                 'limitations': ['Aucun dépôt effectué'], 'next_steps': ['Faire valider le budget']},
                {'actual_model': brain['model']})

    monkeypatch.setattr(integrations, 'direct', direct)
    response = client.post('/api/work/tasks/'+identifier+'/delegate', json={
        'agent_id': agent['id'], 'instruction': 'Prépare une trame pour la réunion.'})
    assert response.status_code == 200, response.text
    run = wait_run(client, response.json()['run']['id'])
    assert run['status'] == 'succeeded', run
    task = client.get('/api/work/tasks/'+identifier).json()
    assert task['status'] == 'review'
    assert task['entries'][-1]['kind'] == 'agent_draft'
    assert task['entries'][-1]['origin'] == 'agent'
    assert calls == [(agent['id'], identifier, [], 'r3-funding')]
    draft_id = task['entries'][-1]['id']
    revised = client.post('/api/work/tasks/'+identifier+'/entries', json={
        'kind': 'deliverable', 'title': 'Dossier revu par le porteur',
        'content': 'Budget à chiffrer et preuves relues.',
        'derived_from': draft_id})
    assert revised.status_code == 200, revised.text
    assert revised.json()['entry']['derived_from'] == draft_id
    assert 'Reprise de la pièce : '+draft_id in client.get(
        '/api/work/tasks/'+identifier+'/export.md').text
    another_id = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r3-funding', 'brief': 'Un autre dossier de financement à préparer.'}).json()['id']
    assert client.post('/api/work/tasks/'+another_id+'/entries', json={
        'kind': 'deliverable', 'title': 'Reprise interdite',
        'content': 'Texte', 'derived_from': draft_id}).status_code == 422
    assert client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'À valider'}).status_code == 422
    with TestClient(app) as other:
        registered = other.post('/api/auth/register', json={
            'email': 'workflow-other@example.test', 'name': 'Autre',
            'password': 'test-password-123'}).json()
        other.headers.update({'X-Passage-CSRF': registered['csrf']})
        assert other.get('/api/work/tasks/'+identifier).status_code == 404
        assert other.get('/api/work/projects/'+pid).status_code == 404
        assert other.get('/api/work/tasks/'+identifier+'/export.md').status_code == 404


def test_invalid_agent_source_is_not_saved_and_task_can_be_retried(client, monkeypatch):
    pid = project(client)
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-state-art', 'brief': 'Comparer les travaux sur la dégradation thermique.'}).json()['id']

    def bad(*args):
        return ({'content': 'Texte trompeur', 'source_ids': ['thesis-inconnue'], 'file_ids': [],
                 'assumptions': [], 'checks': [], 'limitations': [], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', bad)
    response = client.post('/api/work/tasks/'+identifier+'/delegate', json={'agent_id': agent['id']})
    assert response.status_code == 200, response.text
    run = wait_run(client, response.json()['run']['id'])
    assert run['status'] == 'failed'
    task = client.get('/api/work/tasks/'+identifier).json()
    assert task['status'] == 'in_progress'
    assert client.get('/api/work/projects/'+pid).json()[0]['status'] == 'in_progress'
    assert task['entries'] == []
    assert task['last_error']


def test_supervisor_review_is_required_on_current_version(client):
    pid = project(client)
    created = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-disclosure',
        'brief': 'Déterminer si le résultat sur les cellules peut être diffusé.'})
    assert created.status_code == 200
    identifier = created.json()['id']
    answer_worksheet(client, identifier)
    client.post('/api/work/tasks/'+identifier+'/entries', json={
        'kind': 'deliverable', 'title': 'Fiche de diffusion',
        'content': 'Résumé, publication prévue et droits encore à vérifier.'})
    for index in range(len(work_catalog.BY_ID['r1-disclosure']['steps'])):
        assert verified_step(client, identifier, index).status_code == 200
    proof = client.post('/api/work/tasks/'+identifier+'/entries', json={
        'kind': 'evidence', 'title': 'Accord de diffusion',
        'content': 'Périmètre de diffusion vérifié par les personnes habilitées.'})
    assert proof.status_code == 200
    assert client.post('/api/work/tasks/'+identifier+'/checkpoints', json={
        'code': 'rights_cleared',
        'statement': 'Je confirme que les personnes habilitées ont autorisé ce périmètre.',
        'occurred_at': '2026-09-26',
        'evidence_entry_id': proof.json()['entry']['id']}).status_code == 200
    refused = client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Diffusion envisagée.'})
    assert refused.status_code == 422
    with TestClient(app) as supervisor:
        registered = supervisor.post('/api/auth/register', json={
            'email': 'directeur@example.test', 'name': 'Directeur',
            'password': 'test-password-123'}).json()
        supervisor.headers.update({'X-Passage-CSRF': registered['csrf']})
        assert client.post('/api/work/tasks/'+identifier+'/share', json={
            'email': 'directeur@example.test', 'role': 'reviewer'}).status_code == 422
        changed = client.patch('/api/auth/users/'+registered['user']['id'], json={'role': 'lab'})
        assert changed.status_code == 200
        shared = client.post('/api/work/tasks/'+identifier+'/share', json={
            'email': 'directeur@example.test', 'role': 'reviewer'})
        assert shared.status_code == 200, shared.text
        assert len(supervisor.get('/api/work/inbox').json()) == 1
        assert supervisor.get('/api/projects/'+pid).status_code == 404
        review = supervisor.post('/api/work/tasks/'+identifier+'/review', json={
            'decision': 'approve', 'note': 'Je valide la version examinée.'})
        assert review.status_code == 200, review.text
        accepted = client.post('/api/work/tasks/'+identifier+'/complete', json={
            'decision': 'accept', 'note': 'Accord recueilli avant diffusion.'})
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()['task']['status'] == 'done'
        client.post('/api/work/tasks/'+identifier+'/entries', json={
            'kind': 'note', 'title': 'Nouveau résultat', 'content': 'Le contenu a changé.'})
        stale = client.post('/api/work/tasks/'+identifier+'/complete', json={
            'decision': 'accept', 'note': 'Même décision.'})
        assert stale.status_code == 422


def test_file_is_private_and_text_is_available_to_task_agent(client, monkeypatch):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-code', 'brief': 'Relire le programme de traitement des mesures.'}).json()['id']
    uploaded = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'analyse.py',
        'content_base64': base64.b64encode(b'print("MESURES_REELLES")\n').decode()})
    assert uploaded.status_code == 200, uploaded.text
    file_id = uploaded.json()['file']['id']
    assert uploaded.json()['file']['readable_by_agent']
    own_download = client.get('/api/work/tasks/'+identifier+'/files/'+file_id)
    assert own_download.status_code == 200
    assert own_download.content == b'print("MESURES_REELLES")\n'
    assert client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': '../secret.exe', 'content_base64': base64.b64encode(b'bad').decode()}).status_code == 422
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')
    seen = {}

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        seen['files'] = context['files']
        seen['computed_checks'] = context['computed_checks']
        return ({'content': 'Relecture statique, aucune exécution.', 'source_ids': [],
                 'file_ids': [file_id], 'assumptions': [], 'checks': ['Exécuter les tests'],
                 'limitations': ['Code non exécuté'], 'next_steps': ['Relire les sorties']}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    delegated = client.post('/api/work/tasks/'+identifier+'/delegate', json={'agent_id': agent['id']})
    assert delegated.status_code == 200
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
    assert 'MESURES_REELLES' in seen['files'][0]['excerpt']
    assert seen['computed_checks'][0]['result']['type'] == 'python_syntax'
    assert seen['computed_checks'][0]['result']['valid'] is True
    assert seen['computed_checks'][0]['result']['executed'] is False
    assert client.get('/api/work/tasks/'+identifier).json()['entries'][-1]['file_ids'] == [file_id]
    with TestClient(app) as other:
        registered = other.post('/api/auth/register', json={
            'email': 'file-other@example.test', 'name': 'Autre',
            'password': 'test-password-123'}).json()
        other.headers.update({'X-Passage-CSRF': registered['csrf']})
        assert other.get('/api/work/tasks/'+identifier+'/files/'+file_id).status_code == 404


def test_docx_and_pdf_manuscript_text_is_extracted_with_provenance(client):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r3-manuscripts', 'brief': 'Relire les preuves des résultats du manuscrit.'}).json()['id']
    doc = Document()
    doc.add_paragraph('Résultat expérimental à relire dans le manuscrit.')
    doc_bytes = io.BytesIO()
    doc.save(doc_bytes)
    doc_response = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'manuscrit.docx',
        'content_base64': base64.b64encode(doc_bytes.getvalue()).decode()})
    assert doc_response.status_code == 200, doc_response.text
    doc_item = doc_response.json()['file']
    assert doc_item['readable_by_agent'] and doc_item['extraction_method'] == 'docx'
    assert 'Résultat expérimental' in workflows.file_path(doc_item['id']+'.txt').read_text(encoding='utf-8')

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = writer._add_object(DictionaryObject({
        NameObject('/Type'): NameObject('/Font'),
        NameObject('/Subtype'): NameObject('/Type1'),
        NameObject('/BaseFont'): NameObject('/Helvetica')}))
    page[NameObject('/Resources')] = DictionaryObject({
        NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 700 Td (Passage PDF resultats reels) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    pdf_bytes = io.BytesIO()
    writer.write(pdf_bytes)
    assert 'Passage PDF' in (PdfReader(io.BytesIO(pdf_bytes.getvalue())).pages[0].extract_text() or '')
    pdf_response = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'article.pdf', 'content_base64': base64.b64encode(pdf_bytes.getvalue()).decode()})
    assert pdf_response.status_code == 200, pdf_response.text
    pdf_item = pdf_response.json()['file']
    assert pdf_item['readable_by_agent'] and pdf_item['extraction_method'] == 'pdf'
    assert 'Passage PDF' in workflows.file_path(pdf_item['id']+'.txt').read_text(encoding='utf-8')


def test_csv_profile_is_computed_and_available_to_agent(client, monkeypatch):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-data', 'brief': 'Analyser les températures mesurées dans les essais.'}).json()['id']
    csv_data = b'temps_s;temperature_c\n0;20\n1;22\n2;24\n3;\n'
    response = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'mesures.csv', 'content_base64': base64.b64encode(csv_data).decode()})
    assert response.status_code == 200, response.text
    file_id = response.json()['file']['id']
    calculated = client.post('/api/work/tasks/'+identifier+'/files/'+file_id+'/analyze')
    assert calculated.status_code == 200, calculated.text
    profile = calculated.json()['entry']['result']
    assert profile['type'] == 'table_profile'
    assert profile['rows_examined'] == 4
    assert profile['missing_by_column']['temperature_c'] == 1
    assert profile['numeric_by_column']['temperature_c']['mean'] == 22
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')
    seen = {}

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        seen['checks'] = context['computed_checks']
        return ({'content': 'Description des températures seulement.', 'source_ids': [],
                 'file_ids': [file_id], 'assumptions': [],
                 'checks': ['Comparer avec les conditions des essais'],
                 'limitations': ['Pas de conclusion causale'], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    delegated = client.post('/api/work/tasks/'+identifier+'/delegate', json={'agent_id': agent['id']})
    assert delegated.status_code == 200, delegated.text
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
    assert seen['checks'][0]['result']['numeric_by_column']['temperature_c']['mean'] == 22


def test_table_descriptive_analysis_is_reproducible_and_revision_guarded(client):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-data', 'brief': 'Comparer les mesures par groupe sans test inférentiel.'}).json()['id']
    csv_data = b'groupe;temperature_c\nA;20\nA;22\nB;30\nB;erreur\n;35\n'
    uploaded = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'mesures.csv', 'content_base64': base64.b64encode(csv_data).decode()})
    assert uploaded.status_code == 200, uploaded.text
    file_id = uploaded.json()['file']['id']
    base = '/api/work/tasks/'+identifier+'/files/'+file_id
    assert client.get(base+'/profile').json()['columns'] == ['groupe', 'temperature_c']
    revision = uploaded.json()['task']['revision']
    body = {'expected_revision': revision, 'value_column': 'temperature_c', 'group_column': 'groupe'}
    described = client.post(base+'/describe', json=body)
    assert described.status_code == 200, described.text
    result = described.json()['entry']['result']
    assert result['type'] == 'table_descriptive_v1'
    assert result['file_sha256'] == uploaded.json()['file']['sha256']
    assert result['rows_examined'] == 5 and result['rows_used'] == 3 and result['rows_excluded'] == 2
    assert [(group['group'], group['count'], group['mean']) for group in result['groups']] == [
        ('A', 2, 21), ('B', 1, 30)]
    assert result['groups'][0]['sample_std_dev'] == 2**0.5
    assert result['groups'][1]['sample_std_dev'] is None
    assert client.post(base+'/describe', json=body).status_code == 409
    invalid = {**body, 'expected_revision': described.json()['task']['revision'],
               'value_column': 'colonne_absente'}
    assert client.post(base+'/describe', json=invalid).status_code == 422


def test_agent_requests_local_table_analysis_before_final_draft(client, monkeypatch):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-data', 'brief': 'Décrire les températures par condition expérimentale.'}).json()['id']
    csv_data = b'condition;temperature_c\ntemoin;20\ntemoin;22\nessai;26\nessai;28\n'
    uploaded = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'conditions.csv', 'content_base64': base64.b64encode(csv_data).decode()})
    file_id = uploaded.json()['file']['id']
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')
    seen = []

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        seen.append(context)
        base = {'source_ids': [], 'file_ids': [file_id], 'assumptions': [],
                'checks': ['Comparer aux conditions réelles'], 'limitations': ['Description seulement'],
                'next_steps': []}
        if len(seen) == 1:
            return ({**base, 'content': 'Calcul demandé', 'analysis_file_id': file_id,
                     'analysis_value_column': 'temperature_c',
                     'analysis_group_column': 'condition'}, {'input_tokens': 5})
        assert context['computed_analysis']['groups'][0]['mean'] == 21
        assert context['computed_analysis']['groups'][1]['mean'] == 27
        return ({**base, 'content': 'Moyennes calculées : témoin 21, essai 27. '
                 'Cette description ne démontre pas un effet causal.'}, {'input_tokens': 8})

    monkeypatch.setattr(integrations, 'direct', direct)
    delegated = client.post('/api/work/tasks/'+identifier+'/delegate', json={'agent_id': agent['id']})
    assert delegated.status_code == 200, delegated.text
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
    entries = client.get('/api/work/tasks/'+identifier).json()['entries']
    computed, draft = entries[-2:]
    assert len(seen) == 2
    assert computed['kind'] == 'computed' and computed['requested_by_agent_id'] == agent['id']
    assert draft['analysis_entry_id'] == computed['id']
    assert 'témoin 21' in draft['content']


def test_source_anchors_verify_quotes_and_document_versions(client):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-literature', 'brief': 'Comparer les sources sur les batteries thermiques.'}).json()['id']
    text = 'Le protocole mesure la température toutes les dix secondes.\nLa limite vient du capteur.'
    uploaded = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'article.txt', 'content_base64': base64.b64encode(text.encode()).decode()})
    assert uploaded.status_code == 200, uploaded.text
    file_id = uploaded.json()['file']['id']
    revision = uploaded.json()['task']['revision']
    base = '/api/work/tasks/'+identifier+'/anchors'
    body = {'expected_revision': revision, 'source_type': 'file', 'source_id': file_id,
            'quote': 'Le protocole mesure la température toutes les dix secondes.',
            'claim': 'La mesure est périodique.'}
    anchored = client.post(base, json=body)
    assert anchored.status_code == 200, anchored.text
    assert anchored.json()['anchor']['current']
    assert anchored.json()['anchor']['source_sha256'] == uploaded.json()['file']['sha256']
    assert client.post(base, json=body).status_code == 409
    invalid = {**body, 'expected_revision': anchored.json()['task']['revision'],
               'quote': 'Le protocole prouve un rendement de 99 pour cent.'}
    assert client.post(base, json=invalid).status_code == 422
    other = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-writing', 'brief': 'Préparer une autre section sans cette source.'}).json()
    assert client.post('/api/work/tasks/'+other['id']+'/anchors', json={
        **body, 'expected_revision': other['revision']}).status_code == 422

    created = client.post('/api/work/tasks/'+identifier+'/documents', json={
        'title': 'Synthèse source', 'content': 'Une mesure indépendante confirme une hausse de température.'})
    assert created.status_code == 200, created.text
    doc = created.json()['document']
    doc_anchor = client.post(base, json={
        'expected_revision': created.json()['task']['revision'], 'source_type': 'document',
        'source_id': doc['id'], 'quote': 'Une mesure indépendante confirme une hausse de température.',
        'claim': 'Une hausse est mentionnée dans ce document.'})
    assert doc_anchor.status_code == 200, doc_anchor.text
    changed = client.put('/api/work/tasks/'+identifier+'/documents/'+doc['id'], json={
        'title': doc['title'], 'format': 'markdown', 'content': 'La mesure a été retirée.',
        'expected_version': doc['version']})
    assert changed.status_code == 200, changed.text
    current = client.get('/api/work/tasks/'+identifier).json()
    assert current['anchors'][0]['current'] and not current['anchors'][1]['current']
    delivered = client.post('/api/work/tasks/'+identifier+'/entries', json={
        'kind': 'deliverable', 'title': 'Synthèse provisoire',
        'content': 'Synthèse fondée sur les passages conservés.'})
    assert delivered.status_code == 200, delivered.text
    blocked = client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Sources vérifiées.'})
    assert blocked.status_code == 422 and 'passage sourcé actif est périmé' in blocked.text
    anchor_id = current['anchors'][1]['id']
    archived = client.put(base+'/'+anchor_id+'/status', json={
        'expected_revision': delivered.json()['task']['revision'], 'active': False})
    assert archived.status_code == 200 and not archived.json()['anchor']['active']
    assert client.put(base+'/'+anchor_id+'/status', json={
        'expected_revision': archived.json()['task']['revision'], 'active': True}).status_code == 422
    exported = client.get('/api/work/tasks/'+identifier+'/export.md')
    assert exported.status_code == 200
    assert 'La mesure est périodique.' in exported.text
    assert 'source périmée' in exported.text


def test_agent_source_quote_proposals_are_verified_before_adoption(client, monkeypatch):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-state-art', 'brief': 'Rédiger une synthèse sur les mesures de température.'}).json()['id']
    raw = b'La temperature augmente sous forte charge dans cette etude.\nUne confirmation est necessaire.'
    uploaded = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'source.txt', 'content_base64': base64.b64encode(raw).decode()})
    file_id = uploaded.json()['file']['id']
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        assert context['files'][0]['id'] == file_id
        return ({'content': 'La source suggère une hausse, à confirmer.',
                 'source_ids': [], 'file_ids': [file_id], 'assumptions': [],
                 'checks': ['Comparer avec un autre essai'], 'limitations': [], 'next_steps': [],
                 'citation_suggestions': [
                     ['file', file_id, 'La temperature augmente sous forte charge',
                      'Une hausse sous forte charge est rapportée.'],
                     ['file', file_id, 'Le rendement prouvé est de 99 pour cent',
                      'Un rendement de 99 pour cent serait démontré.']]}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    delegated = client.post('/api/work/tasks/'+identifier+'/delegate', json={'agent_id': agent['id']})
    assert delegated.status_code == 200, delegated.text
    assert wait_run(client, delegated.json()['run']['id'])['status'] == 'succeeded'
    current = client.get('/api/work/tasks/'+identifier).json()
    draft = current['entries'][-1]
    assert len(draft['citation_suggestions']) == 1
    assert '1 passage(s) proposés ont été écartés' in draft['limitations'][-1]
    proposal = draft['citation_suggestions'][0]
    adopted = client.post('/api/work/tasks/'+identifier+'/anchors', json={
        'expected_revision': current['revision'], 'source_type': proposal['source_type'],
        'source_id': proposal['source_id'], 'quote': proposal['quote'], 'claim': proposal['claim'],
        'source_entry_id': draft['id'], 'suggestion_index': 0})
    assert adopted.status_code == 200, adopted.text
    assert adopted.json()['anchor']['source_entry_id'] == draft['id']
    assert adopted.json()['anchor']['current']


def test_document_versions_agent_reprise_and_current_submission(client, monkeypatch):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-writing', 'brief': 'Rédiger la section de thèse sur les essais thermiques.'}).json()['id']
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')

    def draft(*args):
        return ({'content': 'Brouillon de section à corriger.', 'source_ids': [], 'file_ids': [],
                 'assumptions': [], 'checks': [], 'limitations': ['Non vérifié'],
                 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', draft)
    delegation = client.post('/api/work/tasks/'+identifier+'/delegate', json={'agent_id': agent['id']})
    assert delegation.status_code == 200
    assert wait_run(client, delegation.json()['run']['id'])['status'] == 'succeeded'
    entry_id = client.get('/api/work/tasks/'+identifier).json()['entries'][-1]['id']
    created = client.post('/api/work/tasks/'+identifier+'/documents', json={
        'title': 'Section résultats', 'source_entry_id': entry_id})
    assert created.status_code == 200, created.text
    doc = created.json()['document']
    assert doc['content'] == 'Brouillon de section à corriger.'
    assert doc['source_entry_id'] == entry_id and doc['version'] == 1
    doc_id = doc['id']
    changed = client.put('/api/work/tasks/'+identifier+'/documents/'+doc_id, json={
        'title': 'Section résultats', 'format': 'markdown',
        'content': 'Résultats corrigés avec valeurs vérifiées.', 'expected_version': 1})
    assert changed.status_code == 200, changed.text
    assert changed.json()['document']['version'] == 2
    assert client.put('/api/work/tasks/'+identifier+'/documents/'+doc_id, json={
        'title': 'Ancienne version', 'format': 'markdown', 'content': 'Écrasement',
        'expected_version': 1}).status_code == 409
    old = client.get('/api/work/tasks/'+identifier+'/documents/'+doc_id+'/versions/1')
    assert old.json()['content'] == 'Brouillon de section à corriger.'
    assert client.get('/api/work/tasks/'+identifier+'/documents/'+doc_id+'/versions/2').json()[
        'content'] == 'Résultats corrigés avec valeurs vérifiées.'
    submitted = client.post('/api/work/tasks/'+identifier+'/documents/'+doc_id+'/submit')
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()['entry']['document_version'] == 2
    answer_worksheet(client, identifier)
    for index in range(4):
        assert verified_step(client, identifier, index).status_code == 200
    accepted = client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Texte et preuves relus par les auteurs.'})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()['task']['approved_entry_id'] == submitted.json()['entry']['id']
    export = client.get('/api/work/tasks/'+identifier+'/export.md')
    assert 'Résultats corrigés avec valeurs vérifiées.' in export.text
    changed_again = client.put('/api/work/tasks/'+identifier+'/documents/'+doc_id, json={
        'title': 'Section résultats', 'format': 'markdown',
        'content': 'Troisième version avec nouvelles vérifications.', 'expected_version': 2})
    assert changed_again.status_code == 200
    assert changed_again.json()['task']['status'] == 'in_progress'
    assert changed_again.json()['task']['approved_entry_id'] is None
    assert client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Texte relu.'}).status_code == 422
    assert client.post('/api/work/tasks/'+identifier+'/documents/'+doc_id+'/submit').status_code == 200
    assert client.post('/api/work/tasks/'+identifier+'/complete', json={
        'decision': 'accept', 'note': 'Nouvelle version relue.'}).status_code == 200


def test_document_import_agent_context_and_reviewer_comments_are_scoped(client, monkeypatch):
    pid = project(client)
    identifier = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-experiment-design',
        'brief': 'Préparer le protocole des essais à température variable.'}).json()['id']
    uploaded = client.post('/api/work/tasks/'+identifier+'/files', json={
        'name': 'protocole.txt',
        'content_base64': base64.b64encode(b'Variable : temperature. Temoin : cellule identique.').decode()})
    file_id = uploaded.json()['file']['id']
    created = client.post('/api/work/tasks/'+identifier+'/documents', json={
        'title': 'Protocole de travail', 'source_file_id': file_id})
    assert created.status_code == 200, created.text
    doc_id = created.json()['document']['id']
    assert created.json()['document']['content'].startswith('Variable : temperature')
    assert client.post('/api/work/tasks/'+identifier+'/documents', json={
        'title': 'Import interdit', 'source_file_id': file_id,
        'content': 'Texte qui remplace la source'}).status_code == 422
    other_id = client.post('/api/work/projects/'+pid, json={
        'type_id': 'r1-notebook', 'brief': 'Consigner un autre essai.'}).json()['id']
    assert client.post('/api/work/tasks/'+other_id+'/documents', json={
        'title': 'Source hors tâche', 'source_file_id': file_id}).status_code == 422
    agent = next(a for a in store.all_of('agent') if a['active'] and a['engine'] == 'direct')
    seen = {}

    def direct(brain, prompt, context, schema, tools, invoke, trace):
        seen['documents'] = context['documents']
        return ({'content': 'Contrôles proposés pour le protocole.', 'source_ids': [],
                 'file_ids': [], 'assumptions': [], 'checks': ['Faire relire'],
                 'limitations': [], 'next_steps': []}, {})

    monkeypatch.setattr(integrations, 'direct', direct)
    response = client.post('/api/work/tasks/'+identifier+'/delegate', json={'agent_id': agent['id']})
    assert response.status_code == 200
    assert wait_run(client, response.json()['run']['id'])['status'] == 'succeeded'
    assert seen['documents'][0]['id'] == doc_id
    assert 'Variable : temperature' in seen['documents'][0]['excerpt']
    assert client.get('/api/work/tasks/'+identifier).json()['entries'][-1][
        'document_context'][0]['version'] == 1
    with TestClient(app) as reviewer:
        registered = reviewer.post('/api/auth/register', json={
            'email': 'document-reviewer@example.test', 'name': 'Relecteur',
            'password': 'test-password-123'}).json()
        reviewer.headers.update({'X-Passage-CSRF': registered['csrf']})
        assert reviewer.get('/api/work/tasks/'+identifier+'/documents/'+doc_id).status_code == 404
        assert client.post('/api/work/tasks/'+identifier+'/share', json={
            'email': 'document-reviewer@example.test', 'role': 'reviewer'}).status_code == 422
        assert client.patch('/api/auth/users/'+registered['user']['id'], json={'role': 'lab'}).status_code == 200
        assert client.post('/api/work/tasks/'+identifier+'/share', json={
            'email': 'document-reviewer@example.test', 'role': 'reviewer'}).status_code == 200
        assert reviewer.get('/api/work/tasks/'+identifier+'/documents/'+doc_id).status_code == 200
        assert reviewer.put('/api/work/tasks/'+identifier+'/documents/'+doc_id, json={
            'title': 'Modification interdite', 'format': 'plain', 'content': 'Texte',
            'expected_version': 1}).status_code == 403
        assert reviewer.post('/api/work/tasks/'+identifier+'/documents/'+doc_id+'/submit').status_code == 403
        assert reviewer.post('/api/work/tasks/'+identifier+'/documents/'+doc_id+'/comments', json={
            'version': 1, 'quote': 'passage absent', 'content': 'Observation.'}).status_code == 422
        comment = reviewer.post('/api/work/tasks/'+identifier+'/documents/'+doc_id+'/comments', json={
            'version': 1, 'quote': 'Variable : temperature',
            'content': 'Préciser les unités et la plage.'})
        assert comment.status_code == 200, comment.text
        assert comment.json()['comment']['actor_id'] == registered['user']['id']
        assert client.get('/api/work/tasks/'+identifier+'/documents/'+doc_id).json()['comments'][0][
            'quote'] == 'Variable : temperature'
        assert 'Préciser les unités et la plage.' in client.get(
            '/api/work/tasks/'+identifier+'/export.md').text
