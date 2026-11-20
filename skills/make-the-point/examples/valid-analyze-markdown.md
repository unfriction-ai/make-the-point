# Markdown example

Nested Markdown tree for every host. It uses no raw HTML. The governing thought is a quoted heading. The full tree follows as nested bullets, with each support line under its claim. The notes follow as a Caveats list.

## Pyramid diagram

> ### Appoint one backlog owner with explicit decision rights.

- `K1` **Split ownership creates priority thrash.**
  - `K1.1` Each team optimizes local goals.\
    ↳ *Sprint goals diverged three times last quarter.*
* `K2` **A single owner can sequence work against one outcome.**\
  ↳ *Peer products that use one owner ship on a shared roadmap.*
- `K3` **Decision rights remove escalation latency.**\
  ↳ *Escalations currently take a median of five days.*

**Caveats**

- Source did not quantify thrash cost beyond escalation latency.

## ArgumentTree JSON (--debug only)

The reply adds this fence only when the skill runs with `--debug`.

```json
{
  "version": 1,
  "mode": "analyze",
  "source": {
    "kind": "text",
    "excerpt": "Memo arguing for a single backlog owner"
  },
  "scqa": {
    "situation": "Two teams share one product backlog.",
    "complication": "Priorities conflict and delivery slips.",
    "question": "How should we set priority?",
    "answer": "Appoint one backlog owner with explicit decision rights."
  },
  "governingThought": "Appoint one backlog owner with explicit decision rights.",
  "horizontalLogic": "inductive",
  "keyLine": [
    {
      "id": "K1",
      "claim": "Split ownership creates priority thrash.",
      "role": "reason",
      "children": [
        {
          "id": "K1.1",
          "claim": "Each team optimizes local goals.",
          "role": "reason",
          "support": ["Sprint goals diverged three times last quarter."]
        }
      ]
    },
    {
      "id": "K2",
      "claim": "A single owner can sequence work against one outcome.",
      "role": "reason",
      "support": ["Peer products that use one owner ship on a shared roadmap."]
    },
    {
      "id": "K3",
      "claim": "Decision rights remove escalation latency.",
      "role": "reason",
      "support": ["Escalations currently take a median of five days."]
    }
  ],
  "prose": "Appoint one backlog owner with explicit decision rights. Split ownership creates priority thrash because each team optimizes local goals. A single owner can sequence work against one outcome. Decision rights remove escalation latency.",
  "notes": ["Source did not quantify thrash cost beyond escalation latency."]
}
```

Plugin: make-the-point 0.3.2

Appoint one backlog owner with explicit decision rights.
