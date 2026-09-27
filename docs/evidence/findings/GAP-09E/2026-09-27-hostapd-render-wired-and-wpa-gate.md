# GAP-09E: hostapd render wired into the oneshot, and the WPA gate

## Finding and authority

- **Finding:** GAP-09E, AP-only network rendering (P1) -- the headless half.
  Advances the GAP-09H register items **G3** (render wired into the oneshot,
  partial) and the **design half of G4** (the WPA security block).
- **Governing records:** `FML-ADR-083` (the runtime is a `Type=oneshot`
  configuration renderer), `FML-ADR-084` (onboarding two-BSS boundary),
  `FML-ADR-057` (operational BSS not isolated), `TBR-SEC-01` (the AP
  authentication mechanism and credential -- **OPEN**), `TBR-LINUX-01` (interface
  names and multi-BSS shape -- **OPEN**), `TBR-NET-01`/`TBR-NET-05` (DHCP and AP
  addressing), `SECURITY.md`, `THREAT_MODEL.md`.
- **Status:** `SIMULATED`. Exercised in the digital twin and the unit suite
  against synthetic fixtures; nothing here is on hardware. Wiring the render into
  the oneshot does not close GAP-09E, G3, or any trade.

## What was built (G3: the render is wired, fail-closed)

`mule/rendering.py` rendered the decided hostapd surface but was not called by the
boot path. It is now called by the oneshot (`mule/configuration.py` `main`), so a
single `python3 -m mule --region ... --mission ... --node ... --out ...`
invocation writes `hostapd.partial.conf` beside `parameters.json`.

The render runs for a node that fields an access point (a resolved `ap_channel`
marks that), and it is **fail-closed**, consistent with `FML-ADR-083`, whose
Consequences state that a configuration failure is a failed oneshot:

- A `RenderError` -- an interface still `TBD` on `nodes/mule-v001`
  (`TBR-LINUX-01`), a mission with no `ap_ssid` -- **fails the oneshot** (exit 5),
  the same fail-closed refusal the resolver makes on a `TBD` value. It never
  reports success without the AP configuration it was asked to produce, and never
  invents an interface name. This is verified for `nodes/mule-v001`'s posture by
  the `test/fixtures/nodes/ap-only` fixture (no interface map): the run exits
  non-zero, names the missing role, and writes **no** hostapd file. For the
  shipped `nodes/mule-v001` this means the oneshot refuses until `TBR-LINUX-01`
  names the interface -- the GAP-09H procedure already brings the AP up by hand
  until then.
- Any render from a previous run is removed before a new one is attempted, so a
  run that cannot complete never leaves a stale `hostapd.partial.conf` beside a
  freshly written `parameters.json`.
- With concrete interfaces (`test/fixtures/nodes/ap-wired`) the render reaches its
  success path and writes the operational block. Both the success path and the two
  behaviours the suite must detect -- the oneshot must render the AP surface
  (`M130`), and a failed render must not be swallowed (`M131`) -- are
  mutation-checked.

The file it writes is **not bootable and is marked so**. It carries the
operational radio block (country/channel/`hw_mode`/`ieee80211d`/`ieee80211h`) and
`ap_isolate=0` (`FML-ADR-057`), and names every gated omission.

### The live onboarding window is deferred, rendered closed

`FML-ADR-084` makes onboarding a time-bounded decision: broadcast the SSID while
the credential is valid, hide it at expiry. A `Type=oneshot` with no timer and no
`Restart` runs once and cannot express that lifecycle. So the boot oneshot renders
the onboarding BSS **closed**, with the reason recorded in the file, and the live
window render is owed to a later increment. This is a deliberate deferral rendered
fail-closed (the same posture `mule.onboarding.decide()` takes on any doubt), not
a decision that onboarding is disabled.

## G4 design half: the WPA security block is gated on TBR-SEC-01

The rendered partial deliberately omits the WPA block and names the gate. This
section records what that block will carry and what must be decided first, so the
gap is a specified owed item rather than a blank.

**The render surface, once `TBR-SEC-01` decides.** A WPA2 operational BSS needs,
in hostapd terms (hostapd.conf(5)): `wpa=2`, a `wpa_key_mgmt` (e.g. `WPA-PSK`),
`rsn_pairwise=CCMP`, and a passphrase source. The exact `wpa_key_mgmt` is the
substance of `TBR-SEC-01` (a pre-shared key is the assumed baseline, but SAE and
enterprise/EAP are the alternatives the trade weighs), so no value is rendered
until it closes -- writing `wpa_key_mgmt=WPA-PSK` now would be inventing the
answer to an open trade.

**The passphrase never enters the repository or the parameter document**
(`SECURITY.md`). It is supplied out of band (GAP-09H step 4) and, when rendered,
will be by reference to protected material -- the same `credential_ref` posture
`FML-ADR-084` already uses for onboarding. The renderer is tested to emit no
`wpa_passphrase`/`wpa_psk` and not to leak the reference.

**An open AP is a defect, never a rendered output.** The GAP-09H v0.0.1 procedure
defers service TLS as a recorded residual risk *on the assumption of at least a
WPA2 AP* (`THREAT_MODEL.md` names WPA2 for the AP separately from TLS for browser
services). WPA2 does not substitute for service TLS; but an **open** AP plus plain
HTTP would compound the deviation. The load-bearing rule for the render is
therefore: it emits a WPA2 block or it emits the gated placeholder it does now --
it never emits an operational BSS with no security block presented as complete.
That the current file is explicitly `NOT A BOOTABLE CONFIG` enforces this: it
cannot be mistaken for a finished, open AP.

## What remains owed

- **G3 hardware half:** the render exercised on the Pi with concrete interface
  names (`TBR-LINUX-01`), per the GAP-09E bring-up card. `SIMULATED` here.
- **G4:** `TBR-SEC-01` decides the auth mechanism and the credential-supply path;
  only then does the WPA block render.
- **The live onboarding window** render (`FML-ADR-084`), which needs a runtime
  mechanism the boot oneshot alone does not provide.
- **DHCP/addressing** (`TBR-NET-01`/`TBR-NET-05`), rendered elsewhere.
