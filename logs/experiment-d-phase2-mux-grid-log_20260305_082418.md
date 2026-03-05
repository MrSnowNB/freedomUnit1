---
title: "Experiment D — Phase 2 (LLM Codec) — MUX Grid — Run Log"
date: 2026-03-05T13:24:18.241557+00:00
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
| 1 | B→A | 55 | 35 | 1.57 | 3221 | 10567 | — | 1 | 75% | 2 | N | None | None | Alert: Flood warning issued for Lawrence Township. | alert flood warning lawrence township sensor data  |
| 2 | A→B | None | 38 | — | — | — | 3771 | 1 | — | None | N | -28 | 5.5 | — | sensor status confirmed water levels rising at sta |
| 3 | B→A | 99 | 33 | 3.00 | 3051 | 11573 | — | 1 | 100% | 0 | N | None | None | Station 3 is currently at 8.5 feet, and station 7  | station 3 is eight point five feet and station 7 i |
| 4 | A→B | None | 26 | — | — | — | 2855 | 1 | — | None | N | -28 | 6.25 | — | send help to stations three and seven watch levels |
| 5 | B→A | 86 | 33 | 2.61 | 3341 | 11745 | — | 1 | 100% | 0 | N | None | None | Station 3 is now at 9.1 feet, and station 7 at 8.8 | station 3 is 9 point 1 feet station 7 is 8 point 8 |
| 6 | A→B | None | 42 | — | — | — | 4014 | 1 | — | None | N | -27 | 5.75 | — | requesting more resources to stations 3 and 7 rise |
| 7 | B→A | 78 | 31 | 2.52 | 4019 | 11771 | — | 1 | 100% | 0 | N | None | None | Station 3 is now 9.8 feet, and station 7 is 9.5 fe | station 3 is 9 point 8 feet station 7 is 9 point 5 |
| 8 | A→B | None | 18 | — | — | — | 3499 | 1 | — | None | N | -28 | 5.75 | — | contact officials about flood levels at stations 3 |
| 9 | B→A | 57 | 23 | 2.48 | 4429 | 11443 | — | 1 | 100% | 0 | N | None | None | Station 3 is at 10.3 feet and station 7 is at 10.0 | station 3 is ten feet station 7 is ten feet need h |
| 10 | A→B | None | 9 | — | — | — | 2274 | 1 | — | None | N | -27 | 5.75 | — | help needed support sent |
| 11 | B→A | 78 | 31 | 2.52 | 6301 | 11879 | — | 1 | 100% | 0 | N | None | None | Station 3 is 10.6 feet, and station 7 is 10.3 feet | station 3 is 10 point 6 feet station 7 is 10 point |
| 12 | A→B | None | 26 | — | — | — | 3031 | 1 | — | None | N | -27 | 6.0 | — | levels at stations three and seven are ten point s |
| 13 | B→A | 68 | 37 | 1.84 | 5838 | 11772 | — | 1 | 94% | 1 | N | None | None | Station 3 is 10.9 feet and station 7 is 10.6 feet. | station 3 is 10 point 9 feet station 7 is 10 point |
| 14 | A→B | None | 26 | — | — | — | 3198 | 1 | — | None | N | -27 | 5.25 | — | levels at stations 3 and 7 are 10 point 9 and 10 p |
| 15 | B→A | 50 | 27 | 1.85 | 5365 | 11169 | — | 1 | 91% | 1 | N | None | None | Station 3 is 11.2 feet and station 7 is 10.9 feet. | station 3 is eleven feet and station 7 is ten feet |
| 16 | A→B | None | 25 | — | — | — | 3742 | 1 | — | None | N | -27 | 5.75 | — | levels at stations three and seven are one one poi |
| 17 | B→A | 48 | 20 | 2.40 | 5765 | 11224 | — | 1 | 100% | 0 | N | None | None | Station 3 is 11.5 feet, and station 7 is 11.2 feet | station 3 is ten feet and station 7 is nine feet |
| 18 | A→B | None | 26 | — | — | — | 3721 | 1 | — | None | N | -26 | 6.0 | — | levels at stations 3 and 7 are 10 point 0 and 9 po |
| 19 | B→A | 82 | 31 | 2.65 | 6624 | 11963 | — | 1 | 100% | 0 | N | None | None | Station 3 is 11.8 feet, and station 7 is 11.5 feet | station 3 is 11 point 8 feet station 7 is 11 point |
| 20 | A→B | None | 26 | — | — | — | 3796 | 1 | — | None | N | -36 | 6.5 | — | levels at stations 3 and 7 are 11 point 8 and 11 p |

## Full Conversation Transcript

| # | Sender | Natural | Encoded/Decoded |
|---|--------|---------|-----------------|
| 1 | Role B | Alert: Flood warning issued for Lawrence Township. Checking  | alert flood warning lawrence township sensor data check |
| 2 | Role A | — | sensor status confirmed water levels rising at stations 3 an |
| 3 | Role B | Station 3 is currently at 8.5 feet, and station 7 is at 7.2  | station 3 is eight point five feet and station 7 is seven po |
| 4 | Role A | — | send help to stations three and seven watch levels closely |
| 5 | Role B | Station 3 is now at 9.1 feet, and station 7 at 8.8 feet. We  | station 3 is 9 point 1 feet station 7 is 8 point 8 feet we m |
| 6 | Role A | — | requesting more resources to stations 3 and 7 rise is 9 poin |
| 7 | Role B | Station 3 is now 9.8 feet, and station 7 is 9.5 feet. We nee | station 3 is 9 point 8 feet station 7 is 9 point 5 feet need |
| 8 | Role A | — | contact officials about flood levels at stations 3 and 7 |
| 9 | Role B | Station 3 is at 10.3 feet and station 7 is at 10.0 feet. We  | station 3 is ten feet station 7 is ten feet need help now |
| 10 | Role A | — | help needed support sent |
| 11 | Role B | Station 3 is 10.6 feet, and station 7 is 10.3 feet. We are m | station 3 is 10 point 6 feet station 7 is 10 point 3 feet we |
| 12 | Role A | — | levels at stations three and seven are ten point six and ten |
| 13 | Role B | Station 3 is 10.9 feet and station 7 is 10.6 feet. We are ma | station 3 is 10 point 9 feet station 7 is 10 point 6 feet we |
| 14 | Role A | — | levels at stations 3 and 7 are 10 point 9 and 10 point 6 fee |
| 15 | Role B | Station 3 is 11.2 feet and station 7 is 10.9 feet. | station 3 is eleven feet and station 7 is ten feet |
| 16 | Role A | — | levels at stations three and seven are one one point zero an |
| 17 | Role B | Station 3 is 11.5 feet, and station 7 is 11.2 feet. | station 3 is ten feet and station 7 is nine feet |
| 18 | Role A | — | levels at stations 3 and 7 are 10 point 0 and 9 point 0 feet |
| 19 | Role B | Station 3 is 11.8 feet, and station 7 is 11.5 feet. We are c | station 3 is 11 point 8 feet station 7 is 11 point 5 feet we |
| 20 | Role A | — | levels at stations 3 and 7 are 11 point 8 and 11 point 5 fee |
