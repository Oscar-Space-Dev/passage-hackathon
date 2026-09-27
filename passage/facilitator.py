"""Marguerite's user-scoped agent creation, adapted from OSCAR's Creator V4."""
import json
import re

from . import agents, auth, creator, projects, store, work_catalog
from .schemas import AgentInput


DOCTRINE = '''Super Skill Facilitator · Passage (adaptation OSCAR AI V4)
1. Cadrer avec la personne : métier, déclencheur, lectures autorisées, décisions humaines, tâches R1–R3 et nature du travail. Poser une question à la fois si une information manque. Ne rien inventer.
2. Cerveau : ChatGPT via Codex par défaut, modèle auto. Une clé API ou un autre fournisseur exige un choix explicite. Gradium ne sert qu'à la voix. Dust et Pipelex ne sont utilisables que si leurs accès sont réellement configurés.
3. Harnais : skill court avec six étapes numérotées, contexte métier, mémoire de faits validés seulement, processus et workflow selon le besoin, outils accordés un par un. L'ADN et les garde-fous de Passage sont injectés par la plateforme ; ne pas les recopier.
4. Contrôle Clear Box : déclencheur, lectures, décisions humaines, point de validation, livrable, spécialités et capacité réelle. Aucun passage fictif ou « à écrire ». Tant que le contrôle échoue, poser une question et ne proposer aucune création.
5. Après accord sur le plan, créer une révision personnelle et l'affecter au projet demandé. L'export .mthds est une projection à relire ; il ne publie ni n'exécute une méthode Pipelex. N'annoncer Pipelex opérationnel qu'après configuration et essai réel.
6. Éprouver l'agent sur un travail réel, conserver la révision et corriger son harnais d'après les retours de l'humain.'''


def visible(agent, user=None):
    user = user or auth.CURRENT_USER.get()
    return agents.visible(agent, user)


def prepare(raw, user, project_id=''):
    """Validate the exact definition that will be saved after plan approval."""
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError()
        data = AgentInput.model_validate(data).model_dump()
    except Exception as exc:
        raise ValueError('La définition de l’agent doit être un objet JSON conforme au créateur.') from exc
    if data['role'] != 'research_task':
        raise ValueError('Marguerite crée actuellement des spécialistes de travaux R1–R3. Précisez leurs tâches.')
    if data['provider'] != 'codex' or data['engine'] != 'direct':
        raise ValueError('Le spécialiste créé par Marguerite utilise ChatGPT via Codex et le moteur direct.')
    if data['connector_ids']:
        raise ValueError('Les connecteurs MCP doivent être accordés séparément dans l’atelier des agents.')
    if data['method_ref']:
        raise ValueError('Une référence Pipelex ne peut être indiquée avant publication de la méthode.')
    if project_id:
        project = projects.get(project_id)
        if project['owner_id'] != user['id'] or projects.busy(project) or len(project['agent_ids']) >= 20:
            raise ValueError('Le projet ne peut pas accueillir cet agent maintenant.')
    data['creator_version'] = creator.VERSION
    data['active'] = True
    data['method_ref'] = ''
    if not data['work_specialties'] or any(task not in work_catalog.BY_ID for task in data['work_specialties']):
        raise ValueError('Choisissez au moins une tâche R1–R3 existante.')
    if len(set(data['work_specialties'])) != len(data['work_specialties']):
        raise ValueError('Une spécialité est répétée.')
    if not all(re.search(r'(?m)^\s*' + str(i) + r'[.)]\s+\S', data['skill']) for i in range(1, 7)):
        raise ValueError('Le skill doit décrire six étapes numérotées, de 1 à 6.')
    missing = agents.control(data)
    if missing:
        raise ValueError('Harnais incomplet : ' + ' ; '.join(missing))
    return data


def create(raw, user, project_id=''):
    data = prepare(raw, user, project_id)
    data.update(id=store.uid('agent_'), owner_id=user['id'], revision=1)
    with store.transaction() as conn:
        store.put('agent', data, conn)
        store.put('revision', {**data, 'id': data['id'] + ':1', 'agent_id': data['id'],
                               'saved_at': store.now()}, conn)
    if project_id:
        project = projects.get(project_id)
        projects.change_team(project_id, projects.TeamInput(agent_ids=project['agent_ids'] + [data['id']]))
    store.event('Agent personnel créé par Marguerite', data['id'], data['name'])
    return {'agent_id': data['id'], 'project_id': project_id, 'status': 'created',
            'creator_version': creator.VERSION, 'mthds_export': f'/api/agents/{data["id"]}/export/pipelex'}
