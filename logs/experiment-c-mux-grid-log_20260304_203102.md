---
title: "Experiment C — MUX Grid — Run Log"
date: 2026-03-05T01:31:02.553269+00:00
version: 3.0.0
codec: mux_grid
model: gemma3:latest
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
---

# Experiment C — MUX Grid — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Inf(ms) | Tokens | Pages | Hit% | ESC | RSSI | SNR | Message (truncated) |
|---|-----|-----|-----|-------|---------|--------|-------|------|-----|------|-----|---------------------|
| 1 | B→A | 78 | 53 | 1.47 | 2003 | 15 | 1 | 64% | 4 | None | None | Alert: Flood warning issued for Lawrence Township. Checking  |
| 2 | A→B | None | 79 | — | — | None | 1 | — | None | -5 | 6.0 | sensor 3 reports rising water levels at 1.5 feet. i’m confir |
| 3 | B→A | 94 | 51 | 1.84 | 1831 | 24 | 1 | 82% | 3 | None | None | Sensor 9 also shows a rise to 0.8 feet. We need to alert loc |
| 4 | A→B | None | 67 | — | — | None | 1 | — | None | -6 | 6.0 | confirming sensor 11 is also reporting 1.2 feet. dispatching |
| 5 | B→A | 56 | 55 | 1.02 | 1550 | 16 | 1 | 50% | 5 | None | None | Sensor 5 now reads 2.1 feet – escalating the response. |
| 6 | A→B | None | 51 | — | — | None | 1 | — | None | -4 | 7.5 | sensor 14 is also at 1.8 feet, requesting additional resourc |
| 7 | B→A | 57 | 48 | 1.19 | 1526 | 19 | 1 | 64% | 4 | None | None | Confirming sensor 15 is at 2.5 feet – this is critical. |
| 8 | A→B | None | 52 | — | — | None | 1 | — | None | -3 | 5.5 | sensor 16 reports 2.3 feet, requesting immediate evacuation  |
| 9 | B→A | 73 | 50 | 1.46 | 1626 | 21 | 1 | 71% | 4 | None | None | Sensor 17 is now at 2.7 feet – we need to prioritize evacuat |
| 10 | A→B | None | 68 | — | — | None | 1 | — | None | -6 | 5.5 | sensor 18 reads 3.1 feet – initiating shelter activation pro |
| 11 | B→A | 64 | 50 | 1.28 | 1520 | 18 | 1 | 64% | 4 | None | None | Sensor 19 is at 3.3 feet – requesting all available personne |
| 12 | A→B | None | 52 | — | — | None | 1 | — | None | -8 | 8.0 | sensor 20 reports 3.5 feet – the situation is rapidly deteri |
| 13 | B→A | 81 | 50 | 1.62 | 2745 | 22 | 1 | 73% | 4 | None | None | Sensor 21 is at 3.7 feet – we need to activate the emergency |
| 14 | A→B | None | 67 | — | — | None | 1 | — | None | -8 | 7.5 | sensor 22 reads 4.0 feet – initiating full-scale emergency r |
| 15 | B→A | 56 | 44 | 1.27 | 1571 | 18 | 1 | 64% | 4 | None | None | Sensor 23 is at 4.2 feet – deploying rescue teams now. |
| 16 | A→B | None | 41 | — | — | None | 1 | — | None | -8 | 8.0 | sensor 24 reports 4.5 feet – all available resources are bei |
| 17 | B→A | 65 | 56 | 1.16 | 1538 | 18 | 1 | 55% | 5 | None | None | Sensor 25 is at 4.8 feet – requesting immediate aerial suppo |
| 18 | A→B | None | 63 | — | — | None | 1 | — | None | -8 | 5.5 | sensor 26 reports 5.1 feet – requesting immediate helicopter |
| 19 | B→A | 75 | 51 | 1.47 | 1632 | 20 | 1 | 69% | 4 | None | None | Sensor 27 is at 5.3 feet – we require immediate aerial rescu |
| 20 | A→B | None | 60 | — | — | None | 1 | — | None | -8 | 7.25 | sensor 28 reports 5.5 feet – initiating full-scale rescue ef |

## Full Conversation Transcript

| # | Sender | Text |
|---|--------|------|
| 1 | Role B | Alert: Flood warning issued for Lawrence Township. Checking sensor status now. |
| 2 | Role A | sensor 3 reports rising water levels at 1.5 feet. i’m confirming sensor 7 and 12 are still operational. |
| 3 | Role B | Sensor 9 also shows a rise to 0.8 feet. We need to alert local emergency services immediately. |
| 4 | Role A | confirming sensor 11 is also reporting 1.2 feet. dispatching alerts to emergency services with all available data. |
| 5 | Role B | Sensor 5 now reads 2.1 feet – escalating the response. |
| 6 | Role A | sensor 14 is also at 1.8 feet, requesting additional resources. |
| 7 | Role B | Confirming sensor 15 is at 2.5 feet – this is critical. |
| 8 | Role A | sensor 16 reports 2.3 feet, requesting immediate evacuation assistance. |
| 9 | Role B | Sensor 17 is now at 2.7 feet – we need to prioritize evacuation routes. |
| 10 | Role A | sensor 18 reads 3.1 feet – initiating shelter activation protocols. |
| 11 | Role B | Sensor 19 is at 3.3 feet – requesting all available personnel. |
| 12 | Role A | sensor 20 reports 3.5 feet – the situation is rapidly deteriorating. |
| 13 | Role B | Sensor 21 is at 3.7 feet – we need to activate the emergency operations center. |
| 14 | Role A | sensor 22 reads 4.0 feet – initiating full-scale emergency response. |
| 15 | Role B | Sensor 23 is at 4.2 feet – deploying rescue teams now. |
| 16 | Role A | sensor 24 reports 4.5 feet – all available resources are being mobilized. |
| 17 | Role B | Sensor 25 is at 4.8 feet – requesting immediate aerial support. |
| 18 | Role A | sensor 26 reports 5.1 feet – requesting immediate helicopter deployment. |
| 19 | Role B | Sensor 27 is at 5.3 feet – we require immediate aerial rescue operations. |
| 20 | Role A | sensor 28 reports 5.5 feet – initiating full-scale rescue efforts. |
