# aiger2vis

Standalone CLI tool to visualize AIGER files (`.aag` and `.aig`) as interactive directed acyclic graphs in the browser.

## Usage

```bash
cd aiger2vis
python -m venv .venv && source .venv/bin/activate
pip install -e .
aiger2vis /path/to/file.aag
aiger2vis /path/to/file.aig -o output.html
python -m aiger2vis /path/to/file.aig
```

## Notes

- This tool is intentionally standalone and does not modify `btor2vis`.
- Negated literals are rendered as dashed orange edges.
- Supports ASCII AIGER (`aag`) and binary AIGER (`aig`).
