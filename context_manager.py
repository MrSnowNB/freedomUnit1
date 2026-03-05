#!/usr/bin/env python3
"""
context_manager.py — Per-sender conversation history for CyberMesh v7.0
========================================================================
Thread-safe conversation state manager. Tracks message history per sender,
implements sliding window with anchor-first pattern (ported from Operator v2).

The anchor-first pattern keeps the first exchange (system context) in the
window even as newer messages push older ones out. This ensures the LLM
always has the conversation opener for context.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import logging
import threading

logger = logging.getLogger(__name__)


class ContextManager:
    """Thread-safe per-sender conversation history with sliding window."""

    def __init__(self, window_size: int = 4, anchor_first: bool = True):
        """
        Args:
            window_size: Number of conversation exchanges (user+assistant pairs)
                         to keep per sender.
            anchor_first: If True, always keep the first exchange even when
                          trimming (Operator v2 pattern).
        """
        self.window_size = window_size
        self.anchor_first = anchor_first
        self._history: dict[str, list[dict[str, str]]] = {}
        self._lock = threading.Lock()

        logger.info("ContextManager init: window_size=%d, anchor_first=%s",
                     window_size, anchor_first)

    def add(self, sender_id: str, role: str, content: str):
        """
        Add a message to a sender's conversation history.

        Args:
            sender_id: Unique identifier for the sender/conversation.
            role: Message role — "user" or "assistant".
            content: Message text content.
        """
        with self._lock:
            if sender_id not in self._history:
                self._history[sender_id] = []
                logger.debug("ContextManager: new sender '%s'", sender_id)

            self._history[sender_id].append({
                "role": role,
                "content": content,
            })

            # Trim: keep first exchange + last (window_size - 1) exchanges
            hist = self._history[sender_id]
            max_messages = self.window_size * 2  # pairs of user+assistant

            if len(hist) > max_messages:
                if self.anchor_first:
                    # Keep first pair (anchor) + most recent messages
                    first_pair = hist[:2]
                    recent = hist[-(max_messages - 2):]
                    self._history[sender_id] = first_pair + recent
                    logger.debug("ContextManager: trimmed '%s' to %d messages "
                                 "(anchor + %d recent)",
                                 sender_id, len(self._history[sender_id]),
                                 len(recent))
                else:
                    # Simple sliding window — keep most recent
                    self._history[sender_id] = hist[-max_messages:]
                    logger.debug("ContextManager: trimmed '%s' to %d messages",
                                 sender_id, max_messages)

    def get(self, sender_id: str) -> list[dict[str, str]]:
        """
        Get conversation history for a sender.

        Args:
            sender_id: Unique identifier for the sender.

        Returns:
            List of {"role": ..., "content": ...} dicts.
            Returns empty list if sender not found.
        """
        with self._lock:
            return list(self._history.get(sender_id, []))

    def clear(self, sender_id: str):
        """Remove all history for a sender."""
        with self._lock:
            removed = self._history.pop(sender_id, None)
            if removed:
                logger.debug("ContextManager: cleared '%s' (%d messages)",
                             sender_id, len(removed))

    def clear_all(self):
        """Remove all history for all senders."""
        with self._lock:
            count = len(self._history)
            self._history.clear()
            logger.info("ContextManager: cleared all %d senders", count)

    def sender_count(self) -> int:
        """Return number of active senders."""
        with self._lock:
            return len(self._history)

    def message_count(self, sender_id: str) -> int:
        """Return message count for a sender."""
        with self._lock:
            return len(self._history.get(sender_id, []))


# ---------------------------------------------------------------------------
# CLI — standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("=" * 78)
    print("  CONTEXT MANAGER v7.0 — CyberMesh / Liberty Mesh")
    print("=" * 78)

    all_pass = True

    # Test 1: Basic add/get
    print("\n  [1] Basic add/get")
    cm = ContextManager(window_size=4, anchor_first=True)
    cm.add("node-A", "user", "Hello from node A")
    cm.add("node-A", "assistant", "Hello back from node A")
    hist = cm.get("node-A")
    ok = (len(hist) == 2 and
          hist[0]["role"] == "user" and
          hist[1]["role"] == "assistant")
    print(f"      Messages: {len(hist)}  Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 2: Sender isolation
    print("\n  [2] Sender isolation")
    cm.add("node-B", "user", "Hello from node B")
    hist_a = cm.get("node-A")
    hist_b = cm.get("node-B")
    ok = len(hist_a) == 2 and len(hist_b) == 1
    print(f"      node-A: {len(hist_a)}, node-B: {len(hist_b)}  "
          f"Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 3: Window trimming with anchor
    print("\n  [3] Window trimming with anchor (window_size=4)")
    cm2 = ContextManager(window_size=4, anchor_first=True)
    # Add 10 exchanges (20 messages) — should trim to 8 (4 pairs)
    for i in range(10):
        cm2.add("test", "user", f"User message {i}")
        cm2.add("test", "assistant", f"Assistant message {i}")
    hist = cm2.get("test")
    # Should have 8 messages: first pair (0) + last 3 pairs (7,8,9)
    ok = len(hist) == 8
    first_ok = (hist[0]["content"] == "User message 0" and
                hist[1]["content"] == "Assistant message 0")
    last_ok = hist[-1]["content"] == "Assistant message 9"
    all_ok = ok and first_ok and last_ok
    print(f"      Total messages: {len(hist)} (expected 8)")
    print(f"      Anchor preserved: {first_ok}")
    print(f"      Latest preserved: {last_ok}")
    print(f"      Result: {'PASS ✓' if all_ok else 'FAIL ✗'}")
    if not all_ok: all_pass = False
    # Print the window contents
    for j, m in enumerate(hist):
        print(f"        [{j}] {m['role']}: \"{m['content']}\"")

    # Test 4: Window trimming without anchor
    print("\n  [4] Window trimming WITHOUT anchor (window_size=4)")
    cm3 = ContextManager(window_size=4, anchor_first=False)
    for i in range(10):
        cm3.add("test2", "user", f"User message {i}")
        cm3.add("test2", "assistant", f"Assistant message {i}")
    hist = cm3.get("test2")
    ok = len(hist) == 8
    # Without anchor, first message should be from exchange 6 (not 0)
    first_ok = hist[0]["content"] == "User message 6"
    last_ok = hist[-1]["content"] == "Assistant message 9"
    all_ok = ok and first_ok and last_ok
    print(f"      Total messages: {len(hist)} (expected 8)")
    print(f"      Oldest is exchange 6: {first_ok}")
    print(f"      Latest preserved: {last_ok}")
    print(f"      Result: {'PASS ✓' if all_ok else 'FAIL ✗'}")
    if not all_ok: all_pass = False

    # Test 5: Thread safety (basic stress test)
    print("\n  [5] Thread safety — 3 senders, 10 exchanges each")
    import concurrent.futures
    cm4 = ContextManager(window_size=4, anchor_first=True)

    def add_messages(sender, count):
        for i in range(count):
            cm4.add(sender, "user", f"msg-{i}")
            cm4.add(sender, "assistant", f"reply-{i}")
        return sender, cm4.message_count(sender)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(add_messages, f"sender-{s}", 10)
                   for s in range(3)]
        results = [f.result() for f in futures]

    ok = all(count == 8 for _, count in results)  # trimmed to window_size*2
    print(f"      Senders: {cm4.sender_count()}")
    for sender, count in results:
        print(f"        {sender}: {count} messages")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 6: Clear
    print("\n  [6] Clear operations")
    cm4.clear("sender-0")
    ok1 = cm4.message_count("sender-0") == 0
    ok2 = cm4.sender_count() == 2
    cm4.clear_all()
    ok3 = cm4.sender_count() == 0
    all_ok = ok1 and ok2 and ok3
    print(f"      After clear(sender-0): {ok1}")
    print(f"      Remaining senders: {ok2}")
    print(f"      After clear_all: {ok3}")
    print(f"      Result: {'PASS ✓' if all_ok else 'FAIL ✗'}")
    if not all_ok: all_pass = False

    print(f"\n{'=' * 78}")
    print(f"  ALL TESTS: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print(f"{'=' * 78}\n")
