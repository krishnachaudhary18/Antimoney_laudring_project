# LaundraLens X — Antigravity Master Implementation Specification

**Project:** LaundraLens X  
**Full name:** Agentic Temporal-Graph Intelligence for Financial Crime Investigation  
**Target:** Razorpay Hackathon  
**Objective:** Build a technically advanced, visually polished, end-to-end financial-risk investigation prototype optimized for a 5-minute demo.

---

## 1. PRODUCT VISION

LaundraLens X is an agentic financial-risk investigation platform.

Core pipeline:

`Detect → Connect → Trace → Understand → Investigate → Explain → Case`

Traditional workflow:

`Transaction → Alert → Manual investigation → Evidence collection → Case`

LaundraLens X:

`Alert → Automated investigation → Temporal + Flow + Graph + Behavior analysis → Evidence → Explanation → Counterfactual → Case → Human review`

The system combines:

- behavioral baselines
- multi-scale temporal analysis
- transaction-flow analysis
- graph analytics
- anomaly detection
- supervised ML
- autoencoder anomaly scoring
- temporal graph learning
- investigation orchestration
- evidence provenance
- explainability
- counterfactual sensitivity
- investigator-facing case generation

The project should feel like an early-stage fintech risk product, not an LLM wrapper.

---

## 2. SAFETY AND PRODUCT BOUNDARIES

This is an investigation-support system.

It MUST NOT:

- claim a person or account is guilty
- state that laundering is confirmed
- automatically freeze accounts
- automatically move/recover money
- modify/delete financial records
- make irreversible customer decisions
- fabricate transactions, evidence, attributes, or model outputs
- present a risk score as probability of criminal activity

Use terms such as:

- investigation priority
- suspicious pattern
- anomaly
- risk signal
- potential downstream lineage
- evidence
- model contribution

All final actions remain human-in-the-loop.

Use synthetic/anonymized data only.

---

# 3. PRIMARY DEMO SCENARIO

Generate realistic normal activity plus planted suspicious-pattern scenarios.

Main scenario:

```text
Account A
   ↓ large inflow
Account B
   ↓ rapid redistribution
 ┌─┼────────┐
 ↓ ↓        ↓
C D         E
            ↓
            F
```

Example demonstration values:

- B receives approximately ₹10,00,000
- B sends approximately ₹9,70,000 onward
- movement occurs rapidly
- several recipients are new
- downstream movement exists
- activity differs materially from historical behavior

These are engineered synthetic patterns for demonstration.

UI disclaimer:

> Synthetic demonstration scenario. Signals indicate investigation priority and do not establish wrongdoing.

---

# 4. HIGH-LEVEL ARCHITECTURE

```text
                         DATA SOURCES
                   Synthetic / CSV / DB
                           │
                           ▼
                    INGESTION + QUALITY
                           │
                           ▼
                 FEATURE INTELLIGENCE ENGINE
          ┌────────────┬────┼────┬─────────────┐
          ▼            ▼         ▼             ▼
      Behavioral    Temporal    Flow         Network
          └────────────┬────────┴──────────────┘
                       ▼
                  MODEL LAYER
          ┌────────────┼───────────────┐
          ▼            ▼               ▼
       XGBoost    Isolation Forest  Autoencoder
          └────────────┼───────────────┘
                       ▼
                 TEMPORAL GRAPH
                 NetworkX + PyG
                       │
                       ▼
                  TEMPORAL GAT
                       │
                       ▼
                 RISK FUSION ENGINE
                       │
                       ▼
              INVESTIGATION ORCHESTRATOR
                       │
             ┌─────────┼──────────┐
             ▼         ▼          ▼
          Data       Graph       ML
          Tools      Tools      Tools
             └─────────┼──────────┘
                       ▼
                  EVIDENCE LEDGER
                       │
             ┌─────────┼──────────┐
             ▼         ▼          ▼
          Timeline   Explain   Sensitivity
             └─────────┼──────────┘
                       ▼
                INVESTIGATOR UI
                       │
                       ▼
                 HUMAN REVIEW
```

---

# 5. KEY ARCHITECTURAL PRINCIPLES

## Detection != Investigation

ML models detect suspicious entities.

The agent investigates and assembles evidence.

## Database is source of truth

LLM never invents factual data.

## Tools calculate facts

Do not ask an LLM to calculate ratios, totals, graph paths, time differences, or anomaly scores.

## LLM interprets structured evidence

The LLM can summarize, explain structured signals, rank findings, and write the report.

## No destructive tools

The agent must be read-only.

Never implement or expose:

```text
freeze_account()
transfer_money()
delete_transaction()
modify_customer()
modify_account()
close_account()
```

---

# 6. TECH STACK

Backend:

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Pandas
- NumPy

ML:

- scikit-learn
- XGBoost
- PyTorch
- PyTorch Geometric

Graph:

- NetworkX
- PyTorch Geometric

Explainability:

- SHAP for XGBoost
- deterministic contribution/sensitivity analysis for other models

UI:

- Streamlit
- Plotly
- optional PyDeck/Plotly graph visualization

Utilities:

- PyYAML
- python-dotenv
- pytest
- Uvicorn

Optional LLM:

- OpenAI-compatible client
- provider/model configurable via environment variables

---

# 7. REPOSITORY STRUCTURE

```text
laundralens-x/
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
│
├── config/
│   ├── model_config.yaml
│   ├── feature_config.yaml
│   ├── risk_config.yaml
│   └── demo_config.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── synthetic/
│   └── metadata/
│
├── scripts/
│   ├── generate_synthetic_data.py
│   ├── prepare_data.py
│   ├── train_models.py
│   ├── build_graph.py
│   ├── run_demo.py
│   └── reset_demo.py
│
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── ingestion/
│   │   ├── loader.py
│   │   ├── validator.py
│   │   └── normalizer.py
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── seed.py
│   ├── features/
│   │   ├── behavioral.py
│   │   ├── temporal.py
│   │   ├── flow.py
│   │   ├── network.py
│   │   ├── entity.py
│   │   └── pipeline.py
│   ├── graph/
│   │   ├── builder.py
│   │   ├── traversal.py
│   │   ├── lineage.py
│   │   └── graph_features.py
│   ├── models/
│   │   ├── xgboost_model.py
│   │   ├── isolation_forest.py
│   │   ├── autoencoder.py
│   │   ├── temporal_gat.py
│   │   ├── ensemble.py
│   │   └── model_registry.py
│   ├── risk/
│   │   ├── scorer.py
│   │   ├── normalization.py
│   │   ├── explanation.py
│   │   └── counterfactual.py
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   ├── tools.py
│   │   ├── memory.py
│   │   └── prompts.py
│   ├── evidence/
│   │   ├── ledger.py
│   │   ├── timeline.py
│   │   ├── findings.py
│   │   └── report.py
│   └── api/
│       ├── main.py
│       ├── dependencies.py
│       ├── schemas.py
│       └── routes/
│           ├── alerts.py
│           ├── accounts.py
│           ├── graph.py
│           ├── investigation.py
│           └── cases.py
│
├── dashboard/
│   ├── app.py
│   └── components/
│       ├── case_queue.py
│       ├── risk_panel.py
│       ├── graph_panel.py
│       ├── timeline_panel.py
│       ├── evidence_panel.py
│       ├── explanation_panel.py
│       └── case_panel.py
│
├── models_artifacts/
│   ├── xgboost/
│   ├── isolation_forest/
│   ├── autoencoder/
│   └── temporal_gat/
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_features.py
│   ├── test_flow.py
│   ├── test_graph.py
│   ├── test_models.py
│   ├── test_risk.py
│   ├── test_agent.py
│   └── test_api.py
│
└── docs/
    ├── HLD.md
    ├── architecture.md
    ├── model_card.md
    ├── evaluation.md
    ├── api.md
    └── demo_script.md
```

---

# 8. DATABASE SCHEMA

Use PostgreSQL.

## transactions

```text
transaction_id TEXT PRIMARY KEY
timestamp TIMESTAMP NOT NULL
sender_account_id TEXT NOT NULL
receiver_account_id TEXT NOT NULL
amount NUMERIC NOT NULL
currency TEXT NOT NULL
channel TEXT NOT NULL
transaction_type TEXT NOT NULL
merchant_category TEXT NULL
location TEXT NULL
status TEXT NOT NULL
scenario_id TEXT NULL
created_at TIMESTAMP NOT NULL
```

Constraints:

```text
amount > 0
sender_account_id != receiver_account_id
```

## accounts

```text
account_id TEXT PRIMARY KEY
customer_id TEXT NOT NULL
account_type TEXT
creation_date DATE
segment TEXT
risk_profile TEXT
status TEXT
home_region TEXT
```

## customers

```text
customer_id TEXT PRIMARY KEY
customer_type TEXT
occupation_or_business_category TEXT
expected_activity_category TEXT
geographic_region TEXT
```

## alerts

```text
alert_id TEXT PRIMARY KEY
account_id TEXT NOT NULL
created_at TIMESTAMP
priority_score FLOAT
risk_band TEXT
trigger_source TEXT
status TEXT
summary TEXT
```

## investigations

```text
case_id TEXT PRIMARY KEY
alert_id TEXT
account_id TEXT
started_at TIMESTAMP
completed_at TIMESTAMP
status TEXT
agent_version TEXT
summary TEXT
```

## evidence

```text
evidence_id TEXT PRIMARY KEY
case_id TEXT
evidence_type TEXT
account_id TEXT
transaction_id TEXT
timestamp TIMESTAMP
source TEXT
value JSONB
calculation TEXT
explanation TEXT
created_at TIMESTAMP
```

## findings

```text
finding_id TEXT PRIMARY KEY
case_id TEXT
category TEXT
severity TEXT
title TEXT
description TEXT
evidence_ids JSONB
confidence_label TEXT
```

## model_scores

```text
score_id TEXT PRIMARY KEY
case_id TEXT
xgboost_score FLOAT
isolation_score FLOAT
autoencoder_score FLOAT
temporal_gat_score FLOAT
behavior_signal FLOAT
flow_signal FLOAT
temporal_signal FLOAT
graph_signal FLOAT
final_score FLOAT
created_at TIMESTAMP
```

## case_memory

```text
memory_id TEXT PRIMARY KEY
case_id TEXT
memory_type TEXT
key TEXT
value JSONB
created_at TIMESTAMP
```

---

# 9. SYNTHETIC DATA GENERATOR

Build a configurable deterministic generator.

Use:

```text
DEMO_SEED=42
```

Normal patterns:

- salary
- rent
- utilities
- groceries
- subscriptions
- shopping
- regular P2P
- supplier payments
- business receipts

Create distinct behavioral profiles:

```text
salary account:
  predictable monthly inflows

student:
  low transaction volume

merchant:
  frequent customer inflows
  multiple supplier outflows

small business:
  periodic inflow
  supplier payment clusters
```

Suspicious demonstration scenarios:

1. Rapid redistribution
2. New-recipient burst
3. Fan-in
4. Fan-out
5. Multi-hop movement
6. Unusual amount
7. Behavioral deviation
8. Temporal burst
9. Combined scenario

Scenario metadata:

```text
scenario_id
involved_accounts
expected_signals
transaction_ids
ground_truth_pattern
```

Use:

```text
ground_truth_pattern = "synthetic_suspicious_pattern"
```

---

# 10. DATA QUALITY PIPELINE

```text
Raw data
 ↓
Schema validation
 ↓
Type normalization
 ↓
Timestamp normalization
 ↓
Duplicate detection
 ↓
Entity normalization
 ↓
Transaction validation
 ↓
Missing-value handling
 ↓
Processed data
```

Log:

```text
input_rows
valid_rows
invalid_rows
duplicate_rows
rows_dropped
drop_reasons
execution_time
```

Never silently discard rows.

---

# 11. BEHAVIORAL BASELINE ENGINE

Calculate historical account profile:

```text
average_inflow
std_inflow
median_inflow
average_outflow
std_outflow
median_outflow
average_transaction_amount
std_transaction_amount
transactions_per_day
transactions_per_week
average_daily_volume
average_weekly_volume
usual_transaction_hours
usual_days_of_week
usual_channels
usual_recipient_count
usual_recipient_set
historical_inflow_outflow_ratio
```

Current deviation:

```text
deviation =
abs(current_value - baseline_mean)
/
(baseline_std + epsilon)
```

Support robust alternatives for skewed monetary data:

```text
log1p(amount)
median/MAD
```

Output:

```text
behavior_deviation_score
```

Important: Baselines may use ONLY historical information available before the alert.

---

# 12. TEMPORAL FEATURE ENGINE

Use multiple windows:

```text
15m
1h
6h
24h
3d
7d
```

Per window:

```text
inflow_total
outflow_total
transaction_count
incoming_count
outgoing_count
unique_counterparties
new_counterparties
new_counterparty_ratio
transaction_velocity
amount_velocity
```

Also calculate:

```text
time_to_first_outflow
time_to_50pct_outflow
time_to_90pct_outflow
```

These support rapid-redistribution detection.

---

# 13. FLOW ANALYSIS ENGINE

Primary signal:

```text
conservation_ratio(window) =
relevant_outflow(window)
/
(relevant_inflow(window) + epsilon)
```

Also calculate:

```text
redistribution_ratio
inflow_outflow_ratio
net_flow
recipient_count
new_recipient_count
new_recipient_ratio
amount_concentration
recipient_concentration
onward_movement
downstream_amount
```

Do NOT hard-code a universal suspicious threshold.

Example:

```text
conservation_ratio = 0.97
time_to_90pct_outflow = 48 minutes
new_recipient_ratio = 0.83
```

Explain:

> A large portion of recent inflow was followed by rapid outflow to mostly new counterparties, increasing investigation priority.

Never state that this proves illegal activity.

---

# 14. GRAPH ENGINE

Directed weighted graph:

```text
node = account
edge = transaction
edge weight = amount
edge timestamp = transaction timestamp
```

Node features:

```text
in_degree
out_degree
weighted_in_degree
weighted_out_degree
unique_counterparties
fan_in
fan_out
new_counterparty_ratio
degree_centrality
betweenness_centrality
community_id
```

Avoid expensive algorithms on large graphs if they hurt demo latency.

---

# 15. GRAPH TRAVERSAL

Implement:

```text
get_neighbors(account_id, direction)
expand_k_hop(account_id, hops)
find_paths(source, target, max_depth)
get_connected_entities(account_id)
```

Return structured results.

Example:

```json
{
  "source_account": "A102",
  "hops": 2,
  "nodes": ["A102", "A205", "A309"],
  "edges": ["T1001", "T1009"],
  "path_count": 2
}
```

---

# 16. POTENTIAL FUND LINEAGE

Implement a heuristic lineage engine.

Goal:

```text
A → B → C → D
```

Associate candidate downstream movement using:

- timestamp proximity
- amount relationship
- transaction sequence
- partial redistribution
- balance context where available

Return:

```text
potential_lineage
```

Example:

```json
{
  "origin_transaction": "T001",
  "candidate_downstream_transactions": ["T010", "T014"],
  "depth": 2,
  "lineage_strength": 0.82,
  "reason": "Temporal proximity and amount relationship"
}
```

Use labels such as:

```text
potential_downstream_lineage
```

Never:

```text
confirmed_source_of_funds
```

---

# 17. NETWORK FEATURES

For investigation targets:

```text
degree
weighted_degree
in_degree
out_degree
fan_in
fan_out
counterparty_count
new_counterparty_ratio
centrality
suspicious_neighbor_count
k_hop_network_size
network_depth
downstream_activity
path_count
community_id
```

These features feed both detection and evidence.

---

# 18. XGBOOST

Purpose:

Supervised tabular detection.

Inputs:

- behavioral
- temporal
- flow
- network
- entity/context features

Output:

```text
xgboost_score ∈ [0,1]
```

Training:

- synthetic labels
- time-aware split where possible
- no future leakage
- persisted artifact

Evaluate:

```text
precision
recall
F1
PR-AUC
ROC-AUC
false positive rate
false discovery rate
```

Explainability:

- SHAP preferred
- native model importance as fallback

Persist top contributions.

---

# 19. ISOLATION FOREST

Purpose:

Detect unusual entities without depending on supervised labels.

Output:

```text
isolation_score ∈ [0,1]
```

Normalize so larger = more anomalous.

---

# 20. AUTOENCODER

Architecture:

```text
Input
 ↓
Dense
 ↓
Latent
 ↓
Dense
 ↓
Reconstruction
```

Train mainly on normal synthetic behavior.

Anomaly score:

```text
reconstruction_error =
mean_squared_error(input, reconstruction)
```

Normalize to:

```text
autoencoder_score ∈ [0,1]
```

Persist artifact.

If training is unstable, use a documented deterministic fallback rather than breaking the product.

---

# 21. TEMPORAL GAT

Use PyTorch Geometric.

Node features:

- behavioral
- temporal
- flow
- network

Edge features:

- amount
- time delta / temporal encoding
- transaction metadata where useful

Architecture:

```text
Node features
 ↓
Linear projection
 ↓
GATConv
 ↓
Non-linearity
 ↓
GATConv
 ↓
Risk head
 ↓
temporal_gat_score
```

Use a shallow architecture for reliability.

If a fully sophisticated temporal formulation is unstable, use:

```text
GAT + explicit temporal features
```

Document what is actually implemented.

---

# 22. MODEL SCORE NORMALIZATION

Store:

```text
xgboost_score
isolation_score
autoencoder_score
temporal_gat_score
```

Transform scores to comparable [0,1] ranges.

Use calibration/training-set statistics where appropriate.

Never blindly average raw scores with different scales.

---

# 23. DETERMINISTIC SIGNALS

Calculate:

```text
behavior_signal
temporal_signal
flow_signal
graph_signal
```

All in:

```text
[0,1]
```

Sub-rules must remain inspectable.

---

# 24. RISK FUSION

Starting configuration:

```yaml
weights:
  xgboost: 0.20
  isolation_forest: 0.10
  autoencoder: 0.10
  temporal_gat: 0.20
  behavior: 0.10
  temporal: 0.10
  flow: 0.10
  graph: 0.10
```

Normalize weights to 1.

Formula:

```text
risk_score =
Σ(weight_i × normalized_signal_i) × 100
```

Bands:

```text
0-30    LOW
30-60   MEDIUM
60-80   HIGH
80-100  CRITICAL
```

Name:

> Investigation Priority Score

---

# 25. INVESTIGATION ORCHESTRATOR

Build ONE primary intelligent orchestrator.

Flow:

```text
ALERT
 ↓
Inspect account
 ↓
Fetch history
 ↓
Analyze multiple windows
 ↓
Analyze behavior deviation
 ↓
Analyze flow
 ↓
Build graph
 ↓
Expand k-hop
 ↓
Trace potential lineage
 ↓
Inspect model scores
 ↓
Collect evidence
 ↓
Rank findings
 ↓
Generate grounded summary
 ↓
Generate case report
```

The agent should adapt based on signals instead of blindly running a fixed script.

---

# 26. INVESTIGATION TOOLS

Implement typed read-only functions:

```text
get_account_profile(account_id)

get_customer_profile(customer_id)

get_account_history(account_id)

get_recent_transactions(account_id, window)

get_inflows(account_id, window)

get_outflows(account_id, window)

analyze_time_windows(account_id)

calculate_velocity(account_id, window)

calculate_conservation(account_id, window)

calculate_behavior_deviation(account_id)

build_subgraph(account_id, hops)

expand_k_hop(account_id, hops)

find_paths(source_account, target_account, max_depth)

trace_potential_lineage(transaction_id, depth)

get_connected_entities(account_id)

get_model_scores(account_id)

get_feature_contributions(case_id)

generate_counterfactual(case_id)

create_timeline(case_id)

collect_evidence(case_id)

generate_case_report(case_id)
```

Each tool returns structured JSON-compatible data.

---

# 27. TOOL CALL LOGGING

Log each tool call:

```json
{
  "case_id": "CASE-0001",
  "tool": "calculate_conservation",
  "arguments": {
    "account_id": "A102",
    "window": "24h"
  },
  "result_summary": "conservation_ratio=0.93",
  "timestamp": "..."
}
```

Also log:

```text
duration
status
error
```

This enables both debugging and a convincing live investigation progress panel.

---

# 28. AGENT MEMORY

## Case memory

Persist:

- case id
- alert id
- tools called
- calculations
- findings
- evidence ids
- score history
- summary
- report state

## Entity memory

Persist:

- historical behavior
- prior alerts
- counterparties
- historical risk signals
- behavior changes

Prefer structured storage.

Do not make vector memory a P0 feature.

---

# 29. ADAPTIVE PLANNER

Examples:

```text
IF behavior deviation is low:
    prioritize temporal and flow analysis

IF flow signal is high:
    inspect downstream recipients

IF new-recipient ratio is high:
    expand graph

IF downstream movement exists:
    run lineage tracing

IF model disagreement is high:
    inspect explanations and sensitivity
```

No irreversible actions.

---

# 30. EVIDENCE LEDGER

Every finding must map to evidence.

Example:

```text
Finding F-004

Title:
Rapid redistribution of incoming funds

Evidence:
E-101
E-102
E-103

Transactions:
T1001
T1005
T1008

Calculation:
₹9,70,000 / ₹10,00,000 = 0.97

Observed period:
48 minutes
```

No report finding should exist without evidence references.

This is a major product differentiator.

---

# 31. TIMELINE ENGINE

Create chronological investigation events:

```text
10:04  +₹10,00,000
10:21  -₹3,20,000
10:36  -₹2,80,000
11:02  -₹1,70,000
11:18  -₹2,00,000
```

Annotations:

```text
new recipient
large outflow
rapid redistribution
downstream movement
behavioral deviation
```

---

# 32. EXPLAINABILITY

Three levels.

## Component explanation

```text
Flow        HIGH
Behavior    HIGH
Temporal    HIGH
Graph       HIGH
```

## Model explanation

XGBoost:

- SHAP preferred
- native feature importance fallback

Example:

```text
new_recipient_ratio      +0.18
time_to_90pct_outflow    +0.15
conservation_ratio       +0.13
transaction_velocity     +0.09
```

For Isolation Forest, Autoencoder, and GAT, use honest score sensitivity or feature/group contribution analysis.

Never fabricate SHAP values.

## Evidence explanation

Signal → calculation → transactions.

Example:

```text
Signal:
Rapid redistribution

Evidence:
T1001, T1005, T1008

Calculation:
0.97 conservation ratio

Observed:
48 minutes
```

---

# 33. COUNTERFACTUAL / SENSITIVITY

Provide:

```text
baseline_score
score_without_flow
score_without_graph
score_without_behavior
score_without_temporal
score_without_xgboost
```

Example:

```text
Current                 91
Without flow            67
Without graph           78
Without behavior        72
Without temporal        81
```

UI label:

> Score sensitivity

Do not claim causal certainty.

---

# 34. CASE REPORT

Generate:

```text
Case ID
Investigation status
Investigation priority
Subject account
Observed time range

Executive summary

Key findings

Behavioral analysis

Temporal analysis

Flow analysis

Graph/network analysis

Potential downstream lineage

Model signals

Evidence references

Sensitivity analysis

Recommended review steps

Human review disclaimer
```

The LLM may generate prose, but factual values must come from structured case data.

---

# 35. DASHBOARD

Primary investigator screen:

```text
┌────────────────────────────────────────────────────────────────┐
│ LAUNDRALENS X                              CASE-2026-0042     │
├──────────────┬────────────────────────────┬───────────────────┤
│ CASE QUEUE   │      TRANSACTION GRAPH     │ AI INVESTIGATOR   │
│ Critical 4   │            B              │ Investigation     │
│ High 12      │         / | \              │ complete          │
│ Medium 31    │        C  D  E             │                   │
│ Low 82       │           |                │ Key findings      │
│              │           F                │ ...               │
├──────────────┴────────────────────────────┴───────────────────┤
│                  INVESTIGATION PRIORITY                       │
│                         91 / 100                              │
│     Flow       Graph       Behavior       Temporal             │
├────────────────────────────────────────────────────────────────┤
│ TIMELINE                                                       │
│ 10:04 +₹10L → 10:21 -₹3.2L → 10:36 -₹2.8L → ...             │
├────────────────────────────────────────────────────────────────┤
│ Evidence │ WHY? │ SCORE SENSITIVITY │ CASE REPORT              │
└────────────────────────────────────────────────────────────────┘
```

UI requirements:

- case queue
- risk score
- graph
- timeline
- investigation progress
- evidence
- why explanation
- sensitivity
- generated case report

---

# 36. INVESTIGATION PROGRESS

When clicking INVESTIGATE, show:

```text
✓ Loading account history
✓ Establishing baseline
✓ Analyzing temporal windows
✓ Measuring fund redistribution
✓ Building transaction graph
✓ Expanding connected entities
✓ Tracing potential lineage
✓ Running model analysis
✓ Collecting evidence
✓ Preparing findings
✓ Generating report
```

Persist real investigation state so the UI is not merely cosmetic.

---

# 37. API DESIGN

Base:

```text
/api/v1
```

Health:

```http
GET /api/v1/health
```

Alerts:

```http
GET /api/v1/alerts
GET /api/v1/alerts/{alert_id}
```

Accounts:

```http
GET /api/v1/accounts/{account_id}
GET /api/v1/accounts/{account_id}/transactions
GET /api/v1/accounts/{account_id}/behavior
```

Graph:

```http
GET /api/v1/graph/{account_id}
GET /api/v1/graph/{account_id}/expand?hops=2
GET /api/v1/graph/{account_id}/lineage
```

Investigation:

```http
POST /api/v1/investigations
GET /api/v1/investigations/{case_id}
GET /api/v1/investigations/{case_id}/timeline
GET /api/v1/investigations/{case_id}/evidence
GET /api/v1/investigations/{case_id}/explanations
GET /api/v1/investigations/{case_id}/counterfactual
```

Case:

```http
GET /api/v1/cases/{case_id}
POST /api/v1/cases/{case_id}/report
```

Use Pydantic request/response schemas.

---

# 38. EXAMPLE RISK RESPONSE

```json
{
  "case_id": "CASE-2026-0042",
  "account_id": "A102",
  "priority_score": 91,
  "risk_band": "CRITICAL",
  "signals": {
    "behavior": 0.86,
    "temporal": 0.91,
    "flow": 0.96,
    "graph": 0.88
  },
  "models": {
    "xgboost": 0.90,
    "isolation_forest": 0.83,
    "autoencoder": 0.88,
    "temporal_gat": 0.92
  }
}
```

Example is a response shape only; actual values must come from the running system.

---

# 39. EVALUATION

Never fabricate results.

Detection:

```text
precision
recall
F1
PR-AUC
ROC-AUC
false positive rate
false discovery rate
```

Operations:

```text
alerts generated
investigation completion rate
average investigation runtime
evidence retrieval time
report generation time
```

Agent:

```text
tool-call success rate
investigation completion rate
unsupported-claim rate
evidence grounding rate
```

Clearly state:

> Evaluation uses synthetic/anonymized demonstration data and does not represent production financial-crime performance.

---

# 40. DATA LEAKAGE CONTROLS

Mandatory:

- no future transactions in past-alert features
- historical baselines use only pre-alert history
- time-aware train/test split where practical
- separate synthetic scenario generation from evaluation where possible
- log random seed
- log feature configuration

---

# 41. PERFORMANCE TARGETS

Aim for:

```text
Dashboard load < 3 sec
Investigation < 10–20 sec
Graph expansion < 2 sec
Case report < 10 sec
```

Use caching for:

- graph objects
- features
- model outputs
- case state

The exact timings are targets, not claims.

---

# 42. ERROR HANDLING

LLM unavailable:

```text
Generate deterministic evidence-based summary
```

Temporal GAT unavailable:

```text
Use graph + temporal deterministic signals
```

SHAP unavailable:

```text
Use model-native feature importance
```

Database unavailable:

```text
Return explicit error
```

Never fabricate data to hide an error.

---

# 43. CONFIGURATION

Example:

```yaml
windows:
  - 15m
  - 1h
  - 6h
  - 24h
  - 3d
  - 7d

graph:
  default_hops: 2
  max_lineage_depth: 4

risk:
  bands:
    low: 30
    medium: 60
    high: 80

weights:
  xgboost: 0.20
  isolation_forest: 0.10
  autoencoder: 0.10
  temporal_gat: 0.20
  behavior: 0.10
  temporal: 0.10
  flow: 0.10
  graph: 0.10
```

No scattered magic numbers.

---

# 44. LLM RULES

System prompt must enforce:

1. Use only supplied structured evidence.
2. Never invent transaction facts.
3. Never fabricate evidence IDs.
4. Never claim wrongdoing.
5. Distinguish observations from interpretations.
6. State uncertainty.
7. Recommend human review.
8. Never request or perform irreversible actions.

Expected format:

```text
Executive Summary
Observed Signals
Evidence
Interpretation
Uncertainty
Recommended Review
```

---

# 45. INVESTIGATION STATE MACHINE

```text
ALERT_CREATED
      ↓
INVESTIGATION_STARTED
      ↓
ACCOUNT_PROFILE_LOADED
      ↓
HISTORY_LOADED
      ↓
TEMPORAL_ANALYSIS_COMPLETE
      ↓
FLOW_ANALYSIS_COMPLETE
      ↓
GRAPH_ANALYSIS_COMPLETE
      ↓
LINEAGE_ANALYSIS_COMPLETE
      ↓
MODEL_ANALYSIS_COMPLETE
      ↓
EVIDENCE_COLLECTED
      ↓
FINDINGS_READY
      ↓
REPORT_READY
      ↓
HUMAN_REVIEW
```

Persist current state.

---

# 46. TESTING

Unit tests:

- schema validation
- baseline calculation
- temporal windows
- conservation ratio
- velocity
- graph traversal
- lineage
- score normalization
- risk fusion
- evidence references

Integration:

```text
alert → investigation → tools → evidence → report
```

API tests for all routes.

Demo regression:

```text
investigation completes
score generated
timeline generated
graph generated
evidence > 0
report generated
```

Do not assert fake hard-coded model scores.

---

# 47. DEVELOPMENT PHASES

## Phase 0 — Bootstrap

Create repo, environment, settings, logging, FastAPI, Streamlit.

Success:

```text
backend starts
dashboard starts
health endpoint works
```

## Phase 1 — Data

Implement:

- database
- synthetic generator
- validation
- normalization
- seeding

Success:

```text
thousands of transactions
multiple planted scenarios
reproducible seed
```

## Phase 2 — Features

Implement:

- behavioral
- temporal
- flow
- network

Success:

```text
feature vector per investigation target
```

## Phase 3 — Detection

Implement:

- XGBoost
- Isolation Forest
- Autoencoder
- score normalization
- evaluation

Success:

```text
each returns normalized scores
```

## Phase 4 — Graph

Implement:

- graph construction
- k-hop
- path search
- graph features
- potential lineage

Success:

```text
main scenario forms readable multi-hop graph
```

## Phase 5 — Temporal GAT

Implement PyG graph data, temporal features, shallow GAT.

Fallback:

```text
GAT + explicit temporal features
```

## Phase 6 — Risk

Implement signals, fusion, bands, explanation data.

## Phase 7 — Investigation Agent

Implement:

- typed tools
- orchestrator
- planner
- state machine
- memory
- logging

Success:

```text
one click runs investigation
```

## Phase 8 — Evidence

Implement:

- ledger
- timeline
- SHAP
- sensitivity
- report

## Phase 9 — Dashboard

Implement all investigator UI.

## Phase 10 — Hardening

Run:

- tests
- failure tests
- performance checks
- UI polish
- docs
- demo recording

No major architecture changes after this phase.

---

# 48. PRIORITY SYSTEM

## P0 — MUST WORK

- synthetic data
- PostgreSQL
- feature engine
- flow analysis
- behavioral analysis
- temporal analysis
- graph
- XGBoost
- Isolation Forest
- risk fusion
- investigation agent
- evidence ledger
- dashboard

## P1 — HIGH VALUE

- Autoencoder
- Temporal GAT
- potential lineage
- SHAP
- sensitivity
- report generation
- polished graph visualization

## P2 — ONLY AFTER P0/P1

- community detection
- graph embeddings
- drift detection
- continual learning
- vector memory

Do NOT spend core time on:

- Kubernetes
- distributed microservices
- real bank integrations
- production streaming
- mobile app
- complicated authentication
- account freezing

A clean modular monolith is preferred for this hackathon prototype.

---

# 49. DEMO MODE

Config:

```text
DEMO_MODE=true
DEMO_CASE_ID=CASE-DEMO-001
```

Dashboard should open directly on the strongest demo case.

Controls:

```text
Run Investigation
Reset Demo
Regenerate Scenario
```

No manual database editing during the demo.

---

# 50. 5-MINUTE DEMO SCRIPT

## 0:00–0:30 — Problem

Show transaction universe and alert queue.

Narration:

> Financial-risk systems can generate alerts, but investigators still need to reconstruct the story behind those alerts. LaundraLens X turns an alert into an automated, evidence-grounded investigation.

## 0:30–1:00 — Alert

Open critical synthetic case.

Show:

```text
Investigation Priority: 91/100
```

Narration:

> The system does not call this account criminal. It prioritizes the case because several independent signals agree.

## 1:00–2:00 — Investigation

Click:

```text
INVESTIGATE
```

Show real tool execution.

## 2:00–3:00 — Explain

Show:

- graph
- timeline
- flow signal
- new counterparties
- behavioral deviation
- model ensemble

## 3:00–4:00 — WHY + WHAT IF

Show the evidence-backed explanation.

Then show:

```text
Current
Without flow
Without graph
Without behavior
```

## 4:00–4:40 — Evidence

Show evidence ledger.

Each major finding links to transactions and calculations.

## 4:40–5:00 — Case

Generate report.

Closing line:

> LaundraLens X does not replace the investigator. It compresses the investigation process — from alert to connected evidence and an investigator-ready case.

---

# 51. VISUAL DESIGN

Aim for a professional analyst workstation.

Use:

- consistent typography
- clean cards
- strong hierarchy
- readable graphs
- timeline annotations
- risk badges
- progress states
- subtle motion only where useful

Avoid:

- generic chatbot-first UI
- excessive gradients
- irrelevant animations
- clutter
- too many screens

The visual narrative is:

```text
Alert → Investigation → Graph → Evidence → Case
```

---

# 52. DOCUMENTATION

README:

1. Problem
2. Product
3. Architecture
4. Innovations
5. Data strategy
6. ML stack
7. Agent architecture
8. Explainability
9. Security boundaries
10. Setup
11. Running
12. Demo
13. Evaluation
14. Limitations
15. Future work

Model card:

```text
purpose
training data
features
evaluation
limitations
failure modes
score interpretation
human-review requirement
```

---

# 53. ANTIGRAVITY EXECUTION RULES

Antigravity must:

1. Build incrementally.
2. Write real code, not pseudocode.
3. Keep modules testable.
4. Avoid placeholder P0 functionality.
5. Externalize configuration.
6. Add tests with core modules.
7. Run the app after major phases.
8. Fix failures before continuing.
9. Never fabricate metrics.
10. Never fabricate evidence.
11. Never commit secrets.
12. Prefer reliable advanced features over unstable theoretical complexity.
13. Make the demo deterministic.
14. Keep the full system runnable from documented commands.
15. Do not perform unnecessary architecture rewrites.

When a sophisticated component fails, preserve the interface and provide a clearly documented fallback so the complete product remains usable.

---

# 54. ACCEPTANCE CRITERIA

The full product is complete only when:

```text
Start application
      ↓
Open dashboard
      ↓
See transaction universe
      ↓
See alert queue
      ↓
Open demo case
      ↓
Click INVESTIGATE
      ↓
Agent executes tools
      ↓
Temporal analysis appears
      ↓
Behavior analysis appears
      ↓
Flow signal appears
      ↓
Graph appears
      ↓
Potential lineage appears
      ↓
Model scores appear
      ↓
Final investigation priority appears
      ↓
Evidence ledger appears
      ↓
WHY appears
      ↓
WHAT-IF appears
      ↓
Case report appears
      ↓
Human review state
```

No manual database edits.

No fabricated results.

No unsupported factual claims.

---

# 55. FINAL DEFINITION OF DONE

Done means:

- backend runs
- dashboard runs
- database seeds successfully
- synthetic scenario reproducible
- feature engine works
- XGBoost works
- Isolation Forest works
- graph intelligence works
- risk fusion works
- investigation agent works
- evidence ledger works
- timeline works
- explanation works
- sensitivity works
- report works
- Autoencoder works or has documented fallback
- Temporal GAT works or has documented fallback
- tests pass
- README works
- demo works cleanly
- no secrets committed

---

# 56. FINAL IMPLEMENTATION PRINCIPLE

Do NOT build:

```text
LLM + dashboard
```

Build:

```text
Data Intelligence
      +
Behavioral Analytics
      +
Temporal Analytics
      +
Flow Intelligence
      +
Graph Intelligence
      +
Multi-Model Detection
      +
Agentic Investigation
      +
Evidence Provenance
      +
Explainability
      +
Human Review
```

The AI should be useful because it can reason over structured financial evidence, not because the UI contains a chatbot.

The intended reviewer reaction is:

> "This is not just a model. This is an investigation system."
