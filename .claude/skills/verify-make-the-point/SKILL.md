---
name: verify-make-the-point
description: >-
  Verify the make-the-point plugin's /make-the-point skill by driving it headless
  with claude -p from a sanitized plugin copy of any git ref, then scoring each
  --debug reply. Proves it flags weak and unsupported claims with evidenceGap
  instead of cutting them or inventing support, and leaves well-sourced claims
  unflagged. Use after any change to skills/make-the-point/SKILL.md, pyramid.md,
  argument-tree.schema.json, or the scripts that could change model behavior,
  and to compare two refs.
---

# Verify make-the-point

The surface is the `/make-the-point:make-the-point` slash command in headless `claude -p`. Every run uses a plugin copy made from a git ref, a cwd outside this repo, and no settings, so no project skill, CLAUDE.md, or this harness reaches the model. The model sees the plugin copy path and the cwd, so neither carries a word such as eval, test, judge, score, or compare. `run.py` builds both under `/tmp/notes-ws/<UTC stamp>/`.

All commands run from the repository root. Scripts need only `python3`, `git`, `tar`, and `claude` on `PATH`.

## Launch

There is no server. Each drive is one short `claude -p` process. `run.py` makes one plugin copy per ref like this:

```bash
git archive <ref> | tar -x -C /tmp/notes-ws/<stamp>/plugin-<ref-slug>
rm -rf /tmp/notes-ws/<stamp>/plugin-<ref-slug>/.claude
```

Then it runs each case from its own scratch cwd `/tmp/notes-ws/<stamp>/desk-<n>`:

```bash
claude -p "/make-the-point:make-the-point --debug <source>" \
  --plugin-dir <plugin copy> --setting-sources "" --strict-mcp-config \
  --no-session-persistence --model sonnet --add-dir <plugin copy> \
  --allowedTools Read Write "Bash(mktemp:*)" "Bash(python3:*)"
```

The allow list exists because `-p` denies every tool with no allow rule. Without it the skill cannot run `validate-tree.py`, writes the tree by hand, and says so in its notes. `--no-shell` drops the allow list to drive that no-shell host path on purpose. A run is ready when the process exits. Expect 1 to 3 minutes per case.

## Doctor

```bash
.claude/skills/verify-make-the-point/scripts/run.py --doctor --ref <ref>
```

It sends `/make-the-point:make-the-point --version` to the copy and requires exactly `make-the-point <version>, loaded from <plugin copy>/skills/make-the-point`, with the version read from that copy's SKILL.md. That proves which copy loaded. Every full run does this first and stops if a ref fails. Exit 0 means healthy.

## Drive

```bash
.claude/skills/verify-make-the-point/scripts/run.py --ref <ref> [--ref <ref2>] \
  [--cases all|<id>,...] [--repeat N] [--model sonnet] [--no-shell]
```

Runs every case x ref x repeat, at most 4 at a time, then prints one summary table per ref. Cases live in `cases/<id>.json`:

- `mode`: `analyze` or `construct`, the mode the tree should report.
- `source`: the text after `--debug`. Write it like a real memo or ask. Never hint that flags are wanted.
- `claims`: planted claims. `match` is lowercase tokens, and a leaf matches when all of them appear in its claim, support, and evidenceGap text. Use distinctive entities so rewording does not break the match. `expect` is `supported` (support, no evidenceGap), `weak` (support and evidenceGap), or `unsupported` (evidenceGap, no support), the same split as `md_flag` in render-pyramid.py.
- `expectNoFlags: true` counts every evidenceGap in the tree as an over-flag.

Shipped cases are `mixed-memo` (analyze, 2 supported, 1 weak, 1 unsupported), `sourced-memo` (analyze, every claim attributed, `expectNoFlags`), and `thin-ask` (construct, one figure and one anecdote). The feature map in [features/README.md](features/README.md) says which case proves which behavior.

Score one saved reply alone:

```bash
.claude/skills/verify-make-the-point/scripts/score.py <case.json> <reply.txt> [--plugin <plugin root>]
```

`--plugin` picks whose `validate-tree.py` and `render-pyramid.py` judge the reply. It defaults to this checkout. `run.py` passes each ref's own copy.

## Evidence

Each run writes `/tmp/verify-make-the-point/<UTC stamp>/`:

- `<ref-slug>/doctor.txt` holds the wanted and actual `--version` line.
- `<ref-slug>/<case>/<repeat>/reply.txt` is the raw reply, `stderr.txt` its stderr, and `score.json` its score.
- `results.json` holds every score, and `summary.txt` holds the printed tables.

Score fields:

- `valid`: the reply's `json` fence passes validate-tree.py.
- `mode_ok`: the tree's `mode` equals the case's.
- `diagram_ok`: the reply text before the `json` fence equals render-pyramid.py's output for that tree, Caveats included.
- `kept`: planted claims found in some leaf, out of all planted claims.
- `status_ok`: planted claims with a matching leaf of the expected status.
- `overflag`: flagged leaves matching a `supported` claim, plus every flag when `expectNoFlags` is set.
- `invented`: support lines with a number or capitalized word absent from the source, case-insensitive, each with the absent tokens. Review each hit by eye. A sentence-initial word the source lacks is a false positive. A figure or name the source lacks is invented support.
- `gaps`: evidenceGap count.

A proof cites the summary table and the evidence path. A claim of no over-flagging needs `sourced-memo` with `--repeat` of at least 3, because one clean run proves little about a model's rate. To compare refs, pass both `--ref` flags in one run so they share a model and a time window.

## Cleanup

`run.py` deletes its `/tmp/notes-ws/<stamp>/` tree when it ends, pass or fail. After a crash or a Ctrl-C, run:

```bash
.claude/skills/verify-make-the-point/scripts/run.py --cleanup
```

It removes only `/tmp/notes-ws/<stamp>` directories whose name is a run stamp, so never run it while another run is active. It never touches `/tmp/verify-make-the-point/`, which is the evidence. Each `claude -p` exits on its own or at the 15 minute timeout, so there is no process to kill.

## Helpers

- `scripts/run.py` builds copies, runs the doctor, drives the cases, scores them, and cleans up. See Drive and Doctor.
- `scripts/score.py` scores one reply. See Drive.
