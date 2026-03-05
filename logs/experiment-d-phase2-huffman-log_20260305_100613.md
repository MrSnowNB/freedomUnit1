---
title: "Experiment E — Phase 2 (LLM Codec) — Huffman (4K) — Run Log"
date: 2026-03-05T15:06:13.588923+00:00
version: 5.0
phase: phase2
codec: huffman
model: test01
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
pretokenizer: True
llm_codec: True
fallback_threshold: 0.7
---

# Experiment E — Phase 2 (LLM Codec) — Huffman (4K) — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Gen(ms) | Enc(ms) | Dec(ms) | Pg | Hit% | ESC | FB | RSSI | SNR | Natural | Encoded |
|---|-----|-----|-----|-------|---------|---------|---------|----|------|-----|----|----- |-----|---------|---------|
| 1 | B→A | 149 | 76 | 1.96 | 1649 | 1112 | — | 1 | 79% | 5 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 2 | A→B | None | 54 | — | — | — | 1410 | 1 | — | None | N | -9 | 5.5 | — | 1 sentence i need to check the flood sensors and s |
| 3 | B→A | 78 | 29 | 2.69 | 1281 | 1119 | — | 1 | 92% | 1 | N | None | None | The flood warning is active. Let's check the senso | the flood warning is active please check the senso |
| 4 | A→B | None | 66 | — | — | — | 1290 | 1 | — | None | N | -10 | 5.75 | — | 2 sentences there are 3 sensors near the river but |
| 5 | B→A | 116 | 58 | 2.00 | 1096 | 1147 | — | 1 | 84% | 3 | N | None | None | The flood warning is active. Two sensors near the  | the flood warning is active two sensors near the r |
| 6 | A→B | None | 31 | — | — | — | 1007 | 1 | — | None | N | -9 | 6.5 | — | let me know if youd like it rephrased further |
| 7 | B→A | 119 | 58 | 2.05 | 1525 | 886 | — | 1 | 84% | 3 | N | None | None | The flood warning is active. Two sensors near the  | the flood warning is active two sensors near the r |
| 8 | A→B | None | 42 | — | — | — | 1006 | 1 | — | None | N | -9 | 5.5 | — | would you like me to help with a more detailed exp |
| 9 | B→A | 156 | 69 | 2.26 | 1285 | 1503 | — | 1 | 89% | 3 | N | None | None | The flood warning is active. Two sensors near the  | the flood warning is active two sensors near the r |
| 10 | A→B | None | 30 | — | — | — | 1338 | 1 | — | None | N | -9 | 5.75 | — | but if you want a more natural or polished version |
| 11 | B→A | 159 | 69 | 2.30 | 1546 | 1565 | — | 1 | 89% | 3 | N | None | None | The flood warning is active. Two sensors near the  | the flood warning is active two sensors near the r |
| 12 | A→B | None | 27 | — | — | — | 691 | 1 | — | None | N | -9 | 6.0 | — | if you meant something else please clarify |
| 13 | B→A | 159 | 69 | 2.30 | 1681 | 1583 | — | 1 | 89% | 3 | N | None | None | The flood warning is active. Two sensors near the  | the flood warning is active two sensors near the r |
| 14 | A→B | None | 19 | — | — | — | 888 | 1 | — | None | N | -9 | 5.5 | — | let me know if you need a more detailed version |
| 15 | B→A | 39 | 22 | 1.77 | 1899 | 786 | — | 1 | 86% | 1 | N | None | None | The flood warning is active. Two sensors near the  | the flood warning is active two sensors |
| 16 | A→B | None | 29 | — | — | — | 32 | 1 | — | None | N | -9 | 5.5 | — | let me know if youd like it adjusted |
| 17 | B→A | 114 | 84 | 1.36 | 1479 | 1290 | — | 1 | 65% | 7 | Y | None | None | I’ve checked the flood sensors in Lawrence Townshi | ive checked the flood sensors in lawrence township |
| 18 | A→B | None | 47 | — | — | — | 1224 | 1 | — | None | N | -9 | 6.0 | — | note this response is a bit long for a single sent |
| 19 | B→A | 97 | 53 | 1.83 | 1316 | 1234 | — | 1 | 81% | 3 | N | None | None | The flood warning is active. Two sensors are worki | the flood warning is active two sensors are operat |
| 20 | A→B | None | 41 | — | — | — | 1061 | 1 | — | None | N | -9 | 6.0 | — | 1 sentence thank you for your prompt response we w |

## Full Conversation Transcript

| # | Sender | Natural | Encoded/Decoded |
|---|--------|---------|-----------------|
| 1 | Role B | The flood warning is active in Lawrence Township, NJ. Please | the flood warning is active in lawrence township nj coordina |
| 2 | Role A | — | 1 sentence i need to check the flood sensors and see if any  |
| 3 | Role B | The flood warning is active. Let's check the sensors and con | the flood warning is active please check the sensors and con |
| 4 | Role A | — | 2 sentences there are 3 sensors near the river but one is no |
| 5 | Role B | The flood warning is active. Two sensors near the river are  | the flood warning is active two sensors near the river are o |
| 6 | Role A | — | let me know if youd like it rephrased further |
| 7 | Role B | The flood warning is active. Two sensors near the river are  | the flood warning is active two sensors near the river are o |
| 8 | Role A | — | would you like me to help with a more detailed explanation o |
| 9 | Role B | The flood warning is active. Two sensors near the river are  | the flood warning is active two sensors near the river are o |
| 10 | Role A | — | but if you want a more natural or polished version you can s |
| 11 | Role B | The flood warning is active. Two sensors near the river are  | the flood warning is active two sensors near the river are o |
| 12 | Role A | — | if you meant something else please clarify |
| 13 | Role B | The flood warning is active. Two sensors near the river are  | the flood warning is active two sensors near the river are o |
| 14 | Role A | — | let me know if you need a more detailed version |
| 15 | Role B | The flood warning is active. Two sensors near the river are  | the flood warning is active two sensors |
| 16 | Role A | — | let me know if youd like it adjusted |
| 17 | Role B | I’ve checked the flood sensors in Lawrence Township. Two are | ive checked the flood sensors in lawrence township two are w |
| 18 | Role A | — | note this response is a bit long for a single sentence but i |
| 19 | Role B | The flood warning is active. Two sensors are working, one ne | the flood warning is active two sensors are operational one  |
| 20 | Role A | — | 1 sentence thank you for your prompt response we will update |
