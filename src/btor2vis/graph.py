"""Build a Cytoscape.js-compatible graph from parsed BTOR2 data."""

from __future__ import annotations

import json
from typing import Any

from btor2vis.parser import Node, Sort

# Node type categories for styling.
PROPERTY_TAGS = {"bad", "constraint", "fair", "output", "justice"}
INPUT_TAGS = {"input"}
CONST_TAGS = {"zero", "one", "ones", "const", "constd", "consth"}
STATE_TAGS = {"state", "init", "next"}


def _node_category(tag: str) -> str:
    if tag in PROPERTY_TAGS:
        return "property"
    if tag in INPUT_TAGS:
        return "input"
    if tag in CONST_TAGS:
        return "constant"
    if tag in STATE_TAGS:
        return "state"
    return "operator"


def _node_label(node: Node) -> str:
    parts = [node.tag]
    if node.symbol:
        parts.append(node.symbol)
    if node.extra:
        parts.append(" ".join(node.extra))
    return " ".join(parts)


def _sort_display(node: Node, sorts: dict[int, Sort]) -> str:
    if node.sort_id is None:
        return ""
    sort = sorts.get(node.sort_id)
    if sort is None:
        return f"sort #{node.sort_id}"
    return sort.display(sorts)


def build_cytoscape_graph(nodes: dict[int, Node], sorts: dict[int, Sort]) -> str:
    """Build Cytoscape.js elements JSON string."""
    elements: dict[str, list[dict[str, Any]]] = {"nodes": [], "edges": []}

    for nid, node in nodes.items():
        category = _node_category(node.tag)
        sort_info = _sort_display(node, sorts)

        elements["nodes"].append({
            "data": {
                "id": str(nid),
                "label": _node_label(node),
                "nid": nid,
                "category": category,
                "sort": sort_info,
            }
        })

        for i, arg in enumerate(node.args):
            negated = arg < 0
            target = abs(arg)
            elements["edges"].append({
                "data": {
                    "id": f"e{nid}_{i}",
                    "source": str(nid),
                    "target": str(target),
                    "negated": negated,
                    "arg_index": i,
                }
            })

    return json.dumps(elements)
