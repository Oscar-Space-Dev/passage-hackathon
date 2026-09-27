'use strict';
Object.assign(S,{view:'chat',user:null,csrf:'',projects:[],project:null,workInbox:[],workPersona:'all',recording:null,voiceReply:false,voiceSend:false,voiceConversation:false,voiceEpoch:0,liveVoice:null});
let missionTimer, oauthTimer, playingAudio, playingAudioUrl, playingResolve;
const personaLabels={R1:'Doctorant',R2:'Jeune docteur',R3:'Directeur de thèse'};
function selectedProjectKey(){return S.user?'passage-selected-project-'+S.user.id:'';}
function rememberProject(){if(S.user)sessionStorage.setItem(selectedProjectKey(),S.project?.id||'');}
function stopPlayingAudio(){
  if(playingAudio){playingAudio.pause();playingAudio.onended=null;playingAudio=null;}
  if(playingAudioUrl){URL.revokeObjectURL(playingAudioUrl);playingAudioUrl=null;}
  if(playingResolve){const resolve=playingResolve;playingResolve=null;resolve();}
}
async function boot(){
  try{
    const status=await api('/auth/status');
    S.googleEnabled=status.google_enabled;
    if(!status.user){
      loginScreen(status.setup_required);
      const googleError=new URLSearchParams(location.search).get('google');
      if(googleError){
        $('#auth-error').innerHTML=errorBox(googleError==='link'?'Ce compte Google correspond à un compte Passage existant. Connectez-vous avec votre mot de passe, puis associez Google dans Connexions.':'La connexion Google a été annulée ou n’a pas pu être vérifiée. Réessayez.');
        history.replaceState(null,'',location.pathname);
      }
      return;
    }
    S.user=status.user;S.csrf=status.csrf;S.role=S.user.role==='admin'?(S.user.account_type||'lab'):S.user.role;
    await refresh();S.projects=await api('/projects');S.workInbox=await api('/work/inbox');
    const remembered=sessionStorage.getItem(selectedProjectKey());
    const chosen=S.projects.find(p=>p.id===remembered)||S.projects[0];
    if(chosen)S.project=await api('/projects/'+chosen.id);
    shell();resumeMission();if(typeof guideBoot==='function')await guideBoot();await showTeamInvite();
    if(new URLSearchParams(location.search).has('google')){
      toast('La connexion Google n’a pas été associée à ce compte Passage.',true);
      history.replaceState(null,'',location.pathname);
    }
  }catch(e){$('#app').innerHTML=`<main class="content"><h1>Passage</h1>${errorBox(e.message)}</main>`;}
}
function loginScreen(register=false){
  if(typeof guideReset==='function')guideReset();
  $('#app').innerHTML=`<main class="auth-layout"><section class="auth-intro"><div class="brand">Passage ↗</div><h1>Un objectif.<br>Une équipe qui avance.</h1><p>Mobilisez vos agents autour d’un projet. Retrouvez leurs travaux, leurs sources et les décisions qui vous reviennent.</p></section><section class="auth-card"><div class="eyebrow">Votre espace de travail</div><h2>${register?'Créer votre compte':'Bienvenue'}</h2><p class="muted">${register?'Choisissez votre profil et créez votre espace personnel. Vous pourrez ensuite créer ou rejoindre une équipe.':'Connectez-vous pour retrouver vos projets et vos agents.'}</p><form id="login-form" data-register="${register}">${register?textField('name','Votre nom','','text',true)+`<div class="field"><label for="account_type">Votre profil</label><select id="account_type" name="account_type"><option value="lab">Laboratoire</option><option value="researcher">Doctorant ou chercheur indépendant</option><option value="company">Entreprise · recherche et développement</option></select></div>`:''}${textField('email','Email','','email',true)}<div class="field"><label for="password">Mot de passe</label><input id="password" name="password" type="password" required minlength="${register?12:1}" autocomplete="${register?'new-password':'current-password'}"></div><button class="btn" type="submit">${register?'Créer mon espace':'Me connecter'}</button><div id="auth-error"></div></form>${S.googleEnabled?`<button class="btn secondary" type="button" data-action="google-login">Continuer avec Google</button>`:`<p class="hint">Connexion Google disponible après configuration OAuth par l’administrateur.</p>`}<button class="btn ghost" data-action="auth-toggle" data-register="${!register}">${register?'J’ai déjà un compte':'Créer un compte'}</button><p class="hint">Compte personnel à cette installation de Passage. Vos projets et conversations restent privés.</p></section></main>`;
}
function homeVoiceBrain(){const base=S.data?.agents.find(a=>a.active&&a.engine==='direct');return base?{...base,provider:'codex',model:'auto'}:null;}
function projectBrain(){const agent=S.project?S.data?.agents.find(a=>a.id===S.project.coordinator_id):homeVoiceBrain();return agent&&S.project?.brain_provider==='codex'?{...agent,provider:'codex',model:S.project.brain_model}:agent;}
function conversationControls(){const brain=projectBrain();const source=brain?.provider==='codex'?'ChatGPT via Codex':brain?.provider==='ollama'?'Modèle local Ollama':'Sélectionnez un coordinateur compatible';return `<div class="voice-conversation"><button type="button" class="live-voice-launch" data-action="voice-conversation" id="voice-conversation-button" aria-label="Démarrer une conversation vocale continue avec Passage" aria-pressed="${Boolean(S.liveVoice)}">${icon('mic')}</button><div><strong>Conversation vocale · ${esc(source)}</strong><p class="hint">Voix Gradium · micro continu · transcription en direct · interrompez Passage en reprenant la parole.${S.project?'':' Dites « crée un projet [nom] » ou « ouvre le projet [nom] » pour conserver la suite.'}</p></div></div>`;}
function liveModeNotice(){
  const brain=projectBrain();
  const label=brain?`${esc(brain.name)} · ${esc(brain.model)}`:'le coordinateur du projet';
  const modelHint=brain?.provider==='ollama'?' Le modèle local peut prendre plusieurs minutes.':' Le délai dépend du modèle choisi.';
  return `<div class="notice info"><strong>Appels réels · agents actifs.</strong> ${label} répond avec son modèle et peut mobiliser l’équipe. Un appel externe Dust ou Pipelex demande votre confirmation dans le projet.${modelHint}${S.project?' Changez le modèle dans « Objectif & équipe ».':' Choisissez un modèle lors de la création du projet.'}</div>`;
}
function chatPage(){
  const p=S.project;
  const inboxRows=(S.workInbox||[]).map(w=>`<div class="team-row"><div><strong>${esc(w.title)}</strong><small>${esc(personaLabels[w.definition.persona]||w.definition.persona)} · ${esc(w.my_access==='reviewer'?'Relecture demandée':'Contribution demandée')} · ${esc(w.status)}</small>${button('Ouvrir','work-open','folder','ghost small',`data-id="${esc(w.id)}"`)}</div></div>`).join('');
  const inbox=inboxRows?`<section class="card"><h3>Travaux partagés avec moi</h3>${inboxRows}</section>`:'';
  const researchPrompts=[
    ['Rédiger','À partir des sources que je fournis, aide-moi à structurer une section de thèse. Sépare les affirmations sourcées, mes interprétations et les points à vérifier.'],
    ['Préparer une expérience','Aide-moi à concevoir une expérience pour tester mon hypothèse. Propose un protocole, les variables, les contrôles, les mesures et les limites, sans inventer de résultats.'],
    ['Simuler','Aide-moi à définir une simulation reproductible pour cette question. Explicite le modèle, les hypothèses, les paramètres, les entrées et les contrôles à effectuer.'],
    ['Démo calcul batterie','Exécute le modèle thermique simplifié de batterie avec des paramètres purement hypothétiques : courant 10 A, résistance 0,1 Ω, capacité thermique 100 J/K, refroidissement 0 W/K, température ambiante 20 °C, température initiale 20 °C, durée 10 s et pas 1 s. Donne le maximum calculé et les limites du modèle ; aucune mesure réelle.'],
    ['Créer un programme','Aide-moi à spécifier un petit outil informatique pour mon travail de recherche : entrées, sorties, méthode, tests et critères de validation.']
  ];
  const promptExamples=`<div class="research-prompts"><span class="hint">Exemples de demandes de recherche</span><div class="actions">${researchPrompts.map(([label,prompt])=>button(label,'research-prompt',null,'ghost small',`data-prompt="${esc(prompt)}"`)).join('')}</div></div>`;
  const teamRows=p?p.agent_ids.map(id=>{
    const a=S.data.agents.find(agent=>agent.id===id);
    return `<div class="team-row">${icon('spark')}<div><strong>${esc(a?.name||id)}</strong><small>${esc(id===p.coordinator_id&&p.brain_provider==='codex'?p.brain_model:a?.model||'')} ${id===p.coordinator_id?'· cerveau du coordinateur':''}</small></div></div>`;
  }).join(''):'';
  const researchRows=p?(p.research||[]).slice().reverse().map(r=>
    `<div class="team-row"><div><strong>${esc(r.title)}</strong><small>${esc(({redaction:'Rédaction',experience:'Expérience',simulation:'Simulation',logiciel:'Logiciel'})[r.kind])} · ${r.status==='computed'?'calcul exécuté · modèle simplifié':'proposition à vérifier'}</small>${button('Lire','research-read','book','ghost small',`data-id="${r.id}"`)}${button('Exporter','research-export','download','ghost small',`data-id="${r.id}"`)}</div></div>`
  ).join(''):'';
  const workRows=p?(p.work_items||[]).slice().reverse().map(w=>
    `<div class="team-row"><div><strong>${esc(w.title)}</strong><small>${esc(personaLabels[w.definition.persona]||w.definition.persona)} · ${esc(({todo:'À commencer',in_progress:'En cours',delegated:'Agent en cours',review:'À relire',done:'Validé'})[w.status]||w.status)} · ${verifiedStepCount(w)}/${w.definition.steps.length} étapes vérifiées</small>${button('Ouvrir le travail','work-open','folder','ghost small',`data-id="${esc(w.id)}"`)}</div></div>`
  ).join(''):'';
  const reportRows=p?p.reports.map(r=>
    `<div class="team-row"><div><strong>${esc(roleNames[r.role])}</strong><small>${esc(r.agent_name.includes('Gemma local')?'Dossier historique · agent retiré':r.agent_name)}</small>${button('Lire le dossier','project-report','book','ghost small',`data-id="${r.id}"`)}</div></div>`
  ).join(''):'';
  const selectedSources=p?(p.source_ids||[]).map(id=>S.data.theses.find(t=>t.id===id)).filter(Boolean):[];
  const projectBody=p?`<div class="project-layout">
    <section class="chat-card"><div class="chat-title"><div><h2>${esc(p.name)}</h2><p>${esc(p.objective)}</p></div>${badge('Coordination par modèle','gray')}</div>
      <div id="messages" class="messages" aria-live="polite">${messageHtml(p)}</div><div id="mission-status"></div>
      <form id="chat-form" class="chat-compose">${liveModeNotice()}<label class="sr-only" for="chat-input">Votre message à l’équipe</label><textarea id="chat-input" name="message" rows="3" required placeholder="Décris ta question, les sources ou données disponibles et le résultat attendu…"></textarea>${promptExamples}
        <div class="chat-controls"><label class="check"><input id="voice-reply" type="checkbox" ${S.voiceReply?'checked':''}>Lire les réponses avec Gradium</label><div class="actions">${button('Parler','voice','mic','secondary','id="voice-button"')}<button type="submit" class="btn">Envoyer ${icon('arrow')}</button></div></div>
        ${conversationControls()}<label class="check tiny"><input id="voice-send" type="checkbox" ${S.voiceSend?'checked':''}>Envoyer la commande vocale dès sa transcription</label><p id="voice-status" class="hint">Micro fermé. Appuyez sur Parler, puis terminez l’enregistrement pour relire la transcription.</p>
        <p class="hint">Commandes possibles : « statut de la mission », « mes validations en attente », « ouvre le projet [nom] », « crée un projet [nom] », « arrête la mission », « liste les modèles ChatGPT », « utilise le modèle ChatGPT [nom] », « reviens au modèle de l’agent », « Demande à Dust de [travail] », « Demande à l’agent Dust [nom] de [travail] », « Réponse Dust », « Retrouve la conversation Dust », « Demande à Pipelex de [travail] » et « Statut Pipelex ». « Liste les agents Dust », « liste les méthodes Pipelex » et « montre la méthode Pipelex [nom] » consultent les catalogues. Chaque lancement externe demande validation.</p>
      </form></section>
    <aside class="project-side"><section class="card"><h3>Sources du projet</h3><p class="tiny muted">${selectedSources.length?selectedSources.map(t=>esc(t.title)).join('<br>'):'Aucune notice sélectionnée. Les brouillons ne pourront pas citer une source vérifiée.'}</p>${button('Choisir les sources','project-sources','book','secondary small')}</section><section class="card"><h3>Agents mobilisables</h3>${teamRows}${button('Composer l’équipe','project-team','user','secondary small')}</section>
      <section class="card"><div class="sectionhead"><h3>Travaux du projet</h3>${button('Nouvelle tâche','work-new','plus','secondary small')}</div><p class="hint">Chaque tâche suit ses étapes. Vous pouvez produire le livrable ou demander un brouillon à un agent de l’équipe, puis le valider.</p>${workRows||'<p class="muted tiny">Aucune tâche ouverte.</p>'}</section>
      <section class="card"><h3>Livrables de recherche</h3>${researchRows||'<p class="muted tiny">Demandez une rédaction, un protocole, une simulation ou un logiciel dans le dialogue.</p>'}</section>
      <section class="card"><h3>Dossiers de valorisation</h3>${reportRows||'<p class="muted tiny">Aucun dossier pour le moment.</p>'}</section>
      <section id="approvals">${approvalHtml(p)}</section></aside>
  </div>`:'';
  return heading('Équipe agentique','De l’objectif aux premiers résultats.','Confiez une mission. Le coordinateur choisit les spécialistes et réévalue la suite après chaque résultat.',button('Nouveau projet','new-project','plus','secondary'))+inbox+
  `<div class="project-toolbar"><label for="project-select">Projet</label><select id="project-select"><option value="">Choisir un projet</option>${S.projects.map(x=>`<option value="${esc(x.id)}" ${p?.id===x.id?'selected':''}>${esc(x.name)}${x.pending_approvals?' · '+x.pending_approvals+' validation(s) en attente':''}</option>`).join('')}</select>${p?button('Objectif & équipe','project-info','settings','ghost small'):''}</div>`+
  (p?projectBody:
  `<section class="card"><div class="eyebrow">Un espace de travail pour la recherche</div><h2>Sur quoi veux-tu avancer ?</h2><p>Structure une partie de thèse, prépare une expérience, définis une simulation ou spécifie un programme dédié. Décris ton objectif ; le coordinateur mobilisera l’équipe disponible.</p>${promptExamples}<form id="chat-form" class="chat-compose">${liveModeNotice()}<label for="chat-input">Ton objectif de recherche ou ta commande</label><textarea id="chat-input" name="message" rows="4" required minlength="10" placeholder="Présente ta question, les sources ou données disponibles et le résultat attendu…"></textarea><div class="chat-controls"><label class="check"><input id="voice-reply" type="checkbox" ${S.voiceReply?'checked':''}>Lire les réponses avec Gradium</label><div class="actions">${button('Parler','voice','mic','secondary','id="voice-button"')}<button type="submit" class="btn">Envoyer à Passage</button></div></div>${conversationControls()}<label class="check tiny"><input id="voice-send" type="checkbox" ${S.voiceSend?'checked':''}>Envoyer la commande vocale dès sa transcription</label><p id="voice-status" class="hint">Le micro est fermé. La transcription restera modifiable.</p><p class="hint">Vous pouvez dire « mes validations en attente », « crée un projet [nom] », « ouvre le projet [nom] », « liste les agents Dust », « liste les méthodes Pipelex » ou « montre la méthode Pipelex [nom] » sans choisir de projet au préalable.</p><p id="dialogue-notice" class="notice info" role="status" hidden></p></form><p class="hint">Les résultats dépendent des agents et outils connectés. Une expérience réelle ou une simulation exécutable nécessite les équipements ou logiciels correspondants.</p></section>`);
}
function workPage(){
  const p=S.project,all=p?.work_items||[],filtered=S.workPersona==='all'?all:all.filter(w=>w.definition.persona===S.workPersona);
  const filters=['all','R1','R2','R3'].map(persona=>button(persona==='all'?'Tous les rôles':personaLabels[persona],'work-filter',null,S.workPersona===persona?'secondary small':'ghost small',`data-persona="${persona}"`)).join('');
  const groups=[['todo','À commencer'],['in_progress','En cours'],['delegated','Agents en cours'],['review','À relire'],['done','Validés']];
  const columns=groups.map(([key,label])=>`<section class="card"><div class="sectionhead"><h3>${label}</h3>${badge(filtered.filter(w=>w.status===key).length,'gray')}</div>${filtered.filter(w=>w.status===key).map(w=>`<div class="team-row"><div><strong>${esc(w.title)}</strong><small>${esc(personaLabels[w.definition.persona]||w.definition.persona)} · ${verifiedStepCount(w)}/${w.definition.steps.length} étapes vérifiées · ${w.due_at?esc(w.due_at):'sans échéance'}</small><p class="tiny muted">${esc(w.brief.slice(0,180))}</p>${button('Ouvrir','work-open','arrow','ghost small',`data-id="${esc(w.id)}"`)}</div></div>`).join('')||'<p class="hint">Aucun travail à ce stade.</p>'}</section>`).join('');
  const inbox=(S.workInbox||[]).map(w=>`<div class="team-row"><div><strong>${esc(w.title)}</strong><small>${esc(personaLabels[w.definition.persona]||w.definition.persona)} · ${esc(w.my_access==='reviewer'?'Avis demandé':'Contribution demandée')}</small>${button('Ouvrir','work-open','arrow','ghost small',`data-id="${esc(w.id)}"`)}</div></div>`).join('');
  return heading('Travaux de recherche','Faire avancer chaque travail.','Un parcours par tâche, avec vos preuves, un livrable humain ou une proposition d’agent et une décision traçable.',p?button('Nouvelle tâche','work-new','plus','secondary'):button('Créer un projet','new-project','plus','secondary'))+
    `<div class="project-toolbar"><label for="work-project-select">Projet</label><select id="work-project-select"><option value="">Choisir un projet</option>${S.projects.map(x=>`<option value="${esc(x.id)}" ${p?.id===x.id?'selected':''}>${esc(x.name)}</option>`).join('')}</select></div>`+
    `<section class="card"><h3>Travaux partagés avec moi</h3>${inbox||'<p class="hint">Aucune relecture ou contribution demandée.</p>'}</section>`+
    (p?`<div class="actions">${filters}</div><div class="grid equal">${columns}</div>`:'<section class="card"><p>Choisissez ou créez un projet pour ouvrir vos tâches R1–R3. Les tâches partagées avec vous sont accessibles ci-dessus.</p></section>');
}
function workEntryProposals(entry,w,canEdit){
  const focus=Number.isInteger(entry.focus_step)&&entry.focus_step>=0?`<p class="hint">Étape ciblée : ${entry.focus_step+1}. ${esc(w.definition.steps[entry.focus_step])}</p>`:'';
  const revision=entry.revises_entry_id?`<h4>Révision du brouillon ${esc(entry.revises_entry_id)}</h4><p class="tiny textwrap">Demande : ${esc(entry.instruction||'')}</p><p class="tiny textwrap">Changements annoncés : ${esc(entry.revision_summary||'Non détaillés par l’agent.')}</p><details><summary>Voir les différences de texte calculées</summary><pre class="textwrap">${esc(entry.revision_diff||'Aucune différence de texte.')}</pre></details>`:'';
  const proposals=entry.worksheet_proposals||{};
  const rows=(w.definition.worksheet_questions||[]).filter(q=>proposals[q.code]).map(q=>`<p class="tiny textwrap"><strong>${esc(q.title)}</strong><br>${esc(proposals[q.code])}</p>`).join('');
  const suggested=(entry.record_suggestions||[]).map((item,index)=>`<div class="team-row"><div><strong>Ligne proposée ${index+1}</strong>${(w.definition.register?.columns||[]).map(column=>`<p class="tiny textwrap">${esc(column.title)} : ${esc(item[column.code]||'À préciser')}</p>`).join('')}${canEdit?button('Reprendre cette ligne','work-record-from-agent','edit','secondary small',`data-id="${esc(w.id)}" data-entry-id="${esc(entry.id)}" data-index="${index}"`):''}</div></div>`).join('');
  const citations=(entry.citation_suggestions||[]).map((item,index)=>`<div class="team-row"><div><strong>Passage proposé ${index+1}</strong><small>${esc(item.source_type)} · ${esc(item.source_id)}</small><p class="tiny textwrap">« ${esc(item.quote)} »</p><p class="tiny textwrap">Affirmation : ${esc(item.claim)}</p>${canEdit?button('Vérifier et reprendre ce passage','work-anchor-from-agent','edit','secondary small',`data-id="${esc(w.id)}" data-entry-id="${esc(entry.id)}" data-index="${index}"`):''}</div></div>`).join('');
  return focus+revision+(rows?`<h4>Réponses proposées par l’agent</h4>${rows}${canEdit?button('Reprendre dans les questions','work-worksheet-from-agent','edit','secondary small',`data-id="${esc(w.id)}" data-entry-id="${esc(entry.id)}"`):''}`:'')+(suggested?`<h4>Lignes proposées pour le registre</h4>${suggested}`:'')+(citations?`<h4>Passages à vérifier</h4>${citations}`:'');
}
function verifiedStepCount(w){return (w.step_checks||[]).filter(item=>item.current).length;}
function stepProofOptions(w,selected=''){
  const options=[['','Aucune pièce liée']];
  (w.entries||[]).filter(e=>!['decision','review'].includes(e.kind)).forEach(e=>options.push([`entry:${e.id}`,`Pièce · ${e.title}`]));
  (w.files||[]).forEach(f=>options.push([`file:${f.id}`,`Fichier · ${f.name}`]));
  (w.documents||[]).forEach(d=>options.push([`document:${d.id}`,`Document · ${d.title} · v${d.version}`]));
  (w.anchors||[]).filter(a=>a.current).forEach(a=>options.push([`anchor:${a.id}`,`Passage sourcé · ${a.claim.slice(0,70)}`]));
  return options.map(([value,label])=>`<option value="${esc(value)}" ${value===selected?'selected':''}>${esc(label)}</option>`).join('');
}
function workModal(w){
  const d=w.definition;
  const canEdit=['owner','editor'].includes(w.my_access),owner=w.my_access==='owner';
  const pendingAgentGates=(w.checkpoints||[]).filter(checkpoint=>checkpoint.before==='agent'&&!checkpoint.valid);
  const toolActions={questions:['work-worksheet','Renseigner les questions'],register:['work-record-new','Ajouter une ligne'],document:['work-document-new','Créer un document'],file:['work-file-add','Joindre un fichier'],diagram:['work-diagram-new','Dessiner le processus'],anchor:['work-anchor-new','Ancrer un passage'],evidence:['work-add','Ajouter une preuve'],share:['work-share','Inviter un relecteur']};
  const stepRows=d.playbook.map((play,index)=>{
    const tool=toolActions[play.tool],canUse=canEdit&&(play.tool!=='share'||owner);
    const attrs=`data-id="${esc(w.id)}"`+(play.tool==='evidence'?' data-kind="evidence"':'');
    const check=(w.step_checks||[])[index]||{},record=check.record||{};
    const status=check.current?'Étape vérifiée':check.checked?'Vérification à renouveler':'À faire ou vérifier';
    const history=(w.step_check_history||[]).filter(item=>item.index===index).slice().reverse();
    return `<div class="team-row"><div><strong>${index+1}. ${esc(play.human_action)}</strong><small>${status}${play.external?' · action hors de Passage réservée à la personne responsable':''}</small><p class="tiny textwrap"><strong>Agent :</strong> ${esc(play.agent_help)}</p><p class="tiny textwrap"><strong>À vérifier :</strong> ${esc(play.evidence)}</p>${record.note?`<p class="tiny textwrap"><strong>Contrôle humain :</strong> ${esc(record.note)} · ${fmt(record.created_at)}${record.proof_id?' · pièce '+esc(record.proof_id):''}</p>`:''}${history.length?`<details><summary>Historique des contrôles (${history.length})</summary>${history.map(item=>`<p class="tiny textwrap">${fmt(item.created_at)} · ${esc(item.actor_id)} · ${item.done?'vérifié':'rouvert'} : ${esc(item.note)}</p>`).join('')}</details>`:''}<div class="actions">${canUse?button(tool[1],tool[0],'edit','ghost small',attrs):''}${owner&&w.status!=='delegated'&&w.status!=='done'?button(play.external?'Préparer avec un agent':'Confier cette étape','work-delegate','spark','secondary small',`data-id="${esc(w.id)}" data-step-index="${index}" ${pendingAgentGates.length?'disabled':''}`):''}</div></div>${canEdit?button(check.current?'Rouvrir':'Vérifier cette étape','work-step',check.current?'edit':'check','ghost small',`data-id="${esc(w.id)}" data-index="${index}" data-done="${!check.current}"`):''}</div>`;
  }).join('');
  const worksheetRows=(d.worksheet_questions||[]).map(q=>`<div class="team-row"><div><strong>${esc(q.title)}</strong><p class="tiny textwrap">${esc(w.worksheet?.[q.code]||'À renseigner ou à faire proposer par un agent.')}</p></div></div>`).join('');
  const worksheetHistory=(w.worksheet_history||[]).slice().reverse().map(v=>`<details><summary>Révision ${v.revision} · ${fmt(v.created_at)} · ${esc(v.actor_id)}${v.source_entry_id?' · proposition d’agent reprise':''}</summary>${(d.worksheet_questions||[]).map(q=>`<p class="tiny"><strong>${esc(q.title)}</strong><br>${esc(v.answers?.[q.code]||'Non renseigné.')}</p>`).join('')}</details>`).join('');
  const worksheetSection=`<h3>Questions propres à ce travail</h3><p class="hint">Ces réponses cadrent le dossier et sont transmises à l’agent choisi. Vous pouvez les compléter au fil du travail.</p>${worksheetRows}${canEdit?button('Renseigner les questions','work-worksheet','edit','secondary small',`data-id="${esc(w.id)}"`):''}${worksheetHistory?`<details><summary>Historique des réponses</summary>${worksheetHistory}</details>`:''}`;
  const registerRows=(w.records||[]).map(record=>`<details><summary>${esc(record.values.c1)} · version ${record.version}${record.active?'':' · archivée'}</summary>${d.register.columns.map(column=>`<p class="tiny textwrap"><strong>${esc(column.title)}</strong><br>${esc(record.values[column.code]||'Non renseigné.')}</p>`).join('')}${record.evidence_entry_id||record.file_id?`<p class="hint">Pièce liée : ${esc(record.evidence_entry_id||record.file_id)}</p>`:''}${record.source_entry_id?`<p class="hint">Repris de la proposition ${esc(record.source_entry_id)} · ligne ${record.suggestion_index+1}</p>`:''}<p class="hint">${esc(record.updated_by)} · ${fmt(record.updated_at)}</p>${canEdit?`<div class="actions">${button('Modifier','work-record-edit','edit','secondary small',`data-id="${esc(w.id)}" data-record-id="${esc(record.id)}"`)}${button(record.active?'Archiver':'Rétablir',record.active?'work-record-archive':'work-record-restore','check','ghost small',`data-id="${esc(w.id)}" data-record-id="${esc(record.id)}"`)}</div>`:''}<details><summary>Historique</summary>${(record.history||[]).map(version=>`<div class="team-row"><div><strong>Version ${version.version} · ${fmt(version.updated_at)}</strong>${d.register.columns.map(column=>`<p class="tiny textwrap">${esc(column.title)} : ${esc(version.values[column.code]||'Non renseigné.')}</p>`).join('')}</div></div>`).join('')}</details></details>`).join('');
  const registerSection=`<h3>${esc(d.register.title)}</h3><p class="hint">Consignez une ligne par élément. Les versions restent dans le dossier ; l’agent lit les lignes actives et peut en proposer de nouvelles.</p>${registerRows||'<p class="hint">Aucune ligne.</p>'}${canEdit?button('Ajouter une ligne','work-record-new','plus','secondary small',`data-id="${esc(w.id)}"`):''}`;
  const anchorRows=(w.anchors||[]).map(item=>`<details><summary>${esc(item.claim.slice(0,120))} · ${item.active?'actif':'archivé'} · ${item.current?'source actuelle':'source périmée'}</summary><p class="tiny textwrap">« ${esc(item.quote)} »</p><p class="hint">${esc(item.source_title)} · version ${item.source_version} · SHA-256 ${esc(item.source_sha256.slice(0,16))}…${item.source_truncated?' · texte extrait partiel':''}</p>${item.source_entry_id?`<p class="hint">Repris de la proposition ${esc(item.source_entry_id)}</p>`:''}${canEdit?button(item.active?'Archiver':'Rétablir',item.active?'work-anchor-archive':'work-anchor-restore','check','ghost small',`data-id="${esc(w.id)}" data-anchor-id="${esc(item.id)}"`):''}</details>`).join('');
  const anchorSection=`<h3>Passages sourcés</h3><p class="hint">Associez une affirmation à un passage présent dans un fichier textuel ou un document de cette tâche. Une nouvelle version du document périme l’ancrage ; archivez-le ou vérifiez à nouveau la version courante.</p>${anchorRows||'<p class="hint">Aucun passage ancré.</p>'}${canEdit?button('Ancrer un passage','work-anchor-new','plus','secondary small',`data-id="${esc(w.id)}"`):''}`;
  const linkRows=(w.linked_sources_status||[]).map(source=>`<div class="team-row"><div><strong>${esc(source.title)}</strong><small>${source.current?source.agent_ready?'Livrable lié actuel':'Livrable actuel · autorisation d’usage par agent à vérifier dans la source':'Livrable périmé · actualisation nécessaire'}</small>${source.accessible?button('Ouvrir la source','work-open','arrow','ghost small',`data-id="${esc(source.task_id)}"`):''}</div></div>`).join('');
  const linkedSection=`<h3>Résultats validés d’autres tâches</h3><p class="hint">Reliez des livrables acceptés du même projet. L’agent de cette tâche recevra un extrait borné des sources autorisées ; une modification de la source demandera une nouvelle vérification.</p>${linkRows||'<p class="hint">Aucun livrable lié.</p>'}${owner?button('Gérer les liens','work-linked-sources','edit','secondary small',`data-id="${esc(w.id)}"`):''}`;
  const items=w.entries.map(e=>`<details><summary>${esc(e.title)} · ${esc(({note:'Note',evidence:'Preuve',deliverable:'Livrable',agent_draft:'Proposition d’agent',decision:'Décision'})[e.kind]||e.kind)} · ${fmt(e.created_at)}</summary><pre class="textwrap">${esc(e.content)}</pre>${e.url?`<p class="hint">Référence : ${esc(e.url)}</p>`:''}${e.derived_from?`<p class="hint">Reprise de la pièce ${esc(e.derived_from)}</p>`:''}${e.document_id?`<p class="hint">Document ${esc(e.document_id)} · version ${e.document_version} déposée</p>`:''}${e.origin==='agent'?`<p class="hint">Agent ${esc(e.actor_id)} · modèle ${esc(e.model||'')} · sources déclarées : ${esc((e.source_ids||[]).join(', ')||'aucune')}</p><p class="hint">Vérifications : ${esc((e.checks||[]).join(' · ')||'aucune')}</p><p class="hint">Limites : ${esc((e.limitations||[]).join(' · ')||'aucune')}</p>${workEntryProposals(e,w,canEdit)}${canEdit?button('Reprendre dans un document','work-document-from-entry','edit','secondary small',`data-id="${esc(w.id)}" data-entry-id="${esc(e.id)}"`):''}`:''}</details>`).join('');
  const status=({todo:'À commencer',in_progress:'En cours',delegated:'Agent en cours',review:'À relire',done:'Validé'})[w.status]||w.status;
  const shares=owner?`<h3>Collaboration</h3><p class="hint">Invitez un autre compte local sur cette tâche. Le relecteur voit le dossier, ajoute ses remarques et donne son avis ; l’éditeur peut aussi travailler sur les étapes.</p>${(w.shares||[]).map(s=>`<p class="tiny">${esc(s.name)} · ${esc(s.email)} · ${esc(s.role)}</p>`).join('')}${button('Partager la tâche','work-share','user','secondary small',`data-id="${esc(w.id)}"`)}`:'';
  const notes=`<div class="actions">${button('Ajouter une note','work-add',null,'secondary small',`data-id="${esc(w.id)}" data-kind="note"`)}${button('Ajouter une preuve','work-add',null,'secondary small',`data-id="${esc(w.id)}" data-kind="evidence"`)}${canEdit?button('Déposer un livrable','work-add',null,'secondary small',`data-id="${esc(w.id)}" data-kind="deliverable"`):''}</div>`;
  const fileRows=(w.files||[]).map(file=>`<div class="team-row"><div><strong>${esc(file.name)}</strong><small>${Math.ceil(file.size/1024)} Ko · SHA-256 ${esc(file.sha256.slice(0,12))}… · ${file.readable_by_agent?file.extracted_chars+' caractères extraits pour l’agent':'fichier conservé, contenu non lu par l’agent'}${file.extraction_truncated?' · extraction partielle':''}${file.extraction_error?' · '+esc(file.extraction_error):''}</small><div class="actions">${button('Télécharger','work-file-download','download','ghost small',`data-id="${esc(w.id)}" data-file-id="${esc(file.id)}" data-name="${esc(file.name)}"`)}${canEdit&&file.readable_by_agent&&!file.extraction_truncated&&file.extracted_chars<=200000?button('Ouvrir le texte dans un document','work-document-from-file','edit','ghost small',`data-id="${esc(w.id)}" data-file-id="${esc(file.id)}"`):''}${canEdit&&/\.(csv|tsv|py|json)$/i.test(file.name)?button('Contrôler','work-file-analyze','search','ghost small',`data-id="${esc(w.id)}" data-file-id="${esc(file.id)}"`):''}${canEdit&&!file.extraction_truncated&&/\.(csv|tsv)$/i.test(file.name)?button('Analyse descriptive','work-file-describe','search','secondary small',`data-id="${esc(w.id)}" data-file-id="${esc(file.id)}"`):''}</div></div></div>`).join('');
  const fileSection=`<h3>Fichiers et provenance</h3>${fileRows||'<p class="hint">Aucun fichier joint.</p>'}<p class="hint">Jusqu’à 8 Mo par fichier. Les agents reçoivent des extraits des fichiers texte, CSV, code, PDF et DOCX lorsque leur texte est extractible. Un scan, une image ou un XLSX reste une pièce à vérifier manuellement.</p>${button('Joindre un fichier','work-file-add','plus','secondary small',`data-id="${esc(w.id)}"`)}`;
  const documentRows=(w.documents||[]).map(doc=>`<div class="team-row"><div><strong>${esc(doc.title)}</strong><small>Version ${doc.version} · ${esc(doc.format)} · ${fmt(doc.updated_at)}${doc.source_entry_id?' · repris d’un brouillon ou d’une pièce':''}${doc.source_file_id?' · importé d’un fichier':''}</small>${button('Ouvrir le document','work-document-open','edit','ghost small',`data-id="${esc(w.id)}" data-document-id="${esc(doc.id)}"`)}</div></div>`).join('');
  const documentSection=`<h3>Documents de travail</h3><p class="hint">Rédigez ici une section, un protocole, un rapport ou du code. Chaque sauvegarde crée une version ; les agents peuvent lire des extraits de la version actuelle. Le livrable doit être déposé explicitement.</p>${documentRows||'<p class="hint">Aucun document de travail.</p>'}${canEdit?button('Créer un document','work-document-new','plus','secondary small',`data-id="${esc(w.id)}"`)+button('Créer une trame métier','work-document-new','edit','ghost small',`data-id="${esc(w.id)}" data-template="true"`):''}`;
  const checkpointRows=(w.checkpoints||[]).map(checkpoint=>`<div class="team-row"><div><strong>${esc(checkpoint.title)}</strong><small>${checkpoint.before==='agent'?'À attester avant délégation à un agent':'À attester avant clôture'} · ${checkpoint.valid?'Attesté par le propriétaire le '+fmt(checkpoint.record.created_at):checkpoint.record?'À renouveler après modification du dossier':'En attente'}</small><p class="hint">${esc(checkpoint.guidance)}</p>${checkpoint.valid?`<p class="tiny textwrap">${esc(checkpoint.record.statement)} · pièce ${esc(checkpoint.record.evidence_entry_id||checkpoint.record.file_id)}</p>`:''}${owner?button(checkpoint.valid?'Renouveler l’attestation':'Attester avec une preuve','work-checkpoint','check','secondary small',`data-id="${esc(w.id)}" data-code="${esc(checkpoint.code)}"`):''}</div></div>`).join('');
  const checkpointSection=checkpointRows?`<h3>Points de contrôle propres à cette tâche</h3><p class="hint">Le propriétaire relie une pièce et atteste ce qui a été fait. Passage conserve cette déclaration et son auteur ; il ne vérifie pas l’action externe. Une modification du dossier rend l’attestation à renouveler.</p>${checkpointRows}`:'';
  const latestDraft=[...(w.entries||[])].reverse().find(item=>item.kind==='agent_draft');
  const diagramRows=(w.diagrams||[]).map(diagram=>`<div class="team-row"><div><strong>${esc(diagram.title)}</strong><small>Version ${diagram.version} · ${fmt(diagram.updated_at)} · SHA-256 ${esc(diagram.sha256.slice(0,12))}…</small><div class="actions">${button('Ouvrir le dessin','work-diagram-open','edit','ghost small',`data-id="${esc(w.id)}" data-diagram-id="${esc(diagram.id)}"`)}${button('Exporter .excalidraw','work-diagram-export','download','ghost small',`data-id="${esc(w.id)}" data-diagram-id="${esc(diagram.id)}"`)}${owner?button('Formaliser avec un agent','work-diagram-formalize','spark','secondary small',`data-id="${esc(w.id)}" data-diagram-id="${esc(diagram.id)}" ${pendingAgentGates.length?'disabled':''}`):''}</div></div></div>`).join('');
  const diagramSection=`<h3>Schémas de protocoles et de processus</h3><p class="hint">Dessinez vos étapes, décisions et transitions. Passage conserve les versions. Un agent peut en faire un protocole ou une méthode Pipelex brouillon que vous relirez.</p>${diagramRows||'<p class="hint">Aucun schéma pour cette tâche.</p>'}${canEdit?button('Créer un schéma','work-diagram-new','plus','secondary small',`data-id="${esc(w.id)}"`):''}`;
  const agent=owner?`<h3>Confier à l’équipe</h3><p class="hint">${esc(d.agent_work)} La proposition restera à relire : ${esc(d.human_gate)}</p>${pendingAgentGates.length?`<p class="notice info">Attestez d’abord : ${esc(pendingAgentGates.map(item=>item.title).join(' · '))}.</p>`:''}${w.status==='delegated'?'<p class="notice info">L’agent travaille. Actualisez après son exécution.</p>':w.status==='done'?'<p class="hint">La tâche est validée. Demandez une révision humaine pour la rouvrir avant de relancer un agent.</p>':button('Demander un brouillon à un agent','work-delegate','spark','secondary',`data-id="${esc(w.id)}" ${pendingAgentGates.length?'disabled':''}`)+(latestDraft?button('Demander une correction du dernier brouillon','work-rework','edit','secondary',`data-id="${esc(w.id)}" data-entry-id="${esc(latestDraft.id)}" ${pendingAgentGates.length?'disabled':''}`):'')}`:'';
  const decision=owner?`<h3>Décision humaine</h3><p class="hint">Une validation exige les trois questions renseignées, toutes les étapes cochées et un livrable.${d.requires_peer_review?' Cette tâche exige aussi l’accord d’un relecteur invité sur la version actuelle.':''} Elle ne certifie pas automatiquement les actions externes.</p>${button('Valider ou demander une révision','work-review','check','secondary',`data-id="${esc(w.id)}"`)}`:`<h3>Votre relecture</h3><p class="hint">Votre avis porte sur la version ${w.revision}. Une modification ultérieure demandera un nouvel accord.</p>${button('Approuver ou demander une révision','work-peer-review','check','secondary',`data-id="${esc(w.id)}"`)}`;
  modal(w.title,`<div class="pills">${badge(personaLabels[d.persona]||d.persona,'gray')}${badge(status,w.status==='done'?'dark':'amber')}</div><p class="textwrap">${esc(w.brief)}</p><p class="hint">Entrées attendues : ${esc(d.inputs)}<br>Livrable : ${esc(d.output)}<br>Validation : ${esc(d.human_gate)}</p>${w.last_error?errorBox(w.last_error):''}<div class="actions">${canEdit?button('Modifier le cadrage','work-edit','edit','secondary small',`data-id="${esc(w.id)}"`):''}${button('Exporter le dossier','work-export','download','ghost small',`data-id="${esc(w.id)}"`)}${button('Actualiser','work-open','search','ghost small',`data-id="${esc(w.id)}"`)}</div><h3>Parcours de travail</h3>${stepRows}${worksheetSection}${registerSection}${anchorSection}${linkedSection}<h3>Notes, preuves et livrables</h3>${items||'<p class="hint">Rien de consigné pour le moment.</p>'}${notes}${documentSection}${diagramSection}${fileSection}${checkpointSection}${shares}${agent}${decision}`,'','large');
}
function workDocumentModal(w,doc){
  const canEdit=['owner','editor'].includes(w.my_access);
  const versions=(doc.versions||[]).slice().reverse().map(v=>`<div class="team-row"><div><strong>Version ${v.version}</strong><small>${fmt(v.created_at)} · ${esc(v.sha256.slice(0,12))}…</small>${button('Lire','work-document-version','book','ghost small',`data-id="${esc(w.id)}" data-document-id="${esc(doc.id)}" data-version="${v.version}"`)}</div></div>`).join('');
  const comments=(doc.comments||[]).slice().reverse().map(c=>`<div class="team-row"><div><strong>Version ${c.version} · ${fmt(c.created_at)}</strong>${c.quote?`<p class="hint textwrap">Passage cité : ${esc(c.quote)}</p>`:''}<p class="textwrap">${esc(c.content)}</p></div></div>`).join('');
  const editor=canEdit?`<form id="work-document-save-form" data-id="${esc(w.id)}" data-document-id="${esc(doc.id)}">${textField('title','Titre',doc.title,'text',true)}<label for="work-document-format">Format du texte</label><select id="work-document-format" name="format">${[['markdown','Markdown'],['latex','LaTeX'],['python','Python'],['r','R'],['plain','Texte brut'],['csv','CSV'],['mthds','Pipelex .mthds']].map(([id,label])=>`<option value="${id}" ${doc.format===id?'selected':''}>${label}</option>`).join('')}</select><label for="work-document-content">Texte</label><textarea id="work-document-content" name="content" rows="18" maxlength="200000">${esc(doc.content)}</textarea><input type="hidden" name="expected_version" value="${doc.version}"><p class="hint">Sauvegardez avant de déposer cette version comme livrable. Une modification ultérieure demandera un nouveau dépôt.</p><button class="btn" type="submit">Sauvegarder une version</button></form>`:`<pre class="textwrap">${esc(doc.content)}</pre>`;
  modal(doc.title,`<div class="actions">${button('Retour à la tâche','work-document-back','arrow','ghost small',`data-id="${esc(w.id)}"`)}${button('Exporter le texte','work-document-export','download','ghost small',`data-id="${esc(w.id)}" data-document-id="${esc(doc.id)}" data-version="${doc.version}" data-format="${esc(doc.format)}"`)}</div><p class="hint">Version ${doc.version} · SHA-256 ${esc(doc.sha256)}${doc.source_entry_id?' · origine : pièce '+esc(doc.source_entry_id):''}${doc.source_file_id?' · origine : fichier '+esc(doc.source_file_id):''}</p>${editor}${canEdit?`<div class="actions">${button('Déposer cette version comme livrable','work-document-submit','check','secondary',`data-id="${esc(w.id)}" data-document-id="${esc(doc.id)}"`)}</div>`:''}<h3>Historique des versions</h3>${versions}<h3>Commentaires</h3>${comments||'<p class="hint">Aucun commentaire.</p>'}<form id="work-document-comment-form" data-id="${esc(w.id)}" data-document-id="${esc(doc.id)}"><input type="hidden" name="version" value="${doc.version}">${textArea('quote','Passage exact à commenter (facultatif)','',2)}${textArea('content','Votre commentaire sur cette version','',3)}<button class="btn secondary" type="submit">Ajouter un commentaire</button></form>`,'','large');
}
function formattedMessage(text){return esc(text).split('\n').map(line=>{
  line=line.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  if(/^#{1,4} /.test(line))return '<h3>'+line.replace(/^#{1,4} /,'')+'</h3>';
  if(/^\* /.test(line))return '<p>• '+line.slice(2)+'</p>';
  return line?'<p>'+line+'</p>':'';
}).join('');}
function messageHtml(p){return p.messages.filter(m=>m.role!=='observation').map(m=>`<article class="chat-message ${m.role}"><div class="message-label">${m.role==='user'?esc(S.user.name):m.role==='action'?'Action de l’équipe':'Coordinateur'} <time>${fmt(m.at)}</time></div><div>${formattedMessage(m.text)}</div>${m.role==='assistant'?button('Écouter','voice-read','mic','ghost small',`data-id="${m.id}"`)+button('Couper la voix','voice-stop',null,'ghost small'):''}</article>`).join('');}
function approvalHtml(p){return p.approvals.map(a=>{
  let followup='';
  const dustEmpty=a.dust_message_count===0?'<p class="notice info">Cette conversation Dust est vide. Aucun message ni réponse d’agent n’a été confirmé ; Passage n’a rien renvoyé.</p>':'';
  if(a.status==='succeeded'&&a.service==='pipelex'&&a.tool==='pipelex_run'){
    followup=`<div class="actions">${a.pipelex_run_id?button('Lire état et résultat Pipelex','pipelex-status','search','secondary small',`data-id="${a.id}"`):'<p class="hint">Identifiant de run non identifié automatiquement. Consultez la réponse du service.</p>'}</div>`;
    if(a.pipelex_checked_at){
      const life=a.pipelex_lifecycle;
      const progress=life?(life.is_terminal?(life.run_status==='COMPLETED'?'Méthode terminée · résultat à vérifier':'Méthode terminée sans livrable · '+life.run_status):'Méthode en cours · '+life.run_status+(life.retry_after_seconds!==null?' · délai conseillé : '+life.retry_after_seconds+' s après cette lecture':'')):'État à lire dans la réponse brute';
      followup+=`<p class="hint">Dernière lecture : ${fmt(a.pipelex_checked_at)} · run ${esc(a.pipelex_run_id)}</p><p class="hint">${esc(progress)}${life?.degraded?' · état ancien selon Pipelex':''}</p><details><summary>État Pipelex</summary><pre>${esc(JSON.stringify(a.pipelex_status,null,2).slice(0,30000))}</pre></details><details><summary>Résultat Pipelex</summary><pre>${esc(JSON.stringify(a.pipelex_results,null,2).slice(0,30000))}</pre></details>`;
    }
  }
  if(a.status==='succeeded'&&['dust','dust-eu'].includes(a.service)&&a.tool==='create_conversation'){
    followup=`<div class="actions">${a.dust_conversation_id?button('Lire la réponse Dust','dust-messages','search','secondary small',`data-id="${a.id}"`):'<p class="hint">Identifiant de conversation non identifié automatiquement. Consultez la réponse du service avant toute nouvelle tentative.</p>'}</div>`;
    if(a.dust_checked_at)followup+=`${dustEmpty}<p class="hint">Dernière lecture : ${fmt(a.dust_checked_at)} · conversation ${esc(a.dust_conversation_id)}</p><details open><summary>Messages Dust</summary><pre>${esc(JSON.stringify(a.dust_messages,null,2).slice(0,30000))}</pre></details>`;
  }
  if(a.status==='delivery_unknown'&&['dust','dust-eu'].includes(a.service)&&a.tool==='create_conversation'&&a.source==='dialogue'){
    followup=`<p class="hint">L'envoi peut avoir créé une conversation. Passage ne renverra pas le message. La recherche exige le droit list_conversations et ne retient que le titre exact de cette carte. La lecture des messages exige get_conversation_messages.</p><div class="actions">${a.dust_conversation_id?button('Lire les messages retrouvés','dust-messages','search','secondary small',`data-id="${a.id}"`):button('Retrouver dans Dust','dust-recover','search','secondary small',`data-id="${a.id}"`)}</div>`;
    if(a.dust_recovered_at)followup+=`<p class="hint">Conversation retrouvée le ${fmt(a.dust_recovered_at)}. Vérifiez si le message initial a été publié.</p>`;
    if(a.dust_checked_at)followup+=`${dustEmpty}<details open><summary>Messages Dust</summary><pre>${esc(JSON.stringify(a.dust_messages,null,2).slice(0,30000))}</pre></details>`;
  }
  return `<article class="card approval"><h3>${a.status==='pending'?'Votre validation':'Action externe'}</h3>${badge(statusNames[a.status]||a.status,'amber')}<p>${esc(a.explanation)}</p><strong>${esc(a.service)} · ${esc(a.tool)}</strong>${a.method_signature?`<p class="hint">Contrat Pipelex vérifié : ${esc(a.method_signature)}</p>`:``}<pre>${esc(JSON.stringify(a.arguments,null,2))}</pre>${a.status==='pending'?`<div class="actions">${button('Confirmer','approve','check','small',`data-id="${a.id}" data-accept="true"`)}${button('Refuser','approve',null,'secondary small',`data-id="${a.id}" data-accept="false"`)}</div>`:''}${a.result?`<details><summary>Réponse du service</summary><pre>${esc(JSON.stringify(a.result,null,2).slice(0,30000))}</pre></details>`:''}${followup}</article>`;
}).join('');}
function coordinatorSelect(selected=''){
  const direct=S.data.agents.filter(a=>a.active&&a.engine==='direct');
  return `<div class="field"><label for="coordinator_id">Cerveau du coordinateur</label><select id="coordinator_id" name="coordinator_id" required>${direct.map(a=>`<option value="${esc(a.id)}" ${a.id===selected?'selected':''}>${esc(a.name)} · ${esc(a.provider==='codex'?'ChatGPT via Codex':a.provider==='ollama'?'Ollama local':a.provider)} · ${esc(a.model)}</option>`).join('')}</select></div>${direct.length?'':'<p class="notice error">Créez d’abord un agent direct actif dans l’Atelier des agents.</p>'}`;
}
async function newProject(){
  let options='<option value="codex:auto">ChatGPT · modèle par défaut de mon compte</option>';
  options+='<option value="agent">Utiliser le fournisseur choisi dans l’agent coordinateur</option>';
  modal('Un projet, une équipe',`<form id="project-form">${textField('name','Nom du projet','','text',true)}${textArea('objective','Objectif et résultat attendu','',4)}${textArea('context','Contexte, contraintes et critères de réussite','',3)}${coordinatorSelect()}<div class="field"><label for="new-project-brain">Cerveau du projet</label><select id="new-project-brain" name="brain_choice">${options}</select></div><p class="hint">ChatGPT est sélectionné par défaut. Connectez ce même compte dans Connexions avant le premier échange réel ; aucun modèle local ne sera choisi automatiquement.</p><button class="btn" type="submit">Créer le projet</button></form>`,'','medium');
  const brainSelect=$('#new-project-brain');
  try{
    const status=await api('/brains/chatgpt/status');
    if(status.connected&&$('#new-project-brain')===brainSelect){
      const available=await api('/brains/chatgpt/models');
      if($('#new-project-brain')===brainSelect){
        for(const model of available.models)brainSelect.add(new Option('ChatGPT · '+(model.displayName||model.model),'codex:'+model.model));
      }
    }
  }catch{}
}
async function sendDialogue(text, conversationEpoch=null){
  const previousProjectId=S.project?.id;
  const response=await post('/dialogue',{project_id:S.project?.id||null,message:text,mode:S.mode});
  if(!response.project_id){
    const input=$('#chat-input');if(input)input.value='';
    const notice=$('#dialogue-notice');if(notice&&response.notice){notice.textContent=response.notice;notice.hidden=false;}
    if(conversationEpoch!==null)await speakAndResume(response.notice||'Commande reçue.',conversationEpoch);
    else if(response.notice&&S.voiceReply)await speakReply(response.notice);
    return;
  }
  S.project=await api('/projects/'+response.project_id);rememberProject();S.projects=await api('/projects');
  if(previousProjectId!==S.project.id)clearTimeout(missionTimer);
  const input=$('#chat-input');if(input)input.value='';
  renderView();
  if(response.notice)toast(response.notice);
  if(response.run){if(conversationEpoch!==null)S.voicePendingRun=response.run.id;followMission(response.run.id);}
  else if(response.command==='select'&&S.project.run_id&&conversationEpoch===null)resumeMission();
  if(!response.run){
    const last=S.project.messages.filter(m=>m.role==='assistant').at(-1);
    const answer=response.notice||(response.command==='create'?'Projet créé et ouvert.':last?.text||'Commande reçue.');
    if(conversationEpoch!==null)await speakAndResume(answer,conversationEpoch);
    else if(S.voiceReply&&answer)await speakReply(answer);
  }
}
async function reloadProject(){if(!S.project)return;S.project=await api('/projects/'+S.project.id);S.projects=await api('/projects');}
function resumeMission(){if(S.project?.run_id)followMission(S.project.run_id);}
async function followMission(id){
  clearTimeout(missionTimer);
  try{
    const job=await api('/runs/'+id);await reloadProject();
    if(S.view==='chat'&&S.project?.run_id===id){
      const messages=$('#messages');if(messages){messages.innerHTML=messageHtml(S.project);messages.scrollTop=messages.scrollHeight;}
      if($('#approvals'))$('#approvals').innerHTML=approvalHtml(S.project);
      if($('#mission-status'))$('#mission-status').innerHTML=`<div class="mission-line">${badge(statusNames[job.status]||job.status)}<span>${esc(job.trace.at(-1)?.message||'Préparation de l’équipe…')}</span>${['queued','running'].includes(job.status)?button('Arrêter','stop-mission',null,'ghost small'):''}</div>`;
      // Keep input usable for stop commands while a model call is running.
    }
    if(['queued','running'].includes(job.status))missionTimer=setTimeout(()=>followMission(id),2000);
    else if(job.status==='failed'){
      toast(job.error,true);
      if(S.voiceConversation&&S.voicePendingRun===id){S.voicePendingRun=null;await speakAndResume('La mission a échoué. Consultez le détail dans les exécutions.',S.voiceEpoch);}
    }
    else if(S.project?.run_id===id){
      if(S.view==='chat')renderView();
      for(const work of S.project.work_items||[]){
        if(work.status==='delegated'&&work.run_id)followWorkRun(work.run_id,work.id);
      }
      const last=S.project.messages.filter(m=>m.role==='assistant').at(-1);
      if(S.voiceConversation&&S.voicePendingRun===id){S.voicePendingRun=null;await speakAndResume(last?.text||'Mission terminée.',S.voiceEpoch);}
      else if(!S.voiceConversation&&S.voiceReply&&last&&S.spoken!==last.id){S.spoken=last.id;await speakReply(last.text);}
    }
  }catch(e){toast(e.message,true);}
}
async function workspaceClick(action,b){
  if(await jinkoAction(action,b))return true;
  if(await teamAction(action,b))return true;
  if(action==='work-filter'){S.workPersona=b.dataset.persona;renderView();return true;}
  if(action==='work-new'){
    const all=await api('/work/catalog');
    const options=all.map(t=>`<option value="${esc(t.id)}">${esc(personaLabels[t.persona]||t.persona)} · ${esc(t.title)}</option>`).join('');
    modal('Ouvrir une tâche de recherche',`<form id="work-create-form"><label for="work-type">Tâche</label><select id="work-type" name="type_id">${options}</select>${textField('title','Titre personnalisé (facultatif)')}${textArea('brief','Votre situation, vos données et le résultat attendu','',5)}<label for="work-due">Échéance (facultative)</label><input id="work-due" type="date" name="due_at"><p class="hint">La tâche donnera un parcours à suivre vous-même ou à confier à un agent de votre équipe.</p><button class="btn" type="submit">Créer la tâche</button></form>`,'','medium');return true;
  }
  if(action==='work-open'){const w=await api('/work/tasks/'+b.dataset.id);if(S.project)await reloadProject();S.workInbox=await api('/work/inbox');renderView();workModal(w);return true;}
  if(action==='work-linked-sources'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const all=await api('/work/projects/'+w.project_id);
    const selected=new Set((w.linked_sources||[]).map(link=>link.task_id));
    const options=all.filter(item=>item.id!==w.id&&item.status==='done').map(item=>`<label class="check"><input type="checkbox" name="source_task_ids" value="${esc(item.id)}" ${selected.has(item.id)?'checked':''}>${esc(item.title)} · ${esc(item.definition.title)}</label>`).join('');
    modal('Lier des livrables validés',`<p class="hint">Six sources maximum. Seuls les livrables actuellement validés peuvent être liés. L’agent recevra leurs extraits si leur droit d’usage par agent est établi. Partagez d’abord chaque tâche source avec tous les invités de ce travail.</p><form id="work-linked-sources-form" data-id="${esc(w.id)}" data-revision="${w.revision}">${options||'<p class="hint">Aucune autre tâche validée dans ce projet.</p>'}<button class="btn" type="submit">Enregistrer les liens</button></form>`,'','medium');return true;
  }
  if(action==='work-checkpoint'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const checkpoint=(w.checkpoints||[]).find(item=>item.code===b.dataset.code);
    if(!checkpoint)throw new Error('Point de contrôle introuvable.');
    const options=[...(w.entries||[]).filter(item=>item.kind==='evidence'&&item.origin==='human').map(item=>['entry:'+item.id,'Preuve · '+item.title]),
      ...(w.files||[]).map(item=>['file:'+item.id,'Fichier · '+item.name])];
    modal('Attester · '+checkpoint.title,`<p>${esc(checkpoint.guidance)}</p><p class="notice info">Cette déclaration sera attribuée à votre compte. Elle ne remplace pas une autorisation institutionnelle ni une vérification de Passage.</p><form id="work-checkpoint-form" data-id="${esc(w.id)}" data-code="${esc(checkpoint.code)}"><label for="checkpoint-evidence">Pièce de cette tâche</label><select id="checkpoint-evidence" name="evidence" required>${options.map(([id,label])=>`<option value="${esc(id)}">${esc(label)}</option>`).join('')}</select>${options.length?'':'<p class="notice info">Ajoutez d’abord une preuve ou un fichier dans la tâche.</p>'}<label for="checkpoint-date">Date de l’action ou de l’accord</label><input id="checkpoint-date" type="date" name="occurred_at" value="${new Date().toISOString().slice(0,10)}" required>${textArea('statement','Décrivez précisément ce que vous attestez et la portée de la pièce','',4)}<button class="btn" type="submit" ${options.length?'':'disabled'}>Enregistrer l’attestation</button></form>`,'','medium');return true;
  }
  if(action==='work-diagram-new'){
    modal('Créer un schéma',`<form id="work-diagram-create-form" data-id="${esc(b.dataset.id)}">${textField('title','Titre du protocole ou du processus','','text',true)}<p class="hint">Le dessin reste dans la tâche et sera versionné.</p><button class="btn" type="submit">Créer et dessiner</button></form>`,'','medium');return true;
  }
  if(action==='work-diagram-open'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const diagram=w.diagrams.find(item=>item.id===b.dataset.diagramId);
    if(!diagram)throw new Error('Schéma introuvable.');
    const url='/static/diagram/index.html?work_id='+encodeURIComponent(w.id)+'&diagram_id='+encodeURIComponent(diagram.id)+'&editable='+(['owner','editor'].includes(w.my_access)?'1':'0');
    modal(diagram.title,`<p class="hint">Enregistrez le dessin avant de fermer cette fenêtre. Le protocole produit par l’agent restera un brouillon à relire.</p><iframe class="diagram-frame" title="Éditeur de schéma" src="${url}"></iframe><div class="actions">${button('Retour à la tâche','work-open','arrow','secondary small',`data-id="${esc(w.id)}"`)}</div>`,'','diagram');return true;
  }
  if(action==='work-diagram-export'){await download('/work/tasks/'+b.dataset.id+'/diagrams/'+b.dataset.diagramId+'/export','passage-'+b.dataset.diagramId+'.excalidraw');return true;}
  if(action==='work-diagram-formalize'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const diagram=w.diagrams.find(item=>item.id===b.dataset.diagramId);
    if(!diagram)throw new Error('Schéma introuvable.');
    const roster=(S.data?.agents||[]).filter(a=>a.active&&a.engine==='direct'&&S.project?.agent_ids.includes(a.id));
    modal('Formaliser le schéma',`<p><strong>${esc(diagram.title)}</strong> · version ${diagram.version}</p><p class="hint">L’agent lira les formes et les flèches enregistrées, signalera les ambiguïtés et créera un document brouillon. Vous déciderez de ses corrections et de son dépôt.</p><form id="work-diagram-formalize-form" data-id="${esc(w.id)}" data-diagram-id="${esc(diagram.id)}" data-version="${diagram.version}"><label for="diagram-agent">Agent de l’équipe</label><select name="agent_id" id="diagram-agent">${roster.map(a=>`<option value="${esc(a.id)}">${esc(a.name)} · ${esc(a.model)}</option>`).join('')}</select><label for="diagram-target">Document à produire</label><select name="target" id="diagram-target"><option value="protocol">Protocole Markdown</option><option value="pipelex">Brouillon de méthode Pipelex .mthds</option></select><p class="hint">Une méthode Pipelex produite ici n’est ni publiée ni exécutée.</p><button class="btn" type="submit" ${roster.length?'':'disabled'}>Demander la formalisation</button></form>`,'','medium');return true;
  }
  if(action==='work-export'){await download('/work/tasks/'+b.dataset.id+'/export.md','passage-travail-'+b.dataset.id+'.md');return true;}
  if(action==='work-document-back'){workModal(await api('/work/tasks/'+b.dataset.id));return true;}
  if(action==='work-document-new'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const template=b.dataset.template==='true'?await api('/work/tasks/'+w.id+'/template'):null;
    modal('Créer un document de travail',`<form id="work-document-create-form" data-id="${esc(w.id)}">${textField('title','Titre',w.definition.output,'text',true)}<label for="new-document-format">Format du texte</label><select id="new-document-format" name="format"><option value="markdown">Markdown</option><option value="latex">LaTeX</option><option value="python">Python</option><option value="r">R</option><option value="plain">Texte brut</option><option value="csv">CSV</option></select>${textArea('content','Premier texte (facultatif)',template?.content||'',12)}<p class="hint">${template?'Trame à compléter et vérifier ; aucun résultat externe n’est présumé.':'Le texte reste privé à cette tâche et à ses comptes invités.'}</p><button class="btn" type="submit">Créer le document</button></form>`,'','large');return true;
  }
  if(action==='work-document-from-entry'){
    const w=await api('/work/tasks/'+b.dataset.id),source=w.entries.find(e=>e.id===b.dataset.entryId);
    if(!source)throw new Error('Pièce introuvable dans cette tâche.');
    const response=await post('/work/tasks/'+w.id+'/documents',{title:w.definition.output,format:'markdown',source_entry_id:source.id});
    if(S.project)await reloadProject();renderView();workDocumentModal(response.task,response.document);return true;
  }
  if(action==='work-document-from-file'){
    const w=await api('/work/tasks/'+b.dataset.id),source=w.files.find(f=>f.id===b.dataset.fileId);
    if(!source)throw new Error('Fichier introuvable dans cette tâche.');
    const extension=source.name.split('.').at(-1).toLowerCase();
    const format=({md:'markdown',tex:'latex',py:'python',r:'r',csv:'csv',mthds:'mthds'})[extension]||'plain';
    const response=await post('/work/tasks/'+w.id+'/documents',{title:source.name,format,source_file_id:source.id});
    if(S.project)await reloadProject();renderView();workDocumentModal(response.task,response.document);return true;
  }
  if(action==='work-document-open'){
    const w=await api('/work/tasks/'+b.dataset.id),doc=await api('/work/tasks/'+b.dataset.id+'/documents/'+b.dataset.documentId);
    workDocumentModal(w,doc);return true;
  }
  if(action==='work-document-version'){
    const version=await api('/work/tasks/'+b.dataset.id+'/documents/'+b.dataset.documentId+'/versions/'+b.dataset.version);
    modal(version.title+' · version '+version.version,`<div class="actions">${button('Retour au document','work-document-open','arrow','ghost small',`data-id="${esc(b.dataset.id)}" data-document-id="${esc(b.dataset.documentId)}"`)}</div><p class="hint">${fmt(version.created_at)} · SHA-256 ${esc(version.sha256)}</p><pre class="textwrap">${esc(version.content)}</pre>`,'','large');return true;
  }
  if(action==='work-document-export'){
    const extension=({markdown:'md',latex:'tex',python:'py',r:'r',plain:'txt',csv:'csv'})[b.dataset.format]||'txt';
    await download('/work/tasks/'+b.dataset.id+'/documents/'+b.dataset.documentId+'/export','passage-document-'+b.dataset.documentId+'-v'+b.dataset.version+'.'+extension);return true;
  }
  if(action==='work-document-submit'){
    const response=await post('/work/tasks/'+b.dataset.id+'/documents/'+b.dataset.documentId+'/submit',{});
    if(S.project)await reloadProject();S.workInbox=await api('/work/inbox');renderView();workModal(response.task);return true;
  }
  if(action==='work-step'){
    const w=await api('/work/tasks/'+b.dataset.id),index=Number(b.dataset.index),done=b.dataset.done==='true';
    const play=w.definition.playbook[index],draft=[...(w.entries||[])].reverse().find(e=>e.kind==='agent_draft'&&e.focus_step===index);
    const previous=(w.step_checks||[])[index]?.record;
    const proposed=done&&draft?(draft.checks||[]).join(' · '):'';
    const initial=done?(previous?.note||proposed):'';
    const selected=done&&draft&&!previous?`entry:${draft.id}`:(previous?.proof_kind?`${previous.proof_kind}:${previous.proof_id}`:'');
    modal(done?'Vérifier l’étape '+(index+1):'Rouvrir l’étape '+(index+1),`<p class="hint">${esc(play.human_action)} · Contrôle attendu : ${esc(play.evidence)}</p>${draft&&done?`<p class="hint">Proposition de l’agent : ${esc(proposed||draft.content.slice(0,400))}. Vérifiez-la avant de confirmer.</p>`:''}<form id="work-step-form" data-id="${esc(w.id)}" data-index="${index}" data-done="${done}" data-revision="${w.revision}">${textArea('note',done?'Ce que vous avez personnellement vérifié':'Pourquoi vous rouvrez cette étape',initial,5)}${done?`<label for="work-step-proof">Pièce liée (facultative)</label><select id="work-step-proof" name="proof">${stepProofOptions(w,selected)}</select>`:''}<button class="btn" type="submit">${done?'Confirmer la vérification':'Rouvrir l’étape'}</button></form>`,'','medium');return true;
  }
  if(action==='work-edit'){
    const w=await api('/work/tasks/'+b.dataset.id);
    modal('Modifier le cadrage',`<form id="work-edit-form" data-id="${esc(w.id)}">${textField('title','Titre',w.title,'text',true)}${textArea('brief','Situation et résultat attendu',w.brief,6)}<label for="work-due">Échéance</label><input id="work-due" type="date" name="due_at" value="${esc(w.due_at||'')}"><button class="btn" type="submit">Enregistrer</button></form>`,'','medium');return true;
  }
  if(action==='work-worksheet'||action==='work-worksheet-from-agent'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const questions=w.definition.worksheet_questions||[];
    const source=action==='work-worksheet-from-agent'?w.entries.find(e=>e.id===b.dataset.entryId&&e.kind==='agent_draft'&&e.worksheet_proposals):null;
    if(action==='work-worksheet-from-agent'&&!source)throw new Error('Proposition structurée introuvable dans cette tâche.');
    const fields=questions.map(q=>`<label for="work-question-${esc(q.code)}">${esc(q.title)}</label><textarea id="work-question-${esc(q.code)}" name="${esc(q.code)}" rows="4" maxlength="4000">${esc(source?.worksheet_proposals?.[q.code]||w.worksheet?.[q.code]||'')}</textarea>`).join('');
    modal('Questions de travail',`<p class="hint">${source?'Relisez et corrigez chaque proposition de l’agent avant de l’enregistrer.':'Renseignez les faits connus. L’agent pourra proposer les parties manquantes ; vous vérifierez son brouillon.'}</p><form id="work-worksheet-form" data-id="${esc(w.id)}" data-revision="${w.revision}" data-source-entry-id="${esc(source?.id||'')}">${fields}<button class="btn" type="submit">Enregistrer les réponses</button></form>`,'','medium');return true;
  }
  if(['work-record-new','work-record-edit','work-record-from-agent'].includes(action)){
    const w=await api('/work/tasks/'+b.dataset.id);
    const record=action==='work-record-edit'?w.records.find(item=>item.id===b.dataset.recordId):null;
    const source=action==='work-record-from-agent'?w.entries.find(item=>item.id===b.dataset.entryId&&item.kind==='agent_draft'):null;
    const suggestionIndex=source?Number(b.dataset.index):-1;
    const suggestion=source?.record_suggestions?.[suggestionIndex];
    if(action==='work-record-edit'&&!record)throw new Error('Ligne introuvable.');
    if(action==='work-record-from-agent'&&!suggestion)throw new Error('Ligne proposée introuvable.');
    const values=record?.values||suggestion||{};
    const fields=w.definition.register.columns.map(column=>`<label for="record-${esc(column.code)}">${esc(column.title)}</label><textarea id="record-${esc(column.code)}" name="${esc(column.code)}" rows="3" maxlength="2000" ${column.code==='c1'?'required':''}>${esc(values[column.code]||'')}</textarea>`).join('');
    const evidenceOptions=[['','Aucune pièce liée'],...(w.entries||[]).filter(item=>item.kind==='evidence'&&item.origin==='human').map(item=>['entry:'+item.id,'Preuve · '+item.title]),...(w.files||[]).map(item=>['file:'+item.id,'Fichier · '+item.name])];
    const selected=record?.evidence_entry_id?'entry:'+record.evidence_entry_id:record?.file_id?'file:'+record.file_id:'';
    const evidence=`<label for="record-evidence">Preuve ou fichier de cette tâche (facultatif)</label><select id="record-evidence" name="evidence">${evidenceOptions.map(([id,label])=>`<option value="${esc(id)}" ${selected===id?'selected':''}>${esc(label)}</option>`).join('')}</select>`;
    modal(record?'Modifier la ligne':'Ajouter une ligne · '+w.definition.register.title,`<p class="hint">${source?'Relisez et corrigez la proposition de l’agent.':'Une ligne correspond à un élément de ce travail ; les cellules peuvent être complétées ensuite.'}</p><form id="work-record-form" data-id="${esc(w.id)}" data-record-id="${esc(record?.id||'')}" data-revision="${w.revision}" data-version="${record?.version||''}" data-source-entry-id="${esc(source?.id||'')}" data-suggestion-index="${suggestionIndex}">${fields}${evidence}<button class="btn" type="submit">Enregistrer la ligne</button></form>`,'','medium');return true;
  }
  if(action==='work-record-archive'||action==='work-record-restore'){
    const w=await api('/work/tasks/'+b.dataset.id),record=w.records.find(item=>item.id===b.dataset.recordId);
    if(!record)throw new Error('Ligne introuvable.');
    const response=await api('/work/tasks/'+w.id+'/records/'+record.id,{method:'PUT',body:JSON.stringify({expected_revision:w.revision,expected_version:record.version,values:record.values,active:action==='work-record-restore',evidence_entry_id:record.evidence_entry_id||'',file_id:record.file_id||''})});
    if(S.project)await reloadProject();renderView();workModal(response.task);return true;
  }
  if(action==='work-anchor-new'||action==='work-anchor-from-agent'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const entry=action==='work-anchor-from-agent'?w.entries.find(item=>item.id===b.dataset.entryId&&item.kind==='agent_draft'):null;
    const index=entry?Number(b.dataset.index):-1;
    const suggestion=entry?.citation_suggestions?.[index];
    if(action==='work-anchor-from-agent'&&!suggestion)throw new Error('Passage proposé introuvable.');
    const sources=[...(w.files||[]).filter(item=>item.readable_by_agent).map(item=>['file:'+item.id,'Fichier · '+item.name]),...(w.documents||[]).map(item=>['document:'+item.id,'Document · '+item.title+' · version '+item.version])];
    const selected=suggestion?suggestion.source_type+':'+suggestion.source_id:'';
    modal('Ancrer un passage',`<p class="hint">Copiez un passage exact du texte extrait ou du document, puis formulez ce qu’il étaye. Passage vérifiera sa présence et conservera la version source. Une citation proposée par l’agent reste à relire.</p><form id="work-anchor-form" data-id="${esc(w.id)}" data-revision="${w.revision}" data-source-entry-id="${esc(entry?.id||'')}" data-suggestion-index="${index}"><label for="anchor-source">Source de cette tâche</label><select id="anchor-source" name="source" required>${sources.map(([key,label])=>`<option value="${esc(key)}" ${selected===key?'selected':''}>${esc(label)}</option>`).join('')}</select>${textArea('quote','Passage exact',suggestion?.quote||'',5)}${textArea('claim','Affirmation étayée',suggestion?.claim||'',4)}<button class="btn" type="submit" ${sources.length?'':'disabled'}>Vérifier et enregistrer</button></form>${sources.length?'':'<p class="notice info">Joignez un fichier lisible ou créez un document avant d’ancrer un passage.</p>'}`,'','medium');return true;
  }
  if(action==='work-anchor-archive'||action==='work-anchor-restore'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const item=(w.anchors||[]).find(anchor=>anchor.id===b.dataset.anchorId);
    if(!item)throw new Error('Passage sourcé introuvable.');
    const response=await api('/work/tasks/'+w.id+'/anchors/'+item.id+'/status',{method:'PUT',body:JSON.stringify({expected_revision:w.revision,active:action==='work-anchor-restore'})});
    if(S.project)await reloadProject();renderView();workModal(response.task);return true;
  }
  if(action==='work-add'){
    const names={note:'Note de travail',evidence:'Preuve ou référence',deliverable:'Livrable humain'};
    let title='',content='',from='';
    if(b.dataset.kind==='deliverable'){
      const w=await api('/work/tasks/'+b.dataset.id);
      const source=w.entries.find(e=>e.id===b.dataset.from&&e.kind==='agent_draft');
      if(b.dataset.from&&!source)throw new Error('Brouillon introuvable dans cette tâche.');
      title=w.definition.output;
      content=source?.content||(await api('/work/tasks/'+w.id+'/template')).content;
      from=source?.id||'';
    }
    modal('Ajouter '+names[b.dataset.kind].toLowerCase(),`<form id="work-entry-form" data-id="${esc(b.dataset.id)}" data-kind="${esc(b.dataset.kind)}"><input type="hidden" name="derived_from" value="${esc(from)}">${textField('title','Titre',title,'text',true)}${textArea('content','Contenu, observations ou résultat',content,12)}${textField('url','Lien de référence (facultatif)')}${from?'<p class="hint">Cette version humaine conserve un lien vers le brouillon de l’agent. Vérifiez et corrigez avant de l’enregistrer.</p>':''}<button class="btn" type="submit">Conserver dans la tâche</button></form>`,'','medium');return true;
  }
  if(action==='work-file-add'){
    modal('Joindre une pièce au travail',`<form id="work-file-form" data-id="${esc(b.dataset.id)}"><label for="work-file-input">Fichier</label><input id="work-file-input" name="file" type="file" required accept=".txt,.md,.csv,.tsv,.json,.py,.r,.tex,.yaml,.yml,.pdf,.docx,.xlsx,.png,.jpg,.jpeg"><p class="hint">8 Mo maximum. Passage extrait le texte des PDF et DOCX lisibles ; les scans, images et XLSX restent des pièces non analysées.</p><button class="btn" type="submit">Conserver le fichier</button></form>`,'','medium');return true;
  }
  if(action==='work-file-download'){await download('/work/tasks/'+b.dataset.id+'/files/'+b.dataset.fileId,b.dataset.name);return true;}
  if(action==='work-file-analyze'){
    const response=await post('/work/tasks/'+b.dataset.id+'/files/'+b.dataset.fileId+'/analyze');
    if(S.project)await reloadProject();S.workInbox=await api('/work/inbox');renderView();workModal(response.task);return true;
  }
  if(action==='work-file-describe'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const profile=await api('/work/tasks/'+b.dataset.id+'/files/'+b.dataset.fileId+'/profile');
    const file=(w.files||[]).find(item=>item.id===b.dataset.fileId);
    if(!file)throw new Error('Fichier introuvable.');
    const columns=profile.columns||[];
    const numeric=Object.keys(profile.numeric_by_column||{});
    modal('Analyse descriptive · '+file.name,`<p class="hint">Calcul local sur le tableau extrait complet. Les lignes sans valeur numérique ou sans groupe seront exclues et comptées. Aucun test statistique ni conclusion causale n’est produit.</p><form id="work-table-analysis-form" data-id="${esc(w.id)}" data-file-id="${esc(file.id)}"><input type="hidden" name="expected_revision" value="${w.revision}"><label for="table-value-column">Variable numérique</label><select id="table-value-column" name="value_column">${columns.map(name=>`<option value="${esc(name)}" ${name===numeric[0]?'selected':''}>${esc(name)}</option>`).join('')}</select><label for="table-group-column">Comparer par groupe (facultatif)</label><select id="table-group-column" name="group_column"><option value="">Tout le tableau</option>${columns.map(name=>`<option value="${esc(name)}">${esc(name)}</option>`).join('')}</select><p class="hint">${profile.rows_examined} lignes repérées · SHA-256 ${esc(file.sha256.slice(0,16))}…</p><button class="btn" type="submit">Calculer et conserver le résultat</button></form>`,'','medium');return true;
  }
  if(action==='work-delegate'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const roster=S.project.agent_ids.map(id=>S.data.agents.find(a=>a.id===id)).filter(a=>a&&a.active&&a.engine==='direct'&&(a.role!=='research_task'||(a.work_specialties||[]).includes(w.type_id)));
    roster.sort((a,b)=>Number(b.role==='research_task')-Number(a.role==='research_task'));
    const requested=Number(b.dataset.stepIndex),focus=Number.isInteger(requested)&&requested>=0&&requested<4?requested:-1;
    modal('Confier à un agent',`<p class="hint">${esc(w.definition.agent_work)}</p><form id="work-delegate-form" data-id="${esc(w.id)}"><input type="hidden" name="expected_revision" value="${w.revision}"><label for="work-agent">Agent de cette équipe</label><select id="work-agent" name="agent_id">${roster.map(a=>`<option value="${esc(a.id)}">${esc(a.name)} · ${a.role==='research_task'?'spécialiste':'généraliste'} · ${esc(a.model)}</option>`).join('')}</select><label for="work-focus-step">Portée de l’aide</label><select id="work-focus-step" name="focus_step"><option value="-1" ${focus<0?'selected':''}>Toute la tâche</option>${w.definition.playbook.map((play,index)=>`<option value="${index}" ${focus===index?'selected':''}>${index+1}. ${esc(play.human_action)}${play.external?' · action humaine externe':''}</option>`).join('')}</select>${roster.length?'':'<p class="notice info">Aucun agent adapté dans cette équipe. Ajoutez un agent actif depuis « Composer l’équipe ».</p>'}${textArea('instruction','Précision pour cet agent (facultative)','',4)}<p class="hint">${focus>=0?esc(w.definition.playbook[focus].agent_help)+' L’action externe reste à la personne responsable.':'Il préparera un brouillon dans la tâche.'} Vous vérifierez le livrable avant validation.</p><button class="btn" type="submit" ${roster.length?'':'disabled'}>Lancer l’agent</button></form>`,'','medium');return true;
  }
  if(action==='work-rework'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const draft=[...(w.entries||[])].reverse().find(item=>item.kind==='agent_draft');
    if(!draft||draft.id!==b.dataset.entryId)throw new Error('Le dernier brouillon a changé. Rechargez la tâche.');
    const roster=S.project.agent_ids.map(id=>S.data.agents.find(a=>a.id===id)).filter(a=>a&&a.active&&a.engine==='direct'&&(a.role!=='research_task'||(a.work_specialties||[]).includes(w.type_id)));
    roster.sort((a,b)=>Number(b.role==='research_task')-Number(a.role==='research_task'));
    modal('Faire corriger le brouillon',`<p class="hint">Brouillon visé : ${esc(draft.title)} · ${fmt(draft.created_at)}. Décrivez les passages à modifier, les preuves manquantes et le résultat attendu. L’agent recevra ce brouillon et les pièces actuelles.</p><form id="work-rework-form" data-id="${esc(w.id)}" data-entry-id="${esc(draft.id)}" data-revision="${w.revision}"><input type="hidden" name="focus_step" value="${Number.isInteger(draft.focus_step)?draft.focus_step:-1}"><label for="rework-agent">Agent de cette équipe</label><select id="rework-agent" name="agent_id">${roster.map(a=>`<option value="${esc(a.id)}" ${a.id===w.last_agent_id?'selected':''}>${esc(a.name)} · ${a.role==='research_task'?'spécialiste':'généraliste'} · ${esc(a.model)}</option>`).join('')}</select>${textArea('instruction','Corrections demandées','',6)}<button class="btn" type="submit" ${roster.length?'':'disabled'}>Confier la correction</button></form>`,'','medium');return true;
  }
  if(action==='project-team'){
    const p=S.project;
    const options=S.data.agents.filter(a=>a.active||p.agent_ids.includes(a.id)).map(a=>`<label class="check"><input type="checkbox" name="agent_ids" value="${esc(a.id)}" ${p.agent_ids.includes(a.id)?'checked':''} ${a.id===p.coordinator_id?'disabled':''}>${esc(a.name)} · ${esc(roleNames[a.role]||a.role)}${a.id===p.coordinator_id?' · coordinateur obligatoire':''}${!a.active?' · inactif, à retirer':''}</label>`).join('');
    modal('Composer l’équipe',`<form id="project-team-form">${options}<p class="hint">Le coordinateur reste dans l’équipe. Les agents spécialisés ne traitent que les tâches choisies dans leur harnais.</p><button class="btn" type="submit">Enregistrer l’équipe</button></form>`,'','medium');return true;
  }
  if(action==='work-review'){
    const w=await api('/work/tasks/'+b.dataset.id);
    const pending=(w.checkpoints||[]).filter(item=>item.before==='done'&&!item.valid);
    const unanswered=(w.definition.worksheet_questions||[]).filter(q=>!w.worksheet?.[q.code]?.trim());
    const blockers=[...unanswered.map(q=>q.title),...pending.map(item=>item.title)];
    if(verifiedStepCount(w)!==w.definition.steps.length)blockers.push('Vérification humaine de chaque étape');
    modal('Décision sur le travail',`<p>${esc(w.title)} · ${verifiedStepCount(w)}/${w.definition.steps.length} étapes vérifiées</p>${blockers.length?`<p class="notice info">Avant validation : ${esc(blockers.join(' · '))}. Complétez les questions et contrôles dans la tâche.</p>`:''}<form id="work-review-form" data-id="${esc(w.id)}"><label for="work-decision">Décision</label><select id="work-decision" name="decision"><option value="accept" ${blockers.length?'disabled':''}>Valider le livrable</option><option value="revise">Demander une révision</option></select>${textArea('note','Motif ou contrôles restant à faire','',4)}<button class="btn" type="submit">Enregistrer la décision</button></form>`,'','medium');return true;
  }
  if(action==='work-share'){
    const w=await api('/work/tasks/'+b.dataset.id);
    modal('Partager la tâche',`${w.linked_sources?.length?'<p class="notice info">Cette tâche utilise des livrables liés. Donnez aussi accès à chaque tâche source avant d’inviter cette personne.</p>':''}<form id="work-share-form" data-id="${esc(b.dataset.id)}">${textField('email','Email d’un compte Passage existant','','email',true)}<label for="work-share-role">Accès</label><select id="work-share-role" name="role"><option value="reviewer">Relecteur : avis et notes</option><option value="editor">Éditeur : étapes et livrables</option></select><button class="btn" type="submit">Donner accès à la tâche</button></form>`,'','medium');return true;
  }
  if(action==='work-peer-review'){
    const w=await api('/work/tasks/'+b.dataset.id);
    modal('Votre avis sur la version '+w.revision,`<form id="work-peer-review-form" data-id="${esc(w.id)}"><label for="work-peer-decision">Avis</label><select id="work-peer-decision" name="decision"><option value="approve">Approuver cette version</option><option value="revise">Demander une révision</option></select>${textArea('note','Motif, réserves ou corrections demandées','',4)}<button class="btn" type="submit">Enregistrer mon avis</button></form>`,'','medium');return true;
  }
  if(action==='voice-conversation'){
    if(S.liveVoice)await stopLiveVoice();
    else await startLiveVoice();
    return true;
  }
  if(action==='research-prompt'){const input=$('#chat-input');if(input){input.value=b.dataset.prompt||'';input.focus();}return true;}
  if(['chatgpt-connect','chatgpt-connect-device','chatgpt-renew-code'].includes(action)){
    if(b.disabled)return true;
    const previous=b.innerHTML;
    b.disabled=true;b.textContent='Préparation de la connexion…';
    try{
      const endpoint=action==='chatgpt-connect'?'connect':action==='chatgpt-renew-code'?'connect-device?restart=true':'connect-device';
      const login=await post('/brains/chatgpt/'+endpoint);
      if(login.connected){await loadBrainAccounts();return true;}
      const el=$('#chatgpt-login');if(el)el.innerHTML=chatgptLoginHtml(login);
      return true;
    }finally{b.disabled=false;b.innerHTML=previous;}
  }
  if(action==='chatgpt-refresh'){await loadBrainAccounts();return true;}
  if(action==='chatgpt-disconnect'){await post('/brains/chatgpt/disconnect');await loadBrainAccounts();return true;}
  if(action==='voice-account-remove'){await api('/voice/account',{method:'DELETE'});await loadVoiceAccount();toast('Clé Gradium personnelle retirée.');return true;}
  if(action==='brain-models'){if($('#provider').value!=='codex'){toast('Choisissez ChatGPT · accès Codex pour charger les modèles de ce compte.');return true;}const result=await api('/brains/chatgpt/models');$('#brain-models').innerHTML=result.models.map(m=>`<option value="${esc(m.model)}">${esc(m.displayName)}</option>`).join('');$('#model').setAttribute('list','brain-models');toast(`${result.models.length} modèles accessibles avec ce compte. Saisissez ou choisissez leur identifiant.`);return true;}
  if(action==='nav'&&S.liveVoice)await stopLiveVoice();
  if(action==='nav'&&S.voiceConversation)await stopVoiceConversation();
  else if(action==='nav'&&S.recording)await stopRecording(false);
  if(action==='voice-read'){const m=S.project?.messages.find(m=>m.id===b.dataset.id);if(m)await speakReply(m.text);return true;}
  if(action==='voice-stop'){stopPlayingAudio();return true;}
  if(action==='auth-toggle'){loginScreen(b.dataset.register==='true');return true;}
  if(action==='google-login'){
    const selected=document.querySelector('#account_type')?.value||'company';
    location.href='/api/auth/google/start?account_type='+encodeURIComponent(selected);
    return true;
  }
  if(action==='google-link'){location.href='/api/auth/google/start?link=true&account_type='+encodeURIComponent(S.user.account_type||'company');return true;}
  if(action==='logout'){await stopLiveVoice();await post('/auth/logout');clearTimeout(missionTimer);await stopRecording(false);stopPlayingAudio();location.reload();return true;}
  if(action==='new-project'){await newProject();return true;}
  if(action==='project-sources'){
    const selected=new Set(S.project.source_ids||[]);
    const rows=S.data.theses.map(t=>`<label class="check source-choice" data-search="${esc((t.title+' '+t.id).toLowerCase())}"><input type="checkbox" name="source_ids" value="${esc(t.id)}" ${selected.has(t.id)?'checked':''}><span><strong>${esc(t.title)}</strong><small>${esc(t.id)} · ${esc(t.status)}${t.abstract?' · résumé disponible':' · sans résumé'}</small></span></label>`).join('');
    modal('Sources du projet',`<p class="hint">Sélectionnez jusqu’à huit notices theses.fr. Leurs résumés seront transmis au rédacteur et au relecteur ; seuls des extraits exacts pourront être cités.</p><form id="project-sources-form"><label for="source-filter">Rechercher un titre ou un identifiant</label><input id="source-filter" type="search" placeholder="Filtrer les notices…"><div class="tool-grants">${rows}</div><button class="btn" type="submit">Enregistrer les sources</button></form>`,'','medium');return true;
  }
  if(action==='project-info'){
    const p=S.project;
    let brainOptions=`<option value="codex:auto" ${p.brain_provider==='codex'&&p.brain_model==='auto'?'selected':''}>ChatGPT · modèle par défaut de mon compte</option><option value="agent" ${p.brain_provider!=='codex'?'selected':''}>Modèle de l’agent · ${esc(S.data.agents.find(a=>a.id===p.coordinator_id)?.model||'')}</option>`;
    try{
      const status=await api('/brains/chatgpt/status');
      if(status.connected){
        const available=await api('/brains/chatgpt/models');
        brainOptions+=available.models.map(m=>`<option value="codex:${esc(m.model)}" ${p.brain_provider==='codex'&&p.brain_model===m.model?'selected':''}>ChatGPT · ${esc(m.displayName||m.model)}</option>`).join('');
      }
    }catch(error){brainOptions+=`<option disabled>Modèles ChatGPT indisponibles : ${esc(error.message)}</option>`;}
    const linked=brainOptions.includes('value="codex:');
    modal('Objectif & équipe',`<h2>${esc(p.name)}</h2><p class="textwrap">${esc(p.objective)}</p><p class="textwrap">${esc(p.context)}</p><form id="coordinator-form">${coordinatorSelect(p.coordinator_id)}<p class="hint">Le coordinateur organise les agents et fournit son harnais au projet.</p><button class="btn" type="submit">Enregistrer le coordinateur</button></form><h3>Cerveau de ce projet</h3><form id="project-brain-form"><label for="project-brain-choice">Modèle utilisé dans le chat et la conversation vocale</label><select id="project-brain-choice" name="brain_choice">${brainOptions}</select><p class="hint">Le choix s’applique à ce projet uniquement. ${linked?'Le compte ChatGPT connecté fournit les modèles disponibles.':'Connectez votre compte ChatGPT dans Connexions pour utiliser ses modèles.'}</p><button class="btn" type="submit">Enregistrer le cerveau</button></form><p class="hint">Pour modifier le nom ou les autres agents de l’équipe, demandez-le dans le chat.</p><h3>Équipe</h3>${p.agent_ids.map(id=>`<p>${esc(S.data.agents.find(a=>a.id===id)?.name||id)}</p>`).join('')}`,'','medium');return true;
  }
  if(action==='project-report'){const r=S.project.reports.find(r=>r.id===b.dataset.id);modal(roleNames[r.role],`<p class="textwrap">${esc(r.content.summary)}</p><h3>Résultat complet</h3><pre>${esc(JSON.stringify(r.content,null,2))}</pre>${button('Exporter','export-report','download','secondary',`data-id="${r.id}"`)}`);return true;}
  if(action==='research-read'){const r=(S.project.research||[]).find(r=>r.id===b.dataset.id);if(!r)throw new Error('Livrable introuvable.');modal(r.title,`<div class="notice info">${r.status==='computed'?'Calcul exécuté avec un modèle thermique simplifié. Comparez ses prédictions à des mesures avant tout usage scientifique.':'Proposition à vérifier · aucune expérience, simulation ou test n’est déclaré comme exécuté.'}</div><pre class="textwrap">${esc(r.content)}</pre>${r.simulation?`<h3>Paramètres du calcul</h3><pre>${esc(JSON.stringify(r.simulation.parameters,null,2))}</pre><p>${r.simulation.series.length} points calculés · ${esc(r.simulation.equation)}</p>`:''}<h3>Sources</h3><p>${esc(r.sources.join(' · ')||'Aucune source sélectionnée ou vérifiée.')}</p>${r.citations?.length?`<h3>Extraits vérifiés des résumés</h3><ul>${r.citations.map(c=>`<li><strong>${esc(c.source_id)}</strong> : « ${esc(c.quote)} »</li>`).join('')}</ul>`:''}${r.review?`<h3>Relecture par ${esc(r.review.agent_name)}</h3><p>${r.review.verdict==='revise'?'Révision demandée':'Prêt pour validation humaine'}</p><p>Points forts : ${esc(r.review.strengths.join(' · '))}</p><p>À corriger : ${esc(r.review.issues.join(' · ')||'Aucun point signalé.')}</p><p>Contrôles requis : ${esc(r.review.required_checks.join(' · '))}</p>`:'<p class="hint">Relecture par un second agent indisponible.</p>'}<h3>Hypothèses</h3><ul>${r.assumptions.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><h3>Vérifications à réaliser</h3><ul>${r.checks.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><h3>Limites</h3><ul>${r.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>${button('Exporter en Markdown','research-export','download','secondary',`data-id="${r.id}"`)}${r.simulation?button('Exporter la série CSV','research-series','download','secondary',`data-id="${r.id}"`):''}`);return true;}
  if(action==='research-export'){await download('/projects/'+S.project.id+'/research/'+b.dataset.id+'/export','passage-recherche-'+b.dataset.id+'.md');return true;}
  if(action==='research-series'){await download('/projects/'+S.project.id+'/research/'+b.dataset.id+'/series.csv','passage-simulation-'+b.dataset.id+'.csv');return true;}
  if(action==='stop-mission'){await post('/projects/'+S.project.id+'/stop');toast('Arrêt demandé après l’appel en cours.');return true;}
  if(action==='approve'){const r=await post('/projects/'+S.project.id+'/approvals/'+b.dataset.id,{accept:b.dataset.accept==='true'});await reloadProject();renderView();if(r.id)followMission(r.id);return true;}
  if(action==='pipelex-status'){b.disabled=true;try{const result=await post('/projects/'+S.project.id+'/approvals/'+b.dataset.id+'/pipelex-status');await reloadProject();renderView();toast(result.cached?'Dernière lecture conservée · réessayez dans '+result.retry_in_seconds+' s.':'État et résultat Pipelex relus.');}finally{b.disabled=false;}return true;}
  if(action==='dust-recover'){b.disabled=true;try{const result=await post('/projects/'+S.project.id+'/approvals/'+b.dataset.id+'/dust-recover');await reloadProject();renderView();toast(result.notice,!result.found);}finally{b.disabled=false;}return true;}
  if(action==='dust-messages'){b.disabled=true;try{const result=await post('/projects/'+S.project.id+'/approvals/'+b.dataset.id+'/dust-messages');await reloadProject();renderView();toast(result.message_count===0?'Conversation Dust vide : aucun message confirmé.':'Conversation Dust relue.');}finally{b.disabled=false;}return true;}
  if(action==='voice'||action==='dictate'){
    if(S.liveVoice)await stopLiveVoice();
    if(S.voiceConversation)await stopVoiceConversation();
    if(S.recording)await stopRecording(true);else await startRecording(action==='dictate'?'problem':'chat-input');return true;
  }
  if(action==='mcp-research-export'){await download('/mcp/pipelex/research-method','passage-recherche-doctorale.mthds');return true;}
  if(action==='mcp-catalog'){const service=b.dataset.service;const el=$('#mcp-catalog-'+service);if(el)el.textContent='Lecture du catalogue…';try{const response=await api('/mcp/'+service+'/catalog');if(el)el.innerHTML=response.items.length?response.items.map(item=>`<div class="list-line textwrap"><div><strong>${esc(item.name)}</strong><p class="tiny muted">${esc(item.description)}</p></div></div>`).join(''):'<p class="hint">Aucun élément lisible dans la réponse du fournisseur.</p>';}catch(e){if(el)el.innerHTML=errorBox(e.message);}return true;}
  if(action==='mcp-connect'){const flow=await post('/mcp/'+b.dataset.service+'/connect');pollOAuth(flow.id);b.disabled=true;return true;}
  if(action==='mcp-disconnect'){await post('/mcp/'+b.dataset.service+'/disconnect');await loadPartners();return true;}
  if(action==='accounts'){const rows=await api('/auth/users');modal('Comptes de cette installation',rows.map(u=>`<form class="account-form" data-id="${u.id}"><p>${esc(u.name)} · ${esc(u.email)}</p><select name="role" aria-label="Rôle de ${esc(u.name)}">${['admin','lab','researcher','company'].map(r=>`<option ${u.role===r?'selected':''}>${r}</option>`).join('')}</select><button class="btn small" type="submit" ${u.id===S.user.id?'disabled':''}>Appliquer</button></form>`).join(''),'','medium');return true;}
  return false;
}
function chatgptConnectionHelp(){
  return `<details class="chatgpt-help" open><summary>Aide : connecter mon compte ChatGPT</summary>
    <ol>
      <li><strong>Ouvrir les paramètres ChatGPT.</strong> <a href="https://chatgpt.com/settings/security" target="_blank" rel="noopener noreferrer">Ouvrir « Sécurité et connexion »</a>. Utilisez le même compte ChatGPT que sur l’écran d’autorisation.</li>
      <li><strong>Activer le code d’appareil.</strong> Descendez tout en bas, dans <strong>« Sécurité des applications »</strong>, et activez <strong>« Activer la connexion par code d’appareil pour Codex, Excel, PowerPoint et Word »</strong>.</li>
      <li><strong>Revenir dans Passage.</strong> Cliquez sur « Connecter mon compte ChatGPT ». Si un code avait déjà été proposé avant l’activation, cliquez sur <strong>« Générer un nouveau code »</strong>.</li>
      <li><strong>Valider chez OpenAI.</strong> Ouvrez la page de connexion avec le bouton ci-dessous, saisissez le nouveau code et terminez la validation. Puis revenez ici et cliquez sur <strong>« Vérifier la connexion »</strong> : le statut doit afficher « Connecté ».</li>
    </ol>
    <p class="hint">La commande « codex login --device-auth » mentionnée par OpenAI est prise en charge par Passage. Vous n’avez rien à installer ni à lancer dans un terminal.</p>
    <details><summary>Je ne trouve pas l’option, ou mon code est refusé</summary>
      <p>Ouvrez ChatGPT dans le navigateur avec le lien ci-dessus. Vérifiez le compte sélectionné et faites défiler toute la page des paramètres de sécurité. Le libellé peut aussi apparaître en anglais : « Enable device code authentication ».</p>
      <p>Dans un espace professionnel ou universitaire géré, cette autorisation peut dépendre de l’administrateur de l’espace. Si l’option reste absente, demandez-lui d’autoriser la connexion par code pour Codex.</p>
      <p>Si le code est expiré ou si vous venez d’activer l’option, générez un nouveau code dans Passage et utilisez uniquement celui-ci. La connexion n’est terminée que lorsque Passage indique « Connecté ».</p>
    </details>
    <p class="hint"><a href="https://developers.openai.com/codex/auth/#preferred-device-code-authentication-beta" target="_blank" rel="noopener noreferrer">Documentation officielle OpenAI</a></p>
  </details>`;
}
function chatgptLoginHtml(login){
  if(!login)return '';
  const value=login.verificationUrl||login.authUrl||'';
  let url='';
  try{const parsed=new URL(value);if(parsed.protocol==='https:'&&['chatgpt.com','auth.openai.com'].includes(parsed.hostname))url=parsed.href;}catch{}
  if(!url)return '<p class="notice error">Lien de connexion inattendu. Relancez la connexion.</p>';
  if(login.type==='chatgptDeviceCode')return `<p>Ouvrez la page officielle puis saisissez ce code :</p><p><code class="login-code">${esc(login.userCode||'')}</code></p><a class="btn secondary" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Ouvrir la page de connexion</a><p class="hint">Si OpenAI demande d’activer la connexion par code d’appareil, ouvrez les paramètres de sécurité ChatGPT depuis son message, activez cette option, puis générez un nouveau code ici.</p>${button('Générer un nouveau code','chatgpt-renew-code',null,'secondary small')}<p class="hint">Après validation chez OpenAI, revenez cliquer sur « Vérifier la connexion ».</p>`;
  return `<a class="btn secondary" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Ouvrir la connexion ChatGPT</a><p class="hint">Revenez ensuite cliquer sur « Vérifier la connexion ». Si le retour local ne fonctionne pas, utilisez le code d’appareil.</p>`;
}
async function workspaceSubmit(f,data){
  if(await jinkoSubmit(f,data))return true;
  if(await teamSubmit(f,data))return true;
  if(f.id==='work-create-form'){
    const w=await post('/work/projects/'+S.project.id,Object.fromEntries(data));
    await reloadProject();renderView();workModal(w);return true;
  }
  if(f.id==='work-edit-form'){
    const w=await api('/work/tasks/'+f.dataset.id,{method:'PATCH',body:JSON.stringify(Object.fromEntries(data))});
    await reloadProject();renderView();workModal(w);return true;
  }
  if(f.id==='work-step-form'){
    const proof=String(data.get('proof')||''),separator=proof.indexOf(':');
    const w=await post('/work/tasks/'+f.dataset.id+'/steps',{
      index:Number(f.dataset.index),done:f.dataset.done==='true',
      note:String(data.get('note')||''),expected_revision:Number(f.dataset.revision),
      proof_kind:separator<0?'':proof.slice(0,separator),
      proof_id:separator<0?'':proof.slice(separator+1)});
    if(S.project)await reloadProject();S.workInbox=await api('/work/inbox');renderView();workModal(w);return true;
  }
  if(f.id==='work-worksheet-form'){
    const w=await api('/work/tasks/'+f.dataset.id,{method:'PUT',body:JSON.stringify({expected_revision:Number(f.dataset.revision),answers:Object.fromEntries(data),source_entry_id:f.dataset.sourceEntryId||''})});
    if(S.project)await reloadProject();renderView();workModal(w);return true;
  }
  if(f.id==='work-record-form'){
    const values=Object.fromEntries(data);
    const evidence=values.evidence||'';delete values.evidence;
    const evidence_entry_id=evidence.startsWith('entry:')?evidence.slice(6):'';
    const file_id=evidence.startsWith('file:')?evidence.slice(5):'';
    const recordId=f.dataset.recordId;
    const endpoint='/work/tasks/'+f.dataset.id+'/records'+(recordId?'/'+recordId:'');
    const body=recordId?{expected_revision:Number(f.dataset.revision),expected_version:Number(f.dataset.version),values,active:true,evidence_entry_id,file_id}:{expected_revision:Number(f.dataset.revision),values,source_entry_id:f.dataset.sourceEntryId||'',suggestion_index:Number(f.dataset.suggestionIndex),evidence_entry_id,file_id};
    const response=recordId?await api(endpoint,{method:'PUT',body:JSON.stringify(body)}):await post(endpoint,body);
    if(S.project)await reloadProject();renderView();workModal(response.task);return true;
  }
  if(f.id==='work-anchor-form'){
    const [source_type,source_id]=String(data.get('source')||'').split(':',2);
    const response=await post('/work/tasks/'+f.dataset.id+'/anchors',{
      expected_revision:Number(f.dataset.revision),source_type,source_id,
      quote:String(data.get('quote')||''),claim:String(data.get('claim')||''),
      source_entry_id:f.dataset.sourceEntryId||'',suggestion_index:Number(f.dataset.suggestionIndex)});
    if(S.project)await reloadProject();renderView();workModal(response.task);return true;
  }
  if(f.id==='work-linked-sources-form'){
    const w=await api('/work/tasks/'+f.dataset.id+'/linked-sources',{method:'PUT',body:JSON.stringify({expected_revision:Number(f.dataset.revision),source_task_ids:data.getAll('source_task_ids')})});
    if(S.project)await reloadProject();renderView();workModal(w);return true;
  }
  if(f.id==='work-entry-form'){
    const response=await post('/work/tasks/'+f.dataset.id+'/entries',{...Object.fromEntries(data),kind:f.dataset.kind});
    await reloadProject();renderView();workModal(response.task);return true;
  }
  if(f.id==='work-document-create-form'){
    const response=await post('/work/tasks/'+f.dataset.id+'/documents',Object.fromEntries(data));
    if(S.project)await reloadProject();renderView();workDocumentModal(response.task,response.document);return true;
  }
  if(f.id==='work-document-save-form'){
    const body={...Object.fromEntries(data),expected_version:Number(data.get('expected_version'))};
    const response=await api('/work/tasks/'+f.dataset.id+'/documents/'+f.dataset.documentId,{method:'PUT',body:JSON.stringify(body)});
    if(S.project)await reloadProject();renderView();workDocumentModal(response.task,response.document);return true;
  }
  if(f.id==='work-document-comment-form'){
    const body={...Object.fromEntries(data),version:Number(data.get('version'))};
    const response=await post('/work/tasks/'+f.dataset.id+'/documents/'+f.dataset.documentId+'/comments',body);
    workDocumentModal(await api('/work/tasks/'+f.dataset.id),response.document);return true;
  }
  if(f.id==='work-file-form'){
    const file=f.querySelector('input[type="file"]').files[0];
    if(!file||file.size>8*1024*1024)throw new Error('Choisissez un fichier de 8 Mo maximum.');
    const dataUrl=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(new Error('Lecture du fichier impossible.'));reader.readAsDataURL(file);});
    const response=await post('/work/tasks/'+f.dataset.id+'/files',{name:file.name,content_base64:String(dataUrl).split(',')[1]});
    if(S.project)await reloadProject();S.workInbox=await api('/work/inbox');renderView();workModal(response.task);return true;
  }
  if(f.id==='work-table-analysis-form'){
    const response=await post('/work/tasks/'+f.dataset.id+'/files/'+f.dataset.fileId+'/describe',{
      expected_revision:Number(data.get('expected_revision')),
      value_column:data.get('value_column'),group_column:data.get('group_column')||''});
    if(S.project)await reloadProject();S.workInbox=await api('/work/inbox');renderView();workModal(response.task);return true;
  }
  if(f.id==='work-delegate-form'){
    const response=await post('/work/tasks/'+f.dataset.id+'/delegate',{
      agent_id:data.get('agent_id'),instruction:data.get('instruction')||'',
      expected_revision:Number(data.get('expected_revision')),
      focus_step:Number(data.get('focus_step'))});
    await reloadProject();renderView();workModal(response.task);followWorkRun(response.run.id,response.task.id);return true;
  }
  if(f.id==='work-rework-form'){
    const response=await post('/work/tasks/'+f.dataset.id+'/delegate',{
      agent_id:data.get('agent_id'),instruction:data.get('instruction')||'',
      source_entry_id:f.dataset.entryId,expected_revision:Number(f.dataset.revision),
      focus_step:Number(data.get('focus_step'))});
    await reloadProject();renderView();workModal(response.task);followWorkRun(response.run.id,response.task.id);return true;
  }
  if(f.id==='work-diagram-create-form'){
    const item=await post('/work/tasks/'+f.dataset.id+'/diagrams',{title:data.get('title')});
    const w=await api('/work/tasks/'+f.dataset.id);if(S.project)await reloadProject();renderView();
    await workspaceClick('work-diagram-open',{dataset:{id:w.id,diagramId:item.id}});return true;
  }
  if(f.id==='work-diagram-formalize-form'){
    const run=await post('/work/tasks/'+f.dataset.id+'/diagrams/'+f.dataset.diagramId+'/formalize',{
      agent_id:data.get('agent_id'),target:data.get('target'),expected_version:Number(f.dataset.version)});
    workModal(await api('/work/tasks/'+f.dataset.id));followWorkRun(run.id,f.dataset.id);return true;
  }
  if(f.id==='work-checkpoint-form'){
    const evidence=String(data.get('evidence')||'');
    const isFile=evidence.startsWith('file:');
    const response=await post('/work/tasks/'+f.dataset.id+'/checkpoints',{
      code:f.dataset.code,statement:data.get('statement'),occurred_at:data.get('occurred_at'),
      evidence_entry_id:isFile?'':evidence.slice(6),file_id:isFile?evidence.slice(5):''});
    if(S.project)await reloadProject();S.workInbox=await api('/work/inbox');renderView();workModal(response.task);return true;
  }
  if(f.id==='work-review-form'){
    const response=await post('/work/tasks/'+f.dataset.id+'/complete',Object.fromEntries(data));
    await reloadProject();renderView();workModal(response.task);return true;
  }
  if(f.id==='work-share-form'){
    const w=await post('/work/tasks/'+f.dataset.id+'/share',Object.fromEntries(data));
    await reloadProject();renderView();workModal(w);return true;
  }
  if(f.id==='work-peer-review-form'){
    const response=await post('/work/tasks/'+f.dataset.id+'/review',Object.fromEntries(data));
    S.workInbox=await api('/work/inbox');if(S.project)await reloadProject();renderView();workModal(response.task);return true;
  }
  if(f.id==='login-form'){
    try{const result=await post('/auth/'+(f.dataset.register==='true'?'register':'login'),Object.fromEntries(data));S.user=result.user;S.csrf=result.csrf;await boot();}catch(e){$('#auth-error').innerHTML=errorBox(e.message);}return true;
  }
  if(f.id==='voice-account-form'){
    await api('/voice/account',{method:'PUT',body:JSON.stringify({api_key:data.get('voice-api-key'),voice_id:data.get('voice-id')})});
    await loadVoiceAccount();toast('Voix Gradium personnelle configurée.');return true;
  }
  if(f.id==='project-form'){
    const body=Object.fromEntries(data);
    const choice=body.brain_choice;delete body.brain_choice;
    body.brain_provider=choice==='agent'?'agent':'codex';
    body.brain_model=choice==='agent'?'':choice.slice(6);
    S.project=await post('/projects',body);rememberProject();closeModal();await reloadProject();S.view='chat';shell();return true;
  }
  if(f.id==='coordinator-form'){if(S.liveVoice)await stopLiveVoice();await api('/projects/'+S.project.id+'/coordinator',{method:'PATCH',body:JSON.stringify({coordinator_id:data.get('coordinator_id')})});await reloadProject();closeModal();renderView();toast('Coordinateur du projet mis à jour.');return true;}
  if(f.id==='project-team-form'){
    const ids=[...new Set([S.project.coordinator_id,...data.getAll('agent_ids')])];
    await api('/projects/'+S.project.id+'/team',{method:'PATCH',body:JSON.stringify({agent_ids:ids})});
    await reloadProject();closeModal();renderView();toast('Équipe du projet mise à jour.');return true;
  }
  if(f.id==='project-brain-form'){
    const choice=data.get('brain_choice');
    const body=choice==='agent'?{provider:'agent',model:''}:{provider:'codex',model:choice.slice(6)};
    if(S.liveVoice)await stopLiveVoice();
    await api('/projects/'+S.project.id+'/brain',{method:'PATCH',body:JSON.stringify(body)});
    await reloadProject();closeModal();renderView();toast('Cerveau du projet mis à jour.');return true;
  }
  if(f.id==='project-sources-form'){await api('/projects/'+S.project.id+'/sources',{method:'PATCH',body:JSON.stringify({source_ids:data.getAll('source_ids')})});await reloadProject();closeModal();renderView();toast('Sources du projet enregistrées.');return true;}
  if(f.id==='chat-form'){if(S.liveVoice)await stopLiveVoice();if(S.voiceConversation)await stopVoiceConversation();await sendDialogue(data.get('message'));return true;}
  if(f.classList.contains('mcp-grants')){await api('/mcp/'+f.dataset.service+'/tools',{method:'PUT',body:JSON.stringify({allowed_tools:data.getAll('tools')})});toast('Outils autorisés mis à jour.');return true;}
  if(f.classList.contains('account-form')){await api('/auth/users/'+f.dataset.id,{method:'PATCH',body:JSON.stringify(Object.fromEntries(data))});toast('Rôle enregistré.');return true;}
  return false;
}
async function followWorkRun(runId,workId){
  try{
    const run=await api('/runs/'+runId);
    if(['queued','running'].includes(run.status)){setTimeout(()=>followWorkRun(runId,workId),2500);return;}
    if(S.project?.id===run.project_id){await reloadProject();renderView();}
    if(run.status==='succeeded')toast('Proposition de l’agent prête à relire dans la tâche.');
    else toast('L’agent n’a pas terminé : '+(run.error||run.status),true);
  }catch(e){toast(e.message,true);}
}
document.addEventListener('input',event=>{
  if(event.target.id!=='source-filter')return;
  const query=event.target.value.trim().toLowerCase();
  document.querySelectorAll('.source-choice').forEach(row=>{row.hidden=!row.dataset.search.includes(query);});
});
async function loadPartners(){
  const el=$('#partners-content');if(!el)return;
  try{const services=await api('/mcp/services');el.innerHTML=`<div class="sectionhead"><h2>Dust & Pipelex · MCP officiel</h2></div><p class="muted">Connectez votre compte, puis choisissez les outils que le coordinateur pourra utiliser.</p><div id="oauth-status" role="status"></div><div class="grid equal">${services.map(s=>`<section class="card"><h3>${esc(s.name)}</h3>${badge(s.connected?'Connecté':'Non connecté',s.connected?'dark':'gray')}<p class="tiny muted">${esc(s.url)}</p><div class="actions">${button(s.connected?'Actualiser les outils':'Connecter avec OAuth','mcp-connect','link','secondary small',`data-service="${s.service}"`)}${s.connected?button('Déconnecter','mcp-disconnect',null,'ghost small',`data-service="${s.service}"`):''}${s.connected&&s.allowed_tools.includes(s.service==='pipelex'?'pipelex_list_methods':'list_agents')?button(s.service==='pipelex'?'Voir les méthodes':'Voir les agents','mcp-catalog','search','ghost small',`data-service="${s.service}"`):''}${s.service==='pipelex'?button('Exporter méthode doctorant','mcp-research-export','download','ghost small'):''}</div><div id="mcp-catalog-${esc(s.service)}"></div>${s.connected?`<form class="mcp-grants" data-service="${s.service}"><div class="tool-grants">${s.tools.map(t=>`<label class="check"><input type="checkbox" name="tools" value="${esc(t.name)}" ${s.allowed_tools.includes(t.name)?'checked':''}><span><strong>${esc(t.name)}</strong><small>${esc((t.description||'').slice(0,200))}</small></span></label>`).join('')}</div><button type="submit" class="btn small">Autoriser la sélection</button></form>`:''}</section>`).join('')}</div>`;}catch(e){el.innerHTML=errorBox(e.message);}
}
async function loadBrainAccounts(){
  const el=$('#brain-accounts');if(!el)return;
  try{const c=await api('/brains/chatgpt/status');
    const windows=c.limits?.rateLimitsByLimitId||{codex:c.limits?.rateLimits};
    const limits=Object.entries(windows).filter(([,v])=>v).map(([name,v])=>[v.primary,v.secondary].filter(Boolean).map(w=>`<p class="tiny">${esc(name)} · ${Math.max(0,100-w.usedPercent)} % disponibles sur ${w.windowDurationMins} minutes${w.resetsAt?' · renouvellement '+fmt(w.resetsAt*1000):''}</p>`).join('')).join('');
    el.innerHTML=`<section class="card"><h3>Mon compte ChatGPT</h3>${badge(c.connected?'Connecté':'Non connecté',c.connected?'dark':'gray')}<p>Utilise l’accès Codex de votre compte ChatGPT. Les modèles et limites dépendent de votre offre. La clé API OpenAI utilise une facturation distincte.</p>${c.account?`<p>${esc(c.account.email||'')} · ${esc(c.account.planType||'')}</p>`:''}${limits}${!c.connected?chatgptConnectionHelp():''}<div class="actions">${c.installed&&!c.connected?(c.browser_login_available!==false?button('Connecter par navigateur','chatgpt-connect','link','secondary small'):'')+button(c.browser_login_available===false?'Connecter mon compte ChatGPT':'Utiliser un code','chatgpt-connect-device','link','secondary small'):''}${!c.installed?'<p>La connexion ChatGPT est indisponible sur ce serveur. Contactez son administrateur.</p>':''}${button('Vérifier la connexion','chatgpt-refresh',null,'ghost small')}${c.connected?button('Déconnecter','chatgpt-disconnect',null,'ghost small'):''}</div><div id="chatgpt-login">${chatgptLoginHtml(c.pending_login)}</div><p class="hint">Connexion personnelle, propre à votre compte Passage.${c.persistent_connection?' Elle est conservée chiffrée pour retrouver votre accès après un redémarrage du serveur. Déconnecter supprime cette sauvegarde.':''}${c.browser_login_available===false?' Validez le code sur la page officielle OpenAI ; si nécessaire, activez la connexion par code dans les paramètres de sécurité de ChatGPT.':''}</p></section>`;
  }catch(e){el.innerHTML=errorBox(e.message);}
}
async function loadVoiceAccount(){
  const el=$('#voice-account');if(!el)return;
  try{
    const c=await api('/voice/account');
    el.innerHTML=`<section class="card"><div class="status-row"><h3>Ma voix · Gradium</h3>${badge(c.personal_configured?'Clé personnelle':c.configured?'Voix de démonstration active':'À configurer',c.configured?'dark':'gray')}</div>${c.configured&&!c.personal_configured?'<p>La voix est prête : aucune clé à saisir pour tester. Les appels utilisent le quota Gradium de Passage.</p>':''}<details ${c.configured?'':'open'}><summary>Utiliser ma propre clé Gradium</summary><p>Votre clé personnelle est conservée chiffrée et utilisée uniquement pour votre transcription et la lecture de vos réponses. Si vous la retirez, Passage reprend la clé de l’installation lorsqu’elle existe.</p><form id="voice-account-form"><div class="field"><label for="voice-api-key">Ma clé API Gradium</label><input id="voice-api-key" name="voice-api-key" type="password" autocomplete="new-password" placeholder="${c.personal_configured?'Déjà configurée — laisser vide pour conserver':'Saisir une clé personnelle'}"><div class="hint">La clé n’est jamais renvoyée à l’interface.</div></div>${textField('voice-id','Identifiant de voix',c.voice_id||'','text',true)}<div class="actions"><button class="btn" type="submit">${icon('check')}Enregistrer ma voix</button>${c.personal_configured?button('Retirer ma clé','voice-account-remove',null,'secondary'):''}</div></form></details></section>`;
  }catch(e){el.innerHTML=errorBox(e.message);}
}
async function pollOAuth(id){
  try{const f=await api('/mcp/flows/'+id);const el=$('#oauth-status');if(!el)return;
    if(f.status==='connected'){await loadPartners();toast('Connexion MCP établie. Choisissez les outils autorisés.');return;}
    if(f.status==='failed'){el.innerHTML=errorBox(f.error);return;}
    let link='';if(f.authorization_url){const u=new URL(f.authorization_url);if(u.protocol==='https:')link=`<a class="btn" href="${esc(u.href)}" target="_blank" rel="noopener noreferrer">Autoriser dans ${esc(f.service)}</a>`;}
    el.innerHTML=`<div class="notice info">${link||'Préparation de la connexion OAuth…'}<p>Revenez dans cette fenêtre après la connexion.</p></div>`;
    oauthTimer=setTimeout(()=>pollOAuth(id),1500);
  }catch(e){toast(e.message,true);}
}
document.addEventListener('change',async e=>{
  try{if(e.target.id==='project-select'||e.target.id==='work-project-select'){await stopLiveVoice();await stopVoiceConversation();await stopRecording(false);stopPlayingAudio();clearTimeout(missionTimer);S.project=e.target.value?await api('/projects/'+e.target.value):null;rememberProject();renderView();resumeMission();}
    if(e.target.id==='voice-reply')S.voiceReply=e.target.checked;
    if(e.target.id==='voice-send')S.voiceSend=e.target.checked;
  }catch(err){toast(err.message,true);}
});

function syncVoiceControls(status=''){
  const button=$('#voice-conversation-button');
  if(button)button.setAttribute('aria-pressed',String(Boolean(S.liveVoice)));
  if($('#voice-reply'))$('#voice-reply').checked=S.voiceReply;
  if($('#voice-send'))$('#voice-send').checked=S.voiceSend;
  if(status&&$('#voice-status'))$('#voice-status').textContent=status;
}
async function stopVoiceConversation(){
  if(!S.voiceConversation)return;
  S.voiceConversation=false;S.voiceEpoch++;S.voicePendingRun=null;
  if(S.recording?.auto)await stopRecording(false);
  stopPlayingAudio();S.voiceReply=false;S.voiceSend=false;syncVoiceControls('Conversation arrêtée. Le micro est fermé.');
}
async function startVoiceConversation(){
  const status=await api('/voice/status');if(!status.configured)throw new Error('Ajoutez votre clé Gradium dans Connexions pour parler à Passage.');
  if(S.recording)await stopRecording(false);
  S.voiceConversation=true;S.voiceEpoch++;S.voiceReply=true;S.voiceSend=true;
  syncVoiceControls('Ouverture du microphone…');
  try{await startRecording('chat-input',true);}
  catch(e){await stopVoiceConversation();throw e;}
}
async function speakAndResume(text,epoch){
  if(!S.voiceConversation||epoch!==S.voiceEpoch)return;
  syncVoiceControls('Passage vous répond…');
  await speakReply(text,true,epoch);
  if(S.voiceConversation&&epoch===S.voiceEpoch&&S.view==='chat'&&!S.recording){
    try{await startRecording('chat-input',true);}catch(e){await stopVoiceConversation();toast(e.message,true);}
  }
}
async function startRecording(target,auto=false){
  const status=await api('/voice/status');if(!status.configured)throw new Error('Ajoutez votre clé Gradium dans Connexions pour parler à Passage.');
  if(!navigator.mediaDevices?.getUserMedia)throw new Error('Ce navigateur ne permet pas l’accès au microphone.');
  stopPlayingAudio();
  const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true},video:false});
  if(auto&&!S.voiceConversation){stream.getTracks().forEach(t=>t.stop());return;}
  let context;
  try{
    context=new AudioContext({sampleRate:24000});
    await context.audioWorklet.addModule('/static/recorder.js');
    if(auto&&!S.voiceConversation){stream.getTracks().forEach(t=>t.stop());await context.close();return;}
    const source=context.createMediaStreamSource(stream),recorder=new AudioWorkletNode(context,'passage-recorder');
    const chunks=[];
    source.connect(recorder);recorder.connect(context.destination);
    const r={stream,context,source,recorder,chunks,target,auto,epoch:S.voiceEpoch,projectId:S.project?.id||null,speechMs:0,lastVoiceAt:0,heardSpeech:false,startedAt:performance.now()};
    S.recording=r;
    recorder.port.onmessage=e=>{
      if(S.recording!==r)return;
      const sample=new Float32Array(e.data);chunks.push(sample);
      if(!auto)return;
      let sum=0;for(let i=0;i<sample.length;i++)sum+=sample[i]*sample[i];
      const loud=Math.sqrt(sum/sample.length)>0.015,now=performance.now();
      if(loud){r.speechMs+=sample.length/context.sampleRate*1000;r.lastVoiceAt=now;if(r.speechMs>=180)r.heardSpeech=true;}
      else if(!r.heardSpeech)r.speechMs=0;
      if(r.heardSpeech&&now-r.lastVoiceAt>1100){stopRecording(true).catch(async err=>{await stopVoiceConversation();toast(err.message,true);});}
    };
    r.timeout=setTimeout(()=>{
      if(auto)stopVoiceConversation().catch(e=>toast(e.message,true));
      else stopRecording(true).catch(e=>toast(e.message,true));
    },59000);
    if($('#voice-button'))$('#voice-button').textContent='Terminer';
    syncVoiceControls(auto?'Je vous écoute. Parlez naturellement ; une pause termine votre phrase.':'Micro ouvert · parlez maintenant (60 secondes maximum).');
    if(!auto)toast('Micro ouvert. Appuyez de nouveau pour terminer.');
  }catch(e){stream.getTracks().forEach(t=>t.stop());if(context&&context.state!=='closed')await context.close();throw e;}
}
function wav(chunks,rate){
  const total=chunks.reduce((n,x)=>n+x.length,0),samples=new Float32Array(total);let offset=0;for(const chunk of chunks){samples.set(chunk,offset);offset+=chunk.length;}
  const size=Math.floor(total*24000/rate),buffer=new ArrayBuffer(44+size*2),v=new DataView(buffer);
  const str=(at,text)=>[...text].forEach((c,i)=>v.setUint8(at+i,c.charCodeAt(0)));
  str(0,'RIFF');v.setUint32(4,36+size*2,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,24000,true);v.setUint32(28,48000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);str(36,'data');v.setUint32(40,size*2,true);
  for(let i=0;i<size;i++){const sample=Math.max(-1,Math.min(1,samples[Math.min(total-1,Math.floor(i*rate/24000))]||0));v.setInt16(44+i*2,sample<0?sample*32768:sample*32767,true);}
  return buffer;
}
async function stopRecording(transcribe){
  const r=S.recording;if(!r)return;S.recording=null;clearTimeout(r.timeout);
  r.stream.getTracks().forEach(t=>t.stop());r.source.disconnect();r.recorder.disconnect();const rate=r.context.sampleRate;await r.context.close();
  if($('#voice-button'))$('#voice-button').textContent='Parler';
  syncVoiceControls(transcribe?'Transcription Gradium en cours…':'Micro fermé.');
  if(!transcribe)return;
  const targetInput=document.getElementById(r.target);
  const response=await fetch('/api/voice/transcribe',{method:'POST',headers:{'Content-Type':'audio/wav','X-Passage-CSRF':S.csrf},body:wav(r.chunks,rate)});
  const data=await response.json();if(!response.ok)throw new Error(data.detail);
  if(r.auto&&(!S.voiceConversation||r.epoch!==S.voiceEpoch))return;
  if((S.project?.id||null)!==r.projectId||document.getElementById(r.target)!==targetInput){
    toast('Projet ou écran changé pendant la transcription. La commande vocale n’a pas été envoyée.');return;
  }
  const input=targetInput;if(input){input.value=data.text;input.focus();}
  if(r.auto){
    if(!data.text?.trim()){await startRecording('chat-input',true);return;}
    syncVoiceControls('Message compris. Passage prépare sa réponse…');
    try{await sendDialogue(data.text,r.epoch);}
    catch(e){await stopVoiceConversation();throw e;}
    return;
  }
  if($('#voice-send')?.checked&&r.target==='chat-input'&&input){
    await sendDialogue(data.text);
    toast('Commande vocale envoyée à l’équipe.');return;
  }
  if($('#voice-status'))$('#voice-status').textContent='Transcription Gradium reçue. Vérifiez votre commande, puis envoyez-la à l’équipe.';
  toast('Commande transcrite. Elle est prête à être envoyée.');
}
async function speakReply(text,waitForEnd=false,epoch=null){
  const plain=String(text||'').replace(/[#*`]/g,'').replace(/\s+/g,' ').trim();
  const spoken=plain.length>1200?plain.slice(0,1100).replace(/\s+\S*$/,'')+'… La suite est affichée dans le chat.':plain;
  try{const response=await fetch('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json','X-Passage-CSRF':S.csrf},body:JSON.stringify({text:spoken})});if(!response.ok)throw new Error((await response.json()).detail);
    if(epoch!==null&&(!S.voiceConversation||epoch!==S.voiceEpoch))return;
    stopPlayingAudio();playingAudioUrl=URL.createObjectURL(await response.blob());playingAudio=new Audio(playingAudioUrl);
    const finished=new Promise(resolve=>{playingResolve=resolve;playingAudio.onended=stopPlayingAudio;});
    await playingAudio.play();if(waitForEnd)await finished;
  }catch(e){stopPlayingAudio();toast(e.message,true);}
}
window.addEventListener('beforeunload',()=>{S.recording?.stream.getTracks().forEach(t=>t.stop());stopPlayingAudio();});
boot();
