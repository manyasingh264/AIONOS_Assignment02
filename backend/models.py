from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class Policy(BaseModel):
    id: str
    title: str
    content: str
    category: str
    keywords: List[str]


class EmployeeRequest(BaseModel):
    id: str
    employee: str
    email: str
    date_opened: str
    request: str
    initial_action: str


class Ticket(BaseModel):
    ticket_id: str
    employee: str
    issue: str
    status: str
    is_active: bool


class ChatRequest(BaseModel):
    message: str
    employee_id: Optional[str] = None
    session_id: Optional[str] = None


class AgentDecision(BaseModel):
    intent: str
    decision: Literal["RESOLVE", "CLARIFY", "ESCALATE", "ROUTE"]
    policy_ids: List[str] = []
    employee_request_id: Optional[str] = None
    ticket_ids: List[str] = []
    reason: str
    recommended_action: str
    escalation_required: bool = False
    escalation_destination: Optional[str] = None
    needs_clarification: bool = False
    response: str


class ChatResponse(BaseModel):
    response: str
    decision: str
    policy_sources: List[str] = []
    recommended_action: str
    ticket: Optional[dict] = None
    audit: List[dict] = []
    message_type: Optional[str] = None   # classification type for UI display


class AuditEvent(BaseModel):
    timestamp: str
    event_type: str
    details: str


class GeneratedTicket(BaseModel):
    ticket_id: str
    employee: str
    category: str
    issue: str
    priority: str
    source: str
    destination: Optional[str]
    status: str
    created_at: str


class ConversationState(BaseModel):
    session_id: str
    employee_id: Optional[str] = None
    current_issue: Optional[str] = None
    current_intent: Optional[str] = None
    current_policy_id: Optional[str] = None
    current_decision: Optional[str] = None
    current_ticket_id: Optional[str] = None
    pending_clarification: Optional[str] = None
    previous_agent_message: Optional[str] = None
    conversation_history: List[dict] = []
    # Track troubleshooting steps the user has already done (e.g. ["restart_spooler"])
    troubleshooting_steps_done: List[str] = []
    # Secondary issue for multi-intent conversations
    secondary_issue: Optional[str] = None
    # Whether we are in security incident context
    in_security_context: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class MessageClassification(BaseModel):
    message_type: Literal[
        "NEW_ISSUE",
        "FOLLOW_UP",
        "CLARIFICATION_RESPONSE",
        "ACKNOWLEDGEMENT",
        "CORRECTION",
        "HUMAN_HANDOFF_REQUEST",
        "MULTI_INTENT",
        "OUT_OF_SCOPE",
        "UNSUPPORTED_POLICY_QUERY",
        "POLICY_INFO_QUESTION",
        "TICKET_STATUS_QUERY",
        "ALREADY_TRIED",
    ]
    confidence: float
    context_update: Optional[dict] = None
