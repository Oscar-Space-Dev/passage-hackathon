"""Passage's guided agent creation, adapted from OSCAR AI Super Skill Creator V4.

The doctrine is versioned with the product. Existing agents remain on their
original definition; only agents created through this guide use these checks.
"""

VERSION = 'super-skill-creator-v4-passage-1'

STEPS = [
    '1 · Cadrer la mission, les déclencheurs et les limites',
    '2 · Choisir le cerveau et sa voie d’exécution',
    '3 · Écrire le skill et les pièces du harnais',
    '4 · Accorder uniquement les outils nécessaires',
    '5 · Contrôler la définition avec un humain',
    '6 · Enregistrer une révision et éprouver un cas réel',
]


def blueprint(role, name, mandate, model):
    """Return an inactive, editable draft. Missing decisions are never guessed."""
    return {
        'id': '', 'name': name + ' personnalisé', 'role': role,
        'mandate': mandate, 'creator_version': VERSION,
        'trigger': '', 'reads': '', 'boundaries': '', 'checkpoint': '',
        'deliverables': '', 'process': '', 'workflow': '', 'experience': '',
        'skill': (f'# {name} — {mandate}\n\n'
                  '## Protocole de travail\n'
                  '1. Cadrer la demande, les sources et les critères de réussite.\n'
                  '2. Proposer une démarche et faire valider les choix importants.\n'
                  '3. Exécuter par étapes visibles ; signaler les incertitudes.\n'
                  '4. Vérifier les preuves, calculs et limites.\n'
                  '5. Livrer un résultat sourcé et compréhensible.\n'
                  '6. Consigner les faits validés et les erreurs corrigées.'),
        'context': '', 'memory': '', 'provider': 'codex', 'model': model,
        'engine': 'direct', 'tools': (['work.read'] if role == 'research_task' else
                                     ['theses.read'] + (['library.search'] if role == 'rapprochement' else [])),
        'work_specialties': [],
        'connector_ids': [], 'method_ref': '', 'method_version': '1.0.0',
        'max_steps': 3, 'active': False, 'revision': 0,
    }


def issues(agent):
    if not agent.get('creator_version'):
        return []
    missing = {
        'trigger': 'Déclencheur : quand cet agent intervient',
        'reads': 'Sources et données que l’agent lit',
        'boundaries': 'Décisions réservées à l’humain',
        'checkpoint': 'Point de vérification humaine',
        'deliverables': 'Livrable attendu et critère de réussite',
        'context': 'Contexte métier propre à cet agent',
    }
    errors = [label for key, label in missing.items() if not agent.get(key, '').strip()]
    for key in ('skill', 'context', 'memory', 'process', 'workflow', 'experience'):
        if 'à écrire' in agent.get(key, '').lower():
            errors.append('Passage à compléter dans ' + key)
    if not agent.get('tools') and not agent.get('connector_ids'):
        errors.append('Au moins un outil accordé')
    if not agent.get('provider') or not agent.get('model') or not agent.get('engine'):
        errors.append('Cerveau et voie d’exécution')
    if agent.get('engine') == 'pipelex' and not agent.get('method_ref'):
        errors.append('Référence de méthode Pipelex')
    return errors
