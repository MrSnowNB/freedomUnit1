---
title: "Experiment D — Phase 2 (LLM Codec) — MUX Grid — Run Log"
date: 2026-03-05T02:25:13.637964+00:00
version: 4.0
phase: phase2
codec: mux_grid
model: gemma3:latest
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
pretokenizer: True
llm_codec: True
fallback_threshold: 0.7
---

# Experiment D — Phase 2 (LLM Codec) — MUX Grid — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Gen(ms) | Enc(ms) | Dec(ms) | Pg | Hit% | ESC | FB | RSSI | SNR | Natural | Encoded |
|---|-----|-----|-----|-------|---------|---------|---------|----|------|-----|----|----- |-----|---------|---------|
| 1 | B→A | 55 | 35 | 1.57 | 4062 | 11273 | — | 1 | 75% | 2 | N | None | None | Alert: Flood warning issued for Lawrence Township. | alert flood warning lawrence township sensor data  |
| 2 | A→B | None | 29 | — | — | — | 2988 | 1 | — | None | N | -17 | 7.5 | — | confirm sensor readings water levels high at stati |
| 3 | B→A | 65 | 42 | 1.55 | 3946 | 11446 | — | 1 | 75% | 3 | N | None | None | Okay, water levels are elevated at stations 3 and  | okay water high at stations 3 and 7 assess impacts |
| 4 | A→B | None | 33 | — | — | — | 3226 | 1 | — | None | N | -4 | 6.25 | — | traffic shows water on route 13 mile 7 i am alerti |
| 5 | B→A | 77 | 39 | 1.97 | 3442 | 11596 | — | 1 | 85% | 2 | N | None | None | Confirming traffic reports, water is also present  | traffic reports confirm water on route 100 mile 3  |
| 6 | A→B | None | 25 | — | — | — | 3371 | 1 | — | None | N | -4 | 6.75 | — | confirm sandbag request station 8 reports high wat |
| 7 | B→A | 60 | 29 | 2.07 | 3653 | 11337 | — | 1 | 92% | 1 | N | None | None | Station 8 confirms high water, dispatching crews t | station 8 says high water send crews now watch sta |
| 8 | A→B | None | 11 | — | — | — | 4002 | 1 | — | None | N | -4 | 5.5 | — | water high send teams now |
| 9 | B→A | 67 | 27 | 2.48 | 4401 | 11563 | — | 1 | 92% | 1 | N | None | None | Dispatching teams to station 7432, prioritizing im | send teams to station 7432 respond quickly monitor |
| 10 | A→B | None | 22 | — | — | — | 3049 | 1 | — | None | N | -5 | 5.75 | — | teams to station 7432 monitor stations 3 and 7 |
| 11 | B→A | 82 | 56 | 1.46 | 5589 | 11895 | — | 1 | 71% | 4 | N | None | None | Confirming, teams are monitoring stations 3, 7, an | confirming teams watch stations 3 7 and 7432 waiti |
| 12 | A→B | None | 14 | — | — | — | 3881 | 1 | — | None | N | -4 | 6.25 | — | bags are coming water level is stable |
| 13 | B→A | 70 | 33 | 2.12 | 5685 | 12066 | — | 1 | 85% | 2 | N | None | None | Water levels are stable at 12, confirming sensor 7 | levels are stable 12 sensor 734 reduce monitoring  |
| 14 | A→B | None | 25 | — | — | — | 3459 | 1 | — | None | N | -4 | 6.5 | — | confirming levels stable monitoring at station one |
| 15 | B→A | 35 | 11 | 3.18 | 5046 | 10812 | — | 1 | 100% | 0 | N | None | None | Confirming, we will continue monitoring station on | confirm we will monitor station one |
| 16 | A→B | None | 9 | — | — | — | 2627 | 1 | — | None | N | -4 | 5.75 | — | level high watch it |
| 17 | B→A | 55 | 48 | 1.15 | 6932 | 10935 | — | 1 | 43% | 4 | Y | None | None | Confirming, dispatching crews to station 734 immed | confirming dispatching crews to station 734 immedi |
| 18 | A→B | None | 21 | — | — | — | 2165 | 1 | — | None | N | -5 | 6.0 | — | teams sent to station 734 watching station 1 |
| 19 | B→A | 62 | 62 | 1.00 | 7208 | 11075 | — | 1 | 44% | 5 | Y | None | None | Confirming crews at 734, maintaining observation o | confirming crews at 734 maintaining observation of |
| 20 | A→B | None | 16 | — | — | — | 3543 | 1 | — | None | N | -4 | 5.25 | — | station ones water level is high needs help |

## Full Conversation Transcript

| # | Sender | Natural | Encoded/Decoded |
|---|--------|---------|-----------------|
| 1 | Role B | Alert: Flood warning issued for Lawrence Township. Checking  | alert flood warning lawrence township sensor data check |
| 2 | Role A | — | confirm sensor readings water levels high at stations 3 and  |
| 3 | Role B | Okay, water levels are elevated at stations 3 and 7. We need | okay water high at stations 3 and 7 assess impacts alert ser |
| 4 | Role A | — | traffic shows water on route 13 mile 7 i am alerting police  |
| 5 | Role B | Confirming traffic reports, water is also present on route 1 | traffic reports confirm water on route 100 mile 3 request sa |
| 6 | Role A | — | confirm sandbag request station 8 reports high water |
| 7 | Role B | Station 8 confirms high water, dispatching crews to that loc | station 8 says high water send crews now watch station 1 too |
| 8 | Role A | — | water high send teams now |
| 9 | Role B | Dispatching teams to station 7432, prioritizing immediate re | send teams to station 7432 respond quickly monitor stations  |
| 10 | Role A | — | teams to station 7432 monitor stations 3 and 7 |
| 11 | Role B | Confirming, teams are monitoring stations 3, 7, and 7432. We | confirming teams watch stations 3 7 and 7432 waiting for dep |
| 12 | Role A | — | bags are coming water level is stable |
| 13 | Role B | Water levels are stable at 12, confirming sensor 734. Let’s  | levels are stable 12 sensor 734 reduce monitoring at station |
| 14 | Role A | — | confirming levels stable monitoring at station one |
| 15 | Role B | Confirming, we will continue monitoring station one. | confirm we will monitor station one |
| 16 | Role A | — | level high watch it |
| 17 | Role B | Confirming, dispatching crews to station 734 immediately. | confirming dispatching crews to station 734 immediately |
| 18 | Role A | — | teams sent to station 734 watching station 1 |
| 19 | Role B | Confirming crews at 734, maintaining observation of station  | confirming crews at 734 maintaining observation of station o |
| 20 | Role A | — | station ones water level is high needs help |
