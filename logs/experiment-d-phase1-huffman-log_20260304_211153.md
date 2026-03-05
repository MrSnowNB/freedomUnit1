---
title: "Experiment D — Phase 1 (Pre-Tokenizer) — Huffman (4K) — Run Log"
date: 2026-03-05T02:11:53.335613+00:00
version: 4.0
phase: phase1
codec: huffman
model: gemma3:latest
role: B
node: "!0408a160"
peer: "!07c01855"
messages_per_node: 10
pretokenizer: True
llm_codec: False
fallback_threshold: 0.7
---

# Experiment D — Phase 1 (Pre-Tokenizer) — Huffman (4K) — Results

## Per-Message Metrics

| # | Dir | Raw | Cmp | Ratio | Inf(ms) | Tokens | Pg | Hit% | ESC | RSSI | SNR | Message |
|---|-----|-----|-----|-------|---------|--------|----|------|-----|------|-----|---------|
| 1 | B→A | 94 | 54 | 1.74 | 2378 | 20 | 1 | 77% | 3 | None | None | alert flood warning issued for lawrence township requesting  |
| 2 | A→B | None | 62 | — | — | None | 1 | — | None | -27 | 6.25 | agent 2 please report sensor readings for zone 1 and zone 3  |
| 3 | B→A | 119 | 62 | 1.92 | 3813 | 37 | 1 | 95% | 1 | None | None | zone 1 reports 1 point 5 feet of water and zone 3 is current |
| 4 | A→B | None | 42 | — | — | None | 1 | — | None | -31 | 5.75 | activate the pump in zone 3 as well zone 1 is now at 1 point |
| 5 | B→A | 52 | 46 | 1.13 | 3004 | 13 | 1 | 57% | 3 | None | None | zone 3 pump activated confirming sensor readings now |
| 6 | A→B | None | 45 | — | — | None | 1 | — | None | -29 | 7.5 | confirming 0 point 8 feet in zone 3 prepare for potential ov |
| 7 | B→A | 54 | 37 | 1.46 | 2411 | 17 | 1 | 89% | 1 | None | None | zone 3 is now at 1 point 2 feet initiating backup pump |
| 8 | A→B | None | 56 | — | — | None | 1 | — | None | -27 | 6.0 | alert zone 1 is at 1 point 5 feet and zone 3 is now 1 point  |
| 9 | B→A | 94 | 61 | 1.54 | 3918 | 23 | 1 | 73% | 4 | None | None | deploying personnel to zone 1 is confirmed we need to monito |
| 10 | A→B | None | 43 | — | — | None | 1 | — | None | -21 | 5.75 | zone 3 is currently 1 point 2 feet maintain close monitoring |
| 11 | B→A | 60 | 36 | 1.67 | 3044 | 16 | 1 | 88% | 1 | None | None | zone 3 is now 1 point 8 feet requesting immediate assistance |
| 12 | A→B | None | 39 | — | — | None | 1 | — | None | -22 | 6.0 | dispatch additional emergency teams to zone 3 the water leve |
| 13 | B→A | 99 | 54 | 1.83 | 3930 | 29 | 1 | 93% | 1 | None | None | zone 1 is at 1 point 5 feet and zone 3 is now 1 point 8 feet |
| 14 | A→B | None | 23 | — | — | None | 1 | — | None | -19 | 6.0 | issue immediate evacuation orders for zone 1 and zone 3 |
| 15 | B→A | 42 | 28 | 1.50 | 1598 | 13 | 1 | 83% | 1 | None | None | evacuation confirmed for zone 1 and zone 3 |
| 16 | A→B | None | 36 | — | — | None | 1 | — | None | -24 | 5.75 | confirming evacuation completion monitor remaining sensors f |
| 17 | B→A | 60 | 25 | 2.40 | 2328 | 11 | 1 | 88% | 1 | None | None | all sensors are reporting normal levels monitoring continues |
| 18 | A→B | None | 53 | — | — | None | 1 | — | None | -24 | 5.75 | confirming normal sensor readings maintaining network vigila |
| 19 | B→A | 60 | 25 | 2.40 | 2306 | 11 | 1 | 88% | 1 | None | None | all sensors are reporting normal levels monitoring continues |
| 20 | A→B | None | 53 | — | — | None | 1 | — | None | -25 | 6.5 | confirming normal sensor readings maintaining network vigila |

## Full Conversation Transcript

| # | Sender | Text |
|---|--------|------|
| 1 | Role B | Alert: Flood warning issued for Lawrence Township. Requesting sensor status updates from Agent 2. |
| 2 | Role A | agent 2 please report sensor readings for zone 1 and zone 3 immediately confirm if any sensors are reporting water levels above 1 foot |
| 3 | Role B | Zone 1 reports 1.5 feet of water, and Zone 3 is currently at 0.8 feet. We need to activate the pump in Zone 1. |
| 4 | Role A | activate the pump in zone 3 as well zone 1 is now at 1 point 5 feet |
| 5 | Role B | Zone 3 pump activated. Confirming sensor readings now. |
| 6 | Role A | confirming 0 point 8 feet in zone 3 prepare for potential overflow |
| 7 | Role B | Zone 3 is now at 1.2 feet, initiating backup pump. |
| 8 | Role A | alert zone 1 is at 1 point 5 feet and zone 3 is now 1 point 2 feet deploy emergency personnel to zone 1 |
| 9 | Role B | Deploying personnel to Zone 1 is confirmed. We need to monitor Zone 3 closely for further rises. |
| 10 | Role A | zone 3 is currently 1 point 2 feet maintain close monitoring and prepare for further escalation |
| 11 | Role B | Zone 3 is now 1.8 feet, requesting immediate assistance. |
| 12 | Role A | dispatch additional emergency teams to zone 3 the water level has risen to 1 point 8 feet |
| 13 | Role B | Zone 1 is at 1.5 feet, and Zone 3 is now 1.8 feet; requesting immediate evacuation orders. |
| 14 | Role A | issue immediate evacuation orders for zone 1 and zone 3 |
| 15 | Role B | Evacuation confirmed for Zone 1 and Zone 3. |
| 16 | Role A | confirming evacuation completion monitor remaining sensors for further issues |
| 17 | Role B | All sensors are reporting normal levels, monitoring continues. |
| 18 | Role A | confirming normal sensor readings maintaining network vigilance |
| 19 | Role B | All sensors are reporting normal levels, monitoring continues. |
| 20 | Role A | confirming normal sensor readings maintaining network vigilance |
