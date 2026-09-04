import sys
sys.path.insert(0, ".")
from src.db.database import SessionLocal
from src.api.routes.graph import _get_or_build_graph
import networkx as nx

db = SessionLocal()
G = _get_or_build_graph(db)

def filter_investigation_network(G: nx.DiGraph, target_id: str, depth: int = 1, mode: str = "investigation"):
    if mode == "full":
        return nx.ego_graph(G, target_id, radius=depth, undirected=True)
    
    # Investigation mode: focus on target, relevant inflows, relevant outflows, downstream movement
    H = nx.DiGraph()
    if target_id not in G:
        return H
    
    H.add_node(target_id, **G.nodes[target_id], role="target")
    
    # 1. Level 1: Inflows & Outflows of target
    in_edges = list(G.in_edges(target_id, data=True))
    out_edges = list(G.out_edges(target_id, data=True))
    
    # Sort by weight / recency
    in_edges = sorted(in_edges, key=lambda e: e[2].get("weight", 0.0), reverse=True)
    out_edges = sorted(out_edges, key=lambda e: e[2].get("weight", 0.0), reverse=True)
    
    for u, v, d in in_edges:
        H.add_node(u, **G.nodes[u], role="inflow_source")
        H.add_edge(u, v, **d, relationship="inflow")
        
    for u, v, d in out_edges:
        H.add_node(v, **G.nodes[v], role="outflow_recipient")
        H.add_edge(u, v, **d, relationship="outflow")
        
    # Level 2+: downstream from outflow recipients and upstream from inflow sources
    if depth >= 2:
        for recipient in [v for _, v, _ in out_edges]:
            recipient_out = sorted(list(G.out_edges(recipient, data=True)), key=lambda e: e[2].get("weight", 0.0), reverse=True)
            # Pick top candidate downstream transfers (e.g. top 3 or suspicious)
            top_downstream = recipient_out[:3]
            for r_u, r_v, r_d in top_downstream:
                H.add_node(r_v, **G.nodes.get(r_v, {}), role="downstream")
                H.add_edge(r_u, r_v, **r_d, relationship="downstream")
            if len(recipient_out) > 3:
                # Add summary node
                summary_node = f"other_{recipient}"
                H.add_node(summary_node, role="summary", label=f"+{len(recipient_out)-3} counterparties", total_volume=0.0)
                H.add_edge(recipient, summary_node, weight=sum(e[2].get("weight", 0) for e in recipient_out[3:]), tx_count=len(recipient_out)-3, relationship="summary")
                
    return H

H1 = filter_investigation_network(G, 'ACC-B-001', depth=1)
print(f"Investigation Level 1: nodes={H1.number_of_nodes()}, edges={H1.number_of_edges()}")
for u, v, d in H1.edges(data=True):
    print(f"  {u} -> {v} [INR {d.get('weight', 0):,.0f}] ({d.get('relationship')})")

H2 = filter_investigation_network(G, 'ACC-B-001', depth=2)
print(f"\nInvestigation Level 2: nodes={H2.number_of_nodes()}, edges={H2.number_of_edges()}")
