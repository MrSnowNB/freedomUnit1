#!/usr/bin/env python3
"""
llm_client.py — Thin LLM API wrapper for Lemonade (OpenAI-compatible)
======================================================================
Raw HTTP requests to Lemonade's /v1/chat/completions endpoint.
No openai library dependency. All timing via time.perf_counter().

Mock mode: when config testing.mock_llm is true, returns hardcoded
responses without hitting the network. For CI/offline validation.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import json
import logging
import time
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around Lemonade OpenAI-compatible API."""

    def __init__(self, base_url: str, model: str, timeout: int = 45,
                 mock: bool = False):
        """
        Args:
            base_url: Lemonade server URL (no trailing slash).
            model:    Model name/alias (e.g. 'test01').
            timeout:  HTTP request timeout in seconds.
            mock:     If True, return hardcoded responses (no network).
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.mock = mock
        self._endpoint = f"{self.base_url}/v1/chat/completions"
        logger.info("LLMClient init: model=%s url=%s mock=%s",
                     model, self.base_url, mock)

    def _call(self, messages: list[dict], max_tokens: int = 200,
              temperature: float = 0.7) -> tuple[str, float]:
        """
        Send a chat completion request. Returns (text, elapsed_ms).

        On timeout or error: returns ("", elapsed_ms) and logs the error.
        """
        t0 = time.perf_counter()

        if self.mock:
            return self._mock_response(messages, max_tokens, temperature)

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            elapsed_ms = (time.perf_counter() - t0) * 1000
            text = data["choices"][0]["message"]["content"].strip()
            logger.debug("LLM response (%d tokens, %.1f ms): %s",
                         max_tokens, elapsed_ms, text[:80])
            return text, elapsed_ms

        except urllib.error.URLError as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.error("LLM request failed (%.1f ms): %s", elapsed_ms, e)
            return "", elapsed_ms

        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.error("LLM unexpected error (%.1f ms): %s", elapsed_ms, e)
            return "", elapsed_ms

    def generate(self, system_prompt: str, user_prompt: str,
                 max_tokens: int = 200, temperature: float = 0.7
                 ) -> tuple[str, float]:
        """
        Generate a response. Returns (generated_text, elapsed_ms).

        Standard chat completion with configurable tokens and temperature.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._call(messages, max_tokens=max_tokens,
                          temperature=temperature)

    def classify(self, system_prompt: str, user_prompt: str
                 ) -> tuple[str, float]:
        """
        Classify a message. Returns (category_string, elapsed_ms).

        Uses max_tokens=5, temperature=0.0 for deterministic single-token
        classification. Result is stripped and lowercased.
        """
        text, elapsed_ms = self.generate(
            system_prompt, user_prompt,
            max_tokens=5, temperature=0.0,
        )
        return text.strip().lower(), elapsed_ms

    def warmup(self) -> float:
        """
        Send a trivial prompt to load the model into memory.

        Returns elapsed_ms. Logs success or failure.
        """
        logger.info("LLM warmup starting...")
        text, elapsed_ms = self.generate(
            system_prompt="You are a test assistant.",
            user_prompt="Reply with the single word: ready",
            max_tokens=5,
            temperature=0.0,
        )
        if text:
            logger.info("LLM warmup complete: %.1f ms — response: '%s'",
                         elapsed_ms, text)
        else:
            logger.warning("LLM warmup returned empty (%.1f ms) — "
                           "model may not be loaded", elapsed_ms)
        return elapsed_ms

    # ── Mock responses for offline/CI testing ──

    def _mock_response(self, messages: list[dict], max_tokens: int,
                       temperature: float) -> tuple[str, float]:
        """Return deterministic mock responses based on system prompt content."""
        t0 = time.perf_counter()

        system = ""
        user = ""
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            elif msg["role"] == "user":
                user = msg["content"]

        # Keyword extraction mock
        if "keyword extractor" in system.lower():
            # Return important words from user prompt
            stop_words = {
                "a", "an", "the", "in", "on", "at", "for", "to", "of",
                "from", "is", "are", "was", "were", "been", "being",
                "have", "has", "had",
            }
            words = user.lower().split()
            keywords = [w for w in words if w not in stop_words][:20]
            result = " ".join(keywords)

        # Classification mock
        elif "classify" in system.lower() and max_tokens <= 5:
            text_lower = user.lower()
            if any(w in text_lower for w in ["report", "update", "status",
                                               "reading", "level"]):
                result = "status"
            elif any(w in text_lower for w in ["move", "evacuate", "deploy",
                                                 "send", "activate"]):
                result = "command"
            elif any(w in text_lower for w in ["summary", "brief",
                                                 "overview"]):
                result = "briefing"
            elif any(w in text_lower for w in ["sensor", "data", "value",
                                                 "measurement"]):
                result = "data"
            else:
                result = "narrative"

        # Reconstruction mock
        elif "reconstructor" in system.lower():
            result = f"Message: {user}"

        # Generic / warmup
        else:
            result = "ready"

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.debug("MOCK response (%.3f ms): %s", elapsed_ms, result[:80])
        return result, elapsed_ms


# ---------------------------------------------------------------------------
# CLI — standalone validation
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import sys
    import yaml

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Load config
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "config.yaml")

    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as f:
            cfg = yaml.safe_load(f)
    else:
        print(f"WARNING: {cfg_path} not found, using defaults")
        cfg = {
            "lemonade": {"base_url": "http://localhost:8000",
                         "model": "test01", "timeout_s": 45},
            "testing": {"mock_llm": True},
        }

    mock_mode = cfg.get("testing", {}).get("mock_llm", False)

    # Allow CLI override: python llm_client.py --mock
    if "--mock" in sys.argv:
        mock_mode = True

    lem = cfg.get("lemonade", {})
    client = LLMClient(
        base_url=lem.get("base_url", "http://localhost:8000"),
        model=lem.get("model", "test01"),
        timeout=lem.get("timeout_s", 45),
        mock=mock_mode,
    )

    print("=" * 70)
    print(f"  LLM CLIENT VALIDATION — mock={mock_mode}")
    print("=" * 70)

    # Test 1: Warmup
    print("\n  [Test 1] Warmup")
    warmup_ms = client.warmup()
    print(f"    Warmup: {warmup_ms:.1f} ms")
    print(f"    Result: {'PASS' if warmup_ms >= 0 else 'FAIL'}")

    # Test 2: Generate
    print("\n  [Test 2] Generate")
    text, gen_ms = client.generate(
        system_prompt="You are a mesh network agent.",
        user_prompt="Report the status of sensor 5.",
        max_tokens=50,
    )
    print(f"    Response: '{text[:60]}{'...' if len(text) > 60 else ''}'")
    print(f"    Timing:   {gen_ms:.1f} ms")
    print(f"    Result:   {'PASS' if text else 'FAIL — empty response'}")

    # Test 3: Classify
    print("\n  [Test 3] Classify")
    category, cls_ms = client.classify(
        system_prompt=("Classify this radio message into exactly one category.\n"
                       "Categories: command, status, narrative, data, briefing\n"
                       "Reply with ONLY the category name, one word, nothing else."),
        user_prompt="Sensor 5 reads 2.1 feet and rising.",
    )
    valid_cats = {"command", "status", "narrative", "data", "briefing"}
    print(f"    Category: '{category}'")
    print(f"    Timing:   {cls_ms:.1f} ms")
    print(f"    Valid:    {'PASS' if category in valid_cats else 'FAIL — not a valid category'}")

    # Test 4: Keyword extraction (mock validation)
    print("\n  [Test 4] Keyword extraction prompt")
    kw_sys = """You are a keyword extractor for emergency radio messages.
Extract ONLY the important information-carrying words.
Return keywords separated by spaces on a single line.
Rules:
- Remove articles (a, an, the), prepositions (in, on, at, for, to, of, from)
- Remove filler (is, are, was, were, been, being, have, has, had)
- KEEP all numbers exactly as written
- KEEP negation words (not, no, never, none, dont, cant, wont)
- KEEP proper nouns (names, places)
- KEEP action verbs and status words
- Maximum 20 keywords
- Output ONLY keywords separated by spaces, nothing else"""
    kw_text, kw_ms = client.generate(
        system_prompt=kw_sys,
        user_prompt="The flood warning is active for Lawrence Township and sensors are operational but station 7 is offline",
        max_tokens=50,
        temperature=0.0,
    )
    print(f"    Keywords: '{kw_text}'")
    print(f"    Timing:   {kw_ms:.1f} ms")
    print(f"    Result:   {'PASS' if kw_text else 'FAIL — empty'}")

    print(f"\n{'=' * 70}")
    print("  All tests complete.")
    print(f"{'=' * 70}\n")
