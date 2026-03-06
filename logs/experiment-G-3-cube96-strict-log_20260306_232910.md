# CyberMesh v7.0 "Smart Router" — Experiment G-3

**Run:**         `cube96-strict`  
**Role:**        A  
**Peer:**        !07c01855  
**Engine:**      mux_grid  
**Codebook:**    cube96  
**Mode:**        strict_only  
**Timestamp:**   20260306_232910  

---

## TX Messages

| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | extract_ms | classify_ms | pkts | text | wire_hex |
|---|-------|-------|-------|-------|----------|-----|----|-----------|-------------|------|------|----------|
| 1 | strict | 119 | 75 | 1.5867 | 90.4762 | 2 | — | — | — | 1 | `The area is experiencing a flood warning. Sensors show critical levels at 3 and 7 sites. We should prepare response teams.` | `15020133ce0740013799020b59170d4a312e3a513d00373c0a37211826464b1935222d3b1c03335f5a101d5032511659ce074002011199020b1b30521c1c21380b1f45060d4934533a1f36` |
| 2 | strict | 77 | 47 | 1.6383 | 86.6667 | 2 | — | — | — | 1 | `Sure, check the sensors at sites 3 and 7 right away and prepare response teams.` | `0f00000a3c20365c59170d222d3b5116591b3052ce074002011199020b27042f372c2502011145060d4934533a1f36` |
| 3 | strict | 105 | 56 | 1.875 | 88.8889 | 2 | — | — | — | 1 | `Confirming sensor status at sites 3 and 7. The flood impact is severe. Ready the response teams immediately.` | `12002f27100a1336073c165116591b3052ce074002011199020b59170d1826460f01343a513d3b561d524d0d59170d4934533a1f36191820` |
| 4 | strict | 90 | 56 | 1.6071 | 88.8889 | 2 | — | — | — | 1 | `The sensors at sites 3 and 7 are critical. Flood impact is severe; teams should be ready now.` | `120059170d222d3b5116591b3052ce074002011199020b5a18375f5a101826460f01343a513d3b561d3a1f36380b1f46593c524d0d2d5e59` |
| 5 | strict | 64 | 35 | 1.8286 | 100.0 | — | — | — | — | 1 | `Confirmed the sensors are critical and teams should be ready now.` | `0b0035393159170d222d3b5a18375f5a100201113a1f36380b1f46593c524d0d2d5e59` |
| 6 | strict | 83 | 47 | 1.766 | 86.6667 | 2 | — | — | — | 1 | `Confirmed the sensors at sites 3 and 7 are critical. Teams must be ready immediately.` | `0f0035393159170d222d3b5116591b3052ce074002011199020b5a18375f5a103a1f3641375046593c524d0d191820` |
| 7 | strict | 68 | 41 | 1.6585 | 84.6154 | 2 | — | — | — | 1 | `Check the sensors at sites 3 and 7. Prepare response teams right away.` | `0d0020365c59170d222d3b5116591b3052ce074002011199020b45060d4934533a1f3627042f372c25` |
| 8 | strict | 68 | 41 | 1.6585 | 84.6154 | 2 | — | — | — | 1 | `Confirmed critical status at sites 3 and 7. Teams should be ready now.` | `0d003539315f5a10073c165116591b3052ce074002011199020b3a1f36380b1f46593c524d0d2d5e59` |
| 9 | strict | 75 | 41 | 1.8293 | 84.6154 | 2 | — | — | — | 1 | `Confirmed critical conditions at sites 3 and 7. Teams should be prepared now.` | `0d003539315f5a10562a175116591b3052ce074002011199020b3a1f36380b1f46593c5034522d5e59` |
| 10 | strict | 65 | 44 | 1.4773 | 85.7143 | 2 | — | — | — | 1 | `Check the sensors at sites 3 and 7 right away. Teams must be ready.` | `0e0020365c59170d222d3b5116591b3052ce074002011199020b27042f372c253a1f3641375046593c524d0d` |

## RX Messages

| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |
|---|-------|-------|----|----------|------|-----|------|--------------|
| 1 | — | — | — | — | — | — | — | `None` |
| 2 | strict | 43 | 13 | — | -27 | 6.5 | 1 | `check the sensors at sites 3 and 7 coordinate with the team immediately` |
| 3 | strict | 40 | 12 | — | -27 | 6.25 | 1 | `verify sensors at sites 3 and 7 assess the flood impact now` |
| 4 | strict | 52 | 16 | — | -27 | 6.0 | 1 | `site 3 and 7 sensors are critical flood impact is severe teams should be ready now` |
| 5 | strict | 58 | 18 | — | -26 | 7.0 | 1 | `i confirm the sensors at sites 3 and 7 are critical response teams need to be ready immediately` |
| 6 | strict | 40 | 12 | — | -26 | 6.75 | 1 | `sensors at sites 3 and 7 are critical teams must be ready` |
| 7 | strict | 40 | 12 | — | -26 | 6.25 | 1 | `check sensors at sites 3 and 7 prepare response teams right away` |
| 8 | strict | 46 | 14 | — | -27 | 5.75 | 1 | `sensors at sites 3 and 7 are critical teams need to be ready now` |
| 9 | strict | 49 | 15 | — | -28 | 5.75 | 1 | `the sensors at sites 3 and 7 are critical teams need to be ready now` |
| 10 | strict | 43 | 13 | — | -28 | 5.75 | 1 | `check the sensors at sites 3 and 7 immediately teams must be ready` |

---

## Summary

- TX messages:       10
- RX messages:       10
- Avg compression:   1.693:1
