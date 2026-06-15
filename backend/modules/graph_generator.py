"""
Graph Generator Module.
Generates D3.js-compatible JSON for dependency visualization.
"""

import networkx as nx
from database import get_connection


def generate_graph(project_id: int) -> dict:
    """Generate D3-compatible graph data from project dependencies."""
    conn = get_connection()
    deps = conn.execute("SELECT * FROM dependencies WHERE project_id = ?", (project_id,)).fetchall()
    files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
    smells = conn.execute("SELECT * FROM code_smells WHERE project_id = ?", (project_id,)).fetchall()
    conn.close()
    
    dep_list = [dict(d) for d in deps]
    file_list = [dict(f) for f in files]
    smell_list = [dict(s) for s in smells]
    
    # Build NetworkX graph for analysis
    G = nx.DiGraph()
    
    for f in file_list:
        G.add_node(f["file_path"], type="file", language=f.get("language", ""), loc=f.get("loc", 0))
    
    for d in dep_list:
        G.add_node(d["source"], type="source")
        G.add_node(d["target"], type="target")
        G.add_edge(d["source"], d["target"], dep_type=d["type"])
    
    # Detect circular dependencies
    circular_nodes = set()
    try:
        for cycle in nx.simple_cycles(G):
            for node in cycle:
                circular_nodes.add(node)
    except Exception:
        pass
    
    # Create smell map for node coloring
    smell_map = {}
    for s in smell_list:
        fname = s["file_name"]
        if fname not in smell_map:
            smell_map[fname] = {"count": 0, "max_severity": "low"}
        smell_map[fname]["count"] += 1
        sev_order = {"low": 0, "medium": 1, "high": 2}
        if sev_order.get(s["severity"], 0) > sev_order.get(smell_map[fname]["max_severity"], 0):
            smell_map[fname]["max_severity"] = s["severity"]
    
    # Compute node metrics
    nodes = []
    for node in G.nodes():
        in_deg = G.in_degree(node)
        out_deg = G.out_degree(node)
        
        # Determine node group by type
        node_data = G.nodes[node]
        group = _determine_group(node, node_data)
        
        # Node size based on connections
        size = max(5, min(30, (in_deg + out_deg) * 3 + 5))
        
        # Smell info
        base_name = node.split("/")[-1] if "/" in node else node
        smell_info = smell_map.get(base_name, {"count": 0, "max_severity": "low"})
        
        nodes.append({
            "id": node,
            "label": base_name,
            "group": group,
            "size": size,
            "in_degree": in_deg,
            "out_degree": out_deg,
            "is_circular": node in circular_nodes,
            "smell_count": smell_info["count"],
            "severity": smell_info["max_severity"],
            "language": node_data.get("language", ""),
            "loc": node_data.get("loc", 0)
        })
    
    # Create links
    links = []
    for u, v, data in G.edges(data=True):
        is_circular = u in circular_nodes and v in circular_nodes
        links.append({
            "source": u,
            "target": v,
            "type": data.get("dep_type", "module"),
            "is_circular": is_circular
        })
    
    # Compute graph metrics
    metrics = {
        "total_nodes": len(nodes),
        "total_edges": len(links),
        "circular_count": len(circular_nodes),
        "avg_degree": round(sum(n["in_degree"] + n["out_degree"] for n in nodes) / max(len(nodes), 1), 2),
        "most_connected": sorted(nodes, key=lambda n: n["in_degree"] + n["out_degree"], reverse=True)[:5]
    }
    
    return {
        "nodes": nodes,
        "links": links,
        "metrics": metrics,
        "circular_nodes": list(circular_nodes)
    }


def _determine_group(node_id: str, node_data: dict) -> int:
    """Determine visual group for a node."""
    lang = node_data.get("language", "")
    if lang == "python":
        return 1
    elif lang in ("javascript", "typescript"):
        return 2
    elif lang == "java":
        return 3
    elif "::" in node_id:  # Function-level
        return 4
    else:
        return 5
