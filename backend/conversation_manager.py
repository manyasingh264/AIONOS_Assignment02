from typing import Optional, List, Dict
from datetime import datetime
from models import ConversationState, MessageClassification


class ConversationManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationState] = {}

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def get_or_create_session(self, session_id: str, employee_id: Optional[str] = None) -> ConversationState:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationState(
                session_id=session_id,
                employee_id=employee_id
            )
        elif employee_id and self.sessions[session_id].employee_id != employee_id:
            self.sessions[session_id].employee_id = employee_id
        return self.sessions[session_id]

    def update_session(self, session_id: str, **updates):
        if session_id in self.sessions:
            for key, value in updates.items():
                if hasattr(self.sessions[session_id], key):
                    setattr(self.sessions[session_id], key, value)
            self.sessions[session_id].updated_at = datetime.now().isoformat()

    def add_to_history(self, session_id: str, role: str, content: str):
        if session_id in self.sessions:
            self.sessions[session_id].conversation_history.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            self.sessions[session_id].updated_at = datetime.now().isoformat()

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    # ------------------------------------------------------------------
    # Message classification — order matters!
    # ------------------------------------------------------------------

    def classify_message(self, message: str, session_state: ConversationState) -> MessageClassification:
        msg = message.lower().strip()

        # 1. Human handoff (highest priority)
        if self._is_human_handoff(msg):
            return MessageClassification(
                message_type="HUMAN_HANDOFF_REQUEST",
                confidence=0.95,
                context_update={}
            )

        # 2. Out-of-scope (before everything else so we don't waste policy searches)
        if self._is_out_of_scope(msg):
            return MessageClassification(
                message_type="OUT_OF_SCOPE",
                confidence=0.85,
                context_update={}
            )

        # 3. Ticket status query ("what's the status of my ticket", "is my request still open")
        if self._is_ticket_status_query(msg):
            return MessageClassification(
                message_type="TICKET_STATUS_QUERY",
                confidence=0.88,
                context_update={}
            )

        # 4. Explicit topic-change correction ("actually my printer is broken")
        #    Check BEFORE acknowledgement / clarification so "actually" sentences don't
        #    get swallowed by the acknowledgement detector.
        if session_state.current_issue and self._is_topic_change(msg, session_state):
            return MessageClassification(
                message_type="NEW_ISSUE",
                confidence=0.75,
                context_update={"topic_changed": True}
            )

        # 5. Attribute correction ("actually I'm a full-time employee", "wait, I meant...")
        if self._is_correction(msg, session_state):
            return MessageClassification(
                message_type="CORRECTION",
                confidence=0.82,
                context_update={}
            )

        # 6a. Conversation closing — "no" after "Is there anything else?" type message
        #     Must run BEFORE CLARIFICATION_RESPONSE so "no" isn't mis-routed to KB logic.
        if self._is_conversation_close(msg, session_state):
            return MessageClassification(
                message_type="ACKNOWLEDGEMENT",
                confidence=0.92,
                context_update={"conversation_closing": True}
            )

        # 6b. CLARIFICATION_RESPONSE — only if there is still an outstanding question
        if session_state.pending_clarification and self._is_clarification_response(msg):
            return MessageClassification(
                message_type="CLARIFICATION_RESPONSE",
                confidence=0.88,
                context_update={"clarification_answer": message}
            )

        # 7. Pure acknowledgements ("ok", "thanks", "got it", "understood"…)
        if self._is_acknowledgement(msg):
            return MessageClassification(
                message_type="ACKNOWLEDGEMENT",
                confidence=0.90,
                context_update={}
            )

        # 8. "I already tried that / it still doesn't work"
        if session_state.current_issue and self._is_already_tried(msg):
            return MessageClassification(
                message_type="ALREADY_TRIED",
                confidence=0.82,
                context_update={}
            )

        # 9. Follow-up questions ("what do I do now", "why", "how do I fix it"…)
        if self._is_follow_up(msg) and session_state.current_issue:
            return MessageClassification(
                message_type="FOLLOW_UP",
                confidence=0.78,
                context_update={}
            )

        # 10. Multi-intent ("my VPN stopped working and my mailbox is full")
        if self._is_multi_intent(msg):
            return MessageClassification(
                message_type="MULTI_INTENT",
                confidence=0.72,
                context_update={}
            )

        # 11. Policy information questions (no incident / no ticket)
        if self._is_policy_question(msg):
            return MessageClassification(
                message_type="POLICY_INFO_QUESTION",
                confidence=0.75,
                context_update={}
            )

        # 12. Default: treat as new IT support issue
        return MessageClassification(
            message_type="NEW_ISSUE",
            confidence=0.60,
            context_update={}
        )

    # ------------------------------------------------------------------
    # Detectors
    # ------------------------------------------------------------------

    def _is_acknowledgement(self, msg: str) -> bool:
        """
        Use word-boundary matching to avoid false positives on words that
        *contain* an ack word (e.g. "define", "refine", "confirm", "fine report").
        """
        ack_words = {
            "ok", "okay", "thanks", "thank you", "got it", "understood",
            "alright", "noted", "acknowledged", "sounds good", "makes sense",
            "appreciate it", "great", "perfect", "cheers"
        }
        words = set(msg.replace(",", " ").replace(".", " ").split())
        # Match whole phrases
        for ack in ack_words:
            if ack in words or msg.startswith(ack) or msg == ack:
                return True
        return False

    def _is_human_handoff(self, msg: str) -> bool:
        phrases = [
            "talk to a human", "talk to someone", "talk to a person",
            "speak to a human", "speak to someone", "speak to a person", "speak to it",
            "i want to talk to", "need a human", "get me a human", "i need a human",
            "can someone help", "can i speak to",
            "i don't understand this. can someone",
            "want to speak to it", "connect me to it", "real person", "support person",
            "human agent", "human support", "live agent", "live person",
        ]
        return any(phrase in msg for phrase in phrases)

    def _is_conversation_close(self, msg: str, session_state) -> bool:
        """
        Detect when the user is closing the conversation after an 'anything else?' prompt.
        Prevents 'no' from being mis-classified as CLARIFICATION_RESPONSE.
        Uses word-set matching to avoid substring false positives (e.g. 'no' in 'now').
        """
        closing_phrases = {
            "no", "nope", "nah", "nothing", "that's all", "thats all",
            "i'm good", "im good", "all good", "i'm fine", "im fine",
            "no thanks", "no thank you", "not right now", "nothing else",
            "that's it", "thats it", "no more", "i'm okay", "im okay",
        }
        msg_clean = msg.strip().rstrip('.').rstrip('!')
        # Word-set for single-word matches — avoids 'no' matching inside 'now'/'know'
        words = set(msg_clean.replace(',', ' ').replace('?', ' ').split())

        is_closing_msg = (
            msg_clean in closing_phrases or               # exact full-message match
            any(
                (len(p.split()) == 1 and p in words) or  # single-word: whole-word match
                (len(p.split()) > 1 and p in msg_clean)  # multi-word phrase: substring ok
                for p in closing_phrases
            )
        )
        if not is_closing_msg:
            return False

        # Only treat as closing if the previous agent message invited a closing
        prev = (session_state.previous_agent_message or "").lower()
        closing_prompts = [
            "anything else", "anything more", "further assistance",
            "help you with anything", "need anything else", "anything i can",
            "is there anything", "let me know if",
        ]
        return any(p in prev for p in closing_prompts)

    def _is_clarification_response(self, msg: str) -> bool:
        """Detect simple yes/no and direct factual answers to a pending clarification."""
        yes_words = {"yes", "yeah", "yep", "yup", "correct", "right", "exactly", "affirmative",
                     "it is", "it's in", "in the catalog", "in catalog"}
        no_words = {"no", "nope", "not", "doesn't", "didn't", "isn't", "aren't",
                    "not in", "not in the catalog", "outside the catalog"}
        words = set(msg.replace(",", " ").replace(".", " ").split())
        return (
            any(yw in words or yw in msg for yw in yes_words) or
            any(nw in words or nw in msg for nw in no_words)
        )

    def _is_correction(self, msg: str, session_state=None) -> bool:
        correction_starters = [
            "wait,", "no, i meant", "correction:", "let me clarify",
            "i meant", "that's not right", "that's incorrect", "not exactly",
            "actually i am", "actually i'm", "actually i have", "actually i work",
        ]
        return any(msg.startswith(s) or s in msg for s in correction_starters)

    def _is_ticket_status_query(self, msg: str) -> bool:
        patterns = [
            "status of my", "status of the", "what happened to my",
            "is my ticket", "is my request", "what's happening with my",
            "whats happening with my", "my ticket", "still open", "still pending",
            "update on my", "any update", "check my ticket", "track my",
        ]
        return any(p in msg for p in patterns)

    def _is_already_tried(self, msg: str) -> bool:
        patterns = [
            "already tried", "already did", "already done", "i tried that",
            "tried that already", "still doesn't work", "still not working",
            "it's still", "its still", "still the same", "didn't fix",
            "didn't work", "didn't help", "doesn't help", "still broken",
            # Printer-specific
            "already restarted", "restarted the spooler", "restarted spooler",
            "already checked the queue", "already checked queue",
            # Security follow-up — user took an action
            "already forwarded", "i forwarded", "forwarded it", "already sent it",
            "i clicked", "i opened it", "i downloaded",
        ]
        return any(p in msg for p in patterns)

    def _is_follow_up(self, msg: str) -> bool:
        patterns = [
            "what do i do", "what should i do", "what do i need",
            "what happens next", "how do i", "how do i fix", "how long",
            "what does that mean", "why", "can you explain", "explain",
            "i don't understand", "dont understand", "i dont understand",
            "don't understand", "not sure what", "i don't get", "i dont get",
            "confused", "what now", "what next", "where do i", "when will",
            "who do i", "which", "can you clarify", "elaborate", "tell me more",
        ]
        return any(p in msg for p in patterns)

    def _is_multi_intent(self, msg: str) -> bool:
        # Need at least two distinct IT keywords separated by a conjunction
        conjunctions = [" and ", " also ", " plus ", " as well as ", " additionally ", " too. "]
        if not any(c in msg for c in conjunctions):
            return False
        # Require at least two different IT topic keywords
        topic_keyword_groups = [
            ["vpn", "remote access"],
            ["printer", "paper jam", "print"],
            ["mailbox", "quota", "email", "mail"],
            ["password", "locked", "account"],
            ["laptop", "computer"],
            ["software", "install", "extension"],
            ["wifi", "wi-fi", "guest"],
            ["expense"],
            ["phishing", "malware", "security"],
            ["home office", "monitor", "chair"],
        ]
        matched = sum(1 for group in topic_keyword_groups if any(kw in msg for kw in group))
        return matched >= 2

    def _is_out_of_scope(self, msg: str) -> bool:
        # Very specific non-IT topics
        out_of_scope = [
            "weather", "today's weather", "forecast", "sports", "football",
            "cricket", "news", "stock price", "recipe", "cook", "movie",
            "politics", "election", "personal advice", "relationship",
        ]
        return any(t in msg for t in out_of_scope)

    def _is_policy_question(self, msg: str) -> bool:
        patterns = [
            "how long do", "what is the policy", "what are the rules",
            "policy for", "policy on", "what does the policy", "how does",
            "procedure for", "what's the limit", "what is the limit",
            "how many days", "how many gb",
        ]
        return any(p in msg for p in patterns)

    def _is_topic_change(self, msg: str, session_state: ConversationState) -> bool:
        """Return True when the message is about a clearly different IT topic than the current issue."""
        if not session_state.current_issue:
            return False

        # Explicit markers of topic change
        topic_change_starters = ["actually,", "actually my", "actually the",
                                  "never mind,", "forget that,", "instead,",
                                  "switching to", "different issue", "new issue"]
        if any(msg.startswith(s) or s in msg for s in topic_change_starters):
            # Make sure it's not just a correction of an attribute (handled by _is_correction)
            if not self._is_correction(msg):
                return True

        # Heuristic: compare current topic keywords vs new message keywords
        topic_keywords = {
            "vpn": ["vpn", "remote access"],
            "password": ["password", "locked out", "unlock", "account locked"],
            "laptop": ["laptop", "computer won't", "screen flickering", "dead laptop"],
            "printer": ["printer", "paper jam", "print", "spooler"],
            "software": ["software", "install", "browser extension", "application"],
            "email": ["mailbox", "quota", "email full", "can't send"],
            "wifi": ["wifi", "wi-fi", "guest", "visitor"],
            "expense": ["expense tool", "expense software"],
            "security": ["phishing", "malware", "suspicious", "unauthorized"],
            "home": ["home office", "monitor", "chair", "work from home"],
        }

        current_topic = None
        for topic, keywords in topic_keywords.items():
            if any(kw in session_state.current_issue.lower() for kw in keywords):
                current_topic = topic
                break

        if not current_topic:
            return False

        # Only consider it a topic change if a *different* topic's keywords appear
        for topic, keywords in topic_keywords.items():
            if topic != current_topic and any(kw in msg for kw in keywords):
                return True

        return False
