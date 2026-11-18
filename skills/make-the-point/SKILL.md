---
name: make-the-point
description: >-
  Understand, construct, and communicate the central argument in writing with the
  Minto Pyramid Principle. Accepts text, a link, or an image. Canonical output
  is one ArgumentTree JSON object. Reply with the host diagram of the governing
  thought and key line, then that JSON. Use ANSI boxes in a terminal, SVG cards
  on Claude Desktop, or a Mermaid flowchart in Markdown chat. Prose comes only
  from the tree. Use for /make-the-point or when the user wants pyramid
  structuring, SCQA, governing thought, key line, MECE argument trees, or
  eval-friendly reading and writing of arguments.
disable-model-invocation: true
---

# Make the point

Build or extract an **ArgumentTree**. The tree is the product. The pyramid diagram and prose are views of the tree.

Method: [Minto Pyramid Principle](https://piramideschrijven.com/minto-pyramid-principle/). Schema: [argument-tree.schema.json](argument-tree.schema.json). Rules: [pyramid.md](pyramid.md). Examples: [rich SVG](examples/valid-analyze.md), [Mermaid](examples/valid-analyze-mermaid.md), [ANSI](examples/valid-analyze-ansi.md).

## Inputs

One of:

- **text** — paste or file
- **link** — fetch and read the page (or the user-provided extract)
- **image** — read the image (OCR / describe visible text and structure)

If the mode is unclear: **analyze** when source writing exists; **construct** when the user wants a message built.

## Workflow

1. Ingest the source. Quote only what you need for `source.excerpt`.
2. Write SCQA, then set `governingThought` to the same string as `scqa.answer`.
3. Build `keyLine` as the top MECE supports. Recurse with vertical logic (child answers why/how for parent).
4. Set `horizontalLogic` to `inductive` (grouped reasons of one kind) or `deductive` (chain).
5. Optionally write `prose` **from the tree only**, answer-first, key-line order. No claim in prose that is not in the tree.
6. Write one JSON object that matches the schema. Then run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate-tree.py path/to/tree.json
```

From the repository root:

```bash
python3 skills/make-the-point/scripts/validate-tree.py path/to/tree.json
```

7. Reply with the host diagram, then the JSON. Run the script when a shell is available. When it is not, emit the diagram from the surface table below. The script is optional. Do not block a Desktop reply on Python.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render-pyramid.py path/to/tree.json --format svg
```

From the repository root, the script is `skills/make-the-point/scripts/render-pyramid.py`. The default format is svg. Pass `--format mermaid` or `--format ansi` for the other hosts.

Fix until validate exits 0. Do not treat a freeform essay as done.

## Output contract

Reply in this order.

1. The diagram for one row of the surface table. Show `governingThought` and `keyLine` only. Keep deeper `children` and `support` in the JSON.
2. The ArgumentTree JSON in a `json` fence. Evals score this object.
3. An optional one-line summary after the JSON.

### Surface table

| Host | Format |
| --- | --- |
| Claude Code, a TUI, or another terminal | ANSI box drawing inside a fenced code block |
| Claude Desktop | SVG cards. No dark page background. Purple `#5B2C6F` and teal `#0E6655` when the host allows color. |
| Cursor, ChatGPT, and other Markdown chats | Mermaid flowchart inside a `mermaid` fence, with purple and teal node styles |
| Optional rich SVG | SVG cards with no `#141414` page fill |
| Never | Raw SVG in a terminal |

Wrap a label to about 40 characters per line. Use at most 3 lines. Use an ellipsis only when the last line still overflows. A narrow card wraps to its own width. Copy words from the claim. Do not invent label text.

Match the example for that paint: [rich SVG](examples/valid-analyze.md), [Mermaid](examples/valid-analyze-mermaid.md), [ANSI](examples/valid-analyze-ansi.md). Put uncertainty in `notes`. Do not invent nodes.

## Decision rules

- Answer first. Never open with background that hides the governing thought.
- One idea per node. Siblings same kind, mutually exclusive, jointly exhaustive for the parent question.
- Vertical: every child must support its parent. Cut orphans.
- Horizontal: do not mix inductive grouping with a deductive chain on the same sibling set.
- Analyze mode maps the source. Prefer the author's point. If the source has no clear point, say so in `notes` and still force a best-effort tree.
- Construct mode invents structure for the user's intent, then drafts prose from it.
- Diagram labels never invent wording absent from the claim. Shorten only by wrapping, and ellipsize only the overflow.
- Pick the paint from the surface table. Do not paste raw SVG into a terminal.
- Do not paint a full-bleed dark page background on the SVG.
- Do not use D3, a widget, or a second skill.

## Structural check

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate-tree.py --self-test
```

From the repository root:

```bash
python3 skills/make-the-point/scripts/validate-tree.py --self-test
```

Must exit 0. Packaged fixtures encode one valid tree, one deliberate failure, and svg, mermaid, and ansi renders of the valid tree.
