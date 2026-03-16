"""Build a Cytoscape.js-compatible graph from parsed AIGER data."""

from __future__ import annotations

import json
from typing import Any

from aiger2vis.parser import AigModel


def build_cytoscape_graph(model: AigModel) -> str:
    """Build Cytoscape.js elements JSON string."""
    elements: dict[str, list[dict[str, Any]]] = {"nodes": [], "edges": []}

    for node_id, node in model.nodes.items():
        elements["nodes"].append(
            {
                "data": {
                    "id": node_id,
                    "label": node.label,
                    "nid": node_id,
                    "category": node.category,
                    "tag": node.tag,
                    "sort": "",
                }
            }
        )

        for i, arg_lit in enumerate(node.args):
            target_lit = arg_lit & ~1
            target_id = str(target_lit)
            elements["edges"].append(
                {
                    "data": {
                        "id": f"e{node_id}_{i}",
                        "source": node_id,
                        "target": target_id,
                        "negated": (arg_lit & 1) == 1,
                        "arg_index": i,
                    }
                }
            )

    return json.dumps(elements)
