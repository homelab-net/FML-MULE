# Configuration templates

Commented template files for the network plane and the radio bearers.

**Every value in these files is `TBD`.** They are skeletons showing what has to
be configured and which trade will decide each value. They are not files to be
filled in on a node.

## Configuration is generated

**No file in this directory contains a frequency, a channel, a bandwidth, or a
transmit power.** Those come from a region profile in `regions/<region-id>/`.

Region is an **input to configuration generation**, not a constant. The sub-GHz
band this program targets is region-specific: 902-928 MHz exists in the United
States and some other administrations, and does not exist for this purpose in
the EU or the UK, which use 863-868 MHz with duty-cycle constraints that have
no analogue in the US rules. A repository hardcoded to one band excludes a
large share of potential contributors.

See `regions/README.md` and `REGULATORY.md`.

The generation mechanism itself is `TBD`, and interacts with the boundary
between the image build and Ansible described in `os/image/README.md`.

## Logical, not physical

Templates are written per **logical function**, not per physical interface.

`FML-ADR-045` decides that the EUD access point and the high-throughput
inter-node mesh are separate logical radio functions, and deliberately leaves
open whether they share a physical radio. `TBR-RF-03` will settle that. Writing
templates per logical function means a later consolidation changes the
generation mapping rather than restructuring every file.

## Files

| File | Configures | Trades |
| --- | --- | --- |
| `meshtasticd.conf.template` | The LoRa plane: radio attachment and the supervisor around the daemon | `TBR-RF-02`, `TBR-NET-02`, `TBR-TAK-01` |
| `networkd.conf.template` | Link configuration, addressing, mesh attachment, the field bridge | `TBR-LINUX-01`, `TBR-NET-01`, `TBR-RF-01`, `TBR-RF-03` |
| `systemd-units.template` | The units that run the above, and the setting that must not be changed | `TBR-LINUX-01`, `TBR-RF-03` |
| `wpa_supplicant.conf.template` | Station and mesh association | `TBR-RF-01`, `TBR-RF-02` |
| `hostapd.conf.template` | EUD access point | `TBR-RF-03` |
| `batman-adv.conf.template` | Layer 2 mesh routing | `TBR-RF-01`, `TBR-NET-01` |
| `nftables.conf.template` | Firewall and forwarding policy | `TBR-NET-01` |
| `interfaces.conf.template` | Interface bring-up and addressing | `TBR-NET-01` |
| `chrony.conf.template` | Local time discipline | `TBR-TIME-01` |
| `dnsmasq.conf.template` | Local DNS and DHCP | `TBR-NET-01` |

## Bring-up ordering

Interface bring-up order matters and is a known source of failure: a mesh
interface configured before its driver has finished initialising, or
`batman-adv` attached to an interface that is not yet up, fails in ways that
look like radio faults.

Ordering is not captured in these templates. It belongs to the systemd unit
structure and is `TBD`, pending `TBR-LINUX-01`. `FML-ADR-023` notes that the
upstream MANET reference project encodes real knowledge about bring-up
ordering, and that where its configuration is adopted the source is cited in
the adopting file.

## Validation

Configuration generated from a region profile must be validated against that
profile before it is applied: a generated channel outside the region's
permitted set is a regulatory problem, not a bug. No validator exists yet.
