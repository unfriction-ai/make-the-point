# Caveats rendering

The reply's diagram is the renderer's output for the reply's own tree. Flag lines sit inside their claim's bullet after its support, and the tree's notes follow as a **Caveats** list, so what the reader sees matches what the JSON says.

## Sub-features

- `render-match` makes the text before the `json` fence equal `render-pyramid.py` output for that fence.
- `render-flags` puts each `⚠` line after its claim's `↳` lines, with the right label.
- `render-caveats` ends the diagram with `**Caveats**` and one bullet per note, exactly when the tree has notes.

## How to get to it (user POV)

- Run `/make-the-point <source>` in Claude Code and read the reply.
- Run `/make-the-point --debug <source>` to read the diagram above its JSON.

## Driving it with run.py

Preconditions:

- `run.py --doctor --ref <ref>` prints `doctor <ref>: OK`.
- Any shipped case works. `mixed-memo` exercises both flag labels.

- **Run a case.** Run `.claude/skills/verify-make-the-point/scripts/run.py --ref <ref> --cases mixed-memo`. The run line prints `valid=True`.
- **Match.** The row shows `diagram_ok` `1/1`.
- **Inspect a mismatch.** When `diagram_ok` is `0`, save the fence as `tree.json` and run `python3 skills/make-the-point/scripts/render-pyramid.py tree.json > drawn.md`, then `diff` it against the reply text above the fence.
- **Structure.** Run `python3 skills/make-the-point/scripts/render-pyramid.py tree.json --check`. It prints `OK`.

## Gotchas

- A reply that opens with a status line before `> ### ` fails `diagram_ok` even when the tree is right. That is a real contract failure, since SKILL.md forbids it.
- `diagram_ok` compares stripped text, so a trailing newline difference does not fail it.
- Without `--debug` there is no fence to compare against. The harness always sends `--debug`.
