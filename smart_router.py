#!/usr/bin/env python3
"""
smart_router.py — AI Smart Router for CyberMesh v7.0
=====================================================
Classifies messages and routes to strict, lossy, or paginate path.

Route logic:
  1. SIZE CHECK (no LLM call): encoded_bytes ≤ strict_threshold → "strict"
  2. LLM CLASSIFICATION (only on overflow): classify message type
  3. MAP category to route:
     - lossy_categories (status, briefing) → "lossy" (keyword mode)
     - lossless_categories (command, narrative, data) → "paginate" (lossless)
     - unknown → "paginate" (safe default — lossless)

The router is ZERO COST for the common case (message fits in 180 bytes).
LLM classification only fires on overflow.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import logging
import time

logger = logging.getLogger(__name__)


class SmartRouter:
    """Classify messages and route to strict, lossy, or paginate path."""

    def __init__(self, llm_client, config: dict):
        """
        Args:
            llm_client: LLMClient instance (or mock).
            config: Full config dict (needs 'router' section).
        """
        self.llm = llm_client
        router_cfg = config.get("router", {})
        self.strict_threshold = router_cfg.get("strict_threshold", 180)
        self.lossy_cats = set(router_cfg.get("lossy_categories",
                                               ["status", "briefing"]))
        self.lossless_cats = set(router_cfg.get("lossless_categories",
                                                  ["command", "narrative",
                                                   "data"]))
        self.all_categories = router_cfg.get("classify_categories",
                                              ["command", "status",
                                               "narrative", "data",
                                               "briefing"])

        # Expose timing for logging
        self.last_classify_ms: float = 0.0
        self.last_category: str = ""

        # Exact classification prompt from v7.0 spec
        self._classify_system = (
            "Classify this radio message into exactly one category.\n"
            "Categories: command, status, narrative, data, briefing\n"
            "Reply with ONLY the category name, one word, nothing else."
        )

        logger.info("SmartRouter init: threshold=%d, lossy=%s, lossless=%s",
                     self.strict_threshold, self.lossy_cats, self.lossless_cats)

    def route(self, encoded_bytes: bytes, original_text: str) -> str:
        """
        Determine routing for a message.

        Args:
            encoded_bytes: Codec-encoded payload (used for size check).
            original_text: Original text (used for LLM classification).

        Returns:
            One of: "strict", "lossy", "paginate"
        """
        t0 = time.perf_counter()

        # Step 1: Size check (no LLM call needed)
        if len(encoded_bytes) <= self.strict_threshold:
            self.last_classify_ms = 0.0
            self.last_category = "n/a"
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("SmartRouter: STRICT (size=%d ≤ %d) %.1f ms",
                         len(encoded_bytes), self.strict_threshold,
                         elapsed_ms)
            return "strict"

        # Step 2: LLM classification (only if overflow)
        category, classify_ms = self.llm.classify(
            self._classify_system,
            original_text[:200],  # First 200 chars per spec
        )
        self.last_classify_ms = classify_ms
        self.last_category = category

        # Step 3: Map category to route
        if category in self.lossy_cats:
            route = "lossy"
        elif category in self.lossless_cats:
            route = "paginate"
        else:
            # Unknown category — safe default to paginate (lossless)
            route = "paginate"
            logger.warning("SmartRouter: unknown category '%s' → "
                           "defaulting to paginate", category)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("SmartRouter: %s (size=%d > %d, category='%s') "
                     "%.1f ms (LLM: %.1f ms)",
                     route.upper(), len(encoded_bytes),
                     self.strict_threshold, category,
                     elapsed_ms, classify_ms)

        return route


# ---------------------------------------------------------------------------
# CLI — standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import sys
    import yaml

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Load config
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "config.yaml")
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)

    from llm_client import LLMClient
    lem = cfg.get("lemonade", {})
    mock_mode = cfg.get("testing", {}).get("mock_llm", False)
    if "--mock" in sys.argv:
        mock_mode = True

    client = LLMClient(
        base_url=lem.get("base_url", "http://localhost:8000"),
        model=lem.get("model", "test01"),
        timeout=lem.get("timeout_s", 45),
        mock=mock_mode,
    )

    router = SmartRouter(llm_client=client, config=cfg)

    print("=" * 78)
    print(f"  SMART ROUTER v7.0 — mock={mock_mode}")
    print(f"  Threshold: {router.strict_threshold} bytes")
    print("=" * 78)

    # Test messages with varying sizes and types
    test_cases = [
        # (message, simulated_encoded_size, expected_route)
        ("ok", 2, "strict"),
        ("sensor online", 8, "strict"),
        ("battery at 89 percent signal strong", 20, "strict"),
        # Messages that exceed threshold — classification needed
        ("The water level at sensor 5 reads 2.1 feet and is rising fast. "
         "We need to monitor closely and prepare for potential evacuation "
         "of the low-lying areas near the river bend." * 2,
         250, None),  # None = depends on classification
        ("Deploy rescue team to north sector immediately. "
         "Three casualties reported at intersection. Send ambulance." * 2,
         300, None),
        ("All sensors reporting normal status. Battery levels above 80 "
         "percent across the mesh. Signal strength is good." * 2,
         280, None),
        ("Executive summary: The flood event began at 0300 and peaked at "
         "0800. Total sensors affected: 12. Estimated damage: moderate." * 2,
         320, None),
    ]

    all_pass = True
    for i, (msg, sim_size, expected) in enumerate(test_cases, 1):
        # Create simulated encoded bytes of the given size
        encoded = bytes(sim_size)
        route = router.route(encoded, msg)

        if expected is not None:
            ok = route == expected
            if not ok:
                all_pass = False
        else:
            ok = route in ("strict", "lossy", "paginate")

        status = "PASS ✓" if ok else "FAIL ✗"
        expected_str = f" (expected: {expected})" if expected else ""
        print(f"\n  [{i}] {status} → {route.upper()}{expected_str}")
        print(f"      Size: {sim_size} bytes "
              f"{'≤' if sim_size <= router.strict_threshold else '>'} "
              f"{router.strict_threshold}")
        if router.last_category != "n/a":
            print(f"      Category: '{router.last_category}' "
                  f"(classify: {router.last_classify_ms:.1f} ms)")
        print(f"      Message: \"{msg[:70]}{'...' if len(msg) > 70 else ''}\"")

    print(f"\n{'=' * 78}")
    print(f"  RESULT: {'ALL TESTS PASS ✓' if all_pass else 'FAILURES ✗'}")
    print(f"{'=' * 78}\n")
