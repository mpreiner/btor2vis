"""Generate HTML visualization and open in browser."""

from __future__ import annotations

import tempfile
import webbrowser
from pathlib import Path


_TEMPLATE = Path(__file__).parent / "template.html"
_PLACEHOLDER = "__GRAPH_DATA__"


def generate_and_open(graph_json: str, output_path: Path | None = None) -> Path:
    """Inject graph data into the HTML template and open in browser."""
    template = _TEMPLATE.read_text()
    html = template.replace(_PLACEHOLDER, graph_json)

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w")
        tmp.write(html)
        tmp.close()
        output_path = Path(tmp.name)
    else:
        output_path.write_text(html)

    print(f"Visualization written to: {output_path}")
    webbrowser.open(output_path.as_uri())
    return output_path
