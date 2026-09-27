'use strict';
// Guided creation stays in the existing editor: the saved agent is the source of truth.
const passageBaseAgentForm = agentForm;
function creatorForm(a, d) {
  if (!a.creator_version) return '';
  const fields = [
    ['trigger', 'Déclencheur · quelle demande met cet agent au travail ?', 2],
    ['reads', 'Ce qu’il lit · sources et données autorisées', 2],
    ['boundaries', 'Ce que l’humain décide', 2],
    ['checkpoint', 'Point où un humain vérifie et décide', 2],
    ['deliverables', 'Livrable attendu et critère de réussite', 2],
    ['process', 'Processus détaillé · si le skill ne suffit pas', 4],
    ['workflow', 'Workflow déclenché par un événement · facultatif', 4],
    ['experience', 'Erreurs et corrections confirmées · facultatif au départ', 3],
  ];
  const status = !a.id
    ? '<p class="tiny">Complétez les décisions de cadrage, puis lancez le contrôle.</p>'
    : d?.control?.length
    ? `<ul class="tiny muted">${d.control.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`
    : '<p class="tiny">Définition complète. Tester sur un cas réel avant de la confier à un projet.</p>';
  const specialties = a.role==='research_task'
    ? `<h3>Tâches confiées à cet agent</h3><p class="hint">Choisissez les tâches R1–R3 qu'il saura traiter. Plusieurs agents spécialisés peuvent être actifs dans la même équipe.</p><div class="grid equal">${(S.workCatalog||[]).map(t=>`<label class="check"><input type="checkbox" name="work_specialties" value="${esc(t.id)}" ${(a.work_specialties||[]).includes(t.id)?'checked':''}>${esc(t.title)} · ${esc(t.persona)}</label>`).join('')}</div><label class="check"><input type="checkbox" name="tools" value="work.read" ${(a.tools||[]).includes('work.read')?'checked':''}>Lire les pièces autorisées de la tâche</label>`
    : '';
  return `<input type="hidden" name="creator_version" value="${esc(a.creator_version)}">
    <section class="card editor-section"><h3>Super Skill Creator · cadrage & pièces</h3>
      <p class="hint">Méthode OSCAR AI V4 adaptée à Passage. Les réponses manquantes restent visibles ; enregistrez un brouillon inactif pour y revenir.</p>
      ${specialties}
      ${fields.slice(0, 5).map(([key, label, rows]) => textArea(key, label, a[key] || '', rows)).join('')}
      <h3>Pièces complémentaires</h3>
      ${fields.slice(5).map(([key, label, rows]) => textArea(key, label, a[key] || '', rows)).join('')}
      <p class="hint">Skill, contexte et mémoire se remplissent dans « Harnais » ci-dessus. Les outils accordés sont des capacités réelles, choisies dans « Boîte à outils ».</p>
      <div class="actions">${button('Contrôler le brouillon', 'creator-check', 'check', 'secondary small')}</div>
      <div id="creator-control" class="notice info">${status}</div>
    </section>`;
}
agentForm = function(a, d, connectors) {
  let base=passageBaseAgentForm(a,d,connectors);
  if(a.role!=='research_task')base=base.replace('<div class="divider"></div><label>Connecteurs MCP accordés</label>',
    `<label class="check"><input type="checkbox" name="tools" value="work.read" ${(a.tools||[]).includes('work.read')?'checked':''}>Lire les travaux autorisés</label><div class="divider"></div><label>Connecteurs MCP accordés</label>`);
  if(a.provider!=='ollama'){
    base=base.replace(/<option value="ollama"[^>]*>Ollama · modèle local<\/option>/,'');
    base=base.replace('<datalist id="brain-models"></datalist>',
      `${button('Ajouter un modèle local', 'enable-local-provider', null, 'ghost small')}<datalist id="brain-models"></datalist>`);
  }
  return base.replace('</form>', creatorForm(a,d)+'</form>')
    .replace('L’activation remplace l’agent actuellement actif de ce rôle.',
      a.role==='research_task'?'Plusieurs agents de recherche peuvent rester actifs et être affectés à un projet.':'L’activation remplace l’agent actuellement actif de ce rôle.');
};
document.addEventListener('click', event => {
  const button=event.target.closest('[data-action="enable-local-provider"]');
  if(!button)return;
  const select=$('#provider');
  if(!select)return;
  select.add(new Option('Ollama · modèle local', 'ollama'));
  select.value='ollama';
  button.remove();
});
forge = async function(role) {
  if(role==='research_task')S.workCatalog=await api('/work/catalog');
  const draft = await api('/agents/creator/blueprint/' + role);
  const connections = await api('/connections');
  S.editAgent = draft.agent;
  const steps = `<details open><summary>Les six étapes de création · ${esc(draft.version)}</summary><ol>${draft.steps.map(x => `<li>${esc(x)}</li>`).join('')}</ol></details>`;
  modal('Créer un agent · ' + roleNames[role], steps + agentForm(draft.agent, {control: []}, connections.connectors),
    `<div class="actions">${button('Fermer', 'close', null, 'secondary')}</div><button class="btn" type="submit" form="agent-form">${icon('check')}Enregistrer le brouillon</button>`);
};
const passageBaseTestAgent = testAgent;
testAgent = async function(id) {
  const agent=S.data.agents.find(a=>a.id===id);
  if(agent?.role!=='research_task')return passageBaseTestAgent(id);
  S.testResearchAgentId=id;
  if(!S.project)return modal('Tester · '+agent.name,
    '<p>Choisissez d’abord un projet et ouvrez une tâche de recherche.</p>'+button('Ouvrir les projets','nav','arrow','secondary','data-view="chat"'));
  if(!S.project.agent_ids.includes(id))return modal('Tester · '+agent.name,
    '<p>Ajoutez cet agent à l’équipe du projet avant de lui confier un travail.</p>'+button('Composer l’équipe','project-team','user','secondary'));
  const tasks=(S.project.work_items||[]).filter(w=>(agent.work_specialties||[]).includes(w.type_id)&&w.status!=='delegated');
  modal('Tester · '+agent.name,tasks.length
    ? `<form id="research-agent-test-form"><label for="research-agent-task">Tâche réelle du projet</label><select id="research-agent-task" name="work_id">${tasks.map(w=>`<option value="${esc(w.id)}">${esc(w.title)}</option>`).join('')}</select>${textArea('instruction','Consigne de test pour cet agent','',3)}<p class="hint">Le brouillon sera conservé dans cette tâche pour contrôle humain.</p><button class="btn" type="submit">Lancer sur cette tâche</button></form>`
    : '<p>Aucune tâche de ce projet ne correspond aux spécialités de cet agent.</p>'+button('Ouvrir les travaux','nav','arrow','secondary','data-view="work"'),'','medium');
};
document.addEventListener('click', async event => {
  const button = event.target.closest('[data-action="creator-check"]');
  if (!button) return;
  const form = $('#agent-form');
  if (!form) return;
  button.disabled = true;
  try {
    const data = new FormData(form);
    const body = Object.fromEntries(data);
    body.active = data.has('active');
    body.max_steps = Number(data.get('max_steps'));
    body.tools = data.getAll('tools');
    body.work_specialties = data.getAll('work_specialties');
    body.connector_ids = data.getAll('connector_ids');
    const result = await post('/agents/creator/check', body);
    $('#creator-control').innerHTML = result.issues.length
      ? `<strong>${result.issues.length} point(s) à compléter avant activation</strong><ul class="tiny">${result.issues.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`
      : '<strong>Définition complète.</strong> Enregistrez puis testez cet agent sur un cas réel.';
  } catch (error) {
    $('#creator-control').innerHTML = errorBox(error.message);
  } finally {
    button.disabled = false;
  }
});
document.addEventListener('submit', async event => {
  if(event.target.id!=='research-agent-test-form')return;
  event.preventDefault();
  const form=event.target;
  const workId=new FormData(form).get('work_id');
  const id=S.testResearchAgentId;
  const submit=form.querySelector('[type=submit]');
  if(submit)submit.disabled=true;
  try{
    const result=await post('/work/tasks/'+workId+'/delegate',{agent_id:id,instruction:new FormData(form).get('instruction')||''});
    await reloadProject();closeModal();S.view='work';renderView();
    followWorkRun(result.run.id,workId);
  }catch(error){if($('#modal-error'))$('#modal-error').innerHTML=errorBox(error.message);if(submit)submit.disabled=false;}
});
