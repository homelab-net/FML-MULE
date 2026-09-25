# TBR-RF-03 decision packet: the EUD access-point band, channel, and EIRP

**State:** `DECIDED` (Owner, 2026-09-21). The Owner set the access-point RF
parameters for the `us-915` region profile (see section 9); they are written to
`regions/us-915/profile.yml` and the `mule-v001` AP-only target now resolves
(`gen-config ... --node mule-v001 --check` exit 0). This records the AP-params
sub-decision only; `TBR-RF-03`'s radio-consolidation/hardware half stays OPEN.

**Trade:** `TBR-RF-03`. **Prepared:** 2026-09-21. **Author:** Claude agent.
**Scope note:** this settles the AP's **RF parameters only** -- a
regulatory/planning decision -- **not** the trade's hardware-gated *consolidation*
question (whether AP and mesh share one radio), which stays open and
`requires-hardware: yes`.

## 1. Why this is on the critical path now

`tools/gen-config.py --check` refuses to resolve the region because
`wifi.ap_channel` and `wifi.max_eirp_dbm` are `TBD` (`No region profile is
resolvable yet`). That refusal is deliberate -- "do not invent an RF/regulatory
value" as code. So the whole v0.0.1 slice is blocked here: **without the AP band /
channel / EIRP, GAP-09E cannot render the AP config, and 09G/H/I cannot follow.**
These are the only AP-side parameters the AP-only target needs, and they are a
paper decision, decidable now, independent of any hardware.

## 2. Governing constraints

- `REGULATORY.md`: no `os/config/` file hardcodes a band, channel, or power; the
  region profile supplies them. Antenna gain raises radiated power; unlicensed
  operation still imposes power and interference obligations. The AP is
  unlicensed Wi-Fi under **47 CFR Part 15** (2.4 GHz: 15.247; 5 GHz UNII: 15.407).
- `FML-ADR-045`: separate physical radios are the planning baseline; consolidation
  is this trade's *hardware* question (not decided here).
- Onboard AP radio is single-stream (CYW43455 class); achievable EIRP is bounded
  by that radio + the chosen antenna (a hardware confirmation, `TBR-RF-03`'s
  hardware half).

## 3. Options and cost-benefit

### Band (`permitted_bands` + which the AP uses)

| Band | Pros | Cons | Cost / benefit |
| --- | --- | --- | --- |
| **2.4 GHz** | Best range + wall/rubble penetration; ubiquitous EUD support; **no DFS** | Congested band; lower throughput; only 3 non-overlapping channels (1/6/11) | **Reach for free**; the cost is throughput (fine for low-bandwidth tiles/ZIM; video is deferred) |
| **5 GHz** | Higher throughput; far less congested; many channels | Shorter range, worse penetration; **DFS** on parts of UNII (radar-avoidance complexity + brief channel unavailability) | Pay in range + DFS complexity to *buy* throughput the v0.0.1 content does not yet need |
| **Dual-band** | Covers both use profiles | Two channels to manage; on a single-stream radio, still one active at a time per client | Most flexible, most config surface; premature for v0.0.1 |

### Channel

- **2.4 GHz:** one of the non-overlapping **1 / 6 / 11**; pick to avoid the local
  noise floor. No DFS.
- **5 GHz:** prefer a **non-DFS UNII-1 (36/40/44/48)** channel to avoid radar
  detection; DFS channels add complexity and a startup listen delay.
- **Coexistence lever:** keeping the AP on **2.4 GHz** leaves the (likely 5 GHz)
  high-rate mesh band clear -- which *reduces* the AP-vs-mesh contention that the
  consolidation question is about, and is data that informs it.

### EIRP (`max_eirp_dbm`)

**Sourced ceilings (why band and EIRP interact):** FCC Part 15.247 allows
**36 dBm** EIRP (point-to-multipoint) on 2.4 GHz and on 5 GHz **UNII-3**
(5725-5850 MHz); Part 15.407 caps 5 GHz **UNII-1** (5150-5250 MHz) at **30 dBm**.
So a UNII-3 primary matches 2.4's ceiling, and dropping to 2.4 buys **propagation**
(more coverage per watt), not EIRP headroom -- which is exactly why "5 GHz unless
coverage/EIRP too low, then 2.4" is sound.

The value is chosen **within the Part 15 ceiling for the band** and is bounded by
the radio + antenna. The cost-benefit is monotonic and worth stating plainly:

| Higher EIRP | Lower EIRP |
| --- | --- |
| + more coverage / range | + longer battery runtime (`TBR-PWR-01`) |
| - more battery draw | + less self-interference with the mesh |
| - more co-channel interference / contention | + smaller RF footprint (OPSEC; SSID is already hidden) |
| - larger detectable signature | - less reach |

A **moderate** operating EIRP (well below the regulatory ceiling) usually wins for
a battery-powered field node: it buys adequate scene coverage without spending
runtime, raising the noise floor for the mesh, or advertising the node.

## 4. Recommendation (the Owner decides)

For the v0.0.1 slice and the disaster-response CONOPS (reach responders' phones at
a scene, often through obstacles):

- **Band: 2.4 GHz.** Range and penetration are the priority; the throughput cost
  is acceptable because the milestone content (Martin tiles, Kiwix ZIM) is
  low-bandwidth and video is deferred. It is DFS-free and keeps the 5 GHz mesh
  band clear.
- **Channel: 1, 6, or 11** (non-overlapping), chosen against the local noise
  floor; **`dfs_required: false`**.
- **EIRP: a moderate value within the Part 15 2.4 GHz ceiling**, sized for scene
  coverage rather than maximum range, to protect battery runtime and mesh
  coexistence. The exact number is bounded by the CYW43455-class radio + antenna
  and is **confirmed on hardware** (`TBR-RF-03` hardware half); set a conservative
  planning value now so `gen-config` resolves.

Alternative: **5 GHz** if throughput / on-AP video to nearby EUDs is prioritized
over reach, accepting shorter range and DFS handling.

## 5. Consequences

- **Unblocks the slice:** once these four fields are set in `regions/us-915/profile.yml`,
  `gen-config` resolves the AP-only target -> **09E renders** -> 09G/H/I proceed;
  the slice can demo on the x86 dev article or the live AP bench.
- **Does not resolve consolidation** (AP+mesh one radio) -- that stays open and
  hardware-gated; this only sets the AP's own RF params.
- **Regulatory:** confirm the chosen values against `REGULATORY.md` and current
  Part 15, accounting for antenna gain; the planning EIRP must be achievable on
  the selected radio/antenna (hardware confirmation).

## 6. Reversibility and smallest safe prototype

Fully reversible: these are region-profile values, changed by editing the profile
and re-running `gen-config`. Smallest prototype: with the values set, render the AP
config and bring an AP up on the dev article / live bench and associate a phone --
no mesh, no field radios.

## 7. Files that change AFTER approval (not now)

`regions/us-915/profile.yml`: set `wifi.permitted_bands`, `wifi.ap_channel`,
`wifi.max_eirp_dbm`, `wifi.dfs_required`, and `wifi.source` (the regulatory basis).
Then `gen-config` resolves the AP-only target and GAP-09E can render.

## 8. Sources reviewed

`tools/gen-config.py` (refuse-on-TBD), `regions/us-915/profile.yml`,
`REGULATORY.md` (Part 15 posture, antenna-gain note), `docs/trades/TBR-RF-03-*.md`,
`FML-ADR-045`, `FML-ADR-025`; 47 CFR Part 15.247 (2.4 GHz) / 15.407 (5 GHz UNII).

## 9. Owner disposition

**`DECIDED` (Owner, 2026-09-21): baseline dual-band, 5 GHz preferred, migrate to
2.4 GHz when achievable EIRP / coverage on 5 GHz is inadequate.**

Written to `regions/us-915/profile.yml`:

- `permitted_bands: ["2.4GHz", "5GHz"]` -- dual-band baseline.
- `ap_channel: 149` -- 5 GHz UNII-3 (non-DFS, outdoor-permitted) as the preferred
  primary; the Owner may override the specific channel.
- `max_eirp_dbm: 36` -- the FCC 47 CFR 15.247 P2MP regulatory ceiling (applies to
  UNII-3 and the 2.4 fallback); the **regulatory maximum, not** the operating
  power, which is hardware-bounded and set well below it.
- `dfs_required: false` -- ch 149 and the 2.4 fallback (1/6/11) are non-DFS.

**Result:** `gen-config --region us-915 --mission <package> --node mule-v001
--check` now reports "all required parameters are resolved" (exit 0). The v0.0.1
AP-only slice is
RF-unblocked and GAP-09E can render the AP RF config. The whole-profile check still
shows HaLow/LoRa/mesh `TBD` (`TBR-RF-02`/`TBR-RF-01`) -- correct, because
`mule-v001` does not field those bearers (`FML-ADR-075`).

**Residuals, flagged not invented:**

- The **2.4 GHz migration trigger is hardware-measured** -- the "too low" coverage
  floor is quantified on real hardware (`TBR-RF-03`'s hardware half). Both bands
  are permitted, so the fallback is a re-point of `ap_channel`, not a re-approval.
- The **operating EIRP** (hostapd tx power) is bounded by the AP radio + antenna
  and confirmed on hardware; `max_eirp_dbm` here is only the regulatory cap.
- The **channel pick (149)** is a recommendation, overridable by the Owner.

This does **not** close `TBR-RF-03`; its radio-consolidation/hardware half remains
OPEN.
