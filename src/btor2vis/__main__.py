import argparse
import sys
from pathlib import Path

from btor2vis.parser import parse_btor2
from btor2vis.graph import build_cytoscape_graph
from btor2vis.visualize import generate_and_open


def main():
    parser = argparse.ArgumentParser(
        prog="btor2vis",
        description="Visualize BTOR2 files as interactive directed acyclic graphs",
    )
    parser.add_argument("file", type=Path, help="Path to a .btor2 file")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Output HTML file path (default: temporary file)",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    nodes, sorts = parse_btor2(args.file)
    graph_json = build_cytoscape_graph(nodes, sorts)
    generate_and_open(graph_json, args.file.name, args.output)


if __name__ == "__main__":
    main()
