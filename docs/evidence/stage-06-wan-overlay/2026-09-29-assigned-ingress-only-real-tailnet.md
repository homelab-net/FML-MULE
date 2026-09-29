# Assigned-ingress-only and one-mission-team-tag: real tailnet, real tagged client

**Tier:** `SIMULATED` / real-Tailscale-ACL + real-tagged-client. This exercises the
**identity half** the netns firewall flat-sat
(`2026-09-29-firewall-boundary-flat-sat.md`) could not: on the real coordination server,
with a real tagged EUD node, that the `FML-ADR-086` grant mechanism reaches only the
assigned MULE's ingress. It is not RF, not the selected hardware, and not the formal
Stage 6 qualification (blocked on `TBR-HW-01`); it is real Tailscale policy enforcement
plus real device tagging. Not `HARDWARE-VERIFIED`.

**Result:** RUN, enforcement confirmed by the coordination server.
**Attempted:** yes. **Date:** 2026-09-29.
**Who ran it:** Cameron Zobrist (executed via Claude Code on the dev bench).
**Instrument:** the Tailscale coordination server's own ACL **tests** (validated on
policy apply) and the device-tags API; `tailscale` 1.102.4 on the MULE.
**Node:** development bench, not selected hardware (`TBR-HW-01` open). The MULE is a real
tailnet node (Debian 13, kernel 6.12.105); the EUD is the Owner's real iOS device.
**Configuration:** ACL per `FML-ADR-086` (SELECTED). Tags: MULE = `tag:mule` +
`tag:mule-bench` (per-MULE identity); EUD = a single `tag:eud-mission-demo-team-alpha`.
Ingress `tcp:8089` (the OTS TLS port standing in for the TBD approved remote-EUD ingress).
**Ambient:** none (service/overlay plane; no radios).

## Why this was done

`FML-ADR-086` decides that a remote-EUD ingress grant targets the **assigned MULE's own
identity**, never the shared `tag:mule`. The netns flat-sat proved the firewall boundary
but says nothing about *which* peer/MULE the tailnet policy admits. This confirms that
identity half on the real coordination server.

## Method

The ACL (`FML-ADR-086` shape) was applied to the tailnet with a `tests` block, which the
coordination server validates on apply and rejects the apply if any assertion is wrong:

```json
"tests": [
  { "src": "tag:eud-mission-demo-team-alpha",
    "accept": ["tag:mule-bench:8089"],
    "deny":   ["tag:mule-bench:22", "tag:mule-bench:9999", "tag:mule:8089"] }
]
```

The apply returned `200` -- the assertions hold. The MULE was then re-authed to carry
`tag:mule` + `tag:mule-bench`, and the Owner's iOS device was tagged (device-tags API)
with the single `tag:eud-mission-demo-team-alpha`, and both were read back.

## What this establishes

- **`assigned-ingress-only` (identity half):** the coordination server enforces that the
  EUD tag reaches **only** `tag:mule-bench:8089`. It is denied the admin port (`:22`),
  a non-ingress port (`:9999`), and -- decisively -- the shared `tag:mule:8089`. The last
  is the per-MULE-scoping proof (`FML-ADR-086`): a grant to the assigned MULE's identity
  does **not** reach the class every MULE shares, so it cannot reach a non-assigned MULE.
- **`one-mission-team-tag`:** the admitted EUD carries **exactly one** tag naming the
  mission and team (`tag:eud-mission-demo-team-alpha`), read back from the device. It is
  not composed from several tags; deny-by-default means removing it removes the grant.
- The MULE carries the per-MULE identity (`tag:mule-bench`) `FML-ADR-086` requires.

## What this does not establish

- **The live dataplane connection** -- that the phone, in use, actually opens `tcp:8089`
  to the MULE and nothing else. The ACL *tests* prove the policy the server enforces; a
  live client connection would confirm the dataplane end to end (available to run: open
  the OTS ingress from the phone on the tailnet).
- **`assigned-mule-lost-no-reattach`** -- that losing the assigned MULE does not admit the
  EUD through another MULE. This needs a **second MULE** and stays not-run.
- Anything about **RF**, throughput, or the selected hardware. `SIMULATED`; the formal
  Stage 6 qualification stays blocked on `TBR-HW-01`.

## Scrub note (SECURITY.md)

No real identity or address is committed. The EUD is referred to only by its synthetic
tag; the tailnet name, device ids, and the OAuth secret are not in the repo. The ingress
port 8089 is a bench stand-in for the TBD approved remote-EUD ingress, not a decided value.
