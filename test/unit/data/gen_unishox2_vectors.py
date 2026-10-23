#!/usr/bin/env python3
"""Generate unishox2_vectors.json with the reference C library (bench only).

  python gen_unishox2_vectors.py > unishox2_vectors.json

Needs the `unishox2-py3` binding, which CI does not have; the committed JSON is
what the tests read. Every string is synthetic. Each vector is decompressed to
its known length and kept only if it round-trips.
"""

import json
import random
import sys
from importlib.metadata import version

import unishox2

FIXED = [
    "",
    "a",
    "A",
    "FML-ALPHA",
    "fml-bench-gw",
    "All Chat Rooms",
    "Team Lead",
    "FML-UID-RF-5F44AFBD",
    "ANDROID-0123456789abcdef",
    "GeoChat.FML-UID-ALPHA.All Chat Rooms",
    "c0ffee12-3456-7890-abcd-ef0123456789",
    "2026-10-23T14:32:36.000Z",
    "2026-10-23",
    "(555) 012-3456",
    "14:32:36",
    "deadbeefcafebabe",
    "DEADBEEFCAFEBABE",
    "x" * 120,
    "ab" * 40,
    "repeat repeat repeat repeat",
    "HELLO WORLD",
    "Hello World",
    "MiXeD cAsE 123",
    '{"k": "v", "n": 1}',
    "</a>",
    'href="x"',
    "https://example.org/x",
    "line1\nline2\r\nline3\ttab",
    "\x01\x02 binary-ish \x7f",
    "cafe café",
    "naïve façade",
    "日本語のテキスト",
    "Привет, мир",
    "emoji \U0001f642\U0001f44d",
    "Ω≈ç√∫",
    "a" * 300,
    "1234567890" * 6,
    "Meet at grid 12345 67890 at 1400",
    "ACK",
    "?!@#$%^&*()_+-=[]{};':\",./<>",
]
PALETTES = [
    "abcdefghijklmnopqrstuvwxyz ",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.",
    "0123456789abcdef-",
    "abcABC 012.,;:!?'\"()[]{}<>/\\@#$%&*+=~`|^\n\t",
    "aéüßçñ日本語" + "Привет\U0001f642 ",
]


def vector(text: str) -> dict | None:
    """Compress text; keep it only if it decompresses back exactly."""
    blob, _ = unishox2.compress(text)
    n = len(text.encode("utf-8"))
    if unishox2.decompress(blob, n) != text:
        return None
    return {"text": text, "hex": blob.hex()}


def main() -> None:
    """Write the vector file to stdout."""
    rng = random.Random(20261023)  # noqa: S311 (seeded test corpus, not crypto)
    texts = list(FIXED)
    for _ in range(400):
        pal = rng.choice(PALETTES)
        texts.append("".join(rng.choice(pal) for _ in range(rng.randint(1, 120))))
    out, dropped = [], 0
    for t in texts:
        v = vector(t)
        if v is None:
            dropped += 1
        else:
            out.append(v)
    json.dump(
        {
            "generator": "test/unit/data/gen_unishox2_vectors.py",
            "library": f"unishox2-py3 {version('unishox2-py3')}",
            "seed": 20261023,
            "dropped_not_round_tripping": dropped,
            "vectors": out,
        },
        sys.stdout,
        ensure_ascii=False,
        indent=0,
    )
    sys.stdout.write("\n")


main()
