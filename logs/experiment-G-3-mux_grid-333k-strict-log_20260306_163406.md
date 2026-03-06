# CyberMesh v7.0 "Smart Router" — Experiment G-3

**Run:**         `mux_grid-333k-strict`  
**Role:**        A  
**Peer:**        !07c01855  
**Engine:**      mux_grid  
**Codebook:**    333k  
**Mode:**        strict_only  
**Timestamp:**   20260306_163406  

---

## TX Messages

| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | extract_ms | classify_ms | pkts | text | wire_hex |
|---|-------|-------|-------|-------|----------|-----|----|-----------|-------------|------|------|----------|
| 1 | strict | 104 | 50 | 2.08 | 93.75 | 1 | — | — | — | 1 | `Check the sensor status at 5 locations. Assess conditions and gather data. Prepare emergency response plan.` | `0010f000000001aa20002590000150fffff00135006bb001d2e0001c30000020029f40000820014330009fc0004fe0001df0` |
| 2 | strict | 111 | 57 | 1.9474 | 100.0 | — | — | — | — | 1 | `I will check the sensors at five locations. I’ll gather the latest data and start planning the emergency response.` | `0000d00001f00010f0000000028c100001500043f0006bb0018770029f400000000024b0000820000020001d90004420000000009fc0004fe0` |
| 3 | strict | 103 | 54 | 1.9074 | 100.0 | — | — | — | — | 1 | `I’m checking the sensors at five locations now. I’ll gather the latest data and prepare the emergency plan.` | `00c450011b10000000028c100001500043f0006bb00004a0018770029f400000000024b0000820000020014330000000009fc0001df0` |
| 4 | strict | 100 | 57 | 1.7544 | 100.0 | — | — | — | — | 1 | `I am checking the sensors at five sites. I will gather the latest data and prepare the emergency plan.` | `0000d0000530011b10000000028c100001500043f00016a00000d00001f0029f400000000024b0000820000020014330000000009fc0001df0` |
| 5 | strict | 134 | 72 | 1.8611 | 100.0 | — | — | — | — | 1 | `I am checking the sensors at five sites and will gather the latest data. I’m preparing the emergency response plan based on the findings.` | `0000d0000530011b10000000028c100001500043f00016a00000200001f0029f400000000024b000082000c45001d450000000009fc0004fe0001df0001080000080000000014590` |
| 6 | strict | 110 | 63 | 1.746 | 100.0 | — | — | — | — | 1 | `I am reviewing the sensor data from five sites. I will prepare the emergency response plan based on what I find.` | `0000d000053003090000000001aa200008200001400043f00016a00000d00001f0014330000000009fc0004fe0001df00010800000800003700000d0000630` |
| 7 | strict | 72 | 39 | 1.8462 | 100.0 | — | — | — | — | 1 | `I am reviewing data from five sites and will finalize the emergency plan.` | `0000d00005300309000008200001400043f00016a00000200001f0078e60000000009fc0001df0` |
| 8 | strict | 72 | 36 | 2.0 | 100.0 | — | — | — | — | 1 | `I am assessing the situation at five sites and coordinating the response.` | `0000d0000530030380000000009f500001500043f00016a000002003eb20000000004fe0` |
| 9 | strict | 76 | 39 | 1.9487 | 100.0 | — | — | — | — | 1 | `I am assessing the flood warning at five sites and coordinating the response.` | `0000d000053003038000000001a680006b900001500043f00016a000002003eb20000000004fe0` |
| 10 | strict | 86 | 42 | 2.0476 | 100.0 | — | — | — | — | 1 | `I am checking sensors at five locations and gathering data. Emergency response is ready.` | `0000d0000530011b10028c100001500043f0006bb0000020020940000820009fc0004fe00000700064f0` |

## RX Messages

| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |
|---|-------|-------|----|----------|------|-----|------|--------------|
| 1 | strict | 47 | 15 | — | -21 | 7.25 | 1 | `the flood warning is active we need to check the sensors and prepare for response` |
| 2 | strict | 65 | 21 | — | -18 | 6.5 | 1 | `coordinate with the team to check five sensors first gather data on the current situation start planning the emergency response now` |
| 3 | strict | 56 | 18 | — | -18 | 5.75 | 1 | `let us check the sensors at five sites and assess the situation data will guide our emergency plan` |
| 4 | strict | 41 | 13 | — | -19 | 7.0 | 1 | `we are checking five sensors now data will help us prepare the plan` |
| 5 | strict | 44 | 14 | — | -21 | 6.0 | 1 | `we are monitoring five sites and collecting data now emergency response is being prepared` |
| 6 | strict | 47 | 15 | — | -22 | 5.75 | 1 | `we are handling five sensor sites data is coming in now emergency response is ready` |
| 7 | strict | 38 | 12 | — | -22 | 6.25 | 1 | `i am reviewing data from five sites and will finalize the plan` |
| 8 | strict | 41 | 13 | — | -22 | 5.25 | 1 | `the situation is being assessed at five sites emergency response is being coordinated` |
| 9 | strict | 41 | 13 | — | -22 | 5.75 | 1 | `the flood warning is active at five sites response is being coordinated now` |
| 10 | strict | 38 | 12 | — | -22 | 5.75 | 1 | `the flood warning applies to five areas response teams are on standby` |

---

## Summary

- TX messages:       10
- RX messages:       10
- Avg compression:   1.914:1
