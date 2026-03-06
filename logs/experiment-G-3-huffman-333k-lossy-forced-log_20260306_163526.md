# CyberMesh v7.0 "Smart Router" — Experiment G-3

**Run:**         `huffman-333k-lossy-forced`  
**Role:**        A  
**Peer:**        !07c01855  
**Engine:**      huffman  
**Codebook:**    333k  
**Mode:**        keyword  
**Timestamp:**   20260306_163526  

---

## TX Messages

| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | extract_ms | classify_ms | pkts | text | wire_hex |
|---|-------|-------|-------|-------|----------|-----|----|-----------|-------------|------|------|----------|
| 1 | strict | 85 | 29 | 2.931 | 100.0 | — | — | — | 0.22 | 1 | `Sure, I’m checking the sensors. Conditions are critical with 3 active alerts in the area.` | `2c44cc8e956d1a5fd7fa9b6e16f560eefa0077d96cad36d19d04507d00` |
| 2 | strict | 81 | 27 | 3.0 | 100.0 | — | — | — | 0.21 | 1 | `The flood warning is active. There are 3 active alerts and conditions are critical.` | `d0c018fee94becb214db0777d003becb656bf5fea6db8584507d00` |
| 3 | strict | 81 | 27 | 3.0 | 100.0 | — | — | — | 0.25 | 1 | `The flood warning is active. There are 3 active alerts and conditions are critical.` | `d0c018fee94becb214db0777d003becb656bf5fea6db8584507d00` |
| 4 | strict | 65 | 23 | 2.8261 | 100.0 | — | — | — | 1.06 | 1 | `The flood warning is active with 3 alerts. Conditions are critical.` | `d0c018fee94becbd583bbe801ecad5fea6db8584507d00` |
| 5 | strict | 65 | 23 | 2.8261 | 100.0 | — | — | — | 0.29 | 1 | `The flood warning is active with 3 alerts. Conditions are critical.` | `d0c018fee94becbd583bbe801ecad5fea6db8584507d00` |
| 6 | strict | 74 | 25 | 2.96 | 100.0 | — | — | — | 0.59 | 1 | `The flood warning is active. There are 3 alerts and conditions are critical.` | `d0c018fee94becb214db0777d003d95afd7fa9b6e161141f40` |
| 7 | strict | 65 | 23 | 2.8261 | 100.0 | — | — | — | 0.36 | 1 | `The flood warning is active with 3 alerts. Conditions are critical.` | `d0c018fee94becbd583bbe801ecad5fea6db8584507d00` |
| 8 | strict | 69 | 20 | 3.45 | 100.0 | — | — | — | 0.33 | 1 | `The flood warning is active with three alerts. Conditions are critical.` | `d0c018fee94becbd45f5b2b57fa9b6e161141f40` |
| 9 | strict | 69 | 20 | 3.45 | 100.0 | — | — | — | 0.18 | 1 | `The flood warning is active with three alerts. Conditions are critical.` | `d0c018fee94becbd45f5b2b57fa9b6e161141f40` |
| 10 | strict | 69 | 20 | 3.45 | 100.0 | — | — | — | 0.2 | 1 | `The flood warning is active with three alerts. Conditions are critical.` | `d0c018fee94becbd45f5b2b57fa9b6e161141f40` |

## RX Messages

| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |
|---|-------|-------|----|----------|------|-----|------|--------------|
| 1 | strict | 23 | 11 | — | -22 | 5.75 | 1 | `the flood warning is active check sensors now conditions are critical` |
| 2 | strict | 32 | 15 | — | -21 | 5.5 | 1 | `the flood warning is real there are 3 active alerts sensors are reporting critical conditions` |
| 3 | strict | 25 | 11 | — | -21 | 5.75 | 1 | `the flood warning is active with 3 alerts conditions are critical` |
| 4 | strict | 29 | 14 | — | -16 | 7.0 | 1 | `the flood warning is active there are 3 active alerts and conditions are critical` |
| 5 | strict | 25 | 11 | — | -16 | 6.5 | 1 | `the flood warning is active with 3 alerts conditions are critical` |
| 6 | strict | 25 | 11 | — | -17 | 8.0 | 1 | `the flood warning is active with 3 alerts conditions are critical` |
| 7 | strict | 25 | 11 | — | -16 | 7.0 | 1 | `the flood warning is active with 3 alerts conditions are critical` |
| 8 | strict | 22 | 11 | — | -17 | 7.5 | 1 | `the flood warning is active with three alerts conditions are critical` |
| 9 | strict | 24 | 13 | — | -17 | 6.75 | 1 | `the flood warning is active and there are three alerts conditions are critical` |
| 10 | strict | 24 | 12 | — | -17 | 7.0 | 1 | `the flood warning is active and three alerts exist conditions are critical` |

---

## Summary

- TX messages:       10
- RX messages:       10
- Avg compression:   3.072:1
