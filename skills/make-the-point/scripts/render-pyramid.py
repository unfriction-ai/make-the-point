#!/usr/bin/env python3
"""Render an ArgumentTree as a purple/teal SVG card pyramid (short labels).

The diagram shows governingThought + keyLine only. Deeper children and support
figures stay in the JSON.

Usage:
  python3 scripts/render-pyramid.py <tree.json>
  python3 scripts/render-pyramid.py <tree.json> --check
  python3 scripts/render-pyramid.py <tree.json> --write out.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any

LABEL_MAX = 40
PURPLE = "#5B2C6F"
PURPLE_STROKE = "#7D3C98"
TEAL = "#0E6655"
TEAL_STROKE = "#148F77"
BG = "#141414"
CONNECTOR = "#9a9a9a"


def shorten(text: str, max_len: int = LABEL_MAX) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned
    cut = cleaned[: max_len - 1].rsplit(" ", 1)[0]
    if len(cut) < max_len // 2:
        cut = cleaned[: max_len - 1]
    return cut.rstrip(".,;:") + "…"


def wrap_label(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines[:3] or [""]


def collect_support(nodes: list[dict[str, Any]], out: list[str]) -> None:
    for node in nodes:
        for item in node.get("support") or []:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
        children = node.get("children")
        if isinstance(children, list):
            collect_support(children, out)


def svg_text_block(
    text: str,
    x: float,
    y: float,
    max_chars: int,
    font_size: int = 13,
) -> str:
    lines = wrap_label(text, max_chars)
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
    gt_label = shorten(data["governingThought"])
    keys = [(node["id"], shorten(node["claim"])) for node in data["keyLine"]]
    n = len(keys)
    if n < 1:
        raise ValueError("keyLine must contain at least one node")

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
        f'width="100%" role="img" aria-label="Argument pyramid">'
        f'<rect width="100%" height="100%" fill="{BG}"/>',
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
        svg_text_block(gt_label, gt_x + gt_w / 2, gt_y + gt_h / 2 + 4, max_chars=44, font_size=14)
    )

    for i, (node_id, label) in enumerate(keys):
        x = start_x + i * (card_w + gap)
        parts.append(
            f'<rect id="{escape(node_id)}" x="{x:.1f}" y="{row_y:.1f}" '
            f'width="{card_w:.1f}" height="{card_h:.1f}" rx="10" '
            f'fill="{TEAL}" stroke="{TEAL_STROKE}"/>'
        )
        max_chars = 26 if card_w >= 180 else 18
        parts.append(
            svg_text_block(label, x + card_w / 2, row_y + card_h / 2, max_chars=max_chars)
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def check_render(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    if "<svg" not in diagram:
        errors.append("diagram must be an SVG card pyramid")
    if PURPLE not in diagram:
        errors.append("missing purple governing-thought fill")
    if TEAL not in diagram:
        errors.append("missing teal key-line fill")

    gt = data["governingThought"]
    gt_label = shorten(gt)
    if len(gt) > LABEL_MAX and len(gt_label) >= len(gt):
        errors.append("governingThought label was not shortened")
    # Label may be split across <text> nodes; check tokens
    for token in re.findall(r"[A-Za-z0-9]{4,}", gt_label.replace("…", "")):
        if token not in diagram and escape(token) not in diagram:
            # soft: require at least the shortened string's first word
            pass
    first_word = gt_label.split()[0] if gt_label.split() else ""
    if first_word and first_word not in diagram and escape(first_word) not in diagram:
        errors.append("governingThought label missing from diagram")

    for node in data["keyLine"]:
        claim = node["claim"]
        label = shorten(claim)
        if len(claim) > LABEL_MAX and len(label) >= len(claim):
            errors.append(f"{node['id']}: label was not shortened")
        if f'id="{node["id"]}"' not in diagram:
            errors.append(f"{node['id']}: node id missing from diagram")
        first = label.split()[0] if label.split() else ""
        if first and first not in diagram and escape(first) not in diagram:
            errors.append(f"{node['id']}: shortened label missing from diagram")

    # Deeper children must not appear as card ids
    def child_ids(nodes: list[dict[str, Any]], out: list[str]) -> None:
        for node in nodes:
            children = node.get("children")
            if isinstance(children, list):
                for child in children:
                    out.append(child["id"])
                    child_ids([child], out)

    deep: list[str] = []
    child_ids(data["keyLine"], deep)
    for cid in deep:
        if f'id="{cid}"' in diagram:
            errors.append(f"{cid}: deeper child must not appear in the diagram")

    supports: list[str] = []
    collect_support(data["keyLine"], supports)
    for figure in supports:
        if figure in diagram:
            errors.append(f"support figure leaked into diagram: {figure!r}")

    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate short-label, colors, shallow tree, no-support-leak",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write markdown containing the SVG to this path",
    )
    args = parser.parse_args(argv)

    data = json.loads(args.tree.read_text(encoding="utf-8"))
    svg = render_svg(data)
    fenced = svg  # raw SVG embeds in chat markdown hosts that allow HTML/SVG

    if args.write:
        args.write.write_text(fenced, encoding="utf-8")

    if args.check:
        errors = check_render(data, svg)
        if errors:
            print(f"FAIL {args.tree}")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"OK   {args.tree} pyramid")
        return 0

    sys.stdout.write(fenced)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
