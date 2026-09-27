import threading
import pytest
from passage import codex_brain, integrations


@pytest.mark.parametrize('error', [{'code':'disconnected'}, {'message':''}, {'message':None}])
def test_disconnect_without_message_returns_handled_error(error):
    client = codex_brain.CodexClient.__new__(codex_brain.CodexClient)
    client.io_lock = threading.RLock()
    client.sequence = 0
    client.pending = {}
    client.send = lambda message: client.pending[message['id']].put({'error':error})
    with pytest.raises(integrations.IntegrationError, match='interrompu'):
        client.request('initialize')
    assert client.pending == {}
