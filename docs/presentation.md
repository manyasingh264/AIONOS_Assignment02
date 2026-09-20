# Presentation Content - Internal IT Support Agent

## Slide 1: Title

**Internal IT Support Agent**
**AI-Powered IT Support for Veridian Corp**

Agentic AI Factory — Assignment 2

---

## Slide 2: Problem

**The Challenge**
- IT support teams overwhelmed with repetitive requests
- Employees need quick, accurate policy-based responses
- Complex/security-sensitive issues require proper escalation
- Inconsistent application of company policies
- Lack of audit trail for support decisions

**Impact**
- Delayed resolution times
- Policy violations
- Security risks from improper handling
- Frustrated employees

---

## Slide 3: Solution

**AI-Powered Internal IT Support Agent**

**Key Features:**
- Natural language understanding of IT requests
- Grounded policy-based decision making
- Deterministic escalation workflows
- Complete audit trail
- Source attribution for all decisions
- No policy hallucination

**Benefits:**
- Immediate response to common requests
- Consistent policy application
- Proper security incident handling
- Transparent decision process

---

## Slide 4: Agent Workflow

```
Employee Message
       ↓
Intent Classification (LLM)
       ↓
Policy Retrieval (Deterministic)
       ↓
Policy Evaluation (Business Rules)
       ↓
Decision: RESOLVE | CLARIFY | ESCALATE | ROUTE
       ↓
Response Generation (LLM)
       ↓
Audit Logging + Ticket Creation
```

**Hybrid Approach:**
- LLM for natural language understanding
- Application code for policy enforcement
- Deterministic retrieval for accuracy
- Structured decisions for reliability

---

## Slide 5: Architecture

**Tech Stack:**
- **Backend:** Python, FastAPI, Pydantic, Groq SDK
- **Frontend:** React, Vite, Tailwind CSS
- **Data:** Local JSON files
- **LLM:** Groq API

**Architecture Pattern:**
```
React Frontend → FastAPI Backend → Policy Engine
                                    ↓
                            Local JSON Data
                                    ↓
                            Groq LLM (Intent/Response)
```

**Key Design Decisions:**
- Monolithic for simplicity
- Local data for reliability
- No vector database (small policy corpus)
- Deterministic policy enforcement

---

## Slide 6: Knowledge/Policy Grounding

**Strict Grounding Rule:**
Use ONLY supplied material as source data

**Data Sources:**
- 10 Knowledge Base Policies (KB-01 through KB-10)
- Asset Management Policy
- 15 Employee Requests (REQ-01 through REQ-15)
- 10 Existing Tickets (TK-1042 through TK-1051)

**Guardrails:**
- Never invent company policies
- Never invent approval requirements
- Never invent department ownership
- Never invent timelines
- State when information is insufficient

**Ticket Status Rules:**
- Active tickets = actionable
- Closed tickets = historical only

---

## Slide 7: Key Agent Capabilities

**Decision Types:**
1. **RESOLVE** - Direct policy-based resolution
2. **CLARIFY** - Ask for missing information
3. **ESCALATE** - Security incidents, complex issues
4. **ROUTE** - Approval workflows

**Automated Actions:**
- Policy retrieval via keyword matching
- Ticket creation for escalations
- Audit trail generation
- Source attribution

**Safety Features:**
- No chain-of-thought exposure
- Graceful LLM failure handling
- Input validation
- Security incident escalation

---

## Slide 8: Demo Scenarios

**Demo 1 - Direct Resolution:**
- Request: "Guest Wi-Fi access"
- Result: RESOLVE, KB-07, no ticket needed

**Demo 2 - Security Escalation:**
- Request: "Phishing email"
- Result: ESCALATE, KB-09, Security ticket created

**Demo 3 - Approval Workflow:**
- Request: "Contractor VPN access"
- Result: ROUTE, KB-02, manager approval required

**Demo 4 - Clarification:**
- Request: "Browser extension install"
- Result: CLARIFY, KB-04, catalog status unknown

**Demo 5 - Grounding:**
- Request: "Finance server admin access"
- Result: ESCALATE, no policy, not invented

---

## Slide 9: Testing & Results

**Test Coverage:**
- All 15 employee requests tested
- Policy identification verified
- Decision classification validated
- Escalation behavior confirmed
- Clarification triggers checked
- Source attribution verified
- No policy hallucination confirmed

**Test Results:**
- 15/15 requests correctly processed
- All policies properly matched
- Security incidents properly escalated
- Approval workflows respected
- Vague requests trigger clarification

**Edge Cases Handled:**
- Closed vs active ticket distinction
- LLM failure graceful degradation
- Missing information handling
- Unknown policy escalation

---

## Slide 10: Future Improvements & Limitations

**Current Limitations:**
- Single-session only (no persistence)
- No user authentication
- Local data storage only
- Limited to supplied knowledge base
- No external system integrations

**Future Improvements:**
- Persistent conversation history
- User authentication & authorization
- Database integration for scalability
- Expanded knowledge base
- Real ITSM system integration
- Multi-language support
- Mobile application

**Assignment Success:**
- ✓ Correct policy grounding
- ✓ Deterministic decision making
- ✓ Proper escalation workflows
- ✓ Complete audit trail
- ✓ Evaluator-friendly UI
- ✓ All 15 requests tested
- ✓ Demo scenarios working

---

## Backup Slides

### Additional Details

**Policies Implemented:**
- KB-01: Password Reset
- KB-02: VPN Access
- KB-03: Laptop Replacement
- KB-04: Software Installation
- KB-05: Printer Troubleshooting
- KB-06: Email Mailbox Quota
- KB-07: Guest Wi-Fi Access
- KB-08: Expense Software Access
- KB-09: Security Incident Reporting
- KB-10: Work-From-Home Equipment
- ASSET-01: Asset Management Policy

**API Endpoints:**
- POST /api/chat
- GET /api/policies
- GET /api/requests
- GET /api/tickets
- POST /api/tickets
- GET /api/health

**Setup Commands:**
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with GROQ_API_KEY
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
