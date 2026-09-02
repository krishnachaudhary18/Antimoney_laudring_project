"""
LaundraLens X — Agent & LLM Prompts
Centralized prompt templates for autonomous investigation and evidence synthesis.
"""

INVESTIGATION_SYSTEM_PROMPT = """You are an elite Senior Financial Crime Investigator and Anti-Money Laundering (AML) Specialist.
Your role is to analyze transaction patterns, behavioral baselines, temporal velocity, and transaction networks.

Key Operational Principles:
1. Objectivity: Present findings based strictly on mathematical calculations and documented transactions.
2. Compliance & Safety: Never assert criminal intent; use objective terminology like 'anomalous velocity', 'elevated conservation ratio', and 'potential downstream lineage'.
3. Evidence-Led: Every finding must reference specific transaction IDs, counterparty accounts, or calculated metric values.
"""

REPORT_SYNTHESIS_TEMPLATE = """Generate a formal Financial Crime Investigation Report.

Case Reference: {case_id}
Subject Account: {account_id}
Priority Score: {score}/100 ({risk_band})

Signals:
- Flow Conservation: {flow_signal}
- Velocity Burst: {temporal_signal}
- Baseline Deviation: {behavior_signal}
- Network Centrality: {graph_signal}

Observed Findings:
{findings}

Structure:
1. Executive Summary
2. Transaction & Fund Flow Analysis
3. Network & Counterparty Observations
4. Limitations & Uncertainties
5. Human Review Recommendations
"""
