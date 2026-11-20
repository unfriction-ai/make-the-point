# make-the-point verification map

This directory is the maintained source for verifying what a `/make-the-point` user sees when a source backs some claims well, some thinly, and some not at all. Read the index before driving, then use the matching feature file as the recipe.

## Baseline preconditions

- `claude`, `python3`, `git`, and `tar` are on `PATH`, and `claude -p` is logged in.
- The ref under check exists locally. `git rev-parse <ref>` prints a SHA.
- `run.py --doctor --ref <ref>` prints `doctor <ref>: OK`.
- Never drive the plugin from this checkout or from a cwd inside the repo. Use only the copies `run.py` builds.

## Driving conventions

- Drive through `run.py`, which sends `/make-the-point:make-the-point --debug <source>` from a scratch cwd.
- Keep case sources organic. A source that asks for flags measures obedience, not judgment.
- Treat each command as literal. Run from the repository root.
- Compare refs in one `run.py` call with two `--ref` flags.

## Proof and skip reporting

- Cite the summary table and the evidence directory `run.py` prints.
- Name the case, ref, model, and repeat count with every number.
- Read `reply.txt` for any run whose score surprises you before reporting it.
- Read every `invented` hit and say whether it is a real invention or a false positive.
- A rate claim, such as "never over-flags", needs `--repeat 3` or more.
- Report an unreachable path with the attempted command and the unmet precondition.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with run.py` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

## Features

- [Analyze flags](./analyze-flags.md) covers keeping and flagging thin or unbacked claims in a source.
- [Construct flags](./construct-flags.md) covers flagging the evidence a user still has to find, with no invented support.
- [Over-flag guard](./over-flag-guard.md) covers leaving well-sourced claims unflagged.
- [Caveats rendering](./caveats-rendering.md) covers the diagram's flag lines and Caveats list matching the tree.
