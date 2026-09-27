"""Focused regression cases from the public deployment audit."""
import base64
import concurrent.futures
import pytest
from fastapi import HTTPException
from passage import agents, auth, guide, store, workflows


def owned_work(client):
    user = client.get('/api/auth/status').json()['user']
    project = client.post('/api/projects', json={'name':'Audit','objective':'Vérifier les droits de modification du travail.'}).json()
    row = client.post('/api/work/projects/'+project['id'], json={'type_id':'r1-code','brief':'Vérifier un programme de recherche.'}).json()
    return user, project, row


def test_private_agent_cannot_become_coordinator(client):
    _, project, _ = owned_work(client)
    agent = dict(store.all_of('agent')[0], id='private-audit', owner_id='someone-else', active=True, engine='direct')
    store.put('agent',agent)
    r=client.patch('/api/projects/'+project['id']+'/coordinator',json={'coordinator_id':agent['id']})
    assert r.status_code == 422
    assert agent['id'] not in store.get('project',project['id'])['agent_ids']


def test_reviewer_cannot_reopen_with_entries_or_files(client):
    owner, _, row = owned_work(client)
    reviewer={'id':'audit-reviewer','role':'lab'}
    row=store.get('work_item',row['id'])
    row.update(status='done', approved_entry_id='approved',shares=[{'user_id':reviewer['id'],'role':'reviewer'}])
    store.put('work_item',row)
    token=auth.CURRENT_USER.set(reviewer)
    try:
        with pytest.raises(HTTPException) as err:
            workflows.upload_file(row['id'], workflows.WorkFileInput(name='test.txt',content_base64=base64.b64encode(b'test').decode()))
        assert err.value.status_code==403
        with pytest.raises(HTTPException) as err:
            workflows._add_entry(row['id'], workflows.WorkEntry(kind='note',title='Note',content='Un commentaire'), 'human')
        assert err.value.status_code==403
        assert store.get('work_item',row['id'])==row
    finally: auth.CURRENT_USER.reset(token)


def test_access_derives_stale_state_without_writing(client,monkeypatch):
    owner,_, row=owned_work(client)
    row=store.get('work_item',row['id'])
    row.update(status='done',approved_entry_id='approved')
    store.put('work_item',row)
    monkeypatch.setattr(workflows,'linked_sources_current',lambda _:False)
    token=auth.CURRENT_USER.set(owner)
    try:
        view=workflows.task(row['id'])
        assert view['status']=='in_progress' and view['approved_entry_id'] is None
        assert view['revision']==row['revision']
        assert store.get('work_item',row['id'])==row
    finally: auth.CURRENT_USER.reset(token)


def test_public_lab_cannot_mutate_shared_catalog(client,monkeypatch):
    monkeypatch.setenv('PASSAGE_PUBLIC_SIGNUP','1')
    user=client.get('/api/auth/status').json()['user']
    saved=store.get('user',user['id']); saved['role']='lab';store.put('user',saved)
    thesis=store.all_of('thesis')[0]
    checks=[('patch','/api/laboratory',{'lab_name':'Changed'}),
      ('patch','/api/theses/'+thesis['id']+'/visibility',{'visible':False}),
      ('patch','/api/theses/'+thesis['id']+'/correction',{'summary':'Correction du résumé public.'}),
      ('post','/api/import',{'query':'batteries','lab_filter':'LRCS','limit':1})]
    for method,path,body in checks:
        response=getattr(client,method)(path,json=body)
        assert response.status_code==403, (path,response.text)
    assert store.get('thesis',thesis['id'])==thesis


def test_conversation_lock_is_scoped_and_reentrant():
    token=auth.CURRENT_USER.set({'id':'account-a'})
    try:
        first=guide.conversation_lock()
        with first:
            assert guide.conversation_lock() is first
            def other():
                t=auth.CURRENT_USER.set({'id':'account-b'})
                try:
                    second=guide.conversation_lock()
                    with second: return second is not first
                finally: auth.CURRENT_USER.reset(t)
            with concurrent.futures.ThreadPoolExecutor() as pool:
                assert pool.submit(other).result(timeout=2)
    finally: auth.CURRENT_USER.reset(token)


def test_filtered_storage_binds_values_and_uses_index(client):
    store.put('audit_row',{'id':'one','project_id':"p' OR 1=1 --"})
    store.put('audit_row',{'id':'two','project_id':'other'})
    assert [r['id'] for r in store.where('audit_row',project_id="p' OR 1=1 --")]==['one']
    with pytest.raises(ValueError): store.where('audit_row',**{"x') OR 1=1 --":'anything'})
    with store.reader() as c:
        plan=c.execute("EXPLAIN QUERY PLAN SELECT body FROM objects WHERE kind=? AND json_extract(body,'$.project_id') IS ?",('audit_row','other')).fetchall()
    assert any('objects_project_id' in str(r[3]) for r in plan)
