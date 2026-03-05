---
title: "Experiment E — Phase 1 (Pre-Tokenizer) — Huffman (4K) — Run Log"
date: 2026-03-05T16:13:47.964151+00:00
version: 5.0
phase: phase1
codec: huffman
model: test01
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
pretokenizer: True
llm_codec: False
fallback_threshold: 0.7
---

# Experiment E — Phase 1 (Pre-Tokenizer) — Huffman (4K) — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Inf(ms) | Tokens | Pg | Hit% | ESC | RSSI | SNR | Message |
|---|-----|-----|-----|-------|---------|--------|----|------|-----|------|-----|---------|
| 1 | B→A | 154 | 64 | 2.41 | 1691 | 32 | 1 | 89% | 3 | None | None | the flood warning is active in lawrence township nj two sens |
| 2 | A→B | None | 47 | — | — | None | 1 | — | None | -42 | 7.0 | 2 sensors are working and im trying to connect to the backup |
| 3 | B→A | 80 | 38 | 2.11 | 1308 | 15 | 1 | 83% | 2 | None | None | were checking sensor status and will coordinate backup power |
| 4 | A→B | None | 44 | — | — | None | 1 | — | None | -31 | 7.0 | 30 seconds left before backup power activates we should move |
| 5 | B→A | 60 | 28 | 2.14 | 1080 | 10 | 1 | 89% | 1 | None | None | well keep monitoring and prepare for backup power activation |
| 6 | A→B | None | 37 | — | — | None | 1 | — | None | -33 | 5.75 | 10 minutes until the system recovers fully ill update you th |
| 7 | B→A | 55 | 17 | 3.24 | 1218 | 10 | 1 | 100% | 0 | None | None | were monitoring the situation and will keep you updated |
| 8 | A→B | None | 5 | — | — | None | 1 | — | None | -26 | 7.25 |  |
| 9 | B→A | 58 | 19 | 3.05 | 1254 | 11 | 1 | 100% | 0 | None | None | were handling the flood warning and will keep you informed |
| 10 | A→B | None | 13 | — | — | None | 1 | — | None | -26 | 6.5 | 5 more minutes remaining |
| 11 | B→A | 61 | 21 | 2.90 | 1333 | 13 | 1 | 100% | 0 | None | None | were keeping an eye on the situation and will update you soo |
| 12 | A→B | None | 23 | — | — | None | 1 | — | None | -26 | 6.5 | 15 minutes left ill confirm the backup is ready |
| 13 | B→A | 61 | 21 | 2.90 | 1462 | 13 | 1 | 100% | 0 | None | None | were keeping an eye on the situation and will update you soo |
| 14 | A→B | None | 31 | — | — | None | 1 | — | None | -26 | 6.5 | 30 minutes from now the system should be fully operational |
| 15 | B→A | 55 | 17 | 3.24 | 1243 | 10 | 1 | 100% | 0 | None | None | were monitoring the situation and will keep you updated |
| 16 | A→B | None | 5 | — | — | None | 1 | — | None | -26 | 6.5 |  |
| 17 | B→A | 61 | 21 | 2.90 | 1531 | 13 | 1 | 100% | 0 | None | None | were keeping an eye on the situation and will update you soo |
| 18 | A→B | None | 19 | — | — | None | 1 | — | None | -25 | 6.75 | 10 minutes left ill check again |
| 19 | B→A | 61 | 21 | 2.90 | 1384 | 13 | 1 | 100% | 0 | None | None | were keeping an eye on the situation and will update you soo |
| 20 | A→B | None | 23 | — | — | None | 1 | — | None | -37 | 6.0 | 5 minutes from now ill send a status report |

## Full Conversation Transcript

| # | Sender | Text |
|---|--------|------|
| 1 | Role B | The flood warning is active in Lawrence Township, NJ. Two sensors are working, one is offline and needs backup power. We’ll contact the main office for support. |
| 2 | Role A | 2 sensors are working and im trying to connect to the backup router to get more coverage lets check status now |
| 3 | Role B | We’re checking sensor status and will coordinate backup power. Let’s stay connected. |
| 4 | Role A | 30 seconds left before backup power activates we should move to the nearest safe zone |
| 5 | Role B | We’ll keep monitoring and prepare for backup power activation. |
| 6 | Role A | 10 minutes until the system recovers fully ill update you then stay safe |
| 7 | Role B | We’re monitoring the situation and will keep you updated. |
| 8 | Role A | — |
| 9 | Role B | We’re handling the flood warning and will keep you informed. |
| 10 | Role A | 5 more minutes remaining |
| 11 | Role B | We’re keeping an eye on the situation and will update you soon. |
| 12 | Role A | 15 minutes left ill confirm the backup is ready |
| 13 | Role B | We’re keeping an eye on the situation and will update you soon. |
| 14 | Role A | 30 minutes from now the system should be fully operational |
| 15 | Role B | We’re monitoring the situation and will keep you updated. |
| 16 | Role A | — |
| 17 | Role B | We’re keeping an eye on the situation and will update you soon. |
| 18 | Role A | 10 minutes left ill check again |
| 19 | Role B | We’re keeping an eye on the situation and will update you soon. |
| 20 | Role A | 5 minutes from now ill send a status report |
