#!/usr/bin/env python3
"""Validate an ArgumentTree JSON file against make-the-point structural rules.

Usage:
  python3 scripts/validate-tree.py <tree.json> [<tree.json> ...]
  python3 scripts/validate-tree.py --self-test
  python3 scripts/validate-tree.py --fixtures

Normal mode exits 0 only when every file passes. --self-test exits 0 when packaged
fixtures match expected pass/fail, the example and the SKILL.md template match
the renderer, the wide and deep fixtures pass --check, and renders of 1 to 12
key-line claims pass --check.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
ROLES = frozenset({"reason", "evidence", "example", "rebuttal"})
MODES = frozenset({"analyze", "construct"})
KINDS = frozenset({"text", "link", "image"})
LOGICS = frozenset({"inductive", "deductive"})


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def require_str(errors: list[str], obj: dict[str, Any], key: str, path: str) -> str | None:
    if key not in obj:
        fail(errors, f"{path}: missing '{key}'")
        return None
    val = obj[key]
    if not isinstance(val, str) or not val.strip():
        fail(errors, f"{path}.{key}: must be a non-empty string")
        return None
    return val


def walk_node(
    node: Any,
    path: str,
    errors: list[str],
    seen_ids: set[str],
) -> None:
    if not isinstance(node, dict):
        fail(errors, f"{path}: must be an object")
        return

    node_id = require_str(errors, node, "id", path)
    if node_id is not None:
        if not ID_RE.match(node_id):
            fail(errors, f"{path}.id: invalid id '{node_id}'")
        if node_id in seen_ids:
            fail(errors, f"{path}.id: duplicate id '{node_id}'")
        else:
            seen_ids.add(node_id)

    require_str(errors, node, "claim", path)

    role = node.get("role")
    if role not in ROLES:
        fail(errors, f"{path}.role: must be one of {sorted(ROLES)}")

    unknown = set(node) - {"id", "claim", "role", "children", "support"}
    if unknown:
        fail(errors, f"{path}: unexpected keys {sorted(unknown)}")

    children = node.get("children")
    support = node.get("support")

    if children is not None:
        if not isinstance(children, list) or len(children) < 1:
            fail(errors, f"{path}.children: must be a non-empty array when present")
        else:
            for i, child in enumerate(children):
                walk_node(child, f"{path}.children[{i}]", errors, seen_ids)

    if support is not None:
        if not isinstance(support, list):
            fail(errors, f"{path}.support: must be an array")
        else:
            for i, item in enumerate(support):
                if not isinstance(item, str) or not item.strip():
                    fail(errors, f"{path}.support[{i}]: must be a non-empty string")

    if children is None and support is None:
        fail(errors, f"{path}: leaf needs 'support' or non-leaf needs 'children'")


def validate_tree(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root: must be an object"]

    if data.get("version") != 1:
        fail(errors, "version: must be 1")

    mode = data.get("mode")
    if mode not in MODES:
        fail(errors, f"mode: must be one of {sorted(MODES)}")

    source = data.get("source")
    if not isinstance(source, dict):
        fail(errors, "source: must be an object")
    else:
        if source.get("kind") not in KINDS:
            fail(errors, f"source.kind: must be one of {sorted(KINDS)}")
        unknown = set(source) - {"kind", "ref", "excerpt"}
        if unknown:
            fail(errors, f"source: unexpected keys {sorted(unknown)}")
        for key in ("ref", "excerpt"):
            if key in source and (not isinstance(source[key], str) or not source[key].strip()):
                fail(errors, f"source.{key}: must be a non-empty string when present")

    scqa = data.get("scqa")
    if not isinstance(scqa, dict):
        fail(errors, "scqa: must be an object")
        situation = complication = question = answer = None
    else:
        unknown = set(scqa) - {"situation", "complication", "question", "answer"}
        if unknown:
            fail(errors, f"scqa: unexpected keys {sorted(unknown)}")
        situation = require_str(errors, scqa, "situation", "scqa")
        complication = require_str(errors, scqa, "complication", "scqa")
        question = require_str(errors, scqa, "question", "scqa")
        answer = require_str(errors, scqa, "answer", "scqa")

    governing = require_str(errors, data, "governingThought", "root")
    if governing is not None and answer is not None and governing.strip() != answer.strip():
        fail(errors, "governingThought must equal scqa.answer")

    logic = data.get("horizontalLogic")
    if logic not in LOGICS:
        fail(errors, f"horizontalLogic: must be one of {sorted(LOGICS)}")

    key_line = data.get("keyLine")
    if not isinstance(key_line, list) or len(key_line) < 1:
        fail(errors, "keyLine: must be a non-empty array")
    else:
        seen_ids: set[str] = set()
        for i, node in enumerate(key_line):
            walk_node(node, f"keyLine[{i}]", errors, seen_ids)

    if "prose" in data:
        if not isinstance(data["prose"], str) or not data["prose"].strip():
            fail(errors, "prose: must be a non-empty string when present")

    if "notes" in data:
        notes = data["notes"]
        if not isinstance(notes, list):
            fail(errors, "notes: must be an array")
        else:
            for i, note in enumerate(notes):
                if not isinstance(note, str) or not note.strip():
                    fail(errors, f"notes[{i}]: must be a non-empty string")

    allowed = {
        "version",
        "mode",
        "source",
        "scqa",
        "governingThought",
        "horizontalLogic",
        "keyLine",
        "prose",
        "notes",
    }
    unknown_root = set(data) - allowed
    if unknown_root:
        fail(errors, f"root: unexpected keys {sorted(unknown_root)}")

    # Silence unused locals when scqa failed early
    _ = (situation, complication, question)
    return errors


def validate_file(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL {path}: {exc}")
        return 1
    errors = validate_tree(data)
    if errors:
        print(f"FAIL {path}")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"OK   {path}")
    return 0


def run_self_test() -> int:
    skill_dir = Path(__file__).resolve().parent.parent
    fixture_dir = skill_dir / "fixtures"
    cases = [
        (fixture_dir / "valid-analyze.json", True),
        (fixture_dir / "valid-wide-keyline.json", True),
        (fixture_dir / "valid-deep.json", True),
        (fixture_dir / "invalid-missing-support.json", False),
    ]
    failed = 0
    for path, should_pass in cases:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            errors = validate_tree(data)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL {path}: {exc}")
            failed += 1
            continue
        passed = not errors
        if passed == should_pass:
            expectation = "OK" if should_pass else "FAIL(expected)"
            print(f"{expectation:14} {path}")
        else:
            failed += 1
            print(f"UNEXPECTED    {path} (wanted pass={should_pass})")
            for err in errors:
                print(f"  - {err}")

    render = Path(__file__).resolve().parent / "render-pyramid.py"
    valid = fixture_dir / "valid-analyze.json"
    fixture_json = valid.read_text(encoding="utf-8").strip()
    failed += check_example(skill_dir / "examples" / "valid-analyze-markdown.md", valid, render, fixture_json)

    wide = fixture_dir / "valid-wide-keyline.json"
    deep = fixture_dir / "valid-deep.json"
    for tree in (wide, deep):
        check = subprocess.run(
            [sys.executable, str(render), str(tree), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )
        sys.stdout.write(check.stdout)
        sys.stderr.write(check.stderr)
        if check.returncode != 0:
            failed += 1

    failed += check_key_line_counts(render, wide)
    failed += check_skill_template(skill_dir / "SKILL.md", valid, render)
    return 1 if failed else 0


def check_skill_template(skill: Path, valid: Path, render: Path) -> int:
    """Hosts without a shell copy this fence by hand, so it must match the renderer byte for byte."""
    match = re.search(r"```markdown\n(.*?\n)```", skill.read_text(encoding="utf-8"), re.DOTALL)
    drawn = subprocess.run([sys.executable, str(render), str(valid)], check=False, capture_output=True, text=True)
    if match is None:
        print(f"FAIL {skill}: missing markdown fence")
        return 1
    if match.group(1) != drawn.stdout:
        print(f"FAIL {skill}: markdown fence does not match renderer output for {valid.name}")
        diff = difflib.unified_diff(
            drawn.stdout.splitlines(True), match.group(1).splitlines(True), fromfile="renderer", tofile=skill.name
        )
        sys.stdout.writelines(diff)
        return 1
    print(f"{'OK':14} {skill} template")
    return 0


def check_key_line_counts(render: Path, wide: Path, counts: range = range(1, 13)) -> int:
    base = json.loads(wide.read_text(encoding="utf-8"))
    claims = base["keyLine"]
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for n in counts:
            key_line = [dict(claims[i % len(claims)], id=f"K{i + 1}") for i in range(n)]
            tree = Path(tmp) / f"n{n}.json"
            tree.write_text(json.dumps(dict(base, keyLine=key_line)), encoding="utf-8")
            check = subprocess.run(
                [sys.executable, str(render), str(tree), "--check"], check=False, capture_output=True, text=True
            )
            if check.returncode != 0:
                failed += 1
                print(f"FAIL n={n}")
                sys.stdout.write(check.stdout)
                sys.stderr.write(check.stderr)
    cases = len(counts)
    print(f"{'OK' if not failed else 'FAIL':14} key-line counts {counts.start}-{counts.stop - 1}: {cases - failed}/{cases} renders pass --check")
    return failed


def diagram_section(text: str) -> str | None:
    marker = "## Pyramid diagram"
    nxt = "## ArgumentTree JSON"
    if marker not in text or nxt not in text:
        return None
    return text.split(marker, 1)[1].split(nxt, 1)[0].strip()


def fenced_json(text: str) -> str | None:
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    return match.group(1) if match else None


def diagram_errors(diagram: str) -> list[str]:
    errors: list[str] = []
    if not diagram.startswith("> ### ") or "↳ *" not in diagram:
        errors.append("diagram must be a quoted heading over a nested bullet tree")
    if "```" in diagram:
        errors.append("example diagram must not include fences")
    return errors


def check_example(
    example: Path,
    valid: Path,
    render: Path,
    fixture_json: str,
) -> int:
    check = subprocess.run(
        [sys.executable, str(render), str(valid), "--check"],
        check=False,
        capture_output=True,
        text=True,
    )
    sys.stdout.write(check.stdout)
    sys.stderr.write(check.stderr)
    if check.returncode != 0:
        return 1

    drawn = subprocess.run(
        [sys.executable, str(render), str(valid)],
        check=False,
        capture_output=True,
        text=True,
    )
    if drawn.returncode != 0:
        print("FAIL renderer")
        sys.stdout.write(drawn.stdout)
        sys.stderr.write(drawn.stderr)
        return 1
    if not example.is_file():
        print(f"FAIL missing example {example}")
        return 1

    text = example.read_text(encoding="utf-8")
    diagram = diagram_section(text)
    payload = fenced_json(text)
    errors: list[str] = []
    if diagram is None:
        errors.append("missing pyramid diagram section")
    elif diagram != drawn.stdout.strip():
        errors.append("diagram does not match renderer output")
    if payload is None:
        errors.append("missing json fence")
    elif payload.strip() != fixture_json:
        errors.append("JSON does not match the valid fixture")
    if diagram is not None:
        errors.extend(diagram_errors(diagram))
    if errors:
        print(f"FAIL {example}")
        for err in errors:
            print(f"  - {err}")
        if diagram is not None and diagram != drawn.stdout.strip():
            diff = difflib.unified_diff(
                drawn.stdout.strip().splitlines(True),
                diagram.splitlines(True),
                fromfile="renderer",
                tofile=example.name,
            )
            sys.stdout.writelines(diff)
        return 1
    print(f"OK             {example}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Validate all *.json under ../fixtures (every file must pass)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Check fixtures, the example, the SKILL.md template, and --check across 1 to 12 key-line claims",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    paths: list[Path] = list(args.paths)
    if args.fixtures:
        fixture_dir = Path(__file__).resolve().parent.parent / "fixtures"
        paths.extend(sorted(fixture_dir.glob("*.json")))

    if not paths:
        parser.error("pass tree JSON paths, --fixtures, or --self-test")

    return 1 if any(validate_file(p) for p in paths) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
