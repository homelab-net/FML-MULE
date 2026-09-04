# The live service bench, and its deltas from the CM4 field node

This records the AP-plus-OpenTAKServer bench that runs an EUD (iTAK) against a
MULE-like node on a **development x86 machine**, how it is made to survive a
reboot, and -- the part that matters for the build -- **where its bring-up
sequence differs from the CM4 field node the BOM specifies**. It is a bench
record, `SIMULATED` tier: it exercises the service-plane user flow end to end,
and says nothing about RF, thermal, power, or CM4 footprint.

The field hardware is `hardware/prototype/prototype-bom-revA.csv`. Read the
deltas table against it before assuming anything here transfers unchanged.

## What the bench runs

On the x86 dev machine, persistent under `/home/mule1/mule/` (not `/tmp`, whose
wipe between sessions is what broke the first attempt):

- **EUD access point** on an RTL8812AU USB adapter (`hostapd` WPA2, `dnsmasq`
  DHCP, `iptables` NAT) with WAN passthrough out the onboard station. Hardened
  for the drop-outs seen earlier: `disassoc_low_ack=0`, `power_save off`, a
  channel clear of the local AP, max regulatory power.
- **OpenTAKServer 1.7.13** (web `:8081`, CoT `:8088`) with **PostGIS** and
  **RabbitMQ**, in rootful `podman --network host` containers.
- **mutual-TLS termination on `:8089`** by an `nginx` stream proxy in front of
  the CoT handler; the client cert is verified against the OTS CA and the
  stream proxied to `:8088`.
- An **iTAK data package** in OpenTAKServer's own iTAK format (`config.pref`
  plus two `p12`s, no `MANIFEST/` -- the ATAK mission-package layout is rejected
  by iTAK).

Reboot persistence, all bench-only mechanisms:

- the RTL8812AU driver is installed by **`dkms`** (`rtl8812au`), so it rebuilds
  across kernel updates and auto-loads on the USB id at boot;
- **`mule-ap.service`** brings the access point up (it waits for the adapter to
  enumerate first);
- **`mule-stack.service`** starts the containers in dependency order with the
  readiness waits `eud_handler` needs -- its RabbitMQ channel is opened
  per-connection and never opens if the AMQP listener is not up first, which is
  what produced the `rabbit_channel is None` errors when the order was wrong.

## The deltas from the CM4 field node

Each row is a place the field bring-up is **not** what the bench does. The basis
column cites the BOM row or the decision that governs the field form.

| Concern | Bench (x86, now) | CM4 field node | Basis |
| --- | --- | --- | --- |
| CPU / arch | `x86_64` Debian | `aarch64`, Raspberry Pi CM4 8GB/32GB | BOM `NODE-CORE/Compute`; `FML-ADR-021`/`022` |
| **EUD AP radio** | RTL8812AU **USB** dongle | **onboard CYW43455**, single-stream, 2.4 GHz | BOM: "Onboard Wi-Fi serves the EUD AP so HaLow can stay on SPI"; `FML-ADR-045` |
| **AP driver step** | build + `dkms` an out-of-tree driver -- a whole extra stage | **none**: `brcmfmac` is mainline, so this stage disappears | `TBR-LINUX-01` |
| Mesh radio | none (this bench is AP-only) | QCA6174A M.2 (`ath10k`), 802.11s + `batman-adv` | BOM `High-rate Wi-Fi`; `FML-ADR-024`/`025`/`053`; `TBR-RF-01`/`03` |
| Sub-GHz lifeline | none | WM6108 **HaLow over SPI** | BOM `HaLow`; `FML-ADR-024`; `TBR-LINUX-01` |
| LoRa plane | none | RAK4631 US915 **over UART** (Meshtastic) | BOM `LoRa`; `FML-ADR-026` |
| Container images | `amd64` (OTS built `FROM python:3.12` amd64) | **`arm64`** -- rebuild/repull, pin arm64 digests | `FML-ADR-029` |
| Container mgmt | ad-hoc `podman run` + these systemd oneshots, **rootful**, `--network host` | **rootless** `podman`, **Quadlet** units from `services/catalog/`, digest-pinned | `FML-ADR-029`; `services/quadlets/`, `services/catalog/` |
| Link config | `nmcli` release + manual `ip`/`hostapd`/`iptables` | **`systemd-networkd`** owns links; **`nftables`** from template; AP **bridged to the mesh interface** | `FML-ADR-056`/`057`/`059`; `os/config/*.template` |
| Addressing | hardcoded `10.41.0.1/24` | **per-deployment generated prefix** from the mission package | `FML-ADR-063`; `mission/schema/mission-package.schema.json` |
| WAN uplink | onboard station to a home AP | **general uplink** (Starlink / Ethernet / cellular), shared across the mesh | CONOPS section 42; `FML-ADR-068`/`069`; `TBR-NET-04` |
| Storage | ample x86 disk | **32 GB eMMC**; M.2 spent on the QCA6174, so Postgres lands on eMMC or a USB2 SSD | BOM `Storage`/notes; `TBR-COMP-01`; `FML-ADR-050` |
| Footprint | not measured (wrong arch) | OTS + PostGIS + the tile service must fit the **one compute element** beside the router | `FML-ADR-021`; `TBR-COMP-01`; `TBR-MAP-01` |
| Regulatory / power | US, 20 dBm on 2.4 GHz (RTL8812AU) | region profile drives it; CYW43455 power envelope differs | `REGULATORY.md`; region profiles |
| Cert enrolment | OTS CA on a persistent path; data package hand-built | same CA flow, but enrolment via the OTS API / EUD provisioning; CA at rest under `TBR-SEC-01` | `TBR-SEC-01`; `TBR-ID-01` |
| Persistence | `dkms` + two systemd oneshots | Quadlet + `networkd` + the cold-start drill, on `os/config/systemd-units.template` | `os/config/systemd-units.template`; `docs/verification/` cold-start drill |

## What the bench still proves, despite all of that

The **service-plane user flow** is form-agnostic and is what the bench
validated: an EUD deleting a stale server, importing an enrolment data package,
completing mutual TLS, registering as an EUD, and its CoT flowing through
`eud_handler` -> RabbitMQ -> `cot_parser` -> PostGIS. That path is the same on
the CM4; what changes is every row above it. The bench is where the flow and the
package format were made correct; the CM4 is where footprint, RF, thermal and
power become knowable, and none of those is answered here.
