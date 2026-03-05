#!/usr/bin/env python3
"""
harness.py — CyberMesh Codec Harness (Experiment F)
====================================================
Lightweight test harness for encode/decode validation against Lemonade Server.

Architecture:
  - SOUL.md prompts define agent identity (OpenClaw pattern)
  - Deterministic hooks run post-processing OUTSIDE the LLM (claude-code pattern)
  - Two-phase: prompt constraints (planning) + regex hooks (enforcement)
  - Comprehensive logging: every step, every call

Dependencies: Python 3.10 + requests + PyYAML ONLY.
No GAIA, no OpenClaw, no new frameworks.

Usage:
  python harness.py --mode sanity-check     # verify API + model
  python harness.py --mode encode            # run 20 encode tests
  python harness.py --mode decode            # run 20 decode tests
  python harness.py --mode stress            # run 40 rapid-fire tests
  python harness.py --mode full              # run all tests
  python harness.py --report                 # generate test_report.md

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import os
import sys
import csv
import json
import time
import re
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
import requests

# Local import — hooks must be in same directory
from hooks import run_hooks

# ─── Constants ────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
VERSION = "1.0.0"

# ─── Logging Setup ────────────────────────────────────────────────────────────


def setup_logging(config: dict) -> logging.Logger:
    """Configure dual logging: console + file."""
    log_level = getattr(logging, config.get("logging", {}).get("log_level", "DEBUG"))
    log_file = SCRIPT_DIR / config.get("logging", {}).get("human_log", "harness.log")

    logger = logging.getLogger("harness")
    logger.setLevel(log_level)
    logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setLevel(log_level)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    logger.addHandler(fh)

    return logger


# ─── Config Loader ────────────────────────────────────────────────────────────


def load_config() -> dict:
    """Load config.yaml from script directory."""
    config_path = SCRIPT_DIR / "config.yaml"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── Codebook Loader ─────────────────────────────────────────────────────────


def load_codebook(config: dict) -> tuple[list[str], set]:
    """
    Load codebook from CSV. Returns (word_list, word_set).

    word_list: frequency-ranked (index 0 = most common)
    word_set: lowercase set for fast membership check
    """
    cb_path = SCRIPT_DIR / config.get("codebook", {}).get("path", "../mux_codebook.csv")
    cb_path = cb_path.resolve()

    if not cb_path.exists():
        raise FileNotFoundError(f"Codebook not found: {cb_path}")

    words = []
    with open(cb_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row["word"]
            if word == "<ESC>":
                continue
            words.append(word.lower())

    return words, set(words)


def build_codebook_subset(words: list[str], subset_size: int = 200) -> str:
    """Build comma-separated codebook subset for prompt injection."""
    subset = words[:subset_size]
    return ", ".join(subset)


# ─── Soul Prompt Loader ──────────────────────────────────────────────────────


def load_soul(config: dict, role: str) -> str:
    """
    Load a soul prompt file, strip YAML frontmatter, return content.

    Args:
        config: Loaded config dict.
        role: 'encode' or 'decode'
    """
    soul_file = config.get("souls", {}).get(role)
    if not soul_file:
        raise ValueError(f"No soul file configured for role: {role}")

    soul_path = SCRIPT_DIR / soul_file
    if not soul_path.exists():
        raise FileNotFoundError(f"Soul file not found: {soul_path}")

    content = soul_path.read_text(encoding="utf-8")

    # Strip YAML frontmatter (--- ... ---)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    return content


# ─── Test Suite Loader ────────────────────────────────────────────────────────


def load_test_suite(config: dict) -> dict:
    """Load test_suite.yaml."""
    suite_file = config.get("test", {}).get("suite_file", "test_suite.yaml")
    suite_path = SCRIPT_DIR / suite_file

    if not suite_path.exists():
        raise FileNotFoundError(f"Test suite not found: {suite_path}")

    with open(suite_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── LLM API Caller ──────────────────────────────────────────────────────────


def call_llm(
    system_prompt: str,
    user_message: str,
    config: dict,
    assistant_prefill: str = "",
    logger: Optional[logging.Logger] = None,
) -> dict:
    """
    Call Lemonade Server via Ollama-compatible /api/generate endpoint.

    Args:
        system_prompt: Full system prompt (soul + codebook).
        user_message: User input text.
        config: Config dict with sampling params.
        assistant_prefill: Optional prefill for assistant response.
        logger: Logger instance.

    Returns:
        dict with: response, elapsed_ms, raw_json, error (if any)
    """
    base_url = config.get("llm_base_url", "http://localhost:8000")
    endpoint = config.get("api_endpoint", "/api/generate")
    model = config.get("model_name", "test01")
    sampling = config.get("sampling", {})
    timeout = config.get("http_timeout", 30)

    url = f"{base_url}{endpoint}"

    # Build request payload (Ollama-compatible format)
    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": user_message,
        "options": {
            "temperature": sampling.get("temperature", 0.1),
            "top_k": sampling.get("top_k", 50),
            "repeat_penalty": sampling.get("repetition_penalty", 1.05),
        },
        "stream": False,
    }

    # Assistant prefill — if non-empty, prepend to prompt to force structure
    # Lemonade's /api/generate uses "prefix" field if available
    if assistant_prefill:
        payload["prefix"] = assistant_prefill

    # Max tokens via num_predict (Ollama-compatible)
    max_tokens = sampling.get("max_tokens", 80)
    payload["options"]["num_predict"] = max_tokens

    if logger:
        logger.debug(
            "call_llm: POST %s model=%s temp=%.1f top_k=%d max_tokens=%d",
            url, model, sampling.get("temperature", 0.1),
            sampling.get("top_k", 50), max_tokens,
        )

    result = {
        "response": "",
        "elapsed_ms": 0.0,
        "raw_json": {},
        "error": None,
        "request_payload": payload,
    }

    try:
        start = time.time()
        resp = requests.post(url, json=payload, timeout=timeout)
        elapsed_ms = (time.time() - start) * 1000

        result["elapsed_ms"] = elapsed_ms
        result["raw_json"] = resp.json()

        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            if logger:
                logger.error("call_llm: %s", result["error"])
            return result

        data = resp.json()
        text = data.get("response", "").strip()

        result["response"] = text

        if logger:
            logger.info(
                "call_llm: OK (%.0fms) response=%d chars",
                elapsed_ms, len(text),
            )

    except requests.exceptions.ConnectionError as e:
        result["error"] = f"ConnectionError: {e}"
        if logger:
            logger.error("call_llm: Cannot connect to %s: %s", url, e)
    except requests.exceptions.Timeout:
        result["error"] = f"Timeout after {timeout}s"
        if logger:
            logger.error("call_llm: Timeout after %ds", timeout)
    except Exception as e:
        result["error"] = f"Unexpected: {e}"
        if logger:
            logger.error("call_llm: Unexpected error: %s", e)

    return result


# ─── JSONL Logger ─────────────────────────────────────────────────────────────


class JsonlLogger:
    """Append one JSON object per line to harness_data.jsonl."""

    def __init__(self, config: dict):
        log_file = config.get("logging", {}).get("machine_log", "harness_data.jsonl")
        self.path = SCRIPT_DIR / log_file
        # Clear file at start of run
        self.path.write_text("", encoding="utf-8")

    def log(self, record: dict):
        """Append a record as one JSON line."""
        record["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─── Sanity Check ────────────────────────────────────────────────────────────


def sanity_check(config: dict, logger: logging.Logger) -> bool:
    """
    Verify Lemonade Server is reachable and model responds.

    Returns True if OK, False on failure.
    """
    logger.info("=" * 60)
    logger.info("SANITY CHECK — verifying Lemonade Server + model")
    logger.info("=" * 60)

    result = call_llm(
        system_prompt="You are a test. Respond with exactly: OK",
        user_message="ping",
        config=config,
        logger=logger,
    )

    if result["error"]:
        logger.error("SANITY CHECK FAILED: %s", result["error"])
        return False

    logger.info("SANITY CHECK PASSED: model responded in %.0fms", result["elapsed_ms"])
    logger.info("  Response: %s", result["response"][:100])
    return True


# ─── Test Runner ──────────────────────────────────────────────────────────────


def run_test_case(
    test_case: dict,
    mode: str,
    system_prompt: str,
    config: dict,
    codebook_set: set,
    hook_names: list[str],
    logger: logging.Logger,
    jsonl: JsonlLogger,
) -> dict:
    """
    Run a single test case (encode or decode).

    Args:
        test_case: dict with 'id', 'input', 'expect_no', 'expect_format'
        mode: 'encode' or 'decode'
        system_prompt: Full system prompt with codebook injected
        config: Config dict
        codebook_set: Set of codebook words
        hook_names: List of hook names to run
        logger: Logger
        jsonl: JSONL logger

    Returns:
        dict with test results
    """
    test_id = test_case["id"]
    input_text = test_case["input"]
    expect_no = test_case.get("expect_no", [])

    logger.info("─── %s ───", test_id)
    logger.info("  Input: %s", input_text)

    # Get assistant prefill from config
    prefill = config.get("assistant_prefill", {}).get(mode, "")

    # Call LLM
    llm_result = call_llm(
        system_prompt=system_prompt,
        user_message=input_text,
        config=config,
        assistant_prefill=prefill,
        logger=logger,
    )

    raw_output = llm_result["response"]
    logger.info("  Raw output: %s", raw_output)

    # Run hooks
    hook_result = run_hooks(
        text=raw_output,
        hook_names=hook_names,
        codebook_set=codebook_set if mode == "encode" else None,
    )

    cleaned_output = hook_result["cleaned"]
    logger.info("  Cleaned: %s", cleaned_output)

    if hook_result["all_violations"]:
        logger.warning("  Violations: %s", hook_result["all_violations"])

    # Check expect_no patterns
    expect_no_violations = []
    for pattern in expect_no:
        if pattern.lower() in raw_output.lower():
            expect_no_violations.append(f"expect_no match: '{pattern}'")

    # Determine pass/fail
    passed = (
        llm_result["error"] is None
        and hook_result["all_passed"]
        and len(expect_no_violations) == 0
    )

    status = "PASS" if passed else "FAIL"
    logger.info("  Status: %s", status)

    # Build result record
    record = {
        "test_id": test_id,
        "mode": mode,
        "input": input_text,
        "raw_output": raw_output,
        "cleaned_output": cleaned_output,
        "elapsed_ms": llm_result["elapsed_ms"],
        "error": llm_result["error"],
        "hook_violations": hook_result["all_violations"],
        "hook_passed": hook_result["all_passed"],
        "expect_no_violations": expect_no_violations,
        "passed": passed,
        "status": status,
        "hook_details": {},
    }

    # Add codebook hit rate for encode tests
    cb_result = hook_result.get("hook_results", {}).get("validate_codebook", {})
    if cb_result:
        record["hit_rate"] = cb_result.get("hit_rate", 0.0)
        record["hits"] = cb_result.get("hits", 0)
        record["total_words"] = cb_result.get("total", 0)
        record["oov_words"] = cb_result.get("oov_words", [])

    # Add meta-loop detection results
    ml_result = hook_result.get("hook_results", {}).get("detect_meta_loop", {})
    if ml_result:
        record["meta_phrases"] = ml_result.get("meta_phrases_found", [])

    # Store individual hook results
    for hook_name, hr in hook_result.get("hook_results", {}).items():
        record["hook_details"][hook_name] = {
            "passed": hr.get("passed", True),
            "violations": hr.get("violations", []),
        }

    # Log to JSONL
    jsonl.log(record)

    return record


def run_stress_test(
    messages: list[str],
    mode: str,
    system_prompt: str,
    config: dict,
    codebook_set: set,
    hook_names: list[str],
    logger: logging.Logger,
    jsonl: JsonlLogger,
) -> list[dict]:
    """
    Run rapid-fire stress tests for persona drift detection.

    Returns list of result dicts.
    """
    logger.info("=" * 60)
    logger.info("STRESS TEST — %s (%d messages)", mode.upper(), len(messages))
    logger.info("=" * 60)

    results = []
    for i, msg in enumerate(messages, 1):
        test_case = {
            "id": f"STR-{mode[0].upper()}-{i:03d}",
            "input": msg,
            "expect_no": [],
            "expect_format": "codebook tokens" if mode == "encode" else "plain text",
        }

        result = run_test_case(
            test_case=test_case,
            mode=mode,
            system_prompt=system_prompt,
            config=config,
            codebook_set=codebook_set,
            hook_names=hook_names,
            logger=logger,
            jsonl=jsonl,
        )
        results.append(result)

    return results


# ─── Report Generator ────────────────────────────────────────────────────────


def generate_report(config: dict, logger: logging.Logger):
    """
    Read harness_data.jsonl and generate test_report.md.
    """
    jsonl_path = SCRIPT_DIR / config.get("logging", {}).get("machine_log", "harness_data.jsonl")
    report_path = SCRIPT_DIR / config.get("logging", {}).get("report", "test_report.md")

    if not jsonl_path.exists():
        logger.error("No data file found at %s. Run tests first.", jsonl_path)
        return

    # Load all records
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        logger.error("No test records found in %s", jsonl_path)
        return

    # Categorize
    encode_results = [r for r in records if r.get("mode") == "encode" and r["test_id"].startswith("ENC")]
    decode_results = [r for r in records if r.get("mode") == "decode" and r["test_id"].startswith("DEC")]
    stress_enc = [r for r in records if r["test_id"].startswith("STR-E")]
    stress_dec = [r for r in records if r["test_id"].startswith("STR-D")]

    # Compute stats
    def stats(results: list[dict]) -> dict:
        if not results:
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0}
        total = len(results)
        passed = sum(1 for r in results if r.get("passed"))
        failed = total - passed
        avg_ms = sum(r.get("elapsed_ms", 0) for r in results) / total if total else 0
        # Count specific violations
        meta_loops = sum(1 for r in results if r.get("meta_phrases"))
        framing_violations = sum(
            1 for r in results
            if any("encode_framing" in v for v in r.get("hook_violations", []))
        )
        noise_violations = sum(
            1 for r in results
            if any("decode_noise" in v or "decode_prefix" in v for v in r.get("hook_violations", []))
        )
        # Codebook stats (encode only)
        hit_rates = [r["hit_rate"] for r in results if "hit_rate" in r]
        avg_hit = sum(hit_rates) / len(hit_rates) if hit_rates else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total * 100 if total else 0,
            "avg_ms": avg_ms,
            "meta_loops": meta_loops,
            "framing_violations": framing_violations,
            "noise_violations": noise_violations,
            "avg_hit_rate": avg_hit,
        }

    enc_stats = stats(encode_results)
    dec_stats = stats(decode_results)
    stress_enc_stats = stats(stress_enc)
    stress_dec_stats = stats(stress_dec)

    # Build report
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "---",
        'title: "Experiment F — Codec Harness Test Report"',
        f'version: "{VERSION}"',
        f'generated: "{now}"',
        f'model: "{config.get("model_name", "test01")}"',
        f'backend: "{config.get("llm_base_url", "http://localhost:8000")}"',
        "---",
        "",
        "# Experiment F — Codec Harness Test Report",
        "",
        f"Generated: {now}",
        f"Model: {config.get('model_name', 'test01')}",
        f"Backend: {config.get('llm_base_url', 'http://localhost:8000')}",
        "",
        "## Summary",
        "",
        "| Suite | Total | Passed | Failed | Pass Rate | Avg Latency |",
        "|-------|-------|--------|--------|-----------|-------------|",
        f"| Encode (20) | {enc_stats['total']} | {enc_stats['passed']} | {enc_stats['failed']} | {enc_stats['pass_rate']:.0f}% | {enc_stats['avg_ms']:.0f}ms |",
        f"| Decode (20) | {dec_stats['total']} | {dec_stats['passed']} | {dec_stats['failed']} | {dec_stats['pass_rate']:.0f}% | {dec_stats['avg_ms']:.0f}ms |",
        f"| Stress Encode | {stress_enc_stats['total']} | {stress_enc_stats['passed']} | {stress_enc_stats['failed']} | {stress_enc_stats['pass_rate']:.0f}% | {stress_enc_stats['avg_ms']:.0f}ms |",
        f"| Stress Decode | {stress_dec_stats['total']} | {stress_dec_stats['passed']} | {stress_dec_stats['failed']} | {stress_dec_stats['pass_rate']:.0f}% | {stress_dec_stats['avg_ms']:.0f}ms |",
        "",
        "## Issue Gates",
        "",
        "| Issue | Metric | Target | Result | Status |",
        "|-------|--------|--------|--------|--------|",
        f"| #1 Meta-loop | Detections | 0 | {enc_stats['meta_loops'] + dec_stats['meta_loops'] + stress_enc_stats['meta_loops'] + stress_dec_stats['meta_loops']} | {'PASS' if (enc_stats['meta_loops'] + dec_stats['meta_loops'] + stress_enc_stats['meta_loops'] + stress_dec_stats['meta_loops']) == 0 else 'FAIL'} |",
        f"| #2 Encode framing | Raw violations | <10% | {enc_stats['framing_violations']}/{enc_stats['total']} ({enc_stats['framing_violations']/enc_stats['total']*100 if enc_stats['total'] else 0:.0f}%) | {'PASS' if enc_stats['total'] and enc_stats['framing_violations']/enc_stats['total'] <= 0.10 else 'FAIL' if enc_stats['total'] else 'N/A'} |",
        f"| #3 Decode noise | Raw violations | <10% | {dec_stats['noise_violations']}/{dec_stats['total']} ({dec_stats['noise_violations']/dec_stats['total']*100 if dec_stats['total'] else 0:.0f}%) | {'PASS' if dec_stats['total'] and dec_stats['noise_violations']/dec_stats['total'] <= 0.10 else 'FAIL' if dec_stats['total'] else 'N/A'} |",
        f"| Codebook hit rate | Avg encode | >=70% | {enc_stats['avg_hit_rate']*100:.1f}% | {'PASS' if enc_stats['avg_hit_rate'] >= 0.70 else 'FAIL'} |",
        "",
    ]

    # Encode details
    if encode_results:
        lines.extend([
            "## Encode Test Details",
            "",
            "| ID | Status | Latency | Hit Rate | OOV | Violations |",
            "|----|--------|---------|----------|-----|------------|",
        ])
        for r in encode_results:
            hr = f"{r.get('hit_rate', 0)*100:.0f}%" if 'hit_rate' in r else "N/A"
            oov = ", ".join(r.get("oov_words", [])[:5]) or "none"
            violations = "; ".join(r.get("hook_violations", [])[:3]) or "none"
            lines.append(
                f"| {r['test_id']} | {r['status']} | {r['elapsed_ms']:.0f}ms | {hr} | {oov} | {violations} |"
            )
        lines.append("")

    # Decode details
    if decode_results:
        lines.extend([
            "## Decode Test Details",
            "",
            "| ID | Status | Latency | Violations |",
            "|----|--------|---------|------------|",
        ])
        for r in decode_results:
            violations = "; ".join(r.get("hook_violations", [])[:3]) or "none"
            lines.append(
                f"| {r['test_id']} | {r['status']} | {r['elapsed_ms']:.0f}ms | {violations} |"
            )
        lines.append("")

    # Stress summary
    if stress_enc or stress_dec:
        lines.extend([
            "## Stress Test Summary",
            "",
            f"Encode stress: {stress_enc_stats['passed']}/{stress_enc_stats['total']} passed, "
            f"{stress_enc_stats['meta_loops']} meta-loops, "
            f"{stress_enc_stats['framing_violations']} framing violations",
            "",
            f"Decode stress: {stress_dec_stats['passed']}/{stress_dec_stats['total']} passed, "
            f"{stress_dec_stats['meta_loops']} meta-loops, "
            f"{stress_dec_stats['noise_violations']} noise violations",
            "",
        ])

    # Failed test details
    failed = [r for r in records if not r.get("passed")]
    if failed:
        lines.extend([
            "## Failed Tests — Detail",
            "",
        ])
        for r in failed:
            lines.extend([
                f"### {r['test_id']} ({r['mode']})",
                "",
                f"Input: `{r['input']}`",
                "",
                f"Raw output: `{r['raw_output']}`",
                "",
                f"Cleaned: `{r['cleaned_output']}`",
                "",
                f"Violations: {r.get('hook_violations', [])}",
                "",
                f"Expect-no violations: {r.get('expect_no_violations', [])}",
                "",
            ])

    lines.extend([
        "---",
        "",
        f"*Report generated by CyberMesh Codec Harness v{VERSION}*",
    ])

    report_text = "\n".join(lines)
    report_path.write_text(report_text, encoding="utf-8")
    logger.info("Report written to %s (%d lines)", report_path, len(lines))


# ─── Main Entry Point ────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="CyberMesh Codec Harness — Experiment F",
    )
    parser.add_argument(
        "--mode",
        choices=["sanity-check", "encode", "decode", "stress", "full"],
        default="full",
        help="Test mode to run (default: full)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate test_report.md from existing harness_data.jsonl",
    )
    args = parser.parse_args()

    # Load config
    config = load_config()
    logger = setup_logging(config)

    logger.info("=" * 60)
    logger.info("CyberMesh Codec Harness v%s — Experiment %s", VERSION, config.get("experiment", "F"))
    logger.info("Model: %s @ %s", config.get("model_name"), config.get("llm_base_url"))
    logger.info("Mode: %s", "report" if args.report else args.mode)
    logger.info("=" * 60)

    # Report-only mode
    if args.report:
        generate_report(config, logger)
        return

    # Sanity check first
    if not sanity_check(config, logger):
        logger.error("Sanity check failed. Is Lemonade Server running?")
        sys.exit(1)

    if args.mode == "sanity-check":
        logger.info("Sanity check passed. Exiting.")
        return

    # Load resources
    codebook_words, codebook_set = load_codebook(config)
    subset_size = config.get("codebook", {}).get("subset_size", 200)
    codebook_subset_str = build_codebook_subset(codebook_words, subset_size)

    logger.info("Codebook loaded: %d words, subset: %d", len(codebook_words), subset_size)

    # Load soul prompts and inject codebook
    encode_soul_raw = load_soul(config, "encode")
    decode_soul_raw = load_soul(config, "decode")

    encode_prompt = encode_soul_raw.replace("{codebook_subset}", codebook_subset_str)
    decode_prompt = decode_soul_raw  # no codebook injection for decode

    logger.info("Encode prompt: %d chars", len(encode_prompt))
    logger.info("Decode prompt: %d chars", len(decode_prompt))

    # Load test suite
    suite = load_test_suite(config)
    logger.info("Test suite loaded: %d encode, %d decode, stress encode=%d decode=%d",
                len(suite.get("encode", [])),
                len(suite.get("decode", [])),
                len(suite.get("stress", {}).get("encode_messages", [])),
                len(suite.get("stress", {}).get("decode_messages", [])))

    # Get hook names from config
    encode_hooks = config.get("hooks", {}).get("encode", [])
    decode_hooks = config.get("hooks", {}).get("decode", [])

    logger.info("Encode hooks: %s", encode_hooks)
    logger.info("Decode hooks: %s", decode_hooks)

    # Initialize JSONL logger
    jsonl = JsonlLogger(config)

    all_results = []

    # ─── Encode Tests ───
    if args.mode in ("encode", "full"):
        logger.info("=" * 60)
        logger.info("ENCODE TESTS (%d cases)", len(suite.get("encode", [])))
        logger.info("=" * 60)

        for tc in suite.get("encode", []):
            result = run_test_case(
                test_case=tc,
                mode="encode",
                system_prompt=encode_prompt,
                config=config,
                codebook_set=codebook_set,
                hook_names=encode_hooks,
                logger=logger,
                jsonl=jsonl,
            )
            all_results.append(result)

    # ─── Decode Tests ───
    if args.mode in ("decode", "full"):
        logger.info("=" * 60)
        logger.info("DECODE TESTS (%d cases)", len(suite.get("decode", [])))
        logger.info("=" * 60)

        for tc in suite.get("decode", []):
            result = run_test_case(
                test_case=tc,
                mode="decode",
                system_prompt=decode_prompt,
                config=config,
                codebook_set=codebook_set,
                hook_names=decode_hooks,
                logger=logger,
                jsonl=jsonl,
            )
            all_results.append(result)

    # ─── Stress Tests ───
    if args.mode in ("stress", "full"):
        stress_config = suite.get("stress", {})

        # Stress encode
        enc_msgs = stress_config.get("encode_messages", [])
        if enc_msgs:
            stress_enc = run_stress_test(
                messages=enc_msgs,
                mode="encode",
                system_prompt=encode_prompt,
                config=config,
                codebook_set=codebook_set,
                hook_names=encode_hooks,
                logger=logger,
                jsonl=jsonl,
            )
            all_results.extend(stress_enc)

        # Stress decode
        dec_msgs = stress_config.get("decode_messages", [])
        if dec_msgs:
            stress_dec = run_stress_test(
                messages=dec_msgs,
                mode="decode",
                system_prompt=decode_prompt,
                config=config,
                codebook_set=codebook_set,
                hook_names=decode_hooks,
                logger=logger,
                jsonl=jsonl,
            )
            all_results.extend(stress_dec)

    # ─── Summary ───
    total = len(all_results)
    passed = sum(1 for r in all_results if r.get("passed"))
    failed = total - passed

    logger.info("=" * 60)
    logger.info("RESULTS: %d/%d passed, %d failed", passed, total, failed)
    logger.info("=" * 60)

    # Generate report
    generate_report(config, logger)

    # Exit code: 0 if all passed, 1 if any failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
