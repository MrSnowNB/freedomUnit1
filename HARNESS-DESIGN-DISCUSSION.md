---
title: "CyberMesh Codec Harness — Research & Design Discussion"
version: "1.1"
date: "2026-03-05"
status: BUILD-READY — decisions locked, architect approved 2026-03-05
context: "Experiment F codec harness design, informed by claude-code-best-practice, GAIA lessons, OpenClaw patterns"
gates: "Plan → Build → Validate → Review → Release"
lifecycle_phase: "Plan"
---

# CyberMesh Codec Harness — Research & Design Discussion

## 1. What We Mean by "Codec Harness"

The codec harness is the deterministic Python scaffolding that wraps the
LLM kernel. Per the architect document, the LLM is a kernel (hot-swappable
compute unit), not an agent. The harness refers to the lightweight
orchestration layer that:

- Assembles context (system prompt, codebook, few-shot examples)
- Calls the LLM kernel (Lemonade Server OpenAI-compatible API)
- Captures raw output
- Runs deterministic post-processing (noise strip, codebook validation)
- Logs every step (input, raw output, processed output, timing, errors)
- Provides a test runner for repeatable evaluation

It is NOT a full agent framework (no MCP, no tool calling, no chat loop).
It is a **single-purpose codec harness** for encode/decode on LFM2.5-1.2B.
The LLM does not make decisions, select tools, or loop autonomously — the
harness decides everything.

---

## 2. Sources Cross-Referenced

### 2a. claude-code-best-practice (github.com/shanraisshan)

**Patterns we adopt:**

| Pattern | How It Applies |
|---------|---------------|
| **Commands** — fixed entry-point prompts | Encode prompt and decode prompt are fixed commands, not free-form |
| **Skills** — reusable knowledge, on-demand | Codebook subset injection = a "skill" loaded per message |
| **Hooks** — deterministic scripts outside the kernel loop | Post-processing strip runs OUTSIDE the LLM kernel, not inside it |
| **CLAUDE.md < 200 lines** | System prompt must be short — LFM2.5-1.2B has <4K context budget |
| **Progressive disclosure** | Don't dump entire codebook; inject only relevant entries |
| **Sub-agents with scoped permissions** | Encode agent ≠ decode agent — separate system prompts, separate concerns |

**Patterns we skip (and why):**

| Pattern | Why We Skip |
|---------|------------|
| MCP servers | No tool-calling needed — encode/decode is prompt→response |
| Checkpointing (git-based) | Overkill for stateless encode/decode calls |
| Status line / CLI startup flags | Not building a CLI, just a test harness |
| Plugins / marketplaces | Single-purpose, not distributable |

**Key insight from claude-code-best-practice**: The distinction between
**agentic tasks** (need LLM reasoning) and **deterministic tasks** (no LLM
needed) is the most important architectural decision. Our 3 Experiment E
issues are all cases where we let the LLM handle things a regex can do better.

### 2b. GAIA Lessons Learned

**What went wrong on the ZBook (from the logs):**

1. **Gemini CLI node-pty broken** — `@lydell/node-pty-win32-x64/conpty.node`
   missing binary. Shell execution completely non-functional. Every `Shell`
   command failed. Agent spent 30+ tool calls wandering filesystem.

2. **Wrong model target** — Gemini CLI wrote `.env` with
   `GAIA_MODEL=Qwen3-Coder-30B-A3B-Instruct-GGUF`. We run LFM2.5-1.2B.
   The agent had no awareness of our actual setup.

3. **Wrong Python version** — GAIA SDK requires Python 3.12 + `uv`.
   ZBook has Python 3.10. Would require a full environment rebuild.

4. **Wrong package manager** — GAIA uses `uv` (Astral), not `pip`.
   The Gemini agent wrote `pip install amd-gaia` which may or may not work.

5. **Fabricated API surface** — Gemini wrote `from gaia.agents.base.agent
   import Agent` and `agent.chat(...)` — this import path likely doesn't
   exist in the actual GAIA SDK. The agent was hallucinating the API.

6. **GAIA Agents Hub not shipped** — The `agent.yaml` + `gaia agent publish`
   SDK targets Q2 2026. Current v0.10.1 has 4 basic demo agents.
   Not production-ready for custom agent development.

**What we learn from GAIA's architecture (worth keeping):**

- Lemonade Server as backend (we already use this)
- OpenAI-compatible REST API at localhost:8000 (we already use this)
- Kernel-specific system prompts (we adopt this pattern)
- GAIA Eval-Judge framework concept (synthetic test data + LLM judge) — good
  pattern for our test protocols, but we implement it simpler
- LFM2.5-1.2B runs well on Strix Halo hardware (confirmed by AMD/Liquid collab)

### 2c. OpenClaw Patterns

OpenClaw is the most relevant cross-reference because it separates concerns
the way we need to.

**Patterns we adopt:**

| OpenClaw Pattern | How It Applies to Our Harness |
|-----------------|-------------------------------|
| **SOUL.md** — kernel behavioral philosophy | Our system prompt defines the codec kernel's "soul": encode only, never explain, never ask questions |
| **4-file separation** (SOUL.md, IDENTITY.md, TOOLS.md, USER.md) | We separate: system prompt (soul), codebook config (tools), test message context (user), post-process rules (output format) |
| **SKILL.md** — YAML frontmatter + markdown instructions | Our encode/decode prompts follow this format: metadata header + structured instructions |
| **Hooks** — deterministic scripts outside the kernel loop | Post-processing regex strip = an OpenClaw-style hook |
| **disable-model-invocation** — skills that only run when called directly | Our codec harness only fires encode/decode on explicit test calls, never autonomous |
| **Approval mode** — "suggest and confirm" before autonomous action | Test harness always logs before acting; human reviews results |
| **Skill scope: narrow and specific** | "Generate a weekly report from these logs" = good. "Manage my operations" = disaster. Our skill: "encode this text to codec tokens" — nothing else. |
| **Read-only first, then add writes later** | Phase 1: test harness is read-only (log results). Phase 2: wire into live mesh. |
| **Policy-as-constraints** (Cedar + OpenClaw pattern) | System prompt constraints are policy. Post-process validation is enforcement. Separate planning (prompt) from enforcement (hook). |

**Patterns we skip (and why):**

| OpenClaw Pattern | Why We Skip |
|-----------------|------------|
| Gateway daemon (always-on process) | We run batch tests, not a persistent service |
| Multi-channel routing (WhatsApp, Slack, Discord) | Single channel: Lemonade API |
| Multi-agent routing | Single agent per call (encode OR decode) |
| Session management / chat history | Stateless encode/decode — no history needed |
| Memory persistence (MEMORY.md) | No memory between calls — each encode/decode is independent |
| ClawHub / skill marketplace | Internal use only |
| Node.js/TypeScript runtime | We use Python — matches existing codebase |

**Key insight from OpenClaw**: The **SOUL.md pattern** — defining who the kernel
IS rather than what it DOES — directly addresses Issue #1 (meta-loop collapse).
When the kernel's identity is "You are a codec encoder. You output tokens. You
never explain, ask questions, or offer alternatives" — the RLHF helpfulness
bias has less room to activate because the kernel's self-concept doesn't include
"helpful assistant."

**Key insight from OpenClaw policy architecture**: The Cedar constraint-aware
planning pattern maps perfectly to our harness. Instead of the LLM discovering
constraints by violating them (producing noise, then us stripping it), we
**inject constraints into the system prompt** so the LLM plans within boundaries.
Then the post-process hook enforces the same boundaries deterministically as
a safety net.

**Two-phase authorization model applied to our harness:**

```
Phase 1 (Planning = System Prompt):
  "You are a codec encoder. Output ONLY codec tokens.
   NEVER add explanations. NEVER ask questions."
  → LLM reasons within these constraints

Phase 2 (Enforcement = Post-Process Hook):
  regex strip framing → validate against codebook → log any violations
  → LLM output is cleaned deterministically regardless of what it generated
```

This is the same pattern as OpenClaw's reactive→constraint-aware evolution,
but applied at the prompt/post-process level instead of the tool/policy level.

---

## 3. Harness Architecture (Discussion)

```
┌─────────────────────────────────────────────────────────────┐
│                    CyberMesh Codec Harness                    │
│                                                               │
│  CONFIG FILES (OpenClaw-style separation):                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ encode.soul  │ │ decode.soul  │ │ codebook.cfg │         │
│  │ (system      │ │ (system      │ │ (subset      │         │
│  │  prompt)     │ │  prompt)     │ │  injection)  │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
│                                                               │
│  TEST RUNNER:                                                 │
│  ┌──────────────────────────────────────────────────┐        │
│  │ 1. Load test messages from test_suite.yaml        │        │
│  │ 2. For each message:                              │        │
│  │    a. Select encode/decode soul                   │        │
│  │    b. Inject codebook subset (progressive)        │        │
│  │    c. Build OpenAI API request                    │        │
│  │       - system: soul + codebook                   │        │
│  │       - user: test message                        │        │
│  │       - assistant prefill (Liquid technique)      │        │
│  │       - params: temp=0.1, top_k=50, rep_pen=1.05 │        │
│  │       - max_tokens: 80                            │        │
│  │    d. Call Lemonade API                           │        │
│  │    e. Log: request, raw response, timing          │        │
│  │    f. Run post-process hooks                      │        │
│  │    g. Log: processed output, violations found     │        │
│  │    h. Run validation (codebook token check)       │        │
│  │    i. Log: validation result                      │        │
│  │ 3. Generate test report                           │        │
│  └──────────────────────────────────────────────────┘        │
│                                                               │
│  POST-PROCESS HOOKS (deterministic, no LLM):                 │
│  ┌──────────────────────────────────────────────────┐        │
│  │ hook_strip_encode_framing()  — Issue #2 fix       │        │
│  │ hook_strip_decode_noise()    — Issue #3 fix       │        │
│  │ hook_validate_codebook()     — token membership    │        │
│  │ hook_detect_meta_loop()      — Issue #1 detection  │        │
│  └──────────────────────────────────────────────────┘        │
│                                                               │
│  LOGGING (every step, every call):                            │
│  ┌──────────────────────────────────────────────────┐        │
│  │ harness.log        — human-readable run log       │        │
│  │ harness_data.jsonl — machine-readable per-call    │        │
│  │ test_report.md     — summary with pass/fail       │        │
│  └──────────────────────────────────────────────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. File Manifest (Proposed)

| File | Purpose | Source Pattern |
|------|---------|---------------|
| `harness.py` | Main test runner + API caller + logging | Custom |
| `encode.soul.md` | Encode system prompt (SOUL.md pattern) | OpenClaw |
| `decode.soul.md` | Decode system prompt (SOUL.md pattern) | OpenClaw |
| `hooks.py` | Post-process regex strips + validation | claude-code hooks |
| `test_suite.yaml` | Test messages + expected behaviors | GAIA Eval-Judge |
| `config.yaml` | API endpoint, model, sampling params | OpenClaw config |
| `test_report.md` | Auto-generated test results | Custom |
| `harness.log` | Full human-readable log | Project standard |
| `harness_data.jsonl` | Machine-readable per-call data | Project standard |
| `TESTING-PROTOCOL.md` | How to run tests, what to check | Project standard |

---

## 5. Testing Protocol (Discussion)

### 5a. What We Test

**Issue #1 — Meta-loop collapse:**
- Detection: scan for phrases like "Would you like", "I can also",
  "Let me", "Here's", "Do you want"
- Metric: meta_loop_count per N messages (target: 0)
- Gate: FAIL if any meta-loop detected in 20-message run

**Issue #2 — Encode hallucination:**
- Detection: scan for framing prefixes ("Translated:", "Encoded:",
  "Here's the encoded", "Output:", "Result:")
- Metric: framing_count per N messages (target: 0)
- Post-hook catch rate: what % of framing was stripped by hook
- Gate: FAIL if raw output contains framing in >10% of messages

**Issue #3 — Decode noise:**
- Detection: scan for trailing noise ("(Word count:", "(Note:",
  "(Total:", "(Approximately:", separators "---")
- Metric: noise_count per N messages (target: 0)
- Post-hook catch rate: what % of noise was stripped by hook
- Gate: FAIL if raw output contains noise in >10% of messages

**Baseline metrics (carry forward from Experiment E):**
- Compression ratio (target: maintain ≥1.79:1 MUX, ≥1.94:1 Huffman)
- Codebook hit rate (target: maintain ≥79.5% MUX, ≥83.5% Huffman)
- ESC tokens per message (target: maintain ≤2.6)
- Fallback rate (target: maintain ≤4/20)
- Response latency (log, compare to Experiment E baselines)

### 5b. Test Suite Structure

```yaml
# test_suite.yaml
metadata:
  version: "1.0"
  experiment: "F"
  description: "Codec harness validation"

test_cases:
  encode:
    - id: ENC-001
      input: "Meet at north bridge 0900"
      expect_no: ["Translated", "Encoded", "Here's", "Would you like"]
      expect_format: "space-separated tokens only"

    - id: ENC-002
      input: "All clear sector 7"
      expect_no: ["Output:", "Result:", "The encoded"]
      expect_format: "space-separated tokens only"

    # ... 20 encode test cases

  decode:
    - id: DEC-001
      input: "dkR7 mN2x bQ4p zW1v"
      expect_no: ["Word count", "Note:", "Total:", "---"]
      expect_format: "plain text only"

    - id: DEC-002
      input: "fT3w hK9v nL5j"
      expect_no: ["(", ")", "Note", "Approximately"]
      expect_format: "plain text only"

    # ... 20 decode test cases

  stress:
    - id: STR-001
      description: "Rapid-fire 10 encodes, check for persona drift"
      messages: [...]
      check: "no meta-loop in any response"
```

### 5c. Test Run Protocol

```
PROTOCOL: Experiment F Codec Harness Validation
HARDWARE: Run on BOTH nodes (Nvidia + Strix Halo)

Step 1: VERIFY PREREQUISITES
  [ ] Lemonade Server running on localhost:8000
  [ ] Model "test01" (LFM2.5-1.2B) loaded and responding
  [ ] Python 3.10+ available
  [ ] harness.py, hooks.py, config.yaml, test_suite.yaml present

Step 2: RUN BASELINE CHECK
  [ ] harness.py --mode sanity-check
  [ ] Confirm API responds, model generates tokens
  [ ] Log: latency, model name, token count

Step 3: RUN ENCODE TESTS
  [ ] harness.py --mode encode --suite test_suite.yaml
  [ ] 20 encode test cases
  [ ] Log: all raw outputs, all processed outputs, all violations

Step 4: RUN DECODE TESTS
  [ ] harness.py --mode decode --suite test_suite.yaml
  [ ] 20 decode test cases
  [ ] Log: all raw outputs, all processed outputs, all violations

Step 5: RUN STRESS TESTS
  [ ] harness.py --mode stress --count 40
  [ ] 40 rapid-fire messages (20 encode + 20 decode)
  [ ] Check for persona drift across sequence

Step 6: GENERATE REPORT
  [ ] harness.py --report
  [ ] Auto-generates test_report.md
  [ ] Compare against Experiment E baselines

Step 7: REVIEW GATES
  [ ] Issue #1 (meta-loop): 0 detections? → PASS/FAIL
  [ ] Issue #2 (encode framing): 0 in raw OR 100% hook catch? → PASS/FAIL
  [ ] Issue #3 (decode noise): 0 in raw OR 100% hook catch? → PASS/FAIL
  [ ] Compression ratio maintained? → PASS/FAIL
  [ ] Codebook hit rate maintained? → PASS/FAIL

Step 8: ON FAILURE
  [ ] Capture logs → update TROUBLESHOOTING.md
  [ ] Update REPLICATION-NOTES.md with failure details
  [ ] Open ISSUE.md with root cause analysis
  [ ] HALT — wait for human input before proceeding
```

---

## 6. Sampling Parameters (Liquid AI Recommended)

From the official Liquid AI prompting guide:

```yaml
# LFM2.5-1.2B-Instruct recommended
temperature: 0.1          # Near-deterministic
top_k: 50                 # Focused token selection
repetition_penalty: 1.05  # Prevent loops (n-gram penalty built into model)
max_tokens: 80            # Hard cap prevents noise appendages
```

Additional Liquid techniques to use:
- **Assistant prefill**: Pre-fill assistant response to force output structure
- **Few-shot examples**: 2-3 input→output pairs in system prompt
- **Negative examples**: Show what NOT to produce

---

## 7. Discussion Points Before Coding

### 7a. Naming

- **"Codec harness"** is the correct term per the architect document. The LLM
  is a kernel, not an agent. The harness is deterministic scaffolding that
  wraps the kernel.
- Alternative terms: "test harness", "prompt harness", "inference harness"
- Recommendation: **"CyberMesh Codec Harness"** — aligns with architect terminology

### 7b. Scope Boundaries

What the codec harness IS:
- A test runner for encode/decode prompts against Lemonade API
- A logging system for every LLM kernel call
- A post-processing pipeline for noise removal
- A validation pipeline for codebook compliance
- A report generator for experiment results

What the codec harness IS NOT:
- Not a chat interface
- Not a persistent service / daemon
- Not a framework for building other codec harnesses
- Not a replacement for GAIA or OpenClaw
- Not wired into the live LoRa mesh (yet — that's Phase 2)

### 7c. Dependency Decisions

| Dependency | Decision | Rationale |
|-----------|----------|-----------|
| Python 3.10 | YES — use what's on both laptops | No new installs |
| requests library | YES — for OpenAI API calls | Already available |
| PyYAML | YES — for config/test suite | Standard library-adjacent |
| GAIA SDK | NO | Not production-ready, wrong Python version |
| OpenClaw | NO | Node.js runtime, massive scope, cloud LLM focus |
| Any new framework | NO | Simple wins. Push back. |

### 7d. What We Borrowed vs What We Built

| Component | Borrowed From | Adapted How |
|-----------|--------------|-------------|
| System prompt as "soul" | OpenClaw SOUL.md | Markdown file defining codec agent identity |
| Deterministic hooks | claude-code-best-practice | Python regex strips instead of shell scripts |
| Narrow skill scope | OpenClaw SKILL.md | Each prompt does ONE thing only |
| Progressive disclosure | claude-code-best-practice | Codebook subset injection, not full dump |
| Policy-as-constraints | OpenClaw + Cedar pattern | Prompt constraints + post-process enforcement |
| Eval-Judge concept | GAIA framework | Simplified: pattern matching, not LLM judge |
| Config separation | OpenClaw 4-file pattern | soul, config, test suite, hooks as separate files |
| Failure handling | Project standard | Logs → TROUBLESHOOTING.md → ISSUE.md → halt |
| Sampling params | Liquid AI prompting guide | Direct adoption: temp=0.1, top_k=50, rep_pen=1.05 |
| Assistant prefill | Liquid AI prompting guide | Force output structure via partial response |

### 7e. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LFM2.5-1.2B ignores system prompt constraints | Medium | High | Few-shot examples + assistant prefill + post-process hooks |
| Post-process hooks strip valid content | Low | Medium | Log both raw and processed; human review on mismatches |
| Codebook subset injection exceeds context window | Low | High | Track token count; keep system prompt < 2K tokens |
| Lemonade API doesn't support all sampling params | Medium | Medium | Test each param individually; fallback to defaults |
| Test suite doesn't cover edge cases | Medium | Low | Start with 20 cases; expand based on live test findings |

---

## 8. Open Questions — RESOLVED

Decisions locked per architect review 2026-03-05.

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Codebook injection | **Subset, not full.** Frequency-ranked static selection, ~200 entries max per call. | Full 4,095-entry Huffman codebook won't fit in <4K context. Codebook is already frequency-ranked, static selection is sufficient. |
| 2 | Assistant prefill | **Test empty string first**, then try first token of expected output. | Don't overthink it until we have baseline data. Iterate based on results. |
| 3 | Test messages | **Reuse Experiment E's 40 messages.** Expand after baseline comparison. | Apples-to-apples comparison required. New messages give broader coverage but no way to attribute improvements to harness vs. message difficulty. |
| 4 | Stress count | **40 per node, 80 total** across both nodes. | Matches Experiment E per-node count for direct comparison. |
| 5 | Live mesh integration | **After all 3 issue gates pass.** Not in parallel. | Sequential lifecycle policy: Plan → Build → Validate → Review → Release. |

### Context Budget (Architect-Specified)

| Section | Token Budget |
|---------|-------------|
| System prompt (soul) | ~300 tokens |
| Few-shot examples (2-3) | ~400 tokens |
| Codebook subset (~200 entries) | ~800 tokens |
| User message | ~200 tokens |
| Generation headroom (max_tokens) | ~80 tokens |
| **Total** | **~1,800 / 4,096** |

This gives ~2,200 tokens of margin. If codebook subset bloats past
800 tokens, we hit the wall. Monitor token counts in every log entry.

### Model Clarification

We are running **LFM2.5-1.2B** (aliased as "test01" on both laptops),
NOT LFM2-2.6B. The AMD/Liquid collaboration blog was referenced as an
architectural pattern (stable system prompt + structured I/O + eval
framework), not as a benchmark target. IFEval scores from LFM2-2.6B
do NOT apply to LFM2.5-1.2B. Benchmark against LFM2.5-1.2B published
capabilities only.

---

## Sources

- claude-code-best-practice: https://github.com/shanraisshan/claude-code-best-practice
- GAIA GitHub: https://github.com/amd/gaia
- GAIA SDK Quickstart: https://amd-gaia.ai/quickstart
- GAIA Agents Hub Roadmap: https://amd-gaia.ai/plans/agent-hub
- AMD + Liquid AI Collaboration: https://www.amd.com/en/blogs/2026/liquid-ai-amd-ryzen-on-device-meeting-summaries.html
- Liquid AI Prompting Guide: https://docs.liquid.ai/docs/key-concepts/text-generation-and-prompting
- LFM2.5-1.2B-Thinking Blog: https://www.liquid.ai/blog/lfm2-5-1-2b-thinking-on-device-reasoning-under-1gb
- OpenClaw GitHub: https://github.com/openclaw/openclaw
- OpenClaw AGENTS.md: https://github.com/openclaw/openclaw/blob/main/AGENTS.md
- OpenClaw Configuration: https://docs.openclaw.ai/gateway/configuration
- OpenClaw Identity Architecture: https://www.mmntm.net/articles/openclaw-identity-architecture
- OpenClaw Custom Skills: https://lumadock.com/tutorials/build-custom-openclaw-skills
- OpenClaw Policy Constraints (Cedar): https://www.windley.com/archives/2026/02/beyond_denial_using_policy_constraints_to_guide_openclaw_planning.shtml
- OpenClaw Creating Skills: https://docs.openclaw.ai/tools/creating-skills
- OpenClaw Threat Model: https://cloudsecurityalliance.org/blog/2026/02/20/openclaw-threat-model-maestro-framework-analysis
- AMD Tiny Agents + Lemonade MCP: https://www.amd.com/en/developer/resources/technical-articles/2025/local-tiny-agents--mcp-agents-on-ryzen-ai-with-lemonade-server.html
- Constrained Decoding Guide: https://www.aidancooper.co.uk/constrained-decoding/
- Persona Drift in LLMs: https://www.emergentmind.com/topics/persona-drift
