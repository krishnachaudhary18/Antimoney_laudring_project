# 5-Minute Judge Demonstration Script — LaundraLens X

## Overview for Evaluators
**LaundraLens X** is an Agentic Temporal-Graph Intelligence platform for autonomous financial crime investigation. It is designed to cut triage time from **45 minutes to under 2 seconds** while guaranteeing explainability, full evidence provenance, and defensible auditability.

---

## 5-Minute Demo Flow

### Minute 0:00 – 1:00: The Problem & The Solution
1. **The Problem:**
   - AML rule systems generate **95%+ false positives**.
   - Investigators spend 45–60 minutes manually pulling statements, drawing counterparty diagrams, and writing Suspicious Activity Reports (SARs).
   - Rapid layering schemes (e.g. money mule rings, rapid passthrough) drain accounts before analysts even open the alert.
2. **The LaundraLens X Solution:**
   - An autonomous agent that ingests alerts, reconstructs pre-alert baselines, measures fund conservation and redistribution velocity, graphs the 2-hop transaction network, runs an ML ensemble (XGBoost + Isolation Forest + Autoencoder), and generates an evidence-grounded report in **<2 seconds**.

---

### Minute 1:00 – 2:00: Live Alert Triage & Launching the Investigation
1. **Open the Dashboard:**
   - Point to `http://localhost:8501` (or show terminal `python scripts/run_demo.py`).
   - Highlight the **Case Queue** on the left: 9 prioritized cases sorted by **Investigation Priority Score**.
2. **Select the Primary Demo Scenario (`ALERT-SCENARIO-001`):**
   - Subject: `ACC-B-001` (Merchant current account).
   - Click **▶ RUN** or inspect the alert details.
   - Show the **AI Investigator Stepper**: watch all 11 state transitions execute in real time.

---

### Minute 2:00 – 3:00: The 4 Core Intelligence Signals
Walk through the 3 main panels:
1. **⚡ Investigation Priority Score (63.2/100 – HIGH / CRITICAL):**
   - Explain the 4 signals:
     - **Flow Conservation (0.815):** ₹9.7L out of ₹10L received was sent onward within 58 minutes (**97% conservation ratio**).
     - **Temporal Velocity (0.587):** Time to 90% outflow was **58 minutes** across 4 rapid transfers.
     - **Behavioral Deviation:** 100% new counterparties compared to historical pre-alert baseline.
     - **Graph Signal:** Hub fan-out pattern to newly introduced accounts.
2. **🕸 Interactive Pyvis Transaction Graph:**
   - Show the purple center node (`ACC-B-001`).
   - Trace the green inflow edge from `ACC-A-001` (₹10,00,000 via RTGS).
   - Trace the 4 red outflow edges to `ACC-C-001`, `ACC-D-001`, `ACC-E-001`, `ACC-F-001`.
   - Hover over nodes to see balance, total volume, and community clusters.

---

### Minute 3:00 – 4:00: Explainability & What-If Counterfactuals
Click through the bottom forensic tabs:
1. **📎 Evidence Ledger:**
   - Show exact mathematical formulas for each evidence item (`conservation_ratio = 970,000 / (1,000,000 + ε) = 0.97`).
   - Every fact is grounded — zero hallucinations.
2. **❓ WHY? Panel (SHAP Waterfall):**
   - Point to the horizontal bar chart showing tree-based feature contributions:
     - `weighted_in_degree`, `behavior_deviation_score`, and `weighted_out_degree` drive the score upward.
3. **📊 Score Sensitivity ("What-If"):**
   - Answer the judge's question: *"How do we know the ML isn't a black box?"*
   - Show that if we nullify the **Flow Conservation** signal, the priority score drops from **63.2 to 51.0**. If we remove XGBoost, it drops to **43.2**.

---

### Minute 4:00 – 5:00: Gemini Case Report & Human-in-the-Loop Governance
1. **📄 Case Report Tab:**
   - Click **Generate Case Report (Gemini)**.
   - Show the generated investigation report:
     - Executive Summary
     - Observed Signals
     - Limitations and Uncertainty
     - Recommended Next Actions
   - Click **⬇ Download Report** (`.md`).
2. **Closing Punchline:**
   - *"LaundraLens X does not replace compliance analysts; it turns an exhausting 45-minute forensic investigation into an instant, explainable, evidence-backed decision in 1.2 seconds."*
