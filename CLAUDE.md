# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

btor2vis is a Python CLI tool that visualizes BTOR2 hardware model checking files as interactive directed acyclic graphs in the browser using Cytoscape.js.

## Commands

```bash
python -m venv .venv && source .venv/bin/activate  # first time setup
pip install -e .                                     # install in dev mode
btor2vis <file.btor2>                                # open visualization in browser
btor2vis <file.btor2> -o output.html                 # save to specific file
python -m btor2vis <file.btor2>                      # alternative invocation
```

## Architecture

The pipeline is: **parse → build graph → generate HTML → open browser**.

- `src/btor2vis/parser.py` — Parses BTOR2 text into `Node` and `Sort` dataclasses. Sorts are stored separately (not as graph nodes) and used as metadata for hover tooltips.
- `src/btor2vis/graph.py` — Converts parsed nodes into Cytoscape.js JSON elements (nodes + edges). Nodes are categorized as: property, input, constant, state, operator. Negative argument references become edges marked as negated.
- `src/btor2vis/visualize.py` — Injects graph JSON into the HTML template and opens in browser.
- `src/btor2vis/template.html` — Self-contained HTML with Cytoscape.js + dagre layout. Loads JS from CDN. Contains all styling, tooltip logic, and graph rendering.
- `src/btor2vis/__main__.py` — CLI entry point wiring the pipeline together.

## BTOR2 Format Notes

- Each line defines a node: `<nid> <tag> [<sort_id>] [<args>...] [<symbol>]`
- Property nodes (bad, constraint, output, fair, justice) have no sort_id
- Negative argument nids (e.g., `-3`) mean bitwise negation of that node
- Sort lines (`<nid> sort bitvec <width>` / `<nid> sort array <sid> <sid>`) define types but are not graph nodes
- No forward references allowed — nodes only reference previously defined nids

## Key Design Decisions

- No runtime dependencies beyond Python stdlib — Cytoscape.js and dagre are loaded from CDN in the generated HTML
- Sorts are metadata, not nodes — displayed on hover tooltip, not in the graph
- DAG layout: roots (bad/constraint/output/fair/justice) at top, leaves (inputs/constants) at bottom
- Negated edges rendered with dashed red lines to distinguish from normal edges
