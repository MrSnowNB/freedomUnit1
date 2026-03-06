# CyberMesh v7.0 "Smart Router" — Experiment G-3

**Run:**         `mux_grid-333k-keyword`  
**Role:**        A  
**Peer:**        !07c01855  
**Engine:**      mux_grid  
**Codebook:**    333k  
**Mode:**        keyword  
**Timestamp:**   20260306_163127  

---

## TX Messages

| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | extract_ms | classify_ms | pkts | text | wire_hex |
|---|-------|-------|-------|-------|----------|-----|----|-----------|-------------|------|------|----------|
| 1 | strict | 70 | 36 | 1.9444 | 100.0 | — | — | — | 0.25 | 1 | `Check the sensor status and assess conditions for the first five zones.` | `0010f000000001aa2000259000002001d2e0001c300000600000000005200043f0024050` |
| 2 | strict | 67 | 39 | 1.7179 | 100.0 | — | — | — | 0.21 | 1 | `I will check the sensor status and conditions for zones one to five.` | `0000d00001f00010f000000001aa20002590000020001c300000600240500002c00000300043f0` |
| 3 | strict | 92 | 48 | 1.9167 | 100.0 | — | — | — | 0.22 | 1 | `I’m checking the sensors for zones one through five. I’ll gather the latest data and conditions.` | `00c450011b10000000028c100000600240500002c0000a500043f0018770029f400000000024b0000820000020001c30` |
| 4 | strict | 143 | 78 | 1.8333 | 100.0 | — | — | — | 0.39 | 1 | `I’m checking the sensors for zones one through five. Water levels are high in zones one and two, and three. We should prepare for possible flooding.` | `00c450011b10000000028c100000600240500002c0000a500043f00014d0005eb0000130000a300000500240500002c00000200007300000200013900001e0000850014330000060002780044ef0` |
| 5 | strict | 153 | 87 | 1.7586 | 100.0 | — | — | — | 0.34 | 1 | `I’ve checked the sensors for zones one to five. Water levels are high in zones one and two, and three. We should prepare for possible flooding in those areas.` | `046800018c90000000028c100000600240500002c00000300043f00014d0005eb0000130000a300000500240500002c00000200007300000200013900001e0000850014330000060002780044ef0000050000ed00027f0` |
| 6 | strict | 99 | 54 | 1.8333 | 100.0 | — | — | — | 0.36 | 1 | `I’ve confirmed the high water levels in zones one and two. Immediate action is needed for those areas.` | `046800019240000000000a300014d0005eb00000500240500002c0000020000730011410001d80000070005660000060000ed00027f0` |
| 7 | strict | 98 | 54 | 1.8148 | 100.0 | — | — | — | 0.36 | 1 | `I’ve confirmed the high water levels in zones one and two. Urgent action is required for those areas.` | `046800019240000000000a300014d0005eb00000500240500002c000002000073002e420001d80000070001e40000060000ed00027f0` |
| 8 | strict | 98 | 54 | 1.8148 | 100.0 | — | — | — | 0.33 | 1 | `I’ve confirmed the high water levels in zones one and two. Urgent action is required for those areas.` | `046800019240000000000a300014d0005eb00000500240500002c000002000073002e420001d80000070001e40000060000ed00027f0` |
| 9 | strict | 52 | 24 | 2.1667 | 100.0 | — | — | — | 0.25 | 1 | `I’m coordinating with the team for emergency response.` | `00c45003eb200000c0000000001c00000060009fc0004fe0` |
| 10 | strict | 52 | 24 | 2.1667 | 100.0 | — | — | — | 0.35 | 1 | `I’m coordinating with the team for emergency response.` | `00c45003eb200000c0000000001c00000060009fc0004fe0` |

## RX Messages

| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |
|---|-------|-------|----|----------|------|-----|------|--------------|
| 1 | strict | 50 | 16 | — | -18 | 5.75 | 1 | `the flood warning is active for the area we need to check sensors and assess conditions` |
| 2 | strict | 38 | 12 | — | -19 | 5.5 | 1 | `coordinate with me to review sensor data for zones one through five` |
| 3 | strict | 32 | 10 | — | -19 | 6.0 | 1 | `ill review the sensor data for zones one to five` |
| 4 | strict | 59 | 19 | — | -19 | 6.0 | 1 | `sensors are online water levels are high in zones one two and three we should prepare for potential flooding` |
| 5 | strict | 53 | 17 | — | -18 | 6.0 | 1 | `we have high water levels in zones one and two prepare for possible flooding in those areas` |
| 6 | strict | 56 | 18 | — | -18 | 6.0 | 1 | `the situation is serious high water in zones one and two needs immediate attention plan for possible flooding` |
| 7 | strict | 47 | 15 | — | -17 | 7.5 | 1 | `the flood warning is real high water in zones one and two requires urgent action` |
| 8 | strict | 53 | 17 | — | -17 | 7.75 | 1 | `the flood warning is real zones one and two have high water levels and need urgent help` |
| 9 | strict | 23 | 7 | — | -18 | 6.0 | 1 | `coordinate with the team for emergency response` |
| 10 | strict | 38 | 12 | — | -19 | 6.0 | 1 | `we are handling the flood warning now emergency response is being coordinated` |

---

## Summary

- TX messages:       10
- RX messages:       10
- Avg compression:   1.897:1
