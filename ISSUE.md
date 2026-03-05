---
title: "Open Issues — CyberMesh Codec POC"
version: 1.0.0
date: 2026-03-05
status: active
project: huffman-mesh-poc
---

# Open Issues

Living document. Updated when conflicts or uncertainties require human input.

---

## ISSUE-001 — Architect Doc Kernel Reference vs Live Data

- **Filed**: 2026-03-05T11:27:00-05:00
- **Source conflict**:
  - `ARCHITECT-TO-CODING-AGENT-2026-03-05.md` §1a states:
    - "Current kernel: Gemma3 4B via Ollama (validated in Experiments C and D)"
    - "Target kernel: LFM2-2.6B via AMD Lemonade Server (not yet tested)"
  - Live data (Experiments E and F, both nodes) shows:
    - **LFM2.5-1.2B** (not LFM2-2.6B) running via Lemonade Server, aliased as `test01`
    - 120+ messages validated over live LoRa across 2 runs
    - Hardware comparison data from both Nvidia and Strix Halo nodes
  - `HARNESS-DESIGN-DISCUSSION.md` §Model Clarification already notes:
    "We are running LFM2.5-1.2B (aliased as 'test01'), NOT LFM2-2.6B."
- **Authority resolution**: Per file hierarchy, Mark Snow's live direction
  (running LFM2.5-1.2B) supersedes the architect doc's kernel reference.
  The architect doc's terminology and architecture principles remain
  authoritative; only the specific model names are outdated.
- **Recommended action**: Update architect doc §1a to reflect:
  - Current kernel: Gemma3 4B via Ollama (validated Experiments C–D) / **LFM2.5-1.2B via Lemonade Server** (validated Experiments E–F)
  - Target kernel: LFM2-2.6B (contemplated, not yet tested)
- **Status**: OPEN — awaiting Mark Snow confirmation
- **Blocking**: Nothing — doc cleanup proceeds using LFM2.5-1.2B as the validated kernel.

---

*Append new issues below.*
