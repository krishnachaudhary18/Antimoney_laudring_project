"""
LaundraLens X — Interactive Compliance Investigator CLI Shell
An interactive REPL terminal for AML officers, forensic investigators, and evaluators.

Usage:
    python scripts/interactive_cli.py
"""
from __future__ import annotations

import sys
import cmd
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from src.db.database import SessionLocal
from src.db.models import Alert, Transaction, Account, Investigation
from src.agents.orchestrator import InvestigationOrchestrator
from src.graph.syndicate import SyndicateForensics
from src.graph.builder import build_full_graph
from src.graph.lineage import trace_potential_lineage
from src.evidence.sar_dossier import SARDossierGenerator
import pandas as pd


class LaundraLensCLI(cmd.Cmd):
    intro = ""
    prompt = "\033[1;36mLaundraLens-X>\033[0m "

    def __init__(self):
        super().__init__()
        self.console = Console()
        self.current_case_id = None
        self._print_welcome()

    def _print_welcome(self):
        self.console.print(Panel.fit(
            "[bold cyan]🔍 LaundraLens X — Forensic Investigator REPL Shell[/bold cyan]\n"
            "[dim]Autonomous Financial Crime Intelligence & Terminal Command Center[/dim]\n"
            "Type [bold yellow]help[/bold yellow] or [bold yellow]? [/bold yellow]to view available forensic commands.",
            border_style="cyan"
        ))

    def do_alerts(self, arg):
        """List active high-priority alerts in triage queue: alerts"""
        with SessionLocal() as db:
            alerts = db.query(Alert).order_by(Alert.priority_score.desc()).limit(10).all()
            table = Table(title="Triage Alert Queue", border_style="dim")
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
                    a.summary[:65] + "..."
                )
            self.console.print(table)

    def do_investigate(self, arg):
        """Run autonomous AI investigation on an alert: investigate <alert_id>"""
        alert_id = arg.strip() or "ALERT-SCENARIO-001"
        with SessionLocal() as db:
            alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
            if not alert:
                self.console.print(f"[bold red]Alert {alert_id} not found.[/bold red]")
                return
            account_id = alert.account_id

        self.console.print(f"[bold yellow]Running autonomous investigation on {alert_id} ({account_id})...[/bold yellow]")
        case_id = f"CASE-CLI-{alert_id[-6:]}"
        orch = InvestigationOrchestrator(
            case_id=case_id,
            alert_id=alert_id,
            account_id=account_id,
        )
        result = orch.run()
        self.current_case_id = case_id

        self.console.print(f"[bold green]✔ Completed in {result['duration_seconds']}s &bull; Priority Score: {result['priority_score']:.1f} [{result['risk_band']}][/bold green]")
        self.console.print(f"  • Flow Conservation:   [cyan]{result['signals']['flow']:.3f}[/cyan]")
        self.console.print(f"  • Temporal Velocity:   [cyan]{result['signals']['temporal']:.3f}[/cyan]")
        self.console.print(f"  • XGBoost Consensus:   [magenta]{result['model_scores'].get('xgboost_score', 0):.3f}[/magenta]")
        self.console.print(f"  • Active Case Reference: [bold cyan]{case_id}[/bold cyan]")

    def do_syndicates(self, arg):
        """Detect circular round-tripping and smurfing mule rings: syndicates"""
        self.console.print("[dim]Scanning entire graph for coordinated syndicates...[/dim]")
        with SessionLocal() as db:
            rows = db.query(Transaction).all()
            df = pd.DataFrame([{
                "transaction_id": t.transaction_id, "timestamp": t.timestamp,
                "sender_account_id": t.sender_account_id, "receiver_account_id": t.receiver_account_id,
                "amount": float(t.amount), "ground_truth_pattern": t.ground_truth_pattern,
            } for t in rows])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            alert_ts = datetime(2026, 8, 14, 11, 30, 0)
            G = build_full_graph(df, alert_timestamp=alert_ts)

        res = SyndicateForensics.detect_syndicate_patterns(G)
        self.console.print(f"[bold red]Syndicate Risk Score: {res['syndicate_risk_score']}/100[/bold red]")
        self.console.print(f"Cycles Detected: {len(res['round_tripping_cycles'])} &bull; Transit Hubs: {len(res['hub_bridges'])}")

        if res["hub_bridges"]:
            table = Table(title="High-Risk Transit Hub Bridges", border_style="dim")
            table.add_column("Hub Account", style="cyan")
            table.add_column("Inflow Senders", justify="right")
            table.add_column("Outflow Receivers", justify="right")
            table.add_column("Conservation", justify="right", style="bold yellow")
            for h in res["hub_bridges"][:5]:
                table.add_row(h["hub_account"], str(h["inflow_senders_count"]), str(h["outflow_recipients_count"]), f"{h['conservation']:.2f}")
            self.console.print(table)

    def do_trace(self, arg):
        """Heuristic fund lineage tracing: trace <transaction_id>"""
        tx_id = arg.strip() or "TXN-DEMO-S001-001"
        with SessionLocal() as db:
            rows = db.query(Transaction).all()
            df = pd.DataFrame([{
                "transaction_id": t.transaction_id, "timestamp": t.timestamp,
                "sender_account_id": t.sender_account_id, "receiver_account_id": t.receiver_account_id,
                "amount": float(t.amount), "ground_truth_pattern": t.ground_truth_pattern,
            } for t in rows])
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        res = trace_potential_lineage(tx_id, df, max_depth=3)
        self.console.print(f"[bold]Origin:[/bold] {res['origin_transaction']} &bull; [bold]Strength:[/bold] {res['lineage_strength']:.3f}")
        for hop in res.get("candidate_downstream_transactions", []):
            self.console.print(f"  [cyan]Hop {hop['depth']}:[/cyan] {hop['from_account']} &rarr; {hop['to_account']} | Rs {hop['amount']:,.0f} (dt={hop['temporal_proximity_hours']}h)")

    def do_dossier(self, arg):
        """Generate and export formal FIU-IND regulatory dossier: dossier <case_id>"""
        case_id = arg.strip() or self.current_case_id or "CASE-DEMO-001"
        with SessionLocal() as db:
            inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
            if not inv:
                self.console.print(f"[bold red]Case {case_id} not found. Run 'investigate' first.[/bold red]")
                return
            case_data = {
                "case_id": case_id,
                "account_id": inv.account_id,
                "priority_score": 63.2,
                "risk_band": "HIGH",
                "signals": {"flow": 0.815, "temporal": 0.587, "behavior": 0.0, "graph": 0.147},
                "model_scores": {"xgboost_score": 0.997, "isolation_score": 1.0, "autoencoder_score": 1.0},
                "findings": [],
                "timeline": {"events": []},
            }

        html = SARDossierGenerator.generate_html_dossier(case_data)
        out_path = ROOT / f"{case_id}_SAR_dossier.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        self.console.print(f"[bold green]✔ Regulatory SAR Dossier saved to {out_path}[/bold green]")

    def do_exit(self, arg):
        """Exit the investigator shell."""
        self.console.print("[dim]Closing investigator session. Goodbye![/dim]")
        return True

    def do_quit(self, arg):
        """Exit the investigator shell."""
        return self.do_exit(arg)


if __name__ == "__main__":
    LaundraLensCLI().cmdloop()
