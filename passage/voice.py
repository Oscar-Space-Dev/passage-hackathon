"""Gradium REST voice adapter: WAV in, transcription out; text in, WAV out."""
import io
import json
import wave
import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from . import auth, integrations, store

router = APIRouter(prefix='/api/voice')
BASE = 'https://api.gradium.ai/api'

def personal_settings():
    user = auth.CURRENT_USER.get()
    row = store.get('voice_account', user['id']) if user else None
    if not row:
        return None
    from .partner_mcp import cipher
    return json.loads(cipher().decrypt(row['encrypted'].encode()))

def credentials():
    personal = personal_settings()
    if personal:
        return personal['api_key'], personal['voice_id'], 'personal'
    return integrations.env('GRADIUM_API_KEY'), integrations.env('GRADIUM_VOICE_ID'), 'installation'

def headers():
    key, _, _ = credentials()
    if not key:
        raise HTTPException(409, 'Configurez la clé Gradium dans Connexions pour utiliser la voix.')
    return {'x-api-key': key}

def checked(response):
    if response.status_code>=400:
        raise HTTPException(502, f'Gradium a répondu HTTP {response.status_code}. Vérifiez la clé et la voix configurées.')
    return response

@router.get('/status')
def status():
    key, voice_id, source = credentials()
    return {'configured': bool(key), 'voice_id': voice_id, 'source': source if key else 'none'}

@router.get('/account')
def account():
    current = status()
    return {**current, 'personal_configured': personal_settings() is not None}

class VoiceAccount(BaseModel):
    api_key: str = Field(default='', max_length=4000)
    voice_id: str = Field(default='', max_length=200)

@router.put('/account')
def save_account(body: VoiceAccount):
    existing = personal_settings() or {}
    key = body.api_key.strip() or existing.get('api_key', '')
    voice_id = body.voice_id.strip() or existing.get('voice_id', '')
    if len(key) < 10 or not voice_id:
        raise HTTPException(422, 'Indiquez votre clé API Gradium et un identifiant de voix.')
    from .partner_mcp import cipher
    store.put('voice_account', {'id': auth.current()['id'],
              'encrypted': cipher().encrypt(json.dumps({'api_key': key, 'voice_id': voice_id}).encode()).decode()})
    store.event('Voix personnelle configurée', auth.current()['id'], 'Clé exclue du journal')
    return account()

@router.delete('/account')
def remove_account():
    store.remove('voice_account', auth.current()['id'])
    store.event('Voix personnelle retirée', auth.current()['id'])
    return account()

@router.post('/transcribe')
async def transcribe(request: Request):
    chunks = bytearray()
    async for chunk in request.stream():
        chunks.extend(chunk)
        if len(chunks)>3_000_000:
            raise HTTPException(413, 'Enregistrement limité à 60 secondes.')
    try:
        with wave.open(io.BytesIO(chunks), 'rb') as recording:
            if recording.getnchannels()!=1 or recording.getsampwidth()!=2 or recording.getframerate()!=24000 or recording.getnframes()>24000*60:
                raise ValueError()
    except (wave.Error, EOFError, ValueError):
        raise HTTPException(422, 'Un enregistrement WAV mono 24 kHz / 16 bits de 60 secondes maximum est requis.')
    import asyncio
    def call():
        response = checked(requests.post(BASE+'/post/speech/asr', headers={**headers(),'Content-Type':'audio/wav'},
            params={'json_config':json.dumps({'language':'fr'})}, data=bytes(chunks), timeout=(10,90)))
        texts=[]
        for line in response.text.splitlines():
            if not line.strip():
                continue
            try:
                event=json.loads(line)
            except ValueError:
                raise HTTPException(502,'Transcription Gradium illisible.')
            if event.get('type')=='error':
                raise HTTPException(502,'Gradium a interrompu la transcription.')
            if event.get('type')=='text':
                texts.append(event.get('text',''))
        text=' '.join(texts).strip()
        if not text:
            raise HTTPException(422,'Aucune parole reconnue. Réessayez ou écrivez votre demande.')
        return {'text':text, 'provider':'gradium'}
    try:
        return await asyncio.to_thread(call)
    except requests.RequestException:
        raise HTTPException(502,'Gradium est inaccessible. La demande n’a pas été envoyée au coordinateur.')

class Speech(BaseModel):
    text: str = Field(min_length=1, max_length=6000)

@router.post('/speak')
def speak(body: Speech):
    _, voice, _ = credentials()
    if not voice:
        raise HTTPException(409,'Renseignez un identifiant de voix Gradium dans Connexions.')
    try:
        response=checked(requests.post(BASE+'/post/speech/tts', headers=headers(),
            json={'text':body.text,'voice_id':voice,'output_format':'wav','only_audio':True},timeout=(10,90)))
    except requests.RequestException:
        raise HTTPException(502,'La lecture Gradium est indisponible. La réponse écrite reste accessible.')
    if not response.content.startswith(b'RIFF'):
        raise HTTPException(502,'Gradium n’a pas renvoyé un fichier audio WAV.')
    return Response(response.content,media_type='audio/wav',headers={'Cache-Control':'no-store'})
