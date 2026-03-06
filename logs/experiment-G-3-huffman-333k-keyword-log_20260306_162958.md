# CyberMesh v7.0 "Smart Router" — Experiment G-3

**Run:**         `huffman-333k-keyword`  
**Role:**        A  
**Peer:**        !07c01855  
**Engine:**      huffman  
**Codebook:**    333k  
**Mode:**        keyword  
**Timestamp:**   20260306_162958  

---

## TX Messages

| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | extract_ms | classify_ms | pkts | text | wire_hex |
|---|-------|-------|-------|-------|----------|-----|----|-----------|-------------|------|------|----------|
| 1 | strict | 87 | 32 | 2.7188 | 100.0 | — | — | — | 0.24 | 1 | `The flood warning is active. Sensors show 3 rain units. We will check response areas soon.` | `d0c018fee94bec9a5fcaa583bbe8018cca339b18c0943afae504534c2283e800` |
| 2 | strict | 97 | 33 | 2.9394 | 100.0 | — | — | — | 0.35 | 1 | `The flood warning remains active. We have 3 rain units recorded and will assess the situation soon.` | `d0c018fee09457d9631e360eefa0063328ce61125fb02f8c16987a29a61141f400` |
| 3 | strict | 98 | 33 | 2.9697 | 100.0 | — | — | — | 0.36 | 1 | `The flood warning is still active. We have 3 rain units recorded and will assess the situation soon.` | `d0c018fee94ead5f658c78d83bbe8018cca33984497ec0be305a61e8a6984507d0` |
| 4 | strict | 85 | 31 | 2.7419 | 100.0 | — | — | — | 0.18 | 1 | `The flood warning is still active with 3 rain units. We will assess the situation soon.` | `d0c018fee94ead5f65eac1ddf400c66519cd8c605f182d30f4534c2283e800` |
| 5 | strict | 89 | 32 | 2.7812 | 100.0 | — | — | — | 0.33 | 1 | `The flood warning is still active. We have 3 rain units and will assess the situation soon.` | `d0c018fee94ead5f658c78d83bbe8018cca339bf605f182d30f4534c2283e800` |
| 6 | strict | 68 | 22 | 3.0909 | 100.0 | — | — | — | 0.2 | 1 | `The flood warning remains active. We have three rain units to monitor.` | `d0c018fee09457d9631e317d0cca339b9641c1141f40` |
| 7 | strict | 78 | 24 | 3.25 | 100.0 | — | — | — | 0.26 | 1 | `The flood warning remains active with three rain units. We will monitor closely.` | `d0c018fee09457d97a8be866519cd8c605907123a04507d0` |
| 8 | strict | 84 | 26 | 3.2308 | 100.0 | — | — | — | 0.56 | 1 | `The flood warning stays active with three rain units. We will keep monitoring closely.` | `d0c018feecc0dafb2f517d0cca339b18c0924d79a123a04507d0` |
| 9 | strict | 69 | 23 | 3.0 | 100.0 | — | — | — | 0.25 | 1 | `The flood warning is still active. We have three rain units to monitor.` | `d0c018fee94ead5f658c78c5f43328ce6e590704507d00` |
| 10 | strict | 86 | 27 | 3.1852 | 100.0 | — | — | — | 0.41 | 1 | `The flood warning is still active with three rain units. We should monitor it regularly.` | `d0c018fee94ead5f65ea2fa1994673631ef590732459c82283e800` |

## RX Messages

| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |
|---|-------|-------|----|----------|------|-----|------|--------------|
| 1 | strict | 34 | 17 | — | -18 | 5.75 | 1 | `the flood warning is active sensors show 3 units of rain plan to check response areas soon` |
| 2 | strict | 34 | 17 | — | -19 | 6.0 | 1 | `the flood warning is active we have 3 rain units recorded and will check response areas soon` |
| 3 | strict | 31 | 14 | — | -21 | 6.25 | 1 | `the flood warning stays active with 3 rain units well assess the situation soon` |
| 4 | strict | 33 | 16 | — | -19 | 5.75 | 1 | `the flood warning is still active with 3 rain units we will assess the situation soon` |
| 5 | strict | 35 | 18 | — | -19 | 6.25 | 1 | `the flood warning is still active and we have 3 rain units we will assess the situation soon` |
| 6 | strict | 29 | 15 | — | -19 | 6.0 | 1 | `the flood warning remains active with three rain units we will assess the situation soon` |
| 7 | strict | 28 | 14 | — | -19 | 5.75 | 1 | `the flood warning stays active with three rain units we will monitor it closely` |
| 8 | strict | 30 | 16 | — | -19 | 6.25 | 1 | `the flood warning stays active with three rain units we will keep an eye on it` |
| 9 | strict | 28 | 14 | — | -19 | 6.75 | 1 | `the flood warning stays active with three rain units we will keep monitoring it` |
| 10 | strict | 29 | 15 | — | -19 | 5.75 | 1 | `the flood warning is still active with three rain units we should monitor it regularly` |

---

## Summary

- TX messages:       10
- RX messages:       10
- Avg compression:   2.991:1
