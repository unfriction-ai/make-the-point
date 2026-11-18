# Rich SVG example

These are the optional rich SVG cards. Claude Desktop uses this same paint. The SVG has no dark page background.

## Pyramid diagram

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720.0 210.0" width="100%" role="img" aria-label="Argument pyramid">
<path d="M 360.0 64.0 V 88.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<path d="M 128.0 88.0 H 592.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<path d="M 128.0 88.0 V 112.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<path d="M 360.0 88.0 V 112.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<path d="M 592.0 88.0 V 112.0" stroke="#9a9a9a" stroke-width="1.5" fill="none"/>
<rect x="80.0" y="20.0" width="560.0" height="44.0" rx="10" fill="#5B2C6F" stroke="#7D3C98"/>
<text x="360.0" y="47.6" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="16">Appoint one backlog owner with explicit decision rights.</text>
<rect id="K1" x="20.0" y="112.0" width="216.0" height="78.0" rx="10" fill="#0E6655" stroke="#148F77"/>
<text x="128.0" y="146.9" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">Split ownership creates</text>
<text x="128.0" y="164.9" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">priority thrash.</text>
<rect id="K2" x="252.0" y="112.0" width="216.0" height="78.0" rx="10" fill="#0E6655" stroke="#148F77"/>
<text x="360.0" y="137.9" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">A single owner can</text>
<text x="360.0" y="155.9" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">sequence work</text>
<text x="360.0" y="173.9" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">against one outcome.</text>
<rect id="K3" x="484.0" y="112.0" width="216.0" height="78.0" rx="10" fill="#0E6655" stroke="#148F77"/>
<text x="592.0" y="146.9" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">Decision rights remove</text>
<text x="592.0" y="164.9" text-anchor="middle" fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" font-size="14">escalation latency.</text>
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
