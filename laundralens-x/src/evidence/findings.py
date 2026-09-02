"""
LaundraLens X — Case Findings Manager
Structures, scores, and links findings directly to supporting forensic evidence IDs.
"""
from __future__ import annotations

import uuid
from typing import List, Dict, Any, Optional


class FindingsManager:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self._findings: List[Dict[str, Any]] = []

    def create_finding(
        self,
        category: str,
        severity: str,
        title: str,
        description: str,
        evidence_ids: Optional[List[str]] = None,
        confidence: str = "HIGH",
    ) -> Dict[str, Any]:
        finding = {
            "finding_id": f"FIND-{uuid.uuid4().hex[:6].upper()}",
            "case_id": self.case_id,
            "category": category,
            "severity": severity,
            "title": title,
            "description": description,
            "evidence_ids": evidence_ids or [],
            "confidence_label": confidence,
        }
        self._findings.append(finding)
        return finding

    def get_findings(self) -> List[Dict[str, Any]]:
        return list(self._findings)
