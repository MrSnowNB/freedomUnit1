---
title: "Experiment C — Huffman (4K) — Run Log"
date: 2026-03-05T01:31:02.553269+00:00
version: 3.0.0
codec: huffman
model: gemma3:latest
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
---

# Experiment C — Huffman (4K) — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Inf(ms) | Tokens | Pages | Hit% | ESC | RSSI | SNR | Message (truncated) |
|---|-----|-----|-----|-------|---------|--------|-------|------|-----|------|-----|---------------------|
| 1 | B→A | 97 | 66 | 1.47 | 1207 | 20 | 1 | 77% | 3 | None | None | Alert: Flood warning issued for Lawrence Township. Requestin |
| 2 | A→B | None | 84 | — | — | None | 1 | — | None | -7 | 5.75 | Agent 2, please report water level readings from all sensors |
| 3 | B→A | 122 | 68 | 1.79 | 2127 | 32 | 1 | 90% | 2 | None | None | Sensor 3 at the Rahway River shows a rapid rise to 8.5 feet. |
| 4 | A→B | None | 88 | — | — | None | 1 | — | None | -8 | 6.75 | Confirming rapid rise at Rahway River, Sensor 3 at 8.5 feet. |
| 5 | B→A | 124 | 69 | 1.80 | 2162 | 28 | 1 | 89% | 2 | None | None | Turbidity at Sensor 7 is now at 95%, significantly above nor |
| 6 | A→B | None | 64 | — | — | None | 1 | — | None | -3 | 6.25 | Notify township emergency services of the escalating situati |
| 7 | B→A | 146 | 75 | 1.95 | 2182 | 32 | 1 | 86% | 3 | None | None | Sensor 10 near the Lawrence Middle School is also reporting  |
| 8 | A→B | None | 100 | — | — | None | 1 | — | None | -3 | 5.75 | Confirming 6.2 feet at Sensor 10, prioritizing evacuation ro |
| 9 | B→A | 128 | 67 | 1.91 | 2259 | 30 | 1 | 89% | 2 | None | None | Sensor 10 is now at 7.1 feet, requiring a revised evacuation |
| 10 | A→B | None | 66 | — | — | None | 1 | — | None | -3 | 5.5 | Confirming 7.1 feet at Sensor 10, expedite evacuation route  |
| 11 | B→A | 65 | 49 | 1.33 | 1752 | 20 | 1 | 80% | 2 | None | None | Sensor 10 is at 7.5 feet; we must finalize evacuation routes |
| 12 | A→B | None | 50 | — | — | None | 1 | — | None | -3 | 5.5 | Confirming 7.5 feet at Sensor 10, urgent action needed for e |
| 13 | B→A | 69 | 48 | 1.44 | 2630 | 18 | 1 | 75% | 2 | None | None | Sensor 10 is at 7.5 feet – initiate immediate evacuation pro |
| 14 | A→B | None | 52 | — | — | None | 1 | — | None | -3 | 6.0 | Confirming 7.5 feet at Sensor 10, deploying emergency respon |
| 15 | B→A | 94 | 46 | 2.04 | 1765 | 23 | 1 | 92% | 1 | None | None | Sensor 10 is at 7.5 feet – all residents near the middle sch |
| 16 | A→B | None | 51 | — | — | None | 1 | — | None | -3 | 5.75 | Confirming 7.5 feet at Sensor 10, focusing on resident evacu |
| 17 | B→A | 86 | 42 | 2.05 | 1746 | 21 | 1 | 91% | 1 | None | None | Sensor 10 is at 7.5 feet – standby for further instructions  |
| 18 | A→B | None | 49 | — | — | None | 1 | — | None | -3 | 5.75 | Confirming 7.5 feet at Sensor 10, awaiting further instructi |
| 19 | B→A | 72 | 34 | 2.12 | 1661 | 20 | 1 | 100% | 0 | None | None | Sensor 10 is at 7.5 feet – continue monitoring and report an |
| 20 | A→B | None | 52 | — | — | None | 1 | — | None | -3 | 5.5 | Confirming 7.5 feet at Sensor 10, maintaining continuous mon |

## Full Conversation Transcript

| # | Sender | Text |
|---|--------|------|
| 1 | Role B | Alert: Flood warning issued for Lawrence Township. Requesting sensor status updates from Agent 2. |
| 2 | Role A | Agent 2, please report water level readings from all sensors in the township. Confirm if any sensors are reporting unusual activity. |
| 3 | Role B | Sensor 3 at the Rahway River shows a rapid rise to 8.5 feet. Sensor 7 near the Post Road is reporting increased turbidity. |
| 4 | Role A | Confirming rapid rise at Rahway River, Sensor 3 at 8.5 feet. Agent 2, please assess turbidity at Sensor 7. |
| 5 | Role B | Turbidity at Sensor 7 is now at 95%, significantly above normal. We need to activate the emergency alert system immediately. |
| 6 | Role A | Notify township emergency services of the escalating situation. Confirm sensor status and prepare for potential evacuations. |
| 7 | Role B | Sensor 10 near the Lawrence Middle School is also reporting a rise to 6.2 feet. We should coordinate with emergency services on evacuation routes. |
| 8 | Role A | Confirming 6.2 feet at Sensor 10, prioritizing evacuation routes near the middle school. Lets coordinate with emergency services on immediate evacuation plans. |
| 9 | Role B | Sensor 10 is now at 7.1 feet, requiring a revised evacuation plan. We need to confirm evacuation routes with emergency services. |
| 10 | Role A | Confirming 7.1 feet at Sensor 10, expedite evacuation route confirmation with emergency services. |
| 11 | Role B | Sensor 10 is at 7.5 feet; we must finalize evacuation routes now. |
| 12 | Role A | Confirming 7.5 feet at Sensor 10, urgent action needed for evacuation. |
| 13 | Role B | Sensor 10 is at 7.5 feet – initiate immediate evacuation protocols. |
| 14 | Role A | Confirming 7.5 feet at Sensor 10, deploying emergency response teams. |
| 15 | Role B | Sensor 10 is at 7.5 feet – all residents near the middle school should evacuate immediately. |
| 16 | Role A | Confirming 7.5 feet at Sensor 10, focusing on resident evacuation. |
| 17 | Role B | Sensor 10 is at 7.5 feet – standby for further instructions from emergency services. |
| 18 | Role A | Confirming 7.5 feet at Sensor 10, awaiting further instructions. |
| 19 | Role B | Sensor 10 is at 7.5 feet – continue monitoring and report any changes. |
| 20 | Role A | Confirming 7.5 feet at Sensor 10, maintaining continuous monitoring. |
