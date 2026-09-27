"""Local Gradbot protocol adapter, with Codex replaced by a deterministic fake."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from passage import voice_codex


class CodexVoiceAdapterTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(voice_codex.router)
        self.client = TestClient(app)
        self.token = voice_codex.register('owner', 'codex-test')
        self.url = '/internal/voice-codex/v1/chat/completions'
        self.headers = {'Authorization': 'Bearer ' + self.token}

    def tearDown(self):
        voice_codex.revoke(self.token)

    def test_answer_and_revoked_token(self):
        fake = SimpleNamespace(complete=lambda *args: (
            {'action': 'answer', 'answer': 'Bonjour.', 'tool_name': '',
             'arguments_json': '{}'}, {}))
        with patch.object(voice_codex.codex_brain, 'client', return_value=fake):
            result = self.client.post(self.url, headers=self.headers, json={
                'model': 'codex-test', 'messages': [{'role': 'user', 'content': 'Bonjour'}],
                'stream': False})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['choices'][0]['message']['content'], 'Bonjour.')
        voice_codex.revoke(self.token)
        self.assertEqual(self.client.post(self.url, headers=self.headers,
            json={'model': 'codex-test', 'messages': []}).status_code, 401)

    def test_streamed_tool_call_is_limited_to_declared_tool(self):
        def complete(*args):
            self.assertEqual(args[0], 'codex-test')
            return {'action': 'tool', 'answer': '', 'tool_name': 'lancer_mission',
                    'arguments_json': '{"demande":"statut"}'}, {}
        fake = SimpleNamespace(complete=complete)
        with patch.object(voice_codex.codex_brain, 'client', return_value=fake):
            result = self.client.post(self.url, headers=self.headers, json={
                'model': 'codex-test', 'messages': [{'role': 'user', 'content': 'statut'}],
                'tools': [{'type': 'function', 'function': {'name': 'lancer_mission',
                    'parameters': {'type': 'object'}}}], 'stream': True})
        self.assertEqual(result.status_code, 200)
        chunks = [json.loads(line[6:]) for line in result.text.splitlines()
                  if line.startswith('data: ')]
        self.assertEqual(chunks[0]['choices'][0]['delta']['tool_calls'][0]
                         ['function']['name'], 'lancer_mission')
        self.assertEqual(chunks[-1]['choices'][0]['finish_reason'], 'tool_calls')

    def test_wrong_model_rejected(self):
        result = self.client.post(self.url, headers=self.headers,
            json={'model': 'other', 'messages': []})
        self.assertEqual(result.status_code, 422)

    def test_guide_voice_routes_every_utterance_to_marguerite_and_reads_her_result(self):
        token = voice_codex.register('owner', 'codex-test', mode='guide')
        headers = {'Authorization': 'Bearer ' + token}
        tools = [{'type': 'function', 'function': {'name': 'parler_a_marguerite',
            'parameters': {'type': 'object'}}}]
        try:
            with patch.object(voice_codex.codex_brain, 'client') as client:
                first = self.client.post(self.url, headers=headers, json={
                    'model': 'codex-test', 'messages': [{'role': 'user',
                    'content': 'Prépare mon protocole.'}], 'tools': tools})
                assert first.status_code == 200, first.text
                call = first.json()['choices'][0]['message']['tool_calls'][0]['function']
                self.assertEqual(call['name'], 'parler_a_marguerite')
                self.assertEqual(json.loads(call['arguments']), {'demande': 'Prépare mon protocole.'})
                second = self.client.post(self.url, headers=headers, json={
                    'model': 'codex-test', 'messages': [
                        {'role': 'user', 'content': 'Prépare mon protocole.'},
                        {'role': 'tool', 'content': json.dumps({'answer': 'Voici le plan à valider.'})}],
                    'tools': tools})
                self.assertEqual(second.status_code, 200)
                self.assertEqual(second.json()['choices'][0]['message']['content'],
                                 'Voici le plan à valider.')
                client.assert_not_called()
        finally:
            voice_codex.revoke(token)


if __name__ == '__main__':
    unittest.main()
