# LaundraLens X — Technical Architecture & Specifications

## 1. Executive Architecture Overview
**LaundraLens X** is an Agentic Temporal-Graph Intelligence platform for autonomous financial crime investigation. It ingests high-velocity banking transaction logs, establishes historical behavioral baselines, models counterparty graph networks, evaluates a 3-tier machine learning ensemble, and autonomously executes an 11-step forensic investigation in **0.68 seconds**.

```
                                  DATA RAILS
                   ┌──────────────────────────────────────┐
                   │  Synthetic Payment Rails (5,061 TXs) │
                   │  UPI · IMPS · RTGS · NEFT · Cash     │
                   └──────────────────┬───────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │    PRE-ALERT TEMPORAL HORIZON PARTITIONER    │
               │  T < T_alert: Baseline  |  T >= T_alert: Obs │
               └──────────────────────┬───────────────────────┘
                                      │
       ┌──────────────────────────────┴──────────────────────────────┐
       ▼                                                             ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│  39-D FEATURE INTELLIGENCE   │              │  TEMPORAL GRAPH INTELLIGENCE │
│  • Flow Conservation (0.97)  │              │  • NetworkX Directed Graph   │
│  • Redistribution Timing     │              │  • Louvain Community Clusters│
│  • Velocity Burst Ratios     │              │  • Heuristic Lineage BFS     │
│  • Historical Log-Normal Dev │              │  • Syndicate Round-Tripping  │
└──────────────┬───────────────┘              └──────────────┬───────────────┘
               │                                             │
               ▼                                             │
┌──────────────────────────────┐                             │
│     ML DETECTION ENSEMBLE    │                             │
│  1. Supervised XGBoost+SHAP  │                             │
│  2. Isolation Forest         │                             │
│  3. PyTorch 5-Layer AE       │                             │
└──────────────┬───────────────┘                             │
               │                                             │
               └──────────────────────┬──────────────────────┘
                                      ▼
                   ┌──────────────────────────────────────┐
                   │    INVESTIGATION PRIORITY SCORER     │
                   │    Σ(w_i * Signal_i) * 100           │
                   │    What-If Counterfactual Sensitivity│
                   └──────────────────┬───────────────────┘
                                      │
                                      ▼
                   ┌──────────────────────────────────────┐
                   │     AI INVESTIGATION ORCHESTRATOR    │
                   │     11 State Machine Transitions     │
                   │     19 Typed Read-Only Forensics     │
                   │     Execution Latency: 0.68s         │
                   └──────────────────┬───────────────────┘
                                      │
       ┌──────────────────────────────┴──────────────────────────────┐
       ▼                                                             ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│  AUDITABLE EVIDENCE LEDGER   │              │   SAR DOSSIER GENERATOR      │
│  • Transaction Level Links   │              │   • Gemini Flash AI Writer   │
│  • SHA-256 Provenance Hash   │              │   • FIU-IND Regulatory HTML  │
│  • Mathematical Formulas     │              │   • Analyst Disposition Sign │
└──────────────────────────────┘              └──────────────────────────────┘
```

---

## 2. Feature Intelligence Mathematics

### 2.1. Fund Flow Conservation Ratio
Quantifies the fraction of received incoming capital that is forwarded to counterparties within a sliding observation window $W$:
$$\text{conservation\_ratio} = \frac{\sum_{t \in \text{Outflows}(W)} \text{amount}_t}{\sum_{t \in \text{Inflows}(W)} \text{amount}_t + \epsilon}$$
Where $\epsilon = 10^{-6}$ avoids division by zero. A conservation ratio $> 0.90$ combined with high velocity strongly indicates passthrough mule activity.

### 2.2. Redistribution Timing
Measures the latency between the primary inflow credit $t_{\text{in}}$ and subsequent outbound debits $t_{\text{out}}$:
- **Time to First Outflow**: $\Delta t_{\text{first}} = t_{\text{out}, 1} - t_{\text{in}}$
- **Time to 90% Outflow**: Time taken for cumulative outflows to reach 90% of the inflow credit.
- **Redistribution Speed Score**:
  $$S_{\text{speed}} = \exp\left(-\frac{\Delta t_{90\%}}{120\text{ mins}}\right)$$

### 2.3. Behavioral Baseline Deviation
Log-normal normalized difference between current transaction amounts and the account's historical average:
$$Z_{\text{amount}} = \frac{\ln(1 + \text{amount}_{\text{curr}}) - \mu_{\ln(\text{hist})}}{\sigma_{\ln(\text{hist})} + \epsilon}$$

---

## 3. Machine Learning Ensemble Formulations

| Model | Objective | Calibration / Scaling | Explainability |
|---|---|---|---|
| **XGBoost** | Supervised binary classification on planted synthetic typologies vs. normal background transactions | Class weight adjustment: $\text{scale\_pos\_weight} = \frac{N_{\text{neg}}}{N_{\text{pos}}}$ | Tree-based **SHAP** values attribute exact impact per feature |
| **Isolation Forest** | Unsupervised density anomaly estimation across 500 account feature vectors | Min-Max normalized anomaly score from tree path lengths $c(n)$ | Feature partition depth analysis |
| **PyTorch Autoencoder** | Unsupervised reconstruction error trained strictly on confirmed normal accounts | Mean Squared Error: $\text{MSE}(x, \hat{x}) = \frac{1}{D}\sum_{j=1}^D (x_j - \hat{x}_j)^2$ | Reconstruction error residuals per dimension |

---

## 4. Multi-Account Syndicate & Graph Forensics

### 4.1. Circular Round-Tripping Cycles
Identifies directed simple cycles $C = (v_1, v_2, \dots, v_k, v_1)$ where $3 \le k \le 5$, computing the circulating volume:
$$V(C) = \sum_{i=1}^{k} \text{weight}(v_i, v_{i+1})$$

### 4.2. Bipartite Funnel Smurfing
Detects accounts with high in-degree ($\text{fan-in} \ge 3$) and high out-degree ($\text{fan-out} \ge 2$) acting as high-throughput transit hubs.

---

## 5. Governance & Responsible AI Standards
1. **Zero Hallucination Guarantee**: AI case reports are strictly bounded by structured evidence items. The LLM cannot invent transaction hashes, currency quantities, or counterparty accounts.
2. **Read-Only Agent Sandbox**: Tools do not possess account-freezing or fund-reversing privileges.
3. **Audit Trail**: Every analyst disposition is permanently stored in the relational database with officer credentials and regulatory reason taxonomy.
