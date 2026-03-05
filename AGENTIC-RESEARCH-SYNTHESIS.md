---
title: "Agentic Behavior Research Synthesis"
version: "1.1"
date: "2026-03-05"
context: "Experiment E Phase 2 — fixing 3 prompt issues on LFM2.5-1.2B kernel via Lemonade"
status: ACTIONABLE
---

# Agentic Behavior Research Synthesis

## Purpose

Cross-reference external research against the 3 Experiment E Phase 2 issues,
produce concrete fixes that work with **small obedient LLM kernels** (LFM2.5-1.2B)
running on **Lemonade Server** via OpenAI-compatible API.

---

## The 3 Issues (from live test analysis)

| # | Issue | Example | Root Cause |
|---|-------|---------|------------|
| 1 | **Meta-loop collapse** | "Would you like me to rewrite this more concisely?" | RLHF-trained helpfulness pattern; kernel treats every turn as open-ended dialogue |
| 2 | **Encode hallucination** | "Translated to Spanish:", "Explanation:" | Kernel adds pedagogical framing — defaults to "teacher mode" instead of raw output |
| 3 | **Decode noise** | "(Word count: 34)", "(Note:...)" | Kernel appends meta-commentary; no output boundary enforcement |

---

## Research Sources & Key Findings

### 1. Liquid AI Official Guidance

**Prompting Guide** (docs.liquid.ai):
- LFM2.5-1.2B-Instruct recommended params: `temperature=0.1`, `top_k=50`, `repetition_penalty=1.05`
- Use `system` role for personality, task context, output format, constraints
- **Prefill technique**: Set `assistant` role with partial response to force kernel output structure
  ```json
  {"role": "assistant", "content": "{"  }
  ```
- Few-shot prompting: provide example input→output pairs to lock pattern
- For structured generation with schema validation: use Outlines library

**LFM2.5-1.2B-Thinking blog** (liquid.ai):
- Doom loops reduced from **15.74% → 0.36%** via n-gram repetition penalty during RLVR
- Preference alignment: reject any looping candidate regardless of score
- Curriculum RL with domain-specific checkpoints avoids capability interference
- Instruct variant (what we use) recommended for chat; Thinking variant for tool use/math

### 2. claude-code-best-practice Patterns (github.com/shanraisshan)

| Pattern | Application to CyberMesh |
|---------|-------------------------|
| **Commands** (entry-point prompts) | Encode/decode prompts become fixed commands, not free-form |
| **Sub-Agents** (scoped tools/permissions) | Separate encode kernel vs decode kernel vs router — each with minimal prompt |
| **Skills** (reusable knowledge, on-demand) | Codebook lookup as a skill, not embedded in every prompt |
| **CLAUDE.md < 200 lines** | System prompt must be short — LFM2.5-1.2B has <4K context budget |
| **Hooks** (deterministic scripts outside kernel loop) | Post-processing strip of noise/meta-commentary = hook, not LLM kernel task |
| **Progressive disclosure** | Don't front-load entire codebook; reveal only relevant entries per message |

### 3. AMD Tiny Agents / Lemonade MCP (amd.com)

- Lemonade 7.0.2+ supports MCP tool calling with streaming
- Tiny Agents pattern: LLM loops between conversation and tool use autonomously
- Hybrid NPU+iGPU models available (Llama-xLAM-2-8b-fc-r-Hybrid) — fine-tuned for tool-calling
- Key insight: **tool-calling models are trained to STOP after producing structured output** — this directly helps Issue #1 (meta-loop)

### 4. Constrained Decoding Research

- Grammar-guided generation can force vocabulary compliance at token level
- **Requires logit access** — not available via OpenAI-compatible API (Lemonade)
- **Workaround**: Outlines library works with local models; or use response_format JSON mode if Lemonade supports it
- Simpler alternative: **post-processing regex strip** (codec harness hook) is deterministic and reliable

### 5. Persona Drift & Mode Collapse Research

- Smaller models actually drift **LESS** than larger ones (ArXiv 2024 study)
- Explicit "never break character" + memory anchoring helps
- Multi-kernel self-chat stabilizes persona
- Mode collapse from RLHF creates "apologize → improve → retry" loops — exactly Issue #1
- Fix: hard stop commands in system prompt ("never ask follow-up questions")

### 6. Small Model Best Practices (HatchWorks, ThirdEyeData)

- Fixed prompts (not editable by users) ensure consistency
- Specific, unambiguous instructions beat lengthy explanations
- Consistent formatting across prompts
- Test and iterate on prompt→response pairs
- Smaller kernels need **more rigid structure** but reward it with higher consistency

---

## Actionable Fixes — Mapped to Issues

### Issue #1: Meta-Loop Collapse

**Root cause**: RLHF helpfulness bias → kernel asks "Would you like me to..."

**Fixes (in priority order):**

1. **System prompt hard stop** (zero cost, immediate):
   ```
   RULES:
   - Output ONLY the encoded/decoded text
   - NEVER ask questions
   - NEVER offer alternatives
   - NEVER use phrases like "Would you like" or "I can also"
   - One response per turn. Stop after output.
   ```

2. **Assistant prefill** (Liquid-recommended technique):
   ```json
   {"role": "assistant", "content": "ENCODED: "}
   ```
   Forces kernel to continue from structured prefix, bypassing helpfulness preamble.

3. **max_tokens cap**: Set `max_tokens` to expected output length + small buffer.
   Prevents runaway generation. E.g., if encoded message should be ~50 tokens, set max_tokens=80.

4. **temperature=0.1** (Liquid-recommended): Near-deterministic output reduces creative tangents.

5. **repetition_penalty=1.05** (Liquid-recommended): Prevents the apologize→retry loop.

### Issue #2: Encode Hallucination

**Root cause**: Kernel adds pedagogical framing ("Translated to Spanish:", "Explanation:")

**Fixes (in priority order):**

1. **Few-shot examples** in system prompt (Liquid-recommended):
   ```
   Example:
   INPUT: "Meet at north bridge 0900"
   OUTPUT: dkR7 mN2x bQ4p

   Example:
   INPUT: "All clear sector 7"
   OUTPUT: fT3w hK9v
   ```
   Model learns the exact pattern: input → raw encoded tokens, nothing else.

2. **Negative examples** (from claude-code-best-practice "skills" pattern):
   ```
   WRONG: "Here's the encoded version: dkR7 mN2x"
   WRONG: "Translated to codec: dkR7 mN2x"
   RIGHT: dkR7 mN2x
   ```

3. **Assistant prefill** to skip framing entirely:
   ```json
   {"role": "assistant", "content": ""}
   ```
   Empty prefill + stop sequence after newline forces bare output.

4. **Deterministic post-processing hook** (codec harness, from claude-code-best-practice):
   ```python
   import re
   def strip_encode_noise(raw: str) -> str:
       # Remove common LLM framing patterns
       patterns = [
           r'^(Here\'s?|Translated|Encoded|Output|Result)[^:]*:\s*',
           r'^(The encoded|The translated|The result)[^:]*:\s*',
           r'^["\'`]+|["\'`]+$',  # Strip quotes
       ]
       cleaned = raw.strip()
       for p in patterns:
           cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)
       return cleaned.strip()
   ```

### Issue #3: Decode Noise

**Root cause**: Kernel appends meta-commentary — "(Word count: 34)", "(Note:...)"

**Fixes (in priority order):**

1. **System prompt constraint**:
   ```
   OUTPUT FORMAT:
   - Return ONLY the decoded plain text
   - No parenthetical notes
   - No word counts
   - No explanations
   - No metadata
   - If unsure about a token, use [?] placeholder
   ```

2. **Deterministic post-processing hook**:
   ```python
   import re
   def strip_decode_noise(raw: str) -> str:
       # Remove trailing parenthetical noise
       patterns = [
           r'\(Word count[^)]*\)',
           r'\(Note[^)]*\)',
           r'\(Total[^)]*\)',
           r'\(Approximately[^)]*\)',
           r'\(Original[^)]*\)',
           r'\n\n---.*$',  # Remove trailing separators
           r'\n\nNote:.*$',
       ]
       cleaned = raw.strip()
       for p in patterns:
           cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
       return cleaned.strip()
   ```

3. **max_tokens cap**: Same as Issue #1 — hard ceiling prevents appendages.

---

## Architecture Recommendation: Codec Harness Hooks Over Agents

From claude-code-best-practice, the key insight is the distinction between:
- **Kernel tasks** (need LLM reasoning): deciding WHAT to encode/decode
- **Deterministic tasks** (no LLM needed): stripping noise, validating codebook tokens, formatting output

**Recommendation**: Use the LLM kernel for the hard part (semantic compression/expansion)
and use **deterministic codec harness hooks** for everything else.

```
┌─────────────────────────────────────────────────┐
│                  Message Flow                     │
│                                                   │
│  Input Text                                       │
│      │                                            │
│      ▼                                            │
│  ┌──────────┐   system prompt + few-shot          │
│  │ LLM Call │   + assistant prefill               │
│  │ (encode) │   + temp=0.1, rep_pen=1.05          │
│  └──────────┘   + max_tokens cap                  │
│      │                                            │
│      ▼                                            │
│  ┌──────────────┐  deterministic                  │
│  │ Post-Process │  regex strip + codebook validate │
│  │ (hook)       │  NO LLM NEEDED                  │
│  └──────────────┘                                 │
│      │                                            │
│      ▼                                            │
│  Clean encoded output                             │
└─────────────────────────────────────────────────┘
```

This follows the project principle: **simple wins, push back where possible**.
The LLM kernel does less, the deterministic codec harness does more.

---

## Prompt Template v2 (Proposed)

### Encode Prompt

```
system: |
  You are a codec encoder. Convert plain text to codec tokens.
  
  RULES:
  - Output ONLY codec tokens separated by spaces
  - NEVER add explanations, labels, or commentary
  - NEVER ask questions or offer alternatives
  - One line of output only
  
  CODEBOOK (subset):
  [relevant entries injected per-message]
  
  EXAMPLES:
  INPUT: "Meet at north bridge 0900"
  OUTPUT: dkR7 mN2x bQ4p zW1v
  
  INPUT: "All clear sector 7"
  OUTPUT: fT3w hK9v nL5j

user: "Resupply needed at waypoint delta"

assistant: ""
```

### Decode Prompt

```
system: |
  You are a codec decoder. Convert codec tokens to plain text.
  
  RULES:
  - Output ONLY the decoded plain text
  - No notes, no word counts, no parenthetical comments
  - No explanations of the decoding process
  - One line of output only
  
  CODEBOOK (subset):
  [relevant entries injected per-message]
  
  EXAMPLES:
  INPUT: dkR7 mN2x bQ4p zW1v
  OUTPUT: Meet at north bridge 0900
  
  INPUT: fT3w hK9v nL5j
  OUTPUT: All clear sector 7

user: "aB3c xY9z kM2w"

assistant: ""
```

---

## Sampling Parameters (Liquid-Recommended)

```yaml
# Experiment F target config
model_name: "test01"  # LFM2.5-1.2B aliased
llm_base_url: "http://localhost:8000"
temperature: 0.1        # Near-deterministic (Liquid recommended)
top_k: 50               # Focused token selection (Liquid recommended)
repetition_penalty: 1.05 # Prevent loops (Liquid recommended)
max_tokens: 80           # Hard cap prevents noise appendages
```

---

## What NOT to Build from Scratch

| Capability | Existing Solution | Notes |
|-----------|-------------------|-------|
| Constrained decoding | Outlines library | Grammar-guided generation for local models |
| MCP tool calling | Lemonade 7.0.2+ | Already supports it natively |
| Agent orchestration | Tiny Agents (HuggingFace) | Works with Lemonade out of the box |
| Structured output | Lemonade + response_format | If supported; else post-process |
| Repetition prevention | repetition_penalty param | Built into Liquid inference |
| Doom loop mitigation | Already in LFM2.5 training | 0.36% rate post-RLVR |

---

## Next Steps (Proposed Experiment F)

1. **Implement prompt v2** with system constraints + few-shot + assistant prefill
2. **Add post-processing hooks** for encode/decode noise stripping (deterministic, no LLM)
3. **Set Liquid-recommended sampling params**: temp=0.1, top_k=50, rep_pen=1.05, max_tokens=80
4. **Re-run 40-message test** on both nodes — measure improvement on all 3 issues
5. **If issues persist**: investigate Outlines structured generation or Lemonade response_format support

---

## Sources

- Liquid AI Prompting Guide: https://docs.liquid.ai/docs/key-concepts/text-generation-and-prompting
- LFM2.5-1.2B-Thinking Blog: https://www.liquid.ai/blog/lfm2-5-1-2b-thinking-on-device-reasoning-under-1gb
- LFM2 Announcement: https://www.liquid.ai/blog/liquid-foundation-models-v2-our-second-series-of-generative-ai-models
- claude-code-best-practice: https://github.com/shanraisshan/claude-code-best-practice
- AMD Tiny Agents + Lemonade MCP: https://www.amd.com/en/developer/resources/technical-articles/2025/local-tiny-agents--mcp-agents-on-ryzen-ai-with-lemonade-server.html
- Persona Drift in LLMs: https://www.emergentmind.com/topics/persona-drift
- Constrained Decoding Guide: https://www.aidancooper.co.uk/constrained-decoding/
- Grammar-Constrained Decoding (ACL 2023): https://aclanthology.org/2023.emnlp-main.674.pdf
- Mode Collapse Mitigations (arXiv): https://arxiv.org/html/2510.01171v1
