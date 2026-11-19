#!/usr/bin/env python3
"""Render an ArgumentTree pyramid as markdown or ansi.

markdown is the default. It renders the full tree as nested bullets with each
support line under its claim. ansi shows governingThought and keyLine only.
Deeper children and support figures stay in the JSON. ansi lays out for
--width in terminal columns (default 80). Key-line cards that do not fit one
row wrap onto balanced rows. markdown ignores --width.

Usage:
  python3 scripts/render-pyramid.py <tree.json> [--format markdown|ansi] [--width N]
  python3 scripts/render-pyramid.py <tree.json> --check [--format markdown|ansi] [--width N]
  python3 scripts/render-pyramid.py <tree.json> --write out.txt [--format markdown|ansi] [--width N]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

LABEL_MAX = 40
LABEL_LINES = 3


@dataclass(frozen=True)
class Metrics:
    default_width: int
    margin: float
    gap: float
    min_card: float
    max_card: float
    max_gt: float
    key_font: float
    gt_font: float
    char_w: float
    pad_x: float
    pad_y: float
    line_gap: float
    row_gap: float
    bar_offset: float
    grid: bool

    def line_h(self, font: float) -> float:
        return font + self.line_gap

    def text_chars(self, box_w: float, font: float) -> int:
        return int((box_w - 2 * self.pad_x) / (self.char_w * font))

    def box_h(self, lines: int, font: float) -> float:
        return lines * self.line_h(font) + 2 * self.pad_y

    def half(self, v: float) -> float:
        return v // 2 if self.grid else v / 2


# ansi boxes use pad_x 2 for the border plus
# one space, and grid coordinates are cells, so a box spans [x, x + w). An odd
# ansi gap gives the trunk between two rows a centre column.
METRICS: dict[str, Metrics] = {
    "ansi": Metrics(
        default_width=80, margin=0, gap=3, min_card=20, max_card=40, max_gt=64,
        key_font=1, gt_font=1, char_w=1, pad_x=2, pad_y=1, line_gap=0,
        row_gap=3, bar_offset=1, grid=True,
    ),
}


def ellipsize(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    budget = max_chars - 1
    if budget < 1:
        return "…"
    cut = text[:budget]
    if " " in cut:
        head, _, _tail = cut.rpartition(" ")
        if len(head) >= max(1, budget // 2):
            cut = head
    return cut.rstrip(".,;:") + "…"


def wrap_and_ellipsize_tail(text: str, max_chars: int = LABEL_MAX, max_lines: int = LABEL_LINES) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return [""]
    words = cleaned.split()
    lines: list[str] = []
    i = 0
    while i < len(words) and len(lines) < max_lines:
        if len(lines) == max_lines - 1:
            rest = " ".join(words[i:])
            lines.append(rest if len(rest) <= max_chars else ellipsize(rest, max_chars))
            break
        word = words[i]
        if len(word) > max_chars:
            lines.append(word[:max_chars])
            words[i] = word[max_chars:]
            continue
        cur = word
        i += 1
        while i < len(words) and len(words[i]) <= max_chars and len(cur) + 1 + len(words[i]) <= max_chars:
            cur = f"{cur} {words[i]}"
            i += 1
        lines.append(cur)
    return lines or [""]


def wrap_balanced(text: str, max_chars: int, max_lines: int = LABEL_LINES) -> list[str]:
    """Wrap at the narrowest width that keeps the greedy line count, so no line is an orphan."""
    lines = wrap_and_ellipsize_tail(text, max_chars, max_lines)
    if len(lines) < 2 or any("…" in line for line in lines):
        return lines
    for chars in range(max(len(w) for w in text.split()), max_chars):
        tighter = wrap_and_ellipsize_tail(text, chars, max_lines)
        if len(tighter) == len(lines) and not any("…" in line for line in tighter):
            return tighter
    return lines


def collect_support(nodes: list[dict[str, Any]], out: list[str]) -> None:
    for node in nodes:
        for item in node.get("support") or []:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
        children = node.get("children")
        if isinstance(children, list):
            collect_support(children, out)


def deeper_nodes(nodes: list[dict[str, Any]], out: list[dict[str, Any]]) -> None:
    for node in nodes:
        children = node.get("children")
        if isinstance(children, list):
            for child in children:
                out.append(child)
                deeper_nodes([child], out)


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float
    lines: tuple[str, ...]
    node_id: str | None = None


@dataclass(frozen=True)
class Row:
    cards: tuple[Box, ...]
    centers: tuple[float, ...]
    bar_y: float
    feed_x: float
    feed_y: float
    out_x: float | None


@dataclass(frozen=True)
class Layout:
    metrics: Metrics
    width: float
    height: float
    gt: Box
    rows: tuple[Row, ...]

    def boxes(self) -> list[Box]:
        return [self.gt, *(card for row in self.rows for card in row.cards)]

    def wires(self) -> list[tuple[float, float, float, float]]:
        out = []
        for row in self.rows:
            out.append((row.feed_x, row.feed_y, row.feed_x, row.bar_y))
            xs = [*row.centers, row.feed_x] + ([row.out_x] if row.out_x is not None else [])
            if min(xs) != max(xs):
                out.append((min(xs), row.bar_y, max(xs), row.bar_y))
        return out

    def drops(self) -> list[tuple[float, float, float, float]]:
        edge = 1 if self.metrics.grid else 0
        return [
            (x, row.bar_y, x, card.y - edge)
            for row in self.rows
            for x, card in zip(row.centers, row.cards)
        ]

    def label_entries(self) -> list[tuple[str, list[str]]]:
        return [("governingThought", list(self.gt.lines))] + [
            (card.node_id or "", list(card.lines)) for row in self.rows for card in row.cards
        ]


def balanced_rows(n: int, per_row: int) -> list[int]:
    """Split n cards into the fewest rows of at most per_row, larger rows last.

    A lone card goes last instead: above another row, the trunk would have to
    route around it.
    """
    rows = -(-n // per_row)
    base, extra = divmod(n, rows)
    sizes = [base + (1 if i >= rows - extra else 0) for i in range(rows)]
    return sizes[1:] + sizes[:1] if rows > 1 and sizes[0] == 1 else sizes


def min_width(m: Metrics) -> int:
    return math.ceil(2 * m.min_card + m.gap + 2 * m.margin)


def layout(data: dict[str, Any], m: Metrics, width: int) -> Layout:
    keys = data["keyLine"]
    n = len(keys)
    if n < 1:
        raise ValueError("keyLine must contain at least one node")
    if width < min_width(m):
        raise ValueError(f"--width {width} is too narrow; use at least {min_width(m)}")

    grid = int(m.grid)
    # One spare grid column absorbs the rounding when rows centre on the axis.
    usable = width - 2 * m.margin - grid
    per_row = int((usable + m.gap) // (m.min_card + m.gap))
    counts = balanced_rows(n, per_row)
    widest = max(counts)
    card_w = min(m.max_card, (usable - (widest - 1) * m.gap) / widest)
    card_w = math.floor(card_w) if grid else card_w
    key_chars = m.text_chars(card_w, m.key_font)
    pitch = card_w + m.gap
    gap_mid = m.gap - m.half(m.gap)

    # Every row is placed against one axis so the stem, the trunks, and the
    # middle drops share a column after rounding to cells.
    axis = m.half(width)
    gt_w = min(usable + grid, m.max_gt)
    gt_lines = wrap_balanced(data["governingThought"], m.text_chars(gt_w, m.gt_font))
    if grid:
        # Terminal text is left-aligned, so a box wider than its text reads as a hole.
        gt_w = min(gt_w, max(len(line) for line in gt_lines) + 2 * m.pad_x)
    gt = Box(axis - m.half(gt_w), m.margin, gt_w, m.box_h(len(gt_lines), m.gt_font), tuple(gt_lines))

    feed_x, feed_y = axis, gt.y + gt.h - grid
    top = gt.y + gt.h
    rows: list[Row] = []
    start = 0
    for i, k in enumerate(counts):
        labels = [
            (node["id"], wrap_balanced(node["claim"], key_chars))
            for node in keys[start : start + k]
        ]
        start += k
        h = m.box_h(max(len(lines) for _, lines in labels), m.key_font)
        y = top + m.row_gap
        middle = (k // 2) * pitch
        x0 = axis - middle - m.half(card_w) if k % 2 else axis - middle + gap_mid
        cards = tuple(
            Box(x0 + j * pitch, y, card_w, h, tuple(lines), node_id)
            for j, (node_id, lines) in enumerate(labels)
        )
        centers = tuple(card.x + m.half(card_w) for card in cards)
        # The trunk to the next row runs down the gap left of the middle card.
        out_x = cards[k // 2].x - gap_mid if i < len(counts) - 1 else None
        bar_y = top + m.bar_offset
        rows.append(Row(cards, centers, bar_y, feed_x, feed_y, out_x))
        if out_x is not None:
            feed_x, feed_y = out_x, bar_y
        top = y + h
    return Layout(m, width, top + m.margin, gt, tuple(rows))


UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8
GLYPHS = {
    UP: "│", DOWN: "│", UP | DOWN: "│",
    LEFT: "─", RIGHT: "─", LEFT | RIGHT: "─",
    DOWN | RIGHT: "┌", DOWN | LEFT: "┐", UP | RIGHT: "└", UP | LEFT: "┘",
    UP | DOWN | RIGHT: "├", UP | DOWN | LEFT: "┤",
    DOWN | LEFT | RIGHT: "┬", UP | LEFT | RIGHT: "┴",
    UP | DOWN | LEFT | RIGHT: "┼",
}
ARROW = "▼"


def render_ansi(data: dict[str, Any], width: int) -> str:
    lay = layout(data, METRICS["ansi"], width)
    cols, height = int(lay.width), int(lay.height)
    links = [[0] * cols for _ in range(height)]
    marks: dict[tuple[int, int], str] = {}

    def wire(x0: float, y0: float, x1: float, y1: float) -> None:
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        if y0 == y1:
            for x in range(x0, x1 + 1):
                links[y0][x] |= (LEFT if x > x0 else 0) | (RIGHT if x < x1 else 0)
        else:
            for y in range(y0, y1 + 1):
                links[y][x0] |= (UP if y > y0 else 0) | (DOWN if y < y1 else 0)

    for box in lay.boxes():
        x, y, right, bottom = int(box.x), int(box.y), int(box.x + box.w) - 1, int(box.y + box.h) - 1
        for edge in ((x, y, right, y), (x, bottom, right, bottom), (x, y, x, bottom), (right, y, right, bottom)):
            wire(*edge)
        for i, line in enumerate(box.lines):
            for j, ch in enumerate(line):
                marks[(y + 1 + i, x + 2 + j)] = ch
    for segment in lay.wires():
        wire(*segment)
    for x, y0, _, y1 in lay.drops():
        wire(x, y0, x, y1)
        marks[(int(y1), int(x))] = ARROW

    rows = []
    for r in range(height):
        rows.append("".join(marks.get((r, c)) or GLYPHS.get(links[r][c], " ") for c in range(cols)).rstrip())
    return "```\n" + "\n".join(rows) + "\n```\n"


def md_escape(text: str) -> str:
    """Backslash-escape inline markdown so the text renders verbatim."""
    text = text.replace("\\", "\\\\")
    text = re.sub(r"([`*_\[\]<>|$~])", r"\\\1", text)
    text = re.sub(r"&(#?\w+;)", r"\\&\1", text)
    return re.sub(r":([a-z0-9_+-]+):", r"\\:\1:", text)


def md_claim(node: dict[str, Any], depth: int) -> str:
    claim = md_escape(node["claim"])
    role = node.get("role", "reason")
    return (f"**{claim}**" if depth == 0 else claim) + ("" if role == "reason" else f" _{role}_")


def render_markdown(data: dict[str, Any]) -> str:
    out = [f"> ### {md_escape(data['governingThought'])}", ""]

    def walk(node: dict[str, Any], depth: int, marker: str) -> None:
        indent = "  " * depth
        lines = [f"{indent}{marker} `{node['id']}` {md_claim(node, depth)}"]
        lines += [f"{indent}  ↳ *{md_escape(s)}*" for s in node.get("support") or []]
        # A trailing backslash is a hard break, so support stays inside its claim's item.
        out.append("\\\n".join(lines))
        for child in node.get("children") or []:
            walk(child, depth + 1, "-")

    # Alternating markers start a new list per key line, which spaces the groups apart.
    grouped = any(node.get("children") for node in data["keyLine"])
    for i, node in enumerate(data["keyLine"]):
        walk(node, 0, "-*"[i % 2] if grouped else "-")
    return "\n".join(out) + "\n"


def check_leaks(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    supports: list[str] = []
    collect_support(data["keyLine"], supports)
    for figure in supports:
        if figure in diagram:
            errors.append(f"support figure leaked into diagram: {figure!r}")
    deep: list[dict[str, Any]] = []
    deeper_nodes(data["keyLine"], deep)
    for child in deep:
        claim = child.get("claim")
        if isinstance(claim, str) and claim and claim in diagram:
            errors.append(f"{child.get('id')}: deeper claim must not appear in the diagram")
    return errors


def check_fitted_labels(
    diagram: str,
    entries: list[tuple[str, list[str]]],
    present: Callable[[str], bool],
) -> list[str]:
    errors: list[str] = []
    saw_ellipsis = False
    for name, lines in entries:
        for line in lines:
            if not present(line):
                errors.append(f"{name}: missing label text {line!r}")
            if "…" in line:
                saw_ellipsis = True
    if not saw_ellipsis and "…" in diagram:
        errors.append("diagram ellipsizes a label that fits")
    return errors


def check_ansi(data: dict[str, Any], diagram: str, width: int) -> list[str]:
    errors = check_leaks(data, diagram)
    if not diagram.startswith("```\n") or "┌" not in diagram or ARROW not in diagram:
        errors.append("diagram must be box-drawing inside a fenced code block")
    for number, line in enumerate(diagram.splitlines(), 1):
        if len(line) > width:
            errors.append(f"line {number} is {len(line)} columns, wider than --width {width}")
    lay = layout(data, METRICS["ansi"], width)
    errors.extend(check_fitted_labels(diagram, lay.label_entries(), lambda line: line in diagram))
    grid = diagram.splitlines()[1:-1]

    def cell(row: int, col: int) -> str:
        line = grid[row] if row < len(grid) else ""
        return line[col] if col < len(line) else " "

    for box in lay.boxes():
        x, y, right, bottom = int(box.x), int(box.y), int(box.x + box.w) - 1, int(box.y + box.h) - 1
        corners = cell(y, x) + cell(y, right) + cell(bottom, x) + cell(bottom, right)
        sides = {cell(r, c) for r in range(y + 1, bottom) for c in (x, right)}
        if corners != "┌┐└┘" or sides != {"│"}:
            errors.append(f"{box.node_id or 'governingThought'}: box border is broken or overwritten")
    return errors


def check_markdown(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    if not diagram.startswith(f"> ### {md_escape(data['governingThought'])}\n\n"):
        errors.append("diagram must open with the governing thought as a quoted heading")
    if re.search(r"(?<!\\)<[A-Za-z/!]", diagram):
        errors.append("Markdown paint must not include raw HTML tags")
    if "```" in diagram:
        errors.append("Markdown paint must not include code fences")
    supports = 0

    def walk(node: dict[str, Any], depth: int) -> None:
        nonlocal supports
        if f"`{node['id']}` {md_claim(node, depth)}" not in diagram:
            errors.append(f"{node['id']}: claim missing from the tree")
        for item in node.get("support") or []:
            supports += 1
            if f"↳ *{md_escape(item)}*" not in diagram:
                errors.append(f"{node['id']}: support missing from the tree: {item!r}")
        for child in node.get("children") or []:
            walk(child, depth + 1)

    for node in data["keyLine"]:
        walk(node, 0)
    lines = diagram.splitlines()
    arrows = [i for i, line in enumerate(lines) if line.lstrip().startswith("↳ ")]
    if len(arrows) != supports:
        errors.append(f"tree has {len(arrows)} support lines, want {supports}")
    for i in arrows:
        if not lines[i - 1].endswith("\\"):
            errors.append(f"line {i + 1}: support must follow a hard break")
    return errors


RENDERERS: dict[str, Callable[[dict[str, Any], int], str]] = {
    "ansi": render_ansi,
    "markdown": lambda data, _width: render_markdown(data),
}
CHECKERS: dict[str, Callable[[dict[str, Any], str, int], list[str]]] = {
    "ansi": check_ansi,
    "markdown": lambda data, diagram, _width: check_markdown(data, diagram),
}
FORMATS = tuple(RENDERERS)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tree", type=Path)
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="markdown",
        help="markdown (default) or ansi",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Target width in ansi columns (default 80). markdown ignores it",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check the chosen format: labels, fit, fences, and depth. Only markdown shows the full tree",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write the chosen format to this path",
    )
    args = parser.parse_args(argv)

    data = json.loads(args.tree.read_text(encoding="utf-8"))
    metrics = METRICS.get(args.format)
    width = args.width or (metrics.default_width if metrics else 0)
    try:
        diagram = RENDERERS[args.format](data, width)
    except ValueError as exc:
        parser.error(str(exc))

    if args.write:
        args.write.write_text(diagram, encoding="utf-8")

    if args.check:
        errors = CHECKERS[args.format](data, diagram, width)
        if errors:
            print(f"FAIL {args.tree} {args.format}")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"OK   {args.tree} {args.format}")
        return 0

    if not args.write:
        sys.stdout.write(diagram)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
