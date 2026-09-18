import argparse
import sys
from pathlib import Path

from aiger2vis.graph import build_cytoscape_graph
from aiger2vis.parser import parse_aiger
from aiger2vis.visualize import generate_and_open


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aiger2vis",
        description="Visualize AIGER files as interactive directed acyclic graphs",
    )
    parser.add_argument("file", type=Path, help="Path to a .aag or .aig file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output HTML file path (default: temporary file)",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    model = parse_aiger(args.file)
    graph_json = build_cytoscape_graph(model)
    generate_and_open(graph_json, args.file.name, args.output)


if __name__ == "__main__":
    main()
