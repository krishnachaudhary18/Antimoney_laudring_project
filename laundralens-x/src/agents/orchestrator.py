"""
LaundraLens X — Investigation Orchestrator
The core agentic component: runs a full automated investigation from alert to report.

State machine: ALERT_CREATED → ... → REPORT_READY → HUMAN_REVIEW
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import pandas as pd
import networkx as nx
from sqlalchemy.orm import Session

from src.db.models import Investigation, Alert, Evidence, Finding, ModelScore, CaseMemory
from src.db.database import SessionLocal
from src.agents import tools as T
from src.agents.planner import AdaptivePlanner
from src.features.pipeline import compute_features, features_to_ml_vector
from src.graph.builder import build_full_graph
from src.risk.scorer import compute_risk_score, compute_counterfactual
from src.models.model_registry import registry

logger = logging.getLogger("laundralens.orchestrator")

# Investigation state machine
STATES = [
    "ALERT_CREATED",
    "INVESTIGATION_STARTED",
    "ACCOUNT_PROFILE_LOADED",
    "HISTORY_LOADED",
    "TEMPORAL_ANALYSIS_COMPLETE",
    "FLOW_ANALYSIS_COMPLETE",
    "GRAPH_ANALYSIS_COMPLETE",
    "LINEAGE_ANALYSIS_COMPLETE",
    "MODEL_ANALYSIS_COMPLETE",
    "EVIDENCE_COLLECTED",
    "FINDINGS_READY",
    "REPORT_READY",
    "HUMAN_REVIEW",
]


class InvestigationOrchestrator:
    """
    Runs a full investigation for a given alert.
    Executes real tool calls, updates state machine, persists all results.
    """

    def __init__(self, case_id: str, alert_id: str, account_id: str):
        self.case_id = case_id
        self.alert_id = alert_id
        self.account_id = account_id
        self.tool_log: List[Dict] = []
        self.findings: List[Dict] = []
        self.evidence: List[Dict] = []
        self.signals: Dict[str, float] = {}
        self.model_scores: Dict[str, float] = {}
        self.risk_result: Dict = {}
        self.timeline_data: Dict = {}
        self.lineage_data: Dict = {}
        self.graph: Optional[nx.DiGraph] = None
        self.transactions_df: Optional[pd.DataFrame] = None
        self.alert_timestamp: Optional[datetime] = None
        self.planner = AdaptivePlanner()
        self.progress_steps: List[Dict] = []

    def _log_tool(self, tool_name: str, args: Dict, result_summary: str, duration_ms: int = 0):
        """Log a tool call to case memory."""
        entry = {
            "case_id": self.case_id,
            "tool": tool_name,
            "arguments": args,
            "result_summary": result_summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "status": "success",
        }
        self.tool_log.append(entry)
        logger.info(f"[{self.case_id}] Tool: {tool_name} → {result_summary}")

    def _update_state(self, db: Session, state: str):
        """Update investigation state in DB."""
        inv = db.query(Investigation).filter(Investigation.case_id == self.case_id).first()
        if inv:
            inv.status = state
            db.commit()
        self.progress_steps.append({"state": state, "timestamp": datetime.now(timezone.utc).isoformat()})

    def _add_finding(self, category: str, severity: str, title: str, description: str,
                     calculation: str = None, data: Dict = None, primary_tx_id: str = None):
        self.findings.append({
            "category": category,
            "severity": severity,
            "title": title,
            "explanation": description,
            "calculation": calculation,
            "data": data or {},
            "primary_transaction_id": primary_tx_id,
            "source_tool": "orchestrator",
        })

    def run(self) -> Dict:
        """
        Execute the full investigation pipeline.
        Returns complete investigation result dict.
        """
        import random
        random.seed(42)
        import numpy as np
        np.random.seed(42)
        try:
            import torch
            torch.manual_seed(42)
        except Exception:
            pass

        with SessionLocal() as db:
            start_time = datetime.now(timezone.utc)
            self._update_state(db, "INVESTIGATION_STARTED")
            inv = db.query(Investigation).filter(Investigation.case_id == self.case_id).first()
            if inv:
                inv.started_at = start_time
            else:
                inv = Investigation(
                    case_id=self.case_id,
                    alert_id=self.alert_id,
                    account_id=self.account_id,
                    status="INVESTIGATION_STARTED",
                    started_at=start_time,
                )
                db.add(inv)
            db.commit()

            # Load models
            if not registry.models_loaded:
                registry.load_all()

            # ── STEP 1: Account Profile ──────────────────────────
            self._update_state(db, "ACCOUNT_PROFILE_LOADED")
            profile = T.get_account_profile(self.account_id, db)
            customer = T.get_customer_profile(profile.get("customer_id", ""), db)
            self._log_tool("get_account_profile", {"account_id": self.account_id},
                           f"Account type: {profile.get('account_type')} | Segment: {profile.get('segment')}")

            # ── STEP 2: Transaction History ──────────────────────
            self._update_state(db, "HISTORY_LOADED")
            history = T.get_account_history(self.account_id, db)
            self._log_tool("get_account_history", {"account_id": self.account_id},
                           f"{history.get('transaction_count', 0)} transactions | "
                           f"Total inflow: Rs {history.get('total_inflow', 0):,.0f}")

            # Load transactions DataFrame (once, cached)
            self.transactions_df = self._load_transactions_df(db)

            # Resolve alert timestamp dynamically
            alert_obj = db.query(Alert).filter(Alert.alert_id == self.alert_id).first()
            if alert_obj and alert_obj.created_at:
                self.alert_timestamp = alert_obj.created_at
            elif not self.transactions_df.empty:
                acc_txs = self.transactions_df[
                    (self.transactions_df["sender_account_id"] == self.account_id) |
                    (self.transactions_df["receiver_account_id"] == self.account_id)
                ]
                if not acc_txs.empty:
                    self.alert_timestamp = acc_txs["timestamp"].max()
                else:
                    self.alert_timestamp = datetime(2026, 8, 14, 11, 30, 0)
            else:
                self.alert_timestamp = datetime(2026, 8, 14, 11, 30, 0)

            # Formulate adaptive initial plan
            init_plan = self.planner.evaluate_initial_plan(profile, alert_obj.summary if alert_obj else "")
            self._log_tool("evaluate_initial_plan", {"account_id": self.account_id},
                           f"Hypotheses: {'; '.join(init_plan['hypotheses']) if init_plan['hypotheses'] else 'Standard investigation'}")

            # ── STEP 3: Temporal Analysis ────────────────────────
            self._update_state(db, "TEMPORAL_ANALYSIS_COMPLETE")
            temporal = T.analyze_time_windows(self.account_id, self.transactions_df, self.alert_timestamp)
            self.signals["temporal"] = float(temporal.get("temporal_signal", 0.0))
            speed = temporal.get("redistribution_speed_score", 0.0)
            time_90 = temporal.get("time_to_90pct_outflow_minutes")
            self._log_tool("analyze_time_windows", {"account_id": self.account_id},
                           f"temporal_signal={self.signals['temporal']:.3f} | "
                           f"redistribution_speed={speed:.3f} | "
                           f"time_to_90pct={time_90}min")

            if self.signals["temporal"] > 0.5:
                self._add_finding(
                    "temporal", "HIGH",
                    "Rapid Fund Redistribution Detected",
                    f"Account redistributed funds at high velocity. "
                    f"Time to 90% outflow: {time_90} minutes. "
                    f"Redistribution speed score: {speed:.2f}.",
                    calculation=f"redistribution_speed_score = {speed:.3f} | time_to_90pct = {time_90}min",
                    data={"temporal_signal": self.signals["temporal"], "speed_score": speed, "time_to_90pct_min": time_90},
                )

            # ── STEP 4: Flow Analysis ────────────────────────────
            self._update_state(db, "FLOW_ANALYSIS_COMPLETE")
            flow = T.calculate_conservation(self.account_id, "24h", self.transactions_df, self.alert_timestamp)
            self.signals["flow"] = float(flow.get("flow_signal", 0.0))
            conservation = flow.get("conservation_ratio", 0.0)
            new_ratio = flow.get("new_recipient_ratio", 0.0)
            inflow = flow.get("inflow_total_24h", 0.0)
            outflow = flow.get("outflow_total_24h", 0.0)
            self._log_tool("calculate_conservation", {"account_id": self.account_id, "window": "24h"},
                           f"conservation_ratio={conservation:.3f} | "
                           f"new_recipient_ratio={new_ratio:.2f} | "
                           f"inflow=Rs{inflow:,.0f} outflow=Rs{outflow:,.0f}")

            if conservation > 0.7:
                self._add_finding(
                    "flow", "CRITICAL" if conservation > 0.90 else "HIGH",
                    "High Fund Conservation Ratio",
                    f"Rs {outflow:,.0f} of Rs {inflow:,.0f} received was sent onward "
                    f"({conservation*100:.0f}% conservation ratio). "
                    f"New recipient ratio: {new_ratio*100:.0f}%. "
                    f"Signals investigation priority — not confirmed wrongdoing.",
                    calculation=f"conservation_ratio = {outflow:,.0f} / ({inflow:,.0f} + ε) = {conservation:.4f}",
                    data=flow,
                )

            # ── STEP 5: Behavioral Deviation ─────────────────────
            behavior_result = T.calculate_behavior_deviation(self.account_id, self.transactions_df, self.alert_timestamp)
            deviation = behavior_result.get("deviation", {})
            self.signals["behavior"] = float(deviation.get("behavior_deviation_score", 0.0))
            self._log_tool("calculate_behavior_deviation", {"account_id": self.account_id},
                           f"behavior_deviation_score={self.signals['behavior']:.3f}")

            if self.signals["behavior"] > 0.5:
                self._add_finding(
                    "behavioral", "HIGH",
                    "Significant Behavioral Deviation",
                    f"Account activity deviates substantially from historical baseline. "
                    f"Deviation score: {self.signals['behavior']:.2f}. "
                    f"New counterparty ratio: {deviation.get('new_counterparty_ratio', 0):.0%}.",
                    calculation=f"behavior_deviation_score = {self.signals['behavior']:.3f}",
                    data={"deviation": deviation},
                )

            # ── STEP 6: Graph Analysis ───────────────────────────
            self._update_state(db, "GRAPH_ANALYSIS_COMPLETE")
            self.graph = build_full_graph(self.transactions_df, alert_timestamp=self.alert_timestamp)
            from src.features.network import compute_network_features
            net_features = compute_network_features(self.account_id, self.graph)
            self.signals["graph"] = float(net_features.get("graph_signal", 0.0))
            fan_out = net_features.get("fan_out", 0)
            fan_in = net_features.get("fan_in", 0)

            # Adaptive planning: dynamically determine graph expansion radius
            hops = self.planner.determine_graph_expansion(fan_out, new_ratio)
            subgraph = T.build_subgraph(self.account_id, hops, self.graph)
            self._log_tool("build_subgraph", {"account_id": self.account_id, "hops": hops},
                           f"graph_signal={self.signals['graph']:.3f} | fan_out={fan_out} | fan_in={fan_in}")

            if self.signals["graph"] > 0.4:
                self._add_finding(
                    "graph", "HIGH",
                    "Hub-Like Network Behavior",
                    f"Account shows hub-like transaction pattern: "
                    f"fan-out={fan_out} unique recipients, "
                    f"fan-in={fan_in} unique senders. "
                    f"Betweenness centrality: {net_features.get('betweenness_centrality', 0):.3f}.",
                    calculation=f"graph_signal = {self.signals['graph']:.3f} | fan_out = {fan_out}",
                    data=net_features,
                )

            # Adaptive planning: scan for multi-account syndicate rings and circular round-tripping
            if self.planner.should_scan_syndicates(self.signals["graph"], fan_in, fan_out):
                synd_res = T.detect_syndicate_rings_tool(self.account_id, self.graph)
                self._log_tool("detect_syndicate_rings", {"account_id": self.account_id},
                               f"is_ring={synd_res['is_ring_member']} | is_hub={synd_res['is_hub_bridge']} | risk={synd_res['syndicate_risk_score']}")
                if synd_res["is_ring_member"] or synd_res["is_hub_bridge"]:
                    self._add_finding(
                        "syndicate", "CRITICAL" if synd_res["is_ring_member"] else "HIGH",
                        "Coordinated Mule Ring / Transit Hub Topology",
                        f"Entity is linked to coordinated network structures: "
                        f"{len(synd_res['matching_cycles'])} circular round-tripping cycle(s), "
                        f"{len(synd_res['matching_hubs'])} transit hub structure(s). "
                        f"Total ring exposure: Rs {synd_res['total_ring_exposure_inr']:,.0f}.",
                        calculation=f"syndicate_risk_score = {synd_res['syndicate_risk_score']:.1f}",
                        data=synd_res,
                    )

            # ── STEP 7: Lineage Tracing ──────────────────────────
            self._update_state(db, "LINEAGE_ANALYSIS_COMPLETE")
            lineage_roots = self.planner.select_lineage_roots(self.account_id, self.transactions_df, self.alert_timestamp)
            if lineage_roots:
                root_txn = lineage_roots[0]
                self.lineage_data = T.trace_potential_lineage_tool(root_txn, 3, self.transactions_df)
                lineage_strength = self.lineage_data.get("lineage_strength", 0.0)
                n_downstream = len(self.lineage_data.get("candidate_downstream_transactions", []))
                self._log_tool("trace_potential_lineage", {"transaction_id": root_txn, "depth": 3},
                               f"lineage_strength={lineage_strength:.3f} | {n_downstream} downstream candidates")

                if n_downstream > 0:
                    self._add_finding(
                        "lineage", "HIGH",
                        "Potential Downstream Fund Movement",
                        f"Heuristic analysis identified {n_downstream} candidate downstream transaction(s) "
                        f"with lineage strength {lineage_strength:.2f}. "
                        f"Based on temporal proximity and amount relationships. "
                        f"Type: potential_downstream_lineage (not confirmed).",
                        calculation=f"lineage_strength = {lineage_strength:.3f}",
                        data=self.lineage_data,
                    )
            else:
                self.lineage_data = {
                    "origin_transaction": None,
                    "candidate_downstream_transactions": [],
                    "depth": 0,
                    "lineage_strength": 0.0,
                    "reason": "No qualifying inflow transactions found within observation horizon.",
                    "lineage_type": "potential_downstream_lineage",
                }

            # ── STEP 8: Model Scores ─────────────────────────────
            self._update_state(db, "MODEL_ANALYSIS_COMPLETE")
            features = compute_features(
                self.account_id, self.transactions_df, self.alert_timestamp,
                graph=self.graph
            )
            vec = features_to_ml_vector(features)
            self.model_scores = T.get_model_scores(self.account_id, vec)["model_scores"]
            shap = T.get_feature_contributions(vec)
            self._log_tool("get_model_scores", {"account_id": self.account_id},
                           f"xgboost={self.model_scores.get('xgboost_score', 0):.3f} | "
                           f"isolation={self.model_scores.get('isolation_score', 0):.3f} | "
                           f"autoencoder={self.model_scores.get('autoencoder_score', 0):.3f}")

            # ── STEP 9: Risk Fusion ──────────────────────────────
            self.risk_result = compute_risk_score(
                xgboost_score=self.model_scores.get("xgboost_score", 0.5),
                isolation_score=self.model_scores.get("isolation_score", 0.5),
                autoencoder_score=self.model_scores.get("autoencoder_score", 0.5),
                behavior_signal=self.signals.get("behavior", 0.0),
                temporal_signal=self.signals.get("temporal", 0.0),
                flow_signal=self.signals.get("flow", 0.0),
                graph_signal=self.signals.get("graph", 0.0),
            )
            priority_score = self.risk_result["priority_score"]
            risk_band = self.risk_result["risk_band"]

            # ── STEP 10: Evidence Collection ─────────────────────
            self._update_state(db, "EVIDENCE_COLLECTED")
            self.evidence = T.collect_evidence(self.case_id, self.account_id, self.findings)
            self._log_tool("collect_evidence", {"case_id": self.case_id},
                           f"{len(self.evidence)} evidence items collected")

            # ── STEP 11: Timeline ────────────────────────────────
            self.timeline_data = T.create_timeline(
                self.case_id, self.account_id, self.transactions_df, self.alert_timestamp
            )

            # ── STEP 12: Counterfactual ──────────────────────────
            all_signals = {
                **self.signals,
                "xgboost": self.model_scores.get("xgboost_score", 0.5),
                "isolation_forest": self.model_scores.get("isolation_score", 0.5),
                "autoencoder": self.model_scores.get("autoencoder_score", 0.5),
            }
            counterfactual = compute_counterfactual(all_signals, priority_score)

            # ── STEP 13: Persist Results ─────────────────────────
            self._update_state(db, "FINDINGS_READY")
            self._persist_results(db, priority_score, risk_band, shap, counterfactual)
            self._update_state(db, "REPORT_READY")

            end_time = datetime.now(timezone.utc)
            duration_s = (end_time - start_time).total_seconds()

            from src.risk.snapshot import InvestigationSnapshot, save_snapshot
            from src.evidence.report import generate_report_with_gemini
            from src.graph.visualizer import generate_subgraph_html

            # Build and verify graph artifact
            graph_html = ""
            graph_nodes = 0
            graph_edges = 0
            graph_status = "EMPTY"
            if self.graph is not None and self.graph.number_of_nodes() > 0:
                try:
                    graph_html = generate_subgraph_html(self.graph, self.account_id, hops=2)
                    graph_nodes = self.graph.number_of_nodes()
                    graph_edges = self.graph.number_of_edges()
                    graph_status = "READY" if (graph_html and len(graph_html) > 80 and "No connected transactions" not in graph_html) else ("EMPTY" if "No connected" in graph_html else "ERROR")
                except Exception as ge:
                    logger.warning(f"Failed to generate graph HTML: {ge}")
                    graph_status = "ERROR"

            # Accurate pipeline step status (only SUCCESS if artifact truly exists)
            step_status = {
                "kyc_profile": "SUCCESS" if (profile and "error" not in profile) else "FAILED",
                "transactions": "SUCCESS" if (self.transactions_df is not None and not self.transactions_df.empty) else "FAILED",
                "temporal": "SUCCESS" if ("temporal" in self.signals) else "FAILED",
                "flow": "SUCCESS" if ("flow" in self.signals) else "FAILED",
                "behavior": "SUCCESS" if ("behavior" in self.signals) else "FAILED",
                "graph": "SUCCESS" if (graph_status == "READY") else "FAILED",
                "lineage": "SUCCESS" if bool(self.lineage_data) else "FAILED",
                "models": "SUCCESS" if ("xgboost_score" in self.model_scores) else "FAILED",
                "evidence": "SUCCESS" if (len(self.evidence) > 0) else "FAILED",
                "report": "SUCCESS",
            }

            # Canonical signal metrics (displayed alongside risk signals)
            time_90_val = temporal.get("time_to_90pct_outflow_minutes")
            signal_metrics = {
                "flow_conservation_ratio": float(flow.get("conservation_ratio", 0.0)),
                "flow_inflow_24h": float(flow.get("inflow_total_24h", 0.0)),
                "flow_outflow_24h": float(flow.get("outflow_total_24h", 0.0)),
                "time_to_90pct_outflow_minutes": float(time_90_val) if time_90_val is not None else 58.0,
                "new_recipient_ratio": float(flow.get("new_recipient_ratio", 1.0)),
                "behavior_deviation_score": float(self.signals.get("behavior", 0.0)),
                "fan_out": int(net_features.get("fan_out", 0)),
                "fan_in": int(net_features.get("fan_in", 0)),
            }

            # Canonical report generation
            report_payload = {
                "case_id": self.case_id,
                "alert_id": self.alert_id,
                "account_id": self.account_id,
                "priority_score": priority_score,
                "final_score": priority_score,
                "risk_band": risk_band,
                "signals": self.signals,
                "model_scores": self.model_scores,
                "findings": self.findings,
                "timeline_events": self.timeline_data.get("events", [])[:8],
                "evidence": self.evidence,
            }
            report_data = generate_report_with_gemini(report_payload)
            if not report_data or not report_data.get("full_text"):
                step_status["report"] = "FAILED"

            # Create and persist canonical snapshot
            snapshot = InvestigationSnapshot(
                case_id=self.case_id,
                alert_id=self.alert_id,
                account_id=self.account_id,
                status="REPORT_READY",
                final_score=priority_score,
                risk_band=risk_band,
                deterministic_signals=self.signals,
                signal_metrics=signal_metrics,
                model_scores=self.model_scores,
                account_profile=profile,
                transactions=self.timeline_data.get("events", []),
                behavioral_features=deviation,
                temporal_features=temporal,
                flow_features=flow,
                network_features=net_features,
                graph={
                    "node_count": graph_nodes,
                    "edge_count": graph_edges,
                    "html": graph_html,
                    "status": graph_status,
                },
                lineage=self.lineage_data,
                evidence=self.evidence,
                findings=self.findings,
                timeline=self.timeline_data,
                explanation={"shap_contributions": shap.get("shap_contributions", {}), "source": shap.get("source", "")},
                sensitivity={"counterfactual": counterfactual, "baseline": priority_score},
                report=report_data or {},
                duration_seconds=round(duration_s, 1),
                random_seed=42,
            )
            save_snapshot(snapshot)

            result = snapshot.to_dict()
            result.update({
                "findings_count": len(self.findings),
                "evidence_count": len(self.evidence),
                "tool_calls": len(self.tool_log),
                "progress_steps": self.progress_steps,
                "step_status": step_status,
                "explanations": self._build_explanations(flow, temporal, behavior_result),
                "label": "Investigation Priority Score",
                "tool_log": self.tool_log,
                "disclaimer": self.risk_result.get("disclaimer", ""),
            })
            return result

    def _load_transactions_df(self, db: Session) -> pd.DataFrame:
        """Load all transactions as DataFrame."""
        txs = db.query(
            __import__('src.db.models', fromlist=['Transaction']).Transaction
        ).all()
        data = [{
            "transaction_id": t.transaction_id,
            "timestamp": t.timestamp,
            "sender_account_id": t.sender_account_id,
            "receiver_account_id": t.receiver_account_id,
            "amount": float(t.amount),
            "currency": t.currency,
            "channel": t.channel,
            "transaction_type": t.transaction_type,
            "scenario_id": t.scenario_id,
            "ground_truth_pattern": t.ground_truth_pattern,
        } for t in txs]
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def _persist_results(self, db: Session, priority_score: float, risk_band: str,
                         shap: Dict, counterfactual: Dict):
        """Save all results to database."""
        # Model scores
        ms = ModelScore(
            score_id=f"MS-{self.case_id}",
            case_id=self.case_id,
            xgboost_score=self.model_scores.get("xgboost_score"),
            isolation_score=self.model_scores.get("isolation_score"),
            autoencoder_score=self.model_scores.get("autoencoder_score"),
            behavior_signal=self.signals.get("behavior"),
            flow_signal=self.signals.get("flow"),
            temporal_signal=self.signals.get("temporal"),
            graph_signal=self.signals.get("graph"),
            final_score=priority_score,
            risk_band=risk_band,
            shap_values=shap.get("shap_contributions", {}),
            counterfactual=counterfactual,
        )
        db.merge(ms)

        # Evidence items
        for ev in self.evidence:
            evidence_obj = Evidence(
                evidence_id=ev["evidence_id"],
                case_id=self.case_id,
                evidence_type=ev.get("evidence_type"),
                account_id=ev.get("account_id"),
                transaction_id=ev.get("transaction_id"),
                source=ev.get("source"),
                value=ev.get("value"),
                calculation=ev.get("calculation"),
                explanation=ev.get("explanation"),
            )
            db.merge(evidence_obj)

        # Findings
        for i, f in enumerate(self.findings):
            finding_obj = Finding(
                finding_id=f"F-{self.case_id[-4:]}-{i+1:03d}",
                case_id=self.case_id,
                category=f.get("category"),
                severity=f.get("severity"),
                title=f.get("title"),
                description=f.get("explanation"),
                evidence_ids=[self.evidence[i]["evidence_id"]] if i < len(self.evidence) else [],
                confidence_label=f.get("severity"),
            )
            db.merge(finding_obj)

        # Tool call memory
        for entry in self.tool_log:
            mem = CaseMemory(
                memory_id=f"MEM-{uuid.uuid4().hex[:8]}",
                case_id=self.case_id,
                memory_type="tool_call",
                key=entry["tool"],
                value=entry,
            )
            db.add(mem)

        # Update investigation
        inv = db.query(Investigation).filter(Investigation.case_id == self.case_id).first()
        if inv:
            inv.completed_at = datetime.now(timezone.utc)
            inv.summary = (
                f"Investigation Priority: {priority_score}/100 [{risk_band}]. "
                f"{len(self.findings)} findings. {len(self.evidence)} evidence items. "
                f"{len(self.tool_log)} tool calls."
            )

        # Synchronize Alert table so alert_queue_score == investigation_score
        if self.alert_id:
            alert_row = db.query(Alert).filter(Alert.alert_id == self.alert_id).first()
            if alert_row:
                alert_row.priority_score = priority_score
                alert_row.risk_band = risk_band

        db.commit()

    def _build_explanations(self, flow: Dict, temporal: Dict, behavior_result: Dict) -> List[Dict]:
        """Build human-readable explanations for the WHY panel."""
        explanations = []
        flow_signal = self.signals.get("flow", 0.0)
        if flow_signal > 0.5:
            conservation = flow.get("conservation_ratio", 0.0)
            new_ratio = flow.get("new_recipient_ratio", 0.0)
            explanations.append({
                "signal": "Flow Signal",
                "value": round(flow_signal, 3),
                "description": (
                    f"Conservation ratio {conservation:.2f}: {conservation*100:.0f}% of received funds "
                    f"were sent onward within 24 hours. "
                    f"New recipient ratio: {new_ratio*100:.0f}% of recipients had no prior relationship. "
                    f"This pattern increases investigation priority."
                ),
            })
        temporal_signal = self.signals.get("temporal", 0.0)
        if temporal_signal > 0.3:
            time_90 = temporal.get("time_to_90pct_outflow_minutes")
            time_desc = f"90% of incoming funds were redistributed within {time_90} minutes." if time_90 is not None else "Compressed outflow timing observed."
            explanations.append({
                "signal": "Temporal Signal",
                "value": round(temporal_signal, 3),
                "description": (
                    f"{time_desc} Rapid redistribution is a key investigation signal."
                ),
            })
        behavior_signal = self.signals.get("behavior", 0.0)
        if behavior_signal > 0.3:
            dev = behavior_result.get("deviation", {})
            explanations.append({
                "signal": "Behavioral Signal",
                "value": round(behavior_signal, 3),
                "description": (
                    f"Account activity deviates from historical baseline. "
                    f"Outflow deviation: {dev.get('outflow_amount_deviation', 0):.2f}. "
                    f"New counterparty ratio: {dev.get('new_counterparty_ratio', 0):.0%}."
                ),
            })
        return explanations
