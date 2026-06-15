"""
Circular Dependency Resolver (Innovative - Viva).
Detects circular calls and suggests separation strategy.
"""

import networkx as nx
from database import get_connection


def resolve_circular(project_id: int) -> dict:
    """Detect and suggest resolutions for circular dependencies."""
    conn = get_connection()
    deps = conn.execute("SELECT * FROM dependencies WHERE project_id = ?", (project_id,)).fetchall()
    files = conn.execute("SELECT file_path, file_name FROM files WHERE project_id = ?", (project_id,)).fetchall()
    conn.close()
    
    dep_list = [dict(d) for d in deps]
    
    # Build directed graph
    G = nx.DiGraph()
    for d in dep_list:
        G.add_edge(d["source"], d["target"])
    
    # Find all cycles
    cycles = []
    try:
        for cycle in nx.simple_cycles(G):
            if len(cycle) >= 2:
                cycles.append(cycle)
    except Exception:
        pass
    
    # Generate resolution strategies
    resolutions = []
    for i, cycle in enumerate(cycles[:10]):  # Limit to top 10
        resolution = _suggest_resolution(cycle, dep_list, G)
        resolutions.append(resolution)
    
    # Overall health
    if not cycles:
        health = "healthy"
        summary = "No circular dependencies detected. Great job!"
    elif len(cycles) <= 3:
        health = "warning"
        summary = f"{len(cycles)} circular dependencies found. Address them to improve maintainability."
    else:
        health = "critical"
        summary = f"{len(cycles)} circular dependencies detected! This significantly impacts code maintainability."
    
    return {
        "health": health,
        "summary": summary,
        "total_cycles": len(cycles),
        "cycles": [{"nodes": c, "length": len(c)} for c in cycles[:10]],
        "resolutions": resolutions
    }


def _suggest_resolution(cycle: list, deps: list, graph: nx.DiGraph) -> dict:
    """Suggest a resolution strategy for a circular dependency."""
    cycle_str = " → ".join([n.split("/")[-1] if "/" in n else n for n in cycle])
    cycle_str += f" → {cycle[0].split('/')[-1] if '/' in cycle[0] else cycle[0]}"
    
    # Find the weakest link (edge with least other dependencies)
    min_weight = float('inf')
    break_edge = None
    
    for i in range(len(cycle)):
        src = cycle[i]
        tgt = cycle[(i + 1) % len(cycle)]
        # Count how many other edges src → tgt participation has
        src_edges = graph.out_degree(src)
        tgt_edges = graph.in_degree(tgt)
        weight = src_edges + tgt_edges
        if weight < min_weight:
            min_weight = weight
            break_edge = (src, tgt)
    
    strategies = []
    
    # Strategy 1: Break dependency
    if break_edge:
        strategies.append({
            "name": "Break Dependency",
            "description": f"Remove the dependency from '{_short(break_edge[0])}' to '{_short(break_edge[1])}' (weakest link in cycle)",
            "action": f"Move shared logic to a new module that both can import"
        })
    
    # Strategy 2: Dependency Inversion
    strategies.append({
        "name": "Dependency Inversion Principle",
        "description": "Introduce an abstract interface/protocol that both modules depend on",
        "action": "Create an interface module and have both modules depend on it instead of each other"
    })
    
    # Strategy 3: Mediator Pattern
    if len(cycle) > 2:
        strategies.append({
            "name": "Mediator Pattern",
            "description": "Introduce a mediator module to coordinate between cyclic modules",
            "action": "Create a central coordinator that manages communication between the modules"
        })
    
    # Strategy 4: Merge
    if len(cycle) == 2:
        strategies.append({
            "name": "Merge Modules",
            "description": f"If '{_short(cycle[0])}' and '{_short(cycle[1])}' are tightly coupled, consider merging them",
            "action": "Combine both modules into a single module if they share the same responsibility"
        })
    
    return {
        "cycle": cycle_str,
        "cycle_length": len(cycle),
        "recommended_break": break_edge,
        "strategies": strategies
    }


def _short(name: str) -> str:
    """Get short name for display."""
    return name.split("/")[-1] if "/" in name else name
