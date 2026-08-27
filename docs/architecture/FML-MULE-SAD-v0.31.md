# Program FERAL MULE (FML)
## Multi-Bearer Utility Link Equipment (MULE)
# System Architecture Description (SAD)

**Version:** 0.31  
**Status:** DRAFT - SRR Package Candidate  
**Date:** 2026-08-25  
**Parent:** FML/MULE CONOPS v1.01 BASELINE  
**Parent Homelab Phase:** Phase 6 / WP-07 RF, Meshtastic & TAK Communications  
**Document Type:** Subsystem System Architecture Description  
**Architecture Maturity:** SRR-ready architecture / evidence-driven refinement phase; quantitative hardware and continuity trades remain open

---

## 0. Document Control

### 0.1 Purpose

This SAD defines the logical, physical, software, network, service, security, RF, data, power, and failure-domain architecture for the MULE subsystem.

The SAD translates the approved FML/MULE CONOPS into an implementable architecture without prematurely locking individual commercial SKUs.

This document is intentionally more specific than the CONOPS and less prescriptive than the future TRD and ICD.

### 0.2 Revision History

| Version | Date | Disposition |
|---|---|---|
| 0.1 | 2026-08-25 | Initial SRR architecture draft. Preferred dual-compute OpenWrt + Debian architecture. |
| 0.2 | 2026-08-25 | Internal multidisciplinary SRR-style review. Preferred single-primary-compute Debian architecture with logical plane isolation. Added TBR closure criteria and preliminary extracted CONOPS traceability. |
| 0.3 | 2026-08-25 | SRR package correction. Fixed architecture-decision configuration control; explicitly resolved the EUD-WLAN versus high-rate-mesh radio-role question at planning level; added kernel promotion and rollback architecture, local time architecture, data-at-rest/zeroize architecture, compute/memory sizing, hardware lifecycle control, original-software inventory, source/evidence register, storage-failure behavior, and owner/gate fields for TBRs. Replaced the machine-extracted §35 with clause-complete traceability and explicit N/A/partial status. No CONOPS requirement was removed. |
| 0.31 | 2026-08-25 | Narrow SRR cleanup. Added power-objective change-control trigger, antenna/stream-count planning, thermal trade, service-authority/discovery ownership, time-to-HA dependency, TBR dependency graph, storage-endurance controls, hardware-in-the-loop kernel-release ownership, named-owner/date placeholders, external-practitioner review actions, and an evidence-driven post-SRR document strategy. No primary architecture decision changed. |

### 0.3 Governing Principles

Architecture selections in this SAD follow these rules:

1. Prefer mature open-source projects over custom software.
2. Prefer standard protocols and documented interfaces over proprietary integration.
3. Use current supported stable software at implementation time.
4. Do not fork an upstream project merely to avoid learning or integrating its supported interfaces.
5. When a fork or local patch is unavoidable, minimize the delta, document it, assign an owner, and maintain an upstream-rebase path.
6. Keep network reachability separate from service authorization.
7. Preserve local operation without WAN, NOMAD, or home infrastructure.
8. Make deployment reproducible from version-controlled configuration.
9. Keep operational users insulated from routing, container, and failover details.
10. Treat custom MULE software as thin integration/control glue, not a replacement for mature infrastructure projects.
11. Prefer one operating-system lifecycle and one primary compute element unless measured reliability, security, RF, or power evidence justifies physical separation.
12. Manual GUI state is never the authoritative configuration source.
13. A field kernel, radio-driver set, and boot image are promoted as one tested compatibility set, not independently.
14. Architecture decisions retain stable identifiers across revisions. A changed decision supersedes an earlier decision; its identifier is never silently reused.

### 0.4 Architecture Decision Status

This document uses the following architecture statuses:

- **SELECTED** - architecture direction accepted for the current SRR package.
- **PREFERRED** - implementation candidate currently favored but replaceable if controlled interfaces remain intact.
- **TBR** - trade to be resolved before the stated gate.
- **TBD** - detailed value to be derived by requirements, testing, or BOM work.
- **FALLBACK** - retained alternate architecture if the preferred approach fails defined closure criteria.
- **SUPERSEDED** - historical decision retained for configuration history but no longer controlling.

### 0.5 Baseline Source Hierarchy

For MULE subsystem work:

1. FML/MULE CONOPS v1.01 is the controlling subsystem operational concept.
2. Homelab v2.5.3 plus as-built Git remains the parent execution authority.
3. The inspectable v2.5.1 TRD, ICD, SOW, ADR, ATP, and BOM remain the detailed reference set where v2.5.3 detail is not directly available.
4. Where the MULE CONOPS intentionally changes an older parent allocation, the difference is recorded as a parent-baseline change action rather than silently reconciled.

### 0.6 Known Parent-Baseline Change

The current inspectable parent TRD and ICD allocate TAK Server and communications gateway functions specifically to NOMAD.

The MULE CONOPS intentionally changes that model by allowing eligible MULEs, NOMAD, and approved portable service hosts to provide shared field services.

Therefore:

> **PBCR-01:** Before MULE integration into the parent Homelab baseline, TAK and communications-gateway allocations must be updated from NOMAD-only to the controlled Field Service Plane described by the MULE subsystem.

This does not block MULE SAD development. It does block parent-system integration baseline closure.

### 0.7 SRR Review Disposition

The v0.31 architecture retains the v0.2 single-host direction and closes document-level weaknesses identified during the second internal multidisciplinary SRR-style review.

The preferred implementation remains one primary Linux compute element with logical isolation. A physically separate network processor remains a fallback if test evidence shows the single-host architecture cannot meet security, recoverability, RF-driver, thermal, or availability requirements.

### 0.8 Architecture Decision Identifier Control

The inline `AD-001` through `AD-020` labels in SAD v0.1 and v0.2 were draft-local identifiers and were incorrectly reused when the meanings changed.

They are historical only and shall not be used as controlling decision identifiers.

Beginning with SAD v0.31, controlling architecture decisions use the persistent `FML-ADR-###` namespace. Identifiers are never reused.

Beginning with v0.31, existing SAD section numbers are frozen for downstream traceability. New material should use existing subsections, decimal subsections, or appendices rather than renumbering established sections after the RTM begins to reference them.

| Current ID | Decision | Status | Historical relationship |
|---|---|---|---|
| FML-ADR-021 | Single primary compute / single Debian host with logical plane isolation | SELECTED | Supersedes v0.1 AD-001 and v0.2 AD-001 |
| FML-ADR-022 | Debian stable as production host OS | SELECTED | Supersedes v0.1 AD-002 and v0.2 AD-002 |
| FML-ADR-023 | Consume OpenMANET as reference/configuration source, not mandatory production firmware | SELECTED | Supersedes v0.1/v0.2 AD-003 framing |
| FML-ADR-024 | IEEE 802.11s + batman-adv/BATMAN-V as baseline IP MANET | SELECTED | Carries forward v0.1/v0.2 AD-004 |
| FML-ADR-025 | High-throughput conventional Wi-Fi as an additional IP bearer | SELECTED | Carries forward v0.1/v0.2 AD-005 |
| FML-ADR-026 | Meshtastic/LoRa remains a separate non-IP degraded plane | SELECTED | Carries forward v0.1/v0.2 AD-006 |
| FML-ADR-027 | RF coexistence controlled through supported host/radio interfaces; no assumed openmanetd primitive | SELECTED | Supersedes v0.1/v0.2 AD-007 implementation assumption |
| FML-ADR-028 | Mission services share the Debian host but cannot directly own network/RF configuration | SELECTED | Supersedes draft AD-008 |
| FML-ADR-029 | Rootless Podman + Quadlet is default OCI execution model | SELECTED | Carries forward draft AD-009 |
| FML-ADR-030 | Shared-kernel logical isolation using users/namespaces/cgroups/nftables | SELECTED | Supersedes draft AD-010 |
| FML-ADR-031 | Stable local DNS + HAProxy/TCP ingress for logical service identities | SELECTED | Supersedes draft AD-011 |
| FML-ADR-032 | OpenTAKServer is preferred initial TAK-compatible server | PREFERRED | Carries forward draft AD-012 |
| FML-ADR-033 | PyTAK is preferred custom CoT transport/gateway library | SELECTED | Carries forward draft AD-013 |
| FML-ADR-034 | PostgreSQL is preferred only if the TAK state study demonstrates it is the correct continuity boundary | CONDITIONAL | Supersedes draft AD-014 |
| FML-ADR-035 | MULE service controller is a fixed-policy lifecycle layer, not a cluster scheduler | SELECTED | Carries forward draft AD-016 |
| FML-ADR-036 | Smallstep step-ca is preferred initial PKI | PREFERRED | Carries forward draft AD-017 |
| FML-ADR-037 | Application-native RBAC first; OPA only when cross-application policy justifies it | SELECTED | Supersedes draft AD-018 |
| FML-ADR-038 | EAP-TLS is the production EUD admission target | SELECTED TARGET | Carries forward draft AD-019 |
| FML-ADR-039 | WAN overlay terminates on MULE infrastructure, never directly on EUDs | SELECTED | Carries forward draft AD-020 |
| FML-ADR-040 | Field kernel/radio-driver promotion is gated and pinned as a tested compatibility set | SELECTED | New in v0.3 |
| FML-ADR-041 | MULE requires an A/B or equivalently bootable known-good rollback path | SELECTED PRINCIPLE | New in v0.3 |
| FML-ADR-042 | Battery-backed local RTC + chrony; optional GNSS discipline; credential validity never fails open | SELECTED | New in v0.3 |
| FML-ADR-043 | Sensitive local mission data uses LUKS2-class block encryption; key-on-same-media unattended unlock is rejected | SELECTED PRINCIPLE | New in v0.3 |
| FML-ADR-044 | Zeroize is primarily cryptographic key/credential invalidation, not flash overwrite | SELECTED PRINCIPLE | New in v0.3 |
| FML-ADR-045 | EUD WLAN and high-throughput inter-node mesh are separate logical radio functions; power/BOM planning assumes separate radios until concurrency is proven | SELECTED PLANNING BASELINE | New in v0.3 |
| FML-ADR-046 | MULE Status Aggregator is approved thin original software | SELECTED | New in v0.3 |
| FML-ADR-047 | Mission Trust Service is approved thin original software and is not a CA | SELECTED | New in v0.3 |
| FML-ADR-048 | Gateway translation uses existing OTS/Meshtastic/PyTAK interfaces first; custom translation is protocol-specific glue only | SELECTED | New in v0.3 |
| FML-ADR-049 | Service Authority Registry is a function of the MULE Status Aggregator, not a separate daemon | SELECTED | New in v0.31 |
| FML-ADR-050 | Local-storage write amplification is bounded by design through controlled logging/telemetry retention and endurance-qualified storage | SELECTED PRINCIPLE | New in v0.31 |

The TAK automatic-recovery mechanism remains **TBR-HA-01** and therefore does not receive an ADR until selected.

### 0.9 SRR Meeting-Risk Findings

The following findings are intentionally opened by the program before external review:

1. radio count and EUD-AP/high-rate-mesh concurrency;
2. kernel/out-of-tree-driver lifecycle;
3. trustworthy offline time;
4. encrypted storage/unlock/zeroize;
5. TAK state continuity versus the 60-second recovery objective;
6. compute/RAM sizing on one host;
7. source/evidence traceability for hardware claims;
8. formal clause-by-clause CONOPS traceability.

These are presented as controlled open engineering items, not hidden deficiencies.

# 1. Architecture Summary

MULE is one standardized field appliance built around one primary compute element, multiple controlled RF interfaces, a protected power subsystem, and field-replaceable external interfaces.

The primary compute element hosts logically separated functional planes:

1. **Network Plane**  
   Native Linux networking, Wi-Fi/HaLow drivers, 802.11s, batman-adv/BATMAN-V, client access, addressing, DNS, firewalling, routing, and service ingress.

2. **Mission Service Plane**  
   TAK-compatible services, browser services, Meshtastic/CoT gateways, identity/trust functions, status aggregation, observability, local mission data, and approved shared-service hosting.

3. **Management and Security Plane**  
   Host administration, configuration management, mission policy, credential handling, software update control, audit, and recovery functions.

4. **HaLow RF Chain**  
   Full-IP range-oriented IEEE 802.11ah bearer.

5. **High-Throughput Wi-Fi RF Chain**  
   Conventional Wi-Fi bearer for high-rate local and inter-node traffic where validated.

6. **LoRa/Meshtastic RF Chain**  
   Independent low-bandwidth non-IP degraded communications path.

7. **Power and Supervisory Domain**  
   Protected battery assembly, power monitoring, external-power interface, and controlled shutdown support.

8. **Optional External Interfaces**  
   Ethernet, WAN, GNSS, approved VHF/UHF/HF gateways, external power, and maintenance interfaces.

## 1.1 System Context Diagram

```text
                             OPTIONAL PARENT / WAN SERVICES
                         NOMAD / Field Host / Tailscale / WAN
                                      |
                                      | approved routed services only
                                      |
+----------------+              +-----+--------------------------------------+
| Authorized EUD |---Wi-Fi----->|                                            |
| ATAK / Browser |              |                  MULE                      |
+----------------+              |                                            |
                                |  +--------------------------------------+  |
+----------------+              |  | Primary Linux Compute                |  |
| Peer MULEs     |<--HaLow/IP-->|  |                                      |  |
| / MANET nodes  |<--Hi-rate--->|  | Network Plane                       |  |
+----------------+              |  | 802.11s / batman-adv / nftables     |  |
                                |  | DHCP/DNS / routing / service ingress |  |
+----------------+              |  |                |                     |  |
| Meshtastic     |<---LoRa----->|  | Mission Service Plane               |  |
| peers          |              |  | TAK / web / gateway / identity      |  |
+----------------+              |  |                |                     |  |
                                |  | Management & Security Plane          |  |
+----------------+              |  +--------------------------------------+  |
| External radio |<--approved-->|          |            |            |       |
| gateway / TNC  |  interface   |       HaLow       Wi-Fi high-rate LoRa     |
+----------------+              |                                            |
                                +--------------------------------------------+
                                      |
                                  protected battery
                                  / external power
```

## 1.2 Internal Logical Block Diagram

```text
                         Debian stable host
+------------------------------------------------------------------+
|                                                                  |
|  HOST NETWORK / RF CONTROL                                       |
|  wpa_supplicant / hostapd / batman-adv / batctl / nftables      |
|  dnsmasq or equivalent / Ethernet / radio drivers                |
|                |                         |                       |
|                | controlled veth/bridge  |                       |
|                v                         v                       |
|  +----------------------+    +-------------------------------+   |
|  | Service namespace /  |    | Management/security services  |   |
|  | rootless OCI network |    | mission trust / audit / CM    |   |
|  |                      |    |                               |   |
|  | TAK / chat / files   |    | privileged actions remain     |   |
|  | portal / status      |    | explicit and policy-gated     |   |
|  +----------------------+    +-------------------------------+   |
|                                                                  |
|  Rootless containers cannot reconfigure mesh/radios/firewall.    |
+------------------------------------------------------------------+
```

The single-host design reduces board count, power, mass, cabling, operating-system lifecycle burden, and internal failure points. Its primary trade is weaker physical isolation between networking and applications because both share one kernel. Section 10 defines the compensating logical controls and Section 26 records the resulting failure domain.

# 2. Primary Architecture Selection

## 2.1 Selected Architecture: Single Primary Compute, Single OS

**FML-ADR-021 - SELECTED**

MULE will use one primary general-purpose compute element running one supported stable Linux operating system. Network, mission-service, management, and security functions are logically separated through Linux process isolation, namespaces, users, capabilities, cgroups, container boundaries, and nftables policy.

Physical separation into a second general-purpose network computer is not part of the preferred v1 architecture.

### Rationale

The primary engineering question is not whether OpenWrt can host applications. It is whether MULE must consume OpenMANET as a complete firmware distribution or may consume its validated networking model, configuration knowledge, and reusable components.

The critical MANET mechanisms are Linux components:

- IEEE 802.11s;
- `mac80211`/`cfg80211`;
- `batman-adv`;
- BATMAN-V;
- Morse Micro Linux drivers and user-space tools;
- standard DHCP/DNS/firewall/routing components.

OpenWrt provides a mature packaging and UCI integration environment, but the required mesh behavior is not inherently OpenWrt-exclusive.

The single-host architecture therefore:

- retains the OpenMANET networking model without requiring the OpenMANET firmware image;
- removes one general-purpose board, one inter-board Ethernet link, and one OS lifecycle;
- reduces idle and active power burden;
- reduces enclosure volume and internal cabling;
- simplifies imaging, Ansible provisioning, observability, and recovery;
- keeps radio drivers close to the physical hardware;
- avoids VM radio passthrough;
- avoids Kubernetes-scale orchestration;
- supports rootless container isolation for ordinary applications;
- remains one standardized appliance.

### Accepted Cost

A host-kernel or primary-compute failure can now remove both network and application functions from that MULE.

This is a real reduction in failure-domain isolation relative to the v0.1 dual-board architecture. The v1 mitigation is:

- strong process and network isolation;
- controlled updates;
- reproducible imaging;
- watchdog/recovery behavior where practical;
- common spare MULE replacement;
- peer network continuity through other MULEs;
- analog/manual PACE.

The architecture will revert to physical compute separation only if testing demonstrates that the shared-host risk is unacceptable.

## 2.2 Architecture Trade Disposition

| Option | Disposition | Reason |
|---|---|---|
| Single board, single Debian OS | **SELECTED** | Best power/mass/sustainment balance; native radio drivers; logical isolation sufficient unless disproven. |
| Single board, OpenWrt VM + Linux host | **NOT PREFERRED** | Adds hypervisor, boot order, virtual networking, and radio-ownership complexity without preserving a meaningful independent network failure domain. |
| Dual board, OpenWrt + Debian | **FALLBACK** | Stronger physical isolation but higher power, mass, cabling, cost, and lifecycle burden. Retained if single-host testing fails. |
| OpenWrt-only monolith | **REJECTED** | Application/service environment is unnecessarily constrained. |
| Two separate operator-carried boxes | **REJECTED** | Violates appliance and human-factors concept. |

## 2.3 Fallback Trigger

The dual-board architecture may be reinstated only if one or more of the following are demonstrated during qualification:

- required HaLow or high-rate radio drivers cannot coexist reliably with the service host;
- application workload causes unacceptable routing latency or packet loss despite cgroups/resource limits;
- security review finds shared-kernel isolation insufficient for the approved threat model;
- service recovery/maintenance cannot occur without unacceptable disruption;
- power or thermal testing unexpectedly favors a dedicated low-power network processor;
- regulatory/RF integration requires a separate certified network module.

Any fallback activation becomes an ADR and BOM/CI change, not an informal field variant.

# 3. Primary Compute Platform and Host Networking

## 3.1 Host Operating System

**FML-ADR-022 - SELECTED**

The primary MULE compute element uses the current Debian stable release at build time.

At issue, Debian 13.6 "trixie" is the current stable release.

The production image will use:

- a supported Debian stable kernel and security-update stream;
- version-controlled package manifests;
- controlled kernel/module configuration;
- Ansible-managed host configuration;
- signed or hash-verified release artifacts;
- a field-release freeze before planned deployments.

The production MULE does not require OpenWrt as its host operating system.

## 3.2 OpenMANET Consumption Model

**FML-ADR-023 - SELECTED**

OpenMANET is consumed as an open-source reference architecture, integration source, configuration baseline, and prototype environment rather than as a mandatory production firmware image.

MULE will preserve or adapt validated OpenMANET behavior for:

- 802.11s HaLow mesh configuration;
- batman-adv/BATMAN-V topology;
- local per-node client addressing concepts;
- multicast-oriented ATAK behavior;
- mesh-gateway behavior;
- Morse Micro integration patterns;
- telemetry concepts;
- field-oriented defaults.

OpenMANET components may be reused directly when they are portable to the selected Linux host.

OpenMANET-specific components that depend on OpenWrt/UCI are not automatically ported or forked. Their useful behavior will first be implemented through standard Linux interfaces where practical.

The MULE team will not create a private OpenMANET fork merely to preserve firmware-level similarity.

## 3.3 Native Linux Network Stack

The preferred production network stack is:

```text
Debian Linux
  |
  +-- cfg80211 / mac80211
  +-- Morse Micro supported Linux driver stack
  +-- wpa_supplicant for 802.11s where appropriate
  +-- hostapd for EUD AP functions where appropriate
  +-- batman-adv / BATMAN-V
  +-- batctl / standard netlink tooling
  +-- nftables
  +-- dnsmasq or equivalent DHCP/DNS service
  +-- systemd-networkd or equivalent controlled link configuration
```

Exact configuration tooling may change if a better supported upstream mechanism is validated, but external interfaces and required behavior remain controlled.

## 3.4 Reproducible Host Build

The authoritative MULE host baseline consists of:

- controlled Debian installation/image;
- package manifest;
- kernel/module requirements;
- Ansible roles;
- network configuration templates;
- systemd units;
- Podman Quadlets;
- pinned OCI image digests;
- mission-package schema;
- hashes and release notes.

Manual GUI changes are not authoritative and must not be required to reconstruct a fielded node.

## 3.5 Prototype Use of OpenMANET Firmware

Current upstream OpenMANET firmware remains useful for:

- comparative RF testing;
- validating OpenMANET defaults;
- ATAK multicast characterization;
- checking new upstream behavior;
- isolating whether a failure is MULE-specific or upstream.

A prototype may run the upstream firmware without making it the production software baseline.

# 4. MANET Architecture

## 4.1 Core MANET

**FML-ADR-024 - SELECTED**

MULE uses:

```text
IEEE 802.11s
      +
batman-adv
      +
BATMAN-V
```

as the primary IP MANET architecture.

This follows the current OpenMANET model and preserves peer ATAK multicast behavior without requiring application-layer routing awareness.

## 4.2 Field L2 Domain

The preferred v0.3 network model retains the upstream OpenMANET flat field domain concept.

The default OpenMANET `10.41.0.0/16` field prefix is retained as the preferred initial MULE field prefix because it:

- does not conflict with the parent Homelab 10.77.0.0/16 home prefix;
- does not conflict with the parent 10.78.0.0/16 rack prefix;
- reduces divergence from upstream OpenMANET;
- already includes a per-node lease-allocation model.

Exact reservations and node ranges become ICD-controlled values.

**TBR-NET-01:** confirm that retaining 10.41.0.0/16 does not create unacceptable collision risk with expected external networks.

## 4.3 Per-Node Client Access

Each MULE provides a local field WLAN for nearby EUDs.

Local EUD access is bridged into the field BATMAN domain so:

- peer ATAK multicast can traverse the mesh;
- a team retains local connectivity if the mesh fragments;
- clients do not require awareness of MANET routing.

Per-node DHCP allocation follows the upstream OpenMANET principle of non-overlapping local scopes.

Because EUD access is bridged into the BATMAN field domain, Stage 2 must measure not only CoT/PLI traffic but also ordinary EUD broadcast, multicast, ARP, mDNS, and discovery load under representative client counts and hop counts. The architecture does not assume that normal phone broadcast behavior is free on a constrained multi-hop mesh.

## 4.4 IPv6

The parent Homelab currently disables managed IPv6.

MULE v1 therefore remains IPv4-first and does not introduce a separate managed IPv6 architecture during initial qualification.

IPv6 may be reintroduced only through controlled parent and subsystem change.

---

# 5. High-Throughput Bearer

## 5.1 Architecture

**FML-ADR-025 - SELECTED**

The high-throughput conventional Wi-Fi bearer is a second IP bearer managed by the host Network Plane.

The preferred architecture is to expose the high-rate 802.11s interface as an additional batman-adv hard interface when chipset and driver stability support it.

This provides:

- one logical field L2;
- continued peer multicast;
- automatic path selection;
- no requirement for application-level route awareness.

Packet-level striping is not required.

## 5.2 EUD WLAN Versus High-Rate Inter-Node Radio

**FML-ADR-045 - SELECTED PLANNING BASELINE**

The EUD-access WLAN and the high-throughput inter-node bearer are two separate **logical radio functions**.

For power, RF, carrier, and BOM planning, v0.3 assumes they are implemented by separate physical conventional-Wi-Fi radio interfaces unless testing proves that one selected chipset can provide stable concurrent AP + 802.11s/mesh operation without unacceptable channel coupling, throughput loss, multicast impairment, or recovery complexity.

The conservative production reference topology is therefore:

```text
1. EUD access radio             conventional Wi-Fi AP
2. High-rate inter-node radio  conventional Wi-Fi mesh/routed adjunct
3. HaLow radio                 IEEE 802.11ah
4. LoRa radio                  Meshtastic
```

Where a selected compute module has suitable integrated Wi-Fi, that integrated radio is the preferred first candidate for the EUD AP role. A separate validated radio then owns the high-rate inter-node function.

Sharing EUD AP and high-rate mesh on one physical radio is an optimization, not a baseline assumption.

**TBR-RF-03** determines whether physical consolidation is permitted.

Its closure evidence must include:

- supported concurrent interface modes;
- AP + 802.11s/mesh stability;
- channel-coupling constraints;
- EUD/client compatibility;
- multicast and roaming behavior;
- radio recovery behavior;
- power delta;
- supported spatial-stream count;
- antenna/feed count;
- whether antennas can be internal, external, or must be field replaceable.

This decision intentionally avoids underestimating power, antenna count, RF coexistence, or carrier-board I/O during early trades.

## 5.3 Fallback Architecture

If the selected high-rate Wi-Fi hardware cannot provide stable 802.11s operation, the high-rate bearer may be implemented as a routed adjunct for:

- bulk file transfer;
- service replication;
- video;
- other high-rate traffic.

In that case HaLow remains the baseline MANET fabric.

This fallback does not change the user-facing service model.

**TBR-RF-01:** validate high-rate 802.11s chipset/driver behavior before PDR.

---

# 6. HaLow Bearer

## 6.1 Implementation Direction

Wi-Fi HaLow uses a Morse Micro-supported MM6108/MM8108-class implementation or a compatible validated successor.

The architecture intentionally references:

- standard Linux `cfg80211/mac80211`;
- Morse Micro open driver/firmware components;
- standard Linux networking interfaces;
- 802.11s;
- batman-adv.

The exact HaLow module remains a BOM decision.

## 6.2 Hardware Compatibility

The network processor must come from a hardware family with a validated path for:

- current supported Debian/Linux kernel and driver path;
- HaLow driver support;
- high-rate Wi-Fi;
- Ethernet;
- required antenna interfaces.

Current OpenMANET-supported families such as Raspberry Pi CM4-class and Gateworks Venice-class hardware are architecture-compatible candidates.

No candidate becomes the procurement baseline until RF, power, mechanical, and software acceptance is complete.

---

# 7. LoRa / Meshtastic Plane

## 7.1 Separation

**FML-ADR-026 - SELECTED**

LoRa/Meshtastic is a separate non-IP communications plane.

It is not bridged into batman-adv and is not used as an arbitrary IP tunnel.

## 7.2 Radio Attachment

A standard Meshtastic-compatible LoRa radio connects to the primary MULE host through an approved standard interface such as:

- USB serial;
- UART;
- TCP where provided by the radio.

The Meshtastic radio continues its own mesh behavior independently of the service processor.

Loss of the primary host may interrupt TAK translation. Where the selected Meshtastic hardware contains its own controller and native mesh firmware, host failure should not prevent that radio from continuing its native Meshtastic participation while independently powered.

## 7.3 TAK Integration

Integration priority is:

1. existing OpenTAKServer Meshtastic support when it satisfies the mission need;
2. TAK Meshtastic Gateway;
3. PyTAK plus Meshtastic Python API for only the translation logic not already provided upstream.

Custom LoRa protocol development is out of scope.

---

# 8. RF Coexistence Control

## 8.1 Architecture Boundary

HaLow and LoRa may share the 902-928 MHz US band and must be treated as colocated potentially interfering systems.

**FML-ADR-027 - SELECTED**

RF coexistence is controlled through a dedicated cross-plane policy interface.

The RF implementation may use:

- channel separation;
- antenna separation;
- filtering;
- time-domain coordination;
- scan timing;
- transmit suppression;
- duty-cycle limits.

The CONOPS priority remains:

> When IP is lost, preservation of LoRa degraded communications takes priority over aggressive HaLow reacquisition that materially desensitizes the LoRa receiver.

## 8.2 Coexistence Interface

The Network Plane must expose or consume a documented supported control interface for:

- HaLow scan/reacquisition state;
- current channel;
- transmit state where available;
- temporary transmit suppression or scan control where supported.

`openmanetd` may be reused where portable and where it exposes the required supported controls, but the coexistence architecture shall not assume that its API provides deterministic scan or transmit-suppression primitives.

A MULE-specific coexistence policy service is **not yet selected**. TBR-RF-02 first determines whether supported driver, netlink/nl80211, `iw`, `wpa_supplicant`, Morse Micro, or equivalent controls are sufficient. Original coexistence software is permitted only if a thin policy layer is still necessary after that test.

**TBR-RF-02:** define the measurable LoRa availability target while HaLow recovery is active.

---

# 9. Mission Service Plane and Application Execution

## 9.1 Execution Model

**FML-ADR-028 - SELECTED**

The Mission Service Plane runs on the same Debian host as the Network Plane but is logically constrained from modifying network/RF state except through explicit privileged interfaces.

Ordinary application services run with least privilege.

## 9.2 Container Runtime

**FML-ADR-029 - SELECTED**

The default application deployment pattern is:

```text
Debian
  |
systemd
  |
Podman
  |
rootless Quadlet-managed OCI containers
```

Rootless containers are the default for ordinary browser applications, file services, status services, and other workloads that do not require privileged hardware or host networking access.

Reasons:

- fully open-source runtime;
- rootless isolation;
- no always-on Docker daemon requirement;
- systemd-native dependency and restart control;
- declarative deployment;
- appropriate scale for one appliance;
- avoids Kubernetes.

OCI image compatibility remains desirable.

## 9.3 Privileged Service Rule

Hardware-touching or host-networking functions run as narrowly scoped native systemd services or purpose-built privileged helpers rather than as a general population of rootful containers.

Examples include:

- radio drivers;
- mesh configuration;
- nftables;
- DHCP/DNS;
- RF coexistence controls;
- hardware/power monitoring;
- selected radio gateways where required by device access.

Mixed rootless and arbitrary rootful container operation is not the normal deployment model.

## 9.4 Native Service Exception

A mission application may run natively under a dedicated Unix identity and systemd when:

- that is the upstream-supported installation method;
- a mature maintained container image is unavailable;
- hardware access makes containerization harmful;
- containerization materially complicates recovery.

OpenTAKServer is currently a valid candidate for this exception.

If OpenTAKServer is deployed natively, the release must include:

- a version-controlled Ansible role;
- pinned package/application versions;
- configuration templates;
- backup procedure;
- restore procedure;
- automated health check;
- Stage 5 recovery test.

The most important shared service may not be the least reproducible service in the appliance.

The restore procedure must be demonstrated onto a **different eligible node**, not merely restored in place, so hostname, certificate, data-path, and service-identity assumptions are exercised.

# 10. Logical Isolation and Enforcement

## 10.1 Isolation Objective

**FML-ADR-030 - SELECTED**

Network, service, management, and security functions are logically separated on one Linux host.

The architecture explicitly acknowledges that this is a weaker boundary than two physically separate computers because the functions share one kernel.

The accepted v1 objective is to prevent routine application compromise, crash, or resource exhaustion from automatically granting the ability to reconfigure radios, routing, firewall policy, or privileged mission trust.

The isolation claim is intentionally **one-directional**:

> ordinary application/service contexts are constrained from changing Network/RF state; the privileged host Network/RF context is not itself contained by those application namespaces.

The shared host therefore does not provide the same bidirectional enforcement-domain separation as two physical computers. That limitation is part of the security review, not hidden by container terminology.

## 10.2 Isolation Mechanisms

The preferred controls are:

- distinct Unix users and groups;
- rootless OCI containers for ordinary applications;
- Linux network namespaces where useful;
- veth/bridge boundaries for service traffic;
- nftables policy between EUD, service, management, WAN, and external-RF domains;
- Linux capabilities minimized per process;
- cgroups/systemd resource limits;
- read-only mounts where practical;
- separate secrets/configuration permissions;
- SELinux/AppArmor may be added if the selected Debian baseline supports it cleanly and the operational burden is acceptable.

## 10.3 Network Ownership

The host root/network control context owns:

- physical Ethernet;
- HaLow interface;
- high-rate Wi-Fi interfaces;
- EUD AP interface;
- 802.11s;
- batman-adv;
- routing;
- nftables;
- DHCP/DNS;
- WAN overlay interface.

Mission-service containers receive only the network access necessary to provide their service.

A rootless application is not granted `CAP_NET_ADMIN` merely for convenience.

## 10.4 Resource Isolation

Critical network functions receive reserved CPU/memory priority sufficient to remain responsive during application load.

S2/S3 services are resource-limited and may be stopped under:

- battery constraint;
- thermal constraint;
- memory pressure;
- CPU pressure;
- mission profile.

The Stage 1 and Stage 7 tests must demonstrate that representative service load does not destabilize the Network Plane.

## 10.5 Physical-Separation Fallback

If security or reliability testing shows that shared-kernel isolation is insufficient, the same logical interface model may be implemented using a second compute element without changing EUD-facing services or field procedures.

Physical separation is therefore an implementation fallback, not a separate operational architecture.

# 11. Stable Logical Service Ingress

## 11.1 User-Facing Names

The CONOPS logical service identities remain:

```text
tak.field
chat.field
files.field
portal.field
```

## 11.2 Local Ingress

**FML-ADR-031 - SELECTED**

The MULE host provides stable local service ingress using:

- local DNS;
- a lightweight TCP/HTTP proxy layer.

HAProxy is the preferred initial open-source proxy because it supports both TCP and HTTP service forwarding, mature health checks, and operation under a dedicated unprivileged service identity.

The preferred model is:

```text
EUD
 |
tak.field
 |
Local MULE ingress
 |
HAProxy
 |
currently authoritative TAK host
```

This avoids requiring EUD DNS/server reconfiguration when a service moves.

## 11.3 TLS

For TAK and other end-to-end protected protocols, TCP passthrough is preferred where possible.

Each eligible backend may hold its own private key and a certificate valid for the same logical service identity.

The architecture does not require copying one service private key to every node.

---

# 12. Service Discovery, Authority, and Health

**FML-ADR-049 - SELECTED**

Service discovery and authority-health tracking are functions of the **MULE Status Aggregator** rather than a sixth standalone MULE-original daemon.

The Status Aggregator therefore contains a **Service Authority Registry** module.

Every eligible S2 service instance must expose machine-readable health/authority state sufficient to distinguish:

- process alive;
- service ready;
- authoritative;
- degraded;
- non-authoritative;
- synchronization/state age where applicable.

A process that is alive but does not hold authoritative state is not an acceptable backend for authoritative service traffic.

The Service Authority Registry:

1. collects local service health and authority state;
2. receives approved peer service-health/authority records over the field IP network;
3. validates the freshness and trust of those records;
4. maintains the local view of eligible/authoritative service hosts;
5. exposes a stable local machine interface to HAProxy/service ingress;
6. marks stale or untrusted records unusable for authoritative routing;
7. reports disagreement or no-safe-authority conditions to the operator status plane.

The registry does **not** elect an authoritative TAK primary by itself.

Authority is determined by the selected service-specific continuity mechanism under §14. The registry reports and consumes that decision.

Preferred local interface:

- HTTP/JSON over loopback or Unix-domain socket;
- explicit schema and freshness timestamp;
- no general remote configuration surface.

Health interfaces from upstream applications should use their supported native APIs/HTTP endpoints where available. Thin adapters may normalize upstream health into the registry schema.

**Owner:** Platform/SRE function.  
**Original-software accounting:** included within FML-ADR-046 MULE Status Aggregator, not counted as an additional daemon.

# 13. TAK Architecture

## 13.1 Preferred Server

**FML-ADR-032 - PREFERRED**

OpenTAKServer is the preferred initial TAK-compatible server implementation.

Reasons include existing support for:

- ATAK/iTAK/WinTAK;
- TLS CoT streaming;
- client certificate enrollment;
- groups/channels;
- DataSync/Mission API;
- data packages;
- Meshtastic integration;
- web UI;
- SBC deployment;
- documented API;
- SQLAlchemy databases.

The architecture remains TAK-compatible, not OpenTAKServer-exclusive.

## 13.2 Gateway Development

**FML-ADR-033 - SELECTED**

PyTAK is the preferred library for custom CoT clients and translation gateways where no existing integration satisfies the requirement.

Generic CoT transport must not be reimplemented without cause.

## 13.3 OpenTAKServer Internal Dependencies

The MULE architecture acknowledges that OpenTAKServer currently uses:

- multiple Python processes;
- RabbitMQ for internal CoT messaging;
- SQLAlchemy-backed persistent storage.

RabbitMQ is treated as local transient service infrastructure, not as a field-wide clustered message bus.

---

# 14. TAK Persistent State and Continuity

## 14.1 State Classification Is the Design Gate

**TBR-TAK-01 - CRITICAL**

No database-HA mechanism will be selected until the program identifies where OpenTAKServer or another chosen TAK implementation actually stores all mission-critical persistent state.

The Stage 5 state study must classify, at minimum:

- relational database state;
- DataSync / Mission API state;
- mission packages and uploaded files;
- client certificate enrollment, issuance, and enrollment-authorization state;
- group/channel configuration;
- server configuration;
- RabbitMQ/transient messaging state;
- reconstructable PLI/presence/session state;
- local map/tile/cache state whose loss would be operationally visible after failover;
- immutable mission-package state.

Each item will be placed into the CONOPS classes:

- Common Trust and Configuration;
- Mission-Critical Persistent State;
- Reconstructable or Ephemeral State.

## 14.2 Database Selection

**FML-ADR-034 - PREFERRED / CONDITIONAL**

PostgreSQL is the preferred relational database if Stage 5 demonstrates that mission-critical TAK state requiring authoritative continuity is stored in the SQL backend and if the chosen TAK server implementation supports the required workflows correctly on PostgreSQL.

SQLite remains acceptable for non-HA prototypes and bench testing where its limitations are understood.

Database support claimed by an ORM is not sufficient acceptance evidence. Stage 5 must test the actual MULE TAK workflows against the selected backend.

## 14.3 Initial Continuity Pattern

The initial v1 continuity pattern is:

```text
authoritative TAK primary
        |
        | controlled state synchronization
        v
named recovery-capable standby
```

The standby may be another eligible MULE, NOMAD, or an approved field-services host.

The required user experience remains:

- stable `tak.field` identity;
- no ordinary EUD server reconfiguration;
- peer ATAK continues during S2 interruption when network reachability exists;
- recovered state is explicitly marked authoritative, degraded, partial, non-authoritative, or unknown.

## 14.4 Automatic Recovery

The CONOPS automatic-recovery objective remains in force.

**TBR-HA-01 - OPEN**

No specific Patroni, etcd, Raft, witness, lease, quorum, or fencing implementation is selected in SAD v0.31.

After TBR-TAK-01 closes, and with TBR-TIME-01 supplying the required clock/holdover bounds for any time-sensitive authority mechanism, the program will select the simplest mechanism that can:

1. prove which host may act as authoritative;
2. avoid uncontrolled split-brain;
3. determine whether required mission-critical state is sufficiently current;
4. promote automatically when safe authority is established;
5. refuse automatic promotion when safe authority cannot be established;
6. support explicit administrative recovery when automatic promotion is unsafe.

Administrative promotion is the mandatory fallback, not the preferred normal case.

## 14.5 State Synchronization

Potential mechanisms may include:

- PostgreSQL streaming replication;
- application-supported replication/export;
- controlled filesystem replication;
- signed mission configuration package;
- immutable predeployment content;
- explicit checkpoint/snapshot transfer.

Syncthing may be used only for data whose conflict and consistency semantics are compatible with file synchronization.

It must not be used as a substitute for transactional database replication.

## 14.6 Recovery-Time Objective

The CONOPS objective remains:

> Restore synchronized shared TAK service within 60 seconds under healthy IP-mesh conditions without ordinary EUD reconfiguration.

This remains an **objective conditional on TBR-TAK-01**.

A 60-second recovery generally implies a warm, pre-established recovery posture with sufficiently current mission-critical state and pre-established trust. If the state study demonstrates that the objective cannot be achieved without disproportionate complexity, unacceptable battery/compute burden, or unsafe authority semantics, the program will raise a CONOPS change request against the applicable §27/§79 criterion rather than introduce an unjustified HA stack merely to preserve the number.

Cold or unsynchronized recovery is a separate recovery class and may take longer.

## 14.7 Closure Order

The continuity trade closes in this sequence:

```text
TBR-TAK-01 state classification
        |
        +--------------------+
        |                    |
        v                    v
database/file          TBR-TIME-01
synchronization        bounded-time behavior
requirements                 |
        |                    |
        +----------+---------+
                   |
                   v
          authority/fencing mechanism
                   |
                   v
      Stage 5 failure and partition testing
                   |
                   v
TBR-HA-01 closure / future persistent FML-ADR assignment
```

# 15. Service Lifecycle Control

## 15.1 Service Controller

MULE requires a small local service lifecycle function to translate:

- mission profile;
- authenticated user demand;
- role/scope;
- battery;
- thermal state;
- network state;
- shared-host availability

into systemd service targets.

## 15.2 Implementation Principle

**FML-ADR-035 - SELECTED**

The service controller will not be a general cluster scheduler.

It will:

- start/stop a fixed approved service catalog;
- apply grace timers;
- apply minimum-residency timers;
- prevent oscillation;
- report current service state;
- never replace systemd/Podman health management.

Custom code is acceptable here because this is MULE-specific policy glue and not a replacement for a mature orchestration platform.

---

# 16. Identity and Trust Architecture

## 16.1 PKI

**FML-ADR-036 - PREFERRED**

Smallstep `step-ca` is the preferred initial open-source PKI implementation for:

- offline organizational root;
- mission intermediate;
- service certificates;
- device certificates;
- short-lived mission credentials.

The root signing key remains offline.

A mission/enrollment authority may be delegated without placing the organizational root key on field nodes.

## 16.2 Mission Trust Service

**FML-ADR-047 - SELECTED**

Each MULE hosts a lightweight **Mission Trust Service** responsible for local enforcement and distribution of signed mission authorization state.

Its responsibilities include:

- current mission trust bundle;
- credential-expiry policy;
- signed revocation records;
- signed role/scope policy data where used;
- node revocation data;
- trust-state status for administrators;
- propagation over available approved IP paths.

The Mission Trust Service does not become a second certificate authority by default.

It distributes validated signed state issued by an authorized mission/enrollment function.

## 16.3 Revocation Model

Revocation is handled by:

- bounded certificate lifetime;
- signed mission revocation data;
- propagation by the Mission Trust Service over available IP mesh and approved WAN paths;
- eventual expiry when a partition cannot receive revocation.

LoRa is not required to carry PKI revocation data in v1.

If later testing shows that a compact signed emergency revocation format is useful over LoRa, it may be added through the ICD and security architecture.

The architecture does not claim instantaneous offline revocation.

## 16.4 Authorization

Identity and authorization remain separate.

A credential proves principal/device identity.

Role and organizational scope are carried in signed mission policy data or equivalent controlled claims.

The architecture should avoid embedding mutable organizational policy permanently into long-lived device certificates.

## 16.5 Policy Engine Selection Rule

**FML-ADR-037 - SELECTED RULE**

Application-native RBAC is preferred when it correctly enforces MULE role + scope and can be provisioned/reviewed reproducibly.

Open Policy Agent may be used when:

- multiple applications require the same cross-application policy decision;
- application-native RBAC cannot express required role/scope semantics consistently;
- policy-as-code materially reduces drift.

OPA is not inserted into every request path merely for architectural uniformity.

## 16.6 Audit Boundary

Security-relevant changes are logged independently of ordinary application telemetry, including:

- credential issuance/revocation;
- role/scope changes;
- mission trust updates;
- node revocation;
- service promotions;
- privileged configuration change;
- zeroize.

This architecture supports the CONOPS audit requirement but final retention and tamper-evidence requirements remain for the Security Architecture/TRD.

# 17. EUD Network Admission

## 17.1 Production Target

**FML-ADR-038 - SELECTED TARGET**

The production target for EUD WLAN admission is certificate-based 802.1X/EAP-TLS.

Benefits:

- per-device identity;
- no shared fleet password;
- offline CA validation;
- revocation/expiry support;
- compatibility with the mission-scoped PKI model.

## 17.2 Prototype Mode

Per-device PPSK may be used during prototype development when EAP-TLS would delay RF/network characterization.

Prototype PPSK must not be treated as the final authorization architecture.

Network admission never substitutes for application authorization.

## 17.3 Offline EAP-TLS Validation

The preferred initial production implementation uses the **hostapd integrated EAP server** for local EAP-TLS validation so EUD admission does not depend on a central RADIUS server.

The Mission Trust Service supplies the local trust/revocation material needed by the admission function.

FreeRADIUS remains an approved alternate if Stage 9 demonstrates a need for richer AAA/accounting or roaming semantics that hostapd cannot provide cleanly.

This is network admission only. Operational role/scope remains application policy.

---

# 18. WAN and Tailscale

## 18.1 Overlay Boundary

**FML-ADR-039 - SELECTED**

Only MULE infrastructure participates in Tailscale or an equivalent WAN overlay.

EUDs do not join the tailnet.

## 18.2 Policy

Tailscale Grants are the preferred current policy model for WAN-overlay access.

Overlay policy remains deny-by-default and restricts MULE nodes to approved field-service destinations.

Tailscale device tags/grants represent infrastructure/service identity.

They do not represent Team Alpha, Team Bravo, Team Lead, or other operational mission roles.

## 18.3 WAN Failure

Tailscale is entirely optional to baseline MULE operation.

Loss of Tailscale or WAN does not remove local mesh, peer ATAK, local services, or LoRa.

---

# 19. Configuration Architecture

## 19.1 Golden Baseline

Each MULE hardware block uses:

- one controlled Debian base image;
- controlled kernel/module requirements;
- controlled network configuration;
- controlled service catalog;
- version-controlled systemd/Quadlet definitions;
- controlled mission-package schema.

The authoritative configuration source is Git plus generated/deployed artifacts.

A web UI or local manual command may perform an authorized emergency change, but that change must be reconciled back into the controlled configuration before the node returns to normal fleet status.

The field-maintenance return-to-service checklist must include a positive configuration-reconciliation step. A node with undocumented emergency changes is not eligible to return to the ready-spare pool.

## 19.2 Mission Configuration Package

The mission package is a signed deployment artifact containing, as applicable:

- node identity;
- mesh identity;
- RF configuration;
- EUD credentials;
- role/scope mappings;
- service candidates;
- logical service names;
- retention policy;
- EXERCISE/live state;
- EMCON policy;
- WAN policy;
- amateur-radio enablement;
- external interoperability data.

The package is verified before activation.

## 19.3 Configuration Tooling

**SELECTED implementation practice:**

- Git for authoritative configuration history;
- Ansible for host provisioning and service installation;
- standard Linux configuration templates for `wpa_supplicant`, `hostapd`, `batman-adv`, `nftables`, DHCP/DNS, and interfaces;
- Podman Quadlet/systemd units for OCI service definitions;
- OCI images pinned by immutable digest for field releases;
- signed/hash-verified mission packages.

The deployed node must be rebuildable without undocumented manual state.

## 19.4 Upstream Lifecycle Ownership

The Communications and Identity Management / Configuration Management function owns a software dependency register for MULE.

At minimum the register tracks:

- upstream project;
- pinned field version;
- current upstream stable version;
- security-support status;
- local patches;
- license;
- update decision;
- validation evidence.

Review occurs:

- before every field-release freeze;
- after a security-significant upstream advisory;
- at least quarterly while the fleet is active.

This prevents the open-source-first strategy from becoming an unmanaged collection of release cadences.

## 19.5 Hardware Lifecycle Register

Configuration Management maintains a hardware lifecycle register parallel to the software dependency register.

At minimum it tracks:

- compute module/SBC;
- carrier board and board-to-board connector;
- RF modules;
- antenna connectors/pigtails;
- battery/BMS/charger components;
- storage devices;
- critical power regulators;
- declared vendor production/obsolescence horizon where available;
- approved second source or successor path;
- impact on hardware-block interchangeability;
- requalification required for substitution.

The register is reviewed before every hardware-block procurement and at least annually while the fleet is active.

Known public lifecycle evidence at issue includes Raspberry Pi CM4 production through at least January 2034 and CM5 production through at least January 2036. These dates are evidence inputs, not procurement decisions.

# 20. Software Supply Chain

## 20.1 General Release Controls

Before field release:

- package/image versions are pinned;
- cryptographic hashes are retained;
- production images are built from controlled source/configuration;
- upstream provenance is recorded;
- local patches are documented;
- software updates are frozen during the parent-system predeployment freeze window;
- unstable/snapshot branches are not used unless an approved exception exists;
- field updates are deliberate and reversible;
- a known-good prior image remains recoverable.

Where feasible, SBOM and vulnerability-scanning tooling should be integrated into the build pipeline rather than executed manually on each field node.

The single-host architecture deliberately reduces the fleet from two general-purpose OS lifecycles to one.

A local fork is a program liability and requires an ADR identifying:

- why upstream interfaces were insufficient;
- exact patch delta;
- maintenance owner;
- upstream/rebase strategy;
- verification impact.

## 20.2 Kernel and Out-of-Tree Radio Driver Lifecycle

**FML-ADR-040 - SELECTED**

The field kernel, Morse Micro/out-of-tree radio driver set, firmware, and required userspace radio tooling are promoted as one tested compatibility set.

MULE will not allow an unattended kernel promotion to silently create a fleet-wide radio-driver incompatibility.

Policy:

1. field-release kernels are pinned;
2. kernel security updates are evaluated promptly but staged outside the field fleet first;
3. DKMS is preferred when supported cleanly by the selected driver package;
4. if DKMS is not the supported path, the driver/module build is pinned to the approved kernel package;
5. every candidate kernel promotion must rebuild/load all required out-of-tree modules;
6. the candidate must pass automated boot, radio enumeration, HaLow mesh formation, high-rate radio, EUD AP, and representative traffic smoke tests;
7. the candidate must survive at least one reboot and rollback exercise;
8. no kernel is promoted during the deployment freeze window except through an approved urgent-security exception.

TBR-LINUX-01 therefore closes on a **repeatable kernel-promotion pipeline**, not merely a one-time successful driver build.

## 20.3 Known-Good Rollback

**FML-ADR-041 - SELECTED PRINCIPLE**

Because one host is the per-node compute single point of failure, MULE requires a bootable recovery path independent of the newly promoted root filesystem.

The production implementation must provide either:

- A/B root filesystem/image slots; or
- an equivalently robust bootable known-good image/rollback mechanism.

A filesystem snapshot that cannot boot when the active root filesystem is damaged is not sufficient by itself.

**TBR-REC-01** selects the exact implementation after the compute/carrier boot chain is chosen.

Acceptance includes:

- failed update;
- corrupt active image;
- failed radio-driver promotion;
- operator-initiated rollback;
- restoration to a known-good fleet baseline without WAN.

## 20.4 Hardware-in-the-Loop Release Bench

The kernel/radio promotion policy requires permanent test capability rather than an ad hoc manual checklist.

**Owner:** Linux/Platform release function.  
**Independent verification support:** Test/Verification function.

Minimum maintained bench:

- two representative MULE prototype/production-block nodes;
- representative HaLow radios;
- representative EUD AP and high-rate radios;
- representative LoRa interface;
- at least one EUD test client;
- controllable Ethernet/WAN path;
- power measurement capability sufficient to detect gross regression.

The bench executes an automated or semi-automated release suite covering:

1. clean boot;
2. expected kernel/modules;
3. radio enumeration;
4. EUD AP startup and association;
5. EAP-TLS admission where enabled;
6. HaLow mesh formation;
7. batman-adv neighbor/path formation;
8. high-rate bearer startup;
9. representative multicast/CoT traffic;
10. service ingress;
11. reboot;
12. rollback to the known-good image.

Bench hardware is a program/test asset and must be reserved in the prototype BOM rather than borrowed from the deployable fleet.

A field kernel/radio compatibility set cannot be promoted solely from a successful package build.

# 21. Observability Architecture

## 21.1 Local First

Each MULE retains enough local telemetry to diagnose:

- battery;
- thermal state;
- bearer state;
- mesh neighbors;
- route state;
- EUD association;
- service state;
- TAK authority state;
- gateway role;
- storage state;
- time state;
- synchronization state.

## 21.2 Standard Native Interfaces

Preferred production telemetry interfaces are:

- `batctl` and batman-adv/netlink data for mesh state;
- `iw` / nl80211 for conventional Wi-Fi and supported wireless state;
- Morse Micro supported driver/user-space interfaces for HaLow state;
- nftables counters for policy/flow state;
- hostapd control/status interfaces for EUD AP/admission state;
- systemd service state;
- Prometheus-compatible metrics;
- structured JSON for MULE-specific normalized status.

`openmanetd` may be used as a prototype/reference telemetry source when running OpenMANET firmware, but production MULE observability does not depend on it.

A thin MULE exporter may normalize the native interfaces above into stable metrics/JSON so upstream implementation changes do not leak into the operator UI.

When NOMAD or parent observability is reachable, selected metrics/logs may be forwarded.

Loss of centralized observability does not remove local status.

# 22. Operator Status Architecture

**FML-ADR-046 - SELECTED**

A local MULE Status Aggregator combines host, RF, network, mission-service, trust, time, storage, and power state into the simplified operator view required by the CONOPS.

It must not require users to interpret BATMAN tables, Linux namespaces, or container status.

The status service distinguishes:

- GREEN / normal;
- DEGRADED;
- LOW-BANDWIDTH;
- NON-AUTHORITATIVE;
- EMCON;
- FAULT.

When shared data is not authoritative, the interface also provides a concise reason code, such as:

- `PARTITION`;
- `STATE_LAG`;
- `HOST_RECOVERY`;
- `NO_SAFE_AUTHORITY`;
- `UNSYNCHRONIZED`;
- `UNKNOWN`.

Where available it also reports:

- time since last authoritative synchronization;
- current shared-service host;
- whether this MULE is carrying elevated service-host power burden.

The diagnostic tier exposes deeper engineering data without granting configuration privilege.

# 23. EMCON Architecture

EMCON is enforced at multiple layers:

1. network/radio advertisement behavior;
2. high-rate bearer state;
3. HaLow update/scanning behavior;
4. service announcement behavior;
5. nonessential service activity;
6. WAN-overlay activity;
7. EUD operator policy.

The architecture does not assume an EUD can be made fully electromagnetically silent by MULE alone.

EMCON transitions must be explicit, locally indicated, and reversible.

The operator must be able to confirm EMCON state without opening a browser or illuminating a normal display.

The production physical design therefore requires a low-signature tactile or momentary local indication of at least:

- EMCON active;
- fault preventing commanded EMCON;
- authorized override state where applicable.

The exact indicator/control implementation is a mechanical/human-factors decision and must satisfy the CONOPS night/signature requirements.

# 24. External RF Gateway Boundary

Approved external VHF/UHF/HF integrations connect to the MULE host through standard interfaces where possible:

- USB serial;
- audio interface;
- TNC;
- Bluetooth;
- TCP/UDP;
- documented vendor API.

Data normalization priority is:

```text
native radio protocol
        |
approved gateway
        |
CoT and/or MQTT
        |
field services
```

PyTAK is used for CoT transport where appropriate.

Dire Wolf remains the preferred initial open-source AX.25/APRS software modem candidate for amateur packet workflows.

Amateur RF remains off by default and requires the distinct control-operator role defined by the CONOPS.

---

# 24.5 Local Time Architecture

## 24.5.1 Time Sources

**FML-ADR-042 - SELECTED**

Every production MULE hardware block must provide a battery-backed hardware real-time clock or equivalent retained local time source.

The software time hierarchy is:

```text
approved GNSS/NTP source when available
            |
          chrony
            |
     local MULE system time
            |
   peer/local NTP service as required
            |
 logs / TAK / certificates / MQTT / audit
```

GNSS is optional mission hardware, not a prerequisite for baseline boot.

WAN time is opportunistic and never the only time source.

## 24.5.2 Boot and Trust Behavior

On boot, MULE evaluates whether retained time is plausible before trust-sensitive operations proceed.

If local time is invalid or exceeds the approved uncertainty/skew threshold:

- the node enters a `TIME_DEGRADED` state;
- certificate validity/expiry checks do **not** fail open;
- basic local networking may continue where safe;
- trust-sensitive enrollment, credential renewal, and authoritative service promotion may be restricted;
- the operator receives a clear recovery indication.

**TBR-TIME-01** establishes:

- acceptable RTC drift/holdover;
- certificate-validation skew tolerance;
- when peer/GNSS time may correct a node automatically;
- behavior when sources disagree;
- maximum disconnected mission duration before time uncertainty becomes operationally significant.

## 24.5.3 Hardware Trade Input

The primary compute/carrier trade must account for:

- RTC availability;
- backup-cell interface;
- RTC current draw;
- optional GNSS/PPS interface;
- secure/time-state retention through battery replacement.

Time is therefore a hardware architecture input, not merely a software utility.

# 25. Power, Compute, and Physical Host Architecture

## 25.1 Power Is a Critical Architecture Driver

**TBR-PWR-01 - CRITICAL / FIRST HARDWARE TRADE**

Power testing is not a late validation activity. It is a primary input to compute, radio, service-hosting, enclosure, and battery architecture.

The initial hardware architecture will not be locked until representative measurements exist for:

1. host idle with all required radios initialized;
2. EUD AP + representative EUD clients;
3. normal HaLow MANET operation;
4. representative TAK/local-service load;
5. high-throughput inter-node transfer / replication load;
6. active shared-service-host load;
7. representative LoRa activity;
8. combined worst credible mission load.

The resulting model must answer:

- average watts;
- peak watts;
- 8-hour energy requirement;
- battery reserve margin;
- pack mass;
- 24-72 hour pack/charging sustainment burden;
- service-host runtime penalty;
- cold-weather derating;
- charger/external-power burden.

The CONOPS 8-hour single-pack endurance value remains an operational objective, not permission to build an impractically heavy battery.

If TBR-PWR-01 demonstrates that the four-radio, one-host architecture cannot meet 8 hours with an acceptable operator-carried pack mass and reasonable reserve, the program will:

1. first evaluate architecture reductions that do not violate required capability, including radio consolidation proven by TBR-RF-03 and service-power management;
2. evaluate mission sustainment through approved external/vehicle/alternate packs as permitted by the CONOPS;
3. if the objective still drives disproportionate mass, cost, or complexity, raise a controlled CONOPS change request against the endurance objective rather than conceal the problem in the battery BOM.

The SRR package therefore presents endurance as a measured architecture trade.

## 25.2 Primary Compute Hardware Trade

No compute module is the production baseline yet.

The hardware trade must include, at minimum:

- Raspberry Pi CM4-class;
- Raspberry Pi CM5-class;
- at least one low-power industrial SBC family with a credible Linux/HaLow integration path.

CM4 remains relevant because of lower resource/power potential and public production commitment through at least January 2034.

CM5 remains relevant because it provides substantially greater compute/RAM/I/O capability and public production commitment through at least January 2036.

Neither wins before measurement.

The selected host must satisfy:

- controlled mounting;
- robust local storage;
- required RAM/CPU;
- reliable Ethernet;
- EUD AP interface;
- high-rate inter-node radio interface;
- HaLow host interface;
- LoRa interface;
- RTC;
- optional GNSS;
- stable power input;
- thermal operation inside the intended enclosure;
- hardware lifecycle suitable for fleet sustainment;
- current Linux support.

## 25.3 Compute and Memory Budget

**TBR-COMP-01 - CRITICAL**

The one-host architecture requires an explicit compute and memory model alongside the power model.

Measure and size, at minimum:

- baseline Debian/network stack;
- hostapd/EAP;
- batman-adv and mesh telemetry;
- OpenTAKServer processes;
- RabbitMQ;
- PostgreSQL if selected;
- HAProxy;
- Mission Trust Service;
- MULE service controller;
- MULE Status Aggregator;
- representative rootless browser/file/chat services;
- observability/exporters;
- failover/synchronization workload.

The budget must define:

- normal RAM utilization;
- peak RAM utilization;
- swap policy;
- CPU utilization under normal and worst representative load;
- reserve margin;
- OOM behavior;
- cgroup/service priority.

The host hardware is not selected until the resource model and power model agree.

## 25.4 Radio Integration

Production radios should be internally retained modules rather than externally protruding USB dongles where practical.

An M.2 physical form factor may still use USB signaling. The architecture values M.2/internal modules primarily for:

- controlled mechanical retention;
- shielding;
- antenna topology;
- repeatability;
- thermal path;
- cable management.

The interface technology is selected based on the radio/module's supported host interface, not on an assumption that M.2 implies PCIe transport.

The power/BOM model assumes the four radio functions in §5.2 until TBR-RF-03 proves consolidation.

### 25.4.1 Antenna Planning Envelope

Exact spatial-stream and antenna counts remain TBR outputs.

For mechanical-envelope planning, the conservative reference case assumes:

- EUD AP: up to 2×2 MIMO;
- high-rate inter-node Wi-Fi: up to 2×2 MIMO;
- HaLow: one primary RF feed unless selected hardware requires more;
- LoRa: one RF feed.

That reference case produces **up to six primary RF antenna/feed positions**.

Optional GNSS may add a seventh RF feed/antenna position.

This is a mechanical planning envelope, not a requirement that all six/seven connectors be external bulkheads.

TBR-RF-03 and TBR-CARRIER-01 must determine:

- actual stream count;
- internal versus external antennas;
- diversity/MIMO requirements;
- approved connector family;
- tactile differentiation;
- replacement method;
- minimum antenna spacing;
- pigtail count and loss;
- snag/guarding strategy.

The enclosure must not be dimensioned around the earlier three-radio mental model.

## 25.5 Battery and Charge-System CI Family

The battery/charge system is its own configuration-item family.

The production battery is not a hobby GPIO battery hat or loose-cell holder.

It is an engineered field-replaceable assembly using approved 18650 cells and including, as applicable:

- matched cells;
- BMS/protection;
- fuse;
- temperature sensing;
- controlled charge path;
- keyed connector;
- retention mechanism;
- labeling/serialization;
- inspection and replacement criteria.

The CI family also includes the approved charger and charge-while-operating path because CONOPS §62 makes simultaneous external-power operation and battery maintenance an architecture requirement.

The carrier-board trade therefore includes:

- external DC input;
- charger/BMS interaction;
- current limit;
- thermal behavior while charging;
- source switchover;
- brownout behavior;
- telemetry;
- safe low-voltage shutdown.

Exact topology and capacity remain TBD until TBR-PWR-01 closes.

## 25.6 Carrier Board Trade

A custom or semi-custom carrier board remains deferred unless prototype evidence justifies it.

The carrier-board trade begins now because it may materially improve:

- power distribution;
- battery/charger interface;
- module retention;
- internal RF mounting;
- bulkhead RF routing;
- RTC/GNSS interfaces;
- status/control interfaces;
- repeatability across the fleet.

**TBR-CARRIER-01** closure evidence includes:

- per-unit assembly time;
- number of hand-terminated electrical/RF connections;
- repeatability across multiple prototypes;
- field-serviceability;
- mechanical retention;
- power loss;
- RF path loss;
- BOM cost;
- volunteer-builder skill burden.

A custom PCB is approved only if this evidence shows that a commercial carrier/wiring approach materially harms repeatability, fieldability, or safety.

## 25.7 Thermal Architecture Trade

**TBR-THERM-01 - CRITICAL**

Power consumption and thermal rejection are related but separate architecture trades.

TBR-THERM-01 determines whether the selected one-host/radio configuration can maintain required Network Plane responsiveness and mission-service performance across the intended field thermal envelope.

The same instrumented test rig used for TBR-PWR-01 should collect thermal evidence to avoid duplicate prototype builds.

Measure, as applicable:

- processor temperature;
- radio/module temperature;
- battery/BMS/charger temperature;
- enclosure internal temperature;
- ambient temperature;
- thermal throttling;
- packet loss/latency while thermally constrained;
- service-host performance;
- solar-load sensitivity where practical;
- passive-versus-active cooling behavior.

The trade must compare consequences of:

- passive conductive enclosure/heatsink design;
- vents;
- fan-assisted cooling;
- fanless industrial SBC alternatives;
- compute/radio duty-cycle reduction.

A fan is not assumed. If required, the design must account for its:

- power;
- acoustic signature;
- mechanical lifetime;
- dust/water ingress path;
- field replaceability.

**Owner:** Power/Mechanical + Platform.  
**Closure gate:** before hardware/enclosure PDR.

## 25.8 Local Storage Endurance

**FML-ADR-050 - SELECTED PRINCIPLE**

The primary MULE storage path must be selected and configured for sustained field-service writes, not only nominal capacity.

Write-producing workloads include:

- PostgreSQL/WAL where selected;
- RabbitMQ state;
- journald;
- application logs;
- Prometheus/local telemetry where retained;
- TAK mission data;
- audit/security logs;
- update/rollback image activity.

Architecture rules:

1. SD-card storage is not the production database/system-state baseline.
2. eMMC/NVMe endurance and vendor lifecycle are inputs to TBR-HW-01.
3. journald receives explicit size/retention caps.
4. application logs use rotation and bounded retention.
5. high-rate observability data is aggregated/downsampled or forwarded rather than retained indefinitely on-node.
6. derived/rebuildable telemetry is purged before mission-critical state.
7. database durability settings may be tuned only with documented data-loss semantics.
8. storage health/endurance indicators are included in maintenance checks where the hardware exposes them.

TBR-HW-01 closure evidence must include:

- storage technology;
- rated endurance where published;
- expected write workload;
- capacity reserve;
- SMART/NVMe/eMMC health visibility where available;
- replaceability/reimage procedure.

Exact byte/day limits are TRD/qualification outputs after representative service testing.

# 26. Failure Domains

The single-host architecture intentionally consolidates the Network Plane and Mission Service Plane into one primary compute failure domain.

| Failure | Expected Result |
|---|---|
| Ordinary application/container failure | Network Plane remains; affected service restarts or remains unavailable |
| TAK process failure | peer ATAK remains; shared-service recovery begins |
| Service namespace failure | native network/RF functions remain if host/kernel is healthy |
| Host OS/kernel/primary compute failure | that MULE loses both primary network and hosted-service capability |
| HaLow failure | high-rate IP if available; LoRa remains independent |
| High-rate Wi-Fi failure | HaLow MANET remains |
| LoRa gateway process failure | IP services remain; native Meshtastic radio may continue if independently implemented |
| WAN/Tailscale failure | local MULE network/services remain |
| TAK host failure | peer ATAK remains; S2 recovery begins |
| Unsafe/no-authority recovery condition | no automatic authoritative promotion |
| Thermal limit / sustained throttling | preserve Network Plane priority; shed/degrade S3 then nonessential S2 workload; raise THERMAL_DEGRADED; controlled shutdown if safe temperature cannot be maintained |
| Local battery depletion | graceful shutdown where remaining energy permits |
| Root filesystem corruption / failed update | boot known-good rollback image; node remains out of ready-spare status until revalidated |
| Mission-data/storage corruption | preserve network plane where host remains bootable; affected stateful services become DEGRADED/NON-AUTHORITATIVE; restore from validated backup/standby before authority is claimed |
| External shared host loss | local S0/S1 capabilities remain |
| Team Lead EUD loss | designated alternate can sustain team functions |

The host/kernel is the primary per-node single point of failure.

The v1 mitigation is fleet-level replaceability rather than duplicated internal compute:

- standardized spare MULE;
- common image/configuration;
- peer MULE continuity;
- field swap;
- analog/manual PACE.

The dual-board fallback in Section 2.3 remains available if testing shows this consolidated failure domain is unacceptable.

# 27. Security Boundaries

The architecture defines logical security boundaries on the single Linux host:

```text
Untrusted / external WAN
        |
   WAN interface + nftables
        |
Field EUD / peer MANET domain
        |
 network admission + firewall
        |
  controlled service ingress
        |
 service namespace / rootless OCI
        |
 application authorization
        |
 shared field services
```

Separate controls exist for:

- host management;
- mission trust;
- external RF gateway;
- LoRa gateway;
- WAN overlay;
- mission data;
- administrative credentials.

The shared kernel is explicitly recognized as a weaker isolation boundary than a second physical computer.

The security claim is one-directional: ordinary application contexts are constrained from privileged Network/RF control, but the privileged host network context is not isolated from applications by a separate kernel or processor.

Compensating controls include:

- rootless containers;
- no `CAP_NET_ADMIN` for ordinary apps;
- least-privilege Unix identities;
- network namespaces;
- nftables;
- cgroups;
- protected secrets;
- controlled privileged helpers;
- reproducible recovery;
- short-lived mission credentials;
- service and configuration audit.

No external RF or WAN path provides unrestricted shell, home/private, Vaultwarden, or management access.

Security review at SRR/PDR must explicitly decide whether this shared-kernel boundary is acceptable for the intended unclassified volunteer/training threat model. If not, Section 2.3's physical-separation fallback is activated.

# 27.5 Data-at-Rest Protection and Zeroize

## 27.5.1 Storage Protection Boundary

**FML-ADR-043 - SELECTED PRINCIPLE**

Sensitive local mission data is stored on a LUKS2-class encrypted block volume or an equivalent open, reviewed Linux block-encryption implementation.

The production design should separate:

1. a rebuildable boot/base-system area sufficient to start controlled recovery and baseline networking; and
2. protected mission-sensitive state requiring an approved unlock method.

The architecture rejects an unattended encryption key stored plainly on the same removable/storage media as the encrypted data because that provides little capture protection.

## 27.5.2 Unlock Trade

**TBR-SEC-01** selects the production unlock method before the hardware block is locked.

The trade compares, at minimum:

- operator-entered mission/recovery passphrase;
- TPM 2.0 or equivalent hardware-backed sealed key plus controlled recovery;
- secure-element-assisted mission key architecture;
- combinations of hardware sealing and operator authorization.

The trade must address:

- unattended restart after brownout/battery change;
- captured intact node;
- removed storage media;
- compromised boot image;
- field recovery in gloves/darkness;
- loss of the authorized operator;
- fleet rekey;
- hardware availability and carrier-board impact.

If a hardware root of trust is required, that requirement becomes part of TBR-HW-01/TBR-CARRIER-01.

## 27.5.3 Zeroize

**FML-ADR-044 - SELECTED PRINCIPLE**

MULE zeroize is primarily a **cryptographic erase and trust invalidation** operation.

An approved zeroize action removes or invalidates, as applicable:

- LUKS mission-volume key material/key slots;
- mission-scoped private keys;
- WAN-overlay node identity;
- locally cached mission secrets;
- privileged tokens;
- current mission configuration secrets.

Zeroize does not rely on overwriting every flash block, which is slow and unreliable on flash media.

The mechanism must be executable without WAN.

The exact user/admin activation method, authentication, physical control, and recoverability are Security Architecture/TRD items.

Zeroize must leave the node in a clearly non-operational/untrusted state requiring controlled reprovisioning before return to service.

## 27.5.4 Capture and Rejoin

A captured, missing, or zeroized node remains revocable through the Mission Trust Service and mission authority.

A recovered former node may not simply rejoin with stale trust or state. It enters the controlled maintenance/rekey/reimage path before field reuse.

# 28. Standard Interface Register - SAD Level

| Interface | Preferred Standard / Contract |
|---|---|
| HaLow RF | IEEE 802.11ah |
| IP mesh | IEEE 802.11s + batman-adv/BATMAN-V |
| High-rate inter-node Wi-Fi | IEEE 802.11 conventional Wi-Fi; 802.11s when validated |
| EUD WLAN | IEEE 802.11 AP function; physically separate from high-rate mesh unless TBR-RF-03 closes favorably |
| Local Ethernet | IEEE 802.3 |
| Logical segmentation | Linux namespaces/veth/bridge + nftables; IEEE 802.1Q where useful |
| IP | IPv4 for v1 |
| EUD WLAN admission | 802.1X/EAP-TLS; hostapd integrated EAP server preferred initially |
| TAK/geospatial | CoT / TAK-supported transports |
| Web/API | HTTPS / REST / JSON |
| Message/event integration | MQTT where appropriate |
| Service metrics | Prometheus exposition |
| Mesh telemetry | batman-adv/netlink / batctl normalized by MULE exporter |
| Wi-Fi telemetry/control | nl80211 / `iw` / hostapd/wpa_supplicant control |
| Time | hardware RTC + NTP/chrony; optional GNSS/PPS |
| Service certificates | X.509 / TLS |
| Data-at-rest | LUKS2-class block encryption for protected mission state |
| Containers | OCI |
| Linux service management | systemd |
| Configuration | YAML/JSON/native Linux config templates as appropriate; no production UCI dependency |
| RF packet integration | AX.25/APRS via approved gateway |
| LoRa gateway API | Meshtastic supported serial/TCP API |
| Software deployment | Ansible + pinned packages/images |
| Recovery image | A/B or equivalent bootable known-good rollback path |

The future ICD will assign controlled interface identifiers and exact endpoint contracts.

# 29. Open-Source Implementation Map

| Function | Preferred Project / Standard | SAD Status |
|---|---|---|
| Host OS | Debian 13 stable | SELECTED |
| MANET reference/integration | OpenMANET | SELECTED reference/configuration source |
| Mesh routing | batman-adv / BATMAN-V | SELECTED |
| 802.11s control | wpa_supplicant + standard Linux wireless stack | PREFERRED |
| EUD AP / EAP-TLS | hostapd integrated EAP server | PREFERRED INITIAL |
| Alternate AAA | FreeRADIUS | ALTERNATE if justified |
| Firewall / segmentation | nftables | SELECTED |
| DHCP/DNS | dnsmasq or equivalent mature Linux service | PREFERRED |
| Link configuration | systemd-networkd or equivalent | PREFERRED |
| HaLow drivers | Morse Micro supported Linux stack | PREFERRED |
| Containers | Podman rootless by default | SELECTED |
| Container/system service declarations | Quadlet + systemd | SELECTED |
| TAK server | OpenTAKServer | PREFERRED |
| CoT gateway library | PyTAK | SELECTED |
| LoRa mesh | Meshtastic | SELECTED |
| LoRa-to-TAK | OTS integration / TAK Meshtastic Gateway before custom | PREFERRED |
| PKI | Smallstep step-ca | PREFERRED |
| Application authorization | native RBAC first | SELECTED rule |
| Cross-application policy | Open Policy Agent only when justified | OPTIONAL |
| TCP/HTTP ingress | HAProxy | PREFERRED |
| SQL database | PostgreSQL if state study justifies | PREFERRED/CONDITIONAL |
| Stateful TAK HA mechanism | TBD after state classification | TBR |
| Block encryption | Linux LUKS2 / dm-crypt class | SELECTED PRINCIPLE |
| Time discipline | chrony + hardware RTC | SELECTED |
| Selected file replication | Syncthing | PREFERRED where semantically safe |
| AX.25/APRS modem | Dire Wolf | PREFERRED |
| Host provisioning | Ansible | SELECTED |
| Version control | Git | SELECTED |
| Metrics | Prometheus-compatible exporters | SELECTED interface |
| Local logs | systemd journal / structured app logs | SELECTED interface |
| Boot rollback | A/B or equivalent open Linux update/recovery implementation | SELECTED PRINCIPLE / TBR implementation |

No project in this table is allowed to change a controlled external interface without SAD/ICD change review.

The architecture is OSS-first but not OSS-maximalist: an upstream project is adopted only when it reduces custom implementation without violating the controlled operational concept.

# 29.5 MULE-Original Software Inventory

Governing Principle 10 requires the program to count and justify its own glue.

| Component | Decision / Status | Owner | Why upstream alone is insufficient | Scope limit |
|---|---|---|---|---|
| **MULE Service Controller** | FML-ADR-035 / SELECTED | Platform / Systems | Mission profile, role demand, power, thermal, and residency logic is MULE-specific | Starts/stops approved systemd targets only; not a cluster scheduler |
| **MULE Status Aggregator + Service Authority Registry** | FML-ADR-046 + FML-ADR-049 / SELECTED | Platform / Field UX / SRE | No upstream project provides the exact operator state model or local authoritative-service registry across RF, TAK authority, trust, power, time, storage, and peer health | Read-mostly normalization and local service-host registry; does not elect TAK authority or provide broad configuration authority |
| **Mission Trust Service** | FML-ADR-047 / SELECTED | Security / Identity | Offline signed revocation/policy propagation across MULEs is subsystem-specific | Not a CA; validates/distributes signed mission trust state |
| **RF Coexistence Policy Service** | TBR-RF-02 / NOT YET SELECTED | RF + Platform | May be needed only if supported radio/driver controls require cross-radio scheduling | Must remain a thin policy layer; no driver fork unless separately approved |
| **Gateway Translation Layer** | FML-ADR-048 / SELECTED RULE | TAK / Integration | Some external radio protocols may need normalization to CoT/MQTT | Existing OTS/Meshtastic/PyTAK integration first; custom code only for missing protocol semantics |

Any new MULE-original daemon requires:

1. an ADR or explicit TBR status;
2. named owner;
3. interface contract;
4. reason an existing OSS project cannot perform the function;
5. unit/health test;
6. resource budget;
7. sustainment owner.

Original software count is therefore a controlled architecture metric, not an incidental implementation detail.

# 30. SRR Internal Consistency Review

The v0.31 architecture incorporates review from:

- systems architecture;
- configuration management;
- network engineering;
- RF/spectrum engineering;
- Linux/platform engineering;
- distributed systems/SRE;
- security/identity;
- TAK integration;
- power/mechanical;
- builder/production;
- field operations;
- sustainment/configuration management;
- test/verification.

## 30.1 Findings Addressed by Architecture

These findings are addressed by a selected architecture direction but remain open until validating evidence is complete.

| Finding | Architecture Response | Validating CONOPS Stage | Evidence State |
|---|---|---:|---|
| Network OS vs application host | one Debian host; logical plane separation; dual-board fallback | 1, 7, 8 | OPEN until test |
| OpenMANET firmware dependency | consume OpenMANET as reference/configuration; native Linux stack | 2 | OPEN until mesh equivalence test |
| EUD AP vs high-rate mesh radio | separate logical functions; assume separate physical radios until concurrency proven | 1, 4, 7 | OPEN / TBR-RF-03 |
| Kernel/driver lifecycle | pinned compatibility set + staged promotion smoke test | 1, 2, 13 | OPEN / TBR-LINUX-01 |
| Trustworthy offline time | hardware RTC + chrony + TIME_DEGRADED behavior | 1, 9 | OPEN / TBR-TIME-01 |
| Data-at-rest / unattended unlock | LUKS2-class protected volume; unlock method deferred | 9 | OPEN / TBR-SEC-01 |
| Zeroize | cryptographic key/trust invalidation | 9 | OPEN until destructive test |
| Peer ATAK vs routed service hosting | EUDs remain on validated BATMAN field domain; services use local ingress | 2, 5 | OPEN until scale/failover test |
| Stable service identity vs host movement | local DNS + HAProxy/TCP passthrough | 5 | OPEN until failover test |
| LoRa as degraded bearer vs IP routing | Meshtastic stays separate from IP MANET | 3 | OPEN until degraded-mode test |
| Tailscale vs mission authorization | EUDs excluded from tailnet; application role/scope remains separate | 6, 9 | OPEN until authorization test |
| Stateful availability vs split brain | state classification first; automatic only when authority is provable; admin fallback | 5 | OPEN until partition test |
| Service workload vs routing stability | rootless containers + cgroups + native network priority | 1, 7 | OPEN / TBR-COMP-01 |
| EMCON usability | tactile/local indication plus multi-layer control | 8, 10 | OPEN until field demo |
| Open-source sustainment burden | one OS lifecycle + dependency register + owner review | 13 | OPEN until process inspection |
| Traceability integrity | clause-complete §35 with explicit PRESENT/PARTIAL/N/A status | SRR / 13 | OPEN until formal RTM baseline |
| Service discovery/authority ownership | folded into Status Aggregator under FML-ADR-049 | 5 | OPEN until failover test |
| Thermal closure | explicit TBR-THERM-01 sharing the power test rig | 7, 8 | OPEN |
| Storage endurance | bounded write policy + endurance-qualified storage criteria | 1, 13 | OPEN until hardware/load evidence |
| Kernel-release HIL ownership | dedicated two-node bench + release owner | 2, 13 | OPEN until bench commissioned |
| TBR schedule concentration | named-person assignment required at SRR; owner concentration becomes program risk | SRR / 13 | OPEN |

## 30.2 TBR Register and Closure Criteria

No calendar schedule has yet been baselined for FML/MULE. This SAD therefore does not invent dates.

**SRR exit action:** the Program Owner assigns one named individual and one calendar target date to every open TBR.

Where a person has not yet been designated, the field is explicitly marked `TBD-SRR` rather than hiding the gap behind a functional organization.

| TBR | Pri. | Function Owner | Named Owner | Depends On | Decision / Question | Closure Evidence | Closure Gate | Target Date |
|---|---:|---|---|---|---|---|---|---|
| **TBR-PWR-01** | 1 | Power/Mechanical | TBD-SRR | RF-03 planning case | Does the one-host/four-radio planning architecture close endurance with acceptable mass? | Measured load states; battery/charge model; cold derating; pack mass; service-host penalty; change-control disposition if 8h is disproportionate | Before hardware PDR / Stage 7 | TBD-SRR |
| **TBR-COMP-01** | 2 | Platform + TAK | TBD-SRR | TAK prototype stack | What CPU/RAM reserve is required for the complete one-host service catalog? | Measured RAM/CPU/OOM/cgroup behavior with representative OTS/RabbitMQ/Postgres/services | Before host selection / Stages 1, 5 | TBD-SRR |
| **TBR-THERM-01** | 3 | Power/Mechanical + Platform | TBD-SRR | PWR test rig; candidate host/radios | Can the host/radios operate across field thermal load without unacceptable throttling or cooling burden? | Temperature/throttle/network-performance data; passive/fan trade; solar/ambient sensitivity | Before hardware/enclosure PDR / Stages 7, 8 | TBD-SRR |
| **TBR-RF-03** | 4 | Network + RF | TBD-SRR | candidate Wi-Fi hardware | Can EUD AP and high-rate inter-node mesh share one physical radio, and what stream/antenna count results? | Concurrent AP+mesh, channel, roaming, multicast, recovery, power, spatial-stream and antenna/feed-count test | Before RF/BOM lock / Stages 1, 4 | TBD-SRR |
| **TBR-TIME-01** | 5 | Platform + Security | TBD-SRR | RTC/GNSS candidate | What RTC/GNSS/skew/holdover behavior preserves certificate and authority correctness offline? | RTC drift; battery-change holdover; invalid-time boot; conflicting-source test; HA timing constraints | Before HW/HA/security lock / Stages 1, 9 | TBD-SRR |
| **TBR-SEC-01** | 6 | Security + Hardware | TBD-SRR | candidate trust/storage hardware | How is protected mission storage unlocked on a headless captured-risk node? | Passphrase vs TPM/secure-element trade; capture/brownout/recovery/zeroize tests | Before hardware block lock / Stage 9 | TBD-SRR |
| **TBR-HW-01** | 7 | Systems + Builder | TBD-SRR | PWR-01, COMP-01, THERM-01, RF-03, TIME-01, SEC-01 | Which CM4/CM5/industrial-SBC class becomes the first hardware block? | Linux support, RAM/storage/endurance/I/O, RTC/trust hardware, radios, measured power/thermal, lifecycle, cost | Before hardware PDR / Stages 1, 7, 8 | TBD-SRR |
| **TBR-LINUX-01** | 8 | Linux/Platform | TBD-SRR | candidate host + HaLow hardware; REC-01 concept | Can HaLow remain reliable across the controlled kernel lifecycle? | Driver install/rebuild, mesh formation, HIL kernel-promotion pipeline, reboot, rollback, sustained traffic | Before production software PDR / Stage 2 | TBD-SRR |
| **TBR-TAK-01** | 9 | TAK + SRE | TBD-SRR | representative TAK build | What TAK state is mission-critical and where is it stored? | State inventory; different-node restore; Postgres DataSync/mission-package/cert/map-cache tests | Before HA architecture lock / Stage 5 | TBD-SRR |
| **TBR-RF-01** | 10 | Network + RF | TBD-SRR | RF-03 disposition | Can high-rate Wi-Fi operate reliably as a second 802.11s/batman interface? | Multi-node mobility/load; recovery; multicast/bulk transfer | Before PDR / Stage 4 | TBD-SRR |
| **TBR-RF-02** | 11 | RF/Spectrum | TBD-SRR | final radio topology from RF-03 | What LoRa availability is preserved during HaLow recovery and what supported controls exist? | Desense; supported-control inventory; recovery; no-fork assessment | Before RF design lock / Stage 3 | TBD-SRR |
| **TBR-HA-01** | 12 | SRE + TAK | TBD-SRR | TAK-01, TIME-01 | What is the simplest safe automatic TAK recovery mechanism? | Primary loss, partition, stale standby, rejoin, no-authority, admin recovery | Before CDR-lite / Stage 5 | TBD-SRR |
| **TBR-REC-01** | 13 | Platform + CM | TBD-SRR | HW-01 boot/storage path | What A/B or equivalent bootable rollback implementation is used? | Failed-update/corrupt-root/radio-driver rollback without WAN | Before production image baseline / Stages 1, 13 | TBD-SRR |
| **TBR-ID-01** | 14 | Security/Identity | TBD-SRR | TIME-01, mission identity model | Is a common browser-service IdP required beyond native app RBAC? | Role/scope workflow; offline login; admin burden | Before Security Architecture lock / Stages 1, 9 | TBD-SRR |
| **TBR-NET-01** | 15 | Network | TBD-SRR | partner/interoperability context | Retain 10.41.0.0/16 or select another field prefix? | Collision analysis + interoperability exercise | Before ICD baseline / Stages 2, 11 | TBD-SRR |
| **TBR-CARRIER-01** | 16 | Builder + Power + RF | TBD-SRR | HW-01, RF-03, PWR-01, THERM-01, TIME-01, SEC-01 | Does repeatability justify custom/semi-custom carrier hardware? | Assembly time, hand terminations, repeatability, RF/power loss, serviceability, cost | Before production hardware-block lock / Stages 8, 13 | TBD-SRR |

No TBR is closed by document wording alone.

A TBR closes only when its listed evidence exists, the named owner accepts the evidence, and the resulting architecture decision is entered into the persistent ADR register.

## 30.3 TBR Dependency Graph

The dependency graph below is the architecture-driven schedule until calendar dates are assigned.

```text
                     TBR-RF-03
                    /    |    \
                   v     |     v
             TBR-PWR-01  |  TBR-RF-01
                   |     |     
                   v     v
             TBR-THERM-01
                   |
TBR-COMP-01 -------+
TBR-TIME-01 -------+
TBR-SEC-01 --------+-------> TBR-HW-01
                               |
                               +------> TBR-REC-01
                               |
                               +------> TBR-CARRIER-01
                               |
                               +------> final TBR-LINUX-01

TBR-TAK-01 --------+
                   +-------> TBR-HA-01
TBR-TIME-01 -------+

TBR-RF-03 ---------> final radio topology ---------> TBR-RF-02
```

Interpretation:

- **HW-01 is a convergence decision**, not an independent early choice.
- **TIME-01 constrains both hardware and HA.**
- **SEC-01 may add a TPM/secure-element requirement and therefore constrains hardware/carrier selection.**
- **RF-03 affects power, thermal, antenna count, high-rate architecture, and coexistence testing.**
- **TAK-01 and TIME-01 gate HA mechanism selection.**

This graph should be used to build the Integrated Test & Evaluation Plan and the first dated program schedule.

# 31. SRR Risk Review

| Risk | Current Architecture Response | SRR Status |
|---|---|---|
| HaLow/LoRa self-interference | separate RF chains + measured coexistence controls | OPEN |
| Flat L2 multicast scaling | BATMAN-V + Stage 2 scale testing + EUD broadcast measurement | OPEN |
| Single active mesh gateway | any MULE capable, one active v1 | ACCEPTED |
| High-rate bearer instability | HaLow remains baseline; routed high-rate fallback | OPEN |
| OpenMANET/OpenWrt dependency drift | OpenMANET as reference/config source; production native Debian/Linux | MITIGATED |
| Shared-kernel compromise affects network plane | rootless apps, namespaces, capabilities, nftables; dual-board fallback | OPEN |
| Host/kernel failure removes one complete MULE | standardized spare / peer MULE / PACE | ACCEPTED |
| Service workload starves routing | cgroups/resource reservations + Stage 1/7 load testing | OPEN |
| Split brain | no automatic authoritative promotion without safe authority proof | OPEN |
| HA complexity creep | state classification before mechanism selection | MITIGATED |
| Offline revocation lag | mission-scoped expiry + Mission Trust Service propagation | ACCEPTED |
| Revocation distribution unassigned | explicit Mission Trust Service | MITIGATED |
| Service scheduler oscillation | systemd targets + damping/residency | MITIGATED |
| Captured node | encrypted state + short-lived trust + revocation/zeroize | OPEN |
| Software supply-chain drift | pinned builds, Git, hashes, dependency register, freeze | MITIGATED |
| Too many upstream lifecycles | single OS baseline + lifecycle ownership | MITIGATED |
| Parent NOMAD-only allocations | PBCR-01 change package | OPEN |
| Battery/endurance infeasible | power model promoted to first hardware trade | OPEN |
| External USB/dongle fragility | internal retained modules + controlled bulkhead RF | MITIGATED |
| EUD/high-rate radio undercount | four-radio planning baseline until TBR-RF-03 closes | MITIGATED |
| Kernel update breaks HaLow fleet-wide | pinned compatibility set + staged kernel promotion + rollback | OPEN |
| Invalid RTC causes credential failure or fail-open behavior | battery-backed RTC + TIME_DEGRADED; no fail-open | OPEN |
| Encrypted storage cannot unlock after field reboot | TBR-SEC-01 before hardware lock | OPEN |
| Sensitive data survives zeroize | cryptographic erase design + Stage 9 destructive verification | OPEN |
| One-host RAM exhaustion | explicit compute/memory budget + cgroups | OPEN |
| Custom carrier creates sustainment burden | carrier board only if prototype evidence justifies | OPEN |
| Thermal throttling or enclosure heat soak degrades routing/services | TBR-THERM-01 + Network Plane priority + service shedding | OPEN |
| Antenna/bulkhead count creates snag, spacing, or enclosure failure | six-feed planning envelope + TBR-RF-03/CARRIER | OPEN |
| Service-authority registry becomes hidden SPOF/custom daemon | registry folded into existing Status Aggregator; HA authority remains service-specific | MITIGATED |
| eMMC/NVMe write wear corrupts state over fleet life | FML-ADR-050; bounded logs/telemetry + endurance criterion | OPEN |
| Kernel release pipeline degrades into manual checklist | permanent two-node HIL bench + named release owner required | OPEN |
| One individual owns too many TBRs/release functions | named-owner assignment and owner-concentration review at SRR | OPEN |
| Practitioner/AHJ review arrives after design lock | external review actions initiated before PDR | OPEN |

# 32. SRR Entry Assessment

The MULE subsystem is ready for SRR package review with SAD v0.31 as the preferred architecture draft.

The architecture is internally coherent with FML/MULE CONOPS v1.01 and explicitly preserves the CONOPS automatic-recovery objective, local-first operation, peer ATAK fallback, role/scope separation, EUD exclusion from the WAN overlay, LoRa degradation path, and field-replaceable appliance philosophy.

The v0.31 architecture intentionally simplifies v0.1:

- one primary compute element instead of two;
- one supported Linux OS lifecycle instead of OpenWrt + Debian;
- OpenMANET consumed as reference/configuration knowledge rather than mandatory firmware;
- no hypervisor in the baseline;
- no Patroni/etcd selection before TAK state is understood;
- rootless containers by default;
- native privileged services only where hardware/network control requires them;
- explicit Mission Trust Service;
- battery and carrier treated as configuration-managed architecture items.

The only known conflict with the existing inspectable parent architecture remains intentional and controlled: older parent documents allocate TAK and communications gateway services exclusively to NOMAD. MULE requires PBCR-01 before parent-system baseline closure.

The architecture does not require:

- a custom MANET routing protocol;
- a custom HaLow PHY;
- a custom LoRa PHY;
- OpenWrt in production;
- a hypervisor;
- Kubernetes;
- a proprietary service mesh;
- a new TAK protocol;
- a custom PKI;
- EUD Tailscale membership;
- Patroni or etcd specifically;
- two general-purpose compute boards.

The architecture does require evidence before PDR/CDR for:

- power/endurance;
- selected host hardware;
- Debian/Morse Micro HaLow integration;
- high-rate Wi-Fi mesh behavior;
- RF coexistence;
- TAK state classification and continuity;
- mission identity lifecycle;
- physical/carrier integration.

No unresolved issue currently requires reopening the CONOPS.

## 32.1 External Practitioner and Independent Review Actions

The CONOPS practitioner-review gates and the v0.31 architecture require review beyond the internal engineering team.

Before operational fielding, the program must obtain the practitioner confirmations already required by the CONOPS, including:

- RF compliance;
- amateur control operator;
- battery safety;
- privacy;
- applicable AHJ/incident-command interoperability review.

These reviews do not need to wait for a final production unit.

The SRR/PDR work plan should also include:

1. **Thermal/mechanical enclosure reviewer**  
   Review heat rejection, environmental sealing, bulkhead density, gloved access, and enclosure materials.

2. **EMC/pre-compliance reviewer**  
   Review the assembled multi-radio test approach, antenna/feed layout, self-interference, and pre-compliance chamber strategy.

3. **Independent shared-kernel security reviewer**  
   Review FML-ADR-021/FML-ADR-030 and determine whether one-kernel logical isolation is acceptable for the intended threat model. A negative finding is an explicit trigger for the dual-compute fallback in §2.3.

4. **Original-software maintainer review**  
   One or more actual developers/maintainers review the service controller, Status Aggregator/Authority Registry, Mission Trust Service, gateway glue, and any coexistence service for realistic implementation and sustainment burden.

5. **Equipment safety reviewer**  
   Review lithium battery, charge-while-operating path, thermal behavior, vehicle/home storage, connectors, fusing, and fault containment.

6. **AHJ/operational stakeholder conversation**  
   Validate what external incident organizations would actually accept, consume, or ignore from MULE so interoperability work is driven by real operational utility.

The AHJ/operational stakeholder conversation may begin before the final hardware architecture is selected.

# 33. Post-SRR Engineering Sequence

SAD v0.311 marks the transition from primarily document-driven architecture development to **evidence-driven engineering**.

Further prose refinement is not expected to close the architecture-driving TBRs.

## 33.1 Artifacts to Write Now

Three low-cost artifacts should proceed immediately:

1. **FML/MULE ADR Register v0.1**  
   Capture the persistent FML-ADR decisions and supersession history while fresh.

2. **PBCR-01**  
   Record the parent Homelab change from NOMAD-only TAK/communications allocation to the controlled MULE Field Service Plane.

3. **FML/MULE Integrated Test & Evaluation Plan (ITEP) v0.1**  
   Convert the TBR dependency graph and CONOPS qualification stages into executable test campaigns, test rigs, instrumentation, prototype quantities, evidence paths, owners, and schedule.

The ITEP is the next major program-control document.

## 33.2 Evidence to Produce Next

The first ITEP tranche should produce, in dependency order:

1. combined **Power / Compute / Thermal characterization**;
2. EUD AP / high-rate radio concurrency and stream/antenna characterization;
3. primary compute hardware trade evidence;
4. Linux/HaLow kernel-lifecycle HIL evidence;
5. TAK state classification and different-node recovery evidence;
6. RF coexistence evidence;
7. time/holdover evidence;
8. storage-encryption/unlock/zeroize evidence;
9. recovery-image evidence.

Where practical, one instrumented rig should collect power, temperature, CPU, RAM, and network performance simultaneously.

## 33.3 Prototype/Test BOM

The next BOM is a **prototype/test BOM**, not a production baseline.

It should buy the minimum alternatives and instrumentation required to resolve the critical TBRs, including:

- at least two representative node builds;
- candidate CM4/CM5/industrial SBC path as justified by the ITEP;
- HaLow;
- EUD AP radio;
- high-rate inter-node radio;
- LoRa/Meshtastic;
- representative antennas/feedlines;
- RTC/GNSS candidates as required;
- candidate protected storage/trust hardware;
- bench power/current instrumentation;
- temperature instrumentation;
- HIL release-bench hardware.

The prototype BOM answers:

> What must be purchased to make the architecture decisions?

It is not the production answer.

## 33.4 TRD, ICD, Production BOM, and Verification Matrix

These documents continue to exist, but their baselining now follows evidence.

**TRD:**  
Maintain a derived-requirement backlog and qualitative SHALLs now. Do not freeze quantitative power, thermal, RAM, endurance, storage, recovery, or radio-concurrency values until the relevant TBR evidence exists.

**ICD:**  
Maintain stable logical/protocol interfaces now. Do not freeze host-radio buses, antenna/connector counts, battery/charge interfaces, RTC/GNSS hardware, secure-element interfaces, or physical carrier details before the hardware trades close.

**Production BOM/CI Registry:**  
Do not baseline until HW-01, PWR-01, COMP-01, THERM-01, RF-03, TIME-01, SEC-01, and the first Linux/HaLow evidence are sufficiently mature.

**Verification Matrix / ATP:**  
Use the ITEP and §35 as predecessors. Formal verification methods and evidence paths should be derived from actual test architecture, not guessed in advance.

## 33.5 Architecture Feedback Loop

```text
CONOPS v1.01
      |
      v
SAD v0.311
      |
      v
ITEP + Prototype/Test BOM
      |
      v
instrument / test / measure
      |
      +--> power / thermal / compute
      +--> RF / mesh / concurrency
      +--> kernel / recovery
      +--> TAK state / continuity
      +--> time / security / storage
      |
      v
SAD evidence update
      |
      +--> TRD quantitative baseline
      +--> ICD physical-interface baseline
      +--> production BOM/CI lock
      +--> Verification Matrix / ATP
```

If measured evidence disproves a CONOPS objective, the response is controlled CONOPS change, not hidden architecture heroics.

## 33.6 Stage 10 Field Quick Reference

The field quick-reference package must include operator action for `NO_SAFE_AUTHORITY`:

- continue peer ATAK/local PACE;
- do not treat stale shared state as authoritative;
- contact the designated administrator/recovery authority when the mission requires shared-service recovery;
- use approved non-digital/manual coordination if shared-service recovery is unavailable.

This is a training/operations deliverable, not a new service dependency.

# 34. External Technical Baseline and Source Register

This section separates sourced implementation facts from architecture decisions.

A source entry supports only the claim listed. It does not by itself select a product.

| Source ID | Source / Evidence | Claim Supported | Architecture Use |
|---|---|---|---|
| SR-001 | Debian Project, "Updated Debian 13: 13.6 released", 2026-07-11, https://www.debian.org/News/2026/20260711.en.html | Debian 13.6 "trixie" is the current stable point release at issue and stable receives security corrections | Host OS/current-stable baseline |
| SR-002 | OpenMANET firmware release 1.7.0, https://github.com/OpenMANET/firmware/releases | OpenMANET 1.7.0 is latest stable release at issue; uses OpenWrt 24.10 base; exposes OpenMANET configuration/mesh behavior and second batman interface work | Prototype/reference baseline, not production OS requirement |
| SR-003 | OpenMANET firmware repository, https://github.com/OpenMANET/firmware | OpenMANET is an OpenWrt-based firmware project integrating ATAK/multicast and supported SBC/HaLow configurations | Reference/configuration source |
| SR-004 | OpenMANET openmanetd, https://github.com/OpenMANET/openmanetd | openmanetd provides OpenMANET-specific mesh/topology/configuration API functionality | Prototype/reference only; production native telemetry does not depend on it |
| SR-005 | Morse Micro MM8108 product brief/data sheet, https://www.morsemicro.com/resources/datasheets/modules/MM8108-MF15457_Data_Sheet.pdf | MM8108 supports USB 2.0 High-Speed, SDIO 2.0, and SPI host interfaces | Carrier/radio host-interface trade |
| SR-006 | Gateworks GW16167 MM8108 M.2 data sheet, https://www.morsemicro.com/wp-content/uploads/2026/02/GW16167-Datasheet.pdf | A production-style M.2 E-key MM8108 module can use USB signaling and controlled MMCX antenna connection | §25.4 statement that M.2 does not imply PCIe; mechanical/RF integration example |
| SR-007 | Raspberry Pi CM4 product page, https://www.raspberrypi.com/products/compute-module-4/ | CM4 supports up to 8 GB RAM, eMMC options, PCIe Gen2 x1, optional 2.4/5 GHz Wi-Fi, and production through at least Jan 2034 | Host hardware trade input |
| SR-008 | Raspberry Pi CM5 product page, https://www.raspberrypi.com/products/compute-module-5/ | CM5 supports up to 16 GB RAM, eMMC options, PCIe x1, USB 2/3, optional 2.4/5 GHz Wi-Fi, and production through at least Jan 2036 | Host hardware trade input |
| SR-009 | Raspberry Pi CM4 IO Board page, https://www.raspberrypi.com/products/compute-module-4-io-board/ | Reference carrier includes RTC with battery socket and PCIe/USB/Ethernet expansion | RTC/carrier trade evidence |
| SR-010 | Raspberry Pi CM5 IO Board page, https://www.raspberrypi.com/products/compute-module-5-io-board/ | Reference carrier provides M.2, fan connector, RTC battery socket, and power interfaces; production through at least Jan 2036 | RTC/thermal/carrier trade evidence |
| SR-011 | Morse Micro `morse_driver`, https://github.com/MorseMicro/morse_driver | MM8108 support is provided through an out-of-tree/open Linux driver repository | Kernel/driver lifecycle risk basis |

Source limitations:

- CM4/CM5 lifecycle statements are vendor commitments, not guarantees of availability in every variant.
- OpenMANET/OpenWrt behavior is evidence for the reference implementation, not proof that native Debian reproduces it until Stage 2.
- Morse Micro host-interface support at the silicon/module level is not proof that every carrier/module exposes every interface.
- No source entry substitutes for assembled-device RF compliance testing.

Exact current package/project versions are reverified at release-candidate freeze.

# 35. Preliminary CONOPS-to-SAD Traceability

## 35.1 Scope and Extraction Integrity

The prior v0.2 table was an extraction aid and was not adequate as an SRR traceability claim.

This v0.3 pass corrects the specific defects identified during review:

- the Section 0 modal-convention marker is excluded because it is not a requirement;
- inline SHALL markers are separated so one row cannot swallow the next marker;
- colon-led SHALLs retain their complete enumerated content;
- document-review/change-control SHALLs are separated from system architecture requirements;
- each architecture row carries a specific SAD allocation or is explicitly marked N/A-SAD;
- `PRESENT` means architecture text currently exists; `PARTIAL` means downstream policy/TRD/ICD/security content is still required;
- the table cross-references the TBR or qualification stage that is expected to produce evidence where identifiable.

Source `[SHALL]` markers: **145**.

System/operational/policy clauses traced below: **140**.

Document-governance clauses handled separately in §35.3: **4**.

This remains a preliminary SRR allocation, not the baselined Verification Matrix.

## 35.2 Clause-Complete Architecture Traceability

| Trace ID | CONOPS § | Complete SHALL clause | SAD allocation | Content status | Evidence / downstream |
|---|---:|---|---|---|---|
| C1-01 | 1 | The system shall be local-first and WAN-independent. Loss of WAN shall<br>not remove baseline local communications. | 1, 18 | PRESENT | Stage 1/6 |
| C2-01 | 2 | The MULE field subsystem shall be validated independently before the<br>parent Homelab architecture is rebaselined. | 0.5-0.6, 32-33 | PRESENT | PBCR-01 / Stage 12 |
| C4-01 | 4 | Organizations employing the system shall maintain mission-appropriate<br>PACE procedures that do not depend on MULE. | N/A-SAD | N/A-SAD | OPS/POLICY; Stage 10/13 |
| C4-02 | 4 | Recurring team training shall include exercise periods in which MULE<br>is intentionally unavailable for a meaningful portion of the problem. | N/A-SAD | N/A-SAD | OPS/POLICY; Stage 10/13 |
| C5-01 | 5 | All normal fielded MULEs within an approved hardware block shall use<br>materially common:<br>* compute hardware;<br>  * approved radio interfaces;<br>  * enclosure architecture;<br>  * battery interface;<br>  * approved firmware;<br>  * approved service catalog;<br>  * management stack;<br>  * security architecture. | 19.1, 19.5, 25 | PRESENT | Stage 13 |
| C5-02 | 5 | Separate leader, relay, gateway, or TAK-server hardware<br>variants shall not be part of the baseline concept. | 2.2, 15 | PRESENT | Stage 1/13 |
| C5-03 | 5 | A spare MULE shall be capable of replacing any normal MULE within<br>the same approved hardware block. | 19.1, 26 | PRESENT | Stage 13 |
| C5-04 | 5 | Each hardware block shall:<br>* satisfy the same controlled interfaces;<br>  * run the same approved mission-service model;<br>  * meet the same functional requirements;<br>  * remain operationally interchangeable within its qualification boundary;<br>  * pass unit-level acceptance testing before fielding. | 19.1, 19.5, 30.2 | PRESENT | Stage 13 |
| C5-05 | 5 | Hardware substitutions shall be requalified against applicable RF,<br>power, software, interface, and acceptance criteria. | 19.5, 30.2 | PRESENT | Stage 13 |
| C5-06 | 5 | Required field capability shall not depend on:<br>* Internet;<br>  * commercial cellular service;<br>  * Starlink;<br>  * Tailscale or any equivalent overlay;<br>  * home Homelab connectivity;<br>  * NOMAD;<br>  * a central TAK Server. | 1, 18, 26 | PRESENT | Stages 1-6 |
| C5-07 | 5 | The system shall lose capability in a controlled order:<br>High-throughput IP<br>        /<br>        v<br>    Range-oriented IP<br>        /<br>        v<br>    LoRa / Meshtastic<br>        /<br>        v<br>    Local digital operation<br>        /<br>        v<br>    Analog / manual PACE | 4-8, 26 | PRESENT | Stages 2-4 |
| C5-08 | 5 | Service placement and route selection shall use damping, persistence,<br>minimum-residency, or threshold logic sufficient to prevent oscillation. | 15 | PRESENT | Stage 5 |
| C6-01 | 6 | Maximum EUD count, total mesh population, acceptable peer-to-peer TAK<br>scale, and performance by hop count shall be established through testing under<br>Section 78, Stage 2. | 4.3, 30.2 | PRESENT | TBR-RF-01/RF-03; Stage 2 |
| C7-01 | 7 | A Unit Member shall not receive infrastructure administration<br>privileges. | 16.4-16.5, 17, 27 | PRESENT | Stage 9 |
| C7-02 | 7 | A Team Lead shall not automatically receive privileged access to<br>another team's scope. | 16.4-16.5, 17, 27 | PRESENT | Stage 9 |
| C7-03 | 7 | Each team shall be capable of designating one or more alternates. | 15, 16.4 | PARTIAL | TRD/OPS; Stage 1/9 |
| C7-04 | 7 | Team capability shall not depend on one person's EUD remaining awake or<br>associated with the network. | 15 | PRESENT | Stage 1 |
| C7-05 | 7 | Field administrative authority shall not automatically confer<br>organizational root or enrollment-authority privilege. | 16.1-16.5 | PRESENT | Stage 9 |
| C7-06 | 7 | The organization shall maintain a standing function responsible for:<br>* onboarding;<br>  * identity issuance;<br>  * periodic identity review;<br>  * revocation;<br>  * mission credentials;<br>  * node identities;<br>  * re-keying;<br>  * mission configuration packages;<br>  * node re-imaging;<br>  * lost-device response;<br>  * privileged-role review;<br>  * audit records;<br>  * replacement-node preparation. | 19.4, 19.5 | PARTIAL | OPS/CM; Stage 13 |
| C7-07 | 7 | This function shall exist and be staffed before fielding. | 19.4, 19.5 | PARTIAL | OPS/CM; Stage 13 |
| C7-08 | 7 | The organization shall maintain custody records for:<br>* MULE serial and configuration identity;<br>  * hardware block;<br>  * battery packs;<br>  * accessories;<br>  * issue and return dates;<br>  * assigned custodian;<br>  * credential status;<br>  * lost or stolen status. | 19.4, 19.5 | PARTIAL | OPS/CM; Stage 13 |
| C7-09 | 7 | When an amateur-radio gateway is activated, a responsible control<br>operator shall be designated as a distinct operational role. | 24 | PARTIAL | OPS/POLICY; Stage 11 |
| C7-10 | 7 | A Field Network Administrator shall not be treated as an amateur<br>control operator by virtue of that role. | 24 | PARTIAL | OPS/POLICY; Stage 11 |
| C7-11 | 7 | Activation of amateur-radio egress shall occur only under an approved<br>mission configuration and applicable lawful operating conditions. | 24, 19.2 | PRESENT | Stage 11 |
| C8-01 | 8 | Every MULE shall carry the same approved software service catalog for<br>its hardware block. | 9, 19.1 | PRESENT | Stage 1/13 |
| C9-01 | 9 | S0 functions shall remain active whenever the node is operational. | 3-4, 15, 26 | PRESENT | Stage 1 |
| C9-02 | 9 | Loss or shutdown of any S3 service shall not disable baseline field<br>communications. S3 services shall be the first class stopped under constrained<br>battery, thermal, bandwidth, or compute conditions. | 15, 25.1, 26 | PRESENT | Stage 7 |
| C10-01 | 10 | Service activation shall not tie team-level capability to a single EUD<br>remaining connected. | 15 | PRESENT | Stage 1 |
| C10-02 | 10 | Grace periods and damping shall be applied so that brief roaming, EUD<br>sleep states, or momentary disconnects do not repeatedly start and stop<br>services. | 15 | PRESENT | Stage 1 |
| C11-01 | 11 | Service activation shall not create externally observable behavior that<br>directly and unnecessarily reveals privileged-user login, leadership presence,<br>or command structure. | 15, 23 | PRESENT | Stage 10 |
| C12-01 | 12 | EUDs shall not join the Tailscale or equivalent WAN overlay directly. | 17, 18, 27 | PRESENT | Stage 6/9 |
| C12-02 | 12 | The MULE shall be the routing, authentication, and security boundary<br>between EUDs and remote field services. | 17, 18, 27 | PRESENT | Stage 6/9 |
| C13-01 | 13 | The system shall separate:<br>1. network admission;<br>  2. user identity;<br>  3. role and scope;<br>  4. application authorization;<br>  5. TAK authorization;<br>  6. infrastructure administration. | 16.4-16.5, 17, 27 | PRESENT | Stage 9 |
| C13-02 | 13 | Knowledge of a shared WLAN password shall not be sufficient<br>authorization for the production field environment. | 17.1-17.3 | PRESENT | Stage 9 |
| C13-03 | 13 | Each authorized EUD shall use an individually identifiable, revocable,<br>and time-bounded credential appropriate to the mission. | 16.2-16.4, 17 | PRESENT | Stage 9 |
| C13-04 | 13 | MAC addresses shall not be trusted as primary proof of user or device<br>identity. | 17 | PRESENT | Stage 9 |
| C14-01 | 14 | Before deployment, authorized users and devices shall receive<br>mission-scoped identities or credentials with a defined validity window. | 16.1-16.4, 24.5 | PRESENT | TBR-TIME-01; Stage 9 |
| C14-02 | 14 | The organizational root shall not be required to be present on any<br>MULE. | 16.1-16.4, 24.5 | PRESENT | TBR-TIME-01; Stage 9 |
| C15-01 | 15 | This revocation-lag limitation shall be stated in administrator and<br>Team Lead training material. | 16.3 | PARTIAL | TRAINING; Stage 9/10 |
| C15-02 | 15 | The production system shall use bounded credential lifetimes such that<br>a disconnected unrevoked credential eventually fails safe by expiry. | 16.2-16.3, 24.5 | PRESENT | TBR-TIME-01; Stage 9 |
| C16-01 | 16 | An authorized user's operational identity shall not be permanently<br>bound to one physical EUD. | 16.2-16.5, 17 | PRESENT | Stage 9 |
| C16-02 | 16 | The system shall support controlled recovery when an EUD is destroyed,<br>lost, damaged, depleted, or replaced. | 16.2-16.5, 17 | PRESENT | Stage 9 |
| C16-03 | 16 | Mission planning shall identify alternate recovery authorities or<br>pre-positioned recovery capability. | 16.2-16.4 | PARTIAL | OPS/POLICY; Stage 9 |
| C17-01 | 17 | Volunteer membership state shall be linked to credential validity. | 16.2-16.4 | PARTIAL | ORG POLICY; Stage 9 |
| C17-02 | 17 | The following events shall trigger identity review or revocation:<br>* resignation;<br>  * termination;<br>  * prolonged inactivity;<br>  * loss of equipment;<br>  * role change;<br>  * privilege reduction;<br>  * suspected compromise. | 16.2-16.4 | PARTIAL | ORG POLICY; Stage 9 |
| C17-03 | 17 | Authority to issue or delegate identities shall be more constrained<br>than normal network administration authority. | 16.2-16.5, 19.2 | PARTIAL | SEC/ORG; Stage 9 |
| C18-01 | 18 | The system shall record security-relevant administrative events<br>including:<br>* credential issuance;<br>  * revocation;<br>  * role changes;<br>  * scope changes;<br>  * mission-profile changes;<br>  * privileged configuration changes;<br>  * service-host promotions;<br>  * zeroize actions;<br>  * node enrollment;<br>  * node decommissioning. | 16.6, 21 | PRESENT | SEC/TRD; Stage 9 |
| C18-02 | 18 | A compensating control shall be established consisting of periodic<br>independent review of privileged identities and administrative actions by a<br>second authorized person. | 16.6 | PARTIAL | SEC POLICY; Stage 9 |
| C19-01 | 19 | Each deployment shall use an approved mission configuration package<br>containing, as applicable:<br>* node identities;<br>  * network parameters;<br>  * trusted credentials;<br>  * approved users;<br>  * mission-scoped identities;<br>  * roles;<br>  * alternates;<br>  * organizational scope;<br>  * service definitions;<br>  * TAK logical identity;<br>  * radio profiles;<br>  * exercise or live status;<br>  * external interoperability parameters;<br>  * amateur-radio enablement state;<br>  * retention policy;<br>  * EMCON parameters. | 19.2 | PRESENT | ICD/TRD; Stage 1/13 |
| C22-01 | 22 | multicast behavior shall be measured under representative<br>    multi-hop load; | 4.3, 30.2 | PRESENT | TBR-RF-01/RF-03; Stage 2 |
| C22-02 | 22 | Stage 2 qualification shall determine usable network size and<br>    hop-count limits. | 4.3, 30.2 | PRESENT | TBR-RF-01/RF-03; Stage 2 |
| C22-03 | 22 | The system shall not assume that bench-scale peer TAK performance<br>extends automatically to a large field network. | 4.3, 30.2 | PRESENT | TBR-RF-01/RF-03; Stage 2 |
| C23-01 | 23 | Information sent through a common peer operational domain shall be<br>treated as potentially visible to all other authenticated participants on that<br>domain. | 4.3, 17, 27 | PRESENT | Stage 2/9 |
| C23-02 | 23 | Role-restricted information shall use an appropriately authenticated<br>service or another approved protection mechanism rather than relying on peer<br>distribution behavior. | 4.3, 17, 27 | PRESENT | Stage 2/9 |
| C23-03 | 23 | This rule shall appear in user training, Team Lead training, and<br>quick-reference material. | 4.3, 27 | PARTIAL | TRAINING; Stage 2/10 |
| C25-01 | 25 | EUDs shall reference a stable logical TAK service identity rather than<br>a specific physical host. | 11, 13-14 | PRESENT | Stage 5 |
| C25-02 | 25 | Movement of the service between eligible hosts shall not require<br>ordinary users to change ATAK server settings. | 11, 13-14 | PRESENT | Stage 5 |
| C25-03 | 25 | Eligible hosts shall use compatible service trust and certificate<br>identity so that failover does not create avoidable client trust failures. | 11, 13-14 | PRESENT | Stage 5 |
| C26-01 | 26 | This class shall be consistent across all eligible service hosts.<br>Examples include:<br>* service trust identity;<br>  * certificate trust;<br>  * mission configuration;<br>  * role definitions;<br>  * shared service configuration. | 14.1-14.5 | PRESENT | TBR-TAK-01; Stage 5 |
| C26-02 | 26 | State in this class shall survive failover before a replacement TAK<br>service may be considered fully authoritative. | 14.1-14.5 | PRESENT | TBR-TAK-01; Stage 5 |
| C26-03 | 26 | The exact data categories in this class shall be defined in the TRD. | 14.1-14.5 | PRESENT | TBR-TAK-01; Stage 5 |
| C27-01 | 27 | Failure of the active TAK host shall trigger recovery when another<br>eligible host is available and safe authority can be established. | 14.3-14.7 | PRESENT | TBR-TAK-01/HA-01; Stage 5 |
| C27-02 | 27 | Operational expectations are:<br>* no manual EUD server change;<br>  * no routine end-user intervention;<br>  * bounded interruption;<br>  * bounded state loss;<br>  * clear authoritative or degraded indication;<br>  * peer ATAK remains available when local networking survives. | 14.3-14.7 | PRESENT | TBR-TAK-01/HA-01; Stage 5 |
| C28-01 | 28 | A Team Lead shall be able to determine when shared mission data is<br>stale, partial, or non-authoritative. | 14, 22 | PRESENT | TBR-HA-01; Stage 5 |
| C28-02 | 28 | A service shall not present itself as fully authoritative merely<br>because the process restarted successfully. | 14, 22 | PRESENT | TBR-HA-01; Stage 5 |
| C29-01 | 29 | Automatic service recovery shall not create uncontrolled competing<br>authoritative stateful services. | 14.4-14.7 | PRESENT | TBR-HA-01; Stage 5 |
| C29-02 | 29 | The system shall prefer loss of shared-service authority over divergent<br>authoritative databases. | 14.4-14.7 | PRESENT | TBR-HA-01; Stage 5 |
| C30-01 | 30 | When safe automatic recovery cannot occur:<br>* the system shall clearly indicate degraded or non-authoritative status;<br>  * an authorized administrator shall be able to perform an explicit recovery<br>    or promotion procedure;<br>  * ordinary users shall not be required to edit EUD server configuration. | 14.4, 33 | PRESENT | TBR-HA-01; Stage 5/10 |
| C30-02 | 30 | The system shall not force automatic promotion merely to maximize<br>apparent availability. | 14.4, 33 | PRESENT | TBR-HA-01; Stage 5/10 |
| C31-01 | 31 | The user status interface shall clearly indicate when the node is<br>carrying elevated service-host responsibility and when that responsibility is<br>materially reducing projected runtime. | 22, 25.1 | PRESENT | Stage 5/7 |
| C33-01 | 33 | The MULE shall be capable of exploiting a higher-throughput IP path<br>when propagation and mission conditions support it. | 5.1-5.3, 25.4 | PRESENT | TBR-RF-03/RF-01; Stage 4 |
| C33-02 | 33 | The requirement is higher-throughput IP capability outside the primary<br>sub-GHz bearer, and shall not be interpreted as mandating a specific Wi-Fi<br>product. | 5.1-5.3, 25.4 | PRESENT | TBR-RF-03/RF-01; Stage 4 |
| C33-03 | 33 | The high-throughput bearer band shall be selected before RF coexistence<br>analysis is completed, so that its harmonic and intermodulation relationships<br>with the sub-GHz chains can be evaluated as part of Section 36. | 5.1-5.3, 25.4 | PRESENT | TBR-RF-03/RF-01; Stage 4 |
| C35-01 | 35 | The LoRa bearer shall not be relied upon to carry arbitrary normal IP<br>traffic. | 7 | PRESENT | Stage 3 |
| C36-01 | 36 | HaLow and LoRa shall use independent RF chains and independent<br>antennas. | 6-8, 25.4 | PRESENT | TBR-RF-02; Stage 3 |
| C36-02 | 36 | Where necessary, HaLow scanning, probing, or transmission shall be<br>coordinated or suppressed to preserve the degraded communications path. | 6-8, 25.4 | PRESENT | TBR-RF-02; Stage 3 |
| C36-03 | 36 | System Architecture shall state a LoRa availability or duty-cycle<br>figure to be maintained while HaLow reacquisition is active, so that the<br>coexistence design has a verifiable target. | 6-8, 25.4 | PRESENT | TBR-RF-02; Stage 3 |
| C37-01 | 37 | A designated RF and spectrum engineering function shall own regulatory<br>compliance of the assembled MULE configuration, including the interaction of:<br>* radio module;<br>  * antenna;<br>  * cable and pigtail losses;<br>  * channel plan;<br>  * regulatory region;<br>  * EIRP;<br>  * field-replaceable antenna options. | 8, 34 | PARTIAL | RF GOVERNANCE; Stage 3/13 |
| C37-02 | 37 | Field replacement shall use approved antenna configurations only.<br>"Replaceable" does not mean "arbitrary." | 8, 25.4, 34 | PARTIAL | RF COMPLIANCE; Stage 3/8 |
| C38-01 | 38 | External antennas shall be treated as field-replaceable consumable<br>accessories and shall be carried as spares in the field kit. | 25.4, 25.6, 28 | PRESENT | TBR-CARRIER-01; Stage 8 |
| C38-02 | 38 | Incorrect RF connections shall be prevented mechanically or tactilely<br>where practical, rather than by color or label alone. | 25.4, 25.6, 28 | PRESENT | TBR-CARRIER-01; Stage 8 |
| C39-01 | 39 | The network shall automatically adapt to:<br>* movement;<br>  * node loss;<br>  * changing neighbors;<br>  * link degradation;<br>  * gateway availability;<br>  * recovery of better paths. | 4-5, 15 | PRESENT | Stages 2/4 |
| C39-02 | 39 | Normal users shall not be required to select routes manually. | 4-5, 15 | PRESENT | Stages 2/4 |
| C40-01 | 40 | Traffic policy shall preserve mission-critical communications before<br>bandwidth-intensive services. | 4-7, 15 | PRESENT | Stages 2-4 |
| C41-01 | 41 | Loss of WAN shall not remove:<br>* local EUD access;<br>  * local mesh;<br>  * peer ATAK;<br>  * local S0 and S1 services;<br>  * LoRa/Meshtastic degraded communications. | 1, 18, 26 | PRESENT | Stage 6 |
| C42-01 | 42 | Any standard MULE shall be technically capable of assuming an<br>authorized local WAN-gateway role. | 18 | PRESENT | Stage 6 |
| C43-01 | 43 | EUDs shall not join the overlay directly. | 18, 27 | PRESENT | Stage 6/9 |
| C43-02 | 43 | The MULE shall remain the WAN security and routing boundary. | 18, 27 | PRESENT | Stage 6/9 |
| C43-03 | 43 | Infrastructure access control and mission authorization shall remain<br>separate. Overlay authentication alone shall not grant service or data<br>authorization. | 18, 27 | PRESENT | Stage 6/9 |
| C44-01 | 44 | Remote ATAK communication shall use the TAK service or another approved<br>routed application service. | 11, 13, 18 | PRESENT | Stage 6 |
| C46-01 | 46 | Amateur-radio egress shall be a distinct mission capability and shall<br>be disabled by default. | 24 | PARTIAL | RF SOP/POLICY; Stage 11 |
| C46-02 | 46 | Activation shall require:<br>* an approved mission profile;<br>  * an appropriately authorized control operator;<br>  * applicable station identification;<br>  * appropriate rate limits;<br>  * lawful message and content handling;<br>  * a defined gateway mode. | 24 | PARTIAL | RF SOP/POLICY; Stage 11 |
| C46-03 | 46 | Automated position or status egress shall not mirror TAK update rates<br>onto shared amateur networks, and the system shall prevent high-rate automated<br>traffic from overloading local packet or APRS infrastructure. | 24 | PARTIAL | RF SOP/POLICY; Stage 11 |
| C46-04 | 46 | Third-party traffic, automatic control, message forwarding, encryption<br>restrictions, and station-identification requirements shall be addressed in the<br>applicable RF operating procedures. | 24 | PARTIAL | RF SOP/POLICY; Stage 11 |
| C46-05 | 46 | Field Network Administrator authority shall not itself authorize<br>amateur transmission. | 24 | PARTIAL | RF SOP/POLICY; Stage 11 |
| C47-01 | 47 | The MULE field network shall not function only as an internal closed<br>ecosystem during disaster response. | 24, 28 | PARTIAL | ICD/INTEROP; Stage 11 |
| C47-02 | 47 | The system shall support operational handoff of mission-relevant<br>information to organizations that do not use TAK. | 24, 28 | PARTIAL | ICD/INTEROP; Stage 11 |
| C48-01 | 48 | When operating under an external incident command structure, the team<br>shall provide the responsible communications or operations authority with, as<br>applicable:<br>* organizational point of contact;<br>  * team callsign;<br>  * voice tasking path;<br>  * declared data-network operation;<br>  * WAN gateway presence;<br>  * amateur control operator and callsign if amateur systems are used;<br>  * relevant RF and data-network operating information;<br>  * the means by which position, resource, and status information will be<br>    handed off. | 24, 28 | PARTIAL | INCIDENT SOP/ICD; Stage 11 |
| C48-02 | 48 | No public-safety or interoperability frequency shall be presumed<br>authorized solely because it appears in a reference document. | 24, 28 | PARTIAL | INCIDENT SOP/ICD; Stage 11 |
| C50-01 | 50 | The system shall define an EMCON entry procedure, a visible or<br>      tactile EMCON state indication, an authorized override, and a re-entry<br>      procedure. | 23, 19.2 | PRESENT | Stage 10 |
| C50-02 | 50 | Exercise data shall be distinguishable from live incident data<br>      and shall be prevented from crossing into real operations where<br>      technically feasible. | 23, 19.2 | PRESENT | Stage 10 |
| C51-01 | 51 | Exercise control shall not create an undocumented production backdoor,<br>and exercise-control authority shall exist only under an approved exercise<br>profile. | 23, 19.2 | PRESENT | Stage 10 |
| C52-01 | 52 | Diagnostic access shall not automatically grant configuration<br>authority. | 21-22, 27 | PRESENT | Stage 10 |
| C53-01 | 53 | The organization shall maintain at least three competency levels with<br>defined qualification standards and recurrence intervals. | 33 | N/A-SAD | TRAINING; Stage 10/13 |
| C53-02 | 53 | Training shall include practical comms-out drills per Section 4. | 33 | N/A-SAD | TRAINING; Stage 10/13 |
| C53-03 | 53 | Fielding shall include quick-reference material, an indicator legend, a<br>new-member brief, and applicable recurrence standards. | 33 | N/A-SAD | TRAINING; Stage 10/13 |
| C54-01 | 54 | The system shall produce exportable mission and exercise records<br>appropriate to the operation. | 19, 21-22 | PARTIAL | AAR/TRD; Stage 10 |
| C54-02 | 54 | Retention shall be governed by Sections 55 through 58. | 19, 21-22 | PARTIAL | AAR/TRD; Stage 10 |
| C55-01 | 55 | The system shall apply data minimization. Information shall be<br>collected and retained only when required for:<br>* current operations;<br>  * accountability;<br>  * safety;<br>  * defined AAR needs;<br>  * legal or incident-authority requirements. | 16, 19, 27.5 | PARTIAL | PRIVACY/POLICY; Stage 10/13 |
| C56-01 | 56 | The default retention model shall be:<br>Mission duration plus an approved AAR and review window, followed by purge<br>    unless longer retention is explicitly required. | 16, 19, 27.5 | PARTIAL | PRIVACY/POLICY; Stage 10/13 |
| C56-02 | 56 | Retention shall not default to indefinite storage. | 16, 19, 27.5 | PARTIAL | PRIVACY/POLICY; Stage 10/13 |
| C57-01 | 57 | Members shall be informed during onboarding that operational<br>participation may include:<br>* continuous location tracking;<br>  * mission activity logging;<br>  * identity records;<br>  * communications metadata;<br>  * AAR retention. | 16, 19, 27.5 | PARTIAL | PRIVACY/POLICY; Stage 10/13 |
| C57-02 | 57 | Consent or acknowledgment shall be handled through the organization's<br>membership or mission policy and shall not be assumed implicitly. | 16, 19, 27.5 | PARTIAL | PRIVACY/POLICY; Stage 10/13 |
| C58-01 | 58 | Victim, evacuee, or other third-party information shall be:<br>* minimized;<br>  * handled under the supported authority's rules;<br>  * segregated where appropriate;<br>  * retained only as required;<br>  * excluded from casual local archives. | 16, 19, 27.5 | PARTIAL | PRIVACY/POLICY; Stage 10/13 |
| C58-02 | 58 | If minors participate or appear in collected information, the<br>organization shall establish additional privacy and retention rules before<br>operational use. | 16, 19, 27.5 | PARTIAL | PRIVACY/POLICY; Stage 10/13 |
| C59-01 | 59 | The battery shall be an engineered protected assembly with appropriate<br>protection and charging controls. Loose cells in an unqualified holder shall not<br>be an approved operating configuration. | 25.5 | PRESENT | TBR-PWR-01; Stage 7/8 |
| C60-01 | 60 | Mission planning products shall address:<br>* number of battery packs;<br>  * pack mass;<br>  * charging;<br>  * charging time;<br>  * external power;<br>  * vehicle power;<br>  * solar or generator support;<br>  * cold-weather derating;<br>  * service-host power penalty;<br>  * reserve margin. | 25.1, 25.5 | PARTIAL | OPS/LOGISTICS; Stage 7 |
| C61-01 | 61 | The final verified endurance requirement shall include defined<br>cold-temperature conditions representative of expected use. | 25.1, 25.5 | PRESENT | TBR-PWR-01; Stage 7 |
| C61-02 | 61 | The nominal 8-hour objective shall not be treated as guaranteed winter<br>endurance in any planning product. | 25.1, 25.5 | PRESENT | TBR-PWR-01; Stage 7 |
| C62-01 | 62 | The MULE shall support operation from an approved external power<br>source while maintaining or replenishing its battery where practical. | 25.5 | PRESENT | TBR-PWR-01; Stage 7 |
| C63-01 | 63 | The organization shall use:<br>* verified battery-cell sources;<br>  * approved protected packs;<br>  * appropriate BMS and protection;<br>  * approved chargers;<br>  * inspection procedures;<br>  * damaged-pack quarantine;<br>  * storage procedures;<br>  * transport procedures;<br>  * disposal procedures. | 25.5 | PARTIAL | BATTERY SOP; Stage 7/8 |
| C63-02 | 63 | Battery packs shall be managed as consumable configuration items under<br>Section 7.7. | 25.5 | PARTIAL | BATTERY SOP; Stage 7/8 |
| C65-01 | 65 | Status illumination shall be suppressible to off. | 23, 25.6 | PRESENT | Stage 8/10 |
| C65-02 | 65 | The production design shall avoid uncontrolled always-on indicator<br>lights, including indicators integral to selected commercial modules. This is a<br>BOM and component-selection constraint as well as a software behavior. | 23, 25.6 | PRESENT | Stage 8/10 |
| C65-03 | 65 | Cold-weather qualification shall include cables, connectors, controls,<br>antenna replacement, battery replacement, and glove use. | 23, 25.6 | PRESENT | Stage 8/10 |
| C66-01 | 66 | Normal users shall not be required to use:<br>* SSH;<br>  * route commands;<br>  * container commands;<br>  * manual overlay configuration;<br>  * manual bearer selection;<br>  * manual TAK server discovery. | 1, 22 | PRESENT | Stage 8/10 |
| C67-01 | 67 | The simplified status view shall answer:<br>* Is the node operational?<br>  * Is the battery healthy?<br>  * What is the projected runtime?<br>  * Is this node hosting shared services?<br>  * Is hosting reducing runtime?<br>  * Is TAK available?<br>  * Is shared data authoritative?<br>  * Is data stale?<br>  * Is the network degraded?<br>  * Is LoRa available?<br>  * Is WAN available?<br>  * Is EMCON active?<br>  * Is a fault present? | 22 | PRESENT | Stage 1/5 |
| C68-01 | 68 | WAN reachability shall not grant access to unrelated home, private,<br>administrative, or cyber-range infrastructure. | 18, 27 | PRESENT | Stage 9 |
| C69-01 | 69 | Loss or capture of one MULE shall not automatically compromise the<br>entire organization. | 16, 24.5, 27, 27.5 | PRESENT | TBR-SEC-01/TIME-01; Stage 9 |
| C69-02 | 69 | Production controls shall include:<br>* encrypted data at rest;<br>  * protected credential storage;<br>  * protected administrative credentials;<br>  * integrity verification where practical;<br>  * zeroize;<br>  * out-of-band revocation;<br>  * replacement identity issuance;<br>  * limited local historical retention. | 16, 24.5, 27, 27.5 | PRESENT | TBR-SEC-01/TIME-01; Stage 9 |
| C69-03 | 69 | A missing node shall be revocable without cooperation from that node,<br>and remaining participants shall reject the revoked identity once updated<br>authorization information becomes available. | 16, 24.5, 27, 27.5 | PRESENT | TBR-SEC-01/TIME-01; Stage 9 |
| C70-01 | 70 | An approved administrative procedure shall allow removal or<br>invalidation of sensitive field information without WAN dependency. | 27.5 | PRESENT | TBR-SEC-01; Stage 9 |
| C71-01 | 71 | Operator procedures and mobile-device hardening guidance shall address:<br>* Wi-Fi probing;<br>  * unnecessary Bluetooth;<br>  * unused radios;<br>  * unnecessary background network traffic;<br>  * device lock;<br>  * unattended device access. | 23, 27 | PARTIAL | EUD HARDENING SOP; Stage 9/10 |
| C73-01 | 73 | Returned failed nodes shall enter a controlled maintenance path for<br>triage, re-imaging, re-keying, test, and return to spares. | 19.1, 20.3, 27.5 | PARTIAL | MAINTENANCE SOP; Stage 13 |
| C74-01 | 74 | Every production MULE shall pass an approved acceptance process<br>before fielding. | 19, 20, 30.2 | PARTIAL | ATP/TEST; Stage 13 |
| C74-02 | 74 | Operational interchangeability shall be verified, not assumed. | 19, 20, 30.2 | PARTIAL | ATP/TEST; Stage 13 |
| C75-01 | 75 | A five-year total-cost-of-ownership assessment shall be completed<br>before fleet procurement. | 19.5, 33 | N/A-SAD | ACQUISITION PLAN; Stage 13 |
| C76-01 | 76 | The system shall not depend on one builder or originator. | 19.3-19.5, 20 | PRESENT | Stage 13 |
| C76-02 | 76 | Before fielding, the program shall maintain:<br>* reproducible build documentation;<br>  * software and configuration repository;<br>  * acceptance procedures;<br>  * at least one additional qualified builder or maintainer;<br>  * known-good imaging and provisioning capability. | 19.3-19.5, 20 | PARTIAL | CM/OPS; Stage 13 |
| C77-01 | 77 | The loss of any shared optional component shall not make an otherwise<br>functional team node unusable. | 1, 26 | PRESENT | Stage 12/13 |

## 35.3 Document-Governance SHALLs

The following SHALLs govern the CONOPS document/review process and are intentionally **N/A-SAD**. They belong in configuration management, review, or verification governance rather than subsystem architecture.

| CONOPS § | Clause | SAD disposition |
|---:|---|---|
| 83 | The review-status column below shall be completed and signed before<br>this document is treated as externally defensible. | N/A-SAD; document governance |
| 83 | Practitioner confirmation shall be obtained for RF compliance<br>(Section 37), amateur-radio governance (Section 46), battery safety<br>(Section 63), and privacy and retention governance (Sections 55 through 58)<br>before operational fielding. | N/A-SAD; document governance |
| 85 | Every criterion shall have at least one validating stage. Any criterion<br>whose validating stage is later removed shall trigger a change request under<br>Section 86. | N/A-SAD; document governance |
| 86 | After signature, changes to this document shall be made by change<br>request recording:<br>1. the section affected;<br>  2. the current text;<br>  3. the proposed text;<br>  4. the operational rationale;<br>  5. downstream documents affected;<br>  6. verification impact against Section 85;<br>  7. approval. | N/A-SAD; document governance |

## 35.4 Formal RTM Exit Criterion

Before the MULE TRD/Verification Matrix is baselined:

1. every `PARTIAL` row must identify the downstream requirement/interface/policy artifact that completes it;
2. every `PRESENT` row must be checked against the actual SAD text by a second reviewer;
3. every verification-bearing row must map to a test method and evidence location;
4. every new TRD requirement derived from an architecture choice must identify its parent CONOPS clause and FML-ADR/TBR source;
5. no document-control requirement may be counted as a system requirement merely to make the matrix appear complete.
6. the second reviewer must confirm quoted CONOPS text against the controlled v1.01 source and record reviewer/date;
7. established SAD section numbers remain frozen once referenced by the baselined RTM; future content uses subsections/appendices rather than renumbering.

---

**END OF DOCUMENT - FML/MULE SAD v0.31 DRAFT**
