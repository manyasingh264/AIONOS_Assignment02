from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

from models import ChatRequest, ChatResponse, Policy, EmployeeRequest, Ticket
from agent import ITSupportAgent
from retrieval import RetrievalSystem
from ticket_manager import TicketManager
from conversation_manager import ConversationManager

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Internal IT Support Agent API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
POLICIES_PATH = os.path.join(DATA_DIR, "policies.json")
REQUESTS_PATH = os.path.join(DATA_DIR, "employee_requests.json")
TICKETS_PATH = os.path.join(DATA_DIR, "tickets.json")

# Check if Groq API key is set
if not os.getenv("GROQ_API_KEY"):
    print("WARNING: GROQ_API_KEY not set in environment variables")

# Initialize agent (will fail gracefully if no API key or Groq issues)
agent = None
try:
    agent = ITSupportAgent(POLICIES_PATH, REQUESTS_PATH, TICKETS_PATH)
    print("Agent initialized successfully")
except Exception as e:
    print(f"Agent initialization error: {e}")
    print("Agent will run in fallback mode without LLM support")

# Initialize retrieval system for data endpoints
retrieval = RetrievalSystem(POLICIES_PATH, REQUESTS_PATH, TICKETS_PATH)
ticket_manager = TicketManager(TICKETS_PATH)
# NOTE: Do NOT create a separate ConversationManager here.
# Use agent.conversation_manager so the DELETE endpoint clears the real session store.


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "groq_configured": os.getenv("GROQ_API_KEY") is not None
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message from an employee"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check GROQ_API_KEY.")
    
    try:
        response = agent.process_message(
            message=request.message,
            employee_id=request.employee_id,
            session_id=request.session_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.get("/api/policies")
async def get_policies():
    """Get all policies"""
    policies = retrieval.get_all_policies()
    return {"policies": [p.dict() for p in policies]}


@app.get("/api/requests")
async def get_employee_requests():
    """Get all employee requests"""
    requests = retrieval.get_all_requests()
    return {"requests": [r.dict() for r in requests]}


@app.get("/api/tickets")
async def get_tickets():
    """Get all tickets (both original and generated)"""
    original_tickets = retrieval.get_all_tickets()
    generated_tickets = ticket_manager.get_generated_tickets()
    
    return {
        "original_tickets": [t.dict() for t in original_tickets],
        "generated_tickets": [t.dict() for t in generated_tickets]
    }


@app.post("/api/tickets")
async def create_ticket(ticket_data: dict):
    """Create a new ticket manually"""
    try:
        # Extract priority (optional - will auto-assign if not provided)
        priority = ticket_data.get("priority")
        if not priority or priority.strip() == "":
            priority = None  # Let ticket manager auto-assign
        
        ticket = ticket_manager.create_ticket(
            employee=ticket_data.get("employee", "Unknown"),
            category=ticket_data.get("category", "General"),
            issue=ticket_data.get("issue", ""),
            source=ticket_data.get("source", "Manual"),
            priority=priority,
            destination=ticket_data.get("destination")
        )
        return ticket.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")


@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a conversation session — uses the agent's own session store."""
    try:
        if agent:
            agent.conversation_manager.clear_session(session_id)
        return {"message": f"Session {session_id} cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get conversation session state"""
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        session = agent.conversation_manager.get_or_create_session(session_id)
        return session.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
