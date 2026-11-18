---
name: make-the-point
description: >-
  Understand, construct, and communicate the central argument in writing via the
  Minto Pyramid Principle. Accepts text, a link, or an image. Canonical output
  is a testable ArgumentTree JSON plus an inline SVG card pyramid (purple
  governing thought, teal key-line cards, short labels); prose is generated or
  analyzed only from that tree. Use for /make-the-point or when the user wants
  pyramid structuring, SCQA, governing thought, key-line, MECE argument trees,
  or eval-friendly reading/writing of arguments.
disable-model-invocation: true
---

# Make the point

Build or extract an **ArgumentTree**. The tree is the product. The pyramid diagram and prose are views of the tree.

Method: [Minto Pyramid Principle](https://piramideschrijven.com/minto-pyramid-principle/). Schema: [argument-tree.schema.json](argument-tree.schema.json). Rules: [pyramid.md](pyramid.md). Example reply: [examples/valid-analyze.md](examples/valid-analyze.md).

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
6. Emit one JSON object matching the schema. Then run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate-tree.py path/to/tree.json
```

From the repository root:

```bash
python3 skills/make-the-point/scripts/validate-tree.py path/to/tree.json
```

7. Render the inline SVG pyramid from that JSON (prefer the script so colors and labels stay consistent):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render-pyramid.py path/to/tree.json
```

From the repository root:

```bash
python3 skills/make-the-point/scripts/render-pyramid.py path/to/tree.json
```

Fix until validate exits 0. Do not treat freeform essay as done.

## Output contract

Reply in this order:

1. **Pyramid diagram** — raw SVG from `render-pyramid.py` (not Mermaid). Purple card for `governingThought`, teal cards for each `keyLine` claim, elbow connectors, short labels (~40 characters). Diagram shows **governing thought + keyLine only**. Deeper `children` and `support` figures stay only in the JSON. Emit the SVG so chat hosts that allow HTML/SVG can paint it (Claude Desktop, Claude Code, Codex, and compatible IDE chats).
2. **ArgumentTree JSON** — fenced `json` block. This is what evals score.
3. Optional one-line human summary after the JSON.

Match [examples/valid-analyze.md](examples/valid-analyze.md). Put uncertainty in `notes`, not by inventing nodes.

## Decision rules

- Answer first. Never open with background that hides the governing thought.
- One idea per node. Siblings same kind, mutually exclusive, jointly exhaustive for the parent question.
- Vertical: every child must support its parent. Cut orphans.
- Horizontal: do not mix inductive grouping with a deductive chain on the same sibling set.
- Analyze mode maps the source. Prefer the author's point. If the source has no clear point, say so in `notes` and still force a best-effort tree.
- Construct mode invents structure for the user's intent, then drafts prose from it.
- Diagram labels never invent wording absent from the claim. Shorten only.
- Never use default Mermaid flowcharts for the pyramid view.

## Structural check

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate-tree.py --self-test
```

From the repository root:

```bash
python3 skills/make-the-point/scripts/validate-tree.py --self-test
```

Must exit 0. Packaged fixtures encode one valid tree, one deliberate failure, and a pyramid render check on the valid tree.
