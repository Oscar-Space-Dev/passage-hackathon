'use strict';
const G={open:false,state:null,busy:false,busyKind:'',timer:null,error:'',pendingText:''};
const guideRoot=()=>document.querySelector('#guide-root');
function guideReset(){clearTimeout(G.timer);G.open=false;G.state=null;G.busy=false;G.busyKind='';G.error='';G.pendingText='';if(guideRoot())guideRoot().innerHTML='';}
async function guideBoot(){
  if(!S.user)return guideReset();
  try{G.state=await api('/guide');G.error='';}catch(e){G.error=e.message;}
  guideRender();guidePoll();
}
function guideActionDetail(a){
  const items=[];
  if(a.project_id&&a.kind!=='create_project')items.push('Projet : '+a.project_id);
  if(a.name)items.push('Nom : '+a.name);
  if(a.objective)items.push('Objectif : '+a.objective);
  if(a.context)items.push('Contexte : '+a.context);
  if(a.agent_ids?.length)items.push('Agents : '+a.agent_ids.join(', '));
  if(a.source_ids?.length)items.push('Sources : '+a.source_ids.join(', '));
  if(a.type_id)items.push('Tâche : '+a.type_id);
  if(a.brief)items.push('Consigne : '+a.brief);
  if(a.task_id)items.push('Dossier : '+a.task_id);
  if(a.agent_id)items.push('Agent : '+a.agent_id);
  if(a.message)items.push('Mission : '+a.message);
  if(a.research_kind)items.push('Livrable : '+a.research_kind);
  if(a.note_title)items.push('Note : '+a.note_title);
  if(a.note_content)items.push('Contenu : '+a.note_content);
  if(a.thesis_id)items.push('Thèse : '+a.thesis_id);
  if(a.service)items.push('Service : '+a.service);
  if(a.tool)items.push('Outil : '+a.tool);
  if(a.arguments_json){
    if(a.kind==='create_agent'){
      try{const spec=JSON.parse(a.arguments_json);
        items.push('Mandat : '+spec.mandate);
        items.push('Cerveau : ChatGPT via Codex · '+(spec.model||'auto'));
        items.push('Tâches : '+(spec.work_specialties||[]).join(', '));
        items.push('Déclencheur : '+spec.trigger);
        items.push('Données lues : '+spec.reads);
        items.push('Validation humaine : '+spec.checkpoint);
        items.push('Livrable : '+spec.deliverables);
        items.push('Skill : '+spec.skill);
        items.push('Contexte : '+spec.context);
        if(spec.memory)items.push('Mémoire : '+spec.memory);
        if(spec.process)items.push('Processus : '+spec.process);
        if(spec.workflow)items.push('Workflow : '+spec.workflow);
      }catch{items.push('Définition : '+a.arguments_json);}
    }else items.push('Paramètres : '+a.arguments_json);
  }
  if(a.diagram_id)items.push('Schéma : '+a.diagram_id);
  if(a.diagram_title)items.push('Titre du schéma : '+a.diagram_title);
  if(a.target)items.push('Document : '+a.target);
  if(a.kind==='mcp_call')items.push('Une écriture externe demandera une validation supplémentaire.');
  return items.map(x=>`<div>${esc(x)}</div>`).join('');
}
function guideRender(){
  const root=guideRoot();if(!root||!S.user)return;
  if(S.liveVoice?.mode==='guide'){
    root.innerHTML='';
    return;
  }
  const state=G.state||{messages:[],plan:null};
  const p=state.plan;
  const messages=state.messages.map(m=>`<div class="guide-message ${m.role}"><strong>${m.role==='user'?'Vous':'Marguerite'}</strong><div>${esc(m.text)}</div>${m.questions?.length?`<ul>${m.questions.map(q=>`<li>${esc(q)}</li>`).join('')}</ul>`:''}${m.human_steps?.length?`<div class="guide-human"><strong>À faire ou à valider par vous</strong><ul>${m.human_steps.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>`:''}</div>`).join('')+(G.pendingText?`<div class="guide-message user"><strong>Vous · envoi en cours</strong><div>${esc(G.pendingText)}</div></div>`:'');
  const results=p?.results||[];
  const resultLinks=results.map(r=>{
    const x=r.result||{};
    if(x.agent_id)return `<button class="btn ghost small" type="button" data-guide="open-agent" data-agent="${esc(x.agent_id)}">Voir le harnais créé</button>`;
    if(x.diagram_id&&x.task_id)return `<button class="btn ghost small" type="button" data-guide="open-diagram" data-project="${esc(x.project_id)}" data-task="${esc(x.task_id)}" data-diagram="${esc(x.diagram_id)}">Ouvrir le dessin</button>`;
    if(x.task_id)return `<button class="btn ghost small" type="button" data-guide="open-task" data-project="${esc(x.project_id)}" data-task="${esc(x.task_id)}">Ouvrir la tâche</button>`;
    if(x.project_id)return `<button class="btn ghost small" type="button" data-guide="open-project" data-project="${esc(x.project_id)}">Ouvrir le projet</button>`;
    return '';
  }).filter((x,i,a)=>x&&a.indexOf(x)===i).join('');
  const plan=p?`<section class="guide-plan"><h3>Plan de Marguerite</h3><ol>${p.actions.map((a,i)=>{const r=results.find(x=>x.index===i);return `<li><strong>${esc(a.label)}</strong><div class="guide-action-detail">${guideActionDetail(a)}</div>${r?`<div class="guide-result ${r.status}">${r.status==='failed'?esc(r.error):r.status==='running'?`Exécution ${esc(r.run_status||'en cours')} · ${esc(r.result?.run_id||'')}`:`${r.status==='succeeded'?'Exécution terminée':'Action faite'} : ${esc(JSON.stringify(r.outcome||r.result))}`}</div>`:''}</li>`;}).join('')}</ol>${p.human_steps?.length?`<div class="guide-human"><strong>Votre intervention reste nécessaire</strong><ul>${p.human_steps.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>`:''}${p.status==='pending'?`<div class="guide-plan-buttons"><button class="btn" type="button" data-guide="approve" ${G.busy?'disabled':''}>${G.busyKind==='approve'?'Validation en cours…':'Valider et exécuter ces actions'}</button><button class="btn ghost" type="button" data-guide="reject" ${G.busy?'disabled':''}>Refuser</button></div>`:`<p class="guide-status">${esc({running:'Marguerite agit dans Passage…',awaiting_runs:'Agents au travail · résultats à suivre',needs_review:'Résultats prêts pour votre contrôle',completed:'Actions terminées',failed:'Arrêté après une erreur',rejected:'Plan refusé',superseded:'Plan remplacé'}[p.status]||p.status)}</p>`}${resultLinks}</section>`:'';
  const guideVoice=S.liveVoice?.mode==='guide';
  root.innerHTML=`<button type="button" class="guide-launch" data-guide="toggle" aria-label="Discuter avec Marguerite" aria-expanded="${G.open}">✦ <span>Marguerite</span></button>${G.open?`<aside class="guide-panel" aria-label="Discussion avec Marguerite"><header><div><strong>Marguerite</strong><small>Votre agent pour agir dans Passage.</small></div><div class="guide-header-actions"><button class="guide-voice" type="button" data-guide="voice" aria-pressed="${guideVoice}" ${G.busy?'disabled':''}>${guideVoice?'Couper le micro':'Conversation vocale'}</button><button class="guide-close" type="button" data-guide="toggle" aria-label="Fermer">×</button></div></header><div class="guide-scroll">${state.profile?`<details class="guide-profile"><summary>Ce que Marguerite retient de vous</summary><p>${esc(state.profile)}</p></details>`:''}<div class="guide-message assistant"><strong>Marguerite</strong><div>Expliquez-moi ce que vous faites et ce que vous voulez obtenir. Je vérifierai les travaux existants, puis vous proposerai les actions réalisables dans Passage.</div></div>${messages}${plan}${G.error?`<div class="notice error" role="alert">${esc(G.error)}</div>`:''}</div><form id="guide-form"><label class="sr-only" for="guide-input">Votre message à Marguerite</label><textarea id="guide-input" name="text" rows="2" maxlength="6000" placeholder="Que souhaitez-vous faire dans Passage ?" required ${G.busy?'disabled':''}></textarea><button class="btn" type="submit" ${G.busy?'disabled':''}>${G.busyKind==='message'?'Réflexion…':'Envoyer'}</button></form></aside>`:''}`;
  if(G.open){const scroll=root.querySelector('.guide-scroll');scroll.scrollTop=scroll.scrollHeight;}
}
async function guidePoll(){
  clearTimeout(G.timer);if(!S.user||!G.state?.plan||!['running','awaiting_runs'].includes(G.state.plan.status))return;
  G.timer=setTimeout(async()=>{try{const previous=G.state.plan.status;G.state=await api('/guide');G.error='';guideRender();guidePoll();if(previous!==G.state.plan?.status&&!['running','awaiting_runs'].includes(G.state.plan?.status)){S.projects=await api('/projects');await refresh();if(S.project)S.project=await api('/projects/'+S.project.id);shell();}}catch(e){G.error=e.message;guideRender();}},2000);
}
document.addEventListener('click',async e=>{
  const b=e.target.closest('[data-guide]');if(!b)return;
  e.preventDefault();e.stopPropagation();
  const command=b.dataset.guide;
  if(command==='toggle'){G.open=!G.open;guideRender();if(G.open)guideRoot().querySelector('#guide-input')?.focus();return;}
  if(command==='voice'){
    if(G.busy)return;
    try{
      const active=S.liveVoice?.mode==='guide';
      if(S.liveVoice)await stopLiveVoice();
      if(!active)await startLiveVoice('guide');
      G.error='';guideRender();
    }catch(err){G.error=err.message;guideRender();}
    return;
  }
  if(command==='open-project'){
    try{S.projects=await api('/projects');S.project=await api('/projects/'+b.dataset.project);rememberProject();S.view='chat';shell();G.open=false;guideRender();}catch(err){G.error=err.message;guideRender();}return;
  }
  if(command==='open-agent'){
    try{const detail=await api('/agents/'+b.dataset.agent);const a=detail.agent;
      modal('Harnais · '+a.name,`<p><strong>${esc(a.mandate)}</strong></p><p>Créé par Marguerite · ${esc(a.creator_version||'')}</p><details open><summary>Skill</summary><pre>${esc(a.skill)}</pre></details><details><summary>Contexte et contrôles</summary><pre>${esc([a.context,a.trigger,a.reads,a.boundaries,a.checkpoint,a.deliverables].filter(Boolean).join('\n\n'))}</pre></details><p>${detail.control.length?esc(detail.control.join(' · ')):'Définition complète. À éprouver sur un travail réel.'}</p><button class="btn ghost small" type="button" data-action="export-agent" data-id="${esc(a.id)}" data-target="pipelex">Exporter le brouillon .mthds</button>`);
    }catch(err){G.error=err.message;guideRender();}return;
  }
  if(command==='open-task'||command==='open-diagram'){
    try{
      S.projects=await api('/projects');S.project=await api('/projects/'+b.dataset.project);rememberProject();
      S.view='work';shell();G.open=false;guideRender();
      await workspaceClick(command==='open-diagram'?'work-diagram-open':'work-open',
        {dataset:{id:b.dataset.task,diagramId:b.dataset.diagram}});
    }catch(err){G.error=err.message;guideRender();}return;
  }
  const p=G.state?.plan;if(!p||G.busy)return;
  G.busy=true;G.busyKind=command;guideRender();
  try{const result=await post('/guide/plans/'+p.id+'/'+command);G.state.plan=result.plan;G.error='';guideRender();guidePoll();}
  catch(err){G.error=err.message;guideRender();}
  finally{G.busy=false;G.busyKind='';guideRender();}
});
document.addEventListener('submit',async e=>{
  if(e.target.id!=='guide-form')return;
  e.preventDefault();e.stopImmediatePropagation();
  if(G.busy)return;
  const textValue=e.target.elements.text.value.trim();if(!textValue)return;
  G.busy=true;G.busyKind='message';G.error='';G.pendingText=textValue;guideRender();
  try{await post('/guide/messages',{text:textValue,project_id:S.project?.id||'',view:S.view||''});G.state=await api('/guide');G.error='';}
  catch(err){G.error=err.message;try{G.state=await api('/guide');}catch{}}
  finally{G.busy=false;G.busyKind='';G.pendingText='';guideRender();}
},true);
