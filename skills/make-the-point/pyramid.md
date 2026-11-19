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

Reply with one diagram, then the JSON. The Markdown tree shows every node and support line. ANSI shows the governing thought and the key line only, and leaves deeper children and support to the JSON.

| Host | Format |
| --- | --- |
| Claude Code, a TUI, or another terminal | ANSI box drawing inside a fenced code block (`--format ansi`) |
| Every other host (Claude Desktop, Claude Code desktop, Cursor, ChatGPT, GitHub, Markdown chats) | Nested Markdown tree (`--format markdown`, the default). The governing thought is a quoted heading. The full tree follows as nested bullets, with each support line under its claim. |

In ANSI, wrap a label to about 40 characters per line. Use at most 3 lines. Use an ellipsis only when the last line still overflows. A narrow card wraps to its own width. Copy words from the claim. The Markdown tree prints each claim in full. ANSI fits cards to `--width` (80 columns by default), so text keeps its full size at any claim count. Claims that do not fit one row wrap onto balanced rows.

Run `scripts/render-pyramid.py` when a shell is available. The default format is markdown. Pass `--format ansi` for a terminal. When no shell is available, emit the same shape from this table. The script is not required for a Markdown reply.

Do not use D3, a widget, or a second skill.

## What not to do

- Do not ship essay-only output.
- Do not ship JSON without the diagram.
- Do not bury the answer under chronology of research.
- Do not use overlapping sibling claims ("better UX" and "easier to use").
- Do not attach evidence that supports a different claim than its parent.
- Do not put full support figures into ANSI labels.
- Do not expand the ANSI diagram into every child node. Only the Markdown tree shows full depth.
- Do not use D3, a widget, or a second skill.


