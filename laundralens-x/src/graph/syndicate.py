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

        # 1. Detect Round-Tripping Cycles (Directed Simple Cycles)
        try:
            # Find simple cycles of length between 3 and max_cycle_length
            all_cycles = list(nx.simple_cycles(G))
            valid_cycles = [c for c in all_cycles if 3 <= len(c) <= max_cycle_length]

            for cycle in valid_cycles[:10]:
                cycle_volume = 0.0
                edges_info = []
                for i in range(len(cycle)):
                    u = cycle[i]
                    v = cycle[(i + 1) % len(cycle)]
                    if G.has_edge(u, v):
                        w = G[u][v].get("weight", 0.0)
                        cycle_volume += w
                        edges_info.append({"from": u, "to": v, "amount": round(w, 2)})

                results["round_tripping_cycles"].append({
                    "ring_accounts": cycle,
                    "length": len(cycle),
                    "cycle_volume": round(cycle_volume, 2),
                    "edges": edges_info,
                    "typology": "circular_layering_cycle",
                })
                results["total_ring_exposure_inr"] += cycle_volume
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
