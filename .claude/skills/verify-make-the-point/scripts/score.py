#!/usr/bin/env python3
"""Score one /make-the-point --debug reply against a case file.

Usage:
  score.py <case.json> <reply.txt> [--plugin <plugin root>]

Prints one JSON object: valid, mode_ok, diagram_ok, kept, status_ok, overflag,
invented, gaps, and per-claim detail. --plugin picks whose validate-tree.py and
render-pyramid.py judge the reply; it defaults to this repository.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[4]
FENCE = re.compile(r"```json[ \t]*\n(.*?)\n```", re.DOTALL)
NAMED = re.compile(r"\d+(?:[.,]\d+)*|\b[A-Z][A-Za-z0-9]*(?:[-'][A-Za-z0-9]+)*")


def status(leaf: dict[str, Any]) -> str:
    """The label render-pyramid.py md_flag would draw, or supported when there is no flag."""
    if "evidenceGap" not in leaf:
        return "supported" if leaf.get("support") else "bare"
    return "weak" if leaf.get("support") else "unsupported"


def leaves(nodes: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for node in nodes:
        if node.get("children"):
            yield from leaves(node["children"])
        else:
            yield node


def leaf_text(leaf: dict[str, Any]) -> str:
    return " ".join([leaf.get("claim", ""), *(leaf.get("support") or []), leaf.get("evidenceGap", "")]).lower()


def extract(reply: str) -> tuple[str, dict[str, Any] | None, str | None]:
    """Split the reply into the diagram before the json fence and the parsed tree."""
    match = FENCE.search(reply)
    if match is None:
        return reply, None, "no ```json fence in reply"
    try:
        tree = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        return reply[: match.start()], None, f"json fence does not parse: {exc}"
    if not isinstance(tree, dict):
        return reply[: match.start()], None, "json fence is not an object"
    return reply[: match.start()], tree, None


def run_script(script: Path, tree: dict[str, Any], *flags: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "tree.json"
        path.write_text(json.dumps(tree), encoding="utf-8")
        return subprocess.run([sys.executable, str(script), str(path), *flags], capture_output=True, text=True, check=False)


def invented_support(tree: dict[str, Any], source: str) -> list[dict[str, str]]:
    found = []
    haystack = source.lower()
    for leaf in leaves(tree.get("keyLine") or []):
        for line in leaf.get("support") or []:
            missing = sorted({tok for tok in NAMED.findall(line) if tok.lower() not in haystack})
            if missing:
                found.append({"id": leaf.get("id", "?"), "support": line, "absent": ", ".join(missing)})
    return found


def score(case: dict[str, Any], reply: str, plugin: Path = REPO) -> dict[str, Any]:
    scripts = plugin / "skills" / "make-the-point" / "scripts"
    claims = case.get("claims", [])
    diagram, tree, error = extract(reply)
    result: dict[str, Any] = {
        "valid": False,
        "mode_ok": False,
        "diagram_ok": False,
        "kept": f"0/{len(claims)}",
        "status_ok": f"0/{len(claims)}",
        "overflag": 0,
        "invented": [],
        "gaps": 0,
        "claims": [],
    }
    if tree is None:
        result["error"] = error
        return result

    check = run_script(scripts / "validate-tree.py", tree)
    result["valid"] = check.returncode == 0
    if not result["valid"]:
        result["error"] = check.stdout.strip()
    result["mode_ok"] = tree.get("mode") == case["mode"]
    drawn = run_script(scripts / "render-pyramid.py", tree)
    result["diagram_ok"] = drawn.returncode == 0 and diagram.strip() == drawn.stdout.strip()

    all_leaves = list(leaves(tree.get("keyLine") or []))
    flagged = [leaf for leaf in all_leaves if "evidenceGap" in leaf]
    kept = status_ok = 0
    overflagged: set[str] = set()
    for claim in claims:
        hits = [leaf for leaf in all_leaves if all(tok in leaf_text(leaf) for tok in claim["match"])]
        got = [status(leaf) for leaf in hits]
        kept += bool(hits)
        status_ok += claim["expect"] in got
        if claim["expect"] == "supported":
            overflagged |= {leaf.get("id", "?") for leaf in hits if "evidenceGap" in leaf}
        result["claims"].append(
            {"match": claim["match"], "expect": claim["expect"], "got": got, "ids": [leaf.get("id") for leaf in hits]}
        )
    if case.get("expectNoFlags"):
        overflagged |= {leaf.get("id", "?") for leaf in flagged}

    result["kept"] = f"{kept}/{len(claims)}"
    result["status_ok"] = f"{status_ok}/{len(claims)}"
    result["overflag"] = len(overflagged)
    result["invented"] = invented_support(tree, case["source"])
    result["gaps"] = len(flagged)
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case", type=Path)
    parser.add_argument("reply", type=Path)
    parser.add_argument("--plugin", type=Path, default=REPO, help="plugin root whose scripts judge the reply")
    args = parser.parse_args(argv)
    case = json.loads(args.case.read_text(encoding="utf-8"))
    result = score(case, args.reply.read_text(encoding="utf-8"), args.plugin)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
