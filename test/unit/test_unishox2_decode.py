"""Tests for test/bench/unishox2_decode.py, the bounded Unishox2 decoder.

The vectors were produced by the reference C library (see test/unit/data); the
decoder must reproduce them exactly, stay within its bound on any input, and
fail only with its own error.
"""

from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "unishox2_decode", _ROOT / "test" / "bench" / "unishox2_decode.py"
)
assert _SPEC is not None and _SPEC.loader is not None
u = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = u
_SPEC.loader.exec_module(u)

_VECTORS = json.loads(
    (_ROOT / "test" / "unit" / "data" / "unishox2_vectors.json").read_text("utf-8")
)["vectors"]

#: Found by the bench differential fuzz: a repeat whose source overlaps the
#: bytes it is about to write, which the reference encoder never produces.
OVERLAPPING_REPEAT = "bcf40d4839936842d7c75fb5540a9107b7d9f0"


def test_every_reference_vector_decodes_exactly() -> None:
    assert len(_VECTORS) >= 400
    for v in _VECTORS:
        text = v["text"]
        assert u.decode(bytes.fromhex(v["hex"]), len(text.encode("utf-8"))) == text


def test_the_bound_is_exact_not_approximate() -> None:
    for v in _VECTORS:
        n = len(v["text"].encode("utf-8"))
        if n:
            with pytest.raises(u.Unishox2Error):
                u.decode(bytes.fromhex(v["hex"]), n - 1)


def test_a_high_ratio_string_over_the_bound_is_refused() -> None:
    blob = next(bytes.fromhex(v["hex"]) for v in _VECTORS if v["text"] == "x" * 120)
    assert len(blob) <= 8  # a few bytes on the air expand to 120
    with pytest.raises(u.Unishox2Error, match="exceeds 100"):
        u.decode(blob, 100)


def test_an_overlapping_repeat_is_refused() -> None:
    with pytest.raises(u.Unishox2Error, match="overlapping"):
        u.decode(bytes.fromhex(OVERLAPPING_REPEAT), 1 << 20)


def test_random_input_stays_bounded_and_fails_only_with_its_own_error() -> None:
    rng = random.Random(20261023)  # noqa: S311 (seeded test input, not crypto)
    for _ in range(3000):
        data = bytes(rng.getrandbits(8) for _ in range(rng.randint(0, 231)))
        try:
            out = u.decode(data, 200)
        except u.Unishox2Error:
            continue
        assert len(out.encode("utf-8")) <= 200


def test_a_negative_bound_is_a_caller_error() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        u.decode(b"\x97", -1)
