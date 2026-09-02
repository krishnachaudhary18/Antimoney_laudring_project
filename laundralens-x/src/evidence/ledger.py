"""
LaundraLens X — Evidence Ledger
Structured registry and indexing of forensic evidence items.
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Any, Optional


class EvidenceLedger:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self._entries: List[Dict[str, Any]] = []

    def record_evidence(
        self,
        evidence_type: str,
        source_tool: str,
        value: Any,
        calculation: Optional[str] = None,
        explanation: Optional[str] = None,
        account_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        item = {
            "evidence_id": f"EV-{uuid.uuid4().hex[:6].upper()}",
            "case_id": self.case_id,
            "evidence_type": evidence_type,
            "source": source_tool,
            "value": value,
            "calculation": calculation,
            "explanation": explanation,
            "account_id": account_id,
            "transaction_id": transaction_id,
        }
        self._entries.append(item)
        return item

    def all_items(self) -> List[Dict[str, Any]]:
        return list(self._entries)

    def filter_by_type(self, evidence_type: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["evidence_type"] == evidence_type]
