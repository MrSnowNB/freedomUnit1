# CyberMesh v7.0 "Smart Router" — Experiment G

**Run:**         `mux_grid-333k-strict`  
**Role:**        A  
**Peer:**        !07c01855  
**Engine:**      mux_grid  
**Codebook:**    333k  
**Mode:**        strict_only  
**Timestamp:**   20260306_131630  

---

## TX Messages

| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | extract_ms | classify_ms | pkts | text |
|---|-------|-------|-------|-------|----------|-----|----|-----------|-------------|------|------|
| 1 | strict | 86 | 51 | 1.6863 | 86.6667 | 2 | — | — | — | 1 | `Check the sensors at locations 12 and 27. Assess conditions ` |
| 2 | strict | 107 | 60 | 1.7833 | 88.8889 | 2 | — | — | — | 1 | `I’m checking sensors at locations 12 and 27. Conditions are ` |
| 3 | strict | 108 | 63 | 1.7143 | 89.4737 | 2 | — | — | — | 1 | `I’m checking the sensors at locations 12 and 27. Conditions ` |
| 4 | strict | 110 | 63 | 1.746 | 89.4737 | 2 | — | — | — | 1 | `I’m assessing the sensors at locations 12 and 27. Conditions` |
| 5 | strict | 112 | 66 | 1.697 | 90.0 | 2 | — | — | — | 1 | `I’m assessing the sensors at locations 12 and 27. Conditions` |
| 6 | strict | 113 | 69 | 1.6377 | 90.4762 | 2 | — | — | — | 1 | `I’m assessing the sensors at locations 12 and 27. Conditions` |
| 7 | strict | 76 | 48 | 1.5833 | 85.7143 | 2 | — | — | — | 1 | `I’ve checked sensors 12 and 27. Conditions are critical. Tea` |
| 8 | strict | 80 | 48 | 1.6667 | 85.7143 | 2 | — | — | — | 1 | `I’ve checked sensors 12 and 27. Conditions are critical. Tea` |
| 9 | strict | 74 | 48 | 1.5417 | 85.7143 | 2 | — | — | — | 1 | `I’ve checked sensors 12 and 27. They’re at high risk. Respon` |
| 10 | strict | 74 | 48 | 1.5417 | 85.7143 | 2 | — | — | — | 1 | `I’ve checked sensors 12 and 27. They show high risk. Respons` |

## RX Messages

| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |
|---|-------|-------|----|----------|------|-----|------|--------------|
| 1 | strict | 53 | — | — | -31 | 6.5 | 1 | `the flood warning is active sensors show high risk levels we need to check the s` |
| 2 | strict | 56 | — | — | -29 | 6.0 | 1 | `sensors at locations 12 and 27 show high risk conditions are unstable prepare re` |
| 3 | strict | 53 | — | — | -31 | 6.5 | 1 | `the situation at sensors 12 and 27 is unstable prepare the response team right a` |
| 4 | strict | 53 | — | — | -31 | 6.0 | 1 | `the sensors at 12 and 27 are unstable i am preparing the response team now` |
| 5 | strict | 59 | — | — | -31 | 6.75 | 1 | `the sensors at 12 and 27 are showing high risk i am ready to deploy the team` |
| 6 | strict | 50 | — | — | -31 | 6.0 | 1 | `the flood risk is high at sensors 12 and 27 deploy the team immediately` |
| 7 | strict | 56 | — | — | -30 | 6.0 | 1 | `the situation at sensors 12 and 27 is critical teams are being prepared to act f` |
| 8 | strict | 41 | — | — | -28 | 7.75 | 1 | `sensors 12 and 27 are critical teams are ready to respond` |
| 9 | strict | 62 | — | — | -30 | 6.25 | 1 | `the flood warning remains active sensors 12 and 27 are at high risk response tea` |
| 10 | strict | 62 | — | — | -28 | 6.5 | 1 | `the flood warning is still active sensors 12 and 27 are showing high risk respon` |

---

## Summary

- TX messages:       10
- RX messages:       10
- Avg compression:   1.660:1
