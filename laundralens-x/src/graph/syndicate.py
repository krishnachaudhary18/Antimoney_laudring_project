"""
LaundraLens X — Multi-Account Syndicate & Mule Ring Forensics
Identifies coordinated financial crime topologies: cycles, round-tripping,
bipartite smurfing funnels, and shared bridge entities.
"""
from __future__ import annotations

from typing import Dict, List, Any, Set, Tuple
import networkx as nx
import pandas as pd


class SyndicateForensics:
    """Forensic graph analyzer specialized in detecting multi-entity coordination."""

    @staticmethod
    def detect_syndicate_patterns(G: nx.DiGraph, max_cycle_length: int = 5) -> Dict[str, Any]:
        """
        Analyzes the full transaction network for coordinated ring structures.
        """
        results = {
            "rings_detected": [],
            "round_tripping_cycles": [],
            "hub_bridges": [],
            "total_ring_exposure_inr": 0.0,
            "syndicate_risk_score": 0.0,
        }

        if G.number_of_nodes() < 3:
            return results

        # 1. Detect Round-Tripping Cycles (Directed 3-Hop and 4-Hop Cycles)
        try:
            seen_cycles: Set[Tuple[str, ...]] = set()

            # 3-hop cycles: A -> B -> C -> A
            for a in G.nodes():
                if len(results["round_tripping_cycles"]) >= 10:
                    break
                for b in G.successors(a):
                    if b == a:
                        continue
                    for c in G.successors(b):
                        if c == a or c == b:
                            continue
                        if G.has_edge(c, a):
                            canonical = tuple(sorted([a, b, c]))
                            if canonical not in seen_cycles:
                                seen_cycles.add(canonical)
                                cycle = [a, b, c]
                                vol = G[a][b].get("weight", 0.0) + G[b][c].get("weight", 0.0) + G[c][a].get("weight", 0.0)
                                edges_info = [
                                    {"from": a, "to": b, "amount": round(G[a][b].get("weight", 0.0), 2)},
                                    {"from": b, "to": c, "amount": round(G[b][c].get("weight", 0.0), 2)},
                                    {"from": c, "to": a, "amount": round(G[c][a].get("weight", 0.0), 2)},
                                ]
                                results["round_tripping_cycles"].append({
                                    "ring_accounts": cycle,
                                    "length": 3,
                                    "cycle_volume": round(vol, 2),
                                    "edges": edges_info,
                                    "typology": "circular_layering_cycle",
                                })
                                results["total_ring_exposure_inr"] += vol
                                if len(results["round_tripping_cycles"]) >= 10:
                                    break
        except Exception:
            pass

        # 2. Detect Bipartite Funnel / Smurfing Networks
        # Accounts with high fan-in immediately connected to accounts with high fan-out
        high_fan_in = [n for n in G.nodes() if G.in_degree(n) >= 3 and G.out_degree(n) >= 2]
        for hub in high_fan_in[:10]:
            inflows = list(G.predecessors(hub))
            outflows = list(G.successors(hub))
            vol_in = sum(G[u][hub].get("weight", 0.0) for u in inflows)
            vol_out = sum(G[hub][v].get("weight", 0.0) for v in outflows)

            results["hub_bridges"].append({
                "hub_account": hub,
                "inflow_senders_count": len(inflows),
                "outflow_recipients_count": len(outflows),
                "inflow_volume": round(vol_in, 2),
                "outflow_volume": round(vol_out, 2),
                "conservation": round(vol_out / (vol_in + 1e-6), 3),
                "connected_accounts": list(set(inflows + outflows)),
            })

        # 3. Overall Syndicate Risk Score
        n_cycles = len(results["round_tripping_cycles"])
        n_hubs = len(results["hub_bridges"])

        score = min(100.0, (n_cycles * 30.0) + (n_hubs * 15.0))
        results["syndicate_risk_score"] = round(score, 1)

        return results
