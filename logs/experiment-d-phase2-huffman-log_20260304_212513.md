---
title: "Experiment D — Phase 2 (LLM Codec) — Huffman (4K) — Run Log"
date: 2026-03-05T02:25:13.647210+00:00
version: 4.0
phase: phase2
codec: huffman
model: gemma3:latest
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
pretokenizer: True
llm_codec: True
fallback_threshold: 0.7
---

# Experiment D — Phase 2 (LLM Codec) — Huffman (4K) — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Gen(ms) | Enc(ms) | Dec(ms) | Pg | Hit% | ESC | FB | RSSI | SNR | Natural | Encoded |
|---|-----|-----|-----|-------|---------|---------|---------|----|------|-----|----|----- |-----|---------|---------|
| 1 | B→A | 47 | 20 | 2.35 | 3528 | 11059 | — | 1 | 100% | 0 | N | None | None | Alert: Flood warning issued for Lawrence Township. | alert flood warning request update from agent 2 |
| 2 | A→B | None | 23 | — | — | — | 3512 | 1 | — | None | N | -4 | 6.0 | — | received checking sensors in zone 3 |
| 3 | B→A | 43 | 29 | 1.48 | 4060 | 11083 | — | 1 | 71% | 2 | N | None | None | Zone 3 sensors report water levels at 1.5 feet and | sensors report water high advise next steps |
| 4 | A→B | None | 14 | — | — | — | 3758 | 1 | — | None | N | -4 | 6.5 | — | confirm high water request evacuation |
| 5 | B→A | 86 | 47 | 1.83 | 3131 | 11347 | — | 1 | 82% | 2 | Y | None | None | Confirming evacuation of sensors 734 and 801. Disp | confirming evacuation of sensors 734 and 801 dispa |
| 6 | A→B | None | 16 | — | — | — | 3429 | 1 | — | None | N | -4 | 7.25 | — | received sending help to zone 3 |
| 7 | B→A | 61 | 31 | 1.97 | 3450 | 11169 | — | 1 | 89% | 1 | N | None | None | Confirming emergency services are en route to zone | confirming services are coming to zone 3 monitor w |
| 8 | A→B | None | 18 | — | — | — | 2579 | 1 | — | None | N | -4 | 5.75 | — | confirm services are here and watching zone 3 |
| 9 | B→A | 46 | 22 | 2.09 | 4386 | 11221 | — | 1 | 100% | 0 | N | None | None | Water levels are now at 2.1 feet.  Continue monito | water is 2 point 1 feet watch prepare for more |
| 10 | A→B | None | 29 | — | — | — | 3823 | 1 | — | None | N | -4 | 6.0 | — | confirming two feet of water seek higher ground no |
| 11 | B→A | 89 | 48 | 1.85 | 4429 | 11552 | — | 1 | 83% | 2 | Y | None | None | Confirming evacuation order; residents near sensor | confirming evacuation order residents near sensors |
| 12 | A→B | None | 18 | — | — | — | 3054 | 1 | — | None | N | -3 | 6.0 | — | received watching water levels in zone 3 |
| 13 | B→A | 25 | 13 | 1.92 | 4764 | 11662 | — | 1 | 100% | 0 | N | None | None | Water levels are now at 2.5 feet; we need to expan | water is high expand zone |
| 14 | A→B | None | 22 | — | — | — | 3565 | 1 | — | None | N | -2 | 6.0 | — | confirm expansion zone in zone 3 request updates o |
| 15 | B→A | 49 | 27 | 1.81 | 4968 | 11884 | — | 1 | 89% | 1 | N | None | None | Water levels at 2.5 feet, expanding evacuation to  | water high two point five feet evacuate zone four |
| 16 | A→B | None | 31 | — | — | — | 3491 | 1 | — | None | N | -2 | 7.5 | — | order evacuate zone 4 water 2 point 5 feet |
| 17 | B→A | 41 | 16 | 2.56 | 5289 | 11597 | — | 1 | 100% | 0 | N | None | None | Confirming evacuation of zone 4. Continue monitori | confirm evacuation zone four monitor data |
| 18 | A→B | None | 20 | — | — | — | 3085 | 1 | — | None | N | -1 | 7.0 | — | confirm evacuation zone 4 water two feet five |
| 19 | B→A | 27 | 14 | 1.93 | 5635 | 11309 | — | 1 | 100% | 0 | N | None | None | Water levels are at 2.5 feet, preparing for potent | water is high may rise more |
| 20 | A→B | None | 44 | — | — | — | 3736 | 1 | — | None | N | -2 | 5.5 | — | confirming continued high water levels preparing f |

## Full Conversation Transcript

| # | Sender | Natural | Encoded/Decoded |
|---|--------|---------|-----------------|
| 1 | Role B | Alert: Flood warning issued for Lawrence Township. Requestin | alert flood warning request update from agent 2 |
| 2 | Role A | — | received checking sensors in zone 3 |
| 3 | Role B | Zone 3 sensors report water levels at 1.5 feet and rising. P | sensors report water high advise next steps |
| 4 | Role A | — | confirm high water request evacuation |
| 5 | Role B | Confirming evacuation of sensors 734 and 801. Dispatch emerg | confirming evacuation of sensors 734 and 801 dispatch emerge |
| 6 | Role A | — | received sending help to zone 3 |
| 7 | Role B | Confirming emergency services are en route to zone 3.  We ne | confirming services are coming to zone 3 monitor water level |
| 8 | Role A | — | confirm services are here and watching zone 3 |
| 9 | Role B | Water levels are now at 2.1 feet.  Continue monitoring and p | water is 2 point 1 feet watch prepare for more |
| 10 | Role A | — | confirming two feet of water seek higher ground now |
| 11 | Role B | Confirming evacuation order; residents near sensors 734 and  | confirming evacuation order residents near sensors 734 and 8 |
| 12 | Role A | — | received watching water levels in zone 3 |
| 13 | Role B | Water levels are now at 2.5 feet; we need to expand the evac | water is high expand zone |
| 14 | Role A | — | confirm expansion zone in zone 3 request updates on area |
| 15 | Role B | Water levels at 2.5 feet, expanding evacuation to zone 4. | water high two point five feet evacuate zone four |
| 16 | Role A | — | order evacuate zone 4 water 2 point 5 feet |
| 17 | Role B | Confirming evacuation of zone 4. Continue monitoring all sen | confirm evacuation zone four monitor data |
| 18 | Role A | — | confirm evacuation zone 4 water two feet five |
| 19 | Role B | Water levels are at 2.5 feet, preparing for potential furthe | water is high may rise more |
| 20 | Role A | — | confirming continued high water levels preparing for potenti |
