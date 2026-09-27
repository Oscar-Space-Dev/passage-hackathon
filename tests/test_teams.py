from passage import store


def register(client, email):
    response = client.post('/api/auth/register', json={'email': email, 'name': email.split('@')[0],
        'password': 'long-test-password', 'account_type': 'researcher'})
    assert response.status_code == 200
    user = response.json()
    client.headers['X-Passage-CSRF'] = user['csrf']
    return user['user']['id']


def login(client, email, password='long-test-password'):
    response = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200
    client.headers['X-Passage-CSRF'] = response.json()['csrf']


def team(client):
    response = client.post('/api/teams', json={'name': 'Research group', 'kind': 'lab'})
    assert response.status_code == 200
    return response.json()['id']


def invite(client, identifier, email):
    response = client.post('/api/teams/'+identifier+'/invitations', json={'email': email})
    assert response.status_code == 200, response.text
    result = response.json()
    return result, result['url'].split('#team-invite=')[1]


def test_team_invite_is_bound_to_recipient_and_does_not_share_private_projects(client):
    private = client.post('/api/projects', json={'name': 'Private work', 'objective': 'Prepare my private research work.'}).json()
    identifier = team(client)
    invitation, token = invite(client, identifier, 'invitee@example.test')
    assert token not in str(store.all_of('team_invite'))
    assert token not in client.get('/api/teams').text
    register(client, 'outsider@example.test')
    assert client.get('/api/teams').json() == []
    assert client.post('/api/teams/invitations/preview', json={'token': token}).status_code == 403
    assert client.post('/api/teams/invitations/accept', json={'token': token}).status_code == 403
    invitee = register(client, 'invitee@example.test')
    assert client.post('/api/teams/invitations/preview', json={'token': token}).json()['team_name'] == 'Research group'
    result = client.post('/api/teams/invitations/accept', json={'token': token})
    assert result.status_code == 200, result.text
    assert invitee in [member['id'] for member in result.json()['members']]
    assert result.json()['can_manage'] is False
    assert 'invitations' not in result.json()
    assert client.get('/api/projects/'+private['id']).status_code == 404
    assert client.get('/api/projects').json() == []
    assert client.post('/api/teams/invitations/accept', json={'token': token}).status_code == 410
    assert client.post('/api/teams/'+identifier+'/invitations', json={'email': 'third@example.test'}).status_code == 403
    owner_id = result.json()['owner_id']
    assert client.delete('/api/teams/'+identifier+'/members/'+owner_id).status_code == 403
    assert client.delete('/api/teams/'+identifier+'/members/'+invitee).status_code == 200
    assert client.get('/api/teams').json() == []


def test_revoked_expired_and_replaced_invites_cannot_be_used(client):
    identifier = team(client)
    original, token1 = invite(client, identifier, 'invitee@example.test')
    replacement, token2 = invite(client, identifier, 'invitee@example.test')
    assert store.get('team_invite', original['id'])['status'] == 'revoked'
    assert client.delete('/api/teams/'+identifier+'/invitations/'+replacement['id']).status_code == 200
    expiring, token3 = invite(client, identifier, 'invitee@example.test')
    row = store.get('team_invite', expiring['id'])
    row['expires_at'] = 0
    store.put('team_invite', row)
    register(client, 'invitee@example.test')
    for token in (token1, token2, token3):
        assert client.post('/api/teams/invitations/accept', json={'token': token}).status_code == 410


def test_only_team_owner_can_remove_other_members(client):
    identifier = team(client)
    _, token = invite(client, identifier, 'invitee@example.test')
    invitee = register(client, 'invitee@example.test')
    client.post('/api/teams/invitations/accept', json={'token': token})
    login(client, 'admin@example.test', 'test-password-123')
    owner_id = client.get('/api/auth/status').json()['user']['id']
    assert client.delete('/api/teams/'+identifier+'/members/'+owner_id).status_code == 409
    assert client.delete('/api/teams/'+identifier+'/members/'+invitee).status_code == 200
    login(client, 'invitee@example.test')
    assert client.get('/api/teams').json() == []
