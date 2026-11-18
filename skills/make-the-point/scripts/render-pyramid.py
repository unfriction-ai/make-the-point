#!/usr/bin/env python3
"""Render an ArgumentTree pyramid as svg, mermaid, or ansi.

The diagram shows governingThought and keyLine only. Deeper children and
support figures stay in the JSON. svg is the default and has no page fill.

Usage:
  python3 scripts/render-pyramid.py <tree.json> [--format svg|mermaid|ansi]
  python3 scripts/render-pyramid.py <tree.json> --check [--format svg|mermaid|ansi]
  python3 scripts/render-pyramid.py <tree.json> --write out.txt [--format svg|mermaid|ansi]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any, Callable

LABEL_MAX = 40
LABEL_LINES = 3
PURPLE = "#5B2C6F"
PURPLE_STROKE = "#7D3C98"
TEAL = "#0E6655"
TEAL_STROKE = "#148F77"
CONNECTOR = "#9a9a9a"
PAGE_FILL = "#141414"


def key_width(n: int) -> int:
    return 26 if n <= 4 else 18


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


def svg_text_block(lines: list[str], x: float, y: float, font_size: int = 13) -> str:
    line_h = font_size + 3
    start = y - ((len(lines) - 1) * line_h) / 2
    chunks = []
    for i, line in enumerate(lines):
        yy = start + i * line_h
        chunks.append(
            f'<text x="{x:.1f}" y="{yy:.1f}" text-anchor="middle" '
            f'fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" '
            f'font-size="{font_size}">{escape(line)}</text>'
        )
    return "\n".join(chunks)


def render_svg(data: dict[str, Any]) -> str:
    n = len(data["keyLine"])
    if n < 1:
        raise ValueError("keyLine must contain at least one node")

    gt_chars, key_chars = LABEL_MAX, key_width(n)
    gt_label = wrap_and_ellipsize_tail(data["governingThought"], gt_chars, LABEL_LINES)
    keys = [
        (node["id"], wrap_and_ellipsize_tail(node["claim"], key_chars, LABEL_LINES))
        for node in data["keyLine"]
    ]

    card_w = 200 if n <= 4 else max(140, int(720 / n) - 16)
    card_h = 72
    gap = 20 if n <= 4 else 12
    gt_w = min(560.0, max(300.0, n * card_w + (n - 1) * gap))
    gt_h = 64.0
    width = max(gt_w + 40.0, n * card_w + (n - 1) * gap + 40.0)
    gt_x = (width - gt_w) / 2
    gt_y = 16.0
    row_y = gt_y + gt_h + 48.0
    total_row = n * card_w + (n - 1) * gap
    start_x = (width - total_row) / 2
    height = row_y + card_h + 24.0
    mid_y = gt_y + gt_h
    branch_y = mid_y + 24.0
    cx = gt_x + gt_w / 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="100%" role="img" aria-label="Argument pyramid">',
        f'<path d="M {cx:.1f} {mid_y:.1f} V {branch_y:.1f}" stroke="{CONNECTOR}" '
        f'stroke-width="1.5" fill="none"/>',
    ]

    if n == 1:
        x = start_x + card_w / 2
        parts.append(
            f'<path d="M {cx:.1f} {branch_y:.1f} H {x:.1f} V {row_y:.1f}" '
            f'stroke="{CONNECTOR}" stroke-width="1.5" fill="none"/>'
        )
    else:
        left = start_x + card_w / 2
        right = start_x + (n - 1) * (card_w + gap) + card_w / 2
        parts.append(
            f'<path d="M {left:.1f} {branch_y:.1f} H {right:.1f}" '
            f'stroke="{CONNECTOR}" stroke-width="1.5" fill="none"/>'
        )
        for i in range(n):
            x = start_x + i * (card_w + gap) + card_w / 2
            parts.append(
                f'<path d="M {x:.1f} {branch_y:.1f} V {row_y:.1f}" '
                f'stroke="{CONNECTOR}" stroke-width="1.5" fill="none"/>'
            )

    parts.append(
        f'<rect x="{gt_x:.1f}" y="{gt_y:.1f}" width="{gt_w:.1f}" height="{gt_h:.1f}" '
        f'rx="10" fill="{PURPLE}" stroke="{PURPLE_STROKE}"/>'
    )
    parts.append(
        svg_text_block(gt_label, gt_x + gt_w / 2, gt_y + gt_h / 2 + 4, font_size=14)
    )

    for i, (node_id, label) in enumerate(keys):
        x = start_x + i * (card_w + gap)
        parts.append(
            f'<rect id="{escape(node_id)}" x="{x:.1f}" y="{row_y:.1f}" '
            f'width="{card_w:.1f}" height="{card_h:.1f}" rx="10" '
            f'fill="{TEAL}" stroke="{TEAL_STROKE}"/>'
        )
        parts.append(svg_text_block(label, x + card_w / 2, row_y + card_h / 2))

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def mermaid_id(node_id: str, used: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9_]", "_", node_id)
    if not base or base[0].isdigit():
        base = "n_" + base
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}_{n}"
        n += 1
    used.add(candidate)
    return candidate


def mermaid_text(lines: list[str]) -> str:
    escaped = [line.replace('"', "'").replace("[", "(").replace("]", ")") for line in lines]
    return "<br/>".join(escaped)


def render_mermaid(data: dict[str, Any]) -> str:
    if len(data["keyLine"]) < 1:
        raise ValueError("keyLine must contain at least one node")
    gt_lines = wrap_and_ellipsize_tail(data["governingThought"], LABEL_MAX, LABEL_LINES)
    used = {"GT"}
    ids = [mermaid_id(node["id"], used) for node in data["keyLine"]]
    key_lines = [
        wrap_and_ellipsize_tail(node["claim"], LABEL_MAX, LABEL_LINES) for node in data["keyLine"]
    ]
    rows = ["flowchart TB", f'  GT["{mermaid_text(gt_lines)}"]']
    for mid, lines in zip(ids, key_lines):
        rows.append(f'  {mid}["{mermaid_text(lines)}"]')
    for mid in ids:
        rows.append(f"  GT --> {mid}")
    rows.append(f"  style GT fill:{PURPLE},stroke:{PURPLE_STROKE},color:#fff")
    for mid in ids:
        rows.append(f"  style {mid} fill:{TEAL},stroke:{TEAL_STROKE},color:#fff")
    return "```mermaid\n" + "\n".join(rows) + "\n```\n"


def box_width(text_width: int) -> int:
    return text_width + 4


def make_box(lines: list[str], text_width: int, stem: int | None = None) -> list[str]:
    inner = text_width + 2
    top = "┌" + "─" * inner + "┐"
    body = ["│ " + line.ljust(text_width) + " │" for line in lines]
    if stem is None:
        bottom = "└" + "─" * inner + "┘"
    else:
        if not 0 <= stem < inner:
            raise ValueError(f"stem column {stem} outside box of width {inner}")
        dashes = ["─"] * inner
        dashes[stem] = "┬"
        bottom = "└" + "".join(dashes) + "┘"
    return [top, *body, bottom]


def place(rows: list[str], x: int, canvas: int) -> list[str]:
    placed = []
    for row in rows:
        pad = canvas - x - len(row)
        if pad < 0:
            raise ValueError("row is wider than the canvas")
        placed.append(" " * x + row + " " * pad)
    return placed


def hjoin(blocks: list[list[str]], gap: int) -> list[str]:
    height = max(len(block) for block in blocks)
    widths = [len(block[0]) for block in blocks]
    rows = []
    for r in range(height):
        parts = []
        for block, width in zip(blocks, widths):
            parts.append(block[r] if r < len(block) else " " * width)
        rows.append((" " * gap).join(parts))
    return rows


def render_ansi(data: dict[str, Any]) -> str:
    keys = data["keyLine"]
    n = len(keys)
    if n < 1:
        raise ValueError("keyLine must contain at least one node")

    key_inner = key_width(n)
    gt_lines = wrap_and_ellipsize_tail(data["governingThought"], LABEL_MAX, LABEL_LINES)
    key_wrapped = [wrap_and_ellipsize_tail(node["claim"], key_inner, LABEL_LINES) for node in keys]
    key_boxes = [make_box(lines, key_inner) for lines in key_wrapped]
    gap = 1
    key_row = hjoin(key_boxes, gap)
    key_w = len(key_row[0])
    gt_box_w = box_width(LABEL_MAX)
    canvas = max(key_w, gt_box_w)
    gt_x = (canvas - gt_box_w) // 2
    key_x = (canvas - key_w) // 2
    gt_stem = gt_x + gt_box_w // 2
    gt_box = make_box(gt_lines, LABEL_MAX, stem=gt_stem - gt_x - 1)

    box_w = box_width(key_inner)
    centers = []
    x = key_x
    for _ in range(n):
        centers.append(x + box_w // 2)
        x += box_w + gap

    rows = place(gt_box, gt_x, canvas)
    stem = [" "] * canvas
    stem[gt_stem] = "│"
    rows.append("".join(stem))

    if n == 1:
        arrow = [" "] * canvas
        arrow[centers[0]] = "▼"
        rows.append("".join(arrow))
    else:
        left, right = centers[0], centers[-1]
        bar = [" "] * canvas
        bar[left] = "┌"
        for col in range(left + 1, right):
            bar[col] = "─"
        bar[right] = "┐"
        if left < gt_stem < right:
            bar[gt_stem] = "┼" if gt_stem in centers else "┬"
        elif gt_stem == left:
            bar[left] = "├"
        elif gt_stem == right:
            bar[right] = "┤"
        rows.append("".join(bar))
        arrow = [" "] * canvas
        for col in centers:
            arrow[col] = "▼"
        rows.append("".join(arrow))

    rows.extend(place(key_row, key_x, canvas))
    art = "\n".join(row.rstrip() for row in rows)
    return "```\n" + art + "\n```\n"


def check_leaks(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    supports: list[str] = []
    collect_support(data["keyLine"], supports)
    for figure in supports:
        if figure in diagram or escape(figure) in diagram:
            errors.append(f"support figure leaked into diagram: {figure!r}")
    deep: list[dict[str, Any]] = []
    deeper_nodes(data["keyLine"], deep)
    for child in deep:
        claim = child.get("claim")
        if isinstance(claim, str) and claim and (claim in diagram or escape(claim) in diagram):
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


def label_entries(data: dict[str, Any], gt_chars: int, key_chars: int) -> list[tuple[str, list[str]]]:
    entries = [("governingThought", wrap_and_ellipsize_tail(data["governingThought"], gt_chars, LABEL_LINES))]
    for node in data["keyLine"]:
        entries.append((node["id"], wrap_and_ellipsize_tail(node["claim"], key_chars, LABEL_LINES)))
    return entries


def check_svg(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    if "<svg" not in diagram:
        errors.append("diagram must be an SVG card pyramid")
    if PURPLE not in diagram or TEAL not in diagram:
        errors.append("missing purple or teal card fill")
    if PAGE_FILL in diagram.lower():
        errors.append("SVG must not use a full-bleed page fill")
    if 'width="100%" height="100%"' in diagram:
        errors.append("SVG must not paint a page-sized background rect")
    n = len(data["keyLine"])
    errors.extend(
        check_fitted_labels(
            diagram,
            label_entries(data, LABEL_MAX, key_width(n)),
            lambda line: escape(line) in diagram,
        )
    )
    for node in data["keyLine"]:
        if f'id="{escape(node["id"])}"' not in diagram:
            errors.append(f"{node['id']}: node id missing from diagram")
    deep: list[dict[str, Any]] = []
    deeper_nodes(data["keyLine"], deep)
    for child in deep:
        cid = child.get("id")
        if isinstance(cid, str) and f'id="{escape(cid)}"' in diagram:
            errors.append(f"{cid}: deeper child must not appear in the diagram")
    return errors


def check_mermaid(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    if "```mermaid" not in diagram or "flowchart TB" not in diagram:
        errors.append("diagram must be a fenced Mermaid flowchart")
    if "<svg" in diagram:
        errors.append("Mermaid paint must not include raw SVG")
    if PURPLE not in diagram or TEAL not in diagram:
        errors.append("missing purple or teal node style")
    if "GT -->" not in diagram:
        errors.append("missing edge from governing thought to key line")
    used = {"GT"}
    ids = [mermaid_id(node["id"], used) for node in data["keyLine"]]
    if f"fill:{TEAL}" not in diagram:
        errors.append("missing teal key-line style")
    for mid in ids:
        if f"{mid}[" not in diagram or f"GT --> {mid}" not in diagram:
            errors.append(f"{mid}: key-line node missing from diagram")
    deep: list[dict[str, Any]] = []
    deeper_nodes(data["keyLine"], deep)
    key_ids = set(ids)
    used_deep: set[str] = set()
    for child in deep:
        cid = child.get("id")
        if not isinstance(cid, str):
            continue
        safe = mermaid_id(cid, used_deep)
        if safe not in key_ids and f"{safe}[" in diagram:
            errors.append(f"{cid}: deeper child must not appear in the diagram")
    errors.extend(
        check_fitted_labels(
            diagram,
            label_entries(data, LABEL_MAX, LABEL_MAX),
            lambda line: mermaid_text([line]) in diagram,
        )
    )
    return errors


def check_ansi(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    if not diagram.startswith("```\n") or "┌" not in diagram or "▼" not in diagram:
        errors.append("diagram must be box-drawing inside a fenced code block")
    if "<svg" in diagram or "```mermaid" in diagram:
        errors.append("ANSI paint must not include SVG or Mermaid")
    if PAGE_FILL in diagram.lower():
        errors.append("ANSI paint must not include the SVG page fill")
    errors.extend(
        check_fitted_labels(
            diagram,
            label_entries(data, LABEL_MAX, key_width(len(data["keyLine"]))),
            lambda line: line in diagram,
        )
    )
    return errors


RENDERERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "svg": render_svg,
    "mermaid": render_mermaid,
    "ansi": render_ansi,
}
CHECKERS: dict[str, Callable[[dict[str, Any], str], list[str]]] = {
    "svg": check_svg,
    "mermaid": check_mermaid,
    "ansi": check_ansi,
}
FORMATS = tuple(RENDERERS)


def check_render(data: dict[str, Any], diagram: str, fmt: str) -> list[str]:
    errors = check_leaks(data, diagram)
    errors.extend(CHECKERS[fmt](data, diagram))
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path)
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="svg",
        help="svg (default), mermaid, or ansi",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check labels, colors or fences, shallow tree, and no support leak",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write the chosen format to this path",
    )
    args = parser.parse_args(argv)

    data = json.loads(args.tree.read_text(encoding="utf-8"))
    diagram = RENDERERS[args.format](data)

    if args.write:
        args.write.write_text(diagram, encoding="utf-8")

    if args.check:
        errors = check_render(data, diagram, args.format)
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
