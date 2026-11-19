#!/usr/bin/env python3
"""Check that every plugin manifest and marketplace catalog describes one release.

Usage:
  python3 scripts/check-manifests.py [--tag vX.Y.Z]

Exits 0 when all versions are equal and valid semver, shared fields agree, every
catalog entry points at a directory that holds the manifest its host reads, and
the optional tag equals "v" + version.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, NamedTuple

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
SHARED = ("name", "version", "description", "repository")


class Manifest(NamedTuple):
    path: str
    fields: tuple[str, ...]


class Catalog(NamedTuple):
    path: str
    fields: tuple[str, ...]
    source: Callable[[dict[str, Any]], Any]
    manifest: str


MANIFESTS = (
    Manifest("plugin.json", ("name", "version", "description", "repository")),
    Manifest(".claude-plugin/plugin.json", ("name", "version", "description", "repository")),
    Manifest(".cursor-plugin/plugin.json", ("name", "version", "description", "repository")),
)

CATALOGS = (
    Catalog(".claude-plugin/marketplace.json", ("name", "source"), lambda e: e.get("source"), ".claude-plugin/plugin.json"),
    Catalog(
        ".agents/plugins/marketplace.json",
        ("name", "source", "policy", "category"),
        lambda e: (e.get("source") or {}).get("path"),
        "plugin.json",
    ),
)


def load(path: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        data = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: must be a JSON object")
        return None
    return data


def check_source(catalog: Catalog, where: str, entry: dict[str, Any], errors: list[str]) -> None:
    source = catalog.source(entry)
    if not isinstance(source, str) or not source.startswith("./"):
        errors.append(f"{where}: source path must be a string starting with './', got {source!r}")
        return
    target = (ROOT / source).resolve()
    if target != ROOT and ROOT not in target.parents:
        errors.append(f"{where}: source path {source!r} leaves the repository root")
    elif not (target / catalog.manifest).is_file():
        errors.append(f"{where}: source path {source!r} has no {catalog.manifest}")


def collect(errors: list[str]) -> dict[str, list[tuple[str, Any]]]:
    seen: dict[str, list[tuple[str, Any]]] = {field: [] for field in SHARED}

    def record(where: str, obj: dict[str, Any], required: tuple[str, ...]) -> None:
        for field in required:
            if field not in obj:
                errors.append(f"{where}: missing '{field}'")
        for field in SHARED:
            if field in obj:
                seen[field].append((where, obj[field]))

    for manifest in MANIFESTS:
        data = load(manifest.path, errors)
        if data is not None:
            record(manifest.path, data, manifest.fields)

    for catalog in CATALOGS:
        data = load(catalog.path, errors)
        if data is None:
            continue
        entries = data.get("plugins")
        if not isinstance(entries, list) or not entries:
            errors.append(f"{catalog.path}: 'plugins' must be a non-empty array")
            continue
        for i, entry in enumerate(entries):
            where = f"{catalog.path} plugins[{i}]"
            if not isinstance(entry, dict):
                errors.append(f"{where}: must be an object")
                continue
            record(where, entry, catalog.fields)
            check_source(catalog, where, entry, errors)
    return seen


def check(tag: str | None) -> list[str]:
    errors: list[str] = []
    seen = collect(errors)

    for field, values in seen.items():
        if len({json.dumps(v, sort_keys=True) for _, v in values}) > 1:
            listing = "\n".join(f"    {where}: {value!r}" for where, value in values)
            errors.append(f"'{field}' disagrees across manifests:\n{listing}")

    versions = {v for _, v in seen["version"]}
    for version in versions:
        if not isinstance(version, str) or not SEMVER.match(version):
            errors.append(f"version {version!r} is not valid semver")

    if tag is not None:
        if len(versions) != 1:
            errors.append(f"tag {tag} cannot match: manifests carry {len(versions)} versions")
        else:
            expected = f"v{next(iter(versions))}"
            if tag != expected:
                errors.append(f"tag {tag} does not match manifest version, expected {expected}")
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tag", help="release tag that must equal 'v' + the manifest version")
    args = parser.parse_args(argv)

    errors = check(args.tag)
    if errors:
        for err in errors:
            print(f"FAIL {err}")
        return 1
    version = json.loads((ROOT / MANIFESTS[0].path).read_text(encoding="utf-8"))["version"]
    names = ", ".join(m.path for m in MANIFESTS + CATALOGS)
    suffix = f", tag {args.tag}" if args.tag else ""
    print(f"OK   version {version}{suffix}: {names}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
