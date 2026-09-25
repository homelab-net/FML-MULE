# GAP-09E execution card: Raspberry Pi EUD AP bring-up

## Finding and authority

- **Finding:** GAP-09E, AP-only network rendering (P1) -- the hardware half.
- **Governing records:** `FML-ADR-084` (onboarding two-BSS boundary),
  `FML-ADR-057` (operational BSS non-isolated), `FML-ADR-083` (the runtime
  oneshot renders config), `FML-ADR-045` (AP is a separate logical radio),
  `FML-ADR-021`/`022`/`040` (compute + compatibility set), PR #177 (the `us-915`
  AP band/channel/EIRP), `TBR-LINUX-01` (driver AP-mode and multi-BSS behavior),
  `TBR-RF-03` (AP RF, hardware half), `TBR-HW-01`.
- **Owner input:** a used Raspberry Pi 8 GB is acquired the weekend of
  2026-09-27; the region is the United States (`country_code: US`).
- **Boundary:** this is the first arm64 bench article and a proxy for the CM4
  field node (`docs/bench-service-bringup.md`); it is **not** a production compute
  selection, a hardware qualification, or permission to close `TBR-LINUX-01`,
  `TBR-RF-03`, or GAP-09E. It converts `SIMULATED` render intent into the first
  real-RF evidence for the EUD AP.

## Status

Every step here is a **procedure to run, not a result**. Nothing becomes
`HARDWARE-VERIFIED` until it is run on the Pi and its evidence is recorded under
`docs/evidence/`. None of this runs in CI: a hosted runner has no wireless stack
(`docs/dev-machine.md`). Run on the Pi as root. This card is the M1 dry run
(`ROADMAP-DEV.md`: one node, its EUD AP, one service to a phone).

## Rules that apply to every step

- **Single step first** (`docs/bench-hardware-bringup.md`): prove one BSS and one
  associated phone before attempting the second (onboarding) BSS. Multi-BSS is the
  interesting case; a working single AP is the boring case that must pass first.
- **Select the radio by driver, never by name.** Read the onboard Wi-Fi from the
  device tree under `/sys` by driver; do not grep interface names (a fuzzy match
  once grabbed a real WAN radio).
- **Record provenance** with every result: `uname -r`, the board model, the radio
  chip and driver, and the image build. Fixtures captured go in `test/fixtures/`
  with that metadata.
- **Region is a parameter.** Use the decided values from `regions/us-915/profile.yml`
  (channel 149, 5 GHz, non-DFS, `country_code: US`); do not type ad-hoc RF values.

## Steps

### Step 1 -- Article and radio inventory (provenance)

Flash Debian arm64 to the Pi; boot; record `uname -r`, `/proc/device-tree/model`,
the Wi-Fi chip and its driver (`/sys/class/net/*/device/uevent`), and the mkosi
image build if the MULE image is used. Record whether the chip is the CYW43455
class named in the `TBR-RF-03` AP packet, or the Pi 5's radio.

### Step 2 -- Regulatory domain (`country_code: US`)

Set and confirm the regdomain: `iw reg set US`; record `iw reg get` and the
per-channel constraints it reports for 5 GHz. Confirm ch 149 (UNII-3) is
permitted and non-DFS in the US domain, matching `regions/us-915/profile.yml`.
Record the effective EIRP ceiling the domain allows against the profile's
`ap_max_eirp_dbm: 36`.

### Step 3 -- Does the driver do AP mode? (`TBR-LINUX-01`, one BSS)

Confirm `iw list` reports AP among supported interface modes. Bring up a single
operational AP with a minimal `hostapd` config using the decided radio block
(`hw_mode=a`, `channel=149`, `country_code=US`, `ieee80211d=1`, `ieee80211h=0`,
`ap_isolate=0`) and a **temporary** local passphrase supplied by hand -- never
committed, never from the mission package (`TBR-SEC-01` still owns the real
mechanism). Record: does the AP start, on which channel, at what tx power, and
the achieved EIRP if measurable.

### Step 4 -- One phone associates and reaches one service

Associate a single phone. Because DHCP addressing is gated (`TBR-NET-01` OPEN),
assign a **static** address by hand for this test; do not derive or invent a DHCP
range. Bring up the one v0.0.1 service (GAP-09F) and confirm the phone reaches it
by IP. Record association success, throughput sanity, and any driver log noise.

### Step 5 -- Two BSS on one radio? (`TBR-LINUX-01`, `FML-ADR-084` fallback gate)

Only after Step 3-4 pass: attempt a second `bss=` stanza for the onboarding
network (client-isolated) on the same radio. Record whether the driver fields two
BSS reliably. **If it cannot**, that triggers the `FML-ADR-084` fallback (a
physically separate onboarding radio) -- record it as the finding, do not force it.

### Step 6 -- Onboarding posture over the window

With two BSS working (or the fallback radio), exercise the `mule/onboarding`
posture against real time: an active window broadcasts the onboarding SSID and
isolates its clients to enrollment only; an expired window (or untrusted time)
hides the SSID and refuses associations. This is the `FML-ADR-084` Stage-9
behavior; the software digital twin already exercises the same three cases
against `FakeClock`.

## What each step informs

| Step | Trade / value it feeds |
| --- | --- |
| 1 | `TBR-RF-03` hardware half; compatibility set (`FML-ADR-040`) |
| 2 | confirms `country_code: US` and the `us-915` channel/EIRP against the real regdomain |
| 3 | `TBR-LINUX-01` (AP-mode viability); the renderable hostapd radio block |
| 4 | GAP-09E acceptance (a phone reaches one service); GAP-09F |
| 5 | `TBR-LINUX-01` multi-BSS; the `FML-ADR-084` single-radio-vs-fallback decision |
| 6 | `FML-ADR-084` Stage-9 onboarding demonstration; the interface names for `nodes/mule-v001` |

## Boundary this card must NOT cross

No invented RF, DHCP, or credential values. The temporary Step-3 passphrase is
hand-supplied and never committed (`SECURITY.md`). Interface names discovered here
update `nodes/mule-v001/node.yml` only after they are real. Closing GAP-09E,
`TBR-LINUX-01`, or `TBR-RF-03` requires the recorded evidence accepted by the
Program Owner, not the running of this card.
