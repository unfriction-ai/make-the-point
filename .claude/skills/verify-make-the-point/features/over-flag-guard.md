# Over-flag guard

A user pastes a memo where every claim cites a concrete figure with a named origin. The reply flags nothing, so a reader learns to trust a flag when one appears.

## Sub-features

- `guard-none` writes no evidenceGap anywhere in the tree.
- `guard-kept` keeps every attributed claim as a leaf with its support.

## How to get to it (user POV)

- Run `/make-the-point <well-sourced memo>` in Claude Code.
- Run `/make-the-point --debug <well-sourced memo>` to see the JSON as well.

## Driving it with run.py

Preconditions:

- `run.py --doctor --ref <ref>` prints `doctor <ref>: OK`.
- `cases/sourced-memo.json` sets `expectNoFlags: true` and plants `38` + `52`, `c7g`, and `212` as supported.

- **Run the memo.** Run `.claude/skills/verify-make-the-point/scripts/run.py --ref <ref> --cases sourced-memo --repeat 3`. Each run line prints `valid=True`.
- **No flags.** The `sourced-memo` row shows `overflag` `0` and `gaps` `0`.
- **Kept with support.** `kept` and `status_ok` are `9/9`.
- **Proof.** `grep -c '⚠' <evidence>/<ref-slug>/sourced-memo/*/reply.txt` prints `0` for every run.

## Gotchas

- Doubts about the whole memo, such as a missing cost of migration, belong in `notes` and are not over-flags. Only an evidenceGap counts.
- One clean run says little about the over-flag rate. Use `--repeat 3` or more before claiming the guard holds.
- Run this with `mixed-memo` in the same call when checking a change. A ref that never flags passes this guard and fails Analyze flags.
