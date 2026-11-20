# Construct flags

A user asks for help building a case and offers one hard fact and one anecdote. The reply builds the argument the decision needs, backs the fact, marks the anecdote Weak support, marks every claim the user has no evidence for Unsupported with the evidence still to find, and never makes up a figure or source to fill a gap.

## Sub-features

- `construct-mode` reports `mode: construct` for a request to build a case.
- `construct-fact` backs the user's concrete figure without a flag.
- `construct-weak` flags the user's anecdote as Weak support.
- `construct-needs` flags each claim the argument needs but the user did not back, naming the evidence to find.
- `construct-no-invention` adds no figure or name the ask lacks to any support line.

## How to get to it (user POV)

- Run `/make-the-point <request to build a case>` in Claude Code.
- Run `/make-the-point --debug <request to build a case>` to see the JSON as well.

## Driving it with run.py

Preconditions:

- `run.py --doctor --ref <ref>` prints `doctor <ref>: OK`.
- `cases/thin-ask.json` plants `310` + `190` as supported and `dmitri` as weak.

- **Run the ask.** Run `.claude/skills/verify-make-the-point/scripts/run.py --ref <ref> --cases thin-ask --repeat 3`. Each run line prints `valid=True`.
- **Mode.** The `thin-ask` row shows `mode_ok` `3/3`.
- **Fact and anecdote.** `kept` and `status_ok` are `6/6`.
- **No invention.** `invented` is `0`. Any hit that is a number or a proper noun is a failure of this feature.
- **Needs flagged.** `gaps` is at least `6`, the anecdote plus at least one claim the user still has to back per run. Read the extra evidenceGap lines in `reply.txt` and confirm each names evidence to find.

## Gotchas

- Construct mode adds its own claims, so the case lists only the two the user gave. Judge the rest by `invented` and by reading the flags.
- A support line that restates the user's figure in other units, such as "a 39% drop", trips `invented` because `39` is absent from the ask. Decide by reading it. A derived number is still support the user did not give.
- If the model picks analyze mode, every other number in the row is still scored, but the feature failed at `construct-mode`.
