import json
from typing import List, Optional
from models import Policy, EmployeeRequest, Ticket


class RetrievalSystem:
    def __init__(self, policies_path: str, requests_path: str, tickets_path: str):
        self.policies_path = policies_path
        self.requests_path = requests_path
        self.tickets_path = tickets_path
        self._policies: List[Policy] = []
        self._requests: List[EmployeeRequest] = []
        self._tickets: List[Ticket] = []
        self._load_data()

    def _load_data(self):
        with open(self.policies_path, 'r') as f:
            policies_data = json.load(f)
            self._policies = [Policy(**p) for p in policies_data['policies']]
        
        with open(self.requests_path, 'r') as f:
            requests_data = json.load(f)
            self._requests = [EmployeeRequest(**r) for r in requests_data['requests']]
        
        with open(self.tickets_path, 'r') as f:
            tickets_data = json.load(f)
            self._tickets = [Ticket(**t) for t in tickets_data['tickets']]

    def search_knowledge_base(self, query: str) -> List[Policy]:
        query_lower = query.lower()
        matching_policies = []
        
        for policy in self._policies:
            score = 0
            query_words = set(query_lower.split())
            
            # Check category match
            if policy.category in query_lower:
                score += 3
            
            # Check keyword matches
            for keyword in policy.keywords:
                if keyword.lower() in query_lower:
                    score += 2
            
            # Check content match
            if any(word in policy.content.lower() for word in query_words):
                score += 1
            
            if score > 0:
                matching_policies.append((policy, score))
        
        # Sort by score and return policies
        matching_policies.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in matching_policies]

    def get_employee_request(self, request_id: Optional[str] = None, 
                            employee_name: Optional[str] = None) -> Optional[EmployeeRequest]:
        if request_id:
            for req in self._requests:
                if req.id == request_id:
                    return req
        if employee_name:
            for req in self._requests:
                if employee_name.lower() in req.employee.lower():
                    return req
        return None

    def search_tickets(self, query: str, active_only: bool = False) -> List[Ticket]:
        query_lower = query.lower()
        matching_tickets = []
        
        for ticket in self._tickets:
            if active_only and not ticket.is_active:
                continue
            
            if (query_lower in ticket.issue.lower() or 
                query_lower in ticket.employee.lower() or
                query_lower in ticket.status.lower()):
                matching_tickets.append(ticket)
        
        return matching_tickets

    def get_all_policies(self) -> List[Policy]:
        return self._policies

    def get_all_requests(self) -> List[EmployeeRequest]:
        return self._requests

    def get_all_tickets(self) -> List[Ticket]:
        return self._tickets
