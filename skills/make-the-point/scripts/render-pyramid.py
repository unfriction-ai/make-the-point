#!/usr/bin/env python3
"""Render an ArgumentTree pyramid as a nested markdown tree.

The governing thought is a quoted heading. Each node is a bullet under its
parent, with each support line under its claim. The tree's notes follow as a
Caveats list. Every host gets this tree.

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
from pathlib import Path
from typing import Any


def md_escape(text: str) -> str:
    """Backslash-escape inline markdown so the text renders verbatim."""
    text = text.replace("\\", "\\\\")
    text = re.sub(r"([`*_\[\]<>|$~])", r"\\\1", text)
    text = re.sub(r"&(#?\w+;)", r"\\&\1", text)
    return re.sub(r":([a-z0-9_+-]+):", r"\\:\1:", text)


def md_escape_line(text: str) -> str:
    """md_escape, plus a leading heading or list marker escaped, for text that starts a line."""
    text = re.sub(r"^(#{1,6}|[-+])(?=\s|$)", r"\\\1", md_escape(text))
    return re.sub(r"^(\d{1,9})([.)])(?=\s|$)", r"\1\\\2", text)


def caveats(data: dict[str, Any]) -> list[str]:
    notes = data.get("notes") or []
    return ["", "**Caveats**", ""] + [f"- {md_escape_line(note)}" for note in notes] if notes else []


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
    return "\n".join(out + caveats(data)) + "\n"


def check_markdown(data: dict[str, Any], diagram: str) -> list[str]:
    errors: list[str] = []
    if not diagram.startswith(f"> ### {md_escape(data['governingThought'])}\n\n"):
        errors.append("diagram must open with the governing thought as a quoted heading")
    if re.search(r"(?<!\\)<[A-Za-z/!]", diagram):
        errors.append("diagram must not include raw HTML tags")
    if "```" in diagram:
        errors.append("diagram must not include code fences")
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
    block = "\n".join(caveats(data))
    tree, _, rest = diagram.partition("\n\n**Caveats**\n")
    if not diagram.endswith(block + "\n") or (not block and rest):
        errors.append("diagram must end with a Caveats list of every note, in order, exactly when the tree has notes")
    lines = tree.splitlines()
    arrows = [i for i, line in enumerate(lines) if line.lstrip().startswith("↳ ")]
    if len(arrows) != supports:
        errors.append(f"tree has {len(arrows)} support lines, want {supports}")
    for i in arrows:
        if not lines[i - 1].endswith("\\"):
            errors.append(f"line {i + 1}: support must follow a hard break")
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tree", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check the tree: heading, every claim, support line, and note, no HTML or fences",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write the tree to this path",
    )
    args = parser.parse_args(argv)

    data = json.loads(args.tree.read_text(encoding="utf-8"))
    diagram = render_markdown(data)

    if args.write:
        args.write.write_text(diagram, encoding="utf-8")

    if args.check:
        errors = check_markdown(data, diagram)
        if errors:
            print(f"FAIL {args.tree}")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"OK   {args.tree}")
        return 0

    if not args.write:
        sys.stdout.write(diagram)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
