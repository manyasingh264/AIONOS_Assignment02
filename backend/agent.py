import os
from typing import Optional, List
from groq import Groq
from models import AgentDecision, ChatResponse, ConversationState
from retrieval import RetrievalSystem
from policy_engine import PolicyEngine
from ticket_manager import TicketManager
from audit import AuditLogger
from conversation_manager import ConversationManager


class ITSupportAgent:
    def __init__(self, policies_path: str, requests_path: str, tickets_path: str):
        self.retrieval = RetrievalSystem(policies_path, requests_path, tickets_path)
        self.policy_engine = PolicyEngine(self.retrieval)
        self.ticket_manager = TicketManager(tickets_path)
        self.audit_logger = AuditLogger()
        self.conversation_manager = ConversationManager()

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not set. Agent will work in fallback mode without LLM.")
            self.groq_client = None
        else:
            try:
                self.groq_client = Groq(api_key=api_key)
            except Exception as e:
                print(f"WARNING: Failed to initialize Groq client: {e}. Fallback mode active.")
                self.groq_client = None

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def process_message(self, message: str, employee_id: Optional[str] = None,
                        session_id: Optional[str] = None) -> ChatResponse:
        if not session_id:
            session_id = f"session_{employee_id or 'default'}"

        session_state = self.conversation_manager.get_or_create_session(session_id, employee_id)
        self.audit_logger.clear()
        self.audit_logger.log("REQUEST_RECEIVED", f"Message from {employee_id or 'unknown'}")

        classification = self.conversation_manager.classify_message(message, session_state)
        msg_type = classification.message_type
        self.audit_logger.log("MESSAGE_CLASSIFIED", msg_type)

        self.conversation_manager.add_to_history(session_id, "user", message)

        # Route to appropriate handler
        if msg_type == "ACKNOWLEDGEMENT":
            result = self._handle_acknowledgement(session_state, session_id)
        elif msg_type == "HUMAN_HANDOFF_REQUEST":
            result = self._handle_human_handoff(session_state, employee_id, session_id)
        elif msg_type == "CLARIFICATION_RESPONSE":
            result = self._handle_clarification_response(message, session_state, employee_id, session_id)
        elif msg_type == "ALREADY_TRIED":
            result = self._handle_already_tried(message, session_state, employee_id, session_id)
        elif msg_type == "FOLLOW_UP":
            result = self._handle_follow_up(message, session_state, employee_id, session_id)
        elif msg_type == "CORRECTION":
            result = self._handle_correction(message, session_state, employee_id, session_id)
        elif msg_type == "TICKET_STATUS_QUERY":
            result = self._handle_ticket_status_query(message, session_state, employee_id, session_id)
        elif msg_type == "MULTI_INTENT":
            result = self._handle_multi_intent(message, session_state, employee_id, session_id)
        elif msg_type == "OUT_OF_SCOPE":
            result = self._handle_out_of_scope(session_state, session_id)
        elif msg_type == "POLICY_INFO_QUESTION":
            result = self._handle_policy_question(message, session_state, session_id)
        else:
            # NEW_ISSUE or default
            result = self._handle_new_issue(message, session_state, employee_id, session_id)

        # Attach the classification type so the frontend can display it
        result.message_type = msg_type
        return result

    # ------------------------------------------------------------------
    # NEW ISSUE
    # ------------------------------------------------------------------

    def _handle_new_issue(self, message: str, session_state: ConversationState,
                          employee_id: Optional[str], session_id: str) -> ChatResponse:
        decision = self.policy_engine.evaluate_request(message, employee_id)
        self.audit_logger.log("NEW_ISSUE_DETECTED", message[:80])
        self.audit_logger.log("INTENT_IDENTIFIED", decision.intent)
        for pid in decision.policy_ids:
            self.audit_logger.log("POLICY_RETRIEVED", pid)
        self.audit_logger.log("DECISION", decision.decision)

        # Update conversation state (reset troubleshooting_steps_done for a fresh issue)
        self.conversation_manager.update_session(
            session_id,
            current_issue=message,
            current_intent=decision.intent,
            current_policy_id=decision.policy_ids[0] if decision.policy_ids else None,
            current_decision=decision.decision,
            pending_clarification=decision.recommended_action if decision.needs_clarification else None,
            troubleshooting_steps_done=[],
            in_security_context=(decision.intent == "security_incident"),
        )

        # Create ticket for all escalations (not just first one in session)
        ticket = None
        if decision.escalation_required:
            ticket = self.ticket_manager.create_ticket(
                employee=employee_id or "Unknown",
                category=decision.intent,
                issue=message,
                source=decision.policy_ids[0] if decision.policy_ids else "Unknown",
                destination=decision.escalation_destination
            )
            self.audit_logger.log("TICKET_CREATED", f"{ticket.ticket_id} -> {ticket.destination}")
            # Update session with latest ticket ID (for tracking)
            self.conversation_manager.update_session(session_id, current_ticket_id=ticket.ticket_id)

        # Generate natural language response using LLM when available
        response = self._generate_conversational_response(
            user_message=message,
            decision=decision,
            session_state=session_state,
            context="new_issue"
        )

        self.conversation_manager.add_to_history(session_id, "assistant", response)
        self.conversation_manager.update_session(session_id, previous_agent_message=response)

        return ChatResponse(
            response=response,
            decision=decision.decision,
            policy_sources=decision.policy_ids,
            recommended_action=decision.recommended_action,
            ticket=ticket.dict() if ticket else None,
            audit=self._build_audit_trail()
        )

    # ------------------------------------------------------------------
    # ACKNOWLEDGEMENT
    # ------------------------------------------------------------------

    def _handle_acknowledgement(self, session_state: ConversationState, session_id: str) -> ChatResponse:
        self.audit_logger.log("ACKNOWLEDGEMENT_DETECTED", "User acknowledged previous response")

        # Build a contextual, natural-sounding ack reply using the LLM
        if self.groq_client and session_state.current_issue:
            prompt = (
                f"The IT support agent just gave this response:\n"
                f"\"{session_state.previous_agent_message}\"\n\n"
                f"The employee replied with a simple acknowledgement like 'ok', 'thanks', 'understood'.\n"
                f"Write a short, natural closing remark (1-2 sentences) that:\n"
                f"- Confirms the action or information was received\n"
                f"- Mentions the ticket ID '{session_state.current_ticket_id}' if one exists\n"
                f"- Invites the user to reach out if they need more help\n"
                f"- Does NOT search for a new policy or create a new ticket\n"
                f"- Is professional and concise."
            )
            response = self._call_llm_simple(prompt)
        else:
            prev_msg = (session_state.previous_agent_message or "").lower()
            already_asked = any(p in prev_msg for p in [
                "anything else", "anything more", "anything i can",
                "further assistance", "let me know if",
            ])
            if already_asked:
                # Employee closing the conversation - give a proper goodbye, not another loop
                ticket_ref = (f" Your ticket {session_state.current_ticket_id} is on record."
                              if session_state.current_ticket_id else "")
                response = (f"Alright, happy to help!{ticket_ref} "
                            f"Feel free to reach out if anything else comes up. Have a great day!")
            elif session_state.current_ticket_id:
                response = (f"Understood. Your request has been logged as "
                            f"{session_state.current_ticket_id}. "
                            f"Is there anything else I can help you with?")
            elif session_state.current_decision == "ESCALATE":
                response = ("Understood. The escalation has been recorded and the team will follow up. "
                            "Let me know if there's anything else you need.")
            else:
                response = "Understood. Let me know if you need any further assistance."


        self.conversation_manager.add_to_history(session_id, "assistant", response)
        # Clear pending_clarification so stale questions can't be re-triggered
        # by future "no" / "yes" messages in the same session
        self.conversation_manager.update_session(
            session_id,
            previous_agent_message=response,
            pending_clarification=None
        )

        return ChatResponse(
            response=response,
            decision=session_state.current_decision or "RESOLVE",
            policy_sources=[session_state.current_policy_id] if session_state.current_policy_id else [],
            recommended_action="Acknowledgement received",
            ticket=None,
            audit=self._build_audit_trail()
        )

    # ------------------------------------------------------------------
    # HUMAN HANDOFF
    # ------------------------------------------------------------------

    def _handle_human_handoff(self, session_state: ConversationState,
                              employee_id: Optional[str], session_id: str) -> ChatResponse:
        self.audit_logger.log("HUMAN_HANDOFF", "User requested human assistance")

        ticket = None
        ticket = self.ticket_manager.create_ticket(
            employee=employee_id or "Unknown",
            category="Human Handoff",
            issue=session_state.current_issue or "User requested human assistance",
            source=session_state.current_policy_id or "Conversation",
            destination="IT Support"
        )
        self.audit_logger.log("TICKET_CREATED", f"{ticket.ticket_id} -> IT Support")
        self.conversation_manager.update_session(session_id, current_ticket_id=ticket.ticket_id)

        # Only include issue if employee described one in THIS session
        # Prevents stale session data appearing when handoff is the first message
        has_prior_context = len(session_state.conversation_history) > 1
        issue_summary = session_state.current_issue if (has_prior_context and session_state.current_issue) else None
        ticket_ref = (ticket.ticket_id if ticket
                      else session_state.current_ticket_id or "")
        ticket_str = f" (Ticket: {ticket_ref})" if ticket_ref else ""

        if issue_summary:
            response = (
                f"Of course — I've escalated your request to the IT Support team{ticket_str}. "
                f"They'll have full context about your issue: \"{issue_summary}\""
                f"{' and the policy that was applied.' if session_state.current_policy_id else '.'}" 
                f" You won't need to explain everything again. Someone will be in touch shortly."
            )
        else:
            response = (
                f"Of course — I've escalated your request to the IT Support team{ticket_str}. "
                f"A support agent will reach out to you shortly to understand your issue and assist you."
            )

        self.conversation_manager.add_to_history(session_id, "assistant", response)
        self.conversation_manager.update_session(session_id, previous_agent_message=response)

        return ChatResponse(
            response=response,
            decision="ESCALATE",
            policy_sources=[session_state.current_policy_id] if session_state.current_policy_id else [],
            recommended_action="Human handoff — escalated to IT Support with full context",
            ticket=ticket.dict() if ticket else None,
            audit=self._build_audit_trail()
        )

    # ------------------------------------------------------------------
    # CLARIFICATION RESPONSE
    # ------------------------------------------------------------------

    def _handle_clarification_response(self, message: str, session_state: ConversationState,
                                       employee_id: Optional[str], session_id: str) -> ChatResponse:
        self.audit_logger.log("CLARIFICATION_RESPONSE_RECEIVED", message)

        if not session_state.current_issue:
            return self._handle_new_issue(message, session_state, employee_id, session_id)

        msg_lower = message.lower()

        # ---- KB-04 / Software installation clarification ----
        if session_state.current_intent in ("software_install", "software_catalog", "software_non_catalog"):
            in_catalog = any(w in msg_lower for w in ["yes", "yeah", "yep", "it is", "in the catalog", "in catalog", "correct"])
            not_in_catalog = any(w in msg_lower for w in ["no", "nope", "not in", "not in the catalog", "outside"])

            if in_catalog:
                decision = AgentDecision(
                    intent="software_catalog",
                    decision="RESOLVE",
                    policy_ids=["KB-04"],
                    reason="User confirmed software is in approved catalog.",
                    recommended_action="Self-install from the approved software catalog.",
                    escalation_required=False,
                    needs_clarification=False,
                    response="Since it's in the approved catalog, you can self-install it per KB-04. No IT ticket or approval is needed."
                )
            elif not_in_catalog:
                decision = AgentDecision(
                    intent="software_non_catalog",
                    decision="ESCALATE",
                    policy_ids=["KB-04"],
                    reason="User confirmed software is NOT in approved catalog — IT Security review required.",
                    recommended_action="Submit for IT Security review (3-5 business days).",
                    escalation_required=True,
                    escalation_destination="IT Security",
                    needs_clarification=False,
                    response="Since that software isn't in the approved catalog, KB-04 requires an IT Security review. This typically takes 3-5 business days. I'm escalating this to IT Security for you."
                )
            else:
                # Ambiguous — ask again
                response = "To help with your software request, could you confirm: is the software available in the Veridian approved software catalog?"
                self.conversation_manager.add_to_history(session_id, "assistant", response)
                self.conversation_manager.update_session(session_id, previous_agent_message=response)
                self.audit_logger.log("CLARIFICATION_REQUESTED", "Repeated catalog check")
                return ChatResponse(
                    response=response,
                    decision="CLARIFY",
                    policy_sources=["KB-04"],
                    recommended_action="Confirm whether software is in approved catalog",
                    ticket=None,
                    audit=self._build_audit_trail()
                )

        # ---- KB-05 / Printer asset tag clarification ----
        elif session_state.current_intent == "printer_issue":
            # User is providing the asset tag
            response = self._continue_printer_workflow(message, session_state, employee_id, session_id)
            self.conversation_manager.add_to_history(session_id, "assistant", response)
            self.conversation_manager.update_session(
                session_id,
                pending_clarification=None,
                previous_agent_message=response
            )
            return ChatResponse(
                response=response,
                decision="ROUTE",
                policy_sources=["KB-05"],
                recommended_action="Ticket logged with asset tag",
                ticket=None,
                audit=self._build_audit_trail()
            )

        # ---- KB-10 / Home equipment days clarification ----
        elif session_state.current_intent in ("home_equipment", "home_equipment_eligible"):
            combined = f"{session_state.current_issue} {message}"
            decision = self.policy_engine.evaluate_request(combined, employee_id)
        
        # ---- KB-03 / Laptop age/type clarification ----
        elif session_state.current_intent in ("laptop_issue", "laptop_repair", "laptop_replacement"):
            combined = f"{session_state.current_issue} {message}"
            decision = self.policy_engine.evaluate_request(combined, employee_id)

        else:
            # Generic: re-evaluate with combined context
            combined = f"{session_state.current_issue} {message}"
            decision = self.policy_engine.evaluate_request(combined, employee_id)

        self.audit_logger.log("INTENT_IDENTIFIED", decision.intent)
        for pid in decision.policy_ids:
            self.audit_logger.log("POLICY_RETRIEVED", pid)
        self.audit_logger.log("DECISION", decision.decision)

        self.conversation_manager.update_session(
            session_id,
            current_intent=decision.intent,
            current_policy_id=decision.policy_ids[0] if decision.policy_ids else None,
            current_decision=decision.decision,
            pending_clarification=None
        )

        ticket = None
        if decision.escalation_required:
            ticket = self.ticket_manager.create_ticket(
                employee=employee_id or "Unknown",
                category=decision.intent,
                issue=session_state.current_issue or message,
                source=decision.policy_ids[0] if decision.policy_ids else "Unknown",
                destination=decision.escalation_destination
            )
            self.audit_logger.log("TICKET_CREATED", f"{ticket.ticket_id} -> {ticket.destination}")
            self.conversation_manager.update_session(session_id, current_ticket_id=ticket.ticket_id)

        response = self._generate_conversational_response(
            user_message=message,
            decision=decision,
            session_state=session_state,
            context="clarification_response"
        )

        self.conversation_manager.add_to_history(session_id, "assistant", response)
        self.conversation_manager.update_session(session_id, previous_agent_message=response)

        return ChatResponse(
            response=response,
            decision=decision.decision,
            policy_sources=decision.policy_ids,
            recommended_action=decision.recommended_action,
            ticket=ticket.dict() if ticket else None,
            audit=self._build_audit_trail()
        )

    # ------------------------------------------------------------------
    # FOLLOW-UP
    # ------------------------------------------------------------------

    def _handle_follow_up(self, message: str, session_state: ConversationState,
                          employee_id: Optional[str], session_id: str) -> ChatResponse:
        self.audit_logger.log("FOLLOW_UP_DETECTED", message[:80])

        if not session_state.current_policy_id:
            return self._handle_new_issue(message, session_state, employee_id, session_id)

        # Fetch the current policy
        policy = next(
            (p for p in self.retrieval.get_all_policies() if p.id == session_state.current_policy_id),
            None
        )

        if not policy:
            response = ("I don't have enough context to answer that. "
                        "Could you clarify what you'd like to know?")
        else:
            response = self._generate_follow_up_response(message, policy, session_state)

        self.conversation_manager.add_to_history(session_id, "assistant", response)
        self.conversation_manager.update_session(session_id, previous_agent_message=response)

        return ChatResponse(
            response=response,
            decision=session_state.current_decision or "RESOLVE",
            policy_sources=[session_state.current_policy_id] if session_state.current_policy_id else [],
            recommended_action="Follow-up answered in context",
            ticket=None,
            audit=self._build_audit_trail()
        )

    def _generate_follow_up_response(self, message: str, policy, session_state: ConversationState) -> str:
        """Generate a contextual follow-up response using the LLM when available."""
        msg_lower = message.lower()

        if self.groq_client:
            history_str = self._format_history_for_llm(session_state.conversation_history[-6:])
            prompt = f"""You are Veridian Corp's Internal IT Support Agent. 
The employee is asking a follow-up question in an ongoing conversation.

CONVERSATION SO FAR:
{history_str}

CURRENT POLICY IN CONTEXT ({policy.id} — {policy.title}):
{policy.content}

EMPLOYEE FOLLOW-UP: "{message}"

Instructions:
- Answer using ONLY the policy content above. Do not invent procedures, timelines, or workflows.
- If the policy doesn't answer the question completely, say so explicitly.
- Keep your answer concise and professional.
- Reference the policy ID ({policy.id}) naturally in your response.
- Do NOT create a ticket or escalate unless the policy explicitly says to."""

            try:
                completion = self.groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[
                        {"role": "system", "content": "You are Veridian Corp's IT Support Agent. Only use supplied policy facts. Never invent information."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=350
                )
                return completion.choices[0].message.content
            except Exception:
                pass  # Fall through to deterministic fallback

        # Deterministic fallback
        if any(w in msg_lower for w in ["why", "reason", "because"]):
            if "reason" in policy.content.lower() or "because" in policy.content.lower():
                return f"Based on {policy.id}: {policy.content}"
            else:
                return (f"{policy.id} states: \"{policy.content}\" "
                        f"The policy does not provide an explicit reason for this requirement.")

        elif any(w in msg_lower for w in ["how", "what do i do", "what should i do", "what now", "what next"]):
            return f"According to {policy.id}: {policy.content}"

        elif any(w in msg_lower for w in ["understand", "explain", "mean", "clarify"]):
            return (f"Let me explain: {policy.id} ({policy.title}) states that {policy.content} "
                    f"If you'd like, I can escalate to IT for further assistance.")

        elif any(w in msg_lower for w in ["renew", "renewal", "how do i renew"]):
            if "renew" in policy.content.lower():
                return f"According to {policy.id}: {policy.content}"
            else:
                return (f"{policy.id} confirms the requirement but does not describe the exact renewal procedure. "
                        f"I'd recommend escalating to IT so they can walk you through the steps.")

        else:
            return f"Based on {policy.id} — {policy.title}: {policy.content}"

    # ------------------------------------------------------------------
    # CORRECTION
    # ------------------------------------------------------------------

    def _handle_correction(self, message: str, session_state: ConversationState,
                           employee_id: Optional[str], session_id: str) -> ChatResponse:
        self.audit_logger.log("CORRECTION_DETECTED", message[:80])

        # Re-evaluate the original issue with the corrected attribute in mind.
        # Combine original issue + correction so the policy engine has full context.
        base_issue = session_state.current_issue or ""
        combined = f"{base_issue} {message}".strip()

        # Clear ticket so we don't accidentally reuse the old ticket
        self.conversation_manager.update_session(session_id, current_ticket_id=None)
        return self._handle_new_issue(combined, session_state, employee_id, session_id)

    # ------------------------------------------------------------------
    # ALREADY TRIED
    # ------------------------------------------------------------------

    def _handle_already_tried(self, message: str, session_state: ConversationState,
                              employee_id: Optional[str], session_id: str) -> ChatResponse:
        self.audit_logger.log("FOLLOW_UP_DETECTED", f"User already tried something: {message[:60]}")

        policy_id = session_state.current_policy_id
        policy = next(
            (p for p in self.retrieval.get_all_policies() if p.id == policy_id),
            None
        )

        # KB-09 security context: user took an action (forwarded, clicked, etc.)
        # Stay strictly in KB-09, do NOT re-evaluate policy
        if session_state.in_security_context or policy_id == "KB-09":
            msg_lower = message.lower()
            if any(w in msg_lower for w in ["forwarded", "forward", "sent it", "shared it", "shared"]):
                response = (
                    "That is important to flag - per KB-09, the phishing email should NOT be forwarded "
                    "to others, as it risks spreading the threat. Please let your colleagues know "
                    "directly that they may have received a suspicious email and should not open it. "
                    "The security team has been notified and is investigating. "
                    "Your escalation ticket remains open."
                )
            elif any(w in msg_lower for w in ["clicked", "opened", "downloaded", "open it"]):
                response = (
                    "That is a serious concern. Per KB-09, please immediately report this to the "
                    "security team if you have not already. Avoid using the device for sensitive work "
                    "until the security team has assessed it. Your escalation ticket is still active."
                )
            else:
                response = (
                    "Understood. The security team has been notified per KB-09 and will follow up. "
                    "Please avoid interacting further with the suspicious email or any links it contained."
                )
            self.conversation_manager.add_to_history(session_id, "assistant", response)
            self.conversation_manager.update_session(session_id, previous_agent_message=response)
            return ChatResponse(
                response=response,
                decision="ESCALATE",
                policy_sources=["KB-09"],
                recommended_action="Security context maintained - user action noted",
                ticket=None,
                audit=self._build_audit_trail()
            )

        # KB-05: Printer — if spooler restart already done, ask for asset tag
        if policy_id == "KB-05":
            msg_lower = message.lower()
            if any(w in msg_lower for w in ["spooler", "queue", "restart", "restarted"]):
                self.conversation_manager.update_session(
                    session_id,
                    troubleshooting_steps_done=session_state.troubleshooting_steps_done + ["restart_spooler"],
                    pending_clarification="Please provide the printer's asset tag to log a support ticket."
                )
                response = (
                    "Understood — since you've already restarted the spooler and the issue persists, "
                    "the next step per KB-05 is to log a ticket with the printer's asset tag. "
                    "Could you please provide the asset tag for the printer? "
                    "(It's usually a sticker on the device.)"
                )
                self.conversation_manager.add_to_history(session_id, "assistant", response)
                self.conversation_manager.update_session(session_id, previous_agent_message=response)
                self.audit_logger.log("CLARIFICATION_REQUESTED", "Asset tag needed for KB-05 ticket")
                return ChatResponse(
                    response=response,
                    decision="CLARIFY",
                    policy_sources=["KB-05"],
                    recommended_action="Request asset tag to log printer ticket",
                    ticket=None,
                    audit=self._build_audit_trail()
                )

        # Generic: use LLM or deterministic fallback to continue the workflow
        if self.groq_client and policy:
            history_str = self._format_history_for_llm(session_state.conversation_history[-6:])
            prompt = f"""You are Veridian Corp's IT Support Agent.
The employee says they have already tried the step you suggested, but the problem continues.

CONVERSATION SO FAR:
{history_str}

POLICY IN CONTEXT ({policy.id}):
{policy.content}

EMPLOYEE: "{message}"

Reply with the NEXT step from the policy. 
- Do NOT repeat a step the user already said they've done.
- If the policy is exhausted, escalate and explain why.
- Do not invent steps not in the policy.
- Be concise and professional."""
            try:
                completion = self.groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[
                        {"role": "system", "content": "Veridian IT Support Agent. Strictly policy-grounded."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=300
                )
                response = completion.choices[0].message.content
            except Exception:
                response = self._fallback_already_tried(policy, session_state)
        elif policy:
            response = self._fallback_already_tried(policy, session_state)
        else:
            response = ("I understand that step didn't resolve the issue. "
                        "Let me escalate this to IT for further assistance.")

        self.conversation_manager.add_to_history(session_id, "assistant", response)
        self.conversation_manager.update_session(session_id, previous_agent_message=response)

        return ChatResponse(
            response=response,
            decision=session_state.current_decision or "RESOLVE",
            policy_sources=[policy_id] if policy_id else [],
            recommended_action="Continued troubleshooting after repeated attempt",
            ticket=None,
            audit=self._build_audit_trail()
        )

    def _fallback_already_tried(self, policy, session_state: ConversationState) -> str:
        return (f"Since that step hasn't resolved the issue, per {policy.id} the next step is to "
                f"escalate to IT with full details. {policy.content}")

    # ------------------------------------------------------------------
    # TICKET STATUS QUERY
    # ------------------------------------------------------------------

    def _handle_ticket_status_query(self, message: str, session_state: ConversationState,
                                    employee_id: Optional[str], session_id: str) -> ChatResponse:
        self.audit_logger.log("FOLLOW_UP_DETECTED", "Ticket status query")

        # Search existing ticket data (both original and generated)
        all_tickets = list(self.retrieval.get_all_tickets()) + self.ticket_manager.get_generated_tickets()

        # Filter by employee if known
        emp_tickets = []
        if employee_id:
            emp_request = self.retrieval.get_employee_request(request_id=employee_id)
            emp_name = emp_request.employee if emp_request else ""
            emp_tickets = [t for t in all_tickets
                           if emp_name and emp_name.split()[0].lower() in (t.employee or "").lower()]

        # Also search by keywords from the message
        msg_lower = message.lower()
        keyword_tickets = [t for t in all_tickets
                           if any(kw in t.issue.lower()
                                  for kw in ["laptop", "vpn", "printer", "mailbox", "password",
                                             "phishing", "software", "home", "expense"]
                                  if kw in msg_lower)]

        # Also check the current session ticket
        session_ticket = None
        if session_state.current_ticket_id:
            session_ticket = next(
                (t for t in self.ticket_manager.get_generated_tickets()
                 if t.ticket_id == session_state.current_ticket_id),
                None
            )

        # Decide what to report
        found_tickets = session_ticket and [session_ticket] or emp_tickets or keyword_tickets

        if found_tickets:
            t = found_tickets[0]
            # Handle both Ticket and GeneratedTicket (one has is_active, other has status)
            status = getattr(t, "status", "Unknown")
            is_active = getattr(t, "is_active", True)
            ticket_id = getattr(t, "ticket_id", "Unknown")

            if is_active:
                response = (f"Your ticket **{ticket_id}** is currently active — "
                            f"Status: *{status}*. "
                            f"No new ticket has been created. Is there anything else you need?")
            else:
                response = (f"Ticket **{ticket_id}** has been closed — "
                            f"Status: *{status}*. "
                            f"If you're still experiencing the same issue, I can open a new request.")
            self.audit_logger.log("POLICY_RETRIEVED", f"Ticket {ticket_id} status returned")
        else:
            response = ("I couldn't find an existing ticket for your request in the supplied ticket data. "
                        "If you have a specific ticket number, please share it and I'll look it up.")

        self.conversation_manager.add_to_history(session_id, "assistant", response)
        self.conversation_manager.update_session(session_id, previous_agent_message=response)

        return ChatResponse(
            response=response,
            decision=session_state.current_decision or "RESOLVE",
            policy_sources=[],
            recommended_action="Ticket status retrieved from supplied data",
            ticket=None,
            audit=self._build_audit_trail()
        )

    # ------------------------------------------------------------------
    # MULTI-INTENT
    # ------------------------------------------------------------------

    def _handle_multi_intent(self, message: str, session_state: ConversationState,
                             employee_id: Optional[str], session_id: str) -> ChatResponse:
        self.audit_logger.log("MULTI_INTENT_DETECTED", message[:80])

        # Split on common conjunctions, preserving both parts
        parts = []
        for sep in [" and ", " also ", " plus ", " as well as "]:
            if sep in message.lower():
                idx = message.lower().index(sep)
                parts = [message[:idx].strip(), message[idx + len(sep):].strip()]
                break

        if len(parts) < 2:
            return self._handle_new_issue(message, session_state, employee_id, session_id)

        first_part, second_part = parts[0], parts[1]

        # Evaluate first issue
        first_decision = self.policy_engine.evaluate_request(first_part, employee_id)
        for pid in first_decision.policy_ids:
            self.audit_logger.log("POLICY_RETRIEVED", pid)

        # Create ticket for first issue only if required
        ticket = None
        if first_decision.escalation_required:
            ticket = self.ticket_manager.create_ticket(
                employee=employee_id or "Unknown",
                category=first_decision.intent,
                issue=first_part,
                source=first_decision.policy_ids[0] if first_decision.policy_ids else "Unknown",
                destination=first_decision.escalation_destination
            )
            self.audit_logger.log("TICKET_CREATED", f"{ticket.ticket_id} -> {ticket.destination}")

        # Store secondary issue
        self.conversation_manager.update_session(
            session_id,
            current_issue=first_part,
            current_intent=first_decision.intent,
            current_policy_id=first_decision.policy_ids[0] if first_decision.policy_ids else None,
            current_decision=first_decision.decision,
            secondary_issue=second_part,
            pending_clarification=first_decision.recommended_action if first_decision.needs_clarification else None,
            in_security_context=(first_decision.intent == "security_incident"),
            current_ticket_id=ticket.ticket_id if ticket else None
        )

        self.audit_logger.log("DECISION", f"MULTI-INTENT: {first_decision.decision} (first: {first_part[:40]}...)")

        # Build combined response
        first_response = first_decision.response
        combined_response = (
            f"I can help with both. Let's address the first issue first.\n\n"
            f"**Issue 1 — {first_part}:**\n{first_response}\n\n"
            f"**Issue 2 — {second_part}:**\nOnce we've sorted the first, send me a message about this "
            f"and I'll look it up right away."
        )

        all_policy_ids = list(first_decision.policy_ids)

        self.conversation_manager.add_to_history(session_id, "assistant", combined_response)
        self.conversation_manager.update_session(session_id, previous_agent_message=combined_response)

        return ChatResponse(
            response=combined_response,
            decision=first_decision.decision,
            policy_sources=all_policy_ids,
            recommended_action=f"Multi-intent: handling '{first_part[:40]}' first",
            ticket=ticket.dict() if ticket else None,
            audit=self._build_audit_trail()
        )

    # ------------------------------------------------------------------
    # OUT OF SCOPE
    # ------------------------------------------------------------------

    def _handle_out_of_scope(self, session_state: ConversationState, session_id: str) -> ChatResponse:
        self.audit_logger.log("OUT_OF_SCOPE", "Query outside IT support scope")

        response = ("I can help with Veridian internal IT support, but I don't have "
                    "information about that topic. Is there an IT-related issue I can assist you with?")

        self.conversation_manager.add_to_history(session_id, "assistant", response)
        self.conversation_manager.update_session(session_id, previous_agent_message=response)

        return ChatResponse(
            response=response,
            decision="RESOLVE",
            policy_sources=[],
            recommended_action="Out of scope — no IT policy applied",
            ticket=None,
            audit=self._build_audit_trail()
        )

    # ------------------------------------------------------------------
    # POLICY INFO QUESTION (no incident / no ticket)
    # ------------------------------------------------------------------

    def _handle_policy_question(self, message: str, session_state: ConversationState,
                                session_id: str) -> ChatResponse:
        self.audit_logger.log("POLICY_INFO_QUESTION", message[:80])

        policies = self.retrieval.search_knowledge_base(message)
        if policies:
            policy = policies[0]
            self.audit_logger.log("POLICY_RETRIEVED", policy.id)
            response = f"According to {policy.id} ({policy.title}): {policy.content}"
        else:
            response = ("I don't have specific policy information about that in the Veridian knowledge base. "
                        "Could you clarify what policy you're asking about?")

        self.conversation_manager.add_to_history(session_id, "assistant", response)
        self.conversation_manager.update_session(session_id, previous_agent_message=response)

        return ChatResponse(
            response=response,
            decision="RESOLVE",
            policy_sources=[policies[0].id] if policies else [],
            recommended_action="Policy information provided — no ticket required",
            ticket=None,
            audit=self._build_audit_trail()
        )

    # ------------------------------------------------------------------
    # Printer workflow helper
    # ------------------------------------------------------------------

    def _continue_printer_workflow(self, message: str, session_state: ConversationState,
                                   employee_id: Optional[str], session_id: str) -> str:
        """Handle asset tag provision for KB-05."""
        # Check if the message looks like an asset tag or a "no" answer
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["no", "don't have", "don't know", "not sure", "i don't"]):
            return (
                "No problem. Please check the sticker on the printer for the asset tag "
                "and come back when you have it. Alternatively, you can ask your facilities "
                "team for the asset tag and I'll log the ticket then."
            )
        else:
            # Treat the message as the asset tag value
            asset_tag = message.strip()
            ticket = self.ticket_manager.create_ticket(
                employee=employee_id or "Unknown",
                category="printer_issue",
                issue=f"Printer issue — asset tag: {asset_tag}. Steps already tried: restart spooler.",
                source="KB-05",
                destination="IT"
            )
            self.audit_logger.log("TICKET_CREATED", f"{ticket.ticket_id} -> IT (printer)")
            self.conversation_manager.update_session(session_id, current_ticket_id=ticket.ticket_id)
            return (
                f"Got it. I've logged a printer support ticket ({ticket.ticket_id}) for asset tag "
                f"**{asset_tag}** and routed it to the IT team. Per KB-05, a technician will follow up. "
                f"Is there anything else I can help you with?"
            )

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------

    def _generate_conversational_response(self, user_message: str, decision: AgentDecision,
                                          session_state: ConversationState, context: str) -> str:
        """
        Generate a natural-sounding response using the LLM with conversation history context.
        Falls back to the deterministic policy engine response if LLM unavailable.
        """
        # Always start from the policy-grounded response
        base_response = decision.response
        if not base_response or len(base_response) < 15:
            base_response = decision.recommended_action or "Your request has been processed."

        if not self.groq_client:
            return base_response

        history_str = self._format_history_for_llm(session_state.conversation_history[-8:])

        system_prompt = """You are Veridian Corp's Internal IT Support Agent.

STRICT RULES:
- Use ONLY the supplied policy facts provided below. Never invent timelines, approval workflows, departments, or procedures.
- Never claim an action occurred unless the application actually performed it.
- Closed tickets are historical and not actionable. Active tickets are actionable.
- Security incidents must follow the supplied security policy exactly.
- Keep responses concise, professional, and easy to understand.
- Do not reveal chain-of-thought or internal reasoning."""

        user_prompt = f"""CONVERSATION HISTORY:
{history_str}

CURRENT EMPLOYEE MESSAGE: "{user_message}"

POLICY-GROUNDED DECISION:
- Intent: {decision.intent}
- Decision: {decision.decision}
- Policy IDs: {', '.join(decision.policy_ids) if decision.policy_ids else 'None'}
- Reason: {decision.reason}
- Recommended Action: {decision.recommended_action}

BASE RESPONSE TO REFINE:
{base_response}

Task: Rewrite the base response to sound more natural and conversational while staying 100% grounded in the policy facts. Keep it concise (2-4 sentences max unless complexity demands more). Reference the policy ID where relevant."""

        try:
            completion = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.25,
                max_tokens=400
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"LLM error: {e}")
            return base_response

    def _call_llm_simple(self, prompt: str) -> str:
        """Simple single-turn LLM call for short conversational responses."""
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are Veridian Corp's IT Support Agent. Be concise and professional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=150
            )
            return completion.choices[0].message.content
        except Exception:
            return "Understood. Let me know if you need anything else."

    def _format_history_for_llm(self, history: list) -> str:
        """Format conversation history as a readable string for the LLM."""
        if not history:
            return "(No prior conversation)"
        lines = []
        for entry in history:
            role = "Employee" if entry.get("role") == "user" else "IT Agent"
            lines.append(f"{role}: {entry.get('content', '')}")
        return "\n".join(lines)

    def _build_audit_trail(self) -> list:
        return [
            {
                "timestamp": event.timestamp,
                "event": event.event_type,
                "details": event.details
            }
            for event in self.audit_logger.get_events()
        ]
