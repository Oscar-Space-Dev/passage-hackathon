'use strict';
const teamKinds={lab:'Laboratoire',researcher:'Collectif de recherche',company:'Entreprise'};
function captureTeamInvite(){
  const token=new URLSearchParams(location.hash.slice(1)).get('team-invite');
  if(!token)return false;
  sessionStorage.setItem('passage-team-invite',token);
  history.replaceState(null,'',location.pathname+location.search);
  return true;
}
captureTeamInvite();
window.addEventListener('hashchange',()=>{if(captureTeamInvite())showTeamInvite();});
function teamsPage(){
  return heading('Collaborer','Mes équipes','Créez une équipe et invitez ses membres. Partagez ensuite les tâches choisies depuis leur dossier.',button('Créer une équipe','team-new','plus'))+
    '<div class="notice info">Rejoindre une équipe donne accès à son annuaire. Vos projets, conversations et connexions restent personnels. Chaque tâche demande un partage explicite.</div><div id="teams-list">Chargement…</div>';
}
async function loadTeams(){
  const target=$('#teams-list');if(!target)return;
  try{
    const rows=await api('/teams');S.teams=rows;
    target.innerHTML=rows.length?rows.map(team=>`<section class="card"><div class="status-row"><h3>${esc(team.name)}</h3>${badge(teamKinds[team.kind])}</div>
      ${team.members.map(member=>`<div class="team-row"><div><strong>${esc(member.name)}</strong><small>${esc(member.email)}${member.id===team.owner_id?' · responsable':''}</small></div>${member.id!==team.owner_id&&(team.can_manage||member.id===S.user.id)?button(member.id===S.user.id?'Quitter':'Retirer','team-member-remove',null,'ghost small',`data-id="${esc(team.id)}" data-user-id="${esc(member.id)}"`):''}</div>`).join('')}
      ${team.can_manage?`${button('Inviter une personne','team-invite','user','secondary',`data-id="${esc(team.id)}"`)}${(team.invitations||[]).filter(invite=>invite.status==='pending').map(invite=>`<p class="tiny">${esc(invite.email)} · invitation en attente ${button('Révoquer','team-invite-revoke',null,'ghost small',`data-id="${esc(team.id)}" data-invite-id="${esc(invite.id)}"`)}</p>`).join('')}`:''}
      <p class="hint">Les accès déjà accordés à une tâche se gèrent dans cette tâche, indépendamment de l’appartenance à l’équipe.</p></section>`).join(''):empty('Créez votre première équipe ou ouvrez un lien d’invitation.','user');
  }catch(e){target.innerHTML=errorBox(e.message);}
}
async function showTeamInvite(){
  const token=sessionStorage.getItem('passage-team-invite');if(!token||!S.user)return;
  try{
    const invite=await post('/teams/invitations/preview',{token});
    modal('Invitation à une équipe',`<p><strong>${esc(invite.owner_name)}</strong> vous invite dans <strong>${esc(invite.team_name)}</strong>.</p><p>Les membres verront votre nom et votre email. Vos conversations, projets et connexions restent privés ; le partage de tâches se fait séparément.</p><div class="actions">${button('Rejoindre l’équipe','team-accept','check')}${button('Ignorer','team-ignore',null,'secondary')}</div>`,'','medium');
  }catch(e){toast(e.message,true);}
}
async function teamAction(action,b){
  if(!action.startsWith('team-'))return false;
  if(action==='team-new'){
    modal('Créer une équipe',`<form id="team-form">${textField('name','Nom de l’équipe','','text',true)}<label for="team-kind">Type</label><select name="kind" id="team-kind">${Object.entries(teamKinds).map(([key,name])=>`<option value="${key}" ${S.user.account_type===key?'selected':''}>${name}</option>`).join('')}</select><button class="btn" type="submit">Créer</button></form>`,'','medium');
  }else if(action==='team-invite'){
    modal('Inviter une personne',`<form id="team-invite-form" data-id="${esc(b.dataset.id)}">${textField('email','Email de la personne invitée','','email',true)}<p>Vous obtiendrez un lien valable sept jours à transmettre. La personne devra se connecter ou créer son compte avec cette adresse pour accepter.</p><button class="btn" type="submit">Préparer le lien</button></form>`,'','medium');
  }else if(action==='team-copy'){
    await navigator.clipboard.writeText($('#team-invite-link').value);toast('Lien copié.');
  }else if(action==='team-invite-revoke'){
    await api('/teams/'+b.dataset.id+'/invitations/'+b.dataset.inviteId,{method:'DELETE'});await loadTeams();
  }else if(action==='team-member-remove'){
    await api('/teams/'+b.dataset.id+'/members/'+b.dataset.userId,{method:'DELETE'});await loadTeams();
  }else if(action==='team-accept'){
    b.disabled=true;
    try{await post('/teams/invitations/accept',{token:sessionStorage.getItem('passage-team-invite')});sessionStorage.removeItem('passage-team-invite');closeModal();S.view='teams';shell();toast('Vous avez rejoint l’équipe.');}finally{b.disabled=false;}
  }else if(action==='team-ignore'){
    sessionStorage.removeItem('passage-team-invite');closeModal();
  }
  return true;
}
async function teamSubmit(f,data){
  if(f.id==='team-form'){
    await post('/teams',Object.fromEntries(data));closeModal();await loadTeams();return true;
  }
  if(f.id==='team-invite-form'){
    const result=await post('/teams/'+f.dataset.id+'/invitations',Object.fromEntries(data));
    modal('Lien d’invitation prêt',`<p>Destinataire : ${esc(result.email)}. Aucun email n’a été envoyé. Transmettez ce lien à cette personne.</p><label for="team-invite-link">Lien valable sept jours</label><input id="team-invite-link" value="${esc(result.url)}" readonly><div class="actions">${button('Copier le lien','team-copy','copy')}${button('Fermer','close',null,'secondary')}</div>`,'','medium');
    await loadTeams();return true;
  }
  return false;
}
