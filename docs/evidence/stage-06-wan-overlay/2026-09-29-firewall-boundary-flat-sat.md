# WAN overlay boundary: firewall flat-sat

**Tier:** `SIMULATED` (netns + nftables). This exercises the **firewall-boundary
half** of several Stage 6 cases on network namespaces with the concrete form of
`os/config/nftables.conf.template`. It says nothing about RF, nothing about Tailscale
itself, and nothing about *which* tailnet peer is the assigned MULE. It is **not**
`HARDWARE-VERIFIED`, and it does **not** mark any Stage 6 case as run: each case has an
owed half (the tailnet-identity half, the full CONOPS section 41 service set, RF, or a
second MULE) that this does not cover. The `*-not-run.md` files stay not-run.

**Result:** RUN, all boundary assertions passed (`cases passed: 6  failed: 0`).
**Attempted:** yes. **Date:** 2026-09-29.
**Who ran it:** Cameron Zobrist (executed via Claude Code on the dev bench).
**Instrument:** `test/bench/wan-overlay-posture.sh` -- `ip netns`, `nftables v1.1.3`,
`iproute2-6.15.0`, `python3 3.13.5` TCP probes.
**Node:** development bench, not selected hardware (`TBR-HW-01` open). Debian GNU/Linux
13 (trixie), kernel `6.12.105+deb13-amd64`.
**Configuration:** one netns is the MULE with logical interfaces `ap0` (EUD access
point), `mesh0` (RF mesh, a plain-veth stand-in -- see the script header), `wan0`
(uplink), `ovl0` (overlay / `tailscale0` stand-in); peers for a local EUD, a remote
overlay EUD, a mesh node, and an unrelated infrastructure host.
**Ambient:** none (no radios; netns only).

## Why this was done

`FML-ADR-082` (with `CCR-04`) makes the MULE the boundary of the WAN overlay:
the overlay is not bridged to the EUD access point or the RF mesh, and an admitted
remote EUD reaches only the assigned MULE's approved remote-EUD ingress. That boundary
is carried by `os/config/nftables.conf.template` (Deliverable B). Stage 6's evidence
folder holds the pass conditions as not-run. This runs the ones that are firewall logic
and need no real tailnet, and proves the boundary **fires** (baseline first).

## Method

The bench brings up the netns model with forwarding on and **no** boundary rules,
and confirms the cross-plane paths the boundary must block are **open** (overlay peer
-> RF mesh service; overlay peer -> unrelated infra). Without that baseline the boundary
would have nothing to block and a "blocked" result would be meaningless. It then loads
the concrete nftables ruleset (the commented rules of `nftables.conf.template` made
loadable) and re-tests. TCP reachability is a stdlib `socket.connect` with a 1.5 s
timeout.

## What was shown (firewall-boundary half only)

| Case | Shown here | Owed (not shown here) |
| --- | --- | --- |
| `access-point-passthrough-not-overlay` | AP EUD forwarded to `wan0`; AP -> overlay dropped; the passthrough carries no overlay interface (`FML-ADR-068`). | -- (firewall half is the case) |
| `posture-disabled` | The AP EUD has no overlay interface/address and no path to the overlay peer; local AP path works. | Real client with the posture set `DISABLED`. |
| `eud-not-on-rf-mesh` | The overlay peer holds no `mesh0` and cannot reach the mesh service (open in baseline, dropped with the boundary). | The "approved mesh service reachable *via the ingress*" positive. |
| `unrelated-infrastructure-inaccessible` | The overlay peer cannot reach infrastructure behind `wan0`. | Real home/Homelab denial on the live tailnet. |
| `wan-loss-local-continuity` | With `ovl0` down, the local AP and mesh services still answer. | The full CONOPS section 41 set (peer ATAK, S0/S1 services, LoRa). |
| `assigned-ingress-only` | The overlay peer reaches only the ingress port (8089) on the overlay interface, not another port; not the AP, mesh, WAN. | **The identity half**: *which* peer / *which* MULE. That is the tailnet policy (`os/config/tailscale-acl.hujson.template`), exercised on a real tailnet, not the firewall. |

## What this does not establish

- The tailnet-identity half of `assigned-ingress-only` and all of
  `one-mission-team-tag` -- those are the Tailscale ACL/grant, run on a real tailnet.
- `assigned-mule-lost-no-reattach` and `three-mules-no-layer2-extension` -- need a
  second MULE.
- Anything about RF, Tailscale's own behaviour, throughput, or the selected hardware.
- It is `SIMULATED`; `FML-ADR-082` stays decided-and-not-fully-demonstrated, and the
  formal Stage 6 qualification stays blocked on `TBR-HW-01`.
