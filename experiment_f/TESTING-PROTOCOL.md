---
title: "Experiment F — Testing Protocol"
version: "1.0"
date: "2026-03-05"
experiment: "F"
status: "ready"
lifecycle_phase: "Validate"
hardware: "Run on BOTH nodes (Nvidia + Strix Halo)"
---

# Experiment F — Testing Protocol

Step-by-step protocol for running the CyberMesh Codec Harness.
Follow sequentially. Do not skip steps. Log all results.

---

## Prerequisites

| Requirement | How to Verify |
|-------------|---------------|
| Lemonade Server running | `curl http://localhost:8000/api/generate -d '{"model":"test01","prompt":"hello","stream":false}'` returns JSON |
| Model "test01" loaded | Above curl returns a `response` field with text |
| Python 3.10+ | `python --version` shows 3.10+ |
| requests library | `python -c "import requests"` exits clean |
| PyYAML library | `python -c "import yaml"` exits clean |
| experiment_f/ directory | All 6 files present (see File Checklist below) |
| mux_codebook.csv | Present in parent directory (`../mux_codebook.csv` from experiment_f/) |

### File Checklist

```
huffman-mesh-poc/
├── mux_codebook.csv          # 4096 entries (DO NOT MODIFY)
└── experiment_f/
    ├── config.yaml            # API endpoint, model, sampling params
    ├── encode.soul.md         # Encoder system prompt (SOUL.md pattern)
    ├── decode.soul.md         # Decoder system prompt (SOUL.md pattern)
    ├── hooks.py               # 4 deterministic post-process hooks
    ├── test_suite.yaml        # 20 encode + 20 decode + 40 stress messages
    ├── harness.py             # Main test runner
    └── TESTING-PROTOCOL.md    # This file
```

---

## Step 1: Verify Prerequisites

```bash
cd huffman-mesh-poc/experiment_f/
python -c "import requests, yaml; print('deps OK')"
curl http://localhost:8000/api/generate -d '{"model":"test01","prompt":"hello","stream":false}'
```

- [ ] Python deps import clean
- [ ] Curl returns JSON with `response` field
- [ ] Model name in response matches "test01"

---

## Step 2: Sanity Check

```bash
python harness.py --mode sanity-check
```

Expected output:
- `SANITY CHECK PASSED: model responded in XXXms`
- Non-empty response text

- [ ] Sanity check PASSED
- [ ] Response latency logged
- [ ] No connection errors

**On failure**: Check Lemonade Server is running. Check `config.yaml` → `llm_base_url`.
Do NOT proceed until sanity check passes.

---

## Step 3: Run Encode Tests

```bash
python harness.py --mode encode
```

This runs 20 encode test cases from `test_suite.yaml`.
Each test:
1. Sends natural text to LLM with encode soul prompt + codebook subset
2. Captures raw output
3. Runs hooks: strip_encode_framing → validate_codebook → detect_meta_loop
4. Logs everything to `harness.log` + `harness_data.jsonl`

- [ ] 20/20 tests executed
- [ ] Check console for PASS/FAIL per test
- [ ] Note any FAIL tests — raw output will show what went wrong
- [ ] Meta-loop detections: should be 0
- [ ] Encode framing violations: note count (stripped by hook)
- [ ] Codebook hit rates: should be >=70% average

---

## Step 4: Run Decode Tests

```bash
python harness.py --mode decode
```

This runs 20 decode test cases from `test_suite.yaml`.
Each test:
1. Sends codebook-constrained text to LLM with decode soul prompt
2. Captures raw output
3. Runs hooks: strip_decode_noise → detect_meta_loop
4. Logs everything

- [ ] 20/20 tests executed
- [ ] Check console for PASS/FAIL per test
- [ ] Meta-loop detections: should be 0
- [ ] Decode noise violations: note count (stripped by hook)
- [ ] Output should be natural English sentences

---

## Step 5: Run Stress Tests

```bash
python harness.py --mode stress
```

This runs 40 rapid-fire messages (20 encode + 20 decode) to detect
persona drift under sustained load.

- [ ] 40 stress tests executed (20 encode + 20 decode)
- [ ] Check for persona drift across sequence (meta-loop count)
- [ ] No degradation in later messages vs earlier
- [ ] All results logged

---

## Step 6: Run Full Suite (Alternative to Steps 3-5)

```bash
python harness.py --mode full
```

Runs all tests in sequence: encode → decode → stress.
Generates report automatically at the end.

- [ ] All 80 tests executed (20+20+20+20)
- [ ] Report generated at `test_report.md`

---

## Step 7: Review Report

```bash
python harness.py --report
```

Or review the auto-generated `test_report.md` from the full run.

### Issue Gates (MUST ALL PASS)

| Gate | Metric | Target | Action if FAIL |
|------|--------|--------|----------------|
| Issue #1 — Meta-loop | meta_loop detections | 0 across all tests | Harden soul prompts, add negative examples |
| Issue #2 — Encode framing | framing in raw output | <10% of messages | Adjust encode.soul.md, tighten few-shot examples |
| Issue #3 — Decode noise | noise in raw output | <10% of messages | Adjust decode.soul.md, add explicit "no notes" |
| Codebook hit rate | avg encode hit rate | >=70% | Adjust codebook subset size, review prompt |
| Baseline metrics | compression ratio | maintain >=1.79:1 MUX, >=1.94:1 Huffman | Compare with Experiment E |

- [ ] Issue #1 gate: PASS / FAIL
- [ ] Issue #2 gate: PASS / FAIL
- [ ] Issue #3 gate: PASS / FAIL
- [ ] Codebook hit rate gate: PASS / FAIL

---

## Step 8: Compare with Experiment E Baselines

Review `test_report.md` against these Experiment E baselines:

| Metric | Experiment E (MUX) | Experiment E (Huffman) |
|--------|-------------------|----------------------|
| Compression ratio | 1.79:1 | 1.94:1 |
| Codebook hit rate | 79.5% | 83.5% |
| Avg ESC/msg | 2.6 | 2.6 |
| Fallback rate | 3/20 | 4/20 |

- [ ] Hit rate maintained or improved
- [ ] Latency comparable to Experiment E
- [ ] No regression in core metrics

---

## Step 9: On Failure

If ANY gate fails:

1. **Capture logs**
   ```bash
   cp harness.log harness_FAIL_$(date +%Y%m%d_%H%M%S).log
   cp harness_data.jsonl harness_data_FAIL_$(date +%Y%m%d_%H%M%S).jsonl
   ```

2. **Update TROUBLESHOOTING.md** with failure details

3. **Update REPLICATION-NOTES.md** with:
   - Which gate failed
   - Raw output samples showing the failure
   - Hardware/node info

4. **Open ISSUE.md** with:
   - Root cause analysis
   - Proposed fix
   - Affected files

5. **HALT** — wait for human input before proceeding

---

## Step 10: On Success (All Gates Pass)

1. **Copy results to both laptops** if tested on one
2. **Run the same protocol on the second node**
3. **Compare results across nodes** (Nvidia vs Strix Halo)
4. **Update REPLICATION-NOTES.md** with Experiment F results
5. **Proceed to Review phase** of lifecycle

---

## Output Files After Run

| File | Purpose |
|------|---------|
| `harness.log` | Human-readable log of entire run |
| `harness_data.jsonl` | Machine-readable per-call data (one JSON object per line) |
| `test_report.md` | Auto-generated summary with pass/fail, gates, details |

All three files are generated in the `experiment_f/` directory.

---

## Quick Reference

```bash
# One-liner: full run on a clean setup
cd huffman-mesh-poc/experiment_f/ && python harness.py --mode full

# Just check if the server is alive
python harness.py --mode sanity-check

# Re-generate report from existing data
python harness.py --report

# Run only encode tests (fastest feedback loop)
python harness.py --mode encode
```
