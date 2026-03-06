#!/usr/bin/env python3
"""
huffman_mesh_poc.py — CyberMesh v7.1 "Smart Router" Harness
=============================================================
Experiment G: Smart Router — Huffman/MUX + Keyword/Strict routing over LoRa.

Architecture:
  - config.yaml       — full v7.1 config
  - llm_client.py     — LLMClient (generate, classify, warmup)
  - huffman_codec.py  — MeshHuffmanCodec (4k | 333k codebook)
  - mux_codec.py      — MuxGridCodec     (4k | 333k | cube96 codebook)
  - keyword_codec.py  — KeywordCodec (extract, reconstruct via LLM)
  - smart_router.py   — SmartRouter (route: strict / lossy / paginate)
  - packet.py         — CyberMeshPacket (encode/decode, codec IDs 0x01-0x06)
  - paginator.py      — paginate_strict(), reassemble_strict()
  - context_manager.py — ContextManager (per-sender sliding-window history)
  - pretokenizer.py   — normalize() (always applied before encoding)

Experiment matrix (runs sequentially):
  Run 1: huffman  + 333k   + keyword
  Run 2: mux_grid + 333k   + keyword
  Run 3: huffman  + 333k   + strict_only
  Run 4: mux_grid + 333k   + strict_only
  Run 5: huffman  + 333k   + lossy-forced
  Run 6: mux_grid + cube96 + keyword
  Run 7: mux_grid + cube96 + strict_only

!ping interrupt: handled before pipeline — replies "PONG", never touches
context or codec pipeline.

Transport: sendData() with PRIVATE_APP portNum 256 (raw bytes) for compressed
payloads; TEXT_MESSAGE_APP for control messages (!ping / PONG).

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os
import sys
import json
import math
import time
import queue
import logging
import threading
from datetime import datetime, timezone

# ── Third-party ───────────────────────────────────────────────────────────────
import yaml
from pubsub import pub

# ── Meshtastic (optional — falls back to loopback) ────────────────────────────
try:
    import meshtastic
    import meshtastic.serial_interface
    MESHTASTIC_AVAILABLE = True
except ImportError:
    MESHTASTIC_AVAILABLE = False

# ── Local modules ─────────────────────────────────────────────────────────────
from llm_client import LLMClient
from huffman_codec import MeshHuffmanCodec
from mux_codec import MuxGridCodec
from keyword_codec import KeywordCodec
from smart_router import SmartRouter
from packet import CyberMeshPacket
from paginator import paginate_strict, reassemble_strict
from context_manager import ContextManager
from pretokenizer import normalize

# =============================================================================
# VERSION
# =============================================================================

VERSION  = "7.0"
CODENAME = "Smart Router"

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("harness")

# In-memory structured log entries (for markdown export)
LOG_ENTRIES: list[dict] = []
LOG_LOCK = threading.Lock()


def log(msg: str, level: str = "INFO") -> None:
    """Timestamped console log with structured storage."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {"ts": ts, "level": level, "msg": msg}
    with LOG_LOCK:
        LOG_ENTRIES.append(entry)
    prefix = {"INFO": "  ", "WARN": "  W", "ERROR": "  E", "DEBUG": "  D"}.get(level, "  ")
    print(f"{prefix} [{ts}] {msg}", flush=True)


# =============================================================================
# CODEBOOK GUARD
# =============================================================================

def ensure_codebooks() -> None:
    """
    Check that codebook .bin files exist. If missing, attempt to
    build them by running the build scripts. If the build fails or the
    source CSV is missing, exit with a clear message.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    codebooks_dir = os.path.join(base, "codebooks")
    huff_bin = os.path.join(codebooks_dir, "huffman_333k.bin")
    mux_bin  = os.path.join(codebooks_dir, "mux_333k.bin")
    cube_bin = os.path.join(codebooks_dir, "mux_cube96.bin")

    missing = []
    if not os.path.exists(huff_bin):
        missing.append(("huffman_333k.bin", "build_huffman_codebook_333k.py"))
    if not os.path.exists(mux_bin):
        missing.append(("mux_333k.bin", "build_mux_codebook_333k.py"))
    if not os.path.exists(cube_bin):
        missing.append(("mux_cube96.bin", "build_mux_cube96.py"))

    if not missing:
        return  # All good

    # Check source CSV exists
    src_csv = os.path.join(base, "english_unigram_freq.csv")
    if not os.path.exists(src_csv):
        log("FATAL: codebook .bin files missing and source CSV "
            f"(english_unigram_freq.csv) not found in {base}", "ERROR")
        log("Download the Kaggle unigram frequency dataset first.", "ERROR")
        sys.exit(1)

    # Auto-build missing codebooks
    import subprocess
    for bin_name, script_name in missing:
        script_path = os.path.join(base, script_name)
        if not os.path.exists(script_path):
            log(f"FATAL: {bin_name} missing and build script {script_name} "
                "not found.", "ERROR")
            sys.exit(1)

        log(f"Building {bin_name} (first run)... this takes ~10s")
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=base, capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                log(f"Build script {script_name} failed:\n{result.stderr}",
                    "ERROR")
                sys.exit(1)
            log(f"Built {bin_name} successfully.")
        except subprocess.TimeoutExpired:
            log(f"Build script {script_name} timed out (120s).", "ERROR")
            sys.exit(1)
        except Exception as exc:
            log(f"Build script {script_name} error: {exc}", "ERROR")
            sys.exit(1)


# =============================================================================
# CONFIG LOADER
# =============================================================================

def load_config() -> dict:
    """Load config.yaml from the script directory."""
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"config.yaml not found at {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    log(f"Config loaded from {cfg_path}")
    return cfg


# =============================================================================
# STARTUP BANNER
# =============================================================================

def print_banner(cfg: dict) -> None:
    codec_cfg  = cfg.get("codec", {})
    lem_cfg    = cfg.get("lemonade", {})
    radio_cfg  = cfg.get("radio", {})
    exp_cfg    = cfg.get("experiment", {})
    test_cfg   = cfg.get("testing", {})

    width = 70
    print("\n" + "=" * width)
    print(f"  CyberMesh v{VERSION}  \"{CODENAME}\"")
    print(f"  Mindtech / Liberty Mesh — Experiment {exp_cfg.get('name', '?')}")
    print("─" * width)
    print(f"  Engine     : {codec_cfg.get('engine', '?')}  |  Codebook: {codec_cfg.get('codebook_size', '?')}")
    print(f"  Mode       : {codec_cfg.get('mode', '?')}")
    print(f"  Model      : {lem_cfg.get('model', '?')}  @  {lem_cfg.get('base_url', '?')}")
    print(f"  Radio port : {radio_cfg.get('port', 'auto')}")
    print(f"  Mock LLM   : {test_cfg.get('mock_llm', False)}")
    print(f"  Warmup     : {lem_cfg.get('warmup_on_start', True)}")
    print(f"  Msgs/node  : {exp_cfg.get('messages_per_node', 10)}")
    print("=" * width + "\n")


# =============================================================================
# CODEC FACTORY
# =============================================================================

def build_codec(engine: str, codebook_size: str):
    """
    Instantiate the correct codec based on config.codec.engine and
    config.codec.codebook_size.

    Returns: (codec_instance, engine_name)
    """
    engine = engine.lower()
    if engine == "huffman":
        codec = MeshHuffmanCodec(codebook_size=codebook_size)
        log(f"Codec: MeshHuffmanCodec ({codebook_size})")
    elif engine == "mux_grid":
        codec = MuxGridCodec(codebook_size=codebook_size)
        log(f"Codec: MuxGridCodec ({codebook_size})")
    else:
        raise ValueError(f"Unknown codec engine: {engine!r}")
    return codec, engine


# =============================================================================
# MESHTASTIC RADIO INTERFACE  (with loopback fallback)
# =============================================================================

class RadioInterface:
    """
    Wraps Meshtastic serial interface with a local loopback fallback.

    In loopback mode every sent packet is immediately placed on a receive
    queue so tests can run without hardware.
    """

    def __init__(self, port: str = "auto"):
        self.port = port
        self.interface = None
        self.my_node_num: int = 0
        self.my_node_id: str = "!00000000"
        self.my_node_name: str = "LocalNode"
        self._loopback = False
        self._loopback_queue: queue.Queue = queue.Queue()
        self._rx_callbacks: list = []
        self._lock = threading.Lock()

    def connect(self) -> bool:
        if not MESHTASTIC_AVAILABLE:
            log("Meshtastic not installed — using loopback mode", "WARN")
            self._loopback = True
            return True

        dev_path = None if self.port == "auto" else self.port
        pub.subscribe(self._on_meshtastic_receive, "meshtastic.receive")
        try:
            if dev_path:
                self.interface = meshtastic.serial_interface.SerialInterface(devPath=dev_path)
            else:
                self.interface = meshtastic.serial_interface.SerialInterface()
        except Exception as exc:
            log(f"Meshtastic connect failed: {exc} — using loopback mode", "WARN")
            self._loopback = True
            return True

        time.sleep(2)
        self.my_node_num  = self.interface.myInfo.my_node_num
        self.my_node_id   = f"!{self.my_node_num:08x}"
        self.my_node_name = self._get_node_name(self.my_node_num)
        log(f"Radio online: {self.my_node_name} ({self.my_node_id})")
        return True

    def _get_node_name(self, node_num: int) -> str:
        if self.interface and self.interface.nodes:
            for node in self.interface.nodes.values():
                if node.get("num") == node_num:
                    return node.get("user", {}).get("longName", f"!{node_num:08x}")
        return f"!{node_num:08x}"

    def register_rx_callback(self, cb) -> None:
        """Register a callback(raw_bytes, sender_id, rssi, snr, packet)."""
        self._rx_callbacks.append(cb)

    def _on_meshtastic_receive(self, packet, interface) -> None:
        """pubsub callback from Meshtastic library."""
        decoded  = packet.get("decoded", {})
        portnum  = decoded.get("portnum", "")
        sender   = packet.get("fromId", "unknown")

        # Ignore own packets
        try:
            sender_num = int(sender.replace("!", ""), 16) if sender.startswith("!") else None
            if sender_num == self.my_node_num:
                return
        except ValueError:
            pass

        pn_match = (portnum in ("PRIVATE_APP", "256") or
                    (isinstance(portnum, int) and portnum == 256))

        if pn_match:
            raw = decoded.get("payload", b"")
            if isinstance(raw, str):
                raw = raw.encode("latin-1")
            rssi = packet.get("rxRssi", packet.get("rssi"))
            snr  = packet.get("rxSnr",  packet.get("snr"))
            for cb in self._rx_callbacks:
                cb(raw, sender, rssi, snr, packet)

        # Text messages (for !ping detection)
        elif portnum == "TEXT_MESSAGE_APP":
            text = decoded.get("text", "")
            rssi = packet.get("rxRssi", packet.get("rssi"))
            snr  = packet.get("rxSnr",  packet.get("snr"))
            for cb in self._rx_callbacks:
                cb(text.encode("utf-8"), sender, rssi, snr, packet)

    def send_data(self, raw: bytes, dest_id: str,
                  port_num: int = 256, want_ack: bool = True) -> None:
        """Send raw bytes. In loopback mode queues immediately for RX."""
        if self._loopback:
            # Simulate receive (own echo) — useful for local testing
            self._loopback_queue.put(raw)
            return
        try:
            self.interface.sendData(raw, destinationId=dest_id,
                                    portNum=port_num, wantAck=want_ack)
        except Exception as exc:
            log(f"Radio TX error: {exc}", "ERROR")

    def send_text(self, text: str, dest_id: str) -> None:
        """Send plain text (used for PONG reply)."""
        if self._loopback:
            return
        try:
            self.interface.sendText(text, destinationId=dest_id)
        except Exception as exc:
            log(f"Radio text TX error: {exc}", "ERROR")

    def pop_loopback(self, timeout: float = 2.0) -> bytes | None:
        """Pop a loopback-queued packet (for mock receive during tests)."""
        try:
            return self._loopback_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        if self.interface:
            try:
                self.interface.close()
            except Exception:
                pass


# =============================================================================
# PAGE BUFFER  (for multi-page reassembly on RX)
# =============================================================================

class PageBuffer:
    """
    Thread-safe per-sender page accumulator.

    Accumulates packets until total_pages are received, then returns the
    reassembled payload.
    """

    def __init__(self):
        self._buffers: dict[str, dict] = {}  # sender_id -> {pages: dict, total: int}
        self._lock = threading.Lock()

    def add(self, sender_id: str, pkt: CyberMeshPacket, raw_pkt: bytes
            ) -> bytes | None:
        """
        Add a packet for sender_id.

        Returns reassembled payload bytes if all pages are present,
        otherwise returns None.
        """
        with self._lock:
            key = sender_id
            if key not in self._buffers:
                self._buffers[key] = {"pages": {}, "total": pkt.total_pages,
                                      "codec_id": pkt.codec_id}

            buf = self._buffers[key]
            buf["pages"][pkt.page_num] = raw_pkt

            if len(buf["pages"]) == buf["total"]:
                # All pages received — reassemble
                ordered = [buf["pages"][i] for i in sorted(buf["pages"])]
                result = reassemble_strict(ordered)
                del self._buffers[key]
                return result
            return None

    def clear(self, sender_id: str) -> None:
        with self._lock:
            self._buffers.pop(sender_id, None)


# =============================================================================
# EXPERIMENT RUN CONFIG
# =============================================================================

# Fixed experiment matrix (v7.1 spec — includes cube96 runs)
EXPERIMENT_MATRIX = [
    {"run": 1, "engine": "huffman",  "codebook_size": "333k",   "mode": "keyword",     "name": "huffman-333k-keyword"},
    {"run": 2, "engine": "mux_grid", "codebook_size": "333k",   "mode": "keyword",     "name": "mux_grid-333k-keyword"},
    {"run": 3, "engine": "huffman",  "codebook_size": "333k",   "mode": "strict_only", "name": "huffman-333k-strict"},
    {"run": 4, "engine": "mux_grid", "codebook_size": "333k",   "mode": "strict_only", "name": "mux_grid-333k-strict"},
    {"run": 5, "engine": "huffman",  "codebook_size": "333k",   "mode": "keyword",     "name": "huffman-333k-lossy-forced",
     "strict_threshold_override": 40},
    {"run": 6, "engine": "mux_grid", "codebook_size": "cube96", "mode": "keyword",     "name": "cube96-keyword"},
    {"run": 7, "engine": "mux_grid", "codebook_size": "cube96", "mode": "strict_only", "name": "cube96-strict"},
]


# =============================================================================
# METRICS RECORD
# =============================================================================

def empty_metrics() -> dict:
    return {
        "route": None,
        "raw_bytes": None,
        "encoded_bytes": None,
        "compression_ratio": None,
        "codebook_hit_rate": None,
        "ESC_count": None,
        "keyword_count": None,
        "extract_ms": None,
        "classify_ms": None,
        "reconstruct_ms": None,
        "RSSI": None,
        "SNR": None,
        "packet_count": None,
        "decoded_text": None,
        "error": None,
    }


# =============================================================================
# TRANSMIT FLOW
# =============================================================================

def transmit(
    text: str,
    sender_id: str,
    engine: str,
    codec,          # MeshHuffmanCodec | MuxGridCodec
    keyword_codec: KeywordCodec,
    smart_router: SmartRouter,
    radio: RadioInterface,
    cfg: dict,
    dest_id: str,
) -> dict:
    """
    Full transmit pipeline per v7.0 spec §3.

    Returns metrics dict.
    """
    t_total = time.perf_counter()
    metrics = empty_metrics()
    mode = cfg.get("codec", {}).get("mode", "keyword")
    inter_pkt_delay = cfg.get("pagination", {}).get("inter_packet_delay_s", 10)

    # ── Step 1: Pretokenize (always) ──────────────────────────────────────────
    pretok = normalize(text)

    # ── Step 2: Encode strict ─────────────────────────────────────────────────
    padding = 0
    if engine == "huffman":
        encoded = codec.encode(pretok)          # returns bytes
    else:
        encoded, padding = codec.encode(pretok)  # returns (bytes, padding)

    metrics["raw_bytes"]     = len(pretok.encode("utf-8"))
    metrics["encoded_bytes"] = len(encoded)

    # Codebook coverage stats
    try:
        cov = codec.codebook_coverage(pretok)
        metrics["codebook_hit_rate"] = round(cov.get("coverage", 0.0), 4)
        metrics["ESC_count"]         = len(cov.get("missing", []))
    except Exception:
        pass

    # ── Step 3: Route ─────────────────────────────────────────────────────────
    strict_threshold = cfg.get("router", {}).get("strict_threshold", 180)

    if mode == "keyword":
        t_classify = time.perf_counter()
        route = smart_router.route(encoded, text)
        metrics["classify_ms"] = round((time.perf_counter() - t_classify) * 1000, 2)
    elif mode == "strict_only":
        route = "strict" if len(encoded) <= strict_threshold else "paginate"
        metrics["classify_ms"] = 0.0
    else:
        # legacy — treat as strict; the old paginator handles overflow via
        # the text-level paginate() call in the v5.0 style
        route = "strict"
        metrics["classify_ms"] = 0.0

    metrics["route"] = route

    # Opt 1: When keyword mode is configured but router chose strict,
    # log what keyword extraction would have yielded (for comparison)
    if mode == "keyword" and route == "strict":
        if cfg.get("logging", {}).get("pipeline_trace", False):
            log(f"  KW-vs-strict note: strict chosen ({len(encoded)}B ≤ {strict_threshold}B). "
                f"Raw text: {len(pretok)}chars")

    # ── Step 4: Act on route ──────────────────────────────────────────────────
    if route == "strict":
        codec_id = 0x01 if engine == "huffman" else 0x02
        pkt = CyberMeshPacket.encode(codec_id, encoded)
        radio.send_data(pkt, dest_id)
        metrics["packet_count"] = 1
        log(f"TX strict: {len(encoded)}B → 1 pkt  codec=0x{codec_id:02X}  "
            f"ratio={metrics['raw_bytes']/(len(encoded) or 1):.2f}:1")

    elif route == "lossy":
        t_extract = time.perf_counter()
        keywords, extract_ms = keyword_codec.extract(text)
        metrics["extract_ms"]   = round(extract_ms, 2)
        metrics["keyword_count"] = len(keywords)

        # Opt 1: Log keyword extraction for comparison
        kw_joined = " ".join(keywords)
        log(f"  KW extract: {len(keywords)} keywords: \"{kw_joined}\"")
        raw_b = metrics["raw_bytes"]
        log(f"  KW vs raw:  raw={raw_b}B  kw_text={len(kw_joined)}chars")

        if engine == "huffman":
            kw_encoded = codec.encode_keywords(keywords)
        else:
            kw_encoded = codec.encode_keywords(keywords)

        codec_id = 0x03 if engine == "huffman" else 0x04
        pkt = CyberMeshPacket.encode(codec_id, kw_encoded,
                                     keyword_count=len(keywords))
        radio.send_data(pkt, dest_id)
        metrics["packet_count"]  = 1
        metrics["encoded_bytes"] = len(kw_encoded)
        log(f"TX lossy: {len(keywords)} keywords → {len(kw_encoded)}B  "
            f"codec=0x{codec_id:02X}  extract={extract_ms:.0f}ms")

    elif route == "paginate":
        codec_id = 0x01 if engine == "huffman" else 0x02
        packets = paginate_strict(encoded, codec_id=codec_id)
        metrics["packet_count"] = len(packets)
        for i, pkt in enumerate(packets):
            radio.send_data(pkt, dest_id)
            if i < len(packets) - 1:
                time.sleep(inter_pkt_delay)
        log(f"TX paginate: {len(encoded)}B → {len(packets)} pkts  "
            f"codec=0x{codec_id:02X}")

    else:
        log(f"TX: unknown route {route!r} — dropping", "ERROR")
        metrics["error"] = f"unknown route: {route}"

    # Compression ratio
    if metrics["raw_bytes"] and metrics["encoded_bytes"]:
        metrics["compression_ratio"] = round(
            metrics["raw_bytes"] / metrics["encoded_bytes"], 4)

    # ── Pipeline trace (controlled by config) ──────────────────────────────────────
    if cfg.get("logging", {}).get("pipeline_trace", False):
        wire_hex = encoded.hex() if encoded else ""
        log(f"  [PIPELINE TX]")
        log(f"    [ORIGINAL]   {text}")
        log(f"    [PRETOK]     {pretok}")
        log(f"    [COMPRESSED] {wire_hex} ({len(encoded)}B)")
        log(f"    [RATIO]      {metrics.get('compression_ratio', 0):.3f}:1")
        log(f"    [ROUTE]      {route}")
        metrics["_wire_hex"] = wire_hex
        metrics["_encoded_bytes_hex"] = wire_hex

    metrics["_total_tx_ms"] = round((time.perf_counter() - t_total) * 1000, 2)
    return metrics


# =============================================================================
# RECEIVE FLOW
# =============================================================================

def receive(
    raw_bytes: bytes,
    sender_id: str,
    engine: str,
    codec,
    keyword_codec: KeywordCodec,
    page_buffer: PageBuffer,
    rssi,
    snr,
) -> dict:
    """
    Full receive pipeline per v7.0 spec §4.

    Returns metrics dict with 'decoded_text' populated.
    """
    metrics = empty_metrics()
    metrics["RSSI"] = rssi
    metrics["SNR"]  = snr

    try:
        pkt = CyberMeshPacket.decode(raw_bytes)
    except Exception as exc:
        log(f"RX: packet decode error: {exc}", "ERROR")
        metrics["error"] = str(exc)
        return metrics

    metrics["encoded_bytes"] = len(raw_bytes)

    # ── Multi-page reassembly ─────────────────────────────────────────────────
    if pkt.total_pages > 1:
        log(f"RX page {pkt.page_num+1}/{pkt.total_pages} from {sender_id}")
        reassembled = page_buffer.add(sender_id, pkt, raw_bytes)
        if reassembled is None:
            # Not all pages yet — caller must wait for more
            metrics["_waiting_for_pages"] = True
            return metrics
        # All pages received — reassemble into a single payload
        # Re-decode the reassembled data with a dummy single-page packet
        # (reassembled is already the raw concatenated payload bytes)
        payload = reassembled
        codec_id = pkt.codec_id
    else:
        payload  = pkt.payload
        codec_id = pkt.codec_id

    metrics["packet_count"] = pkt.total_pages

    # ── Decode by codec_id ────────────────────────────────────────────────────
    if codec_id in (0x01, 0x02):
        # Strict / lossless
        try:
            t_decode = time.perf_counter()
            if codec_id == 0x01:
                decoded = codec.decode(payload)
            else:
                decoded = codec.decode(payload, 0)  # 0 padding for 333k
            metrics["decoded_text"] = decoded
            metrics["decode_ms"] = round((time.perf_counter() - t_decode) * 1000, 2)
            metrics["keyword_count"] = len(decoded.split()) if decoded else 0
            metrics["route"] = "strict"
            log(f"RX strict: {len(raw_bytes)}B → \"{decoded}\"  "
                f"RSSI={rssi}  SNR={snr}")
        except Exception as exc:
            log(f"RX: strict decode error: {exc}", "ERROR")
            metrics["error"] = str(exc)

    elif codec_id in (0x03, 0x04):
        # Lossy / keyword mode
        try:
            if codec_id == 0x03:
                keywords = codec.decode_keywords(payload, pkt.keyword_count)
            else:
                keywords = codec.decode_keywords(payload, pkt.keyword_count)

            metrics["keyword_count"] = len(keywords)
            metrics["route"] = "lossy"

            t_recon = time.perf_counter()
            reconstructed, recon_ms = keyword_codec.reconstruct(keywords)
            metrics["reconstruct_ms"] = round(recon_ms, 2)
            metrics["decoded_text"]   = reconstructed

            log(f"RX lossy: {len(keywords)} kws → \"{reconstructed}\"  "
                f"recon={recon_ms:.0f}ms  RSSI={rssi}  SNR={snr}")

        except Exception as exc:
            log(f"RX: lossy decode error: {exc}", "ERROR")
            metrics["error"] = str(exc)
    else:
        log(f"RX: unknown codec_id 0x{codec_id:02X}", "ERROR")
        metrics["error"] = f"unknown codec_id: 0x{codec_id:02X}"

    # ── Pipeline trace ───────────────────────────────────────────────────
    # Note: pipeline_trace checked by caller; here we always store hex
    wire_hex = raw_bytes.hex() if raw_bytes else ""
    metrics["_wire_hex"] = wire_hex
    metrics["_encoded_bytes_hex"] = wire_hex

    return metrics


# =============================================================================
# PING HANDLER
# =============================================================================

PING_COMMAND = "!ping"
PONG_REPLY   = "PONG"


def handle_ping(raw_bytes: bytes, sender_id: str,
                radio: RadioInterface) -> bool:
    """
    Check for !ping BEFORE any pipeline processing.

    Returns True if packet was a ping (consumed); False otherwise.
    The !ping NEVER enters context_manager or codec pipeline.
    """
    try:
        text = raw_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return False

    if text == PING_COMMAND:
        log(f"PING from {sender_id} — replying PONG")
        radio.send_text(PONG_REPLY, sender_id)
        return True
    return False


# =============================================================================
# LLM GENERATE (for experiment conversation turns)
# =============================================================================

def generate_turn(llm: LLMClient, system_prompt: str,
                  history: list[dict]) -> tuple[str, float]:
    """
    Generate the next conversation turn using the LLM.

    Builds a single user prompt from conversation history and generates
    the next response.

    Returns: (text, elapsed_ms)
    """
    if not history:
        user_prompt = "Begin the conversation."
    else:
        lines = []
        for msg in history:
            role = "You" if msg["role"] == "assistant" else "Them"
            lines.append(f"{role}: {msg['content']}")
        user_prompt = "\n".join(lines) + "\nYou:"

    text, elapsed_ms = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=80,
        temperature=0.7,
    )

    # Clean up: strip quotes, markdown, multiline artefacts
    text = text.strip().strip('"\'')
    if "\n" in text:
        text = text.split("\n")[0].strip()

    return text, elapsed_ms


# =============================================================================
# LOG WRITERS
# =============================================================================

def _make_log_dir(log_dir: str) -> str:
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def write_markdown_log(
    run_name: str,
    exp_name: str,
    role: str,
    peer_id: str,
    run_cfg: dict,
    tx_records: list[dict],
    rx_records: list[dict],
    log_dir: str = "./logs",
) -> str:
    """Write a markdown experiment log. Returns the file path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fname = f"experiment-{exp_name}-{run_name}-log_{ts}.md"
    fpath = os.path.join(_make_log_dir(log_dir), fname)

    lines = [
        f"# CyberMesh v{VERSION} \"{CODENAME}\" — Experiment {exp_name}",
        f"",
        f"**Run:**         `{run_name}`  ",
        f"**Role:**        {role}  ",
        f"**Peer:**        {peer_id}  ",
        f"**Engine:**      {run_cfg['engine']}  ",
        f"**Codebook:**    {run_cfg['codebook_size']}  ",
        f"**Mode:**        {run_cfg['mode']}  ",
        f"**Timestamp:**   {ts}  ",
        f"",
        f"---",
        f"",
        f"## TX Messages",
        f"",
        f"| # | route | raw_B | enc_B | ratio | hit_rate | ESC | kw | "
        f"extract_ms | classify_ms | pkts | text | wire_hex |",
        f"|---|-------|-------|-------|-------|----------|-----|----|"
        f"-----------|-------------|------|------|----------|",
    ]

    for i, r in enumerate(tx_records, 1):
        lines.append(
            f"| {i} "
            f"| {r.get('route') or '—'} "
            f"| {r.get('raw_bytes') or '—'} "
            f"| {r.get('encoded_bytes') or '—'} "
            f"| {r.get('compression_ratio') or '—'} "
            f"| {r.get('codebook_hit_rate') or '—'} "
            f"| {r.get('ESC_count') or '—'} "
            f"| {r.get('keyword_count') or '—'} "
            f"| {r.get('extract_ms') or '—'} "
            f"| {r.get('classify_ms') or '—'} "
            f"| {r.get('packet_count') or '—'} "
            f"| `{str(r.get('_original_text', ''))}` "
            f"| `{r.get('_wire_hex', '')}` |"
        )

    lines += [
        f"",
        f"## RX Messages",
        f"",
        f"| # | route | enc_B | kw | recon_ms | RSSI | SNR | pkts | decoded_text |",
        f"|---|-------|-------|----|----------|------|-----|------|--------------|",
    ]

    for i, r in enumerate(rx_records, 1):
        lines.append(
            f"| {i} "
            f"| {r.get('route') or '—'} "
            f"| {r.get('encoded_bytes') or '—'} "
            f"| {r.get('keyword_count') or '—'} "
            f"| {r.get('reconstruct_ms') or '—'} "
            f"| {r.get('RSSI') or '—'} "
            f"| {r.get('SNR') or '—'} "
            f"| {r.get('packet_count') or '—'} "
            f"| `{str(r.get('decoded_text', ''))}` |"
        )

    lines += ["", "---", ""]

    # Summary stats
    valid_tx = [r for r in tx_records if r.get("compression_ratio")]
    avg_ratio = (sum(r["compression_ratio"] for r in valid_tx) / len(valid_tx)
                 if valid_tx else 0)
    lines += [
        f"## Summary",
        f"",
        f"- TX messages:       {len(tx_records)}",
        f"- RX messages:       {len(rx_records)}",
        f"- Avg compression:   {avg_ratio:.3f}:1",
        f"",
    ]

    with open(fpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    log(f"Log written: {fpath}")
    return fpath


def write_json_log(
    run_name: str,
    exp_name: str,
    all_data: dict,
    log_dir: str = "./logs",
) -> str:
    """Write a JSON experiment log. Returns the file path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fname = f"experiment-{exp_name}-{run_name}-log_{ts}.json"
    fpath = os.path.join(_make_log_dir(log_dir), fname)
    all_data["_fidelity_note"] = ("Cross-reference tx_records[i]._original_text with "
                                  "rx_records[i].decoded_text for fidelity scoring")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, default=str)
    log(f"JSON log written: {fpath}")
    return fpath


# =============================================================================
# SINGLE RUN  (one codec + mode combination)
# =============================================================================

class RunRunner:
    """
    Orchestrates one experiment run (codec + mode + messages_per_node).

    Works in both live LoRa mode and loopback mock mode.
    """

    def __init__(
        self,
        run_cfg: dict,
        global_cfg: dict,
        llm: LLMClient,
        radio: RadioInterface,
        context_manager: ContextManager,
        page_buffer: PageBuffer,
        role: str,
        peer_id: str,
    ):
        self.run_cfg = run_cfg
        self.cfg     = global_cfg
        self.llm     = llm
        self.radio   = radio
        self.ctx     = context_manager
        self.page_buf = page_buffer
        self.role    = role         # "A" (initiator) or "B" (responder)
        self.peer_id = peer_id

        # Override global codec/mode with run-specific values
        self._engine   = run_cfg["engine"]
        self._cb_size  = run_cfg["codebook_size"]
        self._mode     = run_cfg["mode"]

        # Build per-run codec and support objects
        self.codec, _ = build_codec(self._engine, self._cb_size)

        # Patch config for this run
        patched_cfg = dict(global_cfg)
        patched_cfg["codec"] = dict(global_cfg.get("codec", {}))
        patched_cfg["codec"]["engine"]        = self._engine
        patched_cfg["codec"]["codebook_size"] = self._cb_size
        patched_cfg["codec"]["mode"]          = self._mode

        # Opt 4: Per-run threshold override (forces lossy path testing)
        self._strict_threshold_override = run_cfg.get("strict_threshold_override")
        if self._strict_threshold_override is not None:
            patched_cfg["router"] = dict(patched_cfg.get("router", {}))
            patched_cfg["router"]["strict_threshold"] = self._strict_threshold_override
            log(f"  Threshold override: {self._strict_threshold_override}B (force lossy)")

        self.kw_codec  = KeywordCodec(llm_client=llm, config=patched_cfg)
        self.router    = SmartRouter(llm_client=llm, config=patched_cfg)
        self.patched_cfg = patched_cfg

        # Message counts
        self.messages_per_node = global_cfg.get("experiment", {}).get(
            "messages_per_node", global_cfg.get("messages_per_node", 10))
        self.timeout_s = global_cfg.get("lemonade", {}).get("timeout_s",
                         global_cfg.get("timeout_s", 45))
        self.system_prompt = global_cfg.get("conversation_seed", "")

        # Receive synchronization
        self._rx_event   = threading.Event()
        self._rx_pending: dict | None = None
        self._rx_lock    = threading.Lock()

        # Results
        self.tx_records: list[dict] = []
        self.rx_records: list[dict] = []

    def _on_receive(self, raw_bytes: bytes, sender_id: str,
                    rssi, snr, packet) -> None:
        """Radio RX callback — runs in radio thread."""
        # !ping check FIRST — never enters pipeline
        if handle_ping(raw_bytes, sender_id, self.radio):
            return

        # --- Bug 3 fix: Reject trigger-length packets & known control payloads ---
        if len(raw_bytes) < 4:
            log(f"Ignoring short packet ({len(raw_bytes)}B) from {sender_id}"
                " — likely trigger rebroadcast")
            return
        if raw_bytes in (b"Hi", b"ACK", b"PONG"):
            return

        # --- Bug 1 fix: Peer discovery when peer is unknown/broadcast ---
        if self.peer_id == "!ffffffff":
            self.peer_id = sender_id
            # Also update the ExperimentRunner's peer_id via the RunRunner ref
            log(f"Peer discovered: {sender_id}")
        elif sender_id != self.peer_id:
            return  # ignore packets from non-peers

        metrics = receive(
            raw_bytes=raw_bytes,
            sender_id=sender_id,
            engine=self._engine,
            codec=self.codec,
            keyword_codec=self.kw_codec,
            page_buffer=self.page_buf,
            rssi=rssi,
            snr=snr,
        )

        if metrics.get("_waiting_for_pages"):
            return  # wait for more pages

        with self._rx_lock:
            self._rx_pending = metrics
        self._rx_event.set()

    def _wait_for_rx(self) -> dict:
        """Block until RX arrives or timeout."""
        self._rx_event.clear()
        with self._rx_lock:
            self._rx_pending = None

        got = self._rx_event.wait(timeout=self.timeout_s)
        if not got:
            log(f"RX timeout ({self.timeout_s}s)", "WARN")
            m = empty_metrics()
            m["error"] = f"timeout_{self.timeout_s}s"
            return m

        with self._rx_lock:
            return self._rx_pending or empty_metrics()

    def _is_my_tx_step(self, step: int) -> bool:
        """
        Role B sends on odd steps (1, 3, 5, …).
        Role A sends on even steps (2, 4, 6, …).
        """
        return (step % 2 == 1) if self.role == "B" else (step % 2 == 0)

    def run(self) -> tuple[list[dict], list[dict]]:
        """
        Execute all message exchanges for this run.

        Returns (tx_records, rx_records).
        """
        run_name = self.run_cfg["name"]
        total    = self.messages_per_node * 2

        log(f"{'='*65}")
        log(f"RUN {self.run_cfg['run']}/{len(EXPERIMENT_MATRIX)}: {run_name.upper()}")
        log(f"  Engine={self._engine}  Codebook={self._cb_size}  Mode={self._mode}")
        log(f"  Role={self.role}  Peer={self.peer_id}  Steps={total}")
        log(f"{'='*65}")

        # Register RX callback for this run
        self.radio.register_rx_callback(self._on_receive)

        # --- Hardening 2: Track consecutive RX timeouts ---
        MAX_CONSECUTIVE_TIMEOUTS = 5
        consecutive_timeouts = 0

        for step in range(1, total + 1):
            if self._is_my_tx_step(step):
                self._do_tx(step)
                consecutive_timeouts = 0  # TX doesn't count
            else:
                self._do_rx(step)
                # Check if the last RX was a timeout
                if (self.rx_records and
                        (self.rx_records[-1].get("error") or "").startswith("timeout")):
                    consecutive_timeouts += 1
                    if consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
                        log(f"ABORT: {MAX_CONSECUTIVE_TIMEOUTS} consecutive "
                            f"RX timeouts. Peer {self.peer_id} appears "
                            f"offline.", "ERROR")
                        break
                else:
                    consecutive_timeouts = 0

        # --- Bug 5 fix: Post-TX flush delay ---
        # After last step, wait for radio to finish transmitting.
        # Prevents last-packet loss from premature teardown.
        if not self.radio._loopback:
            log("Last step complete. Waiting 5s for radio flush...")
            time.sleep(5)

        # Hard-reset RX callbacks to prevent stacking across runs
        self.radio._rx_callbacks = []

        return self.tx_records, self.rx_records

    def _do_tx(self, step: int) -> None:
        """Generate a message with the LLM and transmit it."""
        history = self.ctx.get(self.peer_id)
        text, gen_ms = generate_turn(self.llm, self.system_prompt, history)
        log(f"[{step}/{self.messages_per_node*2}] TX gen ({gen_ms:.0f}ms): \"{text}\"")

        metrics = transmit(
            text=text,
            sender_id=self.radio.my_node_id,
            engine=self._engine,
            codec=self.codec,
            keyword_codec=self.kw_codec,
            smart_router=self.router,
            radio=self.radio,
            cfg=self.patched_cfg,
            dest_id=self.peer_id,
        )
        metrics["_original_text"] = text
        metrics["_gen_ms"]        = round(gen_ms, 2)
        metrics["_step"]          = step
        self.tx_records.append(metrics)

        # Add to context (assistant role — this node's output)
        self.ctx.add(self.peer_id, "assistant", text)

        # Loopback: the sent packet is also the received one for this node;
        # in live mode the remote node sends back independently.

    def _do_rx(self, step: int) -> None:
        """Wait for an incoming packet and decode it."""
        log(f"[{step}/{self.messages_per_node*2}] RX waiting...")

        if self.radio._loopback:
            # In loopback mode: pop the queued packet we just sent
            raw = self.radio.pop_loopback(timeout=self.timeout_s)
            if raw is None:
                log("Loopback RX timeout", "WARN")
                m = empty_metrics()
                m["error"] = "loopback_timeout"
                m["_step"] = step
                self.rx_records.append(m)
                return

            metrics = receive(
                raw_bytes=raw,
                sender_id=self.peer_id,
                engine=self._engine,
                codec=self.codec,
                keyword_codec=self.kw_codec,
                page_buffer=self.page_buf,
                rssi=None,
                snr=None,
            )
        else:
            metrics = self._wait_for_rx()

        metrics["_step"] = step
        self.rx_records.append(metrics)

        # Pipeline trace
        if self.cfg.get("logging", {}).get("pipeline_trace", False):
            wire_hex = metrics.get("_wire_hex", "")
            decoded_text = metrics.get("decoded_text", "")
            log(f"  [PIPELINE RX]")
            log(f"    [WIRE HEX]  {wire_hex} ({metrics.get('encoded_bytes', 0)}B)")
            log(f"    [DECODED]   {decoded_text}")

        decoded = metrics.get("decoded_text", "")
        if decoded:
            self.ctx.add(self.peer_id, "user", decoded)
            log(f"  RX decoded: \"{decoded}\"")
        elif metrics.get("error"):
            log(f"  RX error: {metrics['error']}", "WARN")


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================

class ExperimentRunner:
    """
    Top-level orchestrator for the 4-run v7.0 experiment matrix.

    Handles:
      - Initialization sequence
      - Trigger / role assignment (Role A = initiator, Role B = responder)
      - Sequential run execution
      - Log output
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg

        # ── Init LLMClient ────────────────────────────────────────────────────
        lem_cfg   = cfg.get("lemonade", {})
        test_cfg  = cfg.get("testing", {})
        self.llm  = LLMClient(
            base_url = lem_cfg.get("base_url", "http://localhost:8000"),
            model    = lem_cfg.get("model", "test01"),
            timeout  = lem_cfg.get("timeout_s", 45),
            mock     = test_cfg.get("mock_llm", False),
        )
        log(f"LLMClient: model={self.llm.model}  base_url={self.llm.base_url}  "
            f"mock={self.llm.mock}")

        # ── Init ContextManager ───────────────────────────────────────────────
        ctx_cfg = cfg.get("context", {})
        self.ctx_mgr = ContextManager(
            window_size  = ctx_cfg.get("window_size", 4),
            anchor_first = ctx_cfg.get("anchor_first", True),
        )

        # ── Init Radio ────────────────────────────────────────────────────────
        radio_cfg = cfg.get("radio", cfg)
        self.radio = RadioInterface(port=radio_cfg.get("port", "auto"))

        # ── Shared page buffer (across runs) ──────────────────────────────────
        self.page_buf = PageBuffer()

        # ── Role / peer ───────────────────────────────────────────────────────
        self.role    = "B"          # default; may change on trigger
        self.peer_id = "!00000000"

        # ── Trigger sync ──────────────────────────────────────────────────────
        self._trigger_event  = threading.Event()
        self._ack_event      = threading.Event()   # Bug 2: ACK handshake
        self._trigger_sender: str | None = None

        # ── Results ───────────────────────────────────────────────────────────
        self.all_results: dict[str, dict] = {}

    # ── Initialization ────────────────────────────────────────────────────────

    def initialize(self) -> None:
        """Full initialization sequence per v7.0 spec §2."""
        log("── Initialization ──────────────────────────────────────────")

        # Warmup LLM
        if self.cfg.get("lemonade", {}).get("warmup_on_start", True):
            log("LLM warmup...")
            warmup_ms = self.llm.warmup()
            log(f"LLM warmup: {warmup_ms:.0f}ms")

        # Connect radio
        self.radio.connect()
        log(f"Radio: {self.radio.my_node_name} ({self.radio.my_node_id})  "
            f"loopback={self.radio._loopback}")

        # Register trigger listener
        self.radio.register_rx_callback(self._on_trigger)
        # Register ACK listener (Bug 2: Role A learns peer ID from ACK)
        self.radio.register_rx_callback(self._on_ack)

        log("── Ready ─────────────────────────────────────────────────")

    def _on_trigger(self, raw_bytes: bytes, sender_id: str,
                    rssi, snr, packet) -> None:
        """
        Trigger detection callback.

        In live mode: Role A sends "Hi" (TEXT_MESSAGE_APP) to start the
        experiment; Role B receives it and sets self.role = "B".
        The node that receives the trigger first becomes Role B.

        In loopback mode: immediately sets self.role = "B".
        """
        if self._trigger_event.is_set():
            return  # Already triggered

        # !ping check
        if handle_ping(raw_bytes, sender_id, self.radio):
            return

        try:
            text = raw_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            text = ""

        trigger_word = self.cfg.get("trigger_word", "Hi")
        if text == trigger_word:
            log(f"TRIGGER received from {sender_id}: \"{text}\"")
            self._trigger_sender = sender_id
            self.peer_id         = sender_id
            self.role            = "B"
            # --- Bug 2 fix: Send ACK so Role A learns our node ID ---
            self.radio.send_text("ACK", sender_id)
            log(f"Trigger ACK sent to {sender_id}")
            self._trigger_event.set()

    def _send_trigger(self) -> None:
        """Role A: send the trigger word to start the experiment."""
        trigger_word = self.cfg.get("trigger_word", "Hi")
        # In loopback, send directly to loopback peer
        dest = self.cfg.get("radio", {}).get("peer_id",
               self.cfg.get("peer_id", "!ffffffff"))
        self.peer_id = dest
        self.role    = "A"
        log(f"Sending trigger \"{trigger_word}\" to {dest}")
        self.radio.send_text(trigger_word, dest)

        # --- Bug 2 fix: Wait for ACK to learn peer ID ---
        ack_received = self._ack_event.wait(timeout=15.0)
        if ack_received:
            log(f"Trigger ACK received. Peer: {self.peer_id}")
        else:
            log("No trigger ACK received (15s). Peer remains: "
                f"{self.peer_id}", "WARN")

    def _on_ack(self, raw_bytes: bytes, sender_id: str,
                rssi, snr, packet) -> None:
        """ACK handler: Role A learns peer ID from ACK response."""
        if self._ack_event.is_set():
            return  # Already received ACK
        try:
            text = raw_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            return
        if text == "ACK":
            self.peer_id = sender_id
            log(f"ACK from {sender_id}")
            self._ack_event.set()

    # ── Main experiment entry point ───────────────────────────────────────────

    def run_experiment(self, role: str = "auto") -> None:
        """
        Run all 4 experiment runs.

        role: "A" = initiator (sends first), "B" = responder, "auto" = wait
        for trigger to determine role.
        """
        exp_name  = self.cfg.get("experiment", {}).get("name", "F")
        log_dir   = self.cfg.get("logging", {}).get("dir", "./logs")
        log_fmt   = self.cfg.get("logging", {}).get("format", "markdown")

        # ── Role assignment ───────────────────────────────────────────────────
        if role == "A":
            self._send_trigger()
            self.role = "A"
        elif role == "B":
            log("Role B: waiting for trigger...")
            if not self.radio._loopback:
                self._trigger_event.wait()
            else:
                # Loopback — self-trigger for testing
                self.peer_id = self.radio.my_node_id
                self.role    = "B"
                log("Loopback mode: self-trigger as Role B")
        else:
            # Auto: wait up to 10 s for external trigger; if none, become A
            log("Auto role: waiting for trigger (10s)...")
            triggered = self._trigger_event.wait(timeout=10)
            if triggered:
                self.role    = "B"
                self.peer_id = self._trigger_sender
                log(f"Role assigned: B (peer={self.peer_id})")
            else:
                self._send_trigger()
                self.role = "A"
                log("No trigger received — assuming Role A")

        log(f"Role: {self.role}  Peer: {self.peer_id}")

        # Remove trigger/ACK listeners (runs handle their own RX)
        for cb in (self._on_trigger, self._on_ack):
            try:
                self.radio._rx_callbacks.remove(cb)
            except ValueError:
                pass

        # --- Hardening 1: Abort if no peer discovered (live mode only) ---
        if not self.radio._loopback and self.peer_id in ("!ffffffff", "!00000000"):
            log("ERROR: No peer discovered during trigger handshake. "
                "Aborting experiment.", "ERROR")
            log("       Ensure both nodes are powered on, on the same "
                "Meshtastic channel, and within radio range.", "ERROR")
            self.radio.close()
            sys.exit(1)

        # ── Sequential runs ───────────────────────────────────────────────────
        for run_cfg in EXPERIMENT_MATRIX:
            run_name = run_cfg["name"]
            log(f"\n{'─'*65}")
            log(f"STARTING RUN {run_cfg['run']}/{len(EXPERIMENT_MATRIX)}: {run_name}")
            log(f"{'─'*65}")

            # Reset context for each run
            self.ctx_mgr.clear(self.peer_id)
            # Reset page buffer
            self.page_buf.clear(self.peer_id)

            runner = RunRunner(
                run_cfg         = run_cfg,
                global_cfg      = self.cfg,
                llm             = self.llm,
                radio           = self.radio,
                context_manager = self.ctx_mgr,
                page_buffer     = self.page_buf,
                role            = self.role,
                peer_id         = self.peer_id,
            )

            tx_records, rx_records = runner.run()

            self.all_results[run_name] = {
                "run_cfg":    run_cfg,
                "role":       self.role,
                "peer_id":    self.peer_id,
                "tx_records": tx_records,
                "rx_records": rx_records,
            }

            # ── Write per-run logs ────────────────────────────────────────────
            if log_fmt in ("markdown", "both"):
                write_markdown_log(
                    run_name   = run_name,
                    exp_name   = exp_name,
                    role       = self.role,
                    peer_id    = self.peer_id,
                    run_cfg    = run_cfg,
                    tx_records = tx_records,
                    rx_records = rx_records,
                    log_dir    = log_dir,
                )
            if log_fmt in ("json", "both"):
                write_json_log(
                    run_name = run_name,
                    exp_name = exp_name,
                    all_data = self.all_results[run_name],
                    log_dir  = log_dir,
                )

            # Brief inter-run pause (allow radio to settle)
            if run_cfg["run"] < len(EXPERIMENT_MATRIX):
                pause = 5
                log(f"Run {run_cfg['run']} complete. Pausing {pause}s...")
                time.sleep(pause)

        # ── Final comparison ──────────────────────────────────────────────────
        self._print_comparison()
        log("Experiment complete.")

    # ── Comparison summary ────────────────────────────────────────────────────

    def _print_comparison(self) -> None:
        width = 86
        print("\n" + "=" * width)
        print(f"  EXPERIMENT COMPARISON — v{VERSION} \"{CODENAME}\"")
        print("─" * width)
        header = (f"  {'Run':<30} {'TX ratio':>10} {'RX ok/tot':>10} "
                  f"{'RX kw/msg':>10} {'RX ms':>8} {'pkts':>6} {'Status':>8}")
        print(header)
        print("─" * width)

        for run_name, data in self.all_results.items():
            tx = data["tx_records"]
            rx = data["rx_records"]

            valid_tx = [r for r in tx if r.get("compression_ratio")]
            avg_ratio = (sum(r["compression_ratio"] for r in valid_tx) /
                         len(valid_tx)) if valid_tx else 0.0

            # --- Hardening 3: RX ok/total + FAILED flag ---
            rx_ok    = sum(1 for r in rx if r.get("decoded_text"))
            rx_total = len(rx)
            rx_str   = f"{rx_ok}/{rx_total}"

            valid_kw = [r for r in rx if r.get("keyword_count") is not None]
            avg_kw   = (sum(r["keyword_count"] for r in valid_kw) /
                        len(valid_kw)) if valid_kw else 0.0

            # RX timing: use decode_ms for strict, reconstruct_ms for lossy
            valid_ms = [r for r in rx if r.get("decode_ms") or r.get("reconstruct_ms")]
            avg_rec  = (sum(r.get("decode_ms") or r.get("reconstruct_ms") or 0
                            for r in valid_ms) /
                        len(valid_ms)) if valid_ms else 0.0

            total_pkts = sum(r.get("packet_count") or 1 for r in tx)

            # Flag FAILED if RX success rate < 50%
            if rx_total > 0 and rx_ok / rx_total < 0.5:
                status = "! FAILED"
            else:
                status = "OK"

            print(f"  {run_name:<30} {avg_ratio:>10.3f} {rx_str:>10} "
                  f"{avg_kw:>10.1f} {avg_rec:>8.1f} {total_pkts:>6} "
                  f"{status:>8}")

        print("=" * width + "\n")


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main() -> None:
    global EXPERIMENT_MATRIX
    import argparse

    parser = argparse.ArgumentParser(
        description=f"CyberMesh v{VERSION} \"{CODENAME}\" Experiment Harness",
    )
    parser.add_argument(
        "--role", choices=["A", "B", "auto"], default="auto",
        help="Node role: A=initiator, B=responder, auto=negotiate (default)",
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Force mock LLM mode (overrides config.testing.mock_llm)",
    )
    valid_runs = sorted(r["run"] for r in EXPERIMENT_MATRIX)
    parser.add_argument(
        "--run", type=int, choices=valid_runs, default=None,
        help=f"Run only a single experiment run ({valid_runs[0]}-{valid_runs[-1]})",
    )
    args = parser.parse_args()

    # ── Load config ───────────────────────────────────────────────────────────
    cfg = load_config()

    # CLI overrides
    if args.mock:
        cfg.setdefault("testing", {})["mock_llm"] = True

    # ── Ensure codebooks exist (auto-build on first run) ──────────────────────
    codebook_size = cfg.get("codec", {}).get("codebook_size", "4k")
    if codebook_size == "333k":
        ensure_codebooks()

    # ── Banner ────────────────────────────────────────────────────────────────
    print_banner(cfg)

    # ── Build & run ───────────────────────────────────────────────────────────
    runner = ExperimentRunner(cfg)
    runner.initialize()

    if args.run is not None:
        # Slice EXPERIMENT_MATRIX to just the requested run
        EXPERIMENT_MATRIX = [r for r in EXPERIMENT_MATRIX if r["run"] == args.run]
        log(f"Single-run mode: {EXPERIMENT_MATRIX[0]['name']}")

    runner.run_experiment(role=args.role)


if __name__ == "__main__":
    main()
