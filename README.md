# Internal IT Support Agent - Veridian Corp

An enterprise AI-powered IT Support Agent built for Veridian Corp to triage, resolve, route, and escalate employee IT requests. The agent operates under strict knowledge base grounding—combining deterministic rule enforcement and policy retrieval with LLM-powered natural language understanding and response formatting.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Key Features & Capabilities](#key-features--capabilities)
- [Architecture & Process Flow](#architecture--process-flow)
- [Tech Stack](#tech-stack)
- [Grounded Data Sources](#grounded-data-sources)
- [Decision Matrix & Guardrails](#decision-matrix--guardrails)
- [API Reference](#api-reference)
- [Setup & Running Locally](#setup--running-locally)
- [Automated Testing & Validation](#automated-testing--validation)
- [Demonstrated Test Scenarios](#demonstrated-test-scenarios)
- [Inputs, Sources & Assumptions](#inputs-sources--assumptions)
- [AI Tools Used](#ai-tools-used)
- [Repository Structure](#repository-structure)

---

## Project Overview

IT service desks often face a high volume of repetitive queries (Wi-Fi access, password/credential expiration, hardware eligibility) alongside critical security incidents (phishing, unauthorized access attempts).

The **Veridian Corp Internal Service Agent** provides an automated, audit-logged first line of support that:
1. **Never hallucinates company policy**: If an item is outside the knowledge base or requires elevated privileges, it escalates rather than guessing.
2. **Maintains multi-turn context**: Retains conversation history, recognizes follow-up questions, detects topic switches, and cleanly terminates conversations when resolved.
3. **Executes deterministic decision logic**: Enforces corporate business rules (approvals, security escalations, hardware replacement eligibility) deterministically.
4. **Provides full transparency**: Displays policy sources cited, confidence badges, routing classifications, and active ticket records in an enterprise dashboard.

---

## Key Features & Capabilities

- **Strict Knowledge Base Grounding**: Operates exclusively against approved Veridian policies (`KB-01` to `KB-10` and Hardware Refresh criteria). Zero ungrounded answers.
- **Intent Classification**: Evaluates user messages across 12 distinct types:
  - `NEW_ISSUE` — New technical problem or request
  - `FOLLOW_UP` — Clarifying or secondary question within existing context
  - `CLARIFICATION_RESPONSE` — Answering an agent question (e.g. catalog verification)
  - `ACKNOWLEDGEMENT` — Acknowledgement ("ok", "got it", "thanks")
  - `CONVERSATION_CLOSE` — Polite session termination ("no", "nope", "all good", "nothing else")
  - `ALREADY_TRIED` — User reports having already attempted troubleshooting steps
  - `TOPIC_SWITCH` — User transitions to a different problem mid-session
  - `MULTI_INTENT` — Messages containing multiple distinct IT issues
  - `HUMAN_HANDOFF_REQUEST` — Direct request to speak with a human engineer
  - `POLICY_INFO_QUESTION` — Informational query regarding policy details (e.g. credential lifespan)
  - `TICKET_STATUS_QUERY` — Status inquiries regarding existing tickets
  - `OUT_OF_SCOPE` — Unrelated questions (e.g. general knowledge, weather)
- **Multi-Turn Context & Session Memory**: Maintains conversational context across turns, persists security incident context (e.g., phishing alerts), and clears pending clarification states dynamically.
- **Conversation Termination Protection**: Gracefully closes out sessions when the user indicates they need no further assistance, preventing circular "How can I help you?" loops.
- **Automated Ticket Creation**: Generates structured tickets with priority scoring, assigned destination teams (e.g., `Security Operations`, `Tier 2 Support`), and full problem descriptions upon escalation.
- **Audit Logging**: Every action, policy retrieval, decision classification, and ticket event is tracked with ISO timestamps for governance.

---

## Architecture & Process Flow

```
                     ┌───────────────────────────────┐
                     │   Employee Message / Chat     │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │     Conversation Manager      │
                     │  - Multi-turn state tracking  │
                     │  - Intent & Close detection   │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │   Deterministic Retrieval     │
                     │  - Policy matching (KB-01..10)│
                     │  - Ticket queue lookup        │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │        Policy Engine          │
                     │  - Business rules evaluation  │
                     │  - Eligibility / Approval     │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │     Action Classification     │
                     ├───────────┬───────────┬───────┴───┬───────────┐
                     │  RESOLVE  │  CLARIFY  │  ESCALATE │   ROUTE   │
                     └─────┬─────┴─────┬─────┴─────┬─────┴─────┬─────┘
                           │           │           │           │
                           ▼           ▼           ▼           ▼
                     ┌───────────────────────────────────────────────┐
                     │   Ticket Manager (if ticket required)        │
                     │   Audit Logger (record full event trace)      │
                     └───────────────────────┬───────────────────────┘
                                             │
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │      Grounded Response Generation             │
                     │   (Grounded in KB text + clear attribution)   │
                     └───────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **Python 3.9+** with **FastAPI** — High-performance asynchronous REST API
- **Pydantic v1/v2** — Rigid data contracts and schema validation
- **Groq API (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`)** — Fast LLM inference with built-in graceful fallback mode
- **python-dotenv** — Environment configuration
- **Uvicorn** — Production-ready ASGI server

### Frontend
- **React 18** with **Vite** — Fast, responsive single-page application
- **Tailwind CSS** — Utility styling following enterprise design standards
- **Typography** — Google Fonts (`DM Sans` for body copy, `DM Mono` for metadata badges)
- **Custom UI Components** — Enterprise split-view layout with real-time Chat, Decision Badges, Cited Policy Sources, Ticket Cards, and Live Activity Audit Trail

---

## Grounded Data Sources

The agent is strictly grounded in the following structured internal assets located in `backend/data/`:

| Source File | Content | Description |
|:---|:---|:---|
| `policies.json` | 10 Knowledge Base Articles (`KB-01` – `KB-10`) | Password policy, VPN access, remote work hardware, software requests, printer support, mailbox quotas, guest Wi-Fi, incident reporting, security incidents, and mobile device management. Includes hardware refresh cycle rules (e.g. 3-year laptop replacement). |
| `tickets.json` | 10 Pre-existing Service Tickets (`TK-1042` – `TK-1051`) | Baseline ticket queue with statuses (`In Progress`, `Pending Approval`, `Resolved`, `Closed`). Closed tickets are treated strictly as historical references. |
| `employee_requests.json` | 15 Benchmark Employee Scenarios (`REQ-01` – `REQ-15`) | Representative employee inquiries across diverse IT operational categories. |

---

## Decision Matrix & Guardrails

### Decision Actions
- **`RESOLVE`**: The request is directly addressable using self-service KB instructions (e.g. Guest Wi-Fi kiosk, routine troubleshooting steps). No ticket is required.
- **`CLARIFY`**: Critical information is missing before an action can be taken (e.g. whether software is already in the approved catalog, device asset tag).
- **`ESCALATE`**: The issue represents a security incident (phishing, credential compromise), high severity hardware failure, ungrounded admin access request, or employee-requested human handoff. Creates a ticket assigned to the proper tier.
- **`ROUTE`**: The request requires formal manager approval or specialized submission workflows (e.g. contractor VPN access, unapproved software purchase).

### Strict Guardrails
1. **Zero Hallucination Policy**: If an employee requests access to systems not covered in policy (e.g. "Admin access to finance reporting server"), the agent explicitly acknowledges that no company policy covers it and escalates to IT Management without inventing approvals.
2. **Ticket Status Invariance**: Tickets marked `Closed` are permanently historical. Only `Open`, `In Progress`, or `Pending Approval` tickets can have actions performed.
3. **Looping Prevention**: When an employee acknowledges a resolution or indicates they are done ("no", "thank you, that is all"), the agent responds courteously and concludes the session rather than asking repetitive clarification questions.

---

## API Reference

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/chat` | Process an incoming employee message with multi-turn session awareness |
| `GET` | `/api/policies` | Retrieve all loaded knowledge base policies |
| `GET` | `/api/requests` | Retrieve sample employee request scenarios |
| `GET` | `/api/tickets` | Retrieve combined list of original and agent-generated tickets |
| `POST` | `/api/tickets` | Create a new ticket manually |
| `GET` | `/api/sessions/{session_id}` | Inspect conversation session state and message history |
| `DELETE` | `/api/sessions/{session_id}` | Reset / clear a conversation session to initial state |
| `GET` | `/api/health` | Health check verifying agent readiness and LLM connectivity |

---

## Setup & Running Locally

### Prerequisites
- Python 3.9+ installed
- Node.js 18+ and npm installed
- Groq API Key (optional, agent runs in rule-based fallback mode if not provided)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env and configure your key
# In backend/.env:
GROQ_API_KEY=gsk_your_actual_groq_api_key_here

# Start the backend server
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs at `http://localhost:8000` (Swagger docs available at `http://localhost:8000/docs`).*

### 2. Frontend Setup

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
*Frontend runs at `http://localhost:5173`.*

---

## Automated Testing & Validation

The backend includes a comprehensive automated test suite validating multi-turn conversations, policy citations, decision types, ticket generation, and guardrails across 12 distinct scenarios with **21 assertion checks**.

### Running the Test Suite:

```bash
cd backend
python run_tests.py
```

### Test Suite Coverage (21 / 21 Passing):
- **Test 1 — Direct Resolution (`RESOLVE`)**: Guest Wi-Fi query references `KB-07`, resolves without opening an unnecessary ticket.
- **Test 2 — Security Incident & Multi-turn Context (`ESCALATE`)**:
  - Initial phishing report triggers high-priority ticket under `KB-09`.
  - Acknowledgement turn ("ok") classified properly.
  - Follow-up query ("What do I do now?") retains security context.
  - "I already forwarded it to my colleague" retains `KB-09` security context without losing grounding.
- **Test 3 — Follow-Up & Renewals (`FOLLOW_UP`)**: VPN expiration questions maintain `KB-02` context.
- **Test 4 — Troubleshooting Steps (`ALREADY_TRIED`)**: User already restarted spooler; agent requests hardware asset tag.
- **Test 5 — Clarification Loop (`CLARIFICATION_RESPONSE`)**: Browser extension verified in approved catalog transitions to `RESOLVE`.
- **Test 6 — Mid-Session Topic Switching (`TOPIC_SWITCH`)**: Transitioning from VPN to printer immediately shifts context to `KB-05`.
- **Test 7 — Ungrounded Admin Access Guardrail (`ESCALATE`)**: Finance server admin access correctly identifies absence of policy, creates escalation without hallucinated approval chains.
- **Test 8 — Multi-Intent Triage (`MULTI_INTENT`)**: Joint VPN and full mailbox message correctly identifies and addresses both `KB-02` and `KB-06`.
- **Test 9 — Human Handoff (`HUMAN_HANDOFF_REQUEST`)**: Direct request to speak with a human creates a Tier 2 support ticket.
- **Test 10 — Out of Scope Guardrail (`OUT_OF_SCOPE`)**: General questions (e.g. weather) are politely rejected without ticket creation.
- **Test 11 — Policy Detail Inquiry (`POLICY_INFO_QUESTION`)**: Inquiring about VPN credential duration cites `KB-02` and retrieves the exact 90-day expiration figure.
- **Test 12 — Ticket Status Inquiry (`TICKET_STATUS_QUERY`)**: Status inquiry for laptop replacement retrieves `TK-1043` status from the ticket queue.

---

## Demonstrated Test Scenarios

| Scenario | User Input | Action | Policy | Outcome |
|:---|:---|:---|:---|:---|
| **Guest Wi-Fi** | *"Can I get Wi-Fi access for a guest visiting our office tomorrow?"* | `RESOLVE` | `KB-07` | Self-service kiosk instructions provided; no ticket. |
| **Phishing Email** | *"I think I got a phishing email asking for my login"* | `ESCALATE` | `KB-09` | High priority security ticket created; isolation advice. |
| **Contractor Access** | *"New contractor joining my team next week, they'll need VPN access"* | `ROUTE` | `KB-02` | Routed to formal manager approval workflow. |
| **Catalog Check** | *"Requesting approval to install a browser extension for productivity tracking"* | `CLARIFY` | `KB-04` | Asks if extension is on the approved software catalog. |
| **Ungrounded Privilege**| *"Can someone give me admin access to the finance reporting server?"* | `ESCALATE` | None | Stated as ungrounded; escalated to IT Management. |
| **Ticket Lookup** | *"What is the status of my laptop replacement?"* | `RESOLVE` | None | Returns status for existing ticket `TK-1043`. |

---

## Inputs, Sources & Assumptions

### Inputs & Sources:
- **Corporate Policies**: 10 knowledge base articles (`policies.json`) defining operational rules for authentication, networking, hardware, software, printing, email, and security.
- **Service Ticket Queue**: 10 baseline tickets (`tickets.json`) reflecting active and closed service records.
- **Employee Persona Queries**: 15 standard inquiries (`employee_requests.json`) representing common tier 1 and tier 2 support interactions.

### Assumptions:
- **Security Priority**: Security-related requests (phishing, malware, suspicious links) supersede regular IT requests and immediately escalate to Security Operations.
- **Session Lifecycles**: Each browser session generates a unique `session_id` stored in-memory during server runtime, clearable on-demand via `DELETE /api/sessions/{session_id}`.
- **Deterministic Priority**: When LLM output conflicts with hardcoded policy rules, the deterministic policy engine takes precedence to guarantee compliance.

---

## AI Tools Used

In accordance with project guidelines, the following AI tools were utilized:
1. **Groq LLM (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`)**:
   - Primary natural language processing engine for classifying nuanced user intents and translating structured decision parameters into professional, user-friendly responses.
   - Operated with system prompts enforcing policy grounding and preventing hallucination.
2. **Antigravity AI Assistant**:
   - Used for interactive test-driven development (TDD), writing the 21-check automated test harness, identifying edge cases (stale clarification prompts, multi-turn context retention), and engineering the enterprise frontend interface.

---

## Repository Structure

```
Internal Service Agent/
├── backend/
│   ├── data/
│   │   ├── policies.json           # 10 company IT knowledge base policies
│   │   ├── tickets.json            # 10 baseline IT support tickets
│   │   └── employee_requests.json  # 15 benchmark employee requests
│   ├── agent.py                    # Main agent orchestrator (ITSupportAgent)
│   ├── conversation_manager.py     # Multi-turn state, intent classification & closing
│   ├── policy_engine.py            # Deterministic policy rules and decision logic
│   ├── retrieval.py                # Keyword and category retrieval system
│   ├── ticket_manager.py           # Ticket generator & queue manager
│   ├── audit.py                    # Audit trail logger
│   ├── models.py                   # Pydantic data schemas & response contracts
│   ├── main.py                     # FastAPI REST server & session routes
│   ├── run_tests.py                # Automated 21-check test suite
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.jsx            # Multi-turn chat interface with message bubbles
│   │   │   ├── DecisionCard.jsx    # Action decision badge & status indicators
│   │   │   ├── SourceCard.jsx      # Cited policy sources with policy ID chips
│   │   │   ├── TicketCard.jsx      # Structured ticket display with status & priority
│   │   │   └── ActivityLog.jsx     # Live event timeline & audit trail
│   │   ├── App.jsx                 # Main application dashboard
│   │   ├── index.css               # Typography and layout styling (DM Sans/Mono)
│   │   └── main.jsx                # React root mount
│   ├── package.json                # Frontend dependencies & scripts
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   └── vite.config.js              # Vite configuration
├── README.md                       # Comprehensive documentation
└── .gitignore                      # Git ignore rules
```
