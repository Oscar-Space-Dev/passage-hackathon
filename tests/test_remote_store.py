"""Persistence contract for stateless Render deployments."""
import sqlite3
import sys
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from passage import store, workflows
from passage.partner_mcp import cipher


def test_render_requires_remote_database(monkeypatch, tmp_path):
    monkeypatch.setenv('PASSAGE_DB', str(tmp_path / 'ephemeral.db'))
    monkeypatch.setenv('PASSAGE_REQUIRE_REMOTE_DB', '1')
    monkeypatch.delenv('TURSO_DATABASE_URL', raising=False)
    with pytest.raises(RuntimeError, match='TURSO_DATABASE_URL'):
        store.init()
    assert not (tmp_path / 'ephemeral.db').exists()


def test_remote_data_and_encryption_survive_reconnect(monkeypatch, tmp_path):
    remote_db = tmp_path / 'remote.db'
    opened = []

    def fake_connect(url, *, auth_token):
        opened.append((url, auth_token))
        return sqlite3.connect(remote_db)

    monkeypatch.setitem(sys.modules, 'turso_serverless', SimpleNamespace(connect=fake_connect))
    monkeypatch.setenv('TURSO_DATABASE_URL', 'turso://passage-example.turso.io')
    monkeypatch.setenv('TURSO_AUTH_TOKEN', 'test-only-token')
    monkeypatch.setenv('PASSAGE_ENCRYPTION_KEY', Fernet.generate_key().decode())
    monkeypatch.setenv('PASSAGE_DB', str(tmp_path / 'ephemeral.db'))
    store.init()
    store.put('project', {'id': 'prj_persist', 'name': 'Thèse'})
    encrypted = cipher().encrypt(b'oauth test-only').decode()
    store.put('oauth_secret', {'id': 'test', 'encrypted': encrypted})
    attachment = workflows.file_path('wf_example')
    attachment.parent.mkdir(parents=True, exist_ok=True)
    attachment.write_bytes(b'document de these')
    workflows.persist_file('wf_example', attachment.read_bytes())
    attachment.unlink()

    assert store.get('project', 'prj_persist')['name'] == 'Thèse'
    assert cipher().decrypt(store.get('oauth_secret', 'test')['encrypted'].encode()) == b'oauth test-only'
    assert workflows.file_path('wf_example').read_bytes() == b'document de these'
    assert not (tmp_path / 'ephemeral.db').exists()
    assert len(opened) >= 3


def test_remote_missing_encryption_key_fails_before_write(monkeypatch):
    monkeypatch.setenv('TURSO_DATABASE_URL', 'turso://passage-example.turso.io')
    monkeypatch.setenv('TURSO_AUTH_TOKEN', 'test-only-token')
    monkeypatch.delenv('PASSAGE_ENCRYPTION_KEY', raising=False)
    with pytest.raises(RuntimeError, match='PASSAGE_ENCRYPTION_KEY'):
        store.init()
    monkeypatch.setenv('PASSAGE_ENCRYPTION_KEY', 'invalid-key')
    with pytest.raises(RuntimeError, match='clé Fernet valide'):
        store.init()
