"""Protocol and access checks for the continuous voice route; no microphone or provider calls."""
import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from passage import voice_live


class Socket:
    def __init__(self, origin='http://127.0.0.1:8088'):
        self.headers = {'origin': origin}
        self.url = SimpleNamespace(netloc='127.0.0.1:8088')
        self.sent = []
        self.closed = None

    async def send_json(self, value, *args, **kwargs):
        self.sent.append(value)

    async def accept(self):
        pass

    async def close(self, code=1000):
        self.closed = code


class LiveVoiceTests(unittest.TestCase):
    def test_voice_uses_fast_chatgpt_model_only_for_auto(self):
        fake=SimpleNamespace(request=lambda *args: {'data': [
            {'model':'gpt-6-astra','isDefault':True},
            {'model':'gpt-6-luna','isDefault':False}]})
        with patch.object(voice_live.codex_brain, 'client', return_value=fake):
            self.assertEqual(voice_live.voice_model('one','auto'),'gpt-6-luna')
            self.assertEqual(voice_live.voice_model('one','gpt-6-sol'),'gpt-6-sol')

    def test_repeated_gradbot_turn_index_keeps_distinct_dialogue_messages(self):
        socket = Socket()
        transcript = voice_live.TranscriptSocket(socket)
        async def feed():
            await transcript.send_json({'type':'user_text','turn_idx':0,'text':'Première question'})
            first = transcript.latest_user_turn()
            await transcript.send_json({'type':'event','event':'push_to_llm'})
            await transcript.send_json({'type':'agent_text','turn_idx':0,'text':'Première réponse'})
            await transcript.send_json({'type':'event','event':'end_of_turn'})
            await transcript.send_json({'type':'user_text','turn_idx':0,'text':'Deuxième question'})
            return first
        first = asyncio.run(feed())
        self.assertNotEqual(first, transcript.latest_user_turn())
        saved = []
        with patch.object(voice_live.projects, 'message', side_effect=lambda *args, **kwargs: saved.append(args)):
            transcript.mark_logged(first, {'user','assistant'})
            transcript.save('project')
        self.assertEqual([(row[1],row[2]) for row in saved], [('user','Deuxième question')])

    def test_cross_origin_rejected_before_authentication(self):
        socket = Socket('https://other.example')
        with patch.object(voice_live.auth, 'authenticate') as authenticate:
            asyncio.run(voice_live.live_voice(socket, 'project'))
        self.assertEqual(socket.closed, 4403)
        authenticate.assert_not_called()

    def test_project_owner_and_transcript(self):
        socket = Socket()
        user = {'id': 'one'}
        project = {'id': 'project', 'owner_id': 'one', 'coordinator_id': 'agent', 'brain_provider': 'agent',
                   'name': 'Essai', 'objective': 'Discuter', 'context': ''}
        brain = {'id': 'agent', 'engine': 'direct', 'provider': 'ollama', 'model': 'test-model'}
        saved = []
        calls = []

        async def session(websocket, **options):
            config = options['on_start']({'type': 'start'})
            self.assertEqual(config.language, voice_live.gradbot.Lang.Fr)
            self.assertEqual(options['output_format'], voice_live.gradbot.AudioFormat.Pcm)
            self.assertEqual(options['run_kwargs']['llm_model_name'], 'test-model')
            await websocket.send_json({'type': 'user_text', 'text': 'Bonjour', 'turn_idx': 0})
            await websocket.send_json({'type': 'agent_text', 'text': 'Bonjour à vous', 'turn_idx': 0})
            class Handle:
                name = 'lancer_mission'
                def __init__(self, demande):
                    self.args = {'demande': demande}
                    self.result = None
                    self.error = None
                async def send_json(self, value):
                    self.result = value
                async def send_error(self, value):
                    self.error = value
            read = Handle('statut')
            await options['on_tool_call'](read, None, websocket)
            self.assertEqual(read.result['answer'], 'Aucune mission en cours.')
            changed = Handle('Utilise le modèle ChatGPT GPT-6 Sol')
            await options['on_tool_call'](changed, None, websocket)
            self.assertEqual(changed.result['command'], 'brain')
            self.assertTrue(any(row.get('type')=='project_update' and row.get('restart_voice')
                                for row in websocket.sent))
            approval = Handle("confirme l'action")
            await options['on_tool_call'](approval, None, websocket)
            self.assertIn('carte du projet', approval.error)

        def get(kind, identifier):
            return project if kind == 'project' else brain if kind == 'agent' else None

        with patch.object(voice_live.auth, 'authenticate', return_value=(user, {'id': 'session'})), \
             patch.object(voice_live.store, 'get', side_effect=get), \
             patch.object(voice_live.voice, 'credentials', return_value=('secret', 'voice', 'personal')), \
             patch.object(voice_live.projects, 'get', return_value=project), \
             patch.object(voice_live.projects, 'messages', return_value=[]), \
             patch.object(voice_live.projects, 'dialogue', side_effect=lambda body: calls.append(body.message) or
                          {'project_id': 'project', 'command': 'brain' if body.message.startswith('Utilise') else 'status', 'run': None,
                           'notice': 'Aucune mission en cours.'}), \
             patch.object(voice_live.store, 'all_of', return_value=[]), \
             patch.object(voice_live.projects, 'message', side_effect=lambda *args, **kwargs: saved.append((args, kwargs))), \
             patch.object(voice_live.gradbot.websocket, 'handle_session', side_effect=session):
            asyncio.run(voice_live.live_voice(socket, 'project'))
        self.assertEqual([row[0][1] for row in saved], ['user', 'assistant'])
        self.assertEqual([row[0][2] for row in saved], ['Bonjour', 'Bonjour à vous'])
        self.assertEqual(calls, ['statut', 'Utilise le modèle ChatGPT GPT-6 Sol'])
        self.assertFalse(voice_live.ACTIVE)

    def test_other_users_project_rejected(self):
        socket = Socket()
        with patch.object(voice_live.auth, 'authenticate', return_value=({'id': 'other'}, {'id': 'session'})), \
             patch.object(voice_live.store, 'get', return_value={'owner_id': 'one'}):
            asyncio.run(voice_live.live_voice(socket, 'project'))
        self.assertEqual(socket.closed, 4401)

    def test_dialogue_messages_are_not_saved_twice_from_voice(self):
        socket = Socket()
        user = {'id': 'one'}
        project = {'id': 'project', 'owner_id': 'one', 'coordinator_id': 'agent', 'brain_provider': 'agent',
                   'name': 'Essai', 'objective': 'Discuter', 'context': ''}
        brain = {'id': 'agent', 'engine': 'direct', 'provider': 'ollama', 'model': 'test-model'}
        messages = []
        saved = []

        class Handle:
            name = 'lancer_mission'
            args = {'demande': 'statut de la mission'}
            result = None

            async def send_json(self, value):
                self.result = value

        def dialogue(_body):
            messages.extend([
                {'id': 'user-1', 'role': 'user', 'text': 'statut de la mission'},
                {'id': 'answer-1', 'role': 'assistant', 'text': 'Aucune mission en cours.'},
            ])
            return {'project_id': 'project', 'command': 'status',
                    'run': None, 'notice': 'Aucune mission en cours.'}

        async def session(websocket, **options):
            await websocket.send_json({'type': 'user_text',
                                       'text': 'Quel est le statut ?', 'turn_idx': 0})
            handle = Handle()
            await options['on_tool_call'](handle, None, websocket)
            self.assertEqual(handle.result['command'], 'status')
            await websocket.send_json({'type': 'agent_text',
                                       'text': 'Aucune mission en cours.', 'turn_idx': 0})
            await websocket.send_json({'type': 'user_text',
                                       'text': 'Merci', 'turn_idx': 1})
            await websocket.send_json({'type': 'agent_text',
                                       'text': 'Je vous en prie.', 'turn_idx': 1})

        def get(kind, identifier):
            return project if kind == 'project' else brain if kind == 'agent' else None

        with patch.object(voice_live.auth, 'authenticate', return_value=(user, {'id': 'session'})), \
             patch.object(voice_live.store, 'get', side_effect=get), \
             patch.object(voice_live.voice, 'credentials', return_value=('secret', 'voice', 'personal')), \
             patch.object(voice_live.projects, 'get', return_value=project), \
             patch.object(voice_live.projects, 'messages', side_effect=lambda _id: messages), \
             patch.object(voice_live.projects, 'dialogue', side_effect=dialogue), \
             patch.object(voice_live.store, 'all_of', return_value=[]), \
             patch.object(voice_live.projects, 'message',
                          side_effect=lambda *args, **kwargs: saved.append(args)), \
             patch.object(voice_live.gradbot.websocket, 'handle_session', side_effect=session):
            asyncio.run(voice_live.live_voice(socket, 'project'))
        self.assertEqual([(row[1], row[2]) for row in saved], [
            ('user', 'Merci'), ('assistant', 'Je vous en prie.')])

    def test_duplicate_does_not_release_first_session(self):
        socket = Socket()
        scoped = ('one', 'project')
        voice_live.ACTIVE.add(scoped)
        try:
            with patch.object(voice_live.auth, 'authenticate',
                              return_value=({'id': 'one'}, {'id': 'session'})), \
                 patch.object(voice_live.store, 'get',
                              return_value={'owner_id': 'one'}):
                asyncio.run(voice_live.live_voice(socket, 'project'))
            self.assertEqual(socket.closed, 4409)
            self.assertIn(scoped, voice_live.ACTIVE)
        finally:
            voice_live.ACTIVE.discard(scoped)

    def test_home_voice_can_create_project_then_save_transcript(self):
        socket = Socket()
        user = {'id': 'one'}
        brain = {'id': 'agent', 'engine': 'direct', 'provider': 'ollama',
                 'model': 'test-model', 'active': True}
        saved = []
        dialogue_inputs = []

        class Handle:
            name = 'lancer_mission'
            args = {'demande': 'Crée un projet Physique quantique'}
            result = None

            async def send_json(self, value):
                self.result = value

        async def session(websocket, **options):
            config = options['on_start']({'type': 'start'})
            self.assertIn('Aucun projet ouvert', config.instructions)
            await websocket.send_json({'type': 'user_text',
                                       'text': 'Crée un projet Physique quantique',
                                       'turn_idx': 0})
            handle = Handle()
            await options['on_tool_call'](handle, None, websocket)
            self.assertEqual(handle.result['command'], 'create')
            await websocket.send_json({'type': 'agent_text',
                                       'text': 'Projet créé.', 'turn_idx': 0})

        def dialogue(body):
            dialogue_inputs.append(body)
            return {'project_id': 'new-project', 'command': 'create',
                    'run': None, 'notice': 'Projet créé.'}

        def all_of(kind):
            return [brain] if kind == 'agent' else []

        with patch.object(voice_live.auth, 'authenticate', return_value=(user, {'id': 'session'})), \
             patch.object(voice_live.store, 'all_of', side_effect=all_of), \
             patch.object(voice_live.codex_brain, 'configured', return_value=True), \
             patch.object(voice_live, 'voice_model', return_value='gpt-6-luna'), \
             patch.object(voice_live.voice, 'credentials', return_value=('secret', 'voice', 'personal')), \
             patch.object(voice_live.projects, 'messages', return_value=[]), \
             patch.object(voice_live.projects, 'dialogue', side_effect=dialogue), \
             patch.object(voice_live.projects, 'message',
                          side_effect=lambda *args, **kwargs: saved.append(args)), \
             patch.object(voice_live.gradbot.websocket, 'handle_session', side_effect=session):
            asyncio.run(voice_live.live_voice(socket))
        self.assertEqual(dialogue_inputs[0].project_id, None)
        self.assertEqual([row['project_id'] for row in socket.sent
                          if row.get('type') == 'project_update'], ['new-project'])
        self.assertEqual([(row[0], row[1], row[2]) for row in saved], [
            ('new-project', 'user', 'Crée un projet Physique quantique'),
            ('new-project', 'assistant', 'Projet créé.')])

    def test_marguerite_voice_uses_guide_conversation_and_keeps_plan_for_screen_review(self):
        socket = Socket('https://passage.example.test')
        socket.url = SimpleNamespace(netloc='passage.example.test', port=443)
        user = {'id': 'one'}
        project = {'id': 'project', 'owner_id': 'one'}
        calls = []

        class Handle:
            name = 'parler_a_marguerite'
            def __init__(self, phrase):
                self.args = {'demande': phrase}
                self.result = None
            async def send_json(self, value):
                self.result = value
            async def send_error(self, value):
                raise AssertionError(value)

        def converse(body):
            calls.append(body)
            return {'message': {'text': 'Voici les étapes.'},
                    'plan': {'id': 'gp_1'} if len(calls) == 2 else None}

        async def session(websocket, **options):
            config = options['on_start']({'type': 'start'})
            self.assertIn('Marguerite', config.instructions)
            self.assertEqual(options['run_kwargs']['llm_base_url'],
                             'http://127.0.0.1:10000/internal/voice-codex/v1')
            self.assertEqual(config.tools[0].name, 'parler_a_marguerite')
            for index, phrase in enumerate(['Bonjour.', 'Prépare mon protocole.']):
                await websocket.send_json({'type': 'user_text', 'text': phrase,
                                           'turn_idx': index})
                handle = Handle(phrase)
                await options['on_tool_call'](handle, None, websocket)
                self.assertIn('Voici les étapes.', handle.result['answer'])
                self.assertEqual(handle.result['plan_pending'], index == 1)
            self.assertEqual([row['plan_pending'] for row in websocket.sent
                              if row.get('type') == 'guide_update'], [False, True])

        with patch.dict(voice_live.os.environ, {'PORT': '10000'}), \
             patch.object(voice_live.auth, 'authenticate', return_value=(user, {'id': 'session'})), \
             patch.object(voice_live.store, 'get', return_value=project), \
             patch.object(voice_live.voice, 'credentials', return_value=('secret', 'voice', 'personal')), \
             patch.object(voice_live.codex_brain, 'configured', return_value=True), \
             patch.object(voice_live, 'voice_model', return_value='gpt-6-luna'), \
             patch.object(voice_live.guide, 'converse', side_effect=converse), \
             patch.object(voice_live.projects, 'dialogue', side_effect=AssertionError('Wrong agent')), \
             patch.object(voice_live.gradbot.websocket, 'handle_session', side_effect=session):
            asyncio.run(voice_live.marguerite_voice(socket, 'project'))
        self.assertEqual([(body.text, body.project_id, body.view) for body in calls], [
            ('Bonjour.', 'project', 'voice'),
            ('Prépare mon protocole.', 'project', 'voice')])
        self.assertFalse(voice_live.ACTIVE)


if __name__ == '__main__':
    unittest.main()
