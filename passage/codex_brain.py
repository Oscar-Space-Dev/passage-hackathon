"""Personal ChatGPT subscription access through the official Codex app-server."""
import atexit
import hashlib
import json
import os
import queue
import shutil
import subprocess
import threading
import time
from collections import deque

from fastapi import APIRouter, HTTPException
from . import auth, integrations, store

router = APIRouter(prefix='/api/brains/chatgpt')
CLIENTS = {}
LOCK = threading.RLock()


def user_directory(user_id):
    key = hashlib.sha256(user_id.encode()).hexdigest()
    return store.db_path().parent / 'runtime' / 'chatgpt' / key


def configured():
    user = auth.CURRENT_USER.get()
    return bool(user and shutil.which('codex') and
                (user_directory(user['id']) / 'home' / 'auth.json').exists())


class CodexClient:
    def __init__(self, user_id):
        executable = shutil.which('codex')
        if not executable:
            raise integrations.IntegrationError('Installez le CLI officiel Codex pour connecter votre compte ChatGPT.')
        self.root = user_directory(user_id)
        self.work = self.root / 'work'
        self.home = self.root / 'home'
        self.work.mkdir(parents=True, exist_ok=True)
        self.home.mkdir(parents=True, exist_ok=True)
        # This user gets an independent login. Never import the desktop host's credentials.
        (self.home / 'config.toml').write_text('cli_auth_credentials_store = "file"\n', encoding='utf-8')
        environment = {k:v for k,v in os.environ.items() if k.upper() in {
            'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','PROGRAMDATA','PATHEXT',
            'HOME','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','SSL_CERT_FILE','REQUESTS_CA_BUNDLE'}}
        environment['CODEX_HOME'] = str(self.home.resolve())
        flags = ['-c', 'web_search="disabled"']
        for feature in ('shell_tool','unified_exec','apps','plugins','code_mode_host','in_app_browser'):
            flags += ['-c', f'features.{feature}=false']
        self.process = subprocess.Popen([executable, *flags, 'app-server'],
            cwd=self.work, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.pending = {}
        self.events = deque(maxlen=2000)
        self.sequence = 0
        self.event_sequence = 0
        self.io_lock = threading.RLock()
        self.mission_lock = threading.Lock()
        self.login_lock = threading.Lock()
        self.login = None
        self.login_created_at = 0.0
        threading.Thread(target=self.read, daemon=True, name='passage-chatgpt').start()
        self.request('initialize', {'clientInfo':{'name':'passage','title':'Passage','version':'0.1.0'}})
        self.send({'method':'initialized','params':{}})

    def send(self, message):
        with self.io_lock:
            if self.process.poll() is not None:
                raise integrations.IntegrationError('La connexion Codex locale est arrêtée. Reconnectez votre compte.')
            self.process.stdin.write(json.dumps(message,ensure_ascii=False)+'\n')
            self.process.stdin.flush()

    def read(self):
        try:
            for line in self.process.stdout:
                try:
                    event=json.loads(line)
                except ValueError:
                    continue
                if 'id' in event and 'method' not in event:
                    with self.io_lock:
                        waiter=self.pending.get(event['id'])
                    if waiter:
                        waiter.put(event)
                elif 'id' in event:
                    # Passage owns the harness: no unhandled host tool/approval is granted.
                    self.send({'id':event['id'],'error':{'code':-32601,'message':'Action non disponible dans ce harnais Passage.'}})
                else:
                    with self.io_lock:
                        self.event_sequence+=1
                        self.events.append((self.event_sequence,event))
                        if event.get('method')=='account/login/completed':
                            completed=(event.get('params') or {}).get('loginId')
                            if self.login and self.login.get('loginId')==completed:
                                self.login=None
                                self.login_created_at=0.0
        finally:
            with self.io_lock:
                for waiter in self.pending.values():
                    waiter.put({'error':{'code':'disconnected'}})

    def request(self, method, params=None, timeout=25):
        with self.io_lock:
            self.sequence+=1
            identifier=self.sequence
            waiter=queue.Queue()
            self.pending[identifier]=waiter
        try:
            self.send({'id':identifier,'method':method,'params':params or {}})
            result=waiter.get(timeout=timeout)
            if 'error' in result:
                message=str(result['error'].get('message','')).splitlines()[0][:240]
                raise integrations.IntegrationError(
                    f'Codex ne peut pas traiter {method}' + (f' : {message}' if message else '.'))
            return result.get('result',{})
        except queue.Empty:
            raise integrations.IntegrationError('Codex ne répond pas dans le délai prévu.')
        finally:
            with self.io_lock:
                self.pending.pop(identifier,None)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:self.process.kill()

    def complete(self, model, prompt, context, schema):
        if not self.mission_lock.acquire(timeout=480):
            raise integrations.IntegrationError('Votre compte ChatGPT est encore occupé après huit minutes. Réessayez cette mission.')
        thread_id=turn_id=None
        try:
            account=self.request('account/read',{'refreshToken':False}).get('account')
            if not account or account.get('type')!='chatgpt':
                raise integrations.IntegrationError('Connectez votre compte ChatGPT dans Connexions.')
            selected_model=model
            if model=='auto':
                available=self.request('model/list',{'limit':100,'includeHidden':False}).get('data',[])
                selected=next((item for item in available if item.get('isDefault')), None)
                selected=selected or next(iter(available), None)
                if not selected:
                    raise integrations.IntegrationError('Aucun modèle disponible avec ce compte ChatGPT.')
                selected_model=selected['model']
            thread=self.request('thread/start',{'model':selected_model,'cwd':str(self.work.resolve()),
                'ephemeral':True,'approvalPolicy':'never','sandbox':'read-only',
                'baseInstructions':'Tu es le cerveau d’un agent Passage. Réponds uniquement au contrat JSON demandé. Utilise seulement les données fournies ; aucune commande système ni lecture de fichier.',
                'developerInstructions':prompt})
            thread_id=thread['thread']['id']
            cursor=self.event_sequence
            started=self.request('turn/start',{'threadId':thread_id,
                'input':[{'type':'text','text':json.dumps(context,ensure_ascii=False)}],
                'outputSchema':schema,'sandboxPolicy':{'type':'readOnly','networkAccess':False}})
            turn_id=started['turn']['id']
            output=[]
            deadline=time.monotonic()+480
            while time.monotonic()<deadline:
                with self.io_lock:
                    events=[(seq,event) for seq,event in self.events if seq>cursor]
                for seq,event in events:
                    cursor=seq
                    params=event.get('params',{})
                    if params.get('threadId')!=thread_id:
                        continue
                    if event.get('method')=='item/completed':
                        item=params.get('item',{})
                        if item.get('type')=='agentMessage' and item.get('phase')!='commentary':
                            output.append(item.get('text',''))
                    if event.get('method')=='turn/completed':
                        if params.get('turn',{}).get('status')!='completed':
                            raise integrations.IntegrationError('Le tour Codex a échoué ou a été interrompu. Vérifiez les limites de votre compte.')
                        result=integrations.extract_json('\n'.join(output))
                        return result,{'actual_model':selected_model,'billing_source':'Compte ChatGPT · Codex','codex_thread_id':thread_id}
                time.sleep(.1)
            raise integrations.IntegrationError('Codex a dépassé le délai de la mission.')
        finally:
            if thread_id and turn_id:
                try:self.request('turn/interrupt',{'threadId':thread_id,'turnId':turn_id},timeout=5)
                except integrations.IntegrationError:pass
            self.mission_lock.release()


def client(user_id):
    key=(str(store.db_path()),user_id)
    with LOCK:
        current=CLIENTS.get(key)
        if current is None or current.process.poll() is not None:
            current=CodexClient(user_id)
            CLIENTS[key]=current
        return current


@router.get('/status')
def status():
    user_id=auth.current()['id']
    if not shutil.which('codex'):
        return {'installed':False,'connected':False,'account':None}
    if not user_directory(user_id).exists():
        return {'installed':True,'connected':False,'account':None}
    try:
        engine=client(user_id)
        account=engine.request('account/read',{'refreshToken':False}).get('account')
        connected=bool(account and account.get('type')=='chatgpt')
        if connected:
            engine.login=None
            engine.login_created_at=0.0
        limits=engine.request('account/rateLimits/read') if connected else None
        return {'installed':True,'connected':connected,'account':account,'limits':limits,
                'pending_login':engine.login if not connected else None}
    except integrations.IntegrationError as exc:
        raise HTTPException(502,str(exc))


def begin_login(kind):
    try:
        engine=client(auth.current()['id'])
        with engine.login_lock:
            account=engine.request('account/read',{'refreshToken':False}).get('account')
            if account and account.get('type')=='chatgpt':
                engine.login=None
                engine.login_created_at=0.0
                return {'connected':True}
            previous=engine.login
            if previous and (previous.get('type')!=kind or
                             time.monotonic()-engine.login_created_at>300):
                if previous.get('loginId'):
                    engine.request('account/login/cancel',{'loginId':previous['loginId']},timeout=10)
                engine.login=None
                engine.login_created_at=0.0
            if not engine.login:
                params=({'type':'chatgpt','useHostedLoginSuccessPage':True,
                         'appBrand':'chatgpt'} if kind=='chatgpt' else
                        {'type':'chatgptDeviceCode'})
                engine.login=engine.request('account/login/start',params)
                engine.login_created_at=time.monotonic()
            return engine.login
    except integrations.IntegrationError as exc:
        raise HTTPException(502,str(exc))


@router.post('/connect')
def connect():
    return begin_login('chatgpt')


@router.post('/connect-device')
def connect_device():
    return begin_login('chatgptDeviceCode')


@router.post('/disconnect')
def disconnect():
    try:
        engine=client(auth.current()['id'])
        if engine.mission_lock.locked():
            raise HTTPException(409,'Attendez la fin de la mission ChatGPT avant de déconnecter ce compte.')
        engine.request('account/logout')
        engine.login=None
        engine.login_created_at=0.0
        return {'ok':True}
    except integrations.IntegrationError as exc:
        raise HTTPException(502,str(exc))


@router.get('/models')
def models():
    try:
        engine=client(auth.current()['id'])
        account=engine.request('account/read').get('account')
        if not account or account.get('type')!='chatgpt':
            raise HTTPException(409,'Connectez votre compte ChatGPT pour découvrir ses modèles.')
        result=[]
        cursor=None
        for _ in range(10):
            page=engine.request('model/list',{'limit':100,'includeHidden':False,'cursor':cursor})
            result.extend(page.get('data',[]))
            cursor=page.get('nextCursor')
            if not cursor:break
        return {'models':result,'billing_source':'Compte ChatGPT · accès Codex'}
    except integrations.IntegrationError as exc:
        raise HTTPException(502,str(exc))


@atexit.register
def shutdown():
    for engine in list(CLIENTS.values()):
        engine.close()
