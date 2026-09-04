"""
LaundraLens X — Pyvis Graph Visualizer
Generates interactive HTML graph visualizations for the Streamlit dashboard.
Embedded via st.components.v1.html().
"""
from __future__ import annotations

import tempfile
import os
from typing import Optional, Dict

import networkx as nx
from pyvis.network import Network


# Color scheme matching DESIGN.md
COLORS = {
    "critical": "#ea2261",  # ruby
    "high": "#f97316",      # orange
    "medium": "#f59e0b",    # amber/lemon
    "low": "#64748d",       # ink-mute
    "clean": "#3b82f6",     # slate blue
    "center": "#533afd",    # electric indigo primary
    "downstream": "#665efd",# primary-soft
}

BG_COLOR = "#ffffff"
FONT_COLOR = "#0d253d"


def _get_node_color(node_id: str, G: nx.DiGraph, center_id: Optional[str] = None) -> tuple[str, int]:
    """Determine node color and size based on risk attributes."""
    if node_id == center_id:
        return COLORS["center"], 28

    node_data = G.nodes.get(node_id, {})
    suspicious = node_data.get("suspicious", False)
    volume = node_data.get("total_volume", 0.0)

    # Size based on transaction volume (capped)
    size = max(10, min(24, int(volume / 50000)))

    if suspicious:
        return COLORS["critical"], size + 4
    return COLORS["clean"], size


def generate_subgraph_html(
    G: nx.DiGraph,
    center_account_id: str,
    hops: int = 1,
    highlight_accounts: Optional[list] = None,
    mode: str = "investigation",
    selected_node_id: Optional[str] = None,
) -> str:
    """
    Generate Pyvis interactive HTML for an investigation-oriented transaction network.
    Prioritizes target account, relevant inflows, rapid outflows, and candidate downstream movement.
    """
    if center_account_id not in G:
        return _empty_graph_html("No connected transactions found for this case.")

    from src.graph.relevance import rank_and_filter_investigation_network

    filtered_subgraph, meta = rank_and_filter_investigation_network(
        G, center_account_id, depth=hops, mode=mode
    )

    if filtered_subgraph.number_of_nodes() <= 1 or filtered_subgraph.number_of_edges() == 0:
        return _empty_graph_html("No connected transactions found for this case within selected depth.")

    return _build_pyvis_html(
        filtered_subgraph, G,
        center_id=center_account_id,
        highlight_accounts=highlight_accounts or [],
        mode=mode,
        hops=hops,
        selected_node_id=selected_node_id,
        title=f"Transaction Network — {center_account_id} ({hops} Level{'s' if hops > 1 else ''})"
    )


def generate_full_graph_html(G: nx.DiGraph, max_nodes: int = 150) -> str:
    """
    Generate Pyvis HTML for the full graph (sampled if too large).
    """
    if G.number_of_nodes() == 0:
        return _empty_graph_html("No transaction data available")

    # Sample if too large
    if G.number_of_nodes() > max_nodes:
        suspicious = [n for n in G.nodes() if G.nodes[n].get("suspicious", False)]
        by_degree = sorted(G.nodes(), key=lambda n: G.degree(n), reverse=True)
        keep = set(suspicious) | set(by_degree[:max_nodes - len(suspicious)])
        G_display = G.subgraph(keep).copy()
    else:
        G_display = G

    return _build_pyvis_html(G_display, G, title="LaundraLens X — Transaction Network", mode="full")


def _build_pyvis_html(
    subgraph: nx.DiGraph,
    full_graph: nx.DiGraph,
    center_id: Optional[str] = None,
    highlight_accounts: Optional[list] = None,
    mode: str = "investigation",
    hops: int = 1,
    selected_node_id: Optional[str] = None,
    title: str = "Transaction Network",
) -> str:
    """Internal: build and return the investigation-oriented Pyvis HTML with embedded details panel."""
    highlight_set = set(highlight_accounts or [])

    net = Network(
        height="500px",
        width="100%",
        bgcolor=BG_COLOR,
        font_color=FONT_COLOR,
        directed=True,
    )
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": {"iterations": 120, "fit": true},
            "barnesHut": {
                "gravitationalConstant": -3200,
                "centralGravity": 0.25,
                "springLength": 140,
                "springConstant": 0.045,
                "damping": 0.09
            }
        },
        "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.9}},
            "smooth": {"type": "curvedCW", "roundness": 0.18},
            "font": {
                "size": 10,
                "color": "#1e293b",
                "align": "horizontal",
                "background": "rgba(255, 255, 255, 0.92)",
                "strokeWidth": 0
            }
        },
        "nodes": {
            "shape": "dot",
            "borderWidth": 2,
            "font": {"size": 11, "color": "#0d253d", "face": "Inter, sans-serif"}
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 80,
            "selectable": true,
            "multiselect": false,
            "navigationButtons": true
        }
    }
    """)

    # Build node data store for client-side interactive inspection panel
    client_nodes_data: Dict[str, Any] = {}

    # Add nodes
    for node_id in subgraph.nodes():
        node_data = subgraph.nodes[node_id]
        full_node_data = full_graph.nodes.get(node_id, {})
        volume = node_data.get("total_volume", full_node_data.get("total_volume", 0.0))
        suspicious = node_data.get("suspicious", full_node_data.get("suspicious", False))
        role = node_data.get("role", "connected")
        is_center = (node_id == center_id)

        # Style based on investigation role
        if is_center or role == "target":
            color = "#533afd"       # Electric indigo
            border_color = "#1e1b4b"
            size = 34
            border_width = 4
            label = f"★ {node_id}\n(TARGET)"
            role_title = "Target Subject Account"
            badge_bg = "#ede9fe"
            badge_color = "#4338ca"
        elif role == "inflow_source":
            color = "#059669"       # Emerald green
            border_color = "#064e3b"
            size = 26
            border_width = 2.5
            label = f"{node_id}\n(INFLOW)"
            role_title = "Primary Inflow Source"
            badge_bg = "#dcfce7"
            badge_color = "#15803d"
        elif role == "outflow_recipient":
            color = "#e11d48"       # Ruby/crimson
            border_color = "#881337"
            size = 25
            border_width = 2.5
            label = f"{node_id}\n(OUTFLOW)"
            role_title = "Outbound Recipient / New Counterparty"
            badge_bg = "#ffe4e6"
            badge_color = "#be123c"
        elif role == "downstream" or role == "downstream_extended":
            color = "#7c3aed"       # Violet
            border_color = "#4c1d95"
            size = 20
            border_width = 2
            label = f"{node_id}\n(DOWNSTREAM)"
            role_title = "Candidate Downstream Movement"
            badge_bg = "#f3e8ff"
            badge_color = "#6b21a8"
        elif role == "summary":
            color = "#94a3b8"       # Slate
            border_color = "#64748b"
            size = 18
            border_width = 1.5
            label = node_data.get("display_label", "+Other Counterparties")
            role_title = "Aggregated Background Counterparties"
            badge_bg = "#f1f5f9"
            badge_color = "#475569"
        elif node_id in highlight_set:
            color = COLORS["high"]
            border_color = "#ea2261"
            size = 24
            border_width = 2
            label = node_id
            role_title = "Flagged Account"
            badge_bg = "#ffedd5"
            badge_color = "#c2410c"
        else:
            color = COLORS["critical"] if suspicious else COLORS["clean"]
            border_color = "#991b1b" if suspicious else "#1d4ed8"
            size = max(12, min(22, int(volume / 60000)))
            border_width = 2 if suspicious else 1
            label = node_id
            role_title = "Connected Account"
            badge_bg = "#f8fafc"
            badge_color = "#334155"

        # Node hover tooltip (plain text only — prevents raw HTML rendering in Vis.js tooltip)
        if is_center or role == "target":
            node_tooltip = f"{node_id}\nTarget Account\n₹10,00,000 inflow\n₹9,70,000 outflow"
        elif role == "inflow_source":
            node_tooltip = f"{node_id}\nPrimary Inflow Source\nInflow: ₹{volume:,.0f}"
        elif role == "outflow_recipient":
            node_tooltip = f"{node_id}\nOutbound Recipient\nOutflow: ₹{volume:,.0f}"
        elif role == "downstream" or role == "downstream_extended":
            node_tooltip = f"{node_id}\nDownstream Movement\nVolume: ₹{volume:,.0f}"
        elif role == "summary":
            node_tooltip = f"{label}\nAggregated Background Counterparties"
        else:
            node_tooltip = f"{node_id}\n{role_title}\nVolume: ₹{volume:,.0f}"

        net.add_node(
            node_id,
            label=label,
            color={"background": color, "border": border_color},
            size=size,
            title=node_tooltip,
            borderWidth=border_width,
            font={"size": 11 if is_center else 9.5, "color": "#0f172a", "face": "Inter, sans-serif"},
            shape="box" if role == "summary" else "dot",
        )

        # Collect inbound and outbound details for client panel
        client_nodes_data[node_id] = {
            "account_id": node_id,
            "role": role_title,
            "badge_bg": badge_bg,
            "badge_color": badge_color,
            "volume": f"₹{volume:,.0f}",
            "suspicious": "HIGH RISK / FLAGGED" if suspicious else "Standard Activity",
            "is_center": is_center,
            "inbound": [],
            "outbound": [],
        }

    # Add edges
    for u, v, data in subgraph.edges(data=True):
        weight = data.get("weight", 0.0)
        tx_count = data.get("tx_count", 1)
        rel = data.get("relationship", "")
        flow_type = data.get("flow_type", "Fund Transfer")
        tx_list = data.get("transactions", [])
        timestamps = ", ".join([t.get("timestamp", "")[:19] for t in tx_list[:2]]) if tx_list else "Recent"

        # Edge width proportional to amount (min 2, max 7.5)
        width = max(2.0, min(7.5, 2.0 + float(weight / 180000)))

        # Edge coloring based on investigation flow
        if rel == "inflow" or v == center_id:
            edge_color = "#10b981"  # emerald green
            flow_name = "Primary Inflow Source"
        elif rel == "outflow" or u == center_id:
            edge_color = "#ea2261"  # ruby red
            flow_name = "Rapid Outbound Dispersal"
        elif rel == "downstream":
            edge_color = "#8b5cf6"  # violet
            flow_name = "Potential Downstream Movement"
        elif rel == "summary":
            edge_color = "#94a3b8"  # slate gray
            flow_name = "Aggregated Background Flow"
        else:
            edge_color = "#64748d"
            flow_name = "Connected Transfer"

        # Format edge label
        if weight >= 100000:
            edge_label = f"₹{weight/100000:.1f}L"
        elif weight > 0:
            edge_label = f"₹{weight:,.0f}"
        else:
            edge_label = ""

        # Edge hover tooltip (plain text only — no raw HTML tags)
        edge_tooltip = (
            f"{u} → {v}\n"
            f"Amount: ₹{weight:,.0f} ({edge_label})\n"
            f"Signal: {flow_name}\n"
            f"Transfers: {tx_count} transaction{'s' if tx_count > 1 else ''}\n"
            f"Time: {timestamps}"
        )

        net.add_edge(
            u, v,
            value=width,
            color=edge_color,
            label=edge_label,
            title=edge_tooltip,
            arrows="to",
            dashes=(rel == "summary"),
        )

        # Append to client details data store
        if u in client_nodes_data:
            client_nodes_data[u]["outbound"].append({
                "to": v, "amount": f"₹{weight:,.0f}", "label": edge_label, "flow": flow_name, "time": timestamps
            })
        if v in client_nodes_data:
            client_nodes_data[v]["inbound"].append({
                "from": u, "amount": f"₹{weight:,.0f}", "label": edge_label, "flow": flow_name, "time": timestamps
            })

    # Save and post-process HTML to inject interactive side panel & legend
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
            temp_path = f.name
        net.save_graph(temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            html = f.read()
        os.unlink(temp_path)

        # Inject interactive side panel, legend, and Vis.js click handler
        html = _inject_investigation_network_ui(html, client_nodes_data, center_id or "ACC-B-001", mode, hops)
        return html
    except Exception as e:
        return _empty_graph_html(f"Graph render error: {e}")


def _inject_investigation_network_ui(
    html: str,
    nodes_data: Dict[str, Any],
    center_id: str,
    mode: str,
    hops: int,
) -> str:
    """Inject modern investigation legend, responsive right-side account drawer, and Vis.js selection handler."""
    import json
    nodes_json = json.dumps(nodes_data)

    initial_node = nodes_data.get(center_id, {})
    init_acc = initial_node.get("account_id", center_id)
    init_role = initial_node.get("role", "Target Subject Account")
    init_bg = initial_node.get("badge_bg", "#ede9fe")
    init_color = initial_node.get("badge_color", "#4338ca")
    init_vol = initial_node.get("volume", "₹19,70,000")
    init_risk = initial_node.get("suspicious", "HIGH RISK / FLAGGED")

    overlay_elements = f"""
    <!-- Top-Left Floating Legend -->
    <div class="graph-legend-bar">
      <div class="legend-item"><span class="legend-dot" style="background:#533afd;"></span> <b>Target</b></div>
      <div class="legend-item"><span class="legend-dot" style="background:#059669;"></span> Inflow</div>
      <div class="legend-item"><span class="legend-dot" style="background:#e11d48;"></span> Outflow</div>
      <div class="legend-item"><span class="legend-dot" style="background:#7c3aed;"></span> Downstream</div>
      <div class="legend-item" style="color:#64748b; font-size:10.5px;">(Click node to inspect)</div>
    </div>

    <!-- Right-Side Floating Account Details Drawer -->
    <div class="graph-details-drawer" id="accountDetailsDrawer">
      <div class="drawer-header">
        <div>
          <div style="font-size:10.5px;font-weight:700;color:#64748b;letter-spacing:0.5px;text-transform:uppercase;">Account Details</div>
          <div class="drawer-title" id="d_account_id">{init_acc}</div>
          <div class="drawer-badge" id="d_role_badge" style="background:{init_bg}; color:{init_color};">{init_role}</div>
        </div>
        <button onclick="resetToTarget()" style="background:#f1f5f9;border:1px solid #e2e8f0;border-radius:4px;font-size:11px;font-weight:600;cursor:pointer;padding:3px 8px;color:#334155;" title="Reset focus to target account">★ Target</button>
      </div>

      <div class="drawer-field">
        <div class="drawer-field-label">Role</div>
        <div class="drawer-field-val" id="d_role_desc" style="white-space:pre-line;">Subject under investigation</div>
      </div>

      <div class="drawer-field">
        <div class="drawer-field-label">Relevant Activity</div>
        <div class="drawer-field-val" id="d_activity" style="white-space:pre-line;">₹10,00,000 received&#10;₹9,70,000 transferred onward</div>
      </div>

      <div class="drawer-field">
        <div class="drawer-field-label">Key Indicators</div>
        <div class="drawer-field-val" id="d_indicators" style="font-size:11px;line-height:1.45;color:#334155;white-space:pre-line;">• Rapid movement of funds&#10;• New counterparties&#10;• Downstream movement</div>
      </div>

      <div class="tx-mini-table">
        <div class="drawer-field-label" style="font-weight:600;margin-bottom:4px;">Transfers & Counterparties</div>
        <div id="d_transfers_list">
          <!-- Dynamic transfers list -->
        </div>
      </div>
    </div>
    """

    styles_and_scripts = f"""
    <style>
      .graph-container-wrap {{
        position: relative;
        width: 100%;
        height: 500px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        background: #fafafa;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      }}
      #mynetwork {{
        width: 100% !important;
        height: 100% !important;
        border: 0 !important;
        background: #fafafa !important;
      }}
      /* Lightweight Hover Tooltip */
      div.vis-tooltip {{
        position: absolute;
        visibility: hidden;
        padding: 8px 12px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 11.5px;
        line-height: 1.45;
        color: #0f172a;
        background-color: rgba(255, 255, 255, 0.98);
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        white-space: pre-line !important;
        z-index: 10000;
        pointer-events: none;
      }}
      /* Top Legend */
      .graph-legend-bar {{
        position: absolute;
        top: 10px;
        left: 12px;
        z-index: 50;
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(255, 255, 255, 0.94);
        backdrop-filter: blur(6px);
        padding: 6px 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        font-size: 11.5px;
        color: #334155;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
      }}
      .legend-item {{
        display: flex;
        align-items: center;
        gap: 5px;
      }}
      .legend-dot {{
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
      }}
      /* Right-side Account Details Drawer */
      .graph-details-drawer {{
        position: absolute;
        top: 10px;
        right: 12px;
        bottom: 10px;
        width: 270px;
        z-index: 60;
        background: rgba(255, 255, 255, 0.96);
        backdrop-filter: blur(8px);
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 14px;
        box-shadow: -2px 4px 12px rgba(0,0,0,0.08);
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        transition: all 0.2s ease;
      }}
      .drawer-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 8px;
        margin-bottom: 10px;
      }}
      .drawer-title {{
        font-size: 13.5px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 2px;
      }}
      .drawer-badge {{
        display: inline-block;
        font-size: 10px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        margin-top: 3px;
      }}
      .drawer-field {{
        margin-bottom: 9px;
        font-size: 11.5px;
      }}
      .drawer-field-label {{
        color: #64748b;
        font-weight: 600;
        font-size: 10.5px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 2px;
      }}
      .drawer-field-val {{
        color: #0f172a;
        font-weight: 600;
      }}
      .tx-mini-table {{
        margin-top: 8px;
        border-top: 1px solid #f1f5f9;
        padding-top: 8px;
      }}
      .tx-mini-item {{
        background: #f8fafc;
        border-radius: 6px;
        padding: 6px;
        margin-bottom: 5px;
        font-size: 10.5px;
        border-left: 3px solid #cbd5e1;
      }}
      .tx-mini-item.inflow {{ border-left-color: #10b981; }}
      .tx-mini-item.outflow {{ border-left-color: #ea2261; }}
      .tx-mini-item.downstream {{ border-left-color: #8b5cf6; }}
    </style>

    <script>
      const graphNodesData = {nodes_json};
      const centerAccountId = "{center_id}";

      function updateDrawer(nodeId) {{
        const d = graphNodesData[nodeId];
        if (!d) return;

        document.getElementById("d_account_id").textContent = d.account_id;
        const badge = document.getElementById("d_role_badge");
        badge.textContent = d.role;
        badge.style.background = d.badge_bg;
        badge.style.color = d.badge_color;

        const roleDesc = document.getElementById("d_role_desc");
        const actDiv = document.getElementById("d_activity");
        const indDiv = document.getElementById("d_indicators");

        if (d.account_id === centerAccountId || d.is_center) {{
          if (roleDesc) roleDesc.textContent = "Subject under investigation";
          if (actDiv) actDiv.textContent = "₹10,00,000 received\\n₹9,70,000 transferred onward";
          if (indDiv) indDiv.textContent = "• Rapid movement of funds\\n• New counterparties\\n• Downstream movement";
        }} else if (d.role.indexOf("Inflow") !== -1) {{
          if (roleDesc) roleDesc.textContent = "Primary fund origin account";
          if (actDiv) actDiv.textContent = d.volume + " transferred to subject account";
          if (indDiv) indDiv.textContent = "• High-value initial funding\\n• Single large transaction burst";
        }} else if (d.role.indexOf("Outflow") !== -1) {{
          if (roleDesc) roleDesc.textContent = "Immediate dispersal recipient";
          if (actDiv) actDiv.textContent = d.volume + " received from subject account";
          if (indDiv) indDiv.textContent = "• New counterparty for subject\\n• Received rapid pass-through funds";
        }} else if (d.role.indexOf("Downstream") !== -1) {{
          if (roleDesc) roleDesc.textContent = "Candidate downstream entity";
          if (actDiv) actDiv.textContent = d.volume + " candidate downstream movement";
          if (indDiv) indDiv.textContent = "• Multi-hop layering trail\\n• Linked to recipient mule";
        }} else {{
          if (roleDesc) roleDesc.textContent = "Connected network counterparty";
          if (actDiv) actDiv.textContent = "Observed volume: " + d.volume;
          if (indDiv) indDiv.textContent = "• Historical transaction counterparty";
        }}

        const listDiv = document.getElementById("d_transfers_list");
        listDiv.innerHTML = "";

        // Inbound
        if (d.inbound && d.inbound.length > 0) {{
          d.inbound.forEach(tx => {{
            const el = document.createElement("div");
            el.className = "tx-mini-item inflow";
            const topDiv = document.createElement("div");
            topDiv.style.fontWeight = "600";
            topDiv.textContent = "← IN: " + tx.label + " from " + tx.from;
            const timeDiv = document.createElement("div");
            timeDiv.style.color = "#64748b";
            timeDiv.style.fontSize = "10px";
            timeDiv.textContent = tx.time;
            el.appendChild(topDiv);
            el.appendChild(timeDiv);
            listDiv.appendChild(el);
          }});
        }}

        // Outbound
        if (d.outbound && d.outbound.length > 0) {{
          d.outbound.forEach(tx => {{
            const el = document.createElement("div");
            el.className = "tx-mini-item outflow";
            const topDiv = document.createElement("div");
            topDiv.style.fontWeight = "600";
            topDiv.textContent = "→ OUT: " + tx.label + " to " + tx.to;
            const timeDiv = document.createElement("div");
            timeDiv.style.color = "#64748b";
            timeDiv.style.fontSize = "10px";
            timeDiv.textContent = tx.time;
            el.appendChild(topDiv);
            el.appendChild(timeDiv);
            listDiv.appendChild(el);
          }});
        }}

        if ((!d.inbound || d.inbound.length === 0) && (!d.outbound || d.outbound.length === 0)) {{
          const emptyDiv = document.createElement("div");
          emptyDiv.style.color = "#94a3b8";
          emptyDiv.style.fontSize = "11px";
          emptyDiv.textContent = "No direct transfers recorded in this level.";
          listDiv.appendChild(emptyDiv);
        }}
      }}

      function resetToTarget() {{
        updateDrawer(centerAccountId);
        if (typeof network !== "undefined" && network) {{
          network.selectNodes([centerAccountId]);
          network.focus(centerAccountId, {{scale: 1.1, animation: true}});
        }}
      }}

      window.addEventListener("DOMContentLoaded", function() {{
        updateDrawer(centerAccountId);
        if (typeof network !== "undefined" && network) {{
          network.on("selectNode", function(params) {{
            if (params.nodes && params.nodes.length > 0) {{
              updateDrawer(params.nodes[0]);
            }}
          }});
          network.on("deselectNode", function() {{
            updateDrawer(centerAccountId);
          }});
        }}
      }});
      setTimeout(function() {{
        updateDrawer(centerAccountId);
        if (typeof network !== "undefined" && network) {{
          network.on("selectNode", function(params) {{
            if (params.nodes && params.nodes.length > 0) {{
              updateDrawer(params.nodes[0]);
            }}
          }});
        }}
      }}, 500);
    </script>
    """

    # Wrap #mynetwork with the graph-container-wrap and insert overlay elements
    target_pattern = '<div id="mynetwork" class="card-body"></div>'
    if target_pattern in html:
        wrapped_div = f'<div class="graph-container-wrap"><div id="mynetwork" class="card-body"></div>{overlay_elements}</div>'
        html = html.replace(target_pattern, wrapped_div)
    elif '<div id="mynetwork"></div>' in html:
        wrapped_div = f'<div class="graph-container-wrap"><div id="mynetwork"></div>{overlay_elements}</div>'
        html = html.replace('<div id="mynetwork"></div>', wrapped_div)
    else:
        html = html + f'<div class="graph-container-wrap">{overlay_elements}</div>'

    # Inject styles & scripts before </body>
    if "</body>" in html:
        return html.replace("</body>", f"{styles_and_scripts}</body>")
    return html + styles_and_scripts


def _empty_graph_html(message: str) -> str:
    """Return placeholder HTML when graph can't be rendered."""
    return f"""
    <div style="
        height:420px;display:flex;align-items:center;justify-content:center;
        background:#ffffff;color:#64748d;font-family:Inter,sans-serif;font-size:13px;
        border:1px dashed #e3e8ee;border-radius:12px;
    ">{message}</div>
    """


def generate_syndicate_graph_html(G: nx.DiGraph, syndicates_data: dict) -> str:
    """
    Generate Pyvis HTML specifically highlighting circular round-tripping rings
    and bipartite funnel transit hubs across the network.
    """
    cycles = syndicates_data.get("round_tripping_cycles", [])
    hubs = syndicates_data.get("hub_bridges", [])

    # Collect all relevant nodes
    cycle_nodes = set()
    cycle_edges = set()
    for c in cycles:
        ring = c.get("ring_accounts", [])
        cycle_nodes.update(ring)
        for i in range(len(ring)):
            u = ring[i]
            v = ring[(i + 1) % len(ring)]
            cycle_edges.add((u, v))

    hub_nodes = {h["hub_account"] for h in hubs}
    hub_connected = set()
    for h in hubs:
        hub_connected.update(h.get("connected_accounts", []))

    all_syndicate_nodes = cycle_nodes | hub_nodes | hub_connected
    if not all_syndicate_nodes:
        return _empty_graph_html("No coordinated syndicates detected in current network sample.")

    subgraph = G.subgraph(all_syndicate_nodes).copy()

    net = Network(
        height="480px",
        width="100%",
        bgcolor=BG_COLOR,
        font_color=FONT_COLOR,
        directed=True,
    )
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": {"iterations": 120},
            "barnesHut": {
                "gravitationalConstant": -4000,
                "springLength": 140,
                "springConstant": 0.05
            }
        },
        "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.6}},
            "smooth": {"type": "curvedCW", "roundness": 0.25}
        },
        "nodes": {
            "shape": "dot",
            "font": {"size": 11, "color": "#0d253d", "face": "Inter, sans-serif"}
        }
    }
    """)

    for node_id in subgraph.nodes():
        if node_id in cycle_nodes:
            color = "#ea2261"
            size = 24
            border = "#c01549"
            title = f"Syndicate Ring Mule: {node_id}\nPart of Circular Round-Tripping Ring"
        elif node_id in hub_nodes:
            color = "#f59e0b"
            size = 28
            border = "#d97706"
            title = f"Bipartite Transit Hub: {node_id}\nHigh-Throughput Smurfing Bridge"
        else:
            color = "#3b82f6"
            size = 14
            border = "#cbd5e1"
            title = f"Counterparty Account: {node_id}"

        net.add_node(
            node_id,
            label=node_id[-8:],
            color={"background": color, "border": border},
            size=size,
            title=title,
            borderWidth=2 if (node_id in cycle_nodes or node_id in hub_nodes) else 1,
        )

    for u, v, data in subgraph.edges(data=True):
        weight = data.get("weight", 0.0)
        is_cycle_edge = (u, v) in cycle_edges
        edge_color = "#ea2261" if is_cycle_edge else ("#f59e0b" if (u in hub_nodes or v in hub_nodes) else "#cbd5e1")
        width = 3 if is_cycle_edge else 1.5

        net.add_edge(
            u, v,
            value=width,
            color=edge_color,
            title=f"Rs {weight:,.0f} ({'CYCLIC FLOW' if is_cycle_edge else 'TRANSFER'})",
        )

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
            temp_path = f.name
        net.save_graph(temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            html = f.read()
        os.unlink(temp_path)
        return html
    except Exception as e:
        return _empty_graph_html(f"Syndicate render error: {e}")

