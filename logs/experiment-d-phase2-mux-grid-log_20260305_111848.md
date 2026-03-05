---
title: "Experiment E — Phase 2 (LLM Codec) — MUX Grid — Run Log"
date: 2026-03-05T16:18:48.965253+00:00
version: 5.0
phase: phase2
codec: mux_grid
model: test01
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
pretokenizer: True
llm_codec: True
fallback_threshold: 0.7
---

# Experiment E — Phase 2 (LLM Codec) — MUX Grid — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Gen(ms) | Enc(ms) | Dec(ms) | Pg | Hit% | ESC | FB | RSSI | SNR | Natural | Encoded |
|---|-----|-----|-----|-------|---------|---------|---------|----|------|-----|----|----- |-----|---------|---------|
| 1 | B→A | 143 | 77 | 1.86 | 63 | 2074 | — | 1 | 81% | 5 | N | None | None | — | it seems like your message might be incomplete or  |
| 2 | A→B | None | 20 | — | — | — | 2745 | 1 | — | None | N | -31 | 5.75 | — | would you like me to also help with a more technic |
| 3 | B→A | 116 | 66 | 1.76 | 1429 | 893 | — | 1 | 79% | 4 | N | None | None | The flood warning is active for Lawrence Township, | the flood warning is active in lawrence township n |
| 4 | A→B | None | 48 | — | — | — | 1187 | 1 | — | None | N | -31 | 6.75 | — | 3 backup sensors are operational proceed with moni |
| 5 | B→A | 122 | 67 | 1.82 | 1562 | 1523 | — | 1 | 79% | 4 | N | None | None | The flood warning is active. We need to check sens | the flood warning is active we must check sensors  |
| 6 | A→B | None | 32 | — | — | — | 978 | 1 | — | None | N | -28 | 6.0 | — | would you like me to help you rephrase this messag |
| 7 | B→A | 116 | 55 | 2.11 | 1379 | 1508 | — | 1 | 84% | 3 | N | None | None | The flood warning is active. We need to check sens | the flood warning is active we must check sensors  |
| 8 | A→B | None | 22 | — | — | — | 1378 | 1 | — | None | N | -24 | 5.75 | — | but you want a more natural polished version |
| 9 | B→A | 150 | 81 | 1.85 | 1321 | 1022 | — | 1 | 80% | 5 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 10 | A→B | None | 24 | — | — | — | 1311 | 1 | — | None | N | -25 | 6.25 | — | would you like me to also help with a more formal  |
| 11 | B→A | 149 | 82 | 1.82 | 2053 | 1771 | — | 1 | 79% | 5 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 12 | A→B | None | 5 | — | — | — | 1554 | 1 | — | None | N | -21 | 6.25 | — | translation |
| 13 | B→A | 149 | 82 | 1.82 | 2258 | 1446 | — | 1 | 79% | 5 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 14 | A→B | None | 29 | — | — | — | 1133 | 1 | — | None | N | -8 | 6.75 | — | 78 of the network is secure keep monitoring and in |
| 15 | B→A | 158 | 95 | 1.66 | 1750 | 1955 | — | 1 | 76% | 6 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 16 | A→B | None | 3 | — | — | — | 832 | 1 | — | None | N | -7 | 5.75 | — | — |
| 17 | B→A | 158 | 95 | 1.66 | 1597 | 1521 | — | 1 | 76% | 6 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 18 | A→B | None | 26 | — | — | — | 1294 | 1 | — | None | N | -9 | 5.5 | — | would you like me to make this sound more formal o |
| 19 | B→A | 143 | 77 | 1.86 | 33 | 3466 | — | 1 | 81% | 5 | N | None | None | — | it seems like your message might be incomplete or  |
| 20 | A→B | None | 27 | — | — | — | 1958 | 1 | — | None | N | -8 | 6.5 | — | if you meant something else or need a different fo |

## Full Conversation Transcript

| # | Sender | Natural | Encoded/Decoded |
|---|--------|---------|-----------------|
| 1 | Role B | — | it seems like your message might be incomplete or missing a  |
| 2 | Role A | — | would you like me to also help with a more technical or form |
| 3 | Role B | The flood warning is active for Lawrence Township, NJ. We ne | the flood warning is active in lawrence township nj we must  |
| 4 | Role A | — | 3 backup sensors are operational proceed with monitoring and |
| 5 | Role B | The flood warning is active. We need to check sensors and pl | the flood warning is active we must check sensors assess con |
| 6 | Role A | — | would you like me to help you rephrase this message for a di |
| 7 | Role B | The flood warning is active. We need to check sensors and pl | the flood warning is active we must check sensors assess con |
| 8 | Role A | — | but you want a more natural polished version |
| 9 | Role B | The flood warning is active in Lawrence Township, NJ. We nee | the flood warning is active in lawrence township nj we need  |
| 10 | Role A | — | would you like me to also help with a more formal version su |
| 11 | Role B | The flood warning is active in Lawrence Township, NJ. We nee | the flood warning is active in lawrence township nj we must  |
| 12 | Role A | — | translation |
| 13 | Role B | The flood warning is active in Lawrence Township, NJ. We nee | the flood warning is active in lawrence township nj we must  |
| 14 | Role A | — | 78 of the network is secure keep monitoring and inform the p |
| 15 | Role B | The flood warning is active in Lawrence Township, NJ. We nee | the flood warning is active in lawrence township nj we need  |
| 16 | Role A | — | The flood warning is active. We need to check sensors and pr |
| 17 | Role B | The flood warning is active in Lawrence Township, NJ. We nee | the flood warning is active in lawrence township nj we need  |
| 18 | Role A | — | would you like me to make this sound more formal or more cas |
| 19 | Role B | — | it seems like your message might be incomplete or missing a  |
| 20 | Role A | — | if you meant something else or need a different format let m |
