"""Parser for AIGER files (.aag ASCII and .aig binary)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AigNode:
    """Single graph node in an AIG model."""

    node_id: str
    tag: str
    category: str
    label: str
    args: list[int] = field(default_factory=list)  # incoming literal references


@dataclass
class AigModel:
    """Parsed AIG model represented as graph nodes."""

    nodes: dict[str, AigNode]


def parse_aiger(path: Path) -> AigModel:
    raw = path.read_bytes()
    header_line, body_start = _split_first_line(raw)
    tokens = header_line.split()
    if len(tokens) < 6:
        raise ValueError(f"Invalid AIGER header: {header_line!r}")

    fmt = tokens[0]
    if fmt not in {"aag", "aig"}:
        raise ValueError(f"Unsupported AIGER format {fmt!r}; expected 'aag' or 'aig'")

    maxvar = int(tokens[1])
    num_inputs = int(tokens[2])
    num_latches = int(tokens[3])
    num_outputs = int(tokens[4])
    num_ands = int(tokens[5])

    if fmt == "aag":
        return _parse_aag(
            raw,
            body_start,
            maxvar,
            num_inputs,
            num_latches,
            num_outputs,
            num_ands,
        )

    return _parse_aig(
        raw,
        body_start,
        maxvar,
        num_inputs,
        num_latches,
        num_outputs,
        num_ands,
    )


def _parse_aag(
    raw: bytes,
    body_start: int,
    maxvar: int,
    num_inputs: int,
    num_latches: int,
    num_outputs: int,
    num_ands: int,
) -> AigModel:
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty AAG file")

    idx = 1
    input_lits = [int(lines[idx + i].split()[0]) for i in range(num_inputs)]
    idx += num_inputs

    latch_lines = [lines[idx + i].split() for i in range(num_latches)]
    idx += num_latches

    output_lits = [int(lines[idx + i].split()[0]) for i in range(num_outputs)]
    idx += num_outputs

    and_tuples: list[tuple[int, int, int]] = []
    for i in range(num_ands):
        lhs, rhs0, rhs1 = (int(x) for x in lines[idx + i].split()[:3])
        and_tuples.append((lhs, rhs0, rhs1))
    idx += num_ands

    symbol_lines = lines[idx:]
    symbols = _parse_symbols(symbol_lines)

    return _build_model(
        maxvar=maxvar,
        num_inputs=num_inputs,
        num_latches=num_latches,
        input_lits=input_lits,
        latch_lines=latch_lines,
        output_lits=output_lits,
        and_tuples=and_tuples,
        symbols=symbols,
    )


def _parse_aig(
    raw: bytes,
    body_start: int,
    maxvar: int,
    num_inputs: int,
    num_latches: int,
    num_outputs: int,
    num_ands: int,
) -> AigModel:
    ptr = body_start

    latch_lines: list[list[str]] = []
    for _ in range(num_latches):
        line, ptr = _read_ascii_line(raw, ptr)
        latch_lines.append(line.split())

    output_lits: list[int] = []
    for _ in range(num_outputs):
        line, ptr = _read_ascii_line(raw, ptr)
        output_lits.append(int(line.split()[0]))

    and_tuples: list[tuple[int, int, int]] = []
    lhs = 2 * (num_inputs + num_latches + 1)
    for _ in range(num_ands):
        delta0, ptr = _read_uvar(raw, ptr)
        delta1, ptr = _read_uvar(raw, ptr)
        rhs0 = lhs - delta0
        rhs1 = rhs0 - delta1
        and_tuples.append((lhs, rhs0, rhs1))
        lhs += 2

    symbol_lines = raw[ptr:].decode("latin1", errors="replace").splitlines()
    symbols = _parse_symbols(symbol_lines)

    input_lits = [2 * (i + 1) for i in range(num_inputs)]

    return _build_model(
        maxvar=maxvar,
        num_inputs=num_inputs,
        num_latches=num_latches,
        input_lits=input_lits,
        latch_lines=latch_lines,
        output_lits=output_lits,
        and_tuples=and_tuples,
        symbols=symbols,
    )


def _build_model(
    *,
    maxvar: int,
    num_inputs: int,
    num_latches: int,
    input_lits: list[int],
    latch_lines: list[list[str]],
    output_lits: list[int],
    and_tuples: list[tuple[int, int, int]],
    symbols: dict[tuple[str, int], str],
) -> AigModel:
    nodes: dict[str, AigNode] = {}

    nodes["0"] = AigNode(node_id="0", tag="const", category="constant", label="const0")

    for i, lit in enumerate(input_lits):
        lit_id = _base_lit(lit)
        nodes[str(lit_id)] = AigNode(
            node_id=str(lit_id),
            tag="input",
            category="input",
            label=str(lit_id),
        )

    for i, parts in enumerate(latch_lines):
        if not parts:
            continue
        cur_lit = int(parts[0])
        next_lit = int(parts[1]) if len(parts) > 1 else 0
        lit_id = _base_lit(cur_lit)
        nodes[str(lit_id)] = AigNode(
            node_id=str(lit_id),
            tag="latch",
            category="state",
            label=str(lit_id),
            args=[next_lit],
        )

    for lhs, rhs0, rhs1 in and_tuples:
        lit_id = _base_lit(lhs)
        nodes[str(lit_id)] = AigNode(
            node_id=str(lit_id),
            tag="and",
            category="operator",
            label=str(lit_id),
            args=[rhs0, rhs1],
        )

    for i, lit in enumerate(output_lits):
        label = symbols.get(("o", i), f"out{i}")
        node_id = f"out{i}"
        nodes[node_id] = AigNode(
            node_id=node_id,
            tag="output",
            category="property",
            label=label,
            args=[lit],
        )

    # Ensure that all referenced literals have backing nodes.
    for node in list(nodes.values()):
        for lit in node.args:
            base_lit = _base_lit(lit)
            key = str(base_lit)
            if key not in nodes:
                if base_lit == 0:
                    continue
                nodes[key] = AigNode(
                    node_id=key,
                    tag="wire",
                    category="operator",
                    label=key,
                )

    # Keep header consistency check in place; AIGER header maxvar is a variable index,
    # while node ids in this visualizer are literal ids (0, 2, 4, ...).
    if maxvar > 0:
        highest_lit = max((_safe_int_id(n.node_id) for n in nodes.values()), default=0)
        if highest_lit > (2 * maxvar):
            raise ValueError(
                f"AIGER graph references literal {highest_lit}, but header max literal is {2 * maxvar}"
            )

    return AigModel(nodes=nodes)


def _parse_symbols(lines: list[str]) -> dict[tuple[str, int], str]:
    symbols: dict[tuple[str, int], str] = {}
    for line in lines:
        if not line:
            continue
        if line == "c":
            break
        prefix = line[0]
        if prefix not in {"i", "l", "o"}:
            continue
        split = line.find(" ")
        if split < 0:
            continue
        idx_str = line[1:split]
        if not idx_str.isdigit():
            continue
        name = line[split + 1 :].strip()
        symbols[(prefix, int(idx_str))] = name
    return symbols


def _base_lit(lit: int) -> int:
    return lit & ~1


def _safe_int_id(node_id: str) -> int:
    try:
        return int(node_id)
    except ValueError:
        return 0


def _split_first_line(raw: bytes) -> tuple[str, int]:
    end = raw.find(b"\n")
    if end < 0:
        line = raw.decode("ascii", errors="replace").strip("\r")
        return line, len(raw)
    line = raw[:end].decode("ascii", errors="replace").strip("\r")
    return line, end + 1


def _read_ascii_line(raw: bytes, ptr: int) -> tuple[str, int]:
    end = raw.find(b"\n", ptr)
    if end < 0:
        line = raw[ptr:].decode("ascii", errors="replace").strip("\r")
        return line, len(raw)
    line = raw[ptr:end].decode("ascii", errors="replace").strip("\r")
    return line, end + 1


def _read_uvar(raw: bytes, ptr: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if ptr >= len(raw):
            raise ValueError("Unexpected EOF while reading binary AIGER delta")
        byte = raw[ptr]
        ptr += 1
        value |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            return value, ptr
        shift += 7
