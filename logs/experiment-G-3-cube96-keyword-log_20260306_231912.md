# CyberMesh v7.0 "Smart Router" — Experiment G-3

**Run:**         `cube96-keyword`  
**Role:**        B  
**Peer:**        !07c01855  
**Engine:**      mux_grid  
**Codebook:**    cube96  
**Mode:**        keyword  
**Timestamp:**   20260306_231912  

---

## TX Messages

| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | extract_ms | classify_ms | pkts | text | wire_hex |
|---|-------|-------|-------|-------|----------|-----|----|-----------|-------------|------|------|----------|
| 1 | strict | 77 | 44 | 1.75 | 100.0 | — | — | — | 1.9 | 1 | `The area has a flood warning in effect. Check the sensors and prepare response.` | `0e0059170d4a312e3150070a37211826464b19355829071c551620365c59170d222d3b02011145060d493453` |
| 2 | strict | 147 | 71 | 2.0704 | 100.0 | — | — | — | 0.37 | 1 | `Check the sensor status and gather current data. Identify affected zones. Assess water levels and possible risks. Ready for emergency action if needed.` | `170020365c59170d0a1336073c16020111291a0b3750563a0e500f180b1956352c273b1459000f41081d503202011104173d37042e524d0d10022b5955265d332c335f08000e42` |
| 3 | strict | 93 | 50 | 1.86 | 87.5 | 2 | — | — | 0.57 | 1 | `Sensors are operational. Flood levels are high in zones 3 and 5. Take necessary precautions now.` | `1000222d3b5a18371524371826461d50325a18370e37095829072c273bce0740020111af2d1811305c202a2b0d1e1b2d5e59` |
| 4 | strict | 46 | 29 | 1.5862 | 77.7778 | 2 | — | — | 1.19 | 1 | `All systems operational. Focus on zones 3 and 5.` | `09005e352f333834152437051f4a58131e2c273bce0740020111af2d18` |
| 5 | strict | 94 | 56 | 1.6786 | 88.8889 | 2 | — | — | 0.54 | 1 | `I'm monitoring the sensors. Flood levels are high in zones 3 and 5. Take precautions right away.` | `12001e1d1b4b0d5514423259170d222d3b1826461d50325a18370e37095829072c273bce0740020111af2d1811305c0d1e1b27042f372c25` |
| 6 | strict | 62 | 41 | 1.5122 | 84.6154 | 2 | — | — | 0.57 | 1 | `Sensors are working and flood levels are high in zones 3 and 5.` | `0d00222d3b5a18371d5a0e0201111826461d50325a18370e37095829072c273bce0740020111af2d18` |
| 7 | strict | 80 | 47 | 1.7021 | 86.6667 | 2 | — | — | 0.36 | 1 | `All systems are working. Zones 3 and 5 show high flood risk. Take immediate action.` | `0f005e352f3338345a18371d5a0e2c273bce0740020111af2d181c03330e37091826462c0e3011305c251c235d332c` |
| 8 | strict | 79 | 50 | 1.58 | 87.5 | 2 | — | — | 0.48 | 1 | `Sensors are active. Flood levels are high in zones 3 and 5. Acting now is crucial.` | `1000222d3b5a18373627361826461d50325a18370e37095829072c273bce0740020111af2d182a104c2d5e593a513d261d15` |
| 9 | strict | 104 | 59 | 1.7627 | 89.4737 | 2 | — | — | 0.34 | 1 | `I confirmed the sensors are operational. Flood risk is high in zones 3 and 5. Immediate action is required.` | `13001e1d1b35393159170d222d3b5a18371524371826462c0e303a513d0e37095829072c273bce0740020111af2d18251c235d332c3a513d104303` |
| 10 | strict | 63 | 41 | 1.5366 | 84.6154 | 2 | — | — | 0.58 | 1 | `All sensors are operational. Flood risk is high in zones 3 and 5.` | `0d005e352f222d3b5a18371524371826462c0e303a513d0e37095829072c273bce0740020111af2d18` |

## RX Messages

| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |
|---|-------|-------|----|----------|------|-----|------|--------------|
| 1 | strict | 40 | 12 | — | -30 | 6.0 | 1 | `check sensor status and assess conditions now we need to respond quickly` |
| 2 | strict | 71 | 19 | — | -30 | 5.5 | 1 | `sensors are online and data is available flood levels are high in zones 3 and 5 immediate action required` |
| 3 | strict | 52 | 16 | — | -29 | 6.25 | 1 | `sensors are working flood levels are high in zones 3 and 5 take precautions right away` |
| 4 | strict | 43 | 13 | — | -29 | 6.5 | 1 | `confirming sensors are working flood risk is high in zones 3 and 5` |
| 5 | strict | 40 | 12 | — | -32 | 6.5 | 1 | `sensors are working flood risk is high in zones 3 and 5` |
| 6 | strict | 40 | 12 | — | -32 | 6.75 | 1 | `sensors are active flood levels are high in zones 3 and 5` |
| 7 | strict | 40 | 12 | — | -32 | 6.25 | 1 | `sensors are active flood levels are high in zones 3 and 5` |
| 8 | strict | 52 | 16 | — | -34 | 7.25 | 1 | `sensors are operational flood risk is high in zones three and five we must act fast` |
| 9 | strict | 46 | 14 | — | -35 | 7.75 | 1 | `sensors are working flood levels are high in zones 3 and 5 act immediately` |
| 10 | strict | 49 | 15 | — | -36 | 5.75 | 1 | `sensors are running flood levels are high in zones three and five take action now` |

---

## Summary

- TX messages:       10
- RX messages:       10
- Avg compression:   1.704:1
