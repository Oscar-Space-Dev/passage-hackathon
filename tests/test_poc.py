import copy
import json
import time
import tomllib
from unittest.mock import Mock
import pytest
import requests
from passage import agents, integrations, sources, store

THERMAL='2014DIJOS078'
SULFUR='2019PSLEC037'
PRINT='s352032'
NEED='En charge rapide, nos cellules dépassent 45 °C. Limiter l’échauffement sans alourdir le pack.'
LAB={'X-Passage-Role':'lab'}
COMPANY={'X-Passage-Role':'company'}
ADMIN={'X-Passage-Role':'admin'}

def wait(client, run, headers=LAB):
    for _ in range(100):
        r=client.get('/api/runs/'+run['id'],headers=headers).json()
        if r['status'] not in ('queued','running'):
            return r
        time.sleep(.02)
    pytest.fail('Job did not terminate')

def run(client, role, thesis_id=THERMAL, problem=NEED, mode='demo', headers=LAB):
    r=client.post('/api/runs',headers=headers,json={'role':role,'thesis_id':thesis_id,'problem':problem,'mode':mode})
    assert r.status_code==200, r.text
    result=wait(client,r.json(),headers)
    assert result['status']=='succeeded',result
    return result

def test_corpus_real_source_and_lab_aliases(client):
    state=client.get('/api/state').json()
    assert len(state['theses'])>=10
    assert state['stats']['lab']==61
    by_id={t['id']:t for t in state['theses']}
    assert {THERMAL,SULFUR,PRINT} <= by_id.keys()
    assert 'DRIVE' in ' '.join(by_id[THERMAL]['labs'])
    assert not by_id[THERMAL]['is_lab']
    assert by_id[PRINT]['status']=='enCours'
    assert by_id[PRINT]['keywords']
    assert all(t['collected_at'] and t['source_url'].startswith('https://theses.fr/') for t in by_id.values())

def test_import_preserves_human_data_and_is_idempotent(client,monkeypatch):
    old=store.get('thesis',PRINT)
    old.update(correction='Correction validée par le doctorant',visible=True)
    store.put('thesis',old)
    row=old['raw']['search']
    def response(path,**kwargs):
        return {'theses':[row],'totalHits':1} if path=='/recherche/' else old['raw']['detail']
    monkeypatch.setattr(sources,'request',response)
    first=sources.import_lab('LRCS Amiens','Réactivité et Chimie des Solides',100)
    second=sources.import_lab('LRCS Amiens','Réactivité et Chimie des Solides',100)
    assert first['retained']==1 and second['updated']==1 and second['added']==0
    assert store.get('thesis',PRINT)['correction']==old['correction']
    assert store.get('thesis',PRINT)['visible']

def test_import_detail_error_retains_previous_abstract(client,monkeypatch):
    old=store.get('thesis',PRINT)
    def response(path,**kwargs):
        if path=='/recherche/':return {'theses':[old['raw']['search']],'totalHits':1}
        raise requests.Timeout()
    monkeypatch.setattr(sources,'request',response)
    result=sources.import_lab('LRCS','Réactivité Chimie Solides',100)
    assert len(result['errors'])==1
    assert store.get('thesis',PRINT)['abstract']==old['abstract']

def test_private_sources_absent_from_company_and_revoked_exports(client):
    r=run(client,'incorporation',headers=COMPANY)['result']
    assert client.patch('/api/theses/'+THERMAL+'/visibility',headers=COMPANY,json={'visible':False}).status_code==403
    assert client.patch('/api/theses/'+THERMAL+'/visibility',headers=LAB,json={'visible':False}).status_code==200
    assert THERMAL not in {t['id'] for t in client.get('/api/state',headers=COMPANY).json()['theses']}
    assert client.get('/api/theses/'+THERMAL,headers=COMPANY).status_code==404
    assert client.get('/api/reports/'+r['id']+'/export',headers=COMPANY).status_code==404
    assert client.post('/api/runs',headers=COMPANY,json={'role':'incorporation','thesis_id':THERMAL,'problem':NEED}).status_code==404

def test_correction_preserved_after_reading(client):
    text='Résumé scientifique corrigé par le doctorant.'
    client.patch('/api/theses/'+THERMAL+'/correction',headers={'X-Passage-Role':'researcher'},json={'summary':text})
    run(client,'lecteur')
    result=client.get('/api/theses/'+THERMAL).json()
    assert result['thesis']['correction']==text
    assert result['corrections'][0]['summary']==text
    assert result['thesis']['abstract']!=text

def test_three_reference_cases_and_out_of_scope(client):
    r=run(client,'rapprochement',None,headers=COMPANY)['result']
    scores={m['thesis_id']:m['score'] for m in r['content']['matches']}
    assert scores[THERMAL]>scores[SULFUR]>scores[PRINT]
    assert r['mode']=='demo' and r['model']=='Aucun — simulation'
    assert all(m['reason'] for m in r['content']['matches'])
    assert agents.rank_score(store.get('thesis',THERMAL),'Créer une application de comptabilité pour restaurants')==0

def test_dossiers_export_trust_sections(client):
    for role in ('lecteur','opportunite','incorporation'):
        r=run(client,role)['result']
        assert r['content']['checks'] and r['content']['uncertainty']
        doc=client.get('/api/reports/'+r['id']+'/export').text
        assert 'SIMULATION' in doc and 'https://theses.fr/'+THERMAL in doc
        assert all(x in doc for x in ['Pourquoi cette thèse','Ce qui est documenté','À vérifier','Contacts','Confiance'])

def test_visits_and_proposal_decisions(client):
    for _ in range(2):client.post('/api/theses/'+THERMAL+'/visit',headers=COMPANY)
    assert client.get('/api/theses/'+THERMAL).json()['visits']==1
    r=run(client,'incorporation',headers=COMPANY)['result']
    body={'thesis_id':THERMAL,'programme_id':'pack-2027','report_id':r['id']}
    p=client.post('/api/proposals',headers=COMPANY,json=body).json()
    assert p['status']=='pending' and not store.all_of('note')
    assert client.post('/api/proposals',headers=COMPANY,json=body).json()['id']==p['id']
    client.post('/api/proposals/'+p['id']+'/decision',headers=COMPANY,json={'decision':'rejected'})
    assert not store.all_of('note')
    p=client.post('/api/proposals',headers=COMPANY,json=body).json()
    for _ in range(2):
        assert client.post('/api/proposals/'+p['id']+'/decision',headers=COMPANY,json={'decision':'accepted'}).status_code==200
    assert len(store.all_of('note'))==1
    assert client.get('/api/theses/'+THERMAL).json()['proposals'][-1]['status']=='accepted'

def test_agent_revisions_snapshots_activation_and_tools(client):
    before=run(client,'lecteur')
    a=client.get('/api/agents/lecteur',headers=ADMIN).json()['agent']
    body={k:v for k,v in a.items() if k not in ('id','revision')}
    body['memory']='Retenir que les preuves du manuscrit doivent être vérifiées.'
    response=client.put('/api/agents/lecteur',headers=ADMIN,json=body)
    assert response.status_code==200,response.text
    assert response.json()['revision']==2
    assert client.get('/api/runs/'+before['id']).json()['agent_snapshot']['revision']==1
    assert body['memory'] in client.get('/api/agents/lecteur',headers=ADMIN).json()['assembled']
    body['name']='Autre lecteur';new=client.post('/api/agents',headers=ADMIN,json=body).json()
    assert not store.get('agent','lecteur')['active'] and store.get('agent',new['id'])['active']
    body['tools']=[]
    client.put('/api/agents/'+new['id'],headers=ADMIN,json=body)
    assert client.post('/api/runs',json={'role':'lecteur','thesis_id':THERMAL}).status_code==409

def test_super_skill_creator_draft_check_activation_and_revision(client):
    guide=client.get('/api/agents/creator/blueprint/lecteur',headers=ADMIN)
    assert guide.status_code==200
    draft=guide.json()['agent']
    assert not draft['active'] and len(guide.json()['steps'])==6
    body={k:v for k,v in draft.items() if k not in ('id','revision')}
    check=client.post('/api/agents/creator/check',headers=ADMIN,json=body)
    assert check.status_code==200 and 'Déclencheur' in ' '.join(check.json()['issues'])
    saved=client.post('/api/agents',headers=ADMIN,json=body)
    assert saved.status_code==200
    identifier=saved.json()['id']
    body['active']=True
    assert client.put('/api/agents/'+identifier,headers=ADMIN,json=body).status_code==422
    body.update(trigger='Sur demande du doctorant.',reads='Notices publiées du projet.',
                boundaries='Le doctorant valide les conclusions.',checkpoint='Validation avant remise.',
                deliverables='Note de lecture sourcée.',context='Thèse du projet et sources autorisées.')
    assert client.post('/api/agents/creator/check',headers=ADMIN,json=body).json()['issues']==[]
    active=client.put('/api/agents/'+identifier,headers=ADMIN,json=body)
    assert active.status_code==200 and active.json()['revision']==2
    detail=client.get('/api/agents/'+identifier,headers=ADMIN).json()
    assert 'DÉCLENCHEUR\nSur demande du doctorant.' in detail['assembled']
    assert len(detail['revisions'])==2
    body['creator_version']=''
    assert client.put('/api/agents/'+identifier,headers=ADMIN,json=body).status_code==422

def test_live_missing_key_no_silent_demo(client):
    response=client.post('/api/runs',json={'role':'lecteur','thesis_id':THERMAL,'mode':'live'})
    assert response.status_code==409
    assert store.all_of('report')==[]

def test_live_openai_contract_uses_harness_and_validates(client,monkeypatch):
    integrations.SESSION_SECRETS['OPENAI_API_KEY']='test-only-key'
    a=store.get('agent','lecteur');a.update(memory='MEMOIRE-TEST',provider='openai',model='gpt-4.1-mini');store.put('agent',a)
    report=agents.demo_report('lecteur',[store.get('thesis',THERMAL)])
    calls=[]
    def fake_http(method,url,**kwargs):
        calls.append(kwargs['json'])
        return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(report)}]}],'usage':{'total_tokens':100}}
    monkeypatch.setattr(integrations,'http',fake_http)
    result=run(client,'lecteur',mode='live')['result']
    assert 'MEMOIRE-TEST' in calls[0]['instructions']
    assert calls[0]['text']['format']['strict'] and calls[0]['store'] is False
    assert result['mode']=='live' and result['usage']['total_tokens']==100

def test_failed_llm_does_not_overwrite_previous_report(client,monkeypatch):
    from passage import codex_brain
    previous=run(client,'lecteur')['result']['id']
    monkeypatch.setattr(codex_brain,'configured',lambda: True)
    monkeypatch.setattr(integrations,'direct',lambda *a,**kw: ({'not':'a report'},{}))
    response=client.post('/api/runs',json={'role':'lecteur','thesis_id':THERMAL,'mode':'live'})
    job=wait(client,response.json())
    assert job['status']=='failed'
    assert len(store.all_of('report'))==1 and store.all_of('report')[0]['id']==previous

def test_invalid_citation_and_in_progress_claim_rejected(client):
    t=store.get('thesis',THERMAL);r=agents.demo_report('lecteur',[t]);r['evidence'][0]['quote']='Citation inventée.'
    with pytest.raises(integrations.IntegrationError):agents.validate_report(r,[t],'lecteur')
    t=store.get('thesis',PRINT);r=agents.demo_report('lecteur',[t]);r['demonstrated']=['Résultat inventé dans une thèse en cours.']
    with pytest.raises(integrations.IntegrationError):agents.validate_report(r,[t],'lecteur')
    r=agents.demo_report('rapprochement',[t],NEED);r['matches'][0]['demonstrated']=['Résultat inventé']
    with pytest.raises(integrations.IntegrationError):agents.validate_report(r,[t],'rapprochement')

def test_tools_cannot_read_private_outside_task(client):
    a=store.get('agent','rapprochement');t=store.get('thesis',THERMAL)
    specs,invoke=agents.tools_for(a,[t])
    assert invoke('read_thesis',{'thesis_id':PRINT})['error']
    with pytest.raises(integrations.IntegrationError):invoke('publish_thesis',{})

def test_dust_projection_sync_and_call_contract(client,monkeypatch):
    a=store.get('agent','incorporation');payload=integrations.dust_export(a,agents.assembled(a))
    assert payload['generation_settings']['model_id']==a['model']
    integrations.SESSION_SECRETS.update(DUST_API_KEY='test-dust',DUST_WORKSPACE_ID='ws')
    report=agents.demo_report('incorporation',[store.get('thesis',THERMAL)],NEED)
    observed=[]
    def fake(method,url,**kw):
        observed.append((url,kw['json']))
        if url.endswith('/import'):return {'agentConfiguration':{'sId':'dust-agent'}}
        return {'conversation':{'sId':'conversation','content':[[{'type':'agent_message','content':json.dumps(report)}]]}}
    monkeypatch.setattr(integrations,'http',fake)
    a['dust_id']=integrations.dust_publish(a,agents.assembled(a));a['dust_revision']=a['revision']
    result,usage=integrations.dust_run(a,{'problem':NEED})
    assert result==report and usage['conversation_id']=='conversation'
    assert observed[-1][1]['message']['mentions']==[{'configurationId':'dust-agent'}]
    a['revision']+=1
    with pytest.raises(integrations.IntegrationError):integrations.dust_run(a,{})

def test_pipelex_export_and_remote_contract(client,monkeypatch):
    a=store.get('agent','lecteur');method=tomllib.loads(agents.method(a))
    assert method['pipe']['analyze']['model']==a['model']
    assert '$request' in method['pipe']['analyze']['prompt']
    integrations.SESSION_SECRETS['PIPELEX_API_KEY']='test-pipelex'
    a['method_ref']='github.com/example/method@v1'
    captured=[]
    monkeypatch.setattr(integrations,'http',lambda *args,**kw: captured.append(kw['json']) or {'pipeline_run_id':'r1'})
    report=agents.demo_report('lecteur',[store.get('thesis',THERMAL)])
    response=Mock(status_code=200);response.json.return_value={'main_stuff':{'content':{'text':json.dumps(report)}}}
    monkeypatch.setattr(integrations.requests,'get',lambda *a,**kw:response)
    result,usage=integrations.pipelex_run(a,{'notices':[]})
    assert result==report and usage['pipeline_run_id']=='r1'
    assert captured[0]['method_ref']==a['method_ref'] and 'request' in captured[0]['inputs']

def test_mcp_tool_allowlist(client,monkeypatch):
    connector={'id':'mcp_abc123','name':'Test','url':'https://example.test/mcp','allowed_tools':['read'],'secret_env':'','enabled':True}
    store.put('connector',connector);a=store.get('agent','lecteur');a['connector_ids']=[connector['id']]
    def fake(c,tool=None,args=None):
        if tool:return {'result':'allowed'}
        return {'tools':[{'name':n,'inputSchema':{'type':'object','properties':{}}} for n in ['read','delete']]}
    monkeypatch.setattr(integrations,'mcp',fake)
    specs,invoke=agents.tools_for(a,[store.get('thesis',THERMAL)])
    assert any(x['name'].endswith('_read') for x in specs)
    assert not any(x['name'].endswith('_delete') for x in specs)

def test_secret_never_returned_and_settings_role(client):
    token='secret-test-value-123'
    assert client.post('/api/connections/settings',headers=COMPANY,json={'OPENAI_API_KEY':token}).status_code==403
    assert client.post('/api/connections/settings',headers=ADMIN,json={'OPENAI_API_KEY':token}).status_code==200
    assert token not in client.get('/api/connections',headers=ADMIN).text
    assert token not in client.get('/api/state').text
    assert token not in json.dumps(store.events())

def test_oscar_only_authorized_tools(client):
    with pytest.raises(integrations.IntegrationError):integrations.oscar('oscar_api',{})
    assert client.get('/api/state').json()['oscar_mode']=='demo'

def test_static_pages_and_csv(client):
    assert client.get('/').status_code==200
    assert client.get('/static/app.js').status_code==200
    assert client.get('/static/styles.css').status_code==200
    assert 'Identifiant' in client.get('/api/laboratory/export').text
    assert client.get('/api/laboratory/export',headers=COMPANY).status_code==403


def test_ollama_native_schema_candidates_and_model_provenance(client,monkeypatch):
    a=store.get('agent','lecteur');a.update(provider='ollama',model='gemma4:26b');store.put('agent',a)
    t=store.get('thesis',THERMAL);report=agents.demo_report('lecteur',[t]);captured=[]
    def fake(method,url,**kw):
        captured.append((url,kw['json']))
        return {'message':{'content':json.dumps(report)},'model':'gemma4:26b','done_reason':'stop','eval_count':500}
    monkeypatch.setattr(integrations,'http',fake)
    result=run(client,'lecteur',mode='live')['result']
    url,payload=captured[0]
    assert url.endswith('/api/chat') and payload['format']['additionalProperties'] is False
    context=json.loads(payload['messages'][1]['content'])
    assert context['citations_candidates'][0]['quote'] in t['abstract']
    assert result['actual_model']=='gemma4:26b' and result['usage']['output_tokens']==500


def test_incorporation_receives_previous_real_reading(client,monkeypatch):
    from passage import codex_brain
    monkeypatch.setattr(codex_brain,'configured',lambda: True)
    captured=[]
    def fake(a,prompt,context,*args):
        captured.append(context)
        return agents.demo_report(context['role'],[store.get('thesis',THERMAL)],NEED),{}
    monkeypatch.setattr(integrations,'direct',fake)
    reader=run(client,'lecteur',mode='live')['result']
    run(client,'incorporation',mode='live')
    assert captured[-1]['lecture_precedente'][0]['report_id']==reader['id']


def test_matching_contract_requires_every_source(client):
    notices=[store.get('thesis',i) for i in [THERMAL,SULFUR,PRINT]]
    contract=agents.task_schema('rapprochement',notices)
    assert contract['properties']['matches']['minItems']==3
    assert contract['properties']['matches']['maxItems']==3
    assert contract['$defs']['Match']['properties']['thesis_id']['enum']==[THERMAL,SULFUR,PRINT]
