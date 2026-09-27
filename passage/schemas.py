from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Evidence(StrictModel):
    thesis_id: str
    quote: str

class Maturity(StrictModel):
    level: str
    rationale: str
    uncertainty: str

class Match(StrictModel):
    thesis_id: str
    score: int = Field(ge=0, le=100)
    reason: str
    demonstrated: list[str]
    checks: list[str]
    confidence: Literal['faible', 'moyenne', 'élevée']

class Report(StrictModel):
    summary: str
    fit: str
    demonstrated: list[str]
    checks: list[str]
    contacts: list[str]
    confidence: Literal['faible', 'moyenne', 'élevée']
    uncertainty: list[str]
    evidence: list[Evidence]
    maturity: Maturity
    rights: str
    verdict: Literal['favorable', 'à approfondir', 'défavorable', 'sans objet']
    application: str
    market: str
    competition: str
    steps: list[str]
    estimates: str
    matches: list[Match]

class AgentInput(StrictModel):
    name: str = Field(min_length=2, max_length=80)
    role: Literal['lecteur', 'opportunite', 'rapprochement', 'incorporation', 'research_task']
    mandate: str = Field(min_length=8, max_length=5000)
    skill: str = Field(min_length=10, max_length=16000)
    context: str = Field(default='', max_length=10000)
    memory: str = Field(default='', max_length=10000)
    creator_version: str = Field(default='', max_length=80)
    trigger: str = Field(default='', max_length=2000)
    reads: str = Field(default='', max_length=3000)
    boundaries: str = Field(default='', max_length=3000)
    checkpoint: str = Field(default='', max_length=3000)
    deliverables: str = Field(default='', max_length=3000)
    process: str = Field(default='', max_length=8000)
    workflow: str = Field(default='', max_length=8000)
    experience: str = Field(default='', max_length=8000)
    provider: Literal['openai', 'compatible', 'ollama', 'codex'] = 'codex'
    model: str = Field(default='auto', min_length=1, max_length=100)
    engine: Literal['direct', 'dust', 'pipelex'] = 'direct'
    tools: list[str] = Field(default_factory=lambda: ['theses.read'])
    work_specialties: list[str] = Field(default_factory=list, max_length=32)
    connector_ids: list[str] = Field(default_factory=list)
    method_ref: str = Field(default='', max_length=500)
    method_version: str = Field(default='1.0.0', max_length=50)
    max_steps: int = Field(default=3, ge=1, le=8)
    active: bool = True

class RunInput(StrictModel):
    project_id: str | None = None
    role: Literal['lecteur', 'opportunite', 'rapprochement', 'incorporation']
    thesis_id: str | None = None
    problem: str = Field(default='', max_length=6000)
    mode: Literal['demo', 'live'] = 'demo'
    agent_id: str | None = None
    question: str = Field(default='', max_length=4000)

class VisibilityInput(StrictModel):
    visible: bool

class CorrectionInput(StrictModel):
    summary: str = Field(min_length=10, max_length=10000)

class ImportInput(StrictModel):
    query: str = Field(default='LRCS Amiens', min_length=2, max_length=200)
    lab_filter: str = Field(default='Réactivité et Chimie des Solides', min_length=2, max_length=200)
    limit: int = Field(default=100, ge=1, le=200)

class ProposalInput(StrictModel):
    thesis_id: str
    programme_id: str
    report_id: str

class DecisionInput(StrictModel):
    decision: Literal['accepted', 'rejected']

class ProgrammeInput(StrictModel):
    name: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=6000)

class ConnectorInput(StrictModel):
    name: str = Field(min_length=2, max_length=80)
    url: str = Field(min_length=8, max_length=1000)
    allowed_tools: list[str] = Field(default_factory=list)
    secret_env: str = Field(default='', pattern=r'^[A-Z0-9_]*$')
    enabled: bool = False
