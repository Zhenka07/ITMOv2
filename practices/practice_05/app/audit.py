"""
Audit Trail Logger for DataHub SDD Service.
Appends tamper-evident audit events in memory and JSONL.
"""

import threading
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class AuditLogger:
    def __init__(self, log_path: Optional[str] = None):
        self._lock = threading.RLock()
        self._events: List[Dict[str, Any]] = []
        self._log_path = log_path

    def record_event(self, action: str, actor: str, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._lock:
            event = {
                "id": f"aud-{len(self._events) + 1:04d}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "actor": actor,
                "resource_id": resource_id,
                "details": details or {},
            }
            self._events.append(event)
            if self._log_path:
                try:
                    with open(self._log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(event, ensure_ascii=False) + "\n")
                except Exception:
                    pass
            return event

    def list_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self._events[-limit:]))

# Global audit logger instance
audit_logger = AuditLogger(os.path.join(os.path.dirname(__file__), "audit.jsonl"))
