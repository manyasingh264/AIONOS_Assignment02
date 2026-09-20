# Project Overview - Internal IT Support Agent

## Problem Statement

IT support teams face significant challenges in handling employee requests efficiently:

- **Volume Overload**: Teams are overwhelmed with repetitive, policy-based requests that could be automated
- **Response Time**: Employees experience delays in getting accurate, policy-compliant responses
- **Inconsistency**: Different agents may apply company policies inconsistently
- **Security Risks**: Improper handling of security incidents can expose the organization to threats
- **Lack of Transparency**: No clear audit trail for support decisions and escalations

**Impact**: These issues result in delayed resolution times, potential policy violations, security risks, and frustrated employees.

## Solution Overview

### AI-Powered Internal IT Support Agent

A deterministic AI agent that processes employee IT support requests using grounded knowledge base policies.

### Key Features

- **Natural Language Understanding**: Interprets employee IT issues in plain language
- **Grounded Decision Making**: Uses only supplied company policies (no hallucination)
- **Deterministic Escalation**: Follows predefined workflows for security and approval processes
- **Complete Audit Trail**: Logs all actions with timestamps for accountability
- **Source Attribution**: Cites specific policies used for each decision
- **Multi-turn Conversations**: Handles follow-up questions and clarifications

### Benefits

- **Immediate Response**: Common requests resolved instantly without human intervention
- **Consistent Policy Application**: Ensures uniform application of company policies
- **Proper Security Handling**: Security incidents escalated immediately per policy
- **Transparent Process**: Clear decision rationale and audit trail for all actions

## Technical Architecture

### Technology Stack

**Backend:**
- Python 3.9+
- FastAPI (REST API framework)
- Pydantic (Data validation)
- Groq SDK (LLM integration)
- python-dotenv (Environment management)

**Frontend:**
- React 18
- Vite (Build tool)
- Tailwind CSS (Styling)
- Lucide React (Icons)

**Data Storage:**
- Local JSON files (policies, requests, tickets)

**LLM Integration:**
- Groq API with Llama 3 models
- System prompts for grounding enforcement
- Graceful fallback on API failure

### System Architecture

```
React Frontend → FastAPI Backend → Policy Engine
                                    ↓
                            Local JSON Data
                                    ↓
                            Groq LLM (Intent/Response)
```

### Design Decisions

- **Monolithic Architecture**: Simplified deployment for assignment scope
- **Local Data Storage**: Reliable access without external dependencies
- **No Vector Database**: Policy corpus is small enough for keyword matching
- **Deterministic Policy Enforcement**: Business logic in code, not LLM
- **Hybrid Approach**: LLM for NLU, application code for decisions

## Agent Workflow

### Processing Pipeline

```
1. Employee Message Input
       ↓
2. Intent Classification (LLM)
       ↓
3. Structured Intent Extraction
       ↓
4. Deterministic Policy Retrieval (Keyword/Category Matching)
       ↓
5. Policy Evaluation (Business Rules)
       ↓
6. Decision Classification:
   - RESOLVE (Direct resolution)
   - CLARIFY (Ask for more information)
   - ESCALATE (Security/complex issues)
   - ROUTE (Approval workflows)
       ↓
7. Response Generation (LLM)
       ↓
8. Audit Logging + Ticket Creation (if needed)
       ↓
9. Structured Response Delivery
```

### Hybrid Approach

- **LLM Responsibilities**: Natural language understanding, response generation
- **Application Code**: Policy enforcement, business rules, decision logic
- **Deterministic Retrieval**: Policy search via keyword matching
- **Structured Decisions**: Reliable, auditable decision process

## Knowledge Base & Grounding

### Strict Grounding Rule

**Use ONLY supplied material as source data. Never invent:**
- Company policies
- Approval requirements
- Department ownership
- SLA timelines
- Employee details
- Security procedures

### Data Sources

**Knowledge Base Policies:**
- KB-01: Password Reset
- KB-02: VPN Access
- KB-03: Laptop Replacement
- KB-04: Software Installation Requests
- KB-05: Printer Troubleshooting
- KB-06: Email Mailbox Quota
- KB-07: Guest Wi-Fi Access
- KB-08: Expense Software Access
- KB-09: Security Incident Reporting
- KB-10: Work-From-Home Equipment
- ASSET-01: Asset Management Policy

**Employee Requests:** 15 sample requests (REQ-01 through REQ-15)

**Ticket Queue:** 10 existing tickets (TK-1042 through TK-1051)

### Guardrails Implementation

When information is insufficient:
1. State that knowledge base lacks information
2. Ask for clarification if appropriate
3. Otherwise escalate to human

**Ticket Status Rules:**
- Active tickets are actionable
- Closed tickets are historical only
- Never treat closed tickets as active

## Decision Classification System

### Decision Types

**1. RESOLVE**
- Direct policy-based resolution
- No ticket creation
- Immediate response to employee

**2. CLARIFY**
- Ask for missing information
- No ticket creation
- Awaits employee response

**3. ESCALATE**
- Security incidents or complex issues
- Ticket creation required
- Route to appropriate team

**4. ROUTE**
- Approval workflows required
- Ticket creation required
- Route to approver (Manager, Finance, etc.)

### Decision Tree Examples

```
Security Incident (phishing, malware, unauthorized)
└── ESCALATE → Security (KB-09)

Guest Wi-Fi Request
└── RESOLVE → Front-desk kiosk (KB-07)

Password Issue
├── ≥5 failed attempts → ESCALATE → IT (KB-01)
└── <5 attempts → RESOLVE → Self-service (KB-01)

VPN Issue
├── Contractor → ROUTE → Manager approval (KB-02)
├── Expired credentials → RESOLVE → Renew (KB-02)
└── General → RESOLVE → Automatic for FTE (KB-02)

Laptop Issue
├── ≥3 years + failure → ROUTE → IT + Finance (KB-03, ASSET-01)
├── <3 years + failure → ROUTE → IT diagnostic (KB-03, ASSET-01)
└── Age/failure unknown → CLARIFY

Software Installation
├── Non-catalog → ESCALATE → IT Security (KB-04)
├── Catalog → RESOLVE → Self-install (KB-04)
└── Unknown → CLARIFY
```

## Agent Capabilities

### Automated Actions

- **Policy Retrieval**: Keyword and category matching from knowledge base
- **Ticket Creation**: Structured ticket generation for escalations
- **Audit Trail**: Complete logging of all system events
- **Source Attribution**: Clear citation of policies used in decisions
- **Conversation Management**: Multi-turn context and state tracking

### Safety Features

- **No Chain-of-Thought Exposure**: Internal reasoning not shared with users
- **Graceful LLM Failure**: Fallback to pre-written responses on API failure
- **Input Validation**: Pydantic models enforce data integrity
- **Security Escalation**: Immediate routing for security incidents
- **Grounding Enforcement**: Strict adherence to supplied policies

### Message Classification

The agent classifies incoming messages to handle different conversation contexts:

- **NEW_ISSUE**: New IT support request
- **FOLLOW_UP**: Follow-up question on current issue
- **CLARIFICATION_RESPONSE**: Answer to previous clarification
- **ACKNOWLEDGEMENT**: User acknowledgment of previous response
- **CORRECTION**: User correction of previous information
- **HUMAN_HANDOFF_REQUEST**: Request to speak with human agent
- **MULTI_INTENT**: Multiple issues in single message
- **OUT_OF_SCOPE**: Query outside IT support scope
- **POLICY_INFO_QUESTION**: Question about policy details

## Testing & Validation

### Test Coverage

All 15 employee requests from the assignment were tested:

1. **REQ-01**: Laptop replacement (3.5 years, dead) → ROUTE
2. **REQ-02**: Guest Wi-Fi access → RESOLVE
3. **REQ-03**: Account lockout (6 attempts) → ESCALATE
4. **REQ-04**: Non-catalog software → ESCALATE
5. **REQ-05**: Expired VPN credentials → RESOLVE
6. **REQ-06**: Printer troubleshooting → ROUTE
7. **REQ-07**: Home office equipment (4 days/week) → ROUTE
8. **REQ-08**: Phishing email → ESCALATE
9. **REQ-09**: Mailbox quota full → RESOLVE
10. **REQ-10**: Admin access request (no policy) → ESCALATE
11. **REQ-11**: Contractor VPN → ROUTE
12. **REQ-12**: Expense software login → ROUTE
13. **REQ-13**: Laptop flickering (2 years) → ROUTE
14. **REQ-14**: Browser extension (unknown catalog) → CLARIFY
15. **REQ-15**: Vague request → CLARIFY

### Validation Criteria

- **Policy Identification**: Correct matching of relevant policies
- **Decision Classification**: Accurate RESOLVE/CLARIFY/ESCALATE/ROUTE decisions
- **Escalation Behavior**: Proper security incident handling
- **Clarification Triggers**: Appropriate requests for missing information
- **Source Attribution**: Clear policy citations
- **No Hallucination**: Strict adherence to supplied policies

### Test Results

- **15/15 requests** correctly processed
- **All policies** properly matched and cited
- **Security incidents** properly escalated per KB-09
- **Approval workflows** respected (manager/finance)
- **Vague requests** trigger clarification appropriately
- **Unknown policies** escalated without invention

### Edge Cases Handled

- **Closed vs Active Tickets**: Proper distinction in escalation logic
- **LLM Failure**: Graceful degradation to pre-written responses
- **Missing Information**: Clarification requests before escalation
- **Unknown Policies**: Escalation without policy invention
- **Multi-turn Conversations**: Context retention across messages

## Implementation Details

### API Endpoints

- `POST /api/chat` - Process employee message
- `GET /api/policies` - Retrieve all policies
- `GET /api/requests` - Get all employee requests
- `GET /api/tickets` - Get all tickets (original and generated)
- `POST /api/tickets` - Create manual ticket
- `GET /api/health` - Health check
- `DELETE /api/sessions/{session_id}` - Clear conversation session
- `GET /api/sessions/{session_id}` - Get conversation state

### Component Architecture

**Agent Orchestrator (`agent.py`):**
- Coordinates all system components
- Manages conversation flow and state
- Integrates LLM for response generation
- Handles errors gracefully

**Policy Engine (`policy_engine.py`):**
- Deterministic policy evaluation
- Business rule enforcement
- Decision classification logic
- No LLM decision-making

**Retrieval System (`retrieval.py`):**
- Policy search via keyword matching
- Employee request lookup
- Ticket search (active/historical)
- Data loading from JSON files

**Ticket Manager (`ticket_manager.py`):**
- Ticket creation and ID generation
- Status management
- Local storage of generated tickets

**Audit Logger (`audit.py`):**
- Event logging with timestamps
- Activity trace generation
- Complete audit trail

**Conversation Manager (`conversation_manager.py`):**
- Multi-turn conversation state
- Message classification
- Context retention
- Session management

### Data Models

**Policy:** KB-ID, title, content, category, keywords
**Employee Request:** REQ-ID, employee, email, date, request, initial_action
**Ticket:** TK-ID, employee, issue, status, is_active
**Agent Decision:** intent, decision, policy_ids, reason, recommended_action, escalation details
**Generated Ticket:** ticket_id, employee, category, issue, priority, source, destination, status, created_at

## Current Limitations

### Technical Constraints

- **Single-Session Only**: No persistent conversation history across sessions
- **No User Authentication**: No user identification or authorization
- **Local Data Storage**: In-memory storage, lost on server restart
- **Limited Knowledge Base**: Restricted to supplied policies only
- **No External Integrations**: No email, ITSM, or external system connections
- **Single-Instance Deployment**: No horizontal scaling capability

### Scope Limitations

These limitations are acceptable for the assignment scope and demo requirements:
- Time-constrained development (6 hours)
- Focus on core functionality over production features
- Demonstration of key concepts over completeness
- Single-user demo scenarios

## Future Improvements

### Potential Enhancements

**Persistence & Scalability:**
- Database integration (PostgreSQL, MongoDB)
- Persistent conversation history
- Horizontal scaling capabilities
- Load balancing and high availability

**Security & Authentication:**
- User authentication and authorization
- Role-based access control
- Enhanced security measures
- Compliance features

**Integration & Expansion:**
- Real ITSM system integration (ServiceNow, Jira)
- Email notification system
- Expanded knowledge base
- Multi-language support
- Mobile application

**Advanced Features:**
- Machine learning for intent classification
- Analytics and reporting dashboard
- Self-service portal integration
- Voice/chatbot interfaces

### Assignment Success Criteria

**✅ Completed Requirements:**
- Correct policy grounding (no hallucination)
- Deterministic decision making
- Proper escalation workflows
- Complete audit trail
- Evaluator-friendly UI
- All 15 requests tested and validated
- Demo scenarios working correctly
- Architecture documentation
- AI tools usage documentation

## Conclusion

The Internal IT Support Agent successfully demonstrates the application of agentic AI principles to a real-world business problem. The hybrid approach—combining LLM natural language understanding with deterministic business logic—provides reliable, grounded decision-making while maintaining conversational capabilities.

The strict adherence to supplied policies ensures consistency and compliance, while the comprehensive audit trail provides transparency and accountability. The system effectively handles the range of IT support scenarios from simple resolutions to complex security escalations, meeting all assignment requirements within the constrained development timeframe.