---
title: "Experiment E — Phase 1 (Pre-Tokenizer) — MUX Grid — Run Log"
date: 2026-03-05T16:13:47.959402+00:00
version: 5.0
phase: phase1
codec: mux_grid
model: test01
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
pretokenizer: True
llm_codec: False
fallback_threshold: 0.7
---

# Experiment E — Phase 1 (Pre-Tokenizer) — MUX Grid — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Inf(ms) | Tokens | Pg | Hit% | ESC | RSSI | SNR | Message |
|---|-----|-----|-----|-------|---------|--------|----|------|-----|------|-----|---------|
| 1 | B→A | 124 | 92 | 1.35 | 1565 | 25 | 1 | 71% | 6 | None | None | the flood warning is active in lawrence township nj two sens |
| 2 | A→B | None | 70 | — | — | None | 1 | — | None | -27 | 5.5 | 2 sensors are working one is offline im checking the status  |
| 3 | B→A | 142 | 55 | 2.58 | 1763 | 28 | 1 | 92% | 2 | None | None | the flood warning is active two sensors are operational one  |
| 4 | A→B | None | 47 | — | — | None | 1 | — | None | -27 | 5.25 | 911 dispatch is on standby ill send a status report to the c |
| 5 | B→A | 137 | 55 | 2.49 | 1918 | 28 | 1 | 92% | 2 | None | None | the flood warning is active two sensors are operational one  |
| 6 | A→B | None | 50 | — | — | None | 1 | — | None | -27 | 6.25 | 911 is ready ill relay updates every 5 minutes stay alert fo |
| 7 | B→A | 157 | 59 | 2.66 | 1956 | 31 | 1 | 93% | 2 | None | None | the flood warning is active two sensors are operational one  |
| 8 | A→B | None | 30 | — | — | None | 1 | — | None | -27 | 6.0 | 100 monitoring progress youll notify me if conditions change |
| 9 | B→A | 157 | 59 | 2.66 | 2015 | 31 | 1 | 93% | 2 | None | None | the flood warning is active two sensors are operational one  |
| 10 | A→B | None | 20 | — | — | None | 1 | — | None | -29 | 6.75 | 911 will continue tracking this situation stay safe |
| 11 | B→A | 157 | 59 | 2.66 | 2127 | 31 | 1 | 93% | 2 | None | None | the flood warning is active two sensors are operational one  |
| 12 | A→B | None | 27 | — | — | None | 1 | — | None | -28 | 7.0 | 911 is active ill be in touch thank you for your attention |
| 13 | B→A | 157 | 59 | 2.66 | 2154 | 31 | 1 | 93% | 2 | None | None | the flood warning is active two sensors are operational one  |
| 14 | A→B | None | 39 | — | — | None | 1 | — | None | -28 | 6.75 | 911 remains on standby ill provide updates as they become av |
| 15 | B→A | 0 | 3 | — | 51 | 0 | 1 | 100% | 0 | None | None |  |
| 16 | A→B | None | 30 | — | — | None | 1 | — | None | -36 | 6.25 | 911 has been notified we will assist further if needed |
| 17 | B→A | 55 | 15 | 3.67 | 829 | 10 | 1 | 100% | 0 | None | None | were monitoring the situation and will keep you updated |
| 18 | A→B | None | 27 | — | — | None | 1 | — | None | -37 | 6.25 | 911 is monitoring thank you for your patience |
| 19 | B→A | 58 | 17 | 3.41 | 877 | 11 | 1 | 100% | 0 | None | None | were handling the flood warning and will keep you informed |
| 20 | A→B | None | 31 | — | — | None | 1 | — | None | -39 | 6.75 | 911 is on standby and ready for further updates stay safe |

## Full Conversation Transcript

| # | Sender | Text |
|---|--------|------|
| 1 | Role B | The flood warning is active in Lawrence Township, NJ. Two sensors are operational, one is not responding. We need to investigate. |
| 2 | Role A | 2 sensors are working one is offline im checking the status now sensor a is 85 functional sensor b is 60 ill need backup power for b soon we should contact the main office for support |
| 3 | Role B | The flood warning is active. Two sensors are operational; one is offline and may need backup power. We should contact the main office for support. |
| 4 | Role A | 911 dispatch is on standby ill send a status report to the control center please keep an eye on the situation |
| 5 | Role B | The flood warning is active. Two sensors are operational; one is offline and may need backup power. We’ll contact the main office for support. |
| 6 | Role A | 911 is ready ill relay updates every 5 minutes stay alert for new sensor readings |
| 7 | Role B | The flood warning is active. Two sensors are operational; one is offline and may need backup power. We’ll keep monitoring and contact the main office for updates. |
| 8 | Role A | 100 monitoring progress youll notify me if conditions change thank you for your cooperation |
| 9 | Role B | The flood warning is active. Two sensors are operational; one is offline and may need backup power. We’ll keep monitoring and contact the main office for updates. |
| 10 | Role A | 911 will continue tracking this situation stay safe |
| 11 | Role B | The flood warning is active. Two sensors are operational; one is offline and may need backup power. We’ll keep monitoring and contact the main office for updates. |
| 12 | Role A | 911 is active ill be in touch thank you for your attention |
| 13 | Role B | The flood warning is active. Two sensors are operational; one is offline and may need backup power. We’ll keep monitoring and contact the main office for updates. |
| 14 | Role A | 911 remains on standby ill provide updates as they become available stay safe |
| 15 | Role B | — |
| 16 | Role A | 911 has been notified we will assist further if needed |
| 17 | Role B | We’re monitoring the situation and will keep you updated. |
| 18 | Role A | 911 is monitoring thank you for your patience |
| 19 | Role B | We’re handling the flood warning and will keep you informed. |
| 20 | Role A | 911 is on standby and ready for further updates stay safe |
