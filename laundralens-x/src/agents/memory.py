"""
LaundraLens X — Case Memory Manager
Maintains in-memory and database-backed audit log of investigation state and tool interactions.
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.db.models import CaseMemory


class CaseMemoryManager:
    def __init__(self, case_id: str, db: Optional[Session] = None):
        self.case_id = case_id
        self.db = db
        self._local_memory: List[Dict[str, Any]] = []

    def record_step(self, memory_type: str, key: str, value: Any):
        entry = {
            "memory_id": f"MEM-{uuid.uuid4().hex[:8]}",
            "case_id": self.case_id,
            "memory_type": memory_type,
            "key": key,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._local_memory.append(entry)

        if self.db:
            mem = CaseMemory(
                memory_id=entry["memory_id"],
                case_id=self.case_id,
                memory_type=memory_type,
                key=key,
                value=value,
            )
            self.db.add(mem)
            self.db.commit()

    def get_history(self) -> List[Dict[str, Any]]:
        return self._local_memory
