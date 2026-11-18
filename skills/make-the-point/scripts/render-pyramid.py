#!/usr/bin/env python3
"""Render an ArgumentTree as a Mermaid flowchart pyramid (short labels).

Usage:
  python3 scripts/render-pyramid.py <tree.json>
  python3 scripts/render-pyramid.py <tree.json> --check

--check exits 0 only when every diagram label is strictly shorter than its
source claim when the claim exceeds LABEL_MAX, no support figure appears in
the diagram text, and every node id is present.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

LABEL_MAX = 40


def shorten(text: str, max_len: int = LABEL_MAX) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned
    cut = cleaned[: max_len - 1].rsplit(" ", 1)[0]
    if len(cut) < max_len // 2:
        cut = cleaned[: max_len - 1]
    return cut.rstrip(".,;:") + "…"


def mermaid_id(node_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", node_id)
    if not safe or safe[0].isdigit():
        safe = "n_" + safe
    return safe


def escape_label(text: str) -> str:
    return text.replace('"', "#quot;")


def walk_nodes(nodes: list[dict[str, Any]], out: list[dict[str, str]]) -> None:
    for node in nodes:
        out.append({"id": node["id"], "claim": node["claim"]})
        children = node.get("children")
        if isinstance(children, list):
            walk_nodes(children, out)


def collect_support(nodes: list[dict[str, Any]], out: list[str]) -> None:
    for node in nodes:
        for item in node.get("support") or []:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
        children = node.get("children")
        if isinstance(children, list):
            collect_support(children, out)


def edges_from_tree(data: dict[str, Any]) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    gt = "GT"

    def walk(parent: str, nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            nid = mermaid_id(node["id"])
            edges.append((parent, nid))
            children = node.get("children")
            if isinstance(children, list):
                walk(nid, children)

    walk(gt, data["keyLine"])
    return edges


def render_mermaid(data: dict[str, Any]) -> str:
    lines = ["flowchart TB"]
    gt_label = escape_label(shorten(data["governingThought"]))
    lines.append(f'  GT["{gt_label}"]')

    nodes: list[dict[str, str]] = []
    walk_nodes(data["keyLine"], nodes)
    for node in nodes:
        nid = mermaid_id(node["id"])
        label = escape_label(shorten(node["claim"]))
        lines.append(f'  {nid}["{label}"]')

    for parent, child in edges_from_tree(data):
        lines.append(f"  {parent} --> {child}")

    return "\n".join(lines) + "\n"


def check_render(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    gt = data["governingThought"]
    gt_label = shorten(gt)
    if len(gt) > LABEL_MAX and len(gt_label) >= len(gt):
        errors.append("governingThought label was not shortened")
    if gt_label not in diagram and escape_label(gt_label) not in diagram:
        errors.append("governingThought label missing from diagram")

    nodes: list[dict[str, str]] = []
    walk_nodes(data["keyLine"], nodes)
    for node in nodes:
        claim = node["claim"]
        label = shorten(claim)
        if len(claim) > LABEL_MAX and len(label) >= len(claim):
            errors.append(f"{node['id']}: label was not shortened")
        if mermaid_id(node["id"]) not in diagram:
            errors.append(f"{node['id']}: node id missing from diagram")
        if label not in diagram and escape_label(label) not in diagram:
            errors.append(f"{node['id']}: shortened label missing from diagram")

    supports: list[str] = []
    collect_support(data["keyLine"], supports)
    for figure in supports:
        if figure in diagram:
            errors.append(f"support figure leaked into diagram: {figure!r}")

    if "flowchart TB" not in diagram:
        errors.append("diagram must be a Mermaid flowchart TB pyramid")
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate short-label and no-support-leak rules",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write fenced Mermaid markdown to this path",
    )
    args = parser.parse_args(argv)

    data = json.loads(args.tree.read_text(encoding="utf-8"))
    body = render_mermaid(data)
    fenced = f"```mermaid\n{body}```\n"

    if args.write:
        args.write.write_text(fenced, encoding="utf-8")

    if args.check:
        errors = check_render(data, body)
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
