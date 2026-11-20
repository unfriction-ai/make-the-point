# Pyramid rules (Minto)

Source framing: [piramideschrijven.com — Minto Pyramid Principle](https://piramideschrijven.com/minto-pyramid-principle/).

## Shape

```
          governingThought  (= scqa.answer)
                 |
     +-----------+-----------+
     |           |           |
   keyLine[0]  keyLine[1]  keyLine[2]   ← MECE, same kind
     |
   children… → support facts
```

1. State the **governing thought** (the answer) first.
2. Under it, the **key line**: the few main ideas that make the answer stand.
3. Under each key-line idea, subordinate ideas, then evidence.

## SCQA

Frame the question the pyramid answers:

| Slot | Job |
| --- | --- |
| Situation | Stable context the reader accepts |
| Complication | Change that creates tension |
| Question | What the complication forces the reader to ask |
| Answer | Governing thought |

`governingThought` and `scqa.answer` must be identical strings.

## Vertical logic

A lower node exists only to support the node above (why / how / prove). If cutting a child does not weaken the parent, delete it.

## Horizontal logic

Siblings at one level:

- Same kind of idea (all reasons, or all steps, or all parts — not a mix).
- MECE: mutually exclusive, collectively exhaustive for that parent's question.
- Ordered: time, structure, or priority. State the order by sequence in `keyLine` / `children`.

`horizontalLogic`:

- **inductive** — independent supports that together justify the parent.
- **deductive** — chained major premise → minor → conclusion toward the parent.

## Prose from the tree

Order: governing thought → key-line points in array order → deepen only as needed. Do not add claims absent from the tree. Do not lead with SCQA story unless the user asks for a full memo intro; SCQA lives in the JSON either way.

## Diagram

Reply with one diagram. The diagram shows the full tree, every node and support line, then the tree's notes as a **Caveats** list. Add the JSON after it only when the skill runs with `--debug`.

Every host gets the nested Markdown tree, terminals and Claude Code included. Claude Code renders it in the terminal. The governing thought is a quoted heading. The full tree follows as nested bullets, with each support line under its claim. Each claim prints in full, copied from the tree.

Run `scripts/render-pyramid.py` when a shell is available. When no shell is available, write the same shape by hand. The script is not required.

Do not use D3, a widget, or a second skill.

## What not to do

- Do not ship essay-only output.
- Do not ship JSON without the diagram.
- Do not show the JSON without `--debug`. Build and validate it either way.
- Do not bury the answer under chronology of research.
- Do not use overlapping sibling claims ("better UX" and "easier to use").
- Do not attach evidence that supports a different claim than its parent.
- Do not drop nodes, support lines, or notes from the diagram.
- Do not use D3, a widget, or a second skill.


