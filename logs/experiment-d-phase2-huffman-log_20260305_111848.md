---
title: "Experiment E — Phase 2 (LLM Codec) — Huffman (4K) — Run Log"
date: 2026-03-05T16:18:48.974386+00:00
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
| 1 | B→A | 148 | 77 | 1.92 | 1581 | 1668 | — | 1 | 79% | 5 | N | None | None | The flood warning is active for Lawrence Township, | the flood warning is active in lawrence township n |
| 2 | A→B | None | 22 | — | — | — | 1189 | 1 | — | None | N | -9 | 7.5 | — | i will provide a concise and clear response |
| 3 | B→A | 85 | 39 | 2.18 | 1415 | 1291 | — | 1 | 86% | 2 | N | None | None | The flood warning is active. Coordinate with the t | the flood warning is active coordinate with the te |
| 4 | A→B | None | 13 | — | — | — | 824 | 1 | — | None | N | -8 | 7.5 | — | answer thank you for your message |
| 5 | B→A | 91 | 42 | 2.17 | 1410 | 1290 | — | 1 | 87% | 2 | N | None | None | The flood warning is active. Coordinate with the t | the flood warning is active coordinate with the te |
| 6 | A→B | None | 22 | — | — | — | 1286 | 1 | — | None | N | -8 | 6.75 | — | i will provide a concise and clear response |
| 7 | B→A | 100 | 60 | 1.67 | 1558 | 1548 | — | 1 | 76% | 4 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 8 | A→B | None | 22 | — | — | — | 1258 | 1 | — | None | N | -8 | 6.75 | — | i will provide a concise and clear response |
| 9 | B→A | 106 | 58 | 1.83 | 1252 | 873 | — | 1 | 76% | 4 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 10 | A→B | None | 22 | — | — | — | 1313 | 1 | — | None | N | -8 | 7.25 | — | i will provide a concise and clear response |
| 11 | B→A | 109 | 50 | 2.18 | 1757 | 1403 | — | 1 | 82% | 3 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 12 | A→B | None | 18 | — | — | — | 1255 | 1 | — | None | N | -9 | 7.75 | — | i understand your request here are two short respo |
| 13 | B→A | 95 | 49 | 1.94 | 1794 | 1368 | — | 1 | 81% | 3 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 14 | A→B | None | 28 | — | — | — | 1400 | 1 | — | None | N | -7 | 8.0 | — | you are asking for a 1 sentence response here it i |
| 15 | B→A | 95 | 49 | 1.94 | 1817 | 1386 | — | 1 | 81% | 3 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 16 | A→B | None | 13 | — | — | — | 1265 | 1 | — | None | N | -9 | 7.75 | — | answer thank you for your message |
| 17 | B→A | 98 | 58 | 1.69 | 1842 | 1475 | — | 1 | 76% | 4 | N | None | None | The flood warning is active in Lawrence Township,  | the flood warning is active in lawrence township n |
| 18 | A→B | None | 31 | — | — | — | 1462 | 1 | — | None | N | -8 | 7.5 | — | let me know if youd like me to tailor it further |
| 19 | B→A | 143 | 74 | 1.93 | 52 | 3471 | — | 1 | 81% | 5 | N | None | None | — | it seems like your message might be incomplete or  |
| 20 | A→B | None | 24 | — | — | — | 1303 | 1 | — | None | N | -8 | 7.0 | — | you would respond with a concise message such as |

## Full Conversation Transcript

| # | Sender | Natural | Encoded/Decoded |
|---|--------|---------|-----------------|
| 1 | Role B | The flood warning is active for Lawrence Township, NJ. Check | the flood warning is active in lawrence township nj review s |
| 2 | Role A | — | i will provide a concise and clear response |
| 3 | Role B | The flood warning is active. Coordinate with the team to ass | the flood warning is active coordinate with the team to asse |
| 4 | Role A | — | answer thank you for your message |
| 5 | Role B | The flood warning is active. Coordinate with the team to ass | the flood warning is active coordinate with the team to eval |
| 6 | Role A | — | i will provide a concise and clear response |
| 7 | Role B | The flood warning is active in Lawrence Township, NJ. Coordi | the flood warning is active in lawrence township nj coordina |
| 8 | Role A | — | i will provide a concise and clear response |
| 9 | Role B | The flood warning is active in Lawrence Township, NJ. Coordi | the flood warning is active in lawrence township nj the team |
| 10 | Role A | — | i will provide a concise and clear response |
| 11 | Role B | The flood warning is active in Lawrence Township, NJ. Coordi | the flood warning is active in lawrence township nj the team |
| 12 | Role A | — | i understand your request here are two short responses |
| 13 | Role B | The flood warning is active in Lawrence Township, NJ. Coordi | the flood warning is active in lawrence township nj the team |
| 14 | Role A | — | you are asking for a 1 sentence response here it is |
| 15 | Role B | The flood warning is active in Lawrence Township, NJ. Coordi | the flood warning is active in lawrence township nj the team |
| 16 | Role A | — | answer thank you for your message |
| 17 | Role B | The flood warning is active in Lawrence Township, NJ. Coordi | the flood warning is active in lawrence township nj coordina |
| 18 | Role A | — | let me know if youd like me to tailor it further |
| 19 | Role B | — | it seems like your message might be incomplete or missing a  |
| 20 | Role A | — | you would respond with a concise message such as |
