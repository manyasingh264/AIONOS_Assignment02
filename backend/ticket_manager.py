import json
from typing import List, Optional
from datetime import datetime
from models import Ticket, GeneratedTicket


class TicketManager:
    def __init__(self, tickets_path: str):
        self.tickets_path = tickets_path
        self.generated_tickets: List[GeneratedTicket] = []
        self._counter = 1

    def _determine_priority(self, category: str, issue: str, destination: Optional[str] = None) -> str:
        """Auto-assign priority based on category and destination"""
        issue_lower = issue.lower()
        
        # Critical priority for security incidents
        if category in ["security_incident", "phishing", "malware", "unauthorized_access"]:
            return "Critical"
        
        if destination == "Security":
            return "Critical"
        
        # High priority for urgent issues
        urgent_keywords = ["urgent", "emergency", "critical", "down", "broken", "dead", "locked"]
        if any(keyword in issue_lower for keyword in urgent_keywords):
            return "High"
        
        # High priority for password lockouts
        if "locked" in issue_lower and "password" in issue_lower:
            return "High"
        
        # Medium priority for approval workflows
        if destination in ["Manager", "Finance", "IT Security"]:
            return "Medium"
        
        # Medium priority for standard IT issues
        if category in ["laptop_replacement", "hardware", "software_install", "printer_issue"]:
            return "Medium"
        
        # Low priority for informational requests
        if category in ["guest_wifi", "password_reset", "mailbox_quota"]:
            return "Low"
        
        # Default to Medium
        return "Medium"

    def create_ticket(self, employee: str, category: str, issue: str, 
                    source: str, priority: str = None,
                    destination: Optional[str] = None) -> GeneratedTicket:
        ticket_id = f"AUTO-{self._counter:03d}"
        self._counter += 1
        
        # Auto-assign priority if not provided
        if not priority:
            priority = self._determine_priority(category, issue, destination)
        
        ticket = GeneratedTicket(
            ticket_id=ticket_id,
            employee=employee,
            category=category,
            issue=issue,
            priority=priority,
            source=source,
            destination=destination,
            status="Escalated" if destination else "Open",
            created_at=datetime.now().isoformat()
        )
        
        self.generated_tickets.append(ticket)
        return ticket

    def get_generated_tickets(self) -> List[GeneratedTicket]:
        return self.generated_tickets

    def get_ticket_by_id(self, ticket_id: str) -> Optional[GeneratedTicket]:
        for ticket in self.generated_tickets:
            if ticket.ticket_id == ticket_id:
                return ticket
        return None
