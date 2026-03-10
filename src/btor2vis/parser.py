"""Parser for the BTOR2 file format."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Sort:
    """A BTOR2 sort (type) definition."""
    nid: int
    kind: str  # "bitvec" or "array"
    width: int | None = None  # bitvec width
    index_sort: int | None = None  # array index sort nid
    element_sort: int | None = None  # array element sort nid

    def display(self, sorts: dict[int, Sort]) -> str:
        if self.kind == "bitvec":
            return f"bv{self.width}"
        idx = sorts[self.index_sort].display(sorts) if self.index_sort else "?"
        elem = sorts[self.element_sort].display(sorts) if self.element_sort else "?"
        return f"array[{idx} -> {elem}]"


@dataclass
class Node:
    """A parsed BTOR2 node (non-sort line)."""
    nid: int
    tag: str
    sort_id: int | None = None  # reference to a sort line (None for properties)
    args: list[int] = field(default_factory=list)  # argument nids (may be negative for negation)
    symbol: str | None = None
    extra: list[str] = field(default_factory=list)  # extra params (e.g. width for sext/uext, bits for slice, value for const)


# Property tags have no sort id — they directly reference an argument node.
PROPERTY_TAGS = {"bad", "constraint", "fair", "output"}
# Justice is special: `justice <num> <nid1> [<nid2>...]`
JUSTICE_TAG = "justice"

# Tags that define sorts (not graph nodes).
SORT_TAG = "sort"

# Indexed operators that have extra integer parameters after the first argument.
# sext/uext: <nid> <op> <sid> <arg> <width>
# slice: <nid> slice <sid> <arg> <upper> <lower>
INDEXED_OPS = {"sext", "uext", "slice"}

# Constants with a value parameter after the sort id.
CONST_TAGS = {"const", "constd", "consth"}

# Nullary operators (no arguments beyond sort id).
NULLARY_TAGS = {"zero", "one", "ones", "input", "state"}


def parse_btor2(path: Path) -> tuple[dict[int, Node], dict[int, Sort]]:
    """Parse a BTOR2 file. Returns (nodes, sorts)."""
    nodes: dict[int, Node] = {}
    sorts: dict[int, Sort] = {}

    with open(path) as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith(";"):
                continue

            # Strip inline comment.
            if " ;" in line:
                line = line[: line.index(" ;")]

            tokens = line.split()
            if len(tokens) < 2:
                continue

            nid = int(tokens[0])
            tag = tokens[1]

            if tag == SORT_TAG:
                sort = _parse_sort(nid, tokens)
                sorts[nid] = sort
                continue

            node = _parse_node(nid, tag, tokens)
            nodes[nid] = node

    return nodes, sorts


def _parse_sort(nid: int, tokens: list[str]) -> Sort:
    kind = tokens[2]
    if kind == "bitvec":
        return Sort(nid=nid, kind="bitvec", width=int(tokens[3]))
    elif kind == "array":
        return Sort(nid=nid, kind="array", index_sort=int(tokens[3]), element_sort=int(tokens[4]))
    else:
        raise ValueError(f"Unknown sort kind: {kind}")


def _parse_node(nid: int, tag: str, tokens: list[str]) -> Node:
    if tag in PROPERTY_TAGS:
        # <nid> <tag> <arg>
        return Node(nid=nid, tag=tag, args=[int(tokens[2])])

    if tag == JUSTICE_TAG:
        # <nid> justice <num> <nid1> [<nid2>...]
        num = int(tokens[2])
        args = [int(t) for t in tokens[3: 3 + num]]
        return Node(nid=nid, tag=tag, args=args)

    # All remaining nodes have a sort id at tokens[2].
    sort_id = int(tokens[2])
    rest = tokens[3:]

    if tag in NULLARY_TAGS:
        # input/state may have an optional symbol name.
        symbol = rest[0] if rest and not _is_int(rest[0]) else None
        return Node(nid=nid, tag=tag, sort_id=sort_id, symbol=symbol)

    if tag in CONST_TAGS:
        # <nid> const <sid> <value>
        return Node(nid=nid, tag=tag, sort_id=sort_id, extra=[rest[0]] if rest else [])

    if tag in INDEXED_OPS:
        if tag == "slice":
            # <nid> slice <sid> <arg> <upper> <lower>
            return Node(nid=nid, tag=tag, sort_id=sort_id,
                        args=[int(rest[0])], extra=[rest[1], rest[2]])
        else:
            # sext/uext: <nid> <op> <sid> <arg> <width>
            return Node(nid=nid, tag=tag, sort_id=sort_id,
                        args=[int(rest[0])], extra=[rest[1]])

    # Generic operator: all remaining tokens are args, except a trailing non-integer symbol.
    args: list[int] = []
    symbol: str | None = None
    for t in rest:
        if _is_int(t):
            args.append(int(t))
        else:
            symbol = t
            break

    return Node(nid=nid, tag=tag, sort_id=sort_id, args=args, symbol=symbol)


def _is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False
