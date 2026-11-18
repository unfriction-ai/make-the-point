# Mermaid example

Mermaid flowchart for Markdown chats. The governing thought is purple. The key line is teal.

## Pyramid diagram

```mermaid
flowchart TB
  GT["Appoint one backlog owner with explicit<br/>decision rights."]
  K1["Split ownership creates priority thrash."]
  K2["A single owner can sequence work against<br/>one outcome."]
  K3["Decision rights remove escalation<br/>latency."]
  GT --> K1
  GT --> K2
  GT --> K3
  style GT fill:#5B2C6F,stroke:#7D3C98,color:#fff
  style K1 fill:#0E6655,stroke:#148F77,color:#fff
  style K2 fill:#0E6655,stroke:#148F77,color:#fff
  style K3 fill:#0E6655,stroke:#148F77,color:#fff
```

## ArgumentTree JSON

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

Appoint one backlog owner with explicit decision rights.
