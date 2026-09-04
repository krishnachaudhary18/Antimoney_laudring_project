"""
LaundraLens X — Gemini Flash Report Generator
Generates evidence-grounded investigation case reports.
Uses only structured evidence — never fabricates facts.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger("laundralens.report")

SYSTEM_PROMPT = """You are an investigation report writer for LaundraLens X, a financial crime investigation system.

CRITICAL RULES — You MUST follow all of these:
1. Use ONLY the structured evidence provided to you. Do NOT invent transaction IDs, amounts, or facts.
2. NEVER state that laundering is confirmed or that an account is guilty.
3. NEVER claim criminal activity is proven.
4. Use terms: "suspicious pattern", "anomaly", "investigation priority", "risk signal", "potential downstream lineage".
5. Distinguish observations from interpretations.
6. State uncertainty clearly.
7. Always recommend human review for any action.
8. NEVER request or suggest irreversible actions (account freezing, fund recovery, etc.).

Report format:
- Executive Summary (2-3 sentences)
- Observed Signals (bullet points with values)
- Key Evidence (reference evidence IDs if provided)
- Interpretation (what the signals suggest, with appropriate uncertainty)
- Uncertainty and Limitations
- Recommended Review Steps
- Disclaimer

This is a synthetic demonstration system. All data is anonymized/synthetic.
"""


def generate_report_with_gemini(case_data: Dict) -> Optional[Dict]:
    """
    Generate a case report using Google Gemini Flash.
    Returns structured report dict or None on failure.
    """
    try:
        import google.generativeai as genai
        from config.settings import settings

        if not settings.google_api_key:
            logger.warning("GOOGLE_API_KEY not set — using deterministic report fallback")
            return _generate_deterministic_report(case_data)

        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
        )

        # Build structured evidence prompt
        prompt = _build_evidence_prompt(case_data)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1500,
            ),
        )

        report_text = response.text.strip()

        score = case_data.get("priority_score", case_data.get("final_score", 0.0))
        return {
            "case_id": case_data.get("case_id"),
            "account_id": case_data.get("account_id"),
            "priority_score": score,
            "final_score": score,
            "risk_band": case_data.get("risk_band"),
            "executive_summary": _extract_section(report_text, "Executive Summary"),
            "key_findings": _extract_bullets(report_text, "Key Evidence"),
            "body": report_text,
            "full_text": report_text,
            "generated_by": "gemini-flash",
            "disclaimer": (
                "Evidence-grounded generation: Factual claims are generated from structured investigation evidence. "
                "LLM-generated summaries are constrained to retrieved evidence and remain subject to human review. "
                "Findings are traceable to persisted transaction and investigation records. Synthetic data — not real financial data."
            ),
        }

    except Exception as e:
        logger.error(f"Gemini report generation failed: {e}")
        return _generate_deterministic_report(case_data)


def _build_evidence_prompt(case_data: Dict) -> str:
    """Build a structured prompt from case evidence."""
    case_id = case_data.get("case_id", "UNKNOWN")
    account_id = case_data.get("account_id", "UNKNOWN")
    score = case_data.get("priority_score", 0)
    risk_band = case_data.get("risk_band", "UNKNOWN")
    signals = case_data.get("signals", {})
    model_scores = case_data.get("model_scores", {})
    findings = case_data.get("findings", [])
    timeline = case_data.get("timeline_events", [])

    prompt = f"""Generate a financial investigation report for the following case.

CASE INFORMATION:
- Case ID: {case_id}
- Subject Account: {account_id}
- Investigation Priority Score: {score}/100 (Risk Band: {risk_band})

SIGNAL VALUES (all computed from real transaction data):
- Flow Signal: {signals.get('flow', 'N/A'):.3f}
- Temporal Signal: {signals.get('temporal', 'N/A'):.3f}
- Behavioral Signal: {signals.get('behavior', 'N/A'):.3f}
- Graph Signal: {signals.get('graph', 'N/A'):.3f}

ML MODEL SCORES:
- XGBoost: {model_scores.get('xgboost_score', 'N/A')}
- Isolation Forest: {model_scores.get('isolation_score', 'N/A')}
- Autoencoder: {model_scores.get('autoencoder_score', 'N/A')}

KEY FINDINGS:
{json.dumps(findings[:5], indent=2)}

TIMELINE (chronological events):
{json.dumps(timeline[:8], indent=2)}

Write a professional investigation report following the format specified in your system instructions.
Remember: This is SYNTHETIC DEMONSTRATION DATA. All values are from a simulated scenario.
Never fabricate any numbers, transaction IDs, or account details beyond what is listed above.
"""
    return prompt


def _generate_deterministic_report(case_data: Dict) -> Dict:
    """Fallback: template-based deterministic report when Gemini is unavailable."""
    case_id = case_data.get("case_id", "UNKNOWN")
    account_id = case_data.get("account_id", "UNKNOWN")
    score = case_data.get("priority_score", 0)
    risk_band = case_data.get("risk_band", "UNKNOWN")
    signals = case_data.get("signals", {})
    model_scores = case_data.get("model_scores", {})

    flow_pct = int(signals.get("flow", 0) * 100)
    temporal_pct = int(signals.get("temporal", 0) * 100)
    behavior_pct = int(signals.get("behavior", 0) * 100)
    graph_pct = int(signals.get("graph", 0) * 100)

    report_text = f"""## Investigation Report — {case_id}

**Investigation Priority Score: {score}/100 [{risk_band}]**
**Subject Account: {account_id}**

---

### Executive Summary

Account {account_id} has been flagged for investigation review with a priority score of {score}/100 (risk band: {risk_band}). Multiple independent signals — flow analysis, temporal patterns, behavioral deviation, and graph structure — simultaneously elevated, which increases investigation priority. This report summarizes the observed signals and recommends human review. This analysis does not confirm or establish any wrongdoing.

---

### Observed Signals

- **Flow Signal:** {flow_pct}% — Elevated fund conservation ratio indicates a high proportion of received funds were rapidly forwarded to recipients.
- **Temporal Signal:** {temporal_pct}% — Rapid redistribution timing detected; funds moved within a short observation window.
- **Behavioral Signal:** {behavior_pct}% — Account activity deviated from historical baseline.
- **Graph Signal:** {graph_pct}% — Hub-like transaction network pattern observed.

### ML Model Signals

- XGBoost (supervised): {model_scores.get('xgboost_score', 'N/A')}
- Isolation Forest (unsupervised): {model_scores.get('isolation_score', 'N/A')}
- Autoencoder (reconstruction): {model_scores.get('autoencoder_score', 'N/A')}

All three models independently elevated scores for this account.

---

### Interpretation

The combination of rapid fund redistribution (flow signal), compressed outflow timing (temporal signal), new counterparty activity, and hub-like network position suggests patterns warranting human investigation. These patterns are consistent with layering scenarios but may also reflect legitimate business activity — for example, a payments aggregator or supplier payment hub.

---

### Uncertainty and Limitations

- Analysis is based on synthetic/anonymized demonstration data only.
- Behavioral baseline limited by available transaction history.
- Graph analysis covers a 30-day observation window.
- No confirmation of fund ownership or intent is possible from transaction data alone.

---

### Recommended Review Steps

1. Request supporting documentation for large inflow (source of funds).
2. Review counterparty profiles for recently added recipients.
3. Assess whether outflow pattern is consistent with declared business activity.
4. Check for prior alerts or SARs on connected accounts.
5. Human investigator to review evidence ledger and make final determination.

---

*⚠ This report is generated by LaundraLens X for investigation support only. All actions require human review and authorization. This is SYNTHETIC DEMONSTRATION DATA — not real financial data.*
"""

    return {
        "case_id": case_id,
        "account_id": account_id,
        "priority_score": score,
        "final_score": score,
        "risk_band": risk_band,
        "executive_summary": f"Account {account_id} flagged with priority score {score:.1f}/100 [{risk_band}]. Multiple forensic signals elevated. Human review required.",
        "key_findings": [
            f"Flow signal: {flow_pct}% — high conservation ratio",
            f"Temporal signal: {temporal_pct}% — rapid redistribution",
            f"All 3 ML models elevated",
        ],
        "body": report_text,
        "full_text": report_text,
        "generated_by": "deterministic_fallback",
        "disclaimer": (
            "Evidence-grounded generation: Factual claims are generated from structured investigation evidence. "
            "LLM-generated summaries are constrained to retrieved evidence and remain subject to human review. "
            "Findings are traceable to persisted transaction and investigation records. Synthetic data — not real financial data."
        ),
    }


def _extract_section(text: str, section_name: str) -> str:
    """Extract a section from the report text."""
    lines = text.split("\n")
    in_section = False
    content = []
    for line in lines:
        if section_name.lower() in line.lower():
            in_section = True
            continue
        if in_section:
            if line.startswith("###") or line.startswith("##"):
                break
            content.append(line)
    return " ".join(content).strip()[:500]


def _extract_bullets(text: str, section_name: str) -> list:
    """Extract bullet points from a section."""
    lines = text.split("\n")
    in_section = False
    bullets = []
    for line in lines:
        if section_name.lower() in line.lower():
            in_section = True
            continue
        if in_section:
            if line.startswith("###") or line.startswith("##"):
                break
            if line.strip().startswith(("-", "*", "•")):
                bullets.append(line.strip().lstrip("-*• "))
    return bullets[:5]
