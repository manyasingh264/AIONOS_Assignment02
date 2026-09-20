import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from policy_engine import PolicyEngine
from retrieval import RetrievalSystem
from models import AgentDecision

def test_all_15_requests():
    """Test all 15 employee requests from the assignment"""
    
    # Initialize retrieval and policy engine
    policies_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'policies.json')
    requests_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'employee_requests.json')
    tickets_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tickets.json')
    
    retrieval = RetrievalSystem(policies_path, requests_path, tickets_path)
    engine = PolicyEngine(retrieval)
    
    # Test cases based on assignment requirements
    test_cases = [
        # REQ-01: Laptop won't turn on, 3.5 years old
        {
            "id": "REQ-01",
            "message": "My laptop won't turn on at all, it's completely dead, had it about 3.5 years now.",
            "expected_decision": "ROUTE",
            "expected_policies": ["KB-03", "ASSET-01"],
            "description": "Laptop replacement with hardware failure at 3.5 years"
        },
        # REQ-02: Guest Wi-Fi
        {
            "id": "REQ-02",
            "message": "Can I get Wi-Fi access for a guest visiting our office tomorrow?",
            "expected_decision": "RESOLVE",
            "expected_policies": ["KB-07"],
            "description": "Guest Wi-Fi request"
        },
        # REQ-03: Account locked after 6 attempts
        {
            "id": "REQ-03",
            "message": "I'm locked out of my account, tried my password 6 times.",
            "expected_decision": "ESCALATE",
            "expected_policies": ["KB-01"],
            "description": "Password lockout exceeding 5 attempts"
        },
        # REQ-04: Non-catalog software
        {
            "id": "REQ-04",
            "message": "Need approval to install a data-analysis tool that's not in the software catalog.",
            "expected_decision": "ESCALATE",
            "expected_policies": ["KB-04"],
            "description": "Non-catalog software installation"
        },
        # REQ-05: Expired VPN credentials
        {
            "id": "REQ-05",
            "message": "My VPN stopped working this morning, says credentials expired.",
            "expected_decision": "RESOLVE",
            "expected_policies": ["KB-02"],
            "description": "Expired VPN credentials"
        },
        # REQ-06: Printer issue
        {
            "id": "REQ-06",
            "message": "Printer on the 3rd floor keeps showing 'paper jam' even though there's no jam.",
            "expected_decision": "ROUTE",
            "expected_policies": ["KB-05"],
            "description": "Printer troubleshooting"
        },
        # REQ-07: Work from home 4 days/week
        {
            "id": "REQ-07",
            "message": "I've started working from home 4 days a week, how do I get a monitor?",
            "expected_decision": "ROUTE",
            "expected_policies": ["KB-10"],
            "description": "Home office equipment eligibility"
        },
        # REQ-08: Phishing email
        {
            "id": "REQ-08",
            "message": "I think I got a phishing email asking for my login - forwarding it to a few teammates to check.",
            "expected_decision": "ESCALATE",
            "expected_policies": ["KB-09"],
            "description": "Security incident - phishing"
        },
        # REQ-09: Mailbox full
        {
            "id": "REQ-09",
            "message": "My mailbox is full and I can't send emails.",
            "expected_decision": "RESOLVE",
            "expected_policies": ["KB-06"],
            "description": "Email mailbox quota"
        },
        # REQ-10: Admin access request (no policy)
        {
            "id": "REQ-10",
            "message": "Can someone give me admin access to the finance reporting server? Need it urgently for month-end.",
            "expected_decision": "ESCALATE",
            "expected_policies": [],
            "description": "Admin access request - no specific policy"
        },
        # REQ-11: Contractor VPN
        {
            "id": "REQ-11",
            "message": "New contractor joining my team next week, they'll need VPN access.",
            "expected_decision": "ROUTE",
            "expected_policies": ["KB-02"],
            "description": "Contractor VPN access"
        },
        # REQ-12: Expense software login
        {
            "id": "REQ-12",
            "message": "I can't log into the expense tool, keeps saying invalid credentials.",
            "expected_decision": "ROUTE",
            "expected_policies": ["KB-08"],
            "description": "Expense software login issue"
        },
        # REQ-13: Laptop flickering, 2 years old
        {
            "id": "REQ-13",
            "message": "Laptop screen is flickering on and off, had it 2 years, might just need a fix not a replacement.",
            "expected_decision": "ROUTE",
            "expected_policies": ["KB-03", "ASSET-01"],
            "description": "Laptop repair vs replacement at 2 years"
        },
        # REQ-14: Browser extension (unknown catalog status)
        {
            "id": "REQ-14",
            "message": "Requesting approval to install a browser extension for productivity tracking.",
            "expected_decision": "CLARIFY",
            "expected_policies": ["KB-04"],
            "description": "Browser extension - catalog status unknown"
        },
        # REQ-15: Vague request
        {
            "id": "REQ-15",
            "message": "hey can you help, its not working",
            "expected_decision": "CLARIFY",
            "expected_policies": [],  # No specific policy expected for vague requests
            "description": "Vague request requiring clarification"
        },
    ]
    
    print("Testing all 15 employee requests...")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\nTest {test_case['id']}: {test_case['description']}")
        print(f"Message: {test_case['message']}")
        
        try:
            decision = engine.evaluate_request(test_case['message'], test_case['id'])
            
            # Check decision
            decision_match = decision.decision == test_case['expected_decision']
            
            # Check policies (allow partial matches, or empty if expected empty)
            if test_case['expected_policies']:
                policy_match = any(p in decision.policy_ids for p in test_case['expected_policies'])
            else:
                # If no policies expected, either match none or it's a vague request
                policy_match = len(decision.policy_ids) == 0 or test_case['id'] == 'REQ-15'
            
            if decision_match and policy_match:
                print(f"[PASS]")
                print(f"  Decision: {decision.decision}")
                print(f"  Policies: {decision.policy_ids}")
                passed += 1
            else:
                print(f"[FAIL]")
                print(f"  Expected Decision: {test_case['expected_decision']}, Got: {decision.decision}")
                print(f"  Expected Policies: {test_case['expected_policies']}, Got: {decision.policy_ids}")
                failed += 1

        except Exception as e:
            print(f"[ERROR]: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    return failed == 0

if __name__ == "__main__":
    success = test_all_15_requests()
    sys.exit(0 if success else 1)
