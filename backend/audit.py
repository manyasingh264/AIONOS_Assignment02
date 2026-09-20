from typing import List
from datetime import datetime
from models import AuditEvent


class AuditLogger:
    def __init__(self):
        self.events: List[AuditEvent] = []

    def log(self, event_type: str, details: str) -> AuditEvent:
        event = AuditEvent(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            event_type=event_type,
            details=details
        )
        self.events.append(event)
        return event

    def get_events(self) -> List[AuditEvent]:
        return self.events

    def clear(self):
        self.events = []
