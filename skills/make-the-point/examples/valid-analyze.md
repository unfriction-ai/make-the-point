# Rich SVG example

These are the optional rich SVG cards. Claude Desktop uses this same paint. The SVG has no dark page background.

## Pyramid diagram

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680.0 224.0" width="100%" role="img" aria-label="Argument pyramid">
<path d="M 340.0 80.0 V 104.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<path d="M 120.0 104.0 H 560.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<path d="M 120.0 104.0 V 128.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<path d="M 340.0 104.0 V 128.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<path d="M 560.0 104.0 V 128.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<rect x="60.0" y="16.0" width="560.0" height="64.0" rx="10" fill="#5B2C6F" stroke="#7D3C98"/>
<text x="340.0" y="43.5" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">Appoint one backlog owner with explicit</text>
<text x="340.0" y="60.5" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">decision rights.</text>
<rect id="K1" x="20.0" y="128.0" width="200.0" height="72.0" rx="10" fill="#0E6655" stroke="#148F77"/>
<text x="120.0" y="156.0" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="13">Split ownership creates</text>
<text x="120.0" y="172.0" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="13">priority thrash.</text>
<rect id="K2" x="240.0" y="128.0" width="200.0" height="72.0" rx="10" fill="#0E6655" stroke="#148F77"/>
<text x="340.0" y="148.0" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="13">A single owner can</text>
<text x="340.0" y="164.0" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="13">sequence work against one</text>
<text x="340.0" y="180.0" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="13">outcome.</text>
<rect id="K3" x="460.0" y="128.0" width="200.0" height="72.0" rx="10" fill="#0E6655" stroke="#148F77"/>
<text x="560.0" y="156.0" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="13">Decision rights remove</text>
<text x="560.0" y="172.0" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="13">escalation latency.</text>
</svg>

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
