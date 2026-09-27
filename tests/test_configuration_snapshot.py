from passage import integrations, store


def test_state_reads_installation_configuration_once(client, monkeypatch):
    calls = []
    original_all = store.all_of
    original_get = store.get
    def all_of(kind):
        if kind == 'installation_setting': calls.append('bulk')
        return original_all(kind)
    def get(kind, identifier, conn=None):
        if kind == 'installation_setting': calls.append('individual')
        return original_get(kind, identifier, conn)
    monkeypatch.setattr(store, 'all_of', all_of)
    monkeypatch.setattr(store, 'get', get)
    response = client.get('/api/state')
    assert response.status_code == 200
    assert calls == ['bulk']
    assert integrations.CONFIGURATION_SNAPSHOT.get() is None


def test_settings_snapshot_is_not_shared_between_operations(client):
    integrations.persist_settings({'DUST_WORKSPACE_ID': 'first'})
    assert integrations.statuses()['values']['DUST_WORKSPACE_ID'] == 'first'
    integrations.persist_settings({'DUST_WORKSPACE_ID': 'second'})
    assert integrations.statuses()['values']['DUST_WORKSPACE_ID'] == 'second'
    assert integrations.CONFIGURATION_SNAPSHOT.get() is None
