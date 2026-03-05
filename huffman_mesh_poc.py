#!/usr/bin/env python3
"""
huffman_mesh_poc.py — Experiment D: LLM Codec + Pre-Tokenizer Over LoRa
=========================================================================
v4.0: Adds pre-tokenizer (Phase 1) and LLM encode/decode codec (Phase 2)
to the LLM conversation pipeline from Experiment C.

Config-driven behavior:
  llm_codec: false  → Phase 1 (pretokenizer + raw codec, like Exp C with normalization)
  llm_codec: true   → Phase 2 (pretokenizer + LLM encode/decode + codec)

One "Hi" DM triggers the full experiment:
  Phase 1: Run 1: MUX Grid + pretokenizer → Run 2: Huffman + pretokenizer
  Phase 2: Run 1: MUX Grid + LLM codec   → Run 2: Huffman + LLM codec

Each message pipeline:
  Phase 1 (Sender): LLM generate → normalize() → codec.encode() → TX
  Phase 2 (Sender): LLM generate → LLM encode → normalize() → codec.encode() → TX
  Phase 2 (Receiver): codec.decode() → LLM decode → conversation history

Transport: sendData() with PRIVATE_APP portNum 256 (raw bytes).
Logging: Full conversation transcript + per-message metrics + comparison + JSON.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import os
import sys
import time
import json
import yaml
import threading
import requests
from datetime import datetime, timezone
from pubsub import pub

# ── Meshtastic imports ──
try:
    import meshtastic
    import meshtastic.serial_interface
except ImportError:
    print("ERROR: meshtastic package not installed.")
    print("  pip install meshtastic")
    sys.exit(1)

# ── Local imports ──
from mesh_huffman import MeshHuffmanCodec
from mux_codec import MuxGridCodec, CODEC_ID_HUFFMAN, CODEC_ID_MUX_GRID
from paginator import paginate, reassemble
from pretokenizer import normalize, compute_hit_rate
from llm_codec import llm_encode, llm_decode, get_codebook_words

VERSION = "4.0"
EXPERIMENT = "D"


# ==========================================
# LOGGING
# ==========================================

LOG_ENTRIES = []

def log(msg: str, level: str = "INFO"):
    """Structured log with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {"ts": ts, "level": level, "msg": msg}
    LOG_ENTRIES.append(entry)
    prefix = {"INFO": "  ", "WARN": "  ⚠", "ERROR": "  ✗", "DEBUG": "  [DBG]"}.get(level, "  ")
    print(f"{prefix} [{ts}] {msg}")


# ==========================================
# CONFIGURATION
# ==========================================

def load_config() -> dict:
    """Load config.yaml from script directory."""
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    raise FileNotFoundError(f"config.yaml not found at {cfg_path}")


# ==========================================
# LLM INTEGRATION — Ollama / Gemma3
# ==========================================

OLLAMA_URL = "http://localhost:11434"

def warmup_model(model_name: str) -> float:
    """Force model into memory. Returns warmup time in seconds."""
    log(f"Warming up model '{model_name}'...")
    start = time.time()
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model_name,
            "prompt": "warmup",
            "options": {"num_predict": 1},
            "stream": False
        }, timeout=120)
        elapsed = time.time() - start
        if resp.status_code == 200:
            log(f"Model '{model_name}' loaded in {elapsed:.1f}s")
            return elapsed
        else:
            raise RuntimeError(f"Ollama returned {resp.status_code}: {resp.text[:200]}")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_URL}. Is it running?")


def generate_response(model: str, system_prompt: str,
                      conversation_history: list[dict]) -> tuple[str, float, int]:
    """
    Generate an LLM response given the conversation history.

    Returns: (text, inference_ms, token_count)
    """
    full_prompt = system_prompt + "\n\nConversation so far:\n"
    for entry in conversation_history:
        role = "You" if entry["sent"] else "Them"
        full_prompt += f"{role}: {entry['text']}\n"
    full_prompt += "You: "

    start = time.time()
    resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": model,
        "prompt": full_prompt,
        "options": {"temperature": 0.7},
        "stream": False
    }, timeout=60)
    elapsed_ms = (time.time() - start) * 1000

    data = resp.json()
    text = data.get("response", "").strip()

    # Clean up: remove quotes, markdown, multiline
    text = text.strip('"\'')
    if '\n' in text:
        text = text.split('\n')[0].strip()

    token_count = data.get("eval_count", len(text.split()))

    return text, elapsed_ms, token_count


# ==========================================
# CODEC WRAPPER
# ==========================================

class CodecWrapper:
    """Wraps Huffman or MUX Grid codec with unified 3-byte packet header."""

    def __init__(self, codec_name: str):
        self.codec_name = codec_name.lower()
        if self.codec_name == "huffman":
            self.huffman = MeshHuffmanCodec()
            self.mux = None
            self.codec_id = CODEC_ID_HUFFMAN
        elif self.codec_name == "mux_grid":
            self.huffman = None
            self.mux = MuxGridCodec()
            self.codec_id = CODEC_ID_MUX_GRID
        else:
            raise ValueError(f"Unknown codec: {codec_name}")

        # Both decoders for auto-detection on receive
        self._huffman_decoder = MeshHuffmanCodec()
        self._mux_decoder = MuxGridCodec()

    def encode_packet(self, text: str, seq: int = 0) -> bytes:
        if self.codec_name == "huffman":
            payload = self.huffman.encode(text)
            header = bytes([CODEC_ID_HUFFMAN, seq & 0xFF, 0])
            return header + payload
        else:
            payload, padding = self.mux.encode(text)
            header = bytes([CODEC_ID_MUX_GRID, seq & 0xFF, padding & 0x07])
            return header + payload

    def decode_packet(self, packet: bytes) -> tuple[str, int, int]:
        if len(packet) < 3:
            raise ValueError(f"Packet too short: {len(packet)} bytes")
        codec_id = packet[0]
        seq = packet[1]
        padding = packet[2]
        payload = packet[3:]
        if codec_id == CODEC_ID_HUFFMAN:
            decoded = self._huffman_decoder.decode(payload)
            return decoded, codec_id, seq
        elif codec_id == CODEC_ID_MUX_GRID:
            decoded = self._mux_decoder.decode(payload, padding)
            return decoded, codec_id, seq
        else:
            raise ValueError(f"Unknown Codec ID: 0x{codec_id:02X}")

    def codebook_coverage(self, text: str) -> dict:
        if self.codec_name == "huffman":
            return self.huffman.codebook_coverage(text)
        else:
            return self.mux.codebook_coverage(text)

    def stats(self) -> dict:
        if self.codec_name == "huffman":
            s = self.huffman.stats()
            s["codec"] = "huffman"
            s["codec_id"] = CODEC_ID_HUFFMAN
            return s
        else:
            s = self.mux.stats()
            s["codec"] = "mux_grid"
            s["codec_id"] = CODEC_ID_MUX_GRID
            return s


# ==========================================
# EXPERIMENT D — LLM CONVERSATION + CODEC
# ==========================================

class ExperimentD:
    """
    Runs Experiment D: LLM conversation over LoRa with pre-tokenizer and
    optional LLM encode/decode codec.

    Config-driven:
      llm_codec: false → Phase 1 (pretokenizer only)
      llm_codec: true  → Phase 2 (pretokenizer + LLM encode/decode)
    """

    def __init__(self, config: dict):
        self.cfg = config
        self.interface = None

        # Node identity
        self.my_node_num = None
        self.my_node_id = None
        self.my_node_name = None
        self.peer_id = None
        self.role = None  # "A" or "B"

        # LLM config
        self.model = config.get("model", "gemma3:latest")
        self.system_prompt = config.get("conversation_seed", "")
        self.messages_per_node = config.get("messages_per_node", 10)
        self.timeout_s = config.get("timeout_s", 45)

        # Phase control
        self.use_pretokenizer = config.get("pretokenizer", True)
        self.use_llm_codec = config.get("llm_codec", False)
        self.fallback_threshold = config.get("fallback_threshold", 0.70)

        # Load codebook words for hit rate checking
        self.codebook_words = get_codebook_words()

        # Phase label for logging
        if self.use_llm_codec:
            self.phase_label = "Phase 2 (LLM Codec)"
        else:
            self.phase_label = "Phase 1 (Pre-Tokenizer)"

        # Synchronization
        self.msg_event = threading.Event()
        self.last_received_data = None
        self.last_received_packet = None
        self.trigger_data_is_step1 = False

        # Run results
        self.runs = {}  # codec_name -> list of result dicts
        self.transcripts = {}  # codec_name -> list of transcript entries

        # State
        self.state = "INIT"
        self.seq_counter = 0
        self.active_codec = None  # current CodecWrapper

    # ── Connection ──

    def connect(self) -> bool:
        port = self.cfg.get("port", "auto")
        dev_path = None if port == "auto" else port

        print(f"\n{'=' * 65}")
        print(f"  EXPERIMENT D — {self.phase_label}")
        print(f"  CyberMesh / Liberty Mesh — v{VERSION}")
        print(f"  Model: {self.model}  |  Messages/node: {self.messages_per_node}")
        print(f"  Port: {port}  |  Timeout: {self.timeout_s}s")
        print(f"  Pretokenizer: {'ON' if self.use_pretokenizer else 'OFF'}  |  LLM Codec: {'ON' if self.use_llm_codec else 'OFF'}")
        print(f"{'=' * 65}\n")

        pub.subscribe(self._on_receive, "meshtastic.receive")

        try:
            if dev_path:
                self.interface = meshtastic.serial_interface.SerialInterface(devPath=dev_path)
            else:
                self.interface = meshtastic.serial_interface.SerialInterface()
        except Exception as e:
            log(f"Could not connect to Meshtastic: {e}", "ERROR")
            return False

        time.sleep(2)

        self.my_node_num = self.interface.myInfo.my_node_num
        self.my_node_id = f"!{self.my_node_num:08x}"
        self.my_node_name = self._get_node_name(self.my_node_num)

        log(f"Node: {self.my_node_name} ({self.my_node_id})")
        log(f"Waiting for 'Hi' trigger DM...")
        self.state = "LISTENING"
        return True

    def _get_node_name(self, node_num: int) -> str:
        if self.interface and self.interface.nodes:
            for node in self.interface.nodes.values():
                if node.get("num") == node_num:
                    return node.get("user", {}).get("longName", f"!{node_num:08x}")
        return f"!{node_num:08x}"

    def _is_my_packet(self, packet: dict) -> bool:
        sender = packet.get("fromId", "")
        if not sender:
            return False
        try:
            sender_num = int(sender.replace("!", ""), 16) if sender.startswith("!") else None
            return sender_num == self.my_node_num
        except ValueError:
            return False

    # ── Packet handler ──

    def _on_receive(self, packet, interface):
        if self._is_my_packet(packet):
            return

        decoded = packet.get("decoded", {})
        portnum = decoded.get("portnum", "")
        sender = packet.get("fromId", "unknown")

        # Text trigger
        if self.state == "LISTENING" and portnum == "TEXT_MESSAGE_APP":
            text = decoded.get("text", "")
            trigger = self.cfg.get("trigger_word", "Hi")
            if text.strip() == trigger:
                log(f"TRIGGER received from {sender}: \"{text}\"")
                self.peer_id = sender
                self.role = "B"
                self.state = "TRIGGERED"
                self.msg_event.set()
                return

        # Compressed data on PRIVATE_APP
        pn_match = (portnum == "PRIVATE_APP" or portnum == "256")
        if not pn_match:
            raw_pn = decoded.get("portnum")
            if isinstance(raw_pn, int) and raw_pn == 256:
                pn_match = True

        if pn_match:
            raw_data = decoded.get("payload", b"")
            if isinstance(raw_data, str):
                raw_data = raw_data.encode("latin-1")

            if self.state == "LISTENING":
                log(f"First compressed message from {sender} — entering as Role A")
                self.peer_id = sender
                self.role = "A"
                self.state = "TRIGGERED"
                self.trigger_data_is_step1 = True

            self.last_received_data = raw_data
            self.last_received_packet = packet
            self.msg_event.set()

    # ── Send / Receive ──

    def _send_message(self, text: str, step: int, natural_text: str = None,
                      encode_ms: float = None, fallback: bool = False) -> dict:
        """
        Paginate, compress, and send a message. Returns result dict.

        Args:
            text: The text to encode and send (may be LLM-encoded or raw).
            step: Message step number.
            natural_text: Original natural text before LLM encode (Phase 2 only).
            encode_ms: LLM encode inference time (Phase 2 only).
            fallback: Whether LLM encode was skipped due to low hit rate.
        """
        pages = paginate(text, max_chars=200)
        total_comp = 0
        raw_bytes = len(text.encode("utf-8"))

        coverage = self.active_codec.codebook_coverage(text)
        hit_pct = coverage["coverage"]
        esc_count = len(coverage["missing"])

        for i, page in enumerate(pages):
            self.seq_counter = (self.seq_counter + 1) & 0xFF
            packet = self.active_codec.encode_packet(page, seq=self.seq_counter)
            total_comp += len(packet)

            try:
                self.interface.sendData(
                    packet,
                    destinationId=self.peer_id,
                    portNum=256,
                    wantAck=True,
                )
            except Exception as e:
                log(f"TX Step {step}: SEND ERROR: {e}", "ERROR")
                return {
                    "step": step, "direction": f"{'B→A' if self.role == 'B' else 'A→B'}",
                    "original": text, "natural": natural_text, "encoded": text if natural_text else None,
                    "decoded_by_llm": None,
                    "raw_bytes": raw_bytes, "comp_bytes": total_comp,
                    "ratio": 0, "roundtrip": False, "error": str(e),
                    "rssi": None, "snr": None,
                    "gen_ms": None, "enc_ms": encode_ms, "dec_ms": None,
                    "tokens": None, "pages": len(pages), "hit_pct": hit_pct,
                    "esc_count": esc_count, "fallback": fallback,
                }

            if len(pages) > 1 and i < len(pages) - 1:
                time.sleep(1.5)  # inter-page delay

        ratio = raw_bytes / total_comp if total_comp else 0

        # Build log message
        fb_tag = " [FALLBACK]" if fallback else ""
        if natural_text:
            log(f"TX Step {step}: NATURAL=\"{natural_text[:50]}\" → ENCODED=\"{text[:50]}\" "
                f"({raw_bytes}B → {total_comp}B, {ratio:.2f}:1, {hit_pct:.0f}% hit){fb_tag}")
        else:
            log(f"TX Step {step}: \"{text[:60]}\" ({raw_bytes}B → {total_comp}B, {ratio:.2f}:1, "
                f"{len(pages)} pg, {hit_pct:.0f}% hit){fb_tag}")

        return {
            "step": step, "direction": f"{'B→A' if self.role == 'B' else 'A→B'}",
            "original": text, "natural": natural_text, "encoded": text if natural_text else None,
            "decoded_by_llm": None,
            "raw_bytes": raw_bytes, "comp_bytes": total_comp,
            "ratio": ratio, "roundtrip": None, "error": None,
            "rssi": None, "snr": None,
            "gen_ms": None, "enc_ms": encode_ms, "dec_ms": None,
            "tokens": None, "pages": len(pages), "hit_pct": hit_pct,
            "esc_count": esc_count, "fallback": fallback,
        }

    def _receive_message(self, step: int, pre_loaded: bool = False) -> dict:
        """Wait for compressed message(s), decompress, reassemble. Returns result dict."""
        if pre_loaded and self.last_received_data is not None:
            log(f"RX Step {step}: pre-loaded from trigger")
            got_it = True
        else:
            self.msg_event.clear()
            self.last_received_data = None
            self.last_received_packet = None
            log(f"RX Step {step}: waiting (timeout {self.timeout_s}s)...")
            got_it = self.msg_event.wait(timeout=self.timeout_s)

        if not got_it or self.last_received_data is None:
            log(f"RX Step {step}: TIMEOUT after {self.timeout_s}s", "WARN")
            return {
                "step": step, "direction": f"{'A→B' if self.role == 'B' else 'B→A'}",
                "original": None, "natural": None, "encoded": None, "decoded_by_llm": None,
                "raw_bytes": None, "comp_bytes": None,
                "ratio": None, "roundtrip": False, "error": f"Timeout {self.timeout_s}s",
                "rssi": None, "snr": None,
                "gen_ms": None, "enc_ms": None, "dec_ms": None,
                "tokens": None, "pages": 0, "hit_pct": None,
                "esc_count": None, "fallback": False,
            }

        data = self.last_received_data
        pkt = self.last_received_packet or {}
        comp_bytes = len(data)

        try:
            decoded, codec_id, seq = self.active_codec.decode_packet(data)
        except Exception as e:
            log(f"RX Step {step}: DECODE ERROR: {e}", "ERROR")
            decoded = f"DECODE_ERROR: {e}"

        rssi = pkt.get("rxRssi", pkt.get("rssi"))
        snr = pkt.get("rxSnr", pkt.get("snr"))

        # Phase 2: LLM decode the codebook-constrained text to natural English
        dec_ms = None
        decoded_by_llm = None
        if self.use_llm_codec and not decoded.startswith("DECODE_ERROR"):
            try:
                decoded_by_llm, dec_ms = llm_decode(decoded, model=self.model)
                log(f"RX Step {step}: CODEC=\"{decoded[:40]}\" → LLM_DECODED=\"{decoded_by_llm[:40]}\" "
                    f"({comp_bytes}B, {dec_ms:.0f}ms, RSSI={rssi}, SNR={snr})")
            except Exception as e:
                log(f"RX Step {step}: LLM DECODE ERROR: {e}", "ERROR")
                decoded_by_llm = decoded  # Fall back to raw decoded text
        else:
            log(f"RX Step {step}: \"{decoded[:60]}\" ({comp_bytes}B, RSSI={rssi}, SNR={snr})")

        return {
            "step": step, "direction": f"{'A→B' if self.role == 'B' else 'B→A'}",
            "original": None, "natural": None, "encoded": decoded,
            "decoded_by_llm": decoded_by_llm,
            "raw_bytes": None, "comp_bytes": comp_bytes,
            "ratio": None, "roundtrip": True, "error": None,
            "rssi": rssi, "snr": snr,
            "gen_ms": None, "enc_ms": None, "dec_ms": dec_ms,
            "tokens": None, "pages": 1, "hit_pct": None,
            "esc_count": None, "fallback": False,
        }

    # ── Single run (one codec) ──

    def _run_conversation(self, codec_name: str) -> tuple[list[dict], list[dict]]:
        """
        Run a full 20-message conversation with the given codec.
        Returns (results, transcript).
        """
        self.active_codec = CodecWrapper(codec_name)
        stats = self.active_codec.stats()
        total_messages = self.messages_per_node * 2
        conversation_history = []
        results = []
        transcript = []

        log(f"=== RUN: {codec_name.upper()} === Codec ID: 0x{stats.get('codec_id', 0):02X}, "
            f"Codebook: {stats.get('codebook_size', '?')} words, {total_messages} messages, "
            f"Pretokenizer: {'ON' if self.use_pretokenizer else 'OFF'}, "
            f"LLM Codec: {'ON' if self.use_llm_codec else 'OFF'}")

        for step in range(1, total_messages + 1):
            is_my_tx = self._is_my_tx_step(step)

            if is_my_tx:
                # ── SENDER PIPELINE ──

                # Call 1: Generate natural response
                natural_text, gen_ms, tokens = generate_response(
                    self.model, self.system_prompt, conversation_history
                )
                log(f"LLM generated ({gen_ms:.0f}ms, {tokens} tokens): \"{natural_text[:80]}\"")

                # Phase 2: Call 2: LLM encode (rewrite to codebook words)
                encode_ms = None
                fallback = False
                if self.use_llm_codec:
                    try:
                        encoded_text, encode_ms = llm_encode(natural_text, model=self.model)
                        log(f"LLM encoded ({encode_ms:.0f}ms): \"{encoded_text[:80]}\"")

                        # Check hit rate — fallback if below threshold
                        if self.use_pretokenizer:
                            check_text = normalize(encoded_text)
                        else:
                            check_text = encoded_text
                        hit_rate = compute_hit_rate(check_text, self.codebook_words)

                        if hit_rate < self.fallback_threshold:
                            log(f"WARN: LLM encode hit rate {hit_rate:.0%}, "
                                f"below threshold {self.fallback_threshold:.0%} — falling back to raw",
                                "WARN")
                            fallback = True
                            text_to_send = natural_text
                        else:
                            text_to_send = encoded_text
                    except Exception as e:
                        log(f"LLM encode error: {e} — falling back to raw", "WARN")
                        fallback = True
                        text_to_send = natural_text
                else:
                    text_to_send = natural_text

                # Pre-tokenizer normalization (always for Experiment D)
                if self.use_pretokenizer:
                    text_to_send = normalize(text_to_send)

                # Send
                result = self._send_message(
                    text_to_send, step,
                    natural_text=natural_text if self.use_llm_codec else None,
                    encode_ms=encode_ms,
                    fallback=fallback,
                )
                result["gen_ms"] = gen_ms
                result["tokens"] = tokens
                results.append(result)

                # Add to conversation history (use natural text for context quality)
                conversation_history.append({"sent": True, "text": natural_text})
                transcript.append({
                    "step": step, "sender": f"Role {self.role}",
                    "natural": natural_text,
                    "encoded": text_to_send if self.use_llm_codec else None,
                    "decoded": None,
                    "fallback": fallback,
                })

            else:
                # ── RECEIVER PIPELINE ──
                pre_loaded = (step == 1 and self.role == "A" and self.trigger_data_is_step1)
                result = self._receive_message(step, pre_loaded=pre_loaded)
                results.append(result)

                if result.get("decoded_by_llm") and not str(result["decoded_by_llm"]).startswith("DECODE_ERROR"):
                    # Phase 2: Use LLM-expanded text for conversation history
                    history_text = result["decoded_by_llm"]
                elif result.get("encoded") and not str(result["encoded"]).startswith("DECODE_ERROR"):
                    # Phase 1 or fallback: Use raw decoded text
                    history_text = result["encoded"]
                else:
                    history_text = None

                if history_text:
                    conversation_history.append({"sent": False, "text": history_text})
                    transcript.append({
                        "step": step, "sender": f"Role {'B' if self.role == 'A' else 'A'}",
                        "natural": None,
                        "encoded": result.get("encoded"),
                        "decoded": result.get("decoded_by_llm"),
                        "fallback": False,
                    })
                else:
                    transcript.append({
                        "step": step, "sender": f"Role {'B' if self.role == 'A' else 'A'}",
                        "natural": None, "encoded": None,
                        "decoded": result.get("error", "MISSING"),
                        "fallback": False,
                    })

        return results, transcript

    def _is_my_tx_step(self, step: int) -> bool:
        """Role B sends on odd steps (1,3,5,...), Role A sends on even steps (2,4,6,...)."""
        if self.role == "B":
            return step % 2 == 1
        else:
            return step % 2 == 0

    # ── Full experiment ──

    def run_experiment(self):
        """Run both codec runs in sequence, then generate comparison."""
        # Warmup LLM
        warmup_model(self.model)

        # Wait for trigger
        log("Waiting for trigger...")
        while self.state == "LISTENING":
            time.sleep(0.5)

        if self.state != "TRIGGERED":
            log(f"Unexpected state: {self.state}", "ERROR")
            return

        self.state = "RUNNING"
        log(f"Role assigned: {self.role}  |  Peer: {self.peer_id}")

        # === Run 1: MUX Grid ===
        log("=" * 50)
        log(f"RUN 1 OF 2: MUX GRID CODEC — {self.phase_label}")
        log("=" * 50)
        mux_results, mux_transcript = self._run_conversation("mux_grid")
        self.runs["mux_grid"] = mux_results
        self.transcripts["mux_grid"] = mux_transcript

        # Brief pause between runs
        log("Run 1 complete. Pausing 5s before Run 2...")
        time.sleep(5)

        # Reset sync state for Run 2
        self.msg_event.clear()
        self.last_received_data = None
        self.last_received_packet = None
        self.trigger_data_is_step1 = False
        self.seq_counter = 0

        # === Run 2: Huffman ===
        log("=" * 50)
        log(f"RUN 2 OF 2: HUFFMAN CODEC (4K) — {self.phase_label}")
        log("=" * 50)

        if self.role == "B":
            huff_results, huff_transcript = self._run_conversation("huffman")
        else:
            log("Role A: waiting for Role B to start Run 2...")
            self.msg_event.clear()
            self.last_received_data = None
            self.last_received_packet = None
            self.trigger_data_is_step1 = True
            self.msg_event.wait(timeout=self.timeout_s)
            huff_results, huff_transcript = self._run_conversation("huffman")

        self.runs["huffman"] = huff_results
        self.transcripts["huffman"] = huff_transcript

        self.state = "COMPLETE"

        # Print summaries and write logs
        self._print_run_summary("mux_grid", mux_results)
        self._print_run_summary("huffman", huff_results)
        self._print_comparison()
        self._write_logs()

    # ── Output ──

    def _print_run_summary(self, codec_name: str, results: list[dict]):
        label = "MUX Grid" if codec_name == "mux_grid" else "Huffman (4K)"
        print(f"\n{'=' * 70}")
        print(f"  {label} — Run Summary (Role {self.role}) — {self.phase_label}")
        print(f"{'=' * 70}")

        if self.use_llm_codec:
            hdr = (f"  {'#':<3} {'Dir':<5} {'Raw':>4} {'Cmp':>4} {'Ratio':>6} "
                   f"{'Gen':>6} {'Enc':>6} {'Dec':>6} {'Pg':>3} {'Hit%':>5} {'ESC':>4} {'FB':>3} "
                   f"{'RSSI':>5} {'SNR':>4}  Message")
            print(hdr)
            sep = (f"  {'─'*3} {'─'*5} {'─'*4} {'─'*4} {'─'*6} "
                   f"{'─'*6} {'─'*6} {'─'*6} {'─'*3} {'─'*5} {'─'*4} {'─'*3} "
                   f"{'─'*5} {'─'*4}  {'─'*35}")
        else:
            hdr = (f"  {'#':<3} {'Dir':<5} {'Raw':>4} {'Cmp':>4} {'Ratio':>6} "
                   f"{'Inf(ms)':>8} {'Pg':>3} {'Hit%':>5} {'ESC':>4} "
                   f"{'RSSI':>5} {'SNR':>4}  Message")
            print(hdr)
            sep = (f"  {'─'*3} {'─'*5} {'─'*4} {'─'*4} {'─'*6} "
                   f"{'─'*8} {'─'*3} {'─'*5} {'─'*4} "
                   f"{'─'*5} {'─'*4}  {'─'*40}")
        print(sep)

        for r in results:
            s = r["step"]
            d = r.get("direction", "?")
            raw = r.get("raw_bytes")
            comp = r.get("comp_bytes")
            ratio = r.get("ratio")
            pg = r.get("pages", 0)
            hit = r.get("hit_pct")
            esc = r.get("esc_count")
            rssi = r.get("rssi")
            snr = r.get("snr")
            msg = (r.get("natural") or r.get("original") or r.get("encoded") or
                   r.get("decoded_by_llm") or "")[:35]

            raw_s = f"{raw:>4}" if raw else "   —"
            comp_s = f"{comp:>4}" if comp else "   —"
            ratio_s = f"{ratio:>6.2f}" if ratio else "     —"
            pg_s = f"{pg:>3}" if pg else "  —"
            hit_s = f"{hit:>4.0f}%" if hit is not None else "    —"
            esc_s = f"{esc:>4}" if esc is not None else "   —"
            rssi_s = f"{rssi:>5}" if rssi is not None else "    —"
            snr_s = f"{snr:>4}" if snr is not None else "   —"

            if self.use_llm_codec:
                gen = r.get("gen_ms")
                enc = r.get("enc_ms")
                dec = r.get("dec_ms")
                fb = "Y" if r.get("fallback") else "N"
                gen_s = f"{gen:>5.0f}" if gen else "    —"
                enc_s = f"{enc:>5.0f}" if enc else "    —"
                dec_s = f"{dec:>5.0f}" if dec else "    —"
                print(f"  {s:<3} {d:<5} {raw_s} {comp_s} {ratio_s} "
                      f"{gen_s} {enc_s} {dec_s} {pg_s} {hit_s} {esc_s}   {fb} "
                      f"{rssi_s} {snr_s}  {msg}")
            else:
                inf = r.get("gen_ms")
                inf_s = f"{inf:>7.0f}" if inf else "      —"
                print(f"  {s:<3} {d:<5} {raw_s} {comp_s} {ratio_s} {inf_s} {pg_s} "
                      f"{hit_s} {esc_s} {rssi_s} {snr_s}  {msg}")

    def _print_comparison(self):
        """Print side-by-side comparison of both runs."""
        print(f"\n{'=' * 70}")
        print(f"  EXPERIMENT D — {self.phase_label} — Combined Results")
        print(f"{'=' * 70}")

        for codec_name, label in [("mux_grid", "MUX Grid"), ("huffman", "Huffman (4K)")]:
            results = self.runs.get(codec_name, [])
            tx_results = [r for r in results if r.get("raw_bytes") is not None]
            rx_results = [r for r in results if r.get("comp_bytes") is not None and r.get("raw_bytes") is None]

            total_raw = sum(r["raw_bytes"] for r in tx_results if r["raw_bytes"])
            total_comp = sum(r["comp_bytes"] for r in tx_results if r["comp_bytes"])
            ratio = total_raw / total_comp if total_comp else 0

            hit_pcts = [r["hit_pct"] for r in tx_results if r.get("hit_pct") is not None]
            avg_hit = sum(hit_pcts) / len(hit_pcts) if hit_pcts else 0

            esc_counts = [r["esc_count"] for r in tx_results if r.get("esc_count") is not None]
            avg_esc = sum(esc_counts) / len(esc_counts) if esc_counts else 0

            gen_times = [r["gen_ms"] for r in tx_results if r.get("gen_ms")]
            avg_gen = sum(gen_times) / len(gen_times) if gen_times else 0

            enc_times = [r["enc_ms"] for r in tx_results if r.get("enc_ms")]
            avg_enc = sum(enc_times) / len(enc_times) if enc_times else 0

            dec_times = [r["dec_ms"] for r in rx_results if r.get("dec_ms")]
            avg_dec = sum(dec_times) / len(dec_times) if dec_times else 0

            pages_gt1 = sum(1 for r in tx_results if (r.get("pages") or 0) > 1)
            fallbacks = sum(1 for r in tx_results if r.get("fallback"))

            msgs_sent = len(tx_results)
            msgs_received = len(rx_results)
            errors = sum(1 for r in results if r.get("error"))

            print(f"\n  --- {label} ---")
            print(f"  Messages sent:           {msgs_sent}")
            print(f"  Messages received:       {msgs_received}")
            print(f"  Errors/Timeouts:         {errors}")
            print(f"  Total raw bytes (TX):    {total_raw}")
            print(f"  Total compressed (TX):   {total_comp}")
            print(f"  Aggregate ratio:         {ratio:.2f}:1")
            print(f"  Avg codebook hit rate:   {avg_hit:.1f}%")
            print(f"  Avg ESC count per msg:   {avg_esc:.1f}")
            print(f"  Avg LLM generate time:   {avg_gen:.0f}ms")
            if self.use_llm_codec:
                print(f"  Avg LLM encode time:     {avg_enc:.0f}ms")
                print(f"  Avg LLM decode time:     {avg_dec:.0f}ms")
                print(f"  Fallback events:         {fallbacks}/{msgs_sent}")
            print(f"  Pages > 1 count:         {pages_gt1}")

    def _write_logs(self):
        """Write all experiment logs."""
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        phase_tag = "phase2" if self.use_llm_codec else "phase1"

        for codec_name in ["mux_grid", "huffman"]:
            label = "MUX Grid" if codec_name == "mux_grid" else "Huffman (4K)"
            results = self.runs.get(codec_name, [])
            transcript = self.transcripts.get(codec_name, [])

            filename = f"experiment-d-{phase_tag}-{codec_name.replace('_','-')}-log_{ts}.md"
            filepath = os.path.join(logs_dir, filename)

            lines = [
                "---",
                f'title: "Experiment D — {self.phase_label} — {label} — Run Log"',
                f"date: {datetime.now(timezone.utc).isoformat()}",
                f"version: {VERSION}",
                f"phase: {phase_tag}",
                f"codec: {codec_name}",
                f"model: {self.model}",
                f"role: {self.role}",
                f'node: "{self.my_node_id}"',
                f'peer: "{self.peer_id}"',
                f"messages_per_node: {self.messages_per_node}",
                f"pretokenizer: {self.use_pretokenizer}",
                f"llm_codec: {self.use_llm_codec}",
                f"fallback_threshold: {self.fallback_threshold}",
                "---",
                "",
                f"# Experiment D — {self.phase_label} — {label} — Results",
                "",
                "## Per-Message Metrics",
                "",
            ]

            if self.use_llm_codec:
                lines.extend([
                    "| # | Dir | Raw | Cmp | Ratio | Gen(ms) | Enc(ms) | Dec(ms) | Pg | Hit% | ESC | FB | RSSI | SNR | Natural | Encoded |",
                    "|---|-----|-----|-----|-------|---------|---------|---------|----|------|-----|----|----- |-----|---------|---------|",
                ])
            else:
                lines.extend([
                    "| # | Dir | Raw | Cmp | Ratio | Inf(ms) | Tokens | Pg | Hit% | ESC | RSSI | SNR | Message |",
                    "|---|-----|-----|-----|-------|---------|--------|----|------|-----|------|-----|---------|",
                ])

            for r in results:
                s = r["step"]
                d = r.get("direction", "?")
                raw = r.get("raw_bytes", "—")
                comp = r.get("comp_bytes", "—")
                ratio = f"{r['ratio']:.2f}" if r.get("ratio") else "—"
                pg = r.get("pages", "—")
                hit = f"{r['hit_pct']:.0f}%" if r.get("hit_pct") is not None else "—"
                esc = r.get("esc_count", "—")
                rssi = r.get("rssi", "—")
                snr = r.get("snr", "—")

                if self.use_llm_codec:
                    gen = f"{r['gen_ms']:.0f}" if r.get("gen_ms") else "—"
                    enc = f"{r['enc_ms']:.0f}" if r.get("enc_ms") else "—"
                    dec = f"{r['dec_ms']:.0f}" if r.get("dec_ms") else "—"
                    fb = "Y" if r.get("fallback") else "N"
                    nat = (r.get("natural") or "—")[:50]
                    ecd = (r.get("encoded") or r.get("original") or "—")[:50]
                    lines.append(f"| {s} | {d} | {raw} | {comp} | {ratio} | {gen} | {enc} | {dec} | "
                                 f"{pg} | {hit} | {esc} | {fb} | {rssi} | {snr} | {nat} | {ecd} |")
                else:
                    gen = f"{r['gen_ms']:.0f}" if r.get("gen_ms") else "—"
                    tok = r.get("tokens", "—")
                    msg = (r.get("original") or r.get("encoded") or r.get("decoded_by_llm") or "")[:60]
                    lines.append(f"| {s} | {d} | {raw} | {comp} | {ratio} | {gen} | {tok} | "
                                 f"{pg} | {hit} | {esc} | {rssi} | {snr} | {msg} |")

            # Transcript
            lines.extend(["", "## Full Conversation Transcript", ""])
            if self.use_llm_codec:
                lines.extend([
                    "| # | Sender | Natural | Encoded/Decoded |",
                    "|---|--------|---------|-----------------|",
                ])
                for t in transcript:
                    nat = (t.get("natural") or "—")[:60]
                    ecd = (t.get("encoded") or t.get("decoded") or "—")[:60]
                    lines.append(f"| {t['step']} | {t['sender']} | {nat} | {ecd} |")
            else:
                lines.extend([
                    "| # | Sender | Text |",
                    "|---|--------|------|",
                ])
                for t in transcript:
                    text = t.get("natural") or t.get("encoded") or t.get("decoded") or "—"
                    lines.append(f"| {t['step']} | {t['sender']} | {text} |")

            lines.append("")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            log(f"Log written: {filepath}")

        # Comparison log
        comp_file = os.path.join(logs_dir, f"experiment-d-{phase_tag}-comparison_{ts}.md")
        self._write_comparison_log(comp_file)
        log(f"Comparison written: {comp_file}")

        # Structured JSON log
        json_file = os.path.join(logs_dir, f"experiment-d-{phase_tag}-data_{ts}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "experiment": "D",
                "phase": phase_tag,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": self.my_node_id,
                "peer": self.peer_id,
                "role": self.role,
                "model": self.model,
                "pretokenizer": self.use_pretokenizer,
                "llm_codec": self.use_llm_codec,
                "fallback_threshold": self.fallback_threshold,
                "runs": {k: v for k, v in self.runs.items()},
                "transcripts": {k: v for k, v in self.transcripts.items()},
                "log_entries": LOG_ENTRIES,
            }, f, indent=2, default=str)
        log(f"JSON data written: {json_file}")

    def _write_comparison_log(self, filepath: str):
        phase_tag = "Phase 2 (LLM Codec)" if self.use_llm_codec else "Phase 1 (Pre-Tokenizer)"
        lines = [
            "---",
            f'title: "Experiment D — {phase_tag} — Combined Results"',
            f"date: {datetime.now(timezone.utc).isoformat()}",
            f"version: {VERSION}",
            "---",
            "",
            f"# Experiment D — {phase_tag} — Combined Results",
            "",
            "| Metric | Huffman (4K) | MUX Grid |",
            "|--------|-------------|----------|",
        ]

        metrics = {}
        for codec_name in ["huffman", "mux_grid"]:
            results = self.runs.get(codec_name, [])
            tx_results = [r for r in results if r.get("raw_bytes") is not None]
            total_raw = sum(r["raw_bytes"] for r in tx_results if r["raw_bytes"])
            total_comp = sum(r["comp_bytes"] for r in tx_results if r["comp_bytes"])
            ratio = f"{total_raw / total_comp:.2f}:1" if total_comp else "—"
            hit_pcts = [r["hit_pct"] for r in tx_results if r.get("hit_pct") is not None]
            avg_hit = f"{sum(hit_pcts) / len(hit_pcts):.1f}%" if hit_pcts else "—"
            esc_counts = [r["esc_count"] for r in tx_results if r.get("esc_count") is not None]
            avg_esc = f"{sum(esc_counts) / len(esc_counts):.1f}" if esc_counts else "—"
            gen_times = [r["gen_ms"] for r in tx_results if r.get("gen_ms")]
            avg_gen = f"{sum(gen_times) / len(gen_times):.0f}ms" if gen_times else "—"
            pages_gt1 = sum(1 for r in tx_results if (r.get("pages") or 0) > 1)
            fallbacks = sum(1 for r in tx_results if r.get("fallback"))

            metrics[codec_name] = {
                "sent": len(tx_results), "ratio": ratio, "hit": avg_hit,
                "esc": avg_esc, "gen": avg_gen, "pages": pages_gt1,
                "fallbacks": fallbacks,
            }

        h, m = metrics["huffman"], metrics["mux_grid"]
        lines.extend([
            f"| Messages sent | {h['sent']} | {m['sent']} |",
            f"| Aggregate ratio | {h['ratio']} | {m['ratio']} |",
            f"| Avg codebook hit rate | {h['hit']} | {m['hit']} |",
            f"| Avg ESC count per msg | {h['esc']} | {m['esc']} |",
            f"| Avg LLM generate time | {h['gen']} | {m['gen']} |",
            f"| Pages > 1 count | {h['pages']} | {m['pages']} |",
        ])
        if self.use_llm_codec:
            lines.append(f"| Fallback events | {h['fallbacks']}/{h['sent']} | {m['fallbacks']}/{m['sent']} |")

        lines.append("")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # ── Main loop ──

    def run(self):
        if not self.connect():
            return

        try:
            self.run_experiment()
            print(f"\n{'=' * 65}")
            print(f"  EXPERIMENT D — {self.phase_label} — COMPLETE")
            print(f"  Check logs/ directory for full results.")
            print(f"{'=' * 65}\n")
        except KeyboardInterrupt:
            print("\n\n  Interrupted by user. Shutting down...")
        finally:
            if self.interface:
                self.interface.close()
            print("  Radio interface closed.\n")


# ==========================================
# ENTRY POINT
# ==========================================

def main():
    config = load_config()

    # Determine phase
    llm_codec = config.get("llm_codec", False)
    phase_label = "Phase 2 (LLM Codec)" if llm_codec else "Phase 1 (Pre-Tokenizer)"

    print("\n" + "─" * 65)
    print(f"  huffman_mesh_poc.py v{VERSION}")
    print(f"  Experiment D — {phase_label}")
    print(f"  CyberMesh / Liberty Mesh Project")
    print(f"  Author: Mark Snow, Jr. — Mindtech")
    print("─" * 65)

    exp = ExperimentD(config)
    exp.run()


if __name__ == "__main__":
    main()
