---
title: "Experiment D — Phase 2 (LLM Codec) — Huffman (4K) — Run Log"
date: 2026-03-05T13:24:18.255555+00:00
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
| 1 | B→A | 72 | 46 | 1.57 | 2747 | 11543 | — | 1 | 70% | 3 | Y | None | None | Alert: Flood warning issued for Lawrence Township. | alert flood warning issued for lawrence township i |
| 2 | A→B | None | 37 | — | — | — | 2543 | 1 | — | None | N | -45 | 7.0 | — | check sensor readings river level at sensor 3 is 1 |
| 3 | B→A | 98 | 44 | 2.23 | 2750 | 11579 | — | 1 | 88% | 2 | N | None | None | Sensor 7 reports a water level of 8.2 feet and ris | sensor seven reports water level eight point two f |
| 4 | A→B | None | 30 | — | — | — | 3496 | 1 | — | None | N | -39 | 7.25 | — | contacting agent sensor three 12 point 5 feet |
| 5 | B→A | 91 | 35 | 2.60 | 3110 | 11322 | — | 1 | 93% | 1 | N | None | None | Sensor 7 is now at 8.7 feet, accelerating rise. Le | sensor seven is now eight point seven feet rising  |
| 6 | A→B | None | 26 | — | — | — | 3399 | 1 | — | None | N | -38 | 5.5 | — | dispatch services to sensor seven sensor three is  |
| 7 | B→A | 83 | 44 | 1.89 | 3807 | 11652 | — | 1 | 92% | 1 | N | None | None | Sensor three remains at 12.5 feet, and sensor seve | sensor three is 12 point 5 feet sensor seven is 9  |
| 8 | A→B | None | 33 | — | — | — | 3214 | 1 | — | None | N | -37 | 6.75 | — | received preparing for closures based on sensor da |
| 9 | B→A | 66 | 40 | 1.65 | 3787 | 11174 | — | 1 | 80% | 2 | N | None | None | Sensor three is still at 12.5 feet; advise residen | sensor three is still 12 point 5 feet advise resid |
| 10 | A→B | None | 23 | — | — | — | 2901 | 1 | — | None | N | -41 | 6.5 | — | received alert evacuate near sensor three |
| 11 | B→A | 90 | 38 | 2.37 | 4785 | 11179 | — | 1 | 93% | 1 | N | None | None | Sensor seven is now 9.5 feet, intensifying the sit | sensor seven is now nine feet intensifying the sit |
| 12 | A→B | None | 35 | — | — | — | 2006 | 1 | — | None | N | -35 | 7.25 | — | confirming orders to evacuate areas near sensor se |
| 13 | B→A | 63 | 30 | 2.10 | 6037 | 11043 | — | 1 | 91% | 1 | N | None | None | Sensor seven is at 9.8 feet, and the water is spre | sensor seven is nine point eight feet water spread |
| 14 | A→B | None | 25 | — | — | — | 2446 | 1 | — | None | N | -44 | 6.0 | — | confirming new zone based on sensor data |
| 15 | B→A | 58 | 25 | 2.32 | 5990 | 11101 | — | 1 | 100% | 0 | N | None | None | Sensor three is at 12.7 feet; the zone expansion i | sensor three is 12 point 7 feet zone expansion is  |
| 16 | A→B | None | 35 | — | — | — | 2974 | 1 | — | None | N | -46 | 5.5 | — | received prioritizing evacuation due to rising riv |
| 17 | B→A | 46 | 30 | 1.53 | 5676 | 11090 | — | 1 | 86% | 1 | N | None | None | Sensor three is 12.7 feet; begin immediate evacuat | sensor three is 12 point 7 feet evacuate areas |
| 18 | A→B | None | 21 | — | — | — | 3874 | 1 | — | None | N | -46 | 6.5 | — | received enacting full evacuation orders |
| 19 | B→A | 71 | 29 | 2.45 | 5233 | 11048 | — | 1 | 92% | 1 | N | None | None | Sensor three is now 12.9 feet; continue the full e | sensor three is now twelve point nine feet continu |
| 20 | A→B | None | 35 | — | — | — | 3316 | 1 | — | None | N | -44 | 6.0 | — | acknowledged maintaining full evacuation orders |

## Full Conversation Transcript

| # | Sender | Natural | Encoded/Decoded |
|---|--------|---------|-----------------|
| 1 | Role B | Alert: Flood warning issued for Lawrence Township. Initiatin | alert flood warning issued for lawrence township initiating  |
| 2 | Role A | — | check sensor readings river level at sensor 3 is 12 point 5  |
| 3 | Role B | Sensor 7 reports a water level of 8.2 feet and rising. We ne | sensor seven reports water level eight point two feet rising |
| 4 | Role A | — | contacting agent sensor three 12 point 5 feet |
| 5 | Role B | Sensor 7 is now at 8.7 feet, accelerating rise. Let’s reques | sensor seven is now eight point seven feet rising fast reque |
| 6 | Role A | — | dispatch services to sensor seven sensor three is 12 point 5 |
| 7 | Role B | Sensor three remains at 12.5 feet, and sensor seven is now 9 | sensor three is 12 point 5 feet sensor seven is 9 point 1 fe |
| 8 | Role A | — | received preparing for closures based on sensor data |
| 9 | Role B | Sensor three is still at 12.5 feet; advise residents in low- | sensor three is still 12 point 5 feet advise residents to ev |
| 10 | Role A | — | received alert evacuate near sensor three |
| 11 | Role B | Sensor seven is now 9.5 feet, intensifying the situation. We | sensor seven is now nine feet intensifying the situation we  |
| 12 | Role A | — | confirming orders to evacuate areas near sensor seven |
| 13 | Role B | Sensor seven is at 9.8 feet, and the water is spreading. We  | sensor seven is nine point eight feet water spreads expand z |
| 14 | Role A | — | confirming new zone based on sensor data |
| 15 | Role B | Sensor three is at 12.7 feet; the zone expansion is critical | sensor three is 12 point 7 feet zone expansion is critical |
| 16 | Role A | — | received prioritizing evacuation due to rising river level |
| 17 | Role B | Sensor three is 12.7 feet; begin immediate evacuation of all | sensor three is 12 point 7 feet evacuate areas |
| 18 | Role A | — | received enacting full evacuation orders |
| 19 | Role B | Sensor three is now 12.9 feet; continue the full evacuation. | sensor three is now twelve point nine feet continue the full |
| 20 | Role A | — | acknowledged maintaining full evacuation orders |
