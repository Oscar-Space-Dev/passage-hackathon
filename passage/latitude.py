"""Optional metadata-only OTLP export to a self-hosted Latitude ingest service."""
import secrets
from datetime import datetime
from urllib.parse import urlparse

import requests

from . import integrations


def configured():
    url = integrations.env('LATITUDE_INGEST_URL').rstrip('/')
    slug = integrations.env('LATITUDE_PROJECT_SLUG')
    key = integrations.env('LATITUDE_API_KEY')
    if integrations.env('LATITUDE_ENABLED') != 'on' or not (url and slug and key):
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return None
    return url, slug, key


def _nanos(iso):
    return str(int(datetime.fromisoformat(iso).timestamp() * 1_000_000_000))


def _attribute(name, value):
    return {'key': name, 'value': {'stringValue': str(value)}}


def export_run(run):
    config = configured()
    if not config:
        return False
    url, slug, key = config
    attrs = [_attribute('passage.run.id', run['id']),
             _attribute('passage.run.kind', run['kind']),
             _attribute('passage.run.status', run['status'])]
    for field in ('project_id', 'work_id', 'diagram_id', 'agent_id'):
        if run.get(field):
            attrs.append(_attribute('passage.'+field, run[field]))
    agent = run.get('agent_snapshot') or {}
    provider = run.get('provider') or agent.get('provider')
    model = run.get('model') or agent.get('model')
    if provider and model:
        attrs += [_attribute('gen_ai.provider.name', provider),
                  _attribute('gen_ai.request.model', model),
                  _attribute('gen_ai.operation.name', 'chat')]
    # No prompt, response, file contents, secrets, names, or user identity leave Passage.
    span = {
        'traceId': secrets.token_hex(16), 'spanId': secrets.token_hex(8),
        'name': 'passage.'+run['kind'], 'kind': 1,
        'startTimeUnixNano': _nanos(run['created_at']),
        'endTimeUnixNano': _nanos(run['ended_at']),
        'attributes': attrs,
        'status': {'code': 1 if run['status'] == 'succeeded' else 2},
    }
    request = {'resourceSpans': [{'resource': {'attributes': [
        _attribute('service.name', 'passage'), _attribute('service.version', 'poc')]},
        'scopeSpans': [{'scope': {'name': 'passage.jobs'}, 'spans': [span]}]}]}
    response = requests.post(url+'/v1/traces', json=request, headers={
        'Authorization': 'Bearer '+key, 'X-Latitude-Project': slug,
        'Content-Type': 'application/json'}, timeout=(2, 4))
    if response.status_code != 202:
        raise integrations.IntegrationError('Latitude ingest HTTP '+str(response.status_code))
    return True
