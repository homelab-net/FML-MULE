# SPDX-License-Identifier: Apache-2.0
# Ported from siara-cc/Unishox2, unishox2.c at commit
# 4981d9403de3bdd1938a635ab73f8a2c5a536059, Copyright (C) 2020 Siara Logics
# (cc), author Arundale Ramanathan, licensed under the Apache License 2.0.
# Only the default-preset decoder is ported; the encoder is not.
"""Bounded, pure-Python Unishox2 decoder for upstream TAKPacket strings.

Upstream Meshtastic TAK senders (OpenTAKServer's encoder, the TAK Meshtastic
Gateway's chats) compress `TAKPacket` strings with Unishox2 and set
`is_compressed`. The bench gateway (`fml-lora-gw.py`) must read them.

Interface contract: `decode(data, max_bytes)` returns the whole decoded string,
or raises `Unishox2Error`. It never returns a partial result, never produces
more than `max_bytes` of UTF-8, and never reads past `data`. The result is
the same string the reference C decoder produces for any input the reference
encoder can emit; input it cannot emit (an overlapping repeat, invalid UTF-8)
is refused.

Why a port rather than the C library: a receiver must bound the decoded size by
its own limits (upstream's field sizes), whatever the packet implies, and a
pure-Python decoder runs in CI, which has no C toolchain for the binding.

Resource budget: linear in the output, which is capped by `max_bytes`; no
allocation beyond one bytearray of at most `max_bytes`. Owner and sustainment:
the bench gateway's owner; it changes only if Unishox2's default preset does.
"""

from __future__ import annotations

__all__ = ["Unishox2Error", "decode"]


class Unishox2Error(ValueError):
    """Input is not a decodable Unishox2 string within the given bound."""


_ALPHA, _SYM, _NUM, _DICT, _DELTA = 0, 1, 2, 3, 4

# Character sets; 0 marks a position handled in code. Laid out as in the
# reference source so the two can be compared line by line.
# fmt: off
_SETS = (
    (0, 32, 101, 116, 97, 111, 105, 110, 115, 114, 108, 99, 100, 104, 117, 112, 109,
     98, 103, 119, 102, 121, 118, 107, 113, 106, 120, 122),
    (34, 123, 125, 95, 60, 62, 58, 10, 0, 91, 93, 92, 59, 39, 9, 64, 42, 38,
     63, 33, 94, 124, 13, 126, 96, 0, 0, 0),
    (0, 44, 46, 48, 49, 57, 50, 53, 45, 47, 51, 52, 54, 55, 56, 40, 41, 32,
     61, 43, 36, 37, 35, 0, 0, 0, 0, 0),
)

# fmt: on

# Default preset (USX_PSET_DFLT).
_HCODES = (0x00, 0x40, 0x80, 0xC0, 0xE0)
_HCODE_LENS = (2, 2, 2, 3, 3)
_FREQ_SEQ = (b'": "', b'": ', b"</", b'="', b'":"', b"://")
_TEMPLATES = (
    b"tfff-of-tfTtf:rf:rf.fffZ",
    b"tfff-of-tf",
    b"(fff) fff-ffff",
    b"tf:rf:rf",
    None,
)

#: Bits per template placeholder: hex nibble (f, F), 3-bit (r), 2-bit (t), 1-bit (o).
_TEMPLATE_WIDTH = {ord("f"): 4, ord("F"): 4, ord("r"): 3, ord("t"): 2, ord("o"): 1}

_VSECTIONS = (0x7F, 0xBF, 0xDF, 0xEF, 0xFF)
_VSECTION_POS = (0, 4, 8, 12, 20)
_VSECTION_MASK = (0x7F, 0x3F, 0x1F, 0x0F, 0x0F)
_VSECTION_SHIFT = (5, 4, 3, 1, 0)
# fmt: off
_VCODE_LOOKUP = (
    (1 << 5) + 0, (1 << 5) + 0, (2 << 5) + 1, (2 << 5) + 2,
    (3 << 5) + 3, (3 << 5) + 4, (3 << 5) + 5, (3 << 5) + 6,
    (3 << 5) + 7, (3 << 5) + 7, (4 << 5) + 8, (4 << 5) + 9,
    (5 << 5) + 10, (5 << 5) + 10, (5 << 5) + 11, (5 << 5) + 11,
    (5 << 5) + 12, (5 << 5) + 12, (6 << 5) + 13, (6 << 5) + 14,
    (6 << 5) + 15, (6 << 5) + 15, (6 << 5) + 16, (6 << 5) + 16,
    (6 << 5) + 17, (6 << 5) + 17, (7 << 5) + 18, (7 << 5) + 19,
    (7 << 5) + 20, (7 << 5) + 21, (7 << 5) + 22, (7 << 5) + 23,
    (7 << 5) + 24, (7 << 5) + 25, (7 << 5) + 26, (7 << 5) + 27,
)
# fmt: on
_LEN_MASKS = (0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE, 0xFF)
_COUNT_BIT_LENS = (2, 4, 7, 11, 16)
_COUNT_ADDER = (4, 20, 148, 2196, 67732)
_UNI_BIT_LEN = (6, 12, 14, 16, 21)
_UNI_ADDER = (0, 64, 4160, 20544, 86080)
_NICE_LEN = 5
_MAGIC_BIT_LEN = 1
_SPECIAL = 0x7FFFFF00  # readUnicode's marker for a special code
_END = 99  # the reference decoder's "no match" index


class _Bits:
    """Bit reader over the input, bounds-checked."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.len = len(data) * 8
        self.pos = _MAGIC_BIT_LEN

    def bit(self, n: int) -> int:
        return (self.data[n >> 3] >> (7 - (n & 7))) & 1 if n < self.len else 0

    def code8(self, n: int) -> int:
        """Next 8 bits from n, padded with 1s past the end (read8bitCode)."""
        shift = n & 7
        pos = n >> 3
        code = (self.data[pos] << shift) & 0xFF
        if pos + 1 < len(self.data):
            code |= self.data[pos + 1] >> (8 - shift)
        else:
            code |= 0xFF >> (8 - shift)
        return code

    def vcode(self) -> int:
        if self.pos >= self.len:
            return _END
        code = self.code8(self.pos)
        for i, top in enumerate(_VSECTIONS):
            if code <= top:
                pos = _VSECTION_POS[i] + (
                    (code & _VSECTION_MASK[i]) >> _VSECTION_SHIFT[i]
                )
                v = _VCODE_LOOKUP[pos]
                self.pos += (v >> 5) + 1
                return _END if self.pos > self.len else v & 0x1F
        return _END

    def hcode(self) -> int:
        if self.pos >= self.len:
            return _END
        code = self.code8(self.pos)
        for i in range(5):
            if (code & _LEN_MASKS[_HCODE_LENS[i] - 1]) == _HCODES[i]:
                self.pos += _HCODE_LENS[i]
                return i
        return _END

    def step(self, limit: int) -> int:
        idx = 0
        while self.pos < self.len and self.bit(self.pos):
            idx += 1
            self.pos += 1
            if idx == limit:
                return idx
        if self.pos >= self.len:
            return _END
        self.pos += 1
        return idx

    def num(self, n: int, count: int) -> int:
        """`count` bits from n as an integer, or -1 if the input ends first."""
        if n + count > self.len:
            return -1
        value = 0
        for i in range(count):
            value = (value << 1) | self.bit(n + i)
        return value

    def count(self) -> int:
        idx = self.step(4)
        if idx == _END or self.pos + _COUNT_BIT_LENS[idx] - 1 >= self.len:
            return -1
        adder = _COUNT_ADDER[idx - 1] if idx else 0
        value = self.num(self.pos, _COUNT_BIT_LENS[idx]) + adder
        self.pos += _COUNT_BIT_LENS[idx]
        return value

    def unicode(self) -> int:
        idx = self.step(5)
        if idx == _END:
            return _SPECIAL + _END
        if idx == 5:
            return _SPECIAL + self.step(4)
        sign = self.bit(self.pos)
        self.pos += 1
        if self.pos + _UNI_BIT_LEN[idx] - 1 >= self.len:
            return _SPECIAL + _END
        value = self.num(self.pos, _UNI_BIT_LEN[idx]) + _UNI_ADDER[idx]
        self.pos += _UNI_BIT_LEN[idx]
        return -value if sign else value


class _Out:
    """Output buffer that refuses to grow past its bound."""

    def __init__(self, limit: int) -> None:
        self.buf = bytearray()
        self.limit = limit

    def put(self, b: bytes | int) -> None:
        add = 1 if isinstance(b, int) else len(b)
        if len(self.buf) + add > self.limit:
            raise Unishox2Error(f"decoded string exceeds {self.limit} bytes")
        if isinstance(b, int):
            self.buf.append(b)
        else:
            self.buf += b

    def utf8(self, uni: int) -> None:
        """writeUTF8, byte for byte: C truncates each byte to 8 bits.

        Out-of-range or overlong results are not refused here; they are not
        UTF-8, so `_finish` refuses them, as the reference binding does.
        """
        if uni < (1 << 11):
            seq = (0xC0 + (uni >> 6), 0x80 + (uni & 0x3F))
        elif uni < (1 << 16):
            seq = (0xE0 + (uni >> 12), 0x80 + ((uni >> 6) & 0x3F), 0x80 + (uni & 0x3F))
        else:
            seq = (
                0xF0 + (uni >> 18),
                0x80 + ((uni >> 12) & 0x3F),
                0x80 + ((uni >> 6) & 0x3F),
                0x80 + (uni & 0x3F),
            )
        self.put(bytes(b & 0xFF for b in seq))

    def repeat(self, bits: _Bits) -> bool:
        """Copy a dictionary repeat (decodeRepeat without prev_lines).

        Returns False where the reference decoder stops.
        """
        length = bits.count() + _NICE_LEN
        if length < _NICE_LEN:
            return False
        dist = bits.count() + _NICE_LEN - 1
        if dist < _NICE_LEN - 1:
            return False
        start = len(self.buf) - dist
        if start < 0:
            return False
        if dist < length:
            raise Unishox2Error("overlapping repeat")
        self.put(bytes(self.buf[start : start + length]))
        return True


def _hex(nibble: int, upper: bool) -> int:
    if nibble <= 9:
        return 48 + nibble
    return (65 if upper else 97) + nibble - 10


def _number_escape(bits: _Bits, out: _Out) -> bool:
    """Template, binary or hex run after USX_NUM vcode 0. False ends decoding."""
    idx = bits.step(5)
    if idx == _END:
        return False
    if idx == 0:
        idx = bits.step(4)
        if idx >= 5:
            return False
        rem = bits.count()
        tpl = _TEMPLATES[idx]
        if rem < 0 or tpl is None or rem > len(tpl):
            return False
        for t in tpl[: len(tpl) - rem]:
            if t in b"frtoF":
                width = _TEMPLATE_WIDTH[t]
                raw = bits.num(bits.pos, width)
                if raw < 0:
                    return False
                out.put(_hex(raw, t != ord("f")))
                bits.pos += width
            else:
                out.put(t)
        return True
    if idx == 5:
        n = bits.count()
        if n <= 0:
            return False
        for _ in range(n):
            raw = bits.num(bits.pos, 8)
            if raw < 0:
                return False
            out.put(raw)
            bits.pos += 8
        return True
    n = 32 if idx in (2, 4) else bits.count()
    if n <= 0:
        return False
    while n:
        nib = bits.num(bits.pos, 4)
        if nib < 0:
            return False
        out.put(_hex(nib, idx >= 3))
        if idx in (2, 4) and n in (25, 21, 17, 13):
            out.put(45)
        bits.pos += 4
        n -= 1
    return True


def decode(data: bytes, max_bytes: int) -> str:
    """Decode a Unishox2 (default preset) string of at most max_bytes UTF-8 bytes."""
    if max_bytes < 0:
        raise ValueError("max_bytes must be non-negative")
    bits = _Bits(bytes(data))
    out = _Out(max_bytes)
    dstate = h = _ALPHA
    all_upper = False
    prev_uni = 0
    while bits.pos < bits.len:
        if dstate == _DELTA or h == _DELTA:
            if dstate != _DELTA:
                h = dstate
            delta = bits.unicode()
            if (delta >> 8) == (_SPECIAL >> 8):
                spl = delta & 0xFF
                if spl == _END:
                    break
                if spl == 0:
                    out.put(32)
                    continue
                if spl == 1:
                    h = bits.hcode()
                    if h == _END:
                        bits.pos = bits.len
                        continue
                    if h in (_DELTA, _ALPHA):
                        dstate = h
                        continue
                    if h == _DICT:
                        if not out.repeat(bits):
                            return _finish(out)
                        h = dstate
                        continue
                elif spl in (2, 3, 4):
                    out.put((44, 46, 10)[spl - 2])
                    continue
            else:
                prev_uni += delta
                out.utf8(prev_uni)
            if dstate == _DELTA and h == _DELTA:
                continue
        else:
            h = dstate
        upper = all_upper
        v = bits.vcode()
        if v == _END or h == _END:
            break
        if v == 0 and h != _SYM:
            if bits.pos >= bits.len:
                break
            if h != _NUM or dstate != _DELTA:
                h = bits.hcode()
                if h == _END or bits.pos >= bits.len:
                    break
            if h == _ALPHA:
                if dstate != _ALPHA:
                    dstate = _ALPHA
                    continue
                if all_upper:
                    upper = all_upper = False
                    continue
                v = bits.vcode()
                if v == _END:
                    break
                if v == 0:
                    h = bits.hcode()
                    if h == _END:
                        break
                    if h == _ALPHA:
                        all_upper = True
                        continue
                upper = True
            elif h == _DICT:
                if not out.repeat(bits):
                    break
                continue
            elif h == _DELTA:
                continue
            else:
                if h != _NUM or dstate != _DELTA:
                    v = bits.vcode()
                if v == _END:
                    break
                if h == _NUM and v == 0:
                    if not _number_escape(bits, out):
                        break
                    if dstate == _DELTA:
                        h = _DELTA
                    continue
        if upper and v == 1:
            h = dstate = _DELTA
            continue
        c = _SETS[h][v] if h < 3 and v < 28 else 0
        if 97 <= c <= 122:
            dstate = _ALPHA
            if upper:
                c -= 32
        elif 48 <= c <= 57:
            dstate = _NUM
        elif c == 0:
            if v == 8:
                out.put(b"\r\n")
            elif h == _NUM and v == 26:
                n = bits.count()
                if n < 0:
                    break
                if not out.buf:
                    return ""
                last = out.buf[-1]
                out.put(bytes([last]) * (n + 4))
            elif h == _SYM and v > 24:
                out.put(_FREQ_SEQ[v - 25])
            elif h == _NUM and 22 < v < 26:
                out.put(_FREQ_SEQ[v - 20])
            else:
                break
            if dstate == _DELTA:
                h = _DELTA
            continue
        if dstate == _DELTA:
            h = _DELTA
        out.put(c)
    return _finish(out)


def _finish(out: _Out) -> str:
    try:
        return out.buf.decode("utf-8")
    except UnicodeDecodeError as e:
        raise Unishox2Error("decoded bytes are not UTF-8") from e
