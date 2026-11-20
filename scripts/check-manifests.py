#!/usr/bin/env python3
"""Check that every plugin manifest and marketplace catalog describes one release.

Usage:
  python3 scripts/check-manifests.py [--tag vX.Y.Z]
  python3 scripts/check-manifests.py --set-version X.Y.Z

Exits 0 when all versions are equal and valid semver (the SKILL.md version lines,
the example's plugin line and each catalog's pinned "vX.Y.Z" ref included),
shared fields agree, every catalog entry pins a release of the repository the
manifests name, and the optional tag equals "v" + version.

--set-version writes X.Y.Z into every one of those version sources, then runs
the check with tag vX.Y.Z.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
SHARED = ("name", "version", "description", "repository")
MISSING = object()


class Manifest(NamedTuple):
    path: str
    fields: tuple[str, ...]


class Catalog(NamedTuple):
    path: str
    fields: tuple[str, ...]
    ref: tuple[str, ...]
    repo: tuple[str, ...]
    repo_url: str


class TextSource(NamedTuple):
    path: str
    pattern: re.Pattern[str]


MANIFESTS = (
    Manifest("plugin.json", ("name", "version", "description", "repository")),
    Manifest(".claude-plugin/plugin.json", ("name", "version", "description", "repository")),
    Manifest(".cursor-plugin/plugin.json", ("name", "version", "description", "repository")),
)

CATALOGS = (
    Catalog(
        ".claude-plugin/marketplace.json",
        ("name", "source"),
        ref=("source", "ref"),
        repo=("source", "repo"),
        repo_url="https://github.com/{}",
    ),
    Catalog(
        ".agents/plugins/marketplace.json",
        ("name", "source", "policy", "category"),
        ref=("source", "ref"),
        repo=("source", "url"),
        repo_url="{}",
    ),
)

TEXT_SOURCES = (
    TextSource("skills/make-the-point/SKILL.md", re.compile(r"^This is make-the-point (\S+)\.$", re.MULTILINE)),
    TextSource("skills/make-the-point/SKILL.md", re.compile(r"`make-the-point (\S+), loaded from ")),
    TextSource(
        "skills/make-the-point/examples/valid-flagged-markdown.md",
        re.compile(r"^Plugin: make-the-point (\S+)$", re.MULTILINE),
    ),
)


def dig(obj: Any, keys: tuple[str, ...]) -> Any:
    for key in keys:
        if not isinstance(obj, dict) or key not in obj:
            return MISSING
        obj = obj[key]
    return obj


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


def dump(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def entries(catalog: Catalog, data: dict[str, Any], errors: list[str]) -> list[tuple[str, dict[str, Any]]]:
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{catalog.path}: 'plugins' must be a non-empty array")
        return []
    found = []
    for i, entry in enumerate(plugins):
        where = f"{catalog.path} plugins[{i}]"
        if isinstance(entry, dict):
            found.append((where, entry))
        else:
            errors.append(f"{where}: must be an object")
    return found


def shown(value: Any) -> str:
    return "nothing" if value is MISSING else repr(value)


def normalize_repo(url: Any) -> Any:
    return url.removesuffix(".git").rstrip("/") if isinstance(url, str) else url


def pinned_version(catalog: Catalog, where: str, entry: dict[str, Any], errors: list[str]) -> Any:
    ref = dig(entry, catalog.ref)
    if not isinstance(ref, str) or not ref.startswith("v"):
        errors.append(f"{where}: {'.'.join(catalog.ref)} must pin a release tag 'vX.Y.Z', got {shown(ref)}")
        return MISSING
    return ref[1:]


def check_repo(catalog: Catalog, where: str, entry: dict[str, Any], repository: Any, errors: list[str]) -> None:
    repo = dig(entry, catalog.repo)
    if not isinstance(repo, str):
        errors.append(f"{where}: {'.'.join(catalog.repo)} must name the repository, got {shown(repo)}")
        return
    url = normalize_repo(catalog.repo_url.format(repo))
    if url != normalize_repo(repository):
        errors.append(f"{where}: source {repo!r} is not this repository {repository!r}")


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

    repository = seen["repository"][0][1] if seen["repository"] else None
    for catalog in CATALOGS:
        data = load(catalog.path, errors)
        if data is None:
            continue
        for where, entry in entries(catalog, data, errors):
            record(where, entry, catalog.fields)
            version = pinned_version(catalog, where, entry, errors)
            if version is not MISSING:
                seen["version"].append((f"{where} {'.'.join(catalog.ref)}", version))
            check_repo(catalog, where, entry, repository, errors)

    for text in TEXT_SOURCES:
        try:
            versions = text.pattern.findall((ROOT / text.path).read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"{text.path}: {exc}")
            continue
        if not versions:
            errors.append(f"{text.path}: no version line matching /{text.pattern.pattern}/")
        seen["version"].extend((text.path, version) for version in versions)
    return seen


def check(tag: str | None) -> list[str]:
    errors: list[str] = []
    seen = collect(errors)

    for field, values in seen.items():
        if len({json.dumps(v, sort_keys=True) for _, v in values}) > 1:
            listing = "\n".join(f"    {where}: {value!r}" for where, value in values)
            errors.append(f"'{field}' disagrees across files:\n{listing}")

    versions = list({json.dumps(v, sort_keys=True): v for _, v in seen["version"]}.values())
    for version in versions:
        if not isinstance(version, str) or not SEMVER.match(version):
            errors.append(f"version {version!r} is not valid semver")

    if tag is not None:
        if len(versions) != 1:
            errors.append(f"tag {tag} cannot match: files carry {len(versions)} versions")
        else:
            expected = f"v{next(iter(versions))}"
            if tag != expected:
                errors.append(f"tag {tag} does not match manifest version, expected {expected}")
    return errors


def rewrite(version: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    texts: dict[str, str] = {}

    def text_of(path: str) -> str:
        if path not in texts:
            texts[path] = (ROOT / path).read_text(encoding="utf-8")
        return texts[path]

    for manifest in MANIFESTS:
        data = load(manifest.path, errors)
        if data is not None:
            data["version"] = version
            texts[manifest.path] = dump(data)

    for catalog in CATALOGS:
        data = load(catalog.path, errors)
        if data is None:
            continue
        for where, entry in entries(catalog, data, errors):
            *parents, key = catalog.ref
            holder = dig(entry, tuple(parents))
            if not isinstance(holder, dict):
                errors.append(f"{where}: no {'.'.join(parents)} object to hold the ref")
                continue
            holder[key] = f"v{version}"
        texts[catalog.path] = dump(data)

    for text in TEXT_SOURCES:
        try:
            content = text_of(text.path)
        except OSError as exc:
            errors.append(f"{text.path}: {exc}")
            continue
        content, count = text.pattern.subn(
            lambda m: m.string[m.start() : m.start(1)] + version + m.string[m.end(1) : m.end()],
            content,
        )
        if not count:
            errors.append(f"{text.path}: no version line matching /{text.pattern.pattern}/")
        texts[text.path] = content

    if errors:
        return errors, []
    changed = []
    for path, content in texts.items():
        if (ROOT / path).read_text(encoding="utf-8") != content:
            (ROOT / path).write_text(content, encoding="utf-8")
            changed.append(path)
    return errors, changed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tag", help="release tag that must equal 'v' + the version in the files")
    group.add_argument("--set-version", metavar="X.Y.Z", help="write X.Y.Z into every version source, then check")
    args = parser.parse_args(argv)

    tag = args.tag
    if args.set_version is not None:
        if not SEMVER.match(args.set_version):
            print(f"FAIL version {args.set_version!r} is not valid semver")
            return 1
        errors, changed = rewrite(args.set_version)
        if errors:
            for err in errors:
                print(f"FAIL {err}")
            return 1
        print(f"SET  version {args.set_version}: " + (", ".join(changed) if changed else "no changes"))
        tag = f"v{args.set_version}"

    errors = check(tag)
    if errors:
        for err in errors:
            print(f"FAIL {err}")
        return 1
    version = json.loads((ROOT / MANIFESTS[0].path).read_text(encoding="utf-8"))["version"]
    names = ", ".join(dict.fromkeys(s.path for s in MANIFESTS + CATALOGS + TEXT_SOURCES))
    suffix = f", tag {tag}" if tag else ""
    print(f"OK   version {version}{suffix}: {names}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
