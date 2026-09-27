'use strict';
async function loadJinkoAccount(){
  const el=$('#jinko-account');if(!el)return;
  try{
    const c=await api('/jinko/account');
    el.innerHTML=`<section class="card"><div class="status-row"><h3>Mon projet Jinkō</h3>${badge(c.configured?'Accès enregistré':'À connecter',c.configured?'dark':'gray')}</div>
      <p>Reliez votre projet de modélisation et d’essais in silico. Un agent auquel vous accordez Jinkō peut consulter ses modèles, diagnostics et résultats existants avec le SDK officiel. Les données consultées sont transmises au cerveau choisi pour cet agent.</p>
      <form id="jinko-account-form"><div class="field"><label for="jinko-api-key">Clé API Jinkō personnelle</label><input id="jinko-api-key" name="api_key" type="password" autocomplete="new-password" placeholder="${c.configured?'Déjà configurée — laisser vide pour conserver':'Saisir la clé de votre projet'}"></div>
      ${textField('project_id','Identifiant du projet Jinkō',c.project_id,'text',true)}
      <p class="hint">Clé chiffrée, propre à votre compte. Ces outils effectuent des lectures ; ils ne lancent ni ne modifient un essai.</p>
      <div class="actions"><button class="btn" type="submit">Vérifier et enregistrer</button>${c.configured?button('Retirer cet accès','jinko-disconnect',null,'secondary'):''}</div></form>
      ${c.configured?`<p class="hint">Dernière vérification : ${fmt(c.checked_at)}.</p><div class="actions">${button('Voir les modèles','jinko-models','search','secondary')}${button('Créer mon agent Jinkō','jinko-create-agent','spark','secondary')}</div><p class="hint">L’agent utilise votre compte ChatGPT. ${S.project?'Il sera ajouté au projet « '+esc(S.project.name)+' ».':'Vous pourrez ensuite l’ajouter à un projet.'}</p><div id="jinko-catalog"></div>`:''}</section>`;
  }catch(e){el.innerHTML=errorBox(e.message);}
}
async function jinkoAction(action,b){
  if(!action.startsWith('jinko-'))return false;
  b.disabled=true;
  try{
    if(action==='jinko-disconnect'){
      await api('/jinko/account',{method:'DELETE'});await loadJinkoAccount();toast('Accès Jinkō retiré.');
    }else if(action==='jinko-models'){
      const r=await post('/jinko/read',{operation:'models',query:'',sid:'',revision:null,explanation:'Catalogue demandé par l’utilisateur.'});
      $('#jinko-catalog').innerHTML=`<h4>Modèles du projet</h4>${r.items.length?r.items.map(item=>`<p>${esc(item.name)} <small>${esc(item.sid)}</small></p>`).join(''):'<p>Aucun modèle trouvé.</p>'}${r.has_more?'<p class="hint">20 premiers modèles ; l’agent peut chercher un nom précis.</p>':''}`;
    }else if(action==='jinko-create-agent'){
      const r=await post('/jinko/agent',{project_id:S.project?.id||''});
      await refresh();if(r.project_id)await reloadProject();
      toast(r.status==='reused'?'Votre agent Jinkō existant est disponible.':'Agent Jinkō créé avec votre compte ChatGPT et les lectures SDK.');
    }
  }finally{b.disabled=false;}
  return true;
}
async function jinkoSubmit(f,data){
  if(f.id!=='jinko-account-form')return false;
  await api('/jinko/account',{method:'PUT',body:JSON.stringify(Object.fromEntries(data))});
  await loadJinkoAccount();toast('Accès au projet Jinkō vérifié et conservé.');return true;
}
