"""Teams and recipient-bound invitation links; personal projects stay private."""
import secrets
import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import Field

from . import auth, store
from .schemas import StrictModel

router = APIRouter(prefix='/api/teams')


class TeamInput(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    kind: Literal['lab', 'researcher', 'company']


class InviteInput(StrictModel):
    email: str = Field(min_length=3, max_length=254)


class InvitationToken(StrictModel):
    token: str = Field(min_length=30, max_length=200)


def get(identifier, owner=False, conn=None):
    row = store.get('team', identifier, conn)
    user_id = auth.current()['id']
    if not row or user_id not in row['member_ids']:
        raise HTTPException(404, 'Équipe introuvable.')
    if owner and row['owner_id'] != user_id:
        raise HTTPException(403, 'Seul le responsable peut gérer les invitations et les membres.')
    return row


def public(row):
    result = {k: row[k] for k in ('id', 'name', 'kind', 'owner_id', 'created_at')}
    result['members'] = [{k: user[k] for k in ('id', 'name', 'email')}
                         for uid in row['member_ids'] if (user := store.get('user', uid))]
    result['can_manage'] = row['owner_id'] == auth.current()['id']
    if result['can_manage']:
        result['invitations'] = [{k: invite[k] for k in ('id', 'email', 'status', 'expires_at')}
                                 for invite in store.all_of('team_invite') if invite['team_id'] == row['id']]
        for invite in result['invitations']:
            if invite['status'] == 'pending' and invite['expires_at'] < time.time():
                invite['status'] = 'expired'
    return result


@router.get('')
def listing():
    return [public(row) for row in store.all_of('team') if auth.current()['id'] in row['member_ids']]


@router.post('')
def create(body: TeamInput):
    name = body.name.strip()
    if len(name) < 2:
        raise HTTPException(422, 'Indiquez le nom de l’équipe.')
    user_id = auth.current()['id']
    row = store.put('team', {'id': store.uid('team_'), 'name': name, 'kind': body.kind,
                            'owner_id': user_id, 'member_ids': [user_id], 'created_at': store.now()})
    store.event('Équipe créée', row['id'])
    return public(row)


@router.post('/{identifier}/invitations')
def invite(identifier: str, body: InviteInput, request: Request):
    email = body.email.strip().casefold()
    if '@' not in email or any(c.isspace() for c in email):
        raise HTTPException(422, 'Adresse email invalide.')
    with store.transaction() as conn:
        team = get(identifier, owner=True, conn=conn)
        if email in {store.get('user', uid, conn)['email'] for uid in team['member_ids']}:
            raise HTTPException(409, 'Cette personne est déjà membre.')
        # Replacing a pending invitation invalidates its old bearer link.
        for old in store.all_of('team_invite'):
            if old['team_id'] == identifier and old['email'] == email and old['status'] == 'pending':
                old['status'] = 'revoked'
                store.put('team_invite', old, conn)
        token = secrets.token_urlsafe(32)
        row = store.put('team_invite', {'id': store.uid('invite_'), 'team_id': identifier,
            'email': email, 'token_hash': auth.digest(token), 'status': 'pending',
            'expires_at': time.time()+7*86400, 'created_at': store.now()}, conn)
    store.event('Invitation d’équipe préparée', identifier)
    return {'id': row['id'], 'email': email, 'expires_at': row['expires_at'],
            'url': str(request.base_url).rstrip('/')+'/#team-invite='+token}


def pending(token, conn=None):
    digest = auth.digest(token)
    row = next((r for r in store.all_of('team_invite') if secrets.compare_digest(r['token_hash'], digest)), None)
    if not row or row['status'] != 'pending' or row['expires_at'] < time.time():
        raise HTTPException(410, 'Invitation expirée, utilisée ou révoquée.')
    if auth.current()['email'].casefold() != row['email']:
        raise HTTPException(403, 'Connectez-vous avec l’adresse email à laquelle cette invitation est destinée.')
    return row


@router.post('/invitations/preview')
def preview(body: InvitationToken):
    row = pending(body.token)
    team = store.get('team', row['team_id'])
    if not team:
        raise HTTPException(410, 'Cette équipe n’existe plus.')
    owner = store.get('user', team['owner_id'])
    return {'team_name': team['name'], 'kind': team['kind'], 'owner_name': owner['name'],
            'email': row['email'], 'expires_at': row['expires_at']}


@router.post('/invitations/accept')
def accept(body: InvitationToken):
    with store.transaction() as conn:
        row = pending(body.token, conn)
        team = store.get('team', row['team_id'], conn)
        if not team:
            raise HTTPException(410, 'Cette équipe n’existe plus.')
        user_id = auth.current()['id']
        if user_id not in team['member_ids']:
            team['member_ids'].append(user_id)
        store.put('team', team, conn)
        row.update(status='accepted', accepted_by=user_id, accepted_at=store.now())
        store.put('team_invite', row, conn)
    store.event('Invitation d’équipe acceptée', team['id'])
    return public(team)


@router.delete('/{identifier}/invitations/{invitation_id}')
def revoke(identifier: str, invitation_id: str):
    with store.transaction() as conn:
        get(identifier, owner=True, conn=conn)
        row = store.get('team_invite', invitation_id, conn)
        if not row or row['team_id'] != identifier:
            raise HTTPException(404, 'Invitation introuvable.')
        if row['status'] != 'pending':
            raise HTTPException(409, 'Cette invitation a déjà été traitée.')
        row['status'] = 'revoked'
        store.put('team_invite', row, conn)
    return {'ok': True}


@router.delete('/{identifier}/members/{user_id}')
def remove_member(identifier: str, user_id: str):
    with store.transaction() as conn:
        team = get(identifier, owner=user_id != auth.current()['id'], conn=conn)
        if user_id == team['owner_id']:
            raise HTTPException(409, 'Le responsable doit rester membre de son équipe.')
        team['member_ids'] = [uid for uid in team['member_ids'] if uid != user_id]
        store.put('team', team, conn)
    store.event('Membre retiré de l’équipe', identifier)
    return {'ok': True}
