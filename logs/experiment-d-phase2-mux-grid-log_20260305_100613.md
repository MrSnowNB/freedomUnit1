---
title: "Experiment E — Phase 2 (LLM Codec) — MUX Grid — Run Log"
date: 2026-03-05T15:06:13.585703+00:00
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
| 1 | B→A | 33 | 29 | 1.14 | 2131 | 879 | — | 1 | 67% | 2 | Y | None | None | Hiker1: The trailhead sign is open. | hiker1 the trailhead sign is open |
| 2 | A→B | None | 33 | — | — | — | 1318 | 1 | — | None | N | -8 | 6.0 | — | would you like me to also help rewrite it in a mor |
| 3 | B→A | 20 | 16 | 1.25 | 2211 | 2225 | — | 1 | 75% | 1 | N | None | None | Hiker1: Yes, please do. | hiker1 yes please do |
| 4 | A→B | None | 48 | — | — | — | 1293 | 1 | — | None | N | -9 | 5.5 | — | could you help me refine this message for clarity  |
| 5 | B→A | 72 | 33 | 2.18 | 2637 | 1068 | — | 1 | 83% | 2 | N | None | None | Hiker1: Yes, please help with the message. | hiker1 could you help me make this message clearer |
| 6 | A→B | None | 39 | — | — | — | 1270 | 1 | — | None | N | -8 | 6.75 | — | let me know if youd like me to adjust the tone or  |
| 7 | B→A | 59 | 36 | 1.64 | 2524 | 1901 | — | 1 | 73% | 3 | N | None | None | Hiker1: Yes, please adjust the tone or content. | hiker1 could you adjust the tone or content of thi |
| 8 | A→B | None | 26 | — | — | — | 2267 | 1 | — | None | N | -8 | 7.0 | — | would you like me to make it sound more formal or  |
| 9 | B→A | 70 | 40 | 1.75 | 2539 | 1732 | — | 1 | 79% | 3 | N | None | None | Hiker1: Would you like me to adjust the tone or co | hiker1 would you like me to adjust the tone or con |
| 10 | A→B | None | 46 | — | — | — | 1922 | 1 | — | None | N | -8 | 6.25 | — | would you like me to rewrite this in a more formal |
| 11 | B→A | 70 | 40 | 1.75 | 2529 | 1897 | — | 1 | 79% | 3 | N | None | None | Hiker1: Would you like me to adjust the tone or co | hiker1 would you like me to adjust the tone or con |
| 12 | A→B | None | 43 | — | — | — | 2310 | 1 | — | None | N | -8 | 5.5 | — | if you want a more formal or polished version here |
| 13 | B→A | 71 | 35 | 2.03 | 2688 | 1696 | — | 1 | 85% | 2 | N | None | None | Hiker1: Would you like a more formal or polished v | hiker1 would you like a more formal or polished ve |
| 14 | A→B | None | 31 | — | — | — | 2026 | 1 | — | None | N | -8 | 5.5 | — | 42 sensors are working ill check again in 30 minut |
| 15 | B→A | 70 | 48 | 1.46 | 2321 | 2242 | — | 1 | 75% | 3 | N | None | None | Hiker1: The 42 sensors are operational; please che | hiker1 the 42 sensors are operational please check |
| 16 | A→B | None | 56 | — | — | — | 1870 | 1 | — | None | N | -10 | 6.75 | — | 42 sensors are operational ill follow up in 30 min |
| 17 | B→A | 167 | 73 | 2.29 | 26 | 3070 | — | 1 | 86% | 4 | N | None | None | — | it seems like your message might be incomplete or  |
| 18 | A→B | None | 37 | — | — | — | 1687 | 1 | — | None | N | -9 | 6.0 | — | if you are asking about a specific context like a  |
| 19 | B→A | 133 | 70 | 1.90 | 1531 | 1389 | — | 1 | 81% | 4 | N | None | None | The flood warning is active for Lawrence Township, | the flood warning is active in lawrence township n |
| 20 | A→B | None | 54 | — | — | — | 1176 | 1 | — | None | N | -9 | 5.75 | — | note if you meant to write a more formal or polish |

## Full Conversation Transcript

| # | Sender | Natural | Encoded/Decoded |
|---|--------|---------|-----------------|
| 1 | Role B | Hiker1: The trailhead sign is open. | hiker1 the trailhead sign is open |
| 2 | Role A | — | would you like me to also help rewrite it in a more formal t |
| 3 | Role B | Hiker1: Yes, please do. | hiker1 yes please do |
| 4 | Role A | — | could you help me refine this message for clarity and profes |
| 5 | Role B | Hiker1: Yes, please help with the message. | hiker1 could you help me make this message clearer and more  |
| 6 | Role A | — | let me know if youd like me to adjust the tone or content fu |
| 7 | Role B | Hiker1: Yes, please adjust the tone or content. | hiker1 could you adjust the tone or content of this message |
| 8 | Role A | — | would you like me to make it sound more formal or more casua |
| 9 | Role B | Hiker1: Would you like me to adjust the tone or content of t | hiker1 would you like me to adjust the tone or content of th |
| 10 | Role A | — | would you like me to rewrite this in a more formal tone or a |
| 11 | Role B | Hiker1: Would you like me to adjust the tone or content of t | hiker1 would you like me to adjust the tone or content of th |
| 12 | Role A | — | if you want a more formal or polished version heres a refine |
| 13 | Role B | Hiker1: Would you like a more formal or polished version of  | hiker1 would you like a more formal or polished version of t |
| 14 | Role A | — | 42 sensors are working ill check again in 30 minutes |
| 15 | Role B | Hiker1: The 42 sensors are operational; please check again i | hiker1 the 42 sensors are operational please check again in  |
| 16 | Role A | — | 42 sensors are operational ill follow up in 30 minutes as in |
| 17 | Role B | — | it seems like your message might be incomplete or missing a  |
| 18 | Role A | — | if you are asking about a specific context like a project a  |
| 19 | Role B | The flood warning is active for Lawrence Township, NJ. Check | the flood warning is active in lawrence township nj review s |
| 20 | Role A | — | note if you meant to write a more formal or polished version |
