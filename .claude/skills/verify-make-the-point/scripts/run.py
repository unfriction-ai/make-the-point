#!/usr/bin/env python3
"""Drive /make-the-point headless on every case x ref x repeat and score each reply.

Usage:
  run.py --ref <git ref> [--ref <ref2>] [--cases all|<id>,...] [--repeat N] [--model sonnet] [--no-shell]
  run.py --doctor --ref <git ref>
  run.py --cleanup

Evidence goes to /tmp/verify-make-the-point/<UTC timestamp>/ and is never deleted.
Plugin copies and scratch cwds go under /tmp/notes-ws/<UTC timestamp>/ and are
removed when the run ends.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import REPO, score  # noqa: E402

SKILL = Path(__file__).resolve().parents[1]
EVIDENCE = Path("/tmp/verify-make-the-point")
# The model can see these paths, so they carry no word that says it is being measured.
WORK = Path("/tmp/notes-ws")
STAMP = re.compile(r"^\d{8}T\d{6}Z$")
PARALLEL = 4
TIMEOUT = 900


# -p mode denies every tool that has no allow rule, which leaves the skill no way to run its validator.
SHELL_TOOLS = ["--allowedTools", "Read", "Write", "Bash(mktemp:*)", "Bash(python3:*)"]


def claude(prompt: str, plugin: Path, cwd: Path, model: str, shell: bool) -> subprocess.CompletedProcess[str]:
    cmd = [
        "claude", "-p", prompt,
        "--plugin-dir", str(plugin),
        "--setting-sources", "",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--model", model,
        "--add-dir", str(plugin),
        *(SHELL_TOOLS if shell else []),
    ]
    cwd.mkdir(parents=True, exist_ok=True)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT, check=False)


def slug(ref: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", ref).strip("-")


def build_copy(ref: str, work: Path) -> Path:
    dest = work / f"plugin-{slug(ref)}"
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(REPO), "archive", ref], capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive.stdout, check=True)
    shutil.rmtree(dest / ".claude", ignore_errors=True)
    return dest


def doctor(ref: str, plugin: Path, work: Path, model: str, out: Path) -> bool:
    text = (plugin / "skills" / "make-the-point" / "SKILL.md").read_text(encoding="utf-8")
    version = re.search(r"This is make-the-point (\S+?)\.\n", text).group(1)
    proc = claude("/make-the-point:make-the-point --version", plugin, work / "desk-doctor", model, shell=False)
    reply = proc.stdout.strip()
    want = [f"make-the-point {version}, loaded from {p}/skills/make-the-point" for p in (plugin, plugin.resolve())]
    ok = proc.returncode == 0 and reply in want
    out.mkdir(parents=True, exist_ok=True)
    (out / "doctor.txt").write_text(f"ref: {ref}\nwant: {want[0]}\ngot:  {reply}\nstderr: {proc.stderr}\n", encoding="utf-8")
    print(f"doctor {ref}: {'OK' if ok else 'FAIL'}  {reply or proc.stderr.strip()}")
    return ok


def drive(job: dict[str, Any]) -> dict[str, Any]:
    out: Path = job["out"]
    out.mkdir(parents=True, exist_ok=True)
    case = job["case"]
    start = time.monotonic()
    try:
        proc = claude(f"/make-the-point:make-the-point --debug {case['source']}", job["plugin"], job["desk"], job["model"], job["shell"])
        reply, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        reply, stderr, code = exc.stdout or "", f"timed out after {TIMEOUT}s", -1
        reply = reply.decode() if isinstance(reply, bytes) else reply
    seconds = round(time.monotonic() - start, 1)
    (out / "reply.txt").write_text(reply, encoding="utf-8")
    (out / "stderr.txt").write_text(stderr, encoding="utf-8")
    result = score(case, reply, job["plugin"])
    result.update(ref=job["ref"], case=job["id"], repeat=job["repeat"], exit=code, seconds=seconds)
    (out / "score.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  {job['ref']} {job['id']} #{job['repeat']}: valid={result['valid']} kept={result['kept']} "
          f"status_ok={result['status_ok']} overflag={result['overflag']} invented={len(result['invented'])} "
          f"gaps={result['gaps']} ({seconds}s)", flush=True)
    return result


def ratio_sum(values: list[str]) -> str:
    pairs = [tuple(map(int, v.split("/"))) for v in values]
    return f"{sum(a for a, _ in pairs)}/{sum(b for _, b in pairs)}"


def summarize(results: list[dict[str, Any]], refs: list[str]) -> str:
    head = ("case", "runs", "valid", "mode_ok", "diagram_ok", "kept", "status_ok", "overflag", "invented", "gaps")
    lines = []
    for ref in refs:
        rows = [head]
        mine = [r for r in results if r["ref"] == ref]
        for case in sorted({r["case"] for r in mine}):
            rs = [r for r in mine if r["case"] == case]
            rows.append((
                case, str(len(rs)),
                *(f"{sum(r[k] for r in rs)}/{len(rs)}" for k in ("valid", "mode_ok", "diagram_ok")),
                ratio_sum([r["kept"] for r in rs]), ratio_sum([r["status_ok"] for r in rs]),
                str(sum(r["overflag"] for r in rs)), str(sum(len(r["invented"]) for r in rs)),
                str(sum(r["gaps"] for r in rs)),
            ))
        widths = [max(len(row[i]) for row in rows) for i in range(len(head))]
        lines.append(f"\n== {ref}")
        lines += ["  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip() for row in rows]
    return "\n".join(lines) + "\n"


def cleanup() -> None:
    for path in sorted(WORK.glob("*")):
        if path.is_dir() and STAMP.match(path.name):
            shutil.rmtree(path)
            print(f"removed {path}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", action="append", default=[], help="git ref to copy as the plugin; repeat to compare")
    parser.add_argument("--cases", default="all", help="all, or comma-separated case ids")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--no-shell", action="store_true", help="deny all tools, so the skill writes the tree by hand")
    parser.add_argument("--doctor", action="store_true", help="only check which copy loads for each ref")
    parser.add_argument("--cleanup", action="store_true", help="remove plugin copies and scratch cwds a crashed run left")
    args = parser.parse_args(argv)

    if args.cleanup:
        cleanup()
        return 0
    if not args.ref:
        parser.error("pass at least one --ref")

    case_files = sorted((SKILL / "cases").glob("*.json"))
    wanted = None if args.cases == "all" else set(args.cases.split(","))
    cases = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in case_files if wanted is None or p.stem in wanted}
    if wanted and wanted - set(cases):
        parser.error(f"unknown cases: {sorted(wanted - set(cases))}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence = EVIDENCE / stamp
    work = WORK / stamp
    evidence.mkdir(parents=True)
    print(f"evidence: {evidence}")
    try:
        plugins = {ref: build_copy(ref, work) for ref in args.ref}
        healthy = [doctor(ref, plugins[ref], work, args.model, evidence / slug(ref)) for ref in args.ref]
        if not all(healthy) or args.doctor:
            return 0 if all(healthy) else 1
        jobs = [
            {"ref": ref, "plugin": plugins[ref], "id": cid, "case": case, "repeat": n, "model": args.model,
             "shell": not args.no_shell, "desk": work / f"desk-{i}", "out": evidence / slug(ref) / cid / str(n)}
            for i, (ref, cid, case, n) in enumerate(
                (ref, cid, case, n) for ref in args.ref for cid, case in cases.items() for n in range(1, args.repeat + 1)
            )
        ]
        with concurrent.futures.ThreadPoolExecutor(PARALLEL) as pool:
            results = list(pool.map(drive, jobs))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    table = summarize(results, args.ref)
    (evidence / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (evidence / "summary.txt").write_text(table, encoding="utf-8")
    print(table + f"evidence: {evidence}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
