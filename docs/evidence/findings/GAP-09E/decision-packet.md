# GAP-09E decision packet: AP-only network rendering

**State:** `APPROVED`; implementation remains open. On 2026-09-25 the Program
Owner selected a temporary, broadcast-while-active onboarding BSS that remains
isolated until admission and becomes hidden when its mission-supplied key or
time window expires. `FML-ADR-084` records the controlling boundary. The
operational EUD BSS remains non-isolated under `FML-ADR-057`.

**Finding:** GAP-09E. **Prepared:** 2026-09-21. **Author:** Claude agent
(redirected from Codex). **Independent verifier:** a separate agent at execution
time.

## 1. Decision requested

The AP-only v0.0.1 network config to render from the target-aware inputs -- the
hostapd AP, dnsmasq DHCP/DNS, and the systemd-networkd host-network -- and, more
importantly, the **unspecified semantics** those templates leave `TBD`.

## 2. What is already decided (the foundation)

- **GAP-03 (CLOSED):** `address_prefix` is preserved and validated through the
  canonical mission model into resolved output (`FML-ADR-063`).
- **GAP-04 (CLOSED):** configuration resolution is target-aware, so the AP-only
  v0.0.1 target resolves without the inactive HaLow/LoRa/mesh `TBD` values.
- The templates exist (`os/config/hostapd.conf.template`,
  `dnsmasq.conf.template`, `networkd.conf.template`) and already encode one hard
  rule: **dnsmasq serves DHCP/DNS on the EUD AP interface only, never onto the
  mesh.**

## 3. What must be resolved before rendering

Every value in the AP templates is `TBD`. One is a **rendering task** derived from
an already-closed record; the rest are genuinely unspecified semantics or bound to
an open trade, and the Owner must resolve those before a render:

| Item | Template | Status |
| --- | --- | --- |
| DHCP range, lease, options | dnsmasq | **GATED on the OPEN `TBR-NET-01`** (field address prefix / address family). Corrected 2026-09-25: `docs/evidence/TBR-NET-01/README.md` records the trade as `OPEN` with the decision not made, so the DHCP range is not a render task. `address_prefix` is also the *mesh* prefix (`FML-ADR-063`), and `mule-v001` fields no mesh -- there is no defined AP subnet to derive from |
| Local DNS: the one 09F service name | dnsmasq | `TBR-TAK-01` is **CLOSED** (`FML-ADR-071`, 2026-09-06); the name follows the 09F choice -- a render task |
| Operational AP client isolation | hostapd | **decided:** off, `FML-ADR-057` |
| Onboarding client isolation | hostapd | **decided:** on, separate BSS/domain, `FML-ADR-084` |
| Onboarding SSID broadcast | hostapd | **decided:** broadcast while active, hidden after expiry or time failure |
| **AP passphrase / credential origin** | hostapd | protected material remains outside the package; the package carries a reference and expiry |
| AP-down / interface-failure behavior | networkd/hostapd | **decided:** fail closed; no open fallback |
| Interface naming | networkd | open: `TBR-LINUX-01` |

## 4. Recommendation (the Owner decides each)

Approved v0.0.1 semantics:

- **DHCP:** a small static range inside the AP subnet, short lease so a device
  moving between nodes recovers. **Gated, not a render detail (corrected
  2026-09-25):** `TBR-NET-01` is OPEN, so the addressing this derives from is
  undecided; the AP subnet itself is undefined for an AP-only node whose only
  addressed prefix is the (absent) mesh (`FML-ADR-063`). This waits on the trade.
- **DNS:** resolve only the single 09F milestone service name (or IP-only if the
  Owner prefers); `TBR-TAK-01` is closed, so this follows the 09F choice; no
  upstream forwarding under EMCON.
- **Client isolation:** on only for the separate onboarding BSS. The operational
  BSS remains non-isolated so admitted EUDs retain peer ATAK.
- **SSID:** broadcast while the mission-supplied onboarding window is active;
  hidden when it expires or time cannot be trusted.
- **AP credential:** generated and stored outside the committed package. The
  mission package carries only its protected-material reference and absolute
  UTC expiry. QR/profile output may carry the join material to the EUD.
- **AP-down:** fail closed (no silent fallback to an open AP).
- **Interface name:** deferred to `TBR-LINUX-01`.

## 5. Consequences and gates this must NOT close

- **Corrected 2026-09-25.** An earlier version of this packet called both
  `TBR-NET-01` and `TBR-TAK-01` CLOSED. Only `TBR-TAK-01` is CLOSED (`FML-ADR-071`);
  `TBR-NET-01` is **OPEN** (`docs/evidence/TBR-NET-01/README.md`). So the DNS name
  is a render task, but the **DHCP range / addressing is gated** on `TBR-NET-01`,
  not a render task. Naming the interface still touches `TBR-LINUX-01` (OPEN). This
  packet writes none of the values.
- **What rendering is gated on (not invented here):** DHCP/addressing/family
  (`TBR-NET-01`); AP and onboarding credentials + the auth mechanism (`TBR-SEC-01`,
  with `FML-ADR-038` EAP-TLS as target); multi-BSS shape and interface names
  (`TBR-LINUX-01`). What is decided and renderable now: client isolation
  (`FML-ADR-057`/`FML-ADR-084`), onboarding broadcast/hidden posture, the SSID from
  the mission package, and -- with the Owner sourcing `country_code: US` into the
  region profile -- the hostapd radio block (band/channel/DFS from the `us-915`
  profile).
- The AP credential must never appear in the repository or resolved parameter
  document (SECURITY.md). `TBR-ID-01` still owns who may enroll and how an
  enrollment becomes a production credential.

## 6. Reversibility and smallest safe prototype

Rendering is fully reversible (generated config, no persistent state). Smallest
safe prototype after approval: render the AP config for the dev article and bring
an AP up in a namespace / on the live AP bench, associating one client -- no
mesh, no field radios.

## 7. Files and acceptance criteria that change AFTER approval (not now)

The remaining outputs are resolved hostapd, DHCP/DNS, firewall and host-network
configuration plus evidence under `docs/evidence/findings/GAP-09E/`.
Acceptance: an onboarding client gets an address and approved name resolution,
can reach enrollment only, cannot reach peers or the operational domain, and is
removed at expiry; an admitted client retains operational peer traffic.

## 8. Sources reviewed

`os/config/hostapd.conf.template`, `dnsmasq.conf.template`,
`networkd.conf.template`; `docs/evidence/findings/GAP-03/`,
`docs/evidence/findings/GAP-04/`; `FML-ADR-063`; `docs/evidence/TBR-SEC-01/2026-08-31-two-credentials-have-no-origin.md`;
REMEDIATION Phase 3, line 651.

## 9. Owner disposition

`APPROVED` -- Program Owner approval recorded 2026-09-25. `FML-ADR-084` selects
the separate quarantined onboarding network, active-window broadcast behavior,
credential-reference boundary and fail-closed expiry. GAP-09E remains open until
the rendered configuration and EUD exercise evidence land.
