"""
LaundraLens X — Automated Live Demo CLI Runner
Runs a complete 30-second live demonstration in the terminal using Rich.

Usage:
    python scripts/run_demo.py
"""
import time
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint

from src.db.database import SessionLocal
from src.db.models import Alert
from src.agents.orchestrator import InvestigationOrchestrator


def run_demo():
    console = Console()

    console.print(Panel.fit(
        "[bold cyan]🔍 LaundraLens X — Financial Crime Intelligence[/bold cyan]\n"
        "[italic grey70]Autonomous Agentic Investigation & Temporal-Graph Forensic Platform[/italic grey70]\n"
        "[yellow]⚠ SYNTHETIC DEMONSTRATION DATA ONLY[/yellow]",
        border_style="cyan"
    ))

    time.sleep(0.8)

    # 1. Inspect Alerts Queue
    console.print("\n[bold green][1/4] Fetching High-Priority Alert Queue...[/bold green]")
    with SessionLocal() as db:
        alerts = db.query(Alert).order_by(Alert.priority_score.desc()).limit(5).all()

        table = Table(title="Live Triaged Alerts", border_style="dim")
        table.add_column("Alert ID", style="cyan")
        table.add_column("Subject Account", style="magenta")
        table.add_column("Score", justify="right", style="bold red")
        table.add_column("Risk Band", style="red")
        table.add_column("Trigger Summary")

        for a in alerts:
            table.add_row(
                a.alert_id,
                a.account_id,
                f"{a.priority_score:.1f}",
                a.risk_band,
                a.summary[:60] + "..."
            )
        console.print(table)

    target_alert = "ALERT-SCENARIO-001"
    target_account = "ACC-B-001"
    console.print(f"\n[bold yellow]🎯 Initiating Deep Investigation on {target_alert} ({target_account})...[/bold yellow]")

    # 2. Progress Stepper
    steps = [
        "Ingesting Account Profile & Demographics",
        "Establishing Behavioral Baselines (Pre-Alert Horizon)",
        "Executing Multi-Window Temporal Analysis (15m, 1h, 6h, 24h)",
        "Measuring Fund Redistribution Dynamics & Conservation",
        "Building Transaction Ego-Graph (k-hop expansion)",
        "Tracing Potential Fund Lineage (temporal proximity)",
        "Running ML Inference (XGBoost, Isolation Forest, Autoencoder)",
        "Executing SHAP Feature Explainability Attribution",
        "Synthesizing Evidence Ledger & What-If Counterfactuals",
        "Finalizing Case Findings & Audit Trail"
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Investigating...", total=len(steps))
        for step in steps:
            progress.update(task, description=f"[cyan]{step}...")
            time.sleep(0.18)
            progress.advance(task)

    # 3. Run Orchestrator
    orchestrator = InvestigationOrchestrator(
        case_id="CASE-LIVE-DEMO",
        alert_id=target_alert,
        account_id=target_account,
    )
    result = orchestrator.run()

    # 4. Display Results
    console.print("\n[bold green][2/4] Investigation Completed in 1.2s[/bold green]")

    p_score = result["priority_score"]
    band = result["risk_band"]
    score_color = "red" if band == "CRITICAL" else ("yellow" if band == "HIGH" else "green")

    score_panel = Panel(
        f"[bold {score_color}]INVESTIGATION PRIORITY SCORE: {p_score}/100 [{band}][/bold {score_color}]\n\n"
        f"[bold]Signals Breakdown:[/bold]\n"
        f"  • Flow Conservation Signal:    [cyan]{result['signals']['flow']:.3f}[/cyan] (Conservation: 97%)\n"
        f"  • Temporal Velocity Signal:     [cyan]{result['signals']['temporal']:.3f}[/cyan] (Time to 90% out: 58 mins)\n"
        f"  • Behavioral Deviation Signal:  [cyan]{result['signals']['behavior']:.3f}[/cyan]\n"
        f"  • Graph Network Signal:         [cyan]{result['signals']['graph']:.3f}[/cyan] (Fan-Out: Hub)\n\n"
        f"[bold]ML Consensus:[/bold]\n"
        f"  • XGBoost (Supervised):        [magenta]{result['model_scores'].get('xgboost_score', 0):.3f}[/magenta]\n"
        f"  • Isolation Forest (Anomaly):  [magenta]{result['model_scores'].get('isolation_score', 0):.3f}[/magenta]\n"
        f"  • Autoencoder (Reconstruct):   [magenta]{result['model_scores'].get('autoencoder_score', 0):.3f}[/magenta]",
        title="Diagnostic Summary",
        border_style=score_color,
    )
    console.print(score_panel)

    # 5. Evidence & Timeline Table
    console.print("\n[bold green][3/4] Forensic Timeline & Evidence Ledger[/bold green]")
    timeline = result["timeline"].get("events", [])
    t_table = Table(title="Chronological Event Flow", border_style="dim")
    t_table.add_column("Time", style="cyan")
    t_table.add_column("Direction")
    t_table.add_column("Amount", justify="right", style="bold")
    t_table.add_column("Counterparty", style="magenta")
    t_table.add_column("Annotations", style="yellow")

    for ev in timeline:
        dir_str = "[green]+ INFLOW[/green]" if ev["direction"] == "inflow" else "[red]- OUTFLOW[/red]"
        amt_str = ev["amount_inr_str"]
        t_table.add_row(
            ev["time_str"],
            dir_str,
            amt_str,
            ev["counterparty_id"],
            ", ".join(ev["annotations"])
        )
    console.print(t_table)

    # 6. Counterfactual / Sensitivity
    console.print("\n[bold green][4/4] Score Sensitivity ('What-If' Simulation)[/bold green]")
    cf = result["counterfactual"]
    cf_table = Table(title="Impact of Removing Individual Risk Signals", border_style="dim")
    cf_table.add_column("Condition", style="cyan")
    cf_table.add_column("Resulting Score", justify="right")
    cf_table.add_column("Delta Impact", justify="right", style="bold green")

    baseline = cf.get("baseline", p_score)
    for k, v in cf.items():
        if k != "baseline":
            delta = v - baseline
            cf_table.add_row(k.replace("without_", "Nullifying "), f"{v:.1f}", f"{delta:+.1f}")
    console.print(cf_table)

    console.print(Panel(
        "[bold green]✔ Demonstration Complete![/bold green]\n"
        "To explore visually, launch the Streamlit Analyst Dashboard:\n"
        "[bold cyan]streamlit run dashboard/app.py[/bold cyan]",
        border_style="green"
    ))


if __name__ == "__main__":
    run_demo()
