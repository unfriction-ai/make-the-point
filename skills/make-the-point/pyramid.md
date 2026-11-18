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

## Surface table

Reply with one diagram, then the JSON. The diagram shows the governing thought and the key line only. Deeper children and support stay in the JSON.

| Host | Format |
| --- | --- |
| Claude Code, a TUI, or another terminal | ANSI box drawing inside a fenced code block |
| Claude Desktop | SVG cards. No dark page background. Purple `#5B2C6F` and teal `#0E6655` when the host allows color. |
| Cursor, ChatGPT, and other Markdown chats | Mermaid flowchart inside a `mermaid` fence, with purple and teal node styles |
| Optional rich SVG | SVG cards with no `#141414` page fill |
| Never | Raw SVG in a terminal |

Wrap a label to about 40 characters per line. Use at most 3 lines. Use an ellipsis only when the last line still overflows. A narrow card wraps to its own width. Copy words from the claim.

Run `scripts/render-pyramid.py` when a shell is available. The default format is svg. Pass `--format mermaid` or `--format ansi` for the other hosts. When no shell is available, emit the same shape from this table. The script is not required for Claude Desktop.

Do not use D3, a widget, or a second skill.

## What not to do

- Do not ship essay-only output.
- Do not ship JSON without the diagram.
- Do not bury the answer under chronology of research.
- Do not use overlapping sibling claims ("better UX" and "easier to use").
- Do not attach evidence that supports a different claim than its parent.
- Do not put full support figures into diagram labels.
- Do not expand the diagram into a deep flowchart of every child node.
- Do not paste raw SVG into a terminal.
- Do not paint a full-bleed dark page background.
- Do not use D3, a widget, or a second skill.


