from agent import ITSupportAgent

agent = ITSupportAgent('data/policies.json', 'data/employee_requests.json', 'data/tickets.json')

PASS = 0
FAIL = 0
results = []

def chat(msg, session, emp='REQ-03'):
    r = agent.process_message(msg, employee_id=emp, session_id=session)
    return r

def check(label, r, expected_type=None, expected_decision=None, expected_policy=None, no_ticket=False):
    global PASS, FAIL
    issues = []
    if expected_type and r.message_type != expected_type:
        issues.append(f"msg_type={r.message_type} (want {expected_type})")
    if expected_decision and r.decision != expected_decision:
        issues.append(f"decision={r.decision} (want {expected_decision})")
    if expected_policy:
        for p in expected_policy:
            if p not in r.policy_sources:
                issues.append(f"missing policy {p} (got {r.policy_sources})")
    if no_ticket and r.ticket is not None:
        issues.append(f"unexpected ticket {r.ticket}")
    status = "PASS" if not issues else "FAIL"
    if status == "PASS":
        PASS += 1
    else:
        FAIL += 1
    tid = r.ticket["ticket_id"] if r.ticket else None
    print(f"  [{status}] {label}")
    print(f"         type={r.message_type} | decision={r.decision} | policy={r.policy_sources} | ticket={tid}")
    print(f"         response: {r.response[:110]}")
    if issues:
        print(f"         ISSUES: {'; '.join(issues)}")
    print()
    return r

print("=" * 65)
print("TEST 1 — Guest Wi-Fi")
print("=" * 65)
r = chat("Can I get Wi-Fi access for a guest visiting our office tomorrow?", "T1")
check("T1 Guest Wi-Fi", r, "NEW_ISSUE", "RESOLVE", ["KB-07"], no_ticket=True)

print("=" * 65)
print("TEST 2 — Phishing multi-turn")
print("=" * 65)
r = chat("I got a phishing email", "T2")
check("T2a Phishing initial", r, "NEW_ISSUE", "ESCALATE", ["KB-09"])
r = chat("ok", "T2")
check("T2b Acknowledgement after phishing", r, "ACKNOWLEDGEMENT", no_ticket=True)
r = chat("What do I do now?", "T2")
check("T2c Follow-up after phishing", r, "FOLLOW_UP", no_ticket=True)
r = chat("I already forwarded it to my colleague", "T2")
# Should stay in KB-09 context (ALREADY_TRIED or FOLLOW_UP), NOT say "no policy found"
ok = r.message_type in ("ALREADY_TRIED", "FOLLOW_UP") and "KB-09" in r.policy_sources
if ok:
    PASS += 1
    print(f"  [PASS] T2d Security context retained after 'already forwarded'")
else:
    FAIL += 1
    print(f"  [FAIL] T2d Security context — got type={r.message_type}, policy={r.policy_sources}")
print(f"         response: {r.response[:110]}\n")

print("=" * 65)
print("TEST 3 — VPN + don't understand")
print("=" * 65)
chat("My VPN stopped working, says credentials expired", "T3")
r = chat("I dont understand", "T3")
check("T3b Don't understand -> FOLLOW_UP", r, "FOLLOW_UP", no_ticket=True)
r = chat("How do I renew it?", "T3")
check("T3c Renewal question uses KB-02", r, "FOLLOW_UP", None, ["KB-02"], no_ticket=True)

print("=" * 65)
print("TEST 4 — Printer + already tried spooler")
print("=" * 65)
chat("My printer isnt working", "T4")
r = chat("I already restarted the spooler", "T4")
check("T4b Already tried spooler -> ask asset tag", r, "ALREADY_TRIED", no_ticket=True)
# Response should mention asset tag
if "asset" in r.response.lower():
    PASS += 1
    print("  [PASS] T4b response mentions asset tag")
else:
    FAIL += 1
    print(f"  [FAIL] T4b response does NOT mention asset tag: {r.response[:80]}")
print()

print("=" * 65)
print("TEST 5 — Browser extension clarification")
print("=" * 65)
chat("I want to install a browser extension", "T5")
r = chat("Yes it is in the catalog", "T5")
check("T5b Clarification yes-in-catalog -> RESOLVE", r, "CLARIFICATION_RESPONSE", "RESOLVE", ["KB-04"], no_ticket=True)

print("=" * 65)
print("TEST 6 — Topic switch VPN -> Printer")
print("=" * 65)
chat("My VPN isnt working", "T6")
r = chat("Actually my printer is broken", "T6")
check("T6b Topic switch -> NEW_ISSUE KB-05", r, "NEW_ISSUE", None, ["KB-05"])

print("=" * 65)
print("TEST 7 — Admin access (no policy)")
print("=" * 65)
r = chat("I need admin access to the finance reporting server", "T7")
check("T7 Admin access no policy -> ESCALATE", r, "NEW_ISSUE", "ESCALATE")
if not r.policy_sources:
    PASS += 1
    print("  [PASS] T7 No invented policy sources")
else:
    FAIL += 1
    print(f"  [FAIL] T7 Has policy sources: {r.policy_sources}")
print()

print("=" * 65)
print("TEST 8 — Multi-intent VPN + mailbox")
print("=" * 65)
r = chat("My VPN stopped working and my mailbox is full", "T8")
check("T8 Multi-intent", r, "MULTI_INTENT")
has_both = any(p in r.policy_sources for p in ["KB-02"]) and "KB-06" in r.response or "mailbox" in r.response.lower()
if has_both:
    PASS += 1
    print("  [PASS] T8 Both issues addressed (VPN + mailbox)")
else:
    FAIL += 1
    print(f"  [FAIL] T8 Not both addressed — policy={r.policy_sources}")
print()

print("=" * 65)
print("TEST 9 — Human handoff")
print("=" * 65)
r = chat("Can I talk to a human?", "T9")
check("T9 Human handoff", r, "HUMAN_HANDOFF_REQUEST", "ESCALATE")

print("=" * 65)
print("TEST 10 — Out of scope")
print("=" * 65)
r = chat("What is todays weather?", "T10")
check("T10 Out of scope", r, "OUT_OF_SCOPE", no_ticket=True)

print("=" * 65)
print("TEST 11 — Policy info no ticket")
print("=" * 65)
r = chat("How long do VPN credentials last?", "T11")
check("T11 Policy info", r, "POLICY_INFO_QUESTION", "RESOLVE", ["KB-02"], no_ticket=True)
if "90" in r.response:
    PASS += 1
    print("  [PASS] T11 Response mentions 90 days")
else:
    FAIL += 1
    print(f"  [FAIL] T11 Missing '90 days' in response: {r.response[:80]}")
print()

print("=" * 65)
print("TEST 12 — Ticket status lookup")
print("=" * 65)
r = chat("What is the status of my laptop replacement?", "T12")
check("T12 Ticket status", r, "TICKET_STATUS_QUERY", no_ticket=True)
if any(x in r.response for x in ["TK-1043", "pending", "Approved", "status"]):
    PASS += 1
    print("  [PASS] T12 Returns ticket data")
else:
    FAIL += 1
    print(f"  [FAIL] T12 No ticket data in response: {r.response[:80]}")
print()

print("=" * 65)
print(f"FINAL SCORE: {PASS} PASSED  |  {FAIL} FAILED")
print("=" * 65)
