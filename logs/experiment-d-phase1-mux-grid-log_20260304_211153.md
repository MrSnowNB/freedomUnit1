---
title: "Experiment D — Phase 1 (Pre-Tokenizer) — MUX Grid — Run Log"
date: 2026-03-05T02:11:53.332775+00:00
version: 4.0
phase: phase1
codec: mux_grid
model: gemma3:latest
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
pretokenizer: True
llm_codec: False
fallback_threshold: 0.7
---

# Experiment D — Phase 1 (Pre-Tokenizer) — MUX Grid — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Inf(ms) | Tokens | Pg | Hit% | ESC | RSSI | SNR | Message |
|---|-----|-----|-----|-------|---------|--------|----|------|-----|------|-----|---------|
| 1 | B→A | 73 | 39 | 1.87 | 3888 | 15 | 1 | 82% | 2 | None | None | alert flood warning issued for lawrence township checking se |
| 2 | A→B | None | 62 | — | — | None | 1 | — | None | -16 | 7.75 | sensor 3 reports rising water levels at 1 point 5 feet im co |
| 3 | B→A | 97 | 42 | 2.31 | 3834 | 28 | 1 | 95% | 1 | None | None | agent 2 please report sensor 7 and 8 readings immediately se |
| 4 | A→B | None | 36 | — | — | None | 1 | — | None | -17 | 6.75 | sensor 7 reports no change currently at 0 point 8 feet senso |
| 5 | B→A | 118 | 64 | 1.84 | 4340 | 35 | 1 | 88% | 3 | None | None | sensor 3 is now at 1 point 7 feet we need to activate the lo |
| 6 | A→B | None | 56 | — | — | None | 1 | — | None | -16 | 6.75 | sensor 3 is now 2 point 1 feet escalating the alert agent 2  |
| 7 | B→A | 118 | 57 | 2.07 | 2282 | 29 | 1 | 90% | 2 | None | None | sensor 3 is at 2 point 3 feet initiating emergency response  |
| 8 | A→B | None | 34 | — | — | None | 1 | — | None | -15 | 5.5 | sensor 3 is now 2 point 8 feet requesting immediate evacuati |
| 9 | B→A | 82 | 46 | 1.78 | 3333 | 18 | 1 | 70% | 3 | None | None | confirming evacuation request dispatching emergency services |
| 10 | A→B | None | 32 | — | — | None | 1 | — | None | -16 | 5.5 | sensor 3 is at 3 point 2 feet requesting additional resource |
| 11 | B→A | 64 | 38 | 1.68 | 2534 | 15 | 1 | 67% | 3 | None | None | dispatching additional crews and equipment to sensor 3s loca |
| 12 | A→B | None | 32 | — | — | None | 1 | — | None | -15 | 5.75 | sensor 3 is now 3 point 7 feet requesting backup support |
| 13 | B→A | 82 | 44 | 1.86 | 2684 | 13 | 1 | 78% | 2 | None | None | acknowledging backup support request coordinating with count |
| 14 | A→B | None | 34 | — | — | None | 1 | — | None | -13 | 5.75 | sensor 3 is at 4 point 1 feet requesting immediate shelter a |
| 15 | B→A | 68 | 44 | 1.55 | 2797 | 15 | 1 | 80% | 2 | None | None | dispatching shelter teams to the affected area prioritizing  |
| 16 | A→B | None | 32 | — | — | None | 1 | — | None | -13 | 6.0 | sensor 3 is now 4 point 6 feet requesting medical support |
| 17 | B→A | 77 | 45 | 1.71 | 2938 | 17 | 1 | 70% | 3 | None | None | dispatching medical personnel to sensor 3s location assessin |
| 18 | A→B | None | 48 | — | — | None | 1 | — | None | -13 | 6.0 | sensor 3 is now 5 point 1 feet requesting heavy equipment fo |
| 19 | B→A | 77 | 46 | 1.67 | 3054 | 17 | 1 | 73% | 3 | None | None | dispatching heavy machinery to sensor 3s location for immedi |
| 20 | A→B | None | 32 | — | — | None | 1 | — | None | -25 | 5.5 | sensor 3 is now 5 point 6 feet requesting further assistance |

## Full Conversation Transcript

| # | Sender | Text |
|---|--------|------|
| 1 | Role B | Alert: Flood warning issued for Lawrence Township. Checking sensor data now. |
| 2 | Role A | sensor 3 reports rising water levels at 1 point 5 feet im confirming with agent 2 about other sensor readings |
| 3 | Role B | Agent 2, please report sensor 7 and 8 readings immediately. Sensor 3 is currently at 1.5 feet. |
| 4 | Role A | sensor 7 reports no change currently at 0 point 8 feet sensor 8 is also stable at 1 point 2 feet |
| 5 | Role B | Sensor 3 is now at 1.7 feet, we need to activate the low-lying area alert. Agent 2, please monitor sensor 3 closely. |
| 6 | Role A | sensor 3 is now 2 point 1 feet escalating the alert agent 2 please monitor sensor 3 continuously |
| 7 | Role B | Sensor 3 is at 2.3 feet, initiating emergency response protocols. Agent 2, maintain constant monitoring of sensor 3. |
| 8 | Role A | sensor 3 is now 2 point 8 feet requesting immediate evacuation assistance |
| 9 | Role B | Confirming evacuation request, dispatching emergency services to sensor 3’s location. |
| 10 | Role A | sensor 3 is at 3 point 2 feet requesting additional resources |
| 11 | Role B | Dispatching additional crews and equipment to sensor 3’s location. |
| 12 | Role A | sensor 3 is now 3 point 7 feet requesting backup support |
| 13 | Role B | Acknowledging backup support request, coordinating with county emergency management. |
| 14 | Role A | sensor 3 is at 4 point 1 feet requesting immediate shelter assistance |
| 15 | Role B | Dispatching shelter teams to the affected area, prioritizing sensor 3. |
| 16 | Role A | sensor 3 is now 4 point 6 feet requesting medical support |
| 17 | Role B | Dispatching medical personnel to sensor 3’s location, assessing immediate needs. |
| 18 | Role A | sensor 3 is now 5 point 1 feet requesting heavy equipment for flood mitigation |
| 19 | Role B | Dispatching heavy machinery to sensor 3’s location for immediate flood control. |
| 20 | Role A | sensor 3 is now 5 point 6 feet requesting further assistance |
