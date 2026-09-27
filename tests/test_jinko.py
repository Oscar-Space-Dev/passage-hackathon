import json
from types import SimpleNamespace

import pytest
from jinko import JinkoClient
from jinko.transport import JinkoTransport, ResponsePayload

from passage import auth, codex_brain, integrations, jinko_bridge, store


def auth_client(config):
    def sender(request, timeout):
        assert request.full_url == 'https://api.jinko.ai/app/v1/auth/check'
        assert request.get_method() == 'GET'
        assert timeout == 20
        return ResponsePayload(200, {}, {'status': 'ok', 'apiKey': {
            'id': 'key-1', 'name': 'Passage test', 'role': 'read', 'expiresAt': None,
            'projectId': config['project_id'], 'organizationId': 'org-test'}})
    transport = JinkoTransport(api_key=config['api_key'], project_id=config['project_id'],
        base_url='https://api.jinko.ai', timeout=20, sender=sender)
    return JinkoClient(transport=transport)


def connect(client, monkeypatch):
    monkeypatch.setattr(jinko_bridge, 'sdk', auth_client)
    result = client.put('/api/jinko/account', json={'api_key': 'test-jinko-secret', 'project_id': 'project-a'})
    assert result.status_code == 200, result.text
    return result


def test_real_sdk_auth_contract_and_private_storage(client, monkeypatch):
    result = connect(client, monkeypatch)
    assert result.json()['configured'] is True
    assert 'test-jinko-secret' not in result.text
    stored = store.all_of('jinko_account')
    assert len(stored) == 1 and 'test-jinko-secret' not in json.dumps(stored)
    second = client.post('/api/auth/register', json={'email': 'second@example.test',
        'password': 'another-long-password', 'name': 'Second'}).json()
    client.headers['X-Passage-CSRF'] = second['csrf']
    assert client.get('/api/jinko/account').json()['configured'] is False
    assert client.post('/api/jinko/read', json={'operation': 'models', 'sid': '', 'query': '',
        'revision': None, 'explanation': ''}).status_code == 409
    assert len(store.all_of('jinko_account')) == 1


def test_failed_connection_keeps_previous_key(client, monkeypatch):
    connect(client, monkeypatch)
    original = store.all_of('jinko_account')
    from jinko import AuthenticationError
    def denied(config):
        raise AuthenticationError('request included test-jinko-secret')
    monkeypatch.setattr(jinko_bridge, 'sdk', denied)
    result = client.put('/api/jinko/account', json={'api_key': 'replacement-secret', 'project_id': 'project-b'})
    assert result.status_code == 502
    assert 'secret' not in result.text
    assert store.all_of('jinko_account') == original


def test_sdk_reads_feed_agent_and_never_launch_trials(client, monkeypatch):
    connect(client, monkeypatch)
    user = store.all_of('user')[0]
    token = auth.CURRENT_USER.set(user)
    reads = []
    class Page(list):
        has_next = False
    model = SimpleNamespace(sid='cm-1', name='Existing model', type='ComputationalModel',
                            content=lambda: {'parameters': [{'name': 'existing', 'unit': 'h'}]})
    class SDK:
        def list_models(self, **kw):
            reads.append(('list', kw)); return Page([model])
        def get_model(self, sid, revision=None):
            reads.append(('get', sid, revision)); return model
    monkeypatch.setattr(jinko_bridge, 'sdk', lambda config: SDK())
    choices = iter([
        {'operation': 'models', 'query': '', 'sid': '', 'revision': None, 'explanation': 'Find model'},
        {'operation': 'model', 'query': '', 'sid': 'cm-1', 'revision': 2, 'explanation': 'Read model'},
        {'operation': 'finish', 'query': '', 'sid': '', 'revision': None, 'explanation': ''}])
    prompts = []
    def model_call(agent, prompt, context, schema, specs, invoke, trace):
        prompts.append(context)
        if 'reads_remaining' in context:
            return next(choices), {}
        return {'result': 'review'}, {'actual_model': 'test'}
    monkeypatch.setattr(integrations, '_direct', model_call)
    try:
        answer, usage = integrations.direct({'tools': ['jinko.read']}, 'review', {'question': 'Review my model'},
            {}, [], None, lambda _: None)
        assert answer['result'] == 'review'
        assert reads == [('list', {'name': None, 'limit': 20}), ('get', 'cm-1', 2)]
        assert prompts[-1]['jinko_observations'][1]['data']['parameters'][0]['unit'] == 'h'
        assert 'test-jinko-secret' not in json.dumps(prompts)
        assert len(usage['jinko']['observations']) == 2
        with pytest.raises(integrations.IntegrationError, match='absent'):
            jinko_bridge.enrich({}, '', {}, lambda *args: ({'operation': 'model', 'sid': 'cm-invented',
                'query': '', 'revision': None, 'explanation': ''}, {}), lambda _: None)
    finally:
        auth.CURRENT_USER.reset(token)


def test_agent_requires_verified_accounts_and_has_personal_harness(client, monkeypatch):
    assert client.post('/api/jinko/agent', json={}).status_code == 409
    connect(client, monkeypatch)
    monkeypatch.setattr(codex_brain, 'status', lambda: {'connected': False})
    assert client.post('/api/jinko/agent', json={}).status_code == 409
    monkeypatch.setattr(codex_brain, 'status', lambda: {'connected': True})
    response = client.post('/api/jinko/agent', json={})
    assert response.status_code == 200, response.text
    agent = store.get('agent', response.json()['agent_id'])
    assert agent['provider'] == 'codex'
    assert agent['owner_id'] == store.all_of('user')[0]['id']
    assert 'jinko.read' in agent['tools']
    assert agent['creator_version'] and agent['work_specialties']
    assert store.get('revision', agent['id']+':1')
    again = client.post('/api/jinko/agent', json={}).json()
    assert again['status'] == 'reused' and again['agent_id'] == agent['id']
    from passage.schemas import AgentInput
    payload = {key: value for key, value in agent.items() if key in AgentInput.model_fields}
    payload['name'] = 'My revised Jinkō agent'
    updated = client.put('/api/agents/'+agent['id'], json=payload, headers={'X-Passage-Role': 'admin'})
    assert updated.status_code == 200, updated.text
    assert updated.json()['owner_id'] == agent['owner_id']
    stranger = client.post('/api/auth/register', json={'email': 'admin2@example.test',
        'password': 'another-long-password', 'name': 'Admin two'}).json()
    stranger_record = store.get('user', stranger['user']['id'])
    stranger_record['role'] = 'admin'
    store.put('user', stranger_record)
    client.headers.update({'X-Passage-CSRF': stranger['csrf'], 'X-Passage-Role': 'admin'})
    assert client.get('/api/agents/'+agent['id']).status_code == 404
    assert client.get('/api/agents/'+agent['id']+'/export/json').status_code == 404
    assert client.put('/api/agents/'+agent['id'], json=payload).status_code == 404
    assert client.post('/api/agents/'+agent['id']+'/publish-dust').status_code == 404


def test_no_generic_sdk_escape_hatch_or_write_api(client, monkeypatch):
    connect(client, monkeypatch)
    assert client.post('/api/jinko/read', json={'operation': 'run', 'sid': 'trial-1', 'query': '',
        'revision': None, 'explanation': ''}).status_code == 422
    result = jinko_bridge.bounded({'large': 'a'*25000})
    assert result['truncated'] and len(result['excerpt']) == 24000
