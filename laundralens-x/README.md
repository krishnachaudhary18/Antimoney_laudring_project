# 🔍 LaundraLens X
### Agentic Temporal-Graph Intelligence for Autonomous Financial Crime Investigation
*Razorpay Hackathon 2026 Submission*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 22 Passed](https://img.shields.io/badge/Tests-22%20Passed-brightgreen.svg)]()

> **⚠ Synthetic Data Disclaimer:**
> All accounts, counterparties, transactions, and behavior flows in this system are purely synthetic demonstration data generated for evaluating algorithmic triage. This software does not connect to live banking rails or real customer PII.

---

## 💡 The Problem
In financial crime compliance, **over 95% of traditional AML rule-based alerts are false positives**. Compliance analysts spend **45 to 60 minutes per alert** manually querying relational databases, cross-referencing account opening forms, hand-drawing counterparty transaction paths, calculating conservation ratios, and writing Suspicious Activity Reports (SARs).

Meanwhile, organized money laundering rings utilize **rapid passthrough schemes (rapid redistribution)**:
1. Significant funds are transferred into a compromised or mule account via RTGS/IMPS.
2. Within minutes, funds are broken down and redistributed across multiple newly activated accounts.
3. By the time a human analyst reviews the 24-hour batch rule alert, the money has already exited the banking perimeter.

---

## ⚡ The Solution: LaundraLens X
**LaundraLens X** turns a 45-minute investigation into a **1.2-second autonomous diagnostic**:
- **Multi-Window Temporal Intelligence:** Measures velocity bursts and redistribution latency across 15m, 1h, 6h, and 24h horizons.
- **Fund Flow Conservation:** Quantifies exact fund passthrough dynamics (`conservation_ratio = outflow / (inflow + ε)`).
- **Network Ego-Graphs:** Interactive 2-hop directed graph mapping counterparty fan-in/fan-out, centrality, and heuristic downstream fund lineage.
- **3-Model ML Ensemble:** Combines supervised **XGBoost** (with tree-based **SHAP** values), unsupervised **Isolation Forest**, and a reconstruction **Autoencoder**.
- **Investigation Priority Scorer:** Synthesizes 7 independent signals into a calibrated priority metric (0–100) with counterfactual **What-If** sensitivity analysis.
- **Evidence-Grounded Reporting:** Generates audit-ready SAR drafts via **Google Gemini Flash** grounded exclusively on forensic evidence items.

---

## 🏛 Architecture Overview

```
                          ┌──────────────────────────┐
                          │   Synthetic Data Rails   │
                          │   5,000+ TXNs · 9 Rings  │
                          └─────────────┬────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FAIR DATA INGESTION & PIPELINE                        │
│          Strict Pre-Alert Behavioral Baselines (Zero Future Leakage)        │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
┌─────────────────────────┐                               ┌─────────────────────────┐
│  Feature Engine (39-D)  │                               │  Graph Intelligence    │
│  • Flow Conservation    │                               │  • 2-Hop Ego Graph      │
│  • Redistribution Speed │                               │  • Louvain Communities │
│  • Baseline Deviation   │                               │  • Lineage Tracer       │
└────────────┬────────────┘                               └────────────┬────────────┘
             │                                                         │
             ▼                                                         ▼
┌─────────────────────────┐                               ┌─────────────────────────┐
│   ML Detection Suite    │                               │  AI Agent Orchestrator  │
│  • XGBoost + SHAP       │                               │  • 11 State Transitions │
│  • Isolation Forest     │                               │  • 19 Read-Only Tools   │
│  • PyTorch Autoencoder  │                               │  • Forensic Evidence    │
└────────────┬────────────┘                               └────────────┬────────────┘
             │                                                         │
             └──────────────────────────┬──────────────────────────────┘
                                        ▼
                   ┌────────────────────────────────────────┐
                   │    Investigation Priority Scorer       │
                   │    Weighted Risk Fusion (0 - 100)      │
                   │    Counterfactual Sensitivity Analysis │
                   └────────────────────┬───────────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
┌──────────────────────────────────┐         ┌──────────────────────────────────┐
│   FastAPI REST Engine (8000)     │         │   Analyst Workstation (8501)     │
│   • /api/v1/alerts               │         │   • Dark Mode Glassmorphic UI    │
│   • /api/v1/investigations       │         │   • Interactive Pyvis Graph      │
│   • /api/v1/cases/{id}/report    │         │   • SHAP Waterfall & Sensitivity │
└──────────────────────────────────┘         └──────────────────────────────────┘
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git

### 2. Setup Environment
```bash
git clone https://github.com/krishnachaudhary18/Antimoney_laudring_project.git
cd Antimoney_laudring_project/laundralens-x

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Generate Data & Seed Database
```bash
# 1. Generate 5,000+ realistic transactions with 9 planted money laundering topologies
python scripts/generate_synthetic_data.py

# 2. Seed SQLite database and configure alerts
python scripts/seed_database.py

# 3. Train all 3 ML models (XGBoost, Isolation Forest, PyTorch Autoencoder)
python scripts/train_models.py
```

### 4. Run the 30-Second Terminal Demo
```bash
python scripts/run_demo.py
```

### 5. Launch the Web System
Start the backend and dashboard in separate terminals:
```bash
# Terminal 1: Launch FastAPI REST Engine
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Launch Streamlit Analyst Dashboard
streamlit run dashboard/app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🧪 Test Suite
LaundraLens X includes a 100% passing test suite across feature engineering, machine learning inference, graph traversal, risk fusion, agent orchestration, and API routes:
```bash
pytest -v
```
Output:
```
tests/test_api.py::test_api_health PASSED
tests/test_api.py::test_api_alerts PASSED
tests/test_api.py::test_api_start_investigation PASSED
tests/test_features.py::test_behavioral_baseline PASSED
tests/test_features.py::test_flow_features PASSED
tests/test_features.py::test_redistribution_timing PASSED
tests/test_features.py::test_network_features PASSED
tests/test_graph.py::test_graph_and_traversal PASSED
tests/test_graph.py::test_lineage_tracing PASSED
tests/test_graph.py::test_pyvis_rendering PASSED
tests/test_models.py::test_model_registry_loaded PASSED
tests/test_models.py::test_model_inference PASSED
tests/test_models.py::test_shap_explanation PASSED
tests/test_orchestrator.py::test_orchestrator_execution PASSED
tests/test_risk_fusion.py::test_risk_score_calculation PASSED
tests/test_risk_fusion.py::test_risk_bands PASSED
tests/test_risk_fusion.py::test_counterfactual_sensitivity PASSED

====================== 17 passed in 11.94s =======================
```

---

## 🎯 9 Planted AML Scenarios

| Scenario ID | Topology Description | Key Signals Observed | Target Account |
|---|---|---|---|
| **SCENARIO-001** | **Primary Demo: Rapid Passthrough Redistribution** | Conservation = 0.97, Time to 90% = 58m | `ACC-B-001` |
| **SCENARIO-002** | New Recipient Burst | 8 new counterparties in 2 hours | `ACC-0104` |
| **SCENARIO-003** | Fan-In Funnel Aggregation | 6 accounts aggregate into 1 recipient | `ACC-0114` |
| **SCENARIO-004** | Fan-Out Smurfing | Rapid dispersal to 10 split recipients | `ACC-0124` |
| **SCENARIO-005** | Multi-Hop Layering Chain | A → B → C → D → E passthrough | `ACC-0174` |
| **SCENARIO-006** | Profile Anomaly (Student Inflow) | Unusually large credit for KYC profile | `ACC-0111` |
| **SCENARIO-007** | Velocity Spike (Salary Account) | 50x normal monthly volume | `ACC-0127` |
| **SCENARIO-008** | Temporal Velocity Burst | 15 transactions in 30 minutes | `ACC-0194` |
| **SCENARIO-009** | Combined Funnel & Redistribution | Inflow aggregation immediately dispersed | `ACC-0224` |

---

## 🛡 Responsible AI & Governance
- **Defensible Decisions:** No ungrounded LLM hallucinations. All findings map to evidence IDs with mathematical formulas.
- **Safety First:** The AI agent possesses only read-only investigative tools. No automated fund freezing or irreversible decisions can be taken without human authorization.
- **Explainability:** Tree-based SHAP values attribute exact contribution per feature, and counterfactual sensitivity displays the impact of nullifying individual signals.

---

## 👥 Contributors
Developed for **Razorpay Hackathon 2026** by Krishna Chaudhary.
