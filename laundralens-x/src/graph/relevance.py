"""
LaundraLens X — Graph Relevance & Filtering Layer
Filters and ranks full transaction graphs for AML investigation workflows.
Prevents unreadable hairballs by prioritizing alert-relevant paths:
1. Target account (at center)
2. Relevant inflow sources (fund origins)
3. Relevant outflow recipients (rapid dispersals, new counterparties)
4. Candidate downstream movement
5. Summarizing excess background counterparties
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import networkx as nx


def rank_and_filter_investigation_network(
    G: nx.DiGraph,
    target_account_id: str,
    depth: int = 1,
    mode: str = "investigation",
    max_downstream_per_node: int = 4,
    min_amount_threshold: float = 0.0,
) -> Tuple[nx.DiGraph, Dict[str, Any]]:
    """
    Extract a prioritized, investigation-oriented subgraph.

    Modes:
    - 'investigation': Filtered, focused on alert relevance, fund flows, and candidate downstream accounts.
                       Excess background counterparties are aggregated into summary nodes.
    - 'full': Standard undirected ego-network expansion up to the given depth radius.

    Returns:
        (filtered_subgraph, metadata_dict)
    """
    if target_account_id not in G:
        return nx.DiGraph(), {"target_account": target_account_id, "node_count": 0, "edge_count": 0}

    # If full network mode requested, return standard ego-graph
    if mode == "full":
        ego = nx.ego_graph(G, target_account_id, radius=depth, undirected=True)
        # Assign default roles
        for n in ego.nodes():
            if n == target_account_id:
                ego.nodes[n]["role"] = "target"
            else:
                ego.nodes[n]["role"] = "connected"
        return ego, {
            "target_account": target_account_id,
            "mode": "full",
            "depth": depth,
            "node_count": ego.number_of_nodes(),
            "edge_count": ego.number_of_edges(),
        }

    # Investigation Mode: Focused alert-relevant extraction
    H = nx.DiGraph()

    # Add Target Node
    target_data = dict(G.nodes[target_account_id])
    target_data["role"] = "target"
    target_data["display_label"] = f"★ {target_account_id} (TARGET)"
    H.add_node(target_account_id, **target_data)

    # 1. Immediate Direct Counterparties (Level 1)
    in_edges = list(G.in_edges(target_account_id, data=True))
    out_edges = list(G.out_edges(target_account_id, data=True))

    # Sort in_edges by total transfer weight descending
    in_edges = sorted(in_edges, key=lambda e: e[2].get("weight", 0.0), reverse=True)
    # Sort out_edges by total transfer weight descending
    out_edges = sorted(out_edges, key=lambda e: e[2].get("weight", 0.0), reverse=True)

    # Inflow sources
    for u, v, d in in_edges:
        if d.get("weight", 0.0) < min_amount_threshold:
            continue
        u_data = dict(G.nodes.get(u, {}))
        u_data["role"] = "inflow_source"
        u_data["display_label"] = f"{u} (INFLOW)"
        H.add_node(u, **u_data)
        
        edge_data = dict(d)
        edge_data["relationship"] = "inflow"
        edge_data["flow_type"] = "Primary Fund Inflow"
        H.add_edge(u, v, **edge_data)

    # Outflow recipients (dispersal / mules / new counterparties)
    outflow_recipients = []
    for u, v, d in out_edges:
        if d.get("weight", 0.0) < min_amount_threshold:
            continue
        v_data = dict(G.nodes.get(v, {}))
        v_data["role"] = "outflow_recipient"
        v_data["display_label"] = f"{v} (OUTFLOW)"
        H.add_node(v, **v_data)
        
        edge_data = dict(d)
        edge_data["relationship"] = "outflow"
        edge_data["flow_type"] = "Rapid Outbound Dispersal"
        H.add_edge(u, v, **edge_data)
        outflow_recipients.append(v)

    # 2. Progressive Downstream Movement (Level 2 & Level 3)
    if depth >= 2:
        for recipient in outflow_recipients:
            recipient_out = list(G.out_edges(recipient, data=True))
            if not recipient_out:
                continue

            # Prioritize downstream edges by amount weight and suspicious flags
            def _downstream_priority(e):
                target_node_suspicious = G.nodes.get(e[1], {}).get("suspicious", False)
                weight = e[2].get("weight", 0.0)
                # Boost suspicious downstream nodes
                return (1 if target_node_suspicious else 0, weight)

            recipient_out = sorted(recipient_out, key=_downstream_priority, reverse=True)

            # Top candidate downstream movements
            top_downstream = recipient_out[:max_downstream_per_node]
            excess_downstream = recipient_out[max_downstream_per_node:]

            for r_u, r_v, r_d in top_downstream:
                if r_v == target_account_id:
                    continue  # Skip circular loops back to center for now or let them display
                r_v_data = dict(G.nodes.get(r_v, {}))
                r_v_data["role"] = "downstream"
                r_v_data["display_label"] = f"{r_v} (DOWNSTREAM)"
                H.add_node(r_v, **r_v_data)

                edge_data = dict(r_d)
                edge_data["relationship"] = "downstream"
                edge_data["flow_type"] = "Potential Downstream Movement"
                H.add_edge(r_u, r_v, **edge_data)

                # Level 3: Extend further downstream from candidate recipients
                if depth >= 3:
                    level3_out = sorted(
                        list(G.out_edges(r_v, data=True)),
                        key=lambda e: e[2].get("weight", 0.0),
                        reverse=True
                    )[:2]
                    for l3_u, l3_v, l3_d in level3_out:
                        if l3_v in [target_account_id, recipient]:
                            continue
                        l3_v_data = dict(G.nodes.get(l3_v, {}))
                        l3_v_data["role"] = "downstream_extended"
                        l3_v_data["display_label"] = f"{l3_v}"
                        H.add_node(l3_v, **l3_v_data)

                        l3_edge_data = dict(l3_d)
                        l3_edge_data["relationship"] = "downstream"
                        l3_edge_data["flow_type"] = "Extended Downstream Movement"
                        H.add_edge(l3_u, l3_v, **l3_edge_data)

            # Summarize remaining excess counterparties
            if excess_downstream:
                excess_count = len(excess_downstream)
                excess_sum = sum(e[2].get("weight", 0.0) for e in excess_downstream)
                summary_node_id = f"SUMMARY-{recipient}"
                H.add_node(
                    summary_node_id,
                    role="summary",
                    display_label=f"+{excess_count} other counterparties",
                    total_volume=excess_sum,
                    counterparty_count=excess_count,
                    parent_account=recipient,
                    suspicious=False,
                )
                H.add_edge(
                    recipient,
                    summary_node_id,
                    weight=excess_sum,
                    tx_count=excess_count,
                    relationship="summary",
                    flow_type=f"{excess_count} background transfers (₹{excess_sum/100000:.1f}L)",
                    transactions=[],
                )

    metadata = {
        "target_account": target_account_id,
        "mode": mode,
        "depth": depth,
        "node_count": H.number_of_nodes(),
        "edge_count": H.number_of_edges(),
        "inflow_sources_count": len(in_edges),
        "outflow_recipients_count": len(outflow_recipients),
    }

    return H, metadata
