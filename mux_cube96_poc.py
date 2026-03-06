#!/usr/bin/env python3
"""
MUX Cube 96³ — 3D Content-Addressable Memory Codec
CyberMesh / Liberty Mesh
 — Mark Snow / Mindtech

Bit layout (byte-aligned, 1 flag per byte):
  Byte 0: [F0 | x6 x5 x4 x3 x2 x1 x0]   F0 = namespace (0=static, 1=meshlex)
  Byte 1: [F1 | y6 y5 y4 y3 y2 y1 y0]   F1 = hyperedge  (0=word, 1=phrase) [reserved]
  Byte 2: [F2 | z6 z5 z4 z3 z2 z1 z0]   F2 = capitalized (0=lower, 1=cap)

Extraction:  x = byte0 & 0x7F   (single AND, no cross-byte ops)
Packing:     byte0 = (f0 << 7) | x

96³ = 884,736 cells per namespace
2 namespaces (static + meshlex) = 1,769,472 addressable words
3 bytes per word, fixed width, CSS burst predictable
"""
import hashlib, json, sys, time

CUBE_SIZE = 96
MAX_COORD = CUBE_SIZE - 1


def pack(x, y, z, f_namespace=0, f_hyperedge=0, f_capitalized=0):
    """Pack (x,y,z) + 3 flags into 3 bytes. One flag per byte high bit."""
    assert 0 <= x <= MAX_COORD and 0 <= y <= MAX_COORD and 0 <= z <= MAX_COORD
    return bytes([(f_namespace << 7) | x,
                  (f_hyperedge << 7) | y,
                  (f_capitalized << 7) | z])


def unpack(data):
    """Unpack 3 bytes into (x,y,z) + 3 flags. Zero cross-byte operations."""
    b0, b1, b2 = data[0], data[1], data[2]
    return {
        'x': b0 & 0x7F, 'y': b1 & 0x7F, 'z': b2 & 0x7F,
        'f_namespace': b0 >> 7, 'f_hyperedge': b1 >> 7, 'f_capitalized': b2 >> 7
    }


def word_to_coords(word, cube_size=CUBE_SIZE):
    """Deterministic word placement via SHA-256 hash."""
    h = hashlib.sha256(word.lower().encode('utf-8')).digest()
    return (h[0] % cube_size, h[1] % cube_size, h[2] % cube_size)


class MuxCube96:
    """3D content-addressable memory codec. 96x96x96 cube, 3 bytes/word."""

    def __init__(self, vocab=None):
        self.word_to_xyz = {}
        self.xyz_to_word = {}
        self.meshlex = {}
        self.meshlex_xyz = {}
        self.collisions = 0
        self.meshlex_adds = 0

        if vocab:
            for word in vocab:
                self._place_word(word.lower(), is_dynamic=False)

    def _place_word(self, word, is_dynamic=False):
        x, y, z = word_to_coords(word)
        attempts = 0
        while (x, y, z) in self.xyz_to_word or (x, y, z) in self.meshlex_xyz:
            z = (z + 1) % CUBE_SIZE
            attempts += 1
            if attempts >= CUBE_SIZE:
                y = (y + 1) % CUBE_SIZE
                attempts = 0
            self.collisions += 1

        if is_dynamic:
            self.meshlex[word] = (x, y, z)
            self.meshlex_xyz[(x, y, z)] = word
            self.meshlex_adds += 1
        else:
            self.word_to_xyz[word] = (x, y, z)
            self.xyz_to_word[(x, y, z)] = word

    def encode_word(self, word):
        is_cap = word[0].isupper() if word else False
        w = word.lower()

        if w in self.word_to_xyz:
            x, y, z = self.word_to_xyz[w]
            return pack(x, y, z, f_namespace=0, f_capitalized=int(is_cap))
        elif w in self.meshlex:
            x, y, z = self.meshlex[w]
            return pack(x, y, z, f_namespace=1, f_capitalized=int(is_cap))
        else:
            self._place_word(w, is_dynamic=True)
            x, y, z = self.meshlex[w]
            return pack(x, y, z, f_namespace=1, f_capitalized=int(is_cap))

    def decode_word(self, data):
        info = unpack(data)
        x, y, z = info['x'], info['y'], info['z']

        if info['f_namespace'] == 0:
            word = self.xyz_to_word.get((x, y, z), f"<UNK:{x},{y},{z}>")
        else:
            word = self.meshlex_xyz.get((x, y, z), f"<DYN_UNK:{x},{y},{z}>")

        if info['f_capitalized']:
            word = word.capitalize()
        return word

    def encode_message(self, text):
        words = text.split()
        encoded = b''
        for w in words:
            encoded += self.encode_word(w)
        return encoded

    def decode_message(self, data):
        words = []
        for i in range(0, len(data), 3):
            chunk = data[i:i+3]
            if len(chunk) == 3:
                words.append(self.decode_word(chunk))
        return ' '.join(words)

    def stats(self):
        return {
            'cube_size': CUBE_SIZE,
            'static_words': len(self.word_to_xyz),
            'meshlex_words': len(self.meshlex),
            'total_words': len(self.word_to_xyz) + len(self.meshlex),
            'capacity': CUBE_SIZE ** 3,
            'utilization': (len(self.word_to_xyz) + len(self.meshlex)) / (CUBE_SIZE ** 3),
            'collisions': self.collisions,
            'meshlex_adds': self.meshlex_adds,
        }


# ─── Self-Test ──────────────────────────────────────────────────────────────

DEMO_VOCAB = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "flood", "warning", "trenton", "water", "level", "evacuate", "emergency",
    "node", "relay", "battery", "status", "clear", "sector", "bridge", "river",
    "wind", "rain", "power", "down", "online", "offline", "signal", "strong",
    "liberty", "mesh", "gauge", "rising", "falling", "update", "confirmed",
    "negative", "affirmative", "standby", "over", "copy", "roger", "dispatch",
    "tornado", "hurricane", "earthquake", "shelter", "staging", "triage",
    "north", "south", "east", "west", "northeast", "northwest", "southeast",
    "southwest", "latitude", "longitude", "altitude", "bearing", "distance",
    "feet", "miles", "meters", "inches", "celsius", "fahrenheit", "barometer",
    "humidity", "visibility", "precipitation", "temperature", "pressure",
    "highway", "intersection", "route", "exit", "checkpoint", "perimeter",
    "boundary", "zone", "area", "region", "district",
]

TEST_MESSAGES = [
    "flood warning trenton water level rising",
    "Liberty node relay battery low status update",
    "emergency evacuate sector north bridge",
    "Tornado warning all nodes standby",
    "wind strong northeast visibility falling pressure low",
    "KD2ZYX relay confirmed signal strong over",
    "GPS 40.2194 74.7401 staging area checkpoint",
    "batt wtr lvl evac dmg gw offline",
]


def main():
    print("=" * 70)
    print("  MUX CUBE 96\u00b3 — 3D Content-Addressable Memory Codec")
    print("  CyberMesh / Liberty Mesh")
    print("=" * 70)

    cube = MuxCube96(vocab=DEMO_VOCAB)
    s = cube.stats()
    print(f"  Static vocab: {s['static_words']}  |  Capacity: {s['capacity']:,}  |  Collisions: {s['collisions']}")
    print()

    total_raw, total_enc = 0, 0
    all_pass = True

    for msg in TEST_MESSAGES:
        enc = cube.encode_message(msg)
        dec = cube.decode_message(enc)
        raw_b = len(msg.encode('utf-8'))
        enc_b = len(enc)
        ratio = raw_b / enc_b
        rt = dec.lower() == msg.lower()
        total_raw += raw_b
        total_enc += enc_b
        if not rt: all_pass = False

        status = "PASS" if rt else "FAIL"
        print(f"  [{status}] {ratio:.2f}:1  \"{msg}\"")
        print(f"         HEX: {enc.hex()}")
        if not rt:
            print(f"         GOT: \"{dec}\"")
        print()

    agg = total_raw / total_enc
    s2 = cube.stats()
    print("=" * 70)
    print(f"  Roundtrip: {'ALL PASS' if all_pass else 'FAILURES'}  |  Ratio: {agg:.3f}:1")
    print(f"  MeshLex adds: {s2['meshlex_adds']}  |  Total vocab: {s2['total_words']}")
    print(f"  Encoding: FIXED 3 bytes/word  |  Burst: PREDICTABLE")
    print("=" * 70)

    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
