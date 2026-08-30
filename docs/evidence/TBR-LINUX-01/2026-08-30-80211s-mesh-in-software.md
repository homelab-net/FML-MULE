# 802.11s and batman-adv, exercised in software with no radio

**Trade:** `TBR-LINUX-01`, and it verifies a mechanism `FML-ADR-059` depends on.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. `mac80211_hwsim` is a kernel software
simulator. **No radio was involved**, and nothing here is an RF result.

## Why this was done

Three files in this repository -- `FML-ADR-059`,
`os/config/networkd.conf.template` and `os/config/systemd-units.template` --
rest on one assumption: that an 802.11s mesh point interface reports no carrier
until the mesh is joined. `systemd-networkd` will not configure a link without
carrier, `ConfigureWithoutCarrier=` defaulting to false, so that assumption is
what makes `BatmanAdvanced=` wait for association instead of needing a unit
ordering nobody can be relied on to write.

All three said it was unverified and pointed at Stage 2. It did not need to
wait for Stage 2.

## Configuration

| Item | Value |
| --- | --- |
| Host | Debian 13, kernel `6.12.105+deb13-amd64` |
| Radios | `mac80211_hwsim`, two virtual `phy` devices |
| Mesh | 802.11s, mesh id `fml-mesh` |
| Routing | `batman-adv` 2024.2, `BATMAN_IV` |
| Topology | Two network namespaces, one `phy` moved into each |

`mac80211_hwsim` ships in the stock Debian kernel and reports `mesh point`
among its supported interface modes, which the two physical adapters on this
bench do not: see `2026-08-30-wireless-adapter-survey.md`.

## Result 1: the carrier assumption holds

A mesh point interface, brought up but not joined to any mesh:

```text
operstate: down   carrier: 0
```

The same interface after `iw dev wlan0 mesh join fml-mesh`:

```text
operstate: dormant   carrier: 1
```

**Carrier appears on joining and not before.** So `networkd`'s default gating
does what the three files claim: a `.network` file carrying `BatmanAdvanced=`
cannot apply to a mesh member that has not associated, and the ordering hazard
is prevented by the component rather than by a unit somebody has to remember.

The assumption is no longer an assumption. What is still unverified is whether
a **real** driver behaves the same way; `mac80211_hwsim` is `mac80211`'s own
simulator and a vendor driver is free to assert carrier earlier. That is a
narrower question than the one the files carried, and it is a reasonable thing
to check on the first board that arrives.

## Result 2: the whole stack composes, without hardware

Two namespaces, one virtual radio each, both mesh point on one mesh id, MTU
1560, `batman-adv` on top, an address on each `bat0`:

```text
=== 802.11s peer link ===
Station 3e:eb:61:fe:33:de (on wlan0)
    mesh plink:    ESTAB

=== batman neighbours ===
[B.A.T.M.A.N. adv 2024.2, MainIF/MAC: wlan0/aa:dd:f4:60:78:69 (bat0/... BATMAN_IV)]
IF             Neighbor              last-seen
        wlan0      3e:eb:61:fe:33:de    0.840s

=== ping ===
3 packets transmitted, 3 received, 0% packet loss
rtt min/avg/max/mdev = 0.087/0.123/0.190/0.087 ms
```

**IP traffic crossed batman-adv, over an 802.11s mesh, with no radio.**

## Why this matters more than the assumption it settled

`.github/workflows/mesh-probe.yml` forms its mesh over `veth`, and says so
plainly: "a perfect wire with no propagation, loss, contention or rate
adaptation". It proves batman-adv routes. **It exercises no 802.11s at all**,
because `veth` is not wireless, so the association layer `FML-ADR-053` selects
has never been run by anything in this repository.

This does run it. The mesh point interface type, the peering state machine,
the plink establishing, and `batman-adv` accepting a wireless mesh interface as
a hard interface are all exercised. That is a layer the program had no coverage
of and assumed its way past.

It also means the bring-up order in `mule/bringup.py` can be exercised against
the interface types a node will actually use rather than against `veth`, and
that `mule.bringup.state_violations` has something to read from.

## What this is not

**Not an RF result, and not close to one.** `mac80211_hwsim` models the
802.11 MAC, not a radio. There is no propagation, no path loss, no
interference, no rate adaptation, no antenna and no regulatory domain in any
physical sense. Every number `TBR-RF-01`, `TBR-RF-02` and `TBR-RF-03` exist to
obtain is still absent, and this changes none of them.

**Not evidence that a real driver works.** It is evidence that the kernel's
802.11s implementation works and that batman-adv composes with it. The adapters
on this bench still cannot do mesh point, and the out-of-tree driver for the
one that might still does not build.

**Not a substitute for Stage 2.** Two nodes cannot answer the questions Stage 2
asks, and the stage README says so: multi-hop, relay, topology change and
reconvergence need a third. `mac80211_hwsim` takes a `radios=` parameter and
three is as easy as two, so that limit is now a choice rather than a
constraint.
