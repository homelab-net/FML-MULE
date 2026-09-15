# RoIP gateway candidates: the analysis half

**Trade:** `TBR-VOICE-01`.
**Date:** 2026-09-15.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** analysis, no hardware. ITEP-C01 item 8, now
permitted because `CCR-03` is approved (2026-09-15). It compares the candidates
against the `CCR-03` section 11 criteria that do **not** need a radio or a CM4; it
does **not** select an implementation (that needs the hardware half and the named
owner's acceptance), and it closes nothing.

## Why this is possible now, and what stays out

`TBR-VOICE-01` could not be worked while `CCR-03` was unapproved -- "selecting an
implementation for an unadopted capability decides a consequence before its
cause." `CCR-03` is now approved, so the analysis half is in scope. The
measurement half stays out: measured RAM and CPU on the CM4 during a live session
alongside the service-host load (`TBR-COMP-01`), and one-way latency, jitter and
PTT acquisition/release on the mesh and over Tailscale, are hardware (GATE
VOICE-01). No number here is one of those.

## The candidates (`TBR-VOICE-01` options)

- **Thin FML-native**: ALSA capture/playback, Opus, an authenticated IP
  transport, serial-RTS PTT, with FML owning session, authorization and
  loop/arbitration.
- **SvxLink-class**: a mature amateur-radio linking stack.
- **AllStar / Asterisk-class**: a full linking platform.

## Against the `CCR-03` section 11 criteria (the no-hardware ones)

| Criterion | Thin FML-native | SvxLink-class | AllStar/Asterisk |
| --- | --- | --- | --- |
| Debian stable ARM64 | Yes (own code) | Packaged for Debian ARM64 | Packaged, heavier |
| USB audio / external PTT | Direct (ALSA + serial RTS) | Supported (USB audio, GPIO/serial PTT) | Supported via channel drivers |
| No mandatory public Internet | Yes by construction | Yes (local links, no reflector required) | Yes, but oriented to public nodes; needs deliberate lock-down |
| Local-first | Yes | Yes | Weaker; its model assumes a network of public nodes |
| Tailscale compatible | Yes (plain IP) | Yes (plain IP) | Yes (plain IP) |
| Authentication | FML owns it | Limited native; FML must wrap | Has its own; another identity system to reconcile (`TBR-ID-01`) |
| Manageable complexity | Highest control, most FML code to write | Moderate | Highest footprint and surface |
| Active maintenance | On FML | Active upstream | Active upstream |
| Avoid unnecessary custom code | Worst (writes the most) | Good | Good |

## The load-bearing question: single-egress enforceability (`FML-ADR-067`)

`FML-ADR-067` requires an operator to receive a linked session through exactly
one path, with no direct MULE-to-headset audio, self-echo suppression by
origin/session ID, and one active gateway per voice group per local net.

- The invariant is enforceable **around** any candidate, because the MULE owns
  the gateway radio and its PTT keying (`FML-ADR-066`): whatever the gateway
  software does internally, the MULE controls when its radio transmits, so a
  policy wrapper can hold the single-egress rule.
- The difference is **where** the rule lives. Thin FML-native owns it directly,
  in code FML tests. A framework requires FML to constrain it from outside and to
  prove the framework does not open a second audio path of its own (a reflector
  leg, a second channel) -- more surface to verify against `FML-ADR-067`.
- Voice-group gating (the criterion "FML mission policy can gate a voice group")
  is unbuilt for all three: the membership credential is `TBR-VOICE-02` /
  `TBR-SEC-01`, so no candidate can be credited with it yet.

## Footprint

Directionally, not measured: thin FML-native is smallest by construction (Opus
plus a thin transport); SvxLink is a moderate resident daemon; AllStar/Asterisk
is the largest, a full PBX. The **measured** resident set against loopback and
virtual peers, and the CM4 figure alongside the ~650 MB service plane
(`TBR-COMP-01`), is the bench/hardware step this analysis does not perform; for
the installable candidates it mirrors `test/bench/service-plane-footprint.sh`.

## Direction (not a selection)

Thin FML-native and SvxLink both satisfy the local-first, offline, ARM64 and
PTT criteria; AllStar/Asterisk is the weakest fit -- public-node-oriented and the
heaviest on a shared CM4. The real trade is thin-native (most control of the
`FML-ADR-067` invariant and of authentication, most code to write and maintain)
versus SvxLink (least custom code, but FML must wrap its policy and prove no
second audio path). The owner selects with the measured RAM/CPU/latency the
hardware half provides; this artifact narrows the field and frames that choice.

## What it is not

- **Not a selection**, and not an ADR: the gate needs the measured basis and the
  owner's acceptance (`CCR-03` section 11 comparison).
- **Not a footprint measurement**: the resident-set and CM4 numbers are hardware
  and bench work (`TBR-COMP-01`, GATE VOICE-01).
- **Not a latency/jitter/PTT result**: those need a radio (GATE VOICE-01).
- **Not a voice-group-gating verdict**: the credential is `TBR-VOICE-02` /
  `TBR-SEC-01`, unbuilt.

## Cross-references

- `docs/trades/TBR-VOICE-01-which-roip-gateway-implementation-thin-native-or-an-existing-framework.md`
  -- the trade and its closure gate.
- `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md` (approved) and
  its source section 11 selection criteria.
- `docs/adr/FML-ADR-067-an-operator-receives-linked-voice-through-exactly-one-audio-path.md`
  -- the single-egress invariant.
- `docs/architecture/roip-voice-data-flow.md` -- how the invariant plays out.
- `docs/trades/TBR-VOICE-02-how-is-voice-group-authorization-expressed-and-how-does-it-behave-across-a-mesh-merge.md`
  and `docs/trades/TBR-SEC-01-protected-storage-unlock.md` -- the voice-group
  credential the gating criterion depends on.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. See `SECURITY.md`.
