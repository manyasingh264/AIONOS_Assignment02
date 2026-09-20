import json
from typing import List, Optional
from datetime import datetime
from models import Ticket, GeneratedTicket


class TicketManager:
    def __init__(self, tickets_path: str):
        self.tickets_path = tickets_path
        self.generated_tickets: List[GeneratedTicket] = []
        self._counter = 1

    def create_ticket(self, employee: str, category: str, issue: str, 
                    priority: str, source: str, 
                    destination: Optional[str] = None) -> GeneratedTicket:
        ticket_id = f"AUTO-{self._counter:03d}"
        self._counter += 1
        
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
