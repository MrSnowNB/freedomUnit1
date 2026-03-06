# CyberMesh v7.0 "Smart Router" — Experiment G

**Run:**         `huffman-333k-keyword`  
**Role:**        A  
**Peer:**        !07c01855  
**Engine:**      huffman  
**Codebook:**    333k  
**Mode:**        keyword  
**Timestamp:**   20260306_131236  

---

## TX Messages

| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | extract_ms | classify_ms | pkts | text |
|---|-------|-------|-------|-------|----------|-----|----|-----------|-------------|------|------|
| 1 | strict | 91 | 27 | 3.3704 | 100.0 | — | — | — | 0.25 | 1 | `Check the river and road sensors. Report any issues. Assess ` |
| 2 | strict | 108 | 36 | 3.0 | 100.0 | — | — | — | 0.26 | 1 | `I checked the sensors near the river and roads. Water levels` |
| 3 | strict | 95 | 31 | 3.0645 | 100.0 | — | — | — | 0.27 | 1 | `The sensors are working. Water levels are high, increasing b` |
| 4 | strict | 138 | 45 | 3.0667 | 100.0 | — | — | — | 0.15 | 1 | `The flood warning is active. Sensors near the river and road` |
| 5 | strict | 97 | 34 | 2.8529 | 100.0 | — | — | — | 0.26 | 1 | `The flood warning remains active. Water levels are high, up ` |
| 6 | strict | 80 | 29 | 2.7586 | 100.0 | — | — | — | 0.38 | 1 | `The flood warning is still active with water up 15 feet. We ` |
| 7 | strict | 139 | 45 | 3.0889 | 100.0 | — | — | — | 0.18 | 1 | `I’ve checked the sensors near the river and roads. Water lev` |
| 8 | strict | 75 | 29 | 2.5862 | 100.0 | — | — | — | 0.27 | 1 | `The flood is worsening, water is 15 feet high. We must act q` |
| 9 | strict | 71 | 29 | 2.4483 | 100.0 | — | — | — | 0.41 | 1 | `The flood is severe with water at 15 feet. We need to act no` |
| 10 | strict | 65 | 26 | 2.5 | 100.0 | — | — | — | 0.22 | 1 | `I see the water is high at 15 feet. We need to prepare immed` |

## RX Messages

| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |
|---|-------|-------|----|----------|------|-----|------|--------------|
| 1 | strict | 38 | — | — | -24 | 6.0 | 1 | `the flood warning is active check sensors near river and roads assess water leve` |
| 2 | strict | 40 | — | — | -25 | 6.25 | 1 | `sensors near the river and roads are operational water levels are high with a ri` |
| 3 | strict | 31 | — | — | -24 | 6.0 | 1 | `sensors are working water is rising fast up 15 feet prepare response right away` |
| 4 | strict | 31 | — | — | -23 | 6.25 | 1 | `the flood is growing quickly water has risen 15 feet act fast to prepare` |
| 5 | strict | 29 | — | — | -24 | 5.75 | 1 | `the flood is rising fast with water up 15 feet we need quick action` |
| 6 | strict | 30 | — | — | -30 | 6.25 | 1 | `the flood is worsening water is up 15 feet and rising fast act immediately` |
| 7 | strict | 31 | — | — | -33 | 5.75 | 1 | `the flood is increasing rapidly with water at 15 feet we must act right away` |
| 8 | strict | 29 | — | — | -32 | 6.25 | 1 | `the flood is getting worse with water at 15 feet act fast to prepare` |
| 9 | strict | 27 | — | — | -32 | 7.0 | 1 | `the flood is severe with water at 15 feet act now to prepare` |
| 10 | strict | 27 | — | — | -32 | 6.75 | 1 | `the flood is severe with water at 15 feet act now to prepare` |

---

## Summary

- TX messages:       10
- RX messages:       10
- Avg compression:   2.874:1
