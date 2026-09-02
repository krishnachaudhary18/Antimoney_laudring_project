"""
LaundraLens X — Interactive Scenario Simulator & Stress Tester
Injects customized financial crime patterns into the sandbox database
to test how the agent, graph, and ML models adapt in real time.

Usage:
    python scripts/simulate_scenario.py --help
    python scripts/simulate_scenario.py --inflow 5000000 --outflow-count 6 --split-minutes 30
"""
from __future__ import annotations

import sys
import uuid
import argparse
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.db.database import SessionLocal
from src.db.models import Transaction, Alert, Account
from src.agents.orchestrator import InvestigationOrchestrator


def inject_custom_scenario(
    subject_account: str,
    inflow_amount: float,
    outflow_count: int,
    conservation_target: float = 0.95,
    split_minutes: int = 45,
):
    console = Console()
    console.print(Panel.fit(
        f"[bold cyan]🧪 Custom Scenario Injector & Stress Tester[/bold cyan]\n"
        f"Simulating rapid passthrough on [bold magenta]{subject_account}[/bold magenta]:\n"
        f"Inflow: [bold green]Rs {inflow_amount:,.2f}[/bold green] &bull; "
        f"Outflow Targets: [bold red]{outflow_count}[/bold red] &bull; "
        f"Window: [bold yellow]{split_minutes} minutes[/bold yellow]",
        border_style="cyan"
    ))

    with SessionLocal() as db:
        from src.db.models import Customer

        # Check or create customer & account
        acc = db.query(Account).filter(Account.account_id == subject_account).first()
        if not acc:
            cust_id = f"CUST-SIM-{uuid.uuid4().hex[:6]}"
            cust = Customer(
                customer_id=cust_id,
                customer_type="business",
                occupation_or_business_category="merchant",
                expected_activity_category="merchant",
                geographic_region="Mumbai",
            )
            db.add(cust)
            db.commit()

            acc = Account(
                account_id=subject_account,
                customer_id=cust_id,
                account_type="current",
                segment="sme",
                risk_profile="medium",
                status="active",
                is_synthetic_suspicious=True,
                scenario_id="SCENARIO-CUSTOM-SIM",
            )
            db.add(acc)
            db.commit()

        # Inflow transaction
        base_time = datetime(2026, 8, 14, 10, 0, 0)
        source_account = "ACC-SIM-SOURCE"

        src_acc = db.query(Account).filter(Account.account_id == source_account).first()
        if not src_acc:
            src_cust_id = f"CUST-SRC-{uuid.uuid4().hex[:6]}"
            src_cust = Customer(
                customer_id=src_cust_id,
                customer_type="business",
                occupation_or_business_category="corporate",
                expected_activity_category="corporate",
                geographic_region="Delhi",
            )
            db.add(src_cust)
            db.commit()

            src_acc = Account(
                account_id=source_account,
                customer_id=src_cust_id,
                account_type="current",
                segment="corporate",
                status="active",
            )
            db.add(src_acc)
            db.commit()

        inflow_tx = Transaction(
            transaction_id=f"TXN-SIM-IN-{uuid.uuid4().hex[:6].upper()}",
            timestamp=base_time,
            sender_account_id=source_account,
            receiver_account_id=subject_account,
            amount=inflow_amount,
            currency="INR",
            channel="RTGS",
            transaction_type="transfer",
            ground_truth_pattern="synthetic_suspicious_pattern",
        )
        db.add(inflow_tx)

        # Split outflow transactions
        total_outflow = inflow_amount * conservation_target
        per_tx = round(total_outflow / outflow_count, 2)
        interval = split_minutes / max(outflow_count, 1)

        outflows = []
        for i in range(outflow_count):
            dest_acc_id = f"ACC-SIM-MULE-{i+1:03d}"
            if not db.query(Account).filter(Account.account_id == dest_acc_id).first():
                mule_cust_id = f"CUST-MULE-{i+1:03d}"
                mule_cust = Customer(
                    customer_id=mule_cust_id,
                    customer_type="individual",
                    occupation_or_business_category="retail",
                    expected_activity_category="student",
                    geographic_region="Bangalore",
                )
                db.add(mule_cust)
                db.commit()

                dest = Account(
                    account_id=dest_acc_id,
                    customer_id=mule_cust_id,
                    account_type="savings",
                    segment="retail",
                    status="active",
                )
                db.add(dest)
                db.commit()

            t_out = Transaction(
                transaction_id=f"TXN-SIM-OUT-{uuid.uuid4().hex[:6].upper()}",
                timestamp=base_time + timedelta(minutes=int(interval * (i + 1))),
                sender_account_id=subject_account,
                receiver_account_id=dest_acc_id,
                amount=per_tx,
                currency="INR",
                channel="IMPS",
                transaction_type="transfer",
                ground_truth_pattern="synthetic_suspicious_pattern",
            )
            db.add(t_out)
            outflows.append(t_out)

        # Create or update alert
        alert_id = f"ALERT-SIM-{uuid.uuid4().hex[:6].upper()}"
        alert = Alert(
            alert_id=alert_id,
            account_id=subject_account,
            priority_score=95.0,
            risk_band="CRITICAL",
            status="open",
            summary=f"Simulated rapid passthrough of Rs {inflow_amount:,.0f} to {outflow_count} counterparties in {split_minutes} mins.",
            scenario_id="SCENARIO-CUSTOM-SIM",
        )
        db.add(alert)
        db.commit()

        console.print(f"[bold green]✔ Successfully injected 1 credit and {outflow_count} debit transactions into sandbox.[/bold green]")
        console.print(f"[dim]Generated Alert ID: {alert_id}[/dim]")

    # Run Autonomous Investigation on simulated scenario
    console.print(f"\n[bold yellow]Triggering Autonomous Investigation on injected scenario...[/bold yellow]")
    orch = InvestigationOrchestrator(
        case_id=f"CASE-SIM-{uuid.uuid4().hex[:6].upper()}",
        alert_id=alert_id,
        account_id=subject_account,
    )
    result = orch.run()

    table = Table(title="Simulation Investigation Diagnostics", border_style="dim")
    table.add_column("Metric", style="cyan")
    table.add_column("Simulated Value", style="bold")

    table.add_row("Investigation Priority Score", f"{result['priority_score']:.1f} / 100 [{result['risk_band']}]")
    table.add_row("Flow Conservation Signal", f"{result['signals']['flow']:.3f}")
    table.add_row("Temporal Velocity Signal", f"{result['signals']['temporal']:.3f}")
    table.add_row("XGBoost Consensus", f"{result['model_scores'].get('xgboost_score', 0):.3f}")
    table.add_row("Isolation Forest Consensus", f"{result['model_scores'].get('isolation_score', 0):.3f}")
    table.add_row("Autoencoder Consensus", f"{result['model_scores'].get('autoencoder_score', 0):.3f}")
    table.add_row("Findings Produced", str(result["findings_count"]))
    table.add_row("Evidence Items Logged", str(result["evidence_count"]))
    table.add_row("Agent Execution Duration", f"{result['duration_seconds']}s")

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="LaundraLens X Scenario Stress Tester")
    parser.add_argument("--account", default="ACC-CUSTOM-001", help="Target account ID")
    parser.add_argument("--inflow", type=float, default=2500000.0, help="Inflow transfer amount in INR")
    parser.add_argument("--outflow-count", type=int, default=5, help="Number of outgoing transfers")
    parser.add_argument("--conservation", type=float, default=0.96, help="Target conservation fraction (e.g. 0.96)")
    parser.add_argument("--split-minutes", type=int, default=40, help="Total minutes across which outflows occur")

    args = parser.parse_args()
    inject_custom_scenario(
        subject_account=args.account,
        inflow_amount=args.inflow,
        outflow_count=args.outflow_count,
        conservation_target=args.conservation,
        split_minutes=args.split_minutes,
    )


if __name__ == "__main__":
    main()
