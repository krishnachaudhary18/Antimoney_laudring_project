"""
Centralized Terminology & Information Architecture Constants for LaundraLens X.
Provides unified, investigator-friendly AML vocabulary across the frontend
while preserving access to deep technical/ML engineering details.
"""

# === BRAND & PLATFORM IDENTITY ===
APP_NAME = "LaundraLens X"
APP_SUBTITLE = "AML INVESTIGATION PLATFORM"
APP_DESCRIPTION = "Prioritize alerts, investigate transaction activity, and review supporting evidence."

# === SIDEBAR NAVIGATION ===
NAVIGATION_ITEMS = [
    ("dashboard", "Dashboard", "📊", "What needs attention?"),
    ("alert_queue", "Alert Queue", "📋", "Which alerts should be investigated first?"),
    ("workspace", "Investigation Workspace", "🔬", "What happened?"),
    ("graph", "Transaction Network", "🕸", "How did the money move between connected accounts?"),
    ("timeline", "Activity Timeline", "⏱", "When did the unusual activity occur?"),
    ("evidence", "Investigation Evidence", "📎", "What supports the finding?"),
    ("explainability", "Why Was This Alert Raised?", "❓", "Why was this alert prioritized?"),
    ("sensitivity", "Risk Drivers", "⚡", "What factors influenced the priority?"),
    ("report", "Case Report", "📄", "What should the investigator review?"),
    ("settings", "Settings", "⚙", "Configure system parameters"),
]

# === RISK SCORE LABELS ===
SCORE_LABEL = "Investigation Priority"
SCORE_LABEL_FULL = "Investigation Priority Score"
SCORE_SUPPORTING_TEXT = "Multiple independent indicators contributed to this priority level."

RISK_BANDS = {
    "CRITICAL": {"label": "CRITICAL", "color": "#ef4444", "bg": "#fef2f2"},
    "HIGH": {"label": "HIGH", "color": "#f97316", "bg": "#fff7ed"},
    "MEDIUM": {"label": "MEDIUM", "color": "#f59e0b", "bg": "#fffbeb"},
    "LOW": {"label": "LOW", "color": "#10b981", "bg": "#ecfdf5"},
}

# === INVESTIGATION ASSISTANT (STEPPER) WORKFLOW ===
INVESTIGATION_STEPS = [
    ("kyc_profile", "Account History", "Account profile loaded", "Retail / Commercial customer baseline established"),
    ("behavior", "Historical Activity", "Historical activity compared", "Identified departure from normal historical activity"),
    ("temporal", "Activity Speed", "Transaction activity speed analyzed", "Measured rapid redistribution velocity over time"),
    ("flow", "Fund Movement", "Rapid movement of funds reviewed", "Observed rapid onward transfer of recent inflow"),
    ("graph", "Connected Accounts", "Connected accounts reviewed", "Identified immediate counterparties and transaction hub"),
    ("lineage", "Downstream Movement", "Potential downstream movement reviewed", "Traced potential onward movement through connected accounts"),
    ("models", "Risk Indicators", "Risk indicators assessed", "Cross-verified indicators across multiple detection models"),
    ("evidence", "Supporting Evidence", "Supporting evidence collected", "Assembled verifiable transaction records and audit ledger"),
    ("report", "Investigation Report", "Investigation report prepared", "Generated structured report for human compliance review"),
]

# === FORENSIC SIGNALS (BUSINESS vs TECHNICAL) ===
SIGNAL_MAPPINGS = {
    "flow": {
        "primary_label": "Rapid Movement of Funds",
        "description": "Portion of recent high-value inflow transferred onward within a short timeframe.",
        "technical_label": "Flow Conservation Ratio",
        "technical_formula": "outflow_in_window / inflow_in_window",
    },
    "temporal": {
        "primary_label": "Transaction Velocity",
        "description": "Speed and concentration of outgoing fund transfers.",
        "technical_label": "Temporal Velocity Compression",
        "technical_formula": "time_to_90pct_outflow",
    },
    "behavior": {
        "primary_label": "New Counterparty Activity",
        "description": "Frequency of transactions with recipients not seen in historical account profile.",
        "technical_label": "Behavioral Deviation Score",
        "technical_formula": "new_counterparty_ratio",
    },
    "graph": {
        "primary_label": "Network Connections",
        "description": "Degree of connectivity and transaction concentration with related accounts.",
        "technical_label": "Network Risk Indicator",
        "technical_formula": "ego_subgraph_centrality",
    },
}

# === DETECTION MODELS (BUSINESS vs TECHNICAL) ===
MODEL_MAPPINGS = {
    "xgboost": {
        "primary_name": "Supervised Risk Model",
        "technical_name": "XGBoost AML Classifier",
        "category": "Pattern Classification",
        "description": "Trained on verified typologies to detect structuring and layering patterns.",
        "weight_pct": 20,
        "status": "Active",
    },
    "isolation_forest": {
        "primary_name": "Behavioral Anomaly Model",
        "technical_name": "Isolation Forest Anomaly Detector",
        "category": "Anomaly Detection",
        "description": "Flags rare and unusual multidimensional transaction distributions.",
        "weight_pct": 10,
        "status": "Active",
    },
    "autoencoder": {
        "primary_name": "Behavioral Pattern Analysis",
        "technical_name": "Deep Autoencoder Reconstruction",
        "category": "Unsupervised Deep Learning",
        "description": "Measures reconstruction error against normal historical banking activity.",
        "weight_pct": 10,
        "status": "Active",
    },
    "network_risk": {
        "primary_name": "Network Risk Model",
        "technical_name": "Graph Feature Heuristic / Centrality",
        "category": "Graph Topology",
        "description": "Evaluates transaction relationships, edge timing, and entity structures.",
        "weight_pct": 15,
        "status": "Fallback / Development",
    },
}

# === TRANSACTION NETWORK CONTROLS ===
NETWORK_DEPTH_OPTIONS = [
    (1, "1 level", "Direct counterparties (immediate senders & receivers)"),
    (2, "2 levels", "Extended network (counterparties of counterparties)"),
    (3, "3 levels", "Wide network (deep connectivity and indirect paths)"),
]

# === CASE REPORT SECTIONS ===
REPORT_SECTIONS = [
    "Investigation Summary",
    "Account Overview",
    "Transaction Activity",
    "Fund Movement",
    "Network Connections",
    "Key Risk Drivers",
    "Supporting Evidence",
    "Model Assessment",
    "Potential Downstream Movement",
    "Investigator Review",
]
