---
title: "Troubleshooting — CyberMesh Codec POC"
version: 2.0.0
date: 2026-03-05
status: active
project: huffman-mesh-poc
---

# Troubleshooting

Living document. Updated on every failure or unexpected behavior.

---

## Issue 001 — Serial Port Auto-Detect Picks Wrong Device

- **Context**: Windows machine with multiple USB serial devices
- **Symptom**: `SerialInterface()` connects to a non-Meshtastic device
- **Error**: `Exception: No Meshtastic device found` or garbled output
- **Probable Cause**: Another USB serial device (Arduino, FTDI cable) detected first
- **Quick Fix**: Set `port: COM6` (or `COM3`) explicitly in `config.yaml`
- **Permanent Fix**: Unplug other serial devices during test
- **Status**: Seeded (known risk from prior Liberty Mesh development)

---

## Issue 002 — pubsub Subscription Timing

- **Context**: `pub.subscribe(onReceive, "meshtastic.receive")` called before
  interface is fully initialized
- **Symptom**: First 1-2 messages silently dropped after script startup
- **Error**: No error — messages just don't appear
- **Probable Cause**: Race condition between SerialInterface init and pubsub
  registration. Known from `liberty_mesh_v2.py` debugging.
- **Quick Fix**: Add 2-second `time.sleep()` after interface init, before
  printing "listening" banner
- **Permanent Fix**: Subscribe before creating interface (pubsub queues events)
- **Status**: Seeded (mitigated in POC by subscribing before interface connect)

---

## Issue 003 — Echo Cancellation (Own Packets)

- **Context**: Node receives its own outbound messages via `meshtastic.receive`
- **Symptom**: Script processes its own sent messages as incoming test data
- **Error**: Test sequence gets out of order, double-logs messages
- **Probable Cause**: `packet['fromId']` is a hex string (`!aabbccdd`),
  `interface.myInfo.my_node_num` is an integer. Direct comparison always fails.
- **Quick Fix**: Convert hex string to int before comparing:
  `int(sender.replace("!", ""), 16) == interface.myInfo.my_node_num`
- **Permanent Fix**: Implemented in POC script's `_is_my_packet()` method
- **Status**: Seeded (discovered and fixed in operator_v5.py)

---

## Issue 004 — Channel Filter Drops Packets

- **Context**: Filtering `packet.get('channel', 0) != target_channel`
- **Symptom**: All messages silently dropped
- **Error**: No error output
- **Probable Cause**: protobuf3 doesn't serialize default zero values. Packets
  on channel 0 often lack the `channel` key entirely.
  `packet.get('channel', 0)` returns 0, which works — but filtering on
  non-zero channels requires the key to exist.
- **Quick Fix**: Don't filter by channel for this POC. Trigger uses DM
  (any channel), test data uses custom portnum (channel irrelevant).
- **Permanent Fix**: Filter by `portNum` instead of channel index
- **Status**: Seeded (discovered in liberty_mesh_v2.py debugging)

---

## Issue 005 — sendData portNum Not Received

- **Context**: Sending compressed bytes via `sendData(data, portNum=256)`
- **Symptom**: Receiver never sees the packet
- **Probable Cause**: Custom portnum may need to be in the valid range.
  Meshtastic reserves portnums 1-255 for built-in apps. User portnums
  should be 256+ per the Meshtastic protobufs.
- **Quick Fix**: Verify with `portNum=256`. If not received, try `portNum=257`.
- **Permanent Fix**: Check Meshtastic Python API docs for valid user portnum range
- **Status**: Seeded (untested — first use of custom portnum in this project)

---

## Issue 006 — sendData destinationId Format

- **Context**: First live test, Role B sending compressed data
- **Symptom**: `sendData()` completes without exception but packets never arrive at peer
- **Error**: No Python error — silent failure
- **Probable Cause**: Passed `destinationId` as int (converted from hex string).
  While API accepts int, the hex string format (`"!07c01855"`) is what all
  internal Meshtastic examples use. Int conversion may lose leading zeros or
  cause routing lookup failure.
- **Quick Fix**: Pass `self.peer_id` directly (already a hex string from packet)
- **Permanent Fix**: Always use hex string format for `destinationId`
- **Status**: Fixed in v1.1

---

## Issue 007 — Portnum String Mismatch on Receive

- **Context**: Receiving packets with custom portnum 256
- **Symptom**: Receiver never matches incoming compressed packets
- **Error**: No error — portnum check silently fails
- **Probable Cause**: `decoded["portnum"]` returns `"PRIVATE_APP"` (the protobuf
  enum name), not `"256"`. Code was checking for `"256"` as a string.
- **Quick Fix**: Add `portnum == "PRIVATE_APP"` to match conditions
- **Permanent Fix**: Check enum name as primary, integer as fallback
- **Status**: Fixed in v1.1

---

## Issue 008 — State Machine Phase Drift (v2.0 Independent Loops)

- **Context**: First live LoRa test of Experiment B (MUX Grid codec, v2.0)
- **Symptom**: Both nodes ran to completion, but only 1 of 8 messages
  roundtripped per side. DBG logs showed PRIVATE_APP packets arriving
  AFTER the receiving side had already timed out and moved to next step.
- **Error**: No error — packets were delivered, but arrived outside the
  receive window.
- **Root cause (two bugs, same fix)**:
  1. Trigger packet consumed by LISTENING→TRIGGERED state transition.
     `_receive_compressed(0, ...)` then clears the buffer and waits
     fresh for data that already arrived. 15s wasted on Step 1.
  2. Both nodes used independent `for` loops with `time.sleep(3)`
     between steps. No synchronization between them. After the 15s
     timeout on Step 1, every subsequent step is further out of phase.
     Both sides keep sending while the other isn't yet listening.
- **Why Steps 7-8 worked**: Drift accumulated to exactly one cycle
  offset by step 7, accidentally re-aligning the two nodes. This
  confirmed the radio pipe and codec were both working correctly.
- **Quick Fix**: Make the protocol reactive instead of timed.
  Send-then-block: after TX, block on `msg_event.wait(timeout=15)`.
  After RX (or timeout), immediately TX the next message. No sleep().
- **Permanent Fix** (v2.1):
  1. `trigger_data_is_step1` flag preserves trigger packet as Step 1
  2. Reactive send-then-block loop (radio latency = pacer)
  3. Timeout = skip-one-RX, proceed to next TX (re-syncs naturally)
- **Status**: Fixed in v2.1

---

*Append new issues below.*
