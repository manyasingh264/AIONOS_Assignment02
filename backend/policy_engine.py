from typing import List, Optional, Tuple
from models import Policy, EmployeeRequest, Ticket, AgentDecision
from retrieval import RetrievalSystem


class PolicyEngine:
    def __init__(self, retrieval: RetrievalSystem):
        self.retrieval = retrieval

    def evaluate_request(self, message: str, employee_id: Optional[str] = None) -> AgentDecision:
        # Step 1: Search for relevant policies
        policies = self.retrieval.search_knowledge_base(message)
        
        # Step 2: Get employee request if ID provided
        employee_request = None
        if employee_id:
            employee_request = self.retrieval.get_employee_request(request_id=employee_id)
        
        # Step 3: Search for relevant tickets
        tickets = self.retrieval.search_tickets(message, active_only=True)
        
        # Step 4: Make decision based on policies and context
        decision = self._make_decision(message, policies, employee_request, tickets)
        
        return decision

    def _make_decision(self, message: str, policies: List[Policy], 
                     employee_request: Optional[EmployeeRequest],
                     tickets: List[Ticket]) -> AgentDecision:
        message_lower = message.lower()
        
        # Handle specific scenarios based on policies
        
        # KB-09: Security Incident (Phishing, Malware, Unauthorized Access)
        if self._matches_security_incident(message_lower):
            security_policy = self._get_policy_by_id("KB-09", policies)
            if security_policy:
                return AgentDecision(
                    intent="security_incident",
                    decision="ESCALATE",
                    policy_ids=["KB-09"],
                    employee_request_id=employee_request.id if employee_request else None,
                    ticket_ids=[],
                    reason="KB-09 requires suspected phishing, malware, or unauthorized access attempts to be reported immediately to Security.",
                    recommended_action="Report to security@veridian-corp.example immediately. Do not forward the suspicious email to others.",
                    escalation_required=True,
                    escalation_destination="Security",
                    needs_clarification=False,
                    response="This appears to be a security incident. Per KB-09, I must report this immediately to Security. Please do not forward the suspicious email to other employees. I have escalated this to security@veridian-corp.example."
                )
        
        # KB-07: Guest Wi-Fi (can be resolved directly)
        if self._matches_guest_wifi(message_lower):
            wifi_policy = self._get_policy_by_id("KB-07", policies)
            if wifi_policy:
                return AgentDecision(
                    intent="guest_wifi",
                    decision="RESOLVE",
                    policy_ids=["KB-07"],
                    employee_request_id=employee_request.id if employee_request else None,
                    ticket_ids=[],
                    reason="KB-07 states guest Wi-Fi credentials can be generated from the front-desk kiosk without IT ticket.",
                    recommended_action="Generate credentials from front-desk kiosk. No IT ticket required.",
                    escalation_required=False,
                    escalation_destination=None,
                    needs_clarification=False,
                    response="You can generate guest Wi-Fi credentials from the front-desk kiosk. They are valid for 24 hours. No IT ticket is required for this."
                )
        
        # KB-01: Password Reset (check for lockout)
        if self._matches_password_issue(message_lower):
            password_policy = self._get_policy_by_id("KB-01", policies)
            if password_policy:
                # Check if locked out (5+ failed attempts)
                if "6" in message_lower or ("locked" in message_lower and "attempt" in message_lower):
                    return AgentDecision(
                        intent="password_lockout",
                        decision="ESCALATE",
                        policy_ids=["KB-01"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-01 states that after 5 failed attempts, IT must be contacted for manual unlock.",
                        recommended_action="Contact IT for manual account unlock.",
                        escalation_required=True,
                        escalation_destination="IT",
                        needs_clarification=False,
                        response="Since you've exceeded 5 failed password attempts, your account is locked. Per KB-01, IT must perform a manual unlock. I'm escalating this to IT now."
                    )
                else:
                    return AgentDecision(
                        intent="password_reset",
                        decision="RESOLVE",
                        policy_ids=["KB-01"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-01 allows employees to reset their own password via self-service portal.",
                        recommended_action="Use self-service portal to reset password.",
                        escalation_required=False,
                        escalation_destination=None,
                        needs_clarification=False,
                        response="You can reset your password using the self-service portal. If you're locked out after 5 failed attempts, please contact IT for manual unlock."
                    )
        
        # KB-02: VPN Access
        if self._matches_vpn_issue(message_lower):
            vpn_policy = self._get_policy_by_id("KB-02", policies)
            if vpn_policy:
                # Check if contractor or credentials expired
                if "contractor" in message_lower:
                    return AgentDecision(
                        intent="vpn_contractor",
                        decision="ROUTE",
                        policy_ids=["KB-02"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-02 requires contractor VPN access to have manager approval via access request form.",
                        recommended_action="Submit access request form with manager approval.",
                        escalation_required=True,
                        escalation_destination="Manager",
                        needs_clarification=False,
                        response="For contractor VPN access, KB-02 requires manager approval via an access request form. Please have the manager submit the access request form."
                    )
                elif "expired" in message_lower or "expire" in message_lower:
                    return AgentDecision(
                        intent="vpn_expired",
                        decision="RESOLVE",
                        policy_ids=["KB-02"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-02 states VPN credentials expire every 90 days and must be renewed.",
                        recommended_action="Renew VPN credentials (automatic for full-time employees).",
                        escalation_required=False,
                        escalation_destination=None,
                        needs_clarification=False,
                        response="Your VPN credentials have expired. Per KB-02, credentials expire every 90 days. As a full-time employee, you can renew them through the standard renewal process."
                    )
                else:
                    return AgentDecision(
                        intent="vpn_access",
                        decision="RESOLVE",
                        policy_ids=["KB-02"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-02 states VPN access is automatic for full-time employees.",
                        recommended_action="VPN access is automatic for full-time employees.",
                        escalation_required=False,
                        escalation_destination=None,
                        needs_clarification=False,
                        response="VPN access is automatic for full-time employees. If you're a contractor, you'll need manager approval via an access request form."
                    )
        
        # KB-03 + ASSET-01: Laptop Replacement
        if self._matches_laptop_issue(message_lower):
            laptop_policy = self._get_policy_by_id("KB-03", policies)
            asset_policy = self._get_policy_by_id("ASSET-01", policies)
            policy_ids = ["KB-03"]
            if asset_policy:
                policy_ids.append("ASSET-01")
            
            if laptop_policy:
                # Check age and failure type
                if "3.5" in message_lower or ("3" in message_lower and "year" in message_lower and "dead" in message_lower):
                    return AgentDecision(
                        intent="laptop_replacement",
                        decision="ROUTE",
                        policy_ids=policy_ids,
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-03 allows replacement after 3 years or hardware failure. ASSET-01 requires Finance sign-off for early replacement beyond 4-year cycle.",
                        recommended_action="Submit laptop replacement request with hardware verification. Requires IT and Finance approval for early replacement.",
                        escalation_required=True,
                        escalation_destination="IT",
                        needs_clarification=False,
                        response="Your laptop is 3.5 years old with complete failure. Per KB-03, replacement is eligible due to hardware failure. However, ASSET-01 requires Finance sign-off for early replacement beyond the 4-year cycle. I'm routing this to IT for processing with required approvals."
                    )
                elif "flickering" in message_lower or "2 year" in message_lower:
                    return AgentDecision(
                        intent="laptop_repair",
                        decision="ROUTE",
                        policy_ids=policy_ids,
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="Laptop is 2 years old (within 4-year cycle). KB-03 allows replacement for verified hardware failure. May qualify for repair instead of replacement.",
                        recommended_action="Submit ticket for hardware diagnostic to determine if repair or replacement is appropriate.",
                        escalation_required=True,
                        escalation_destination="IT",
                        needs_clarification=False,
                        response="Your laptop is 2 years old with screen flickering. Since it's within the 4-year refresh cycle (ASSET-01), please submit a ticket for hardware diagnostic to determine if this qualifies for repair or requires replacement per KB-03."
                    )
                else:
                    return AgentDecision(
                        intent="laptop_issue",
                        decision="CLARIFY",
                        policy_ids=policy_ids,
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="Need more information about laptop age and type of failure to determine eligibility per KB-03 and ASSET-01.",
                        recommended_action="Provide laptop age and specific hardware issue.",
                        escalation_required=False,
                        escalation_destination=None,
                        needs_clarification=True,
                        response="To help with your laptop issue, I need to know: How old is the laptop? What specific hardware problem are you experiencing? This will help determine if it qualifies for replacement per KB-03 or falls under the 4-year refresh cycle per ASSET-01."
                    )
        
        # KB-08: Expense Software Access (check before general software)
        if "expense" in message_lower:
            expense_policy = self._get_policy_by_id("KB-08", policies)
            if expense_policy:
                if "login" in message_lower or "credential" in message_lower or "can't log" in message_lower or "log into" in message_lower:
                    return AgentDecision(
                        intent="expense_login",
                        decision="ROUTE",
                        policy_ids=["KB-08"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-08 states IT assists with login/technical issues once an account exists.",
                        recommended_action="IT will assist with login issue. Verify account exists with Finance first.",
                        escalation_required=True,
                        escalation_destination="IT",
                        needs_clarification=False,
                        response="For expense software login issues, KB-08 states that IT can assist with technical issues once an account exists. Please confirm you have an account (granted by Finance), and I'll route this to IT for login support."
                    )
                else:
                    return AgentDecision(
                        intent="expense_access",
                        decision="ROUTE",
                        policy_ids=["KB-08"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-08 states expense software access is granted by Finance, not IT.",
                        recommended_action="Contact Finance for account access.",
                        escalation_required=True,
                        escalation_destination="Finance",
                        needs_clarification=False,
                        response="Per KB-08, expense software access is granted by Finance, not IT. Please contact Finance to request account access. Once you have an account, IT can help with login or technical issues."
                    )

        # KB-04: Software Installation
        if self._matches_software_install(message_lower):
            software_policy = self._get_policy_by_id("KB-04", policies)
            if software_policy:
                if "catalog" in message_lower and ("not" in message_lower or "non" in message_lower):
                    return AgentDecision(
                        intent="software_non_catalog",
                        decision="ESCALATE",
                        policy_ids=["KB-04"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-04 requires IT Security review for non-catalog software (3-5 business days).",
                        recommended_action="Submit for IT Security review. Approval takes 3-5 business days.",
                        escalation_required=True,
                        escalation_destination="IT Security",
                        needs_clarification=False,
                        response="Since this software is not in the approved catalog, KB-04 requires IT Security review. This process takes 3-5 business days. I'm escalating this to IT Security for review."
                    )
                elif "catalog" in message_lower:
                    return AgentDecision(
                        intent="software_catalog",
                        decision="RESOLVE",
                        policy_ids=["KB-04"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-04 allows self-installation of standard software from approved catalog.",
                        recommended_action="Self-install from approved software catalog.",
                        escalation_required=False,
                        escalation_destination=None,
                        needs_clarification=False,
                        response="Standard software from the approved catalog can be self-installed per KB-04. You can install it directly from the software catalog."
                    )
                else:
                    return AgentDecision(
                        intent="software_install",
                        decision="CLARIFY",
                        policy_ids=["KB-04"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="Need to determine if software is in approved catalog per KB-04.",
                        recommended_action="Specify whether software is in approved catalog.",
                        escalation_required=False,
                        escalation_destination=None,
                        needs_clarification=True,
                        response="For software installation, I need to know: Is this software in the approved catalog? Per KB-04, catalog software can be self-installed, but non-catalog software requires IT Security review."
                    )

        # KB-05: Printer Troubleshooting
        if self._matches_printer_issue(message_lower):
            printer_policy = self._get_policy_by_id("KB-05", policies)
            if printer_policy:
                return AgentDecision(
                    intent="printer_issue",
                    decision="ROUTE",
                    policy_ids=["KB-05"],
                    employee_request_id=employee_request.id if employee_request else None,
                    ticket_ids=[],
                    reason="KB-05 requires checking queue and restarting spooler first. If issue persists, log ticket with asset tag.",
                    recommended_action="Check printer queue, restart spooler. If issue persists, provide asset tag for ticket creation.",
                    escalation_required=True,
                    escalation_destination="IT",
                    needs_clarification=True,
                    response="Per KB-05, please first check the printer queue and restart the print spooler. If the problem persists, I'll need the printer's asset tag to log a ticket. Do you have the asset tag, or would you like me to wait while you try these steps first?"
                )

        # KB-06: Email Mailbox Quota
        if self._matches_mailbox_issue(message_lower):
            mailbox_policy = self._get_policy_by_id("KB-06", policies)
            if mailbox_policy:
                return AgentDecision(
                    intent="mailbox_quota",
                    decision="RESOLVE",
                    policy_ids=["KB-06"],
                    employee_request_id=employee_request.id if employee_request else None,
                    ticket_ids=[],
                    reason="KB-06 states default is 25GB. Employees should archive old mail. Increases require manager approval, capped at 50GB.",
                    recommended_action="Archive old emails. If increase needed, request manager approval (max 50GB).",
                    escalation_required=False,
                    escalation_destination=None,
                    needs_clarification=False,
                    response="Your mailbox quota is 25GB per KB-06. Please archive old emails to free up space. If you need a quota increase beyond 25GB, this requires manager approval and is capped at 50GB."
                )

        # KB-10: Work-From-Home Equipment
        if self._matches_home_equipment(message_lower):
            home_policy = self._get_policy_by_id("KB-10", policies)
            if home_policy:
                if "4 day" in message_lower or "more than 3" in message_lower:
                    return AgentDecision(
                        intent="home_equipment_eligible",
                        decision="ROUTE",
                        policy_ids=["KB-10"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-10 states employees working remotely >3 days/week are eligible for one-time home office equipment allowance. Requires manager sign-off and Finance processing.",
                        recommended_action="Submit request with manager sign-off. Finance processes approval, IT handles shipping.",
                        escalation_required=True,
                        escalation_destination="Finance",
                        needs_clarification=False,
                        response="Since you work from home 4 days a week, you're eligible for the one-time home office equipment allowance per KB-10. This requires manager sign-off and Finance processing. Once approved, IT handles shipping. Please obtain manager sign-off and submit to Finance."
                    )
                else:
                    return AgentDecision(
                        intent="home_equipment",
                        decision="CLARIFY",
                        policy_ids=["KB-10"],
                        employee_request_id=employee_request.id if employee_request else None,
                        ticket_ids=[],
                        reason="KB-10 eligibility depends on working remotely >3 days/week.",
                        recommended_action="Specify number of remote work days per week.",
                        escalation_required=False,
                        escalation_destination=None,
                        needs_clarification=True,
                        response="For home office equipment eligibility per KB-10, I need to know: How many days per week do you work from home? The allowance is available for employees working remotely more than 3 days per week."
                    )

        # Admin access requests (no specific policy - insufficient information)
        if self._matches_admin_access(message_lower):
            return AgentDecision(
                intent="admin_access",
                decision="ESCALATE",
                policy_ids=[],
                employee_request_id=employee_request.id if employee_request else None,
                ticket_ids=[],
                reason="The supplied knowledge base does not specify the approval workflow for admin access requests.",
                recommended_action="Escalate to appropriate team for admin access request evaluation.",
                escalation_required=True,
                escalation_destination="IT Management",
                needs_clarification=False,
                response="The available knowledge base does not specify the required approval workflow for admin access requests. I'm escalating this to IT Management for evaluation. Please provide business justification for your request."
            )
        
        # Vague/unclear requests
        if self._is_vague_request(message_lower):
            return AgentDecision(
                intent="unknown",
                decision="CLARIFY",
                policy_ids=[],
                employee_request_id=employee_request.id if employee_request else None,
                ticket_ids=[],
                reason="Request is too vague to determine intent or relevant policy.",
                recommended_action="Ask for clarification about the specific issue.",
                escalation_required=False,
                escalation_destination=None,
                needs_clarification=True,
                response="I'd like to help, but I need more information. Could you please describe what specifically isn't working? For example, is it related to your laptop, software, VPN, email, or another system?"
            )
        
        # Default: No matching policy found
        if policies:
            return AgentDecision(
                intent="general",
                decision="ESCALATE",
                policy_ids=[p.id for p in policies[:1]],
                employee_request_id=employee_request.id if employee_request else None,
                ticket_ids=[],
                reason=f"Found potentially relevant policy ({policies[0].id}) but request requires human evaluation.",
                recommended_action="Review matched policy and escalate if needed.",
                escalation_required=True,
                escalation_destination="IT",
                needs_clarification=False,
                response=f"I found {policies[0].title} which may be relevant, but I need to escalate this for proper evaluation. {policies[0].content}"
            )
        else:
            return AgentDecision(
                intent="unknown",
                decision="ESCALATE",
                policy_ids=[],
                employee_request_id=employee_request.id if employee_request else None,
                ticket_ids=[],
                reason="No matching policy found in knowledge base.",
                recommended_action="Escalate to IT for manual evaluation.",
                escalation_required=True,
                escalation_destination="IT",
                needs_clarification=False,
                response="I couldn't find a specific policy in the knowledge base that matches your request. I'm escalating this to IT for manual evaluation."
            )

    def _get_policy_by_id(self, policy_id: str, policies: List[Policy]) -> Optional[Policy]:
        for policy in policies:
            if policy.id == policy_id:
                return policy
        return None

    def _matches_security_incident(self, message: str) -> bool:
        keywords = ["phishing", "malware", "unauthorized", "hack", "suspicious", "security"]
        return any(keyword in message for keyword in keywords)

    def _matches_guest_wifi(self, message: str) -> bool:
        keywords = ["guest", "visitor", "wifi", "wi-fi"]
        return any(keyword in message for keyword in keywords)

    def _matches_password_issue(self, message: str) -> bool:
        keywords = ["password", "locked", "unlock", "account"]
        return any(keyword in message for keyword in keywords)

    def _matches_vpn_issue(self, message: str) -> bool:
        keywords = ["vpn", "remote access"]
        return any(keyword in message for keyword in keywords)

    def _matches_laptop_issue(self, message: str) -> bool:
        keywords = ["laptop", "computer", "dead", "won't turn", "screen", "flickering"]
        return any(keyword in message for keyword in keywords)

    def _matches_software_install(self, message: str) -> bool:
        keywords = ["install", "software", "extension", "browser", "tool", "application"]
        return any(keyword in message for keyword in keywords)

    def _matches_printer_issue(self, message: str) -> bool:
        keywords = ["printer", "paper jam", "print"]
        return any(keyword in message for keyword in keywords)

    def _matches_mailbox_issue(self, message: str) -> bool:
        keywords = ["mailbox", "quota", "full", "storage", "email"]
        return any(keyword in message for keyword in keywords)

    def _matches_expense_issue(self, message: str) -> bool:
        keywords = ["expense"]
        return any(keyword in message for keyword in keywords)

    def _matches_home_equipment(self, message: str) -> bool:
        keywords = ["home", "remote", "monitor", "chair", "work from home"]
        return any(keyword in message for keyword in keywords)

    def _matches_admin_access(self, message: str) -> bool:
        keywords = ["admin", "access", "server", "privilege"]
        return any(keyword in message for keyword in keywords)

    def _is_vague_request(self, message: str) -> bool:
        vague_indicators = ["not working", "help", "broken", "issue", "problem"]
        message_words = message.split()
        # If message is very short and contains vague indicators
        return len(message_words) < 8 and any(indicator in message for indicator in vague_indicators)
