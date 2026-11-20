# Analyze flags

A user pastes a memo whose claims are backed unevenly. The reply keeps every claim the author made, marks a claim backed by one anecdote `⚠ **Weak support.**`, marks a bare assertion `⚠ **Unsupported.**`, and leaves claims backed by a concrete, attributed figure unflagged.

## Sub-features

- `analyze-keep` keeps every planted claim as a leaf instead of cutting it or folding it into a parent.
- `analyze-weak` flags a claim backed by one named person's anecdote as Weak support.
- `analyze-unsupported` flags a claim with no backing as Unsupported.
- `analyze-supported` leaves a claim backed by a named figure unflagged.
- `analyze-no-invention` adds no figure or name the source lacks to any support line.

## How to get to it (user POV)

- Run `/make-the-point <memo text>` in Claude Code.
- Run `/make-the-point --debug <memo text>` to see the ArgumentTree JSON as well.

## Driving it with run.py

Preconditions:

- `run.py --doctor --ref <ref>` prints `doctor <ref>: OK`.
- `cases/mixed-memo.json` plants `41` + `escalation` and `186` as supported, `lisbon` as weak, and `churn` as unsupported.

- **Run the memo.** Run `.claude/skills/verify-make-the-point/scripts/run.py --ref <ref> --cases mixed-memo --repeat 3`. Each run line prints `valid=True`.
- **Keep.** Read the `mixed-memo` row. `kept` is `12/12`.
- **Flag by kind.** `status_ok` is `12/12`, and `gaps` is `6`, one weak and one unsupported flag per run.
- **No invention.** `invented` is `0`, or each hit in `score.json` is a sentence-initial word, not a figure or name.
- **Proof.** Open `<evidence>/<ref-slug>/mixed-memo/1/reply.txt`. The Lisbon claim ends with a `⚠ **Weak support.**` line after its `↳` line, and the churn claim has a `⚠ **Unsupported.**` line and no `↳` line.

## Gotchas

- A planted supported claim must say no more than its figure shows. "The night shift is where we lose the most" over a 41% figure is a fair Weak support flag, not an over-flag. Fix the case, not the scorer.
- The model may split one planted claim across two leaves. `got` in `score.json` then lists two statuses, and `status_ok` counts the claim when any of them matches.
- With `--no-shell` the tree is written by hand. Expect more `valid=False` runs, and read `error` in `score.json` before blaming the skill.
