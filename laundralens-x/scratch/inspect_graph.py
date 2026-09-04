import sys
sys.path.insert(0, ".")
from src.db.database import SessionLocal
from src.api.routes.graph import _get_or_build_graph
import networkx as nx

db = SessionLocal()
G = _get_or_build_graph(db)
ego1 = nx.ego_graph(G, 'ACC-B-001', radius=1, undirected=True)
print('Hops 1 Nodes:', list(ego1.nodes()))
for u, v, d in ego1.edges(data=True):
    print(f"  {u} -> {v}: weight={d.get('weight')}, tx_count={d.get('tx_count')}, txs={d.get('transactions')}")

print('\nHops 2 stats:')
ego2 = nx.ego_graph(G, 'ACC-B-001', radius=2, undirected=True)
print(f'Hops 2: {ego2.number_of_nodes()} nodes, {ego2.number_of_edges()} edges')

# Let's check downstream of ACC-C-001, ACC-D-001, ACC-E-001, ACC-F-001
for mule in ['ACC-C-001', 'ACC-D-001', 'ACC-E-001', 'ACC-F-001']:
    out_edges = list(G.out_edges(mule, data=True))
    print(f'{mule} out_edges count: {len(out_edges)}')
    for u, v, d in out_edges[:3]:
        print(f'    {u} -> {v}: weight={d.get("weight")}, txs={d.get("transactions")}')
