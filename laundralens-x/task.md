# LaundraLens X — Task Tracker

## Phase 0 — Bootstrap [COMPLETED]
- [x] Create project folder structure
- [x] `requirements.txt`
- [x] `.env.example` + `.gitignore`
- [x] `config/settings.py`
- [x] `config/risk_config.yaml`
- [x] `config/demo_config.yaml`
- [x] `src/db/database.py`
- [x] `src/db/models.py`
- [x] `src/api/main.py` (FastAPI + health)
- [x] `dashboard/app.py` (Streamlit skeleton)
- [x] `dashboard/style.css`

## Phase 1 — Data Layer [COMPLETED]
- [x] `scripts/generate_synthetic_data.py` (5,061 transactions, 500 accounts/customers)
- [x] `scripts/seed_database.py` (9 scenario alerts + demo investigation seeded)
- [x] `src/db/repositories.py`
- [x] `src/ingestion/loader.py`
- [x] `src/ingestion/validator.py`
- [x] `src/ingestion/normalizer.py`

## Phase 2 — Feature Intelligence [COMPLETED]
- [x] `src/features/behavioral.py` (Pre-alert horizon, baseline deviation)
- [x] `src/features/temporal.py` (Multi-window velocity + redistribution speed)
- [x] `src/features/flow.py` (Conservation ratio, recipient concentration)
- [x] `src/features/network.py` (Degree centrality, ego subgraph betweenness)
- [x] `src/features/pipeline.py` (39-D unified feature vector)

## Phase 3 — ML Detection [COMPLETED]
- [x] `src/models/xgboost_model.py` (Supervised classifier + SHAP explainability)
- [x] `src/models/isolation_forest.py` (Unsupervised anomaly detector)
- [x] `src/models/autoencoder.py` (PyTorch reconstruction autoencoder)
- [x] `src/models/model_registry.py` (Singleton registry & batch inference)
- [x] `scripts/train_models.py` (All models trained, evaluated & saved)

## Phase 4 — Graph Intelligence [COMPLETED]
- [x] `src/graph/builder.py` (NetworkX directed graph + Louvain communities)
- [x] `src/graph/traversal.py` (k-hop expansion, path finder, connected entities)
- [x] `src/graph/lineage.py` (Potential downstream fund lineage tracer)
- [x] `src/graph/syndicate.py` (Multi-account circular round-tripping & funnel detection)
- [x] `src/graph/visualizer.py` (Interactive Pyvis HTML visualizer)
- [x] Graph API routes (`/api/v1/graph`)

## Phase 5 — Risk Fusion [COMPLETED]
- [x] `src/risk/scorer.py` (Investigation Priority Score: 0-100)
- [x] `src/risk/explanation.py` (Analyst narrative synthesizer)
- [x] `src/risk/counterfactual.py` (What-If sensitivity simulator)

## Phase 6 — Investigation Agent [COMPLETED]
- [x] `src/agents/tools.py` (All 19 typed read-only investigative tools)
- [x] `src/agents/orchestrator.py` (11-step state machine, runs in 0.68s)
- [x] `src/agents/planner.py` (Adaptive planning & branching)
- [x] `src/agents/memory.py` (Case memory manager)
- [x] `src/agents/prompts.py` (Investigation and SAR templates)
- [x] Investigation API routes (`/api/v1/investigations`)

## Phase 7 — Evidence + Reports [COMPLETED]
- [x] `src/evidence/ledger.py` (Forensic evidence index)
- [x] `src/evidence/timeline.py` (Event chronology builder)
- [x] `src/evidence/findings.py` (Findings manager)
- [x] `src/evidence/report.py` (Gemini Flash report writer + fallback)
- [x] `src/evidence/sar_dossier.py` (Formal FIU-IND regulatory dossier generator)

## Phase 8 — Dashboard & UI [COMPLETED]
- [x] `dashboard/style.css` (Glassmorphic dark-mode CSS design system)
- [x] `dashboard/app.py` (Full Streamlit analyst workstation with 6 forensic tabs)
- [x] `dashboard/components/` (7 modular component packages)
- [x] Interactive Pyvis network graph integration
- [x] SHAP waterfall chart (Plotly)
- [x] Score sensitivity simulator (Plotly)
- [x] Compliance Officer disposition workflow
- [x] Interactive web scenario stress tester

## Phase 9 — Governance & Benchmarks [COMPLETED]
- [x] `src/api/routes/decisions.py` (Human-in-the-loop audit logging)
- [x] `scripts/benchmark_performance.py` (Mean: 0.68s full agent cycle)
- [x] `scripts/simulate_scenario.py` (Custom injection stress tester)
- [x] `tests/` suite (21/21 tests passing, 100% green)

## Phase 10 — Polish + Demo Prep [COMPLETED]
- [x] `README.md` (Full repository documentation)
- [x] `docs/demo_script.md` (5-minute judge demonstration script)
- [x] `run_laundralens.bat` & `run_laundralens.ps1` (One-click launchers)
