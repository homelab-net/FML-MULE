# Assigned-mule-lost-no-reattach: two MULEs on the tailnet

**Tier:** `SIMULATED` / real-Tailscale-ACL + two real tagged MULE nodes. This adds a
second MULE to the tailnet and confirms, on the coordination server, that an EUD
assigned to one MULE has no grant to the other -- so losing its assigned MULE gives it
no path to a second one. It is not RF, not the selected hardware, and not the live
dataplane; it is the policy-layer negative with a real second node present. Not
`HARDWARE-VERIFIED`.

**Result:** RUN, enforcement confirmed by the coordination server.
**Attempted:** yes. **Date:** 2026-09-29.
**Who ran it:** Cameron Zobrist (executed via Claude Code on the dev bench).
**Instrument:** the Tailscale coordination server's own ACL **tests** (validated on
apply), plus a second `tailscaled` (userspace-networking) as a real second MULE node.
**Node:** development bench, not selected hardware (`TBR-HW-01` open). `mule-bench` is
the real MULE (Debian 13, OTS on `tcp:8089`); `mule-bench2` is a second tailnet node
tagged `tag:mule-bench2` (userspace `tailscaled`, no services -- it exists to be the
"other MULE").
**Configuration:** ACL per `FML-ADR-086`. Tags: EUD =
`tag:eud-mission-demo-team-alpha` (assigned to `tag:mule-bench`); the second MULE =
`tag:mule-bench2`. The EUD grant is to `tag:mule-bench` only.
**Ambient:** none (overlay plane; no radios).

## Why this was done

`FML-ADR-082` requires that if the assigned MULE is unavailable, the EUD does not obtain
overlay ingress through another MULE. `FML-ADR-086` provides the mechanism (a grant to
the assigned MULE's own identity, never the shared `tag:mule`). This adds a real second
MULE and checks the negative directly.

## Method

`mule-bench2` was brought up as a second tailnet node (userspace `tailscaled`,
`--advertise-tags=tag:mule-bench2`). The ACL was applied with a `tests` block the
coordination server validates on apply (rejecting the apply if any assertion is wrong):

```json
"tests": [
  { "src": "tag:eud-mission-demo-team-alpha",
    "accept": ["tag:mule-bench:8089"],
    "deny":   ["tag:mule-bench:22", "tag:mule-bench:9999", "tag:mule:8089",
               "tag:mule-bench2:8089", "tag:mule-bench2:22"] }
]
```

The apply returned `200` -- every assertion holds, including the two new denies to
`tag:mule-bench2`.

## What this establishes

- **`assigned-mule-lost-no-reattach` (policy layer):** the EUD tag has **no grant** to
  the second MULE on any tested port. Its only ingress grant is to its assigned MULE
  (`tag:mule-bench`). Because the grant targets the assigned MULE's own identity and not
  the shared `tag:mule` class, there is nothing for the EUD to fall back to when its
  assigned MULE is down -- the "no reattach through another MULE" property is structural,
  not stateful.
- A real second MULE (`mule-bench2`) is present on the overlay while this holds, so the
  denial is against an actually-reachable-by-admin node, not a name with nothing behind
  it.

## What this does not establish

- **The live dataplane** with the assigned MULE actually taken down -- that the EUD, in
  use, fails to reach `mule-bench2` while `mule-bench` is offline. The ACL tests prove
  the policy the server enforces; a live run was not taken because the assigned MULE
  (`mule-bench`) is the node the Owner reaches remotely over this same overlay, and
  taking its ingress down to test could interrupt that access. The policy proof does not
  depend on the assigned MULE's state.
- `three-mules-no-layer2-extension` -- that batman-adv does not stretch across the WAN.
  The sim nodes carry no mesh; that case is separate and stays not-run.
- Anything about **RF** or the selected hardware. `SIMULATED`; the formal Stage 6
  qualification stays blocked on `TBR-HW-01`.

## Scrub note (SECURITY.md)

No real identity or address is committed. Nodes are referred to by synthetic tags; the
tailnet name, device ids, and the OAuth secret are not in the repo. `mule-bench2` is a
throwaway ephemeral sim node.
