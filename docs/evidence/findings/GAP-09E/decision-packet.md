# GAP-09E decision packet: AP-only network rendering

**State:** `AWAITING_USER_DECISION`. This packet **surfaces the unspecified AP
semantics and decides none**. Rendering hostapd/DHCP/DNS/host-network requires
the Owner to approve the addressing, isolation, and failure semantics
(REMEDIATION gate -- "AP network design" and "unspecified addressing, isolation,
or failure semantics"; register 09E user gate). **No config is rendered by this
packet.**

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

Every value in the AP templates is `TBD`. Two are **rendering tasks** derived from
already-closed records; the rest are genuinely unspecified semantics or bound to an
open trade, and the Owner must resolve those before a render:

| Item | Template | Status |
| --- | --- | --- |
| DHCP range, lease, options | dnsmasq | **derives from the CLOSED `TBR-NET-01`** (field address prefix) -- a render task, not a gate |
| Local DNS: the one 09F service name | dnsmasq | `TBR-TAK-01` is **CLOSED**; the name follows the 09F choice -- a render task |
| AP client isolation (client-to-client) | hostapd | **unspecified** security semantic |
| SSID broadcast vs hidden (`ignore_broadcast_ssid`) | hostapd | **unspecified** (Owner has leaned "do not broadcast") |
| **AP passphrase / credential origin** | hostapd | the "two credentials have no origin" gap (identity plane) -- **not** in the mission package schema |
| AP-down / interface-failure behavior | networkd/hostapd | **unspecified** failure semantic |
| Interface naming | networkd | open: `TBR-LINUX-01` |

## 4. Recommendation (the Owner decides each)

Minimal, security-first v0.0.1 defaults, offered as recommendations only:

- **DHCP:** a small static range inside the AP subnet derived from the closed
  `TBR-NET-01` addressing, short lease so a device moving between nodes recovers --
  a render detail to confirm, not a blocked gate.
- **DNS:** resolve only the single 09F milestone service name (or IP-only if the
  Owner prefers); `TBR-TAK-01` is closed, so this follows the 09F choice; no
  upstream forwarding under EMCON.
- **Client isolation:** **on** (EUDs reach services, not each other) unless the
  mission needs peer-to-peer.
- **SSID:** hidden (`ignore_broadcast_ssid`) per the Owner's stated lean.
- **AP credential:** **flagged, not resolved** -- its origin is the open identity
  question; the v0.0.1 AP needs a provisioned passphrase whose source the Owner
  must name (this packet will not invent one or place one in any file).
- **AP-down:** fail closed (no silent fallback to an open AP).
- **Interface name:** deferred to `TBR-LINUX-01`.

## 5. Consequences and gates this must NOT close

- `TBR-NET-01` and `TBR-TAK-01` are **CLOSED**, so the DHCP range and the DNS name
  are render tasks derived from decided records, not gate-closing acts. Naming the
  interface still touches `TBR-LINUX-01` (OPEN). This packet writes none of the
  values.
- The AP credential must never appear in the repository (SECURITY.md); its origin
  is an identity-plane decision, not this render.

## 6. Reversibility and smallest safe prototype

Rendering is fully reversible (generated config, no persistent state). Smallest
safe prototype after approval: render the AP config for the dev article and bring
an AP up in a namespace / on the live AP bench, associating one client -- no
mesh, no field radios.

## 7. Files and acceptance criteria that change AFTER approval (not now)

After approval: the resolved AP config outputs generated from the templates; any
new addressing/isolation values recorded against their trades; evidence under
`docs/evidence/findings/GAP-09E/`. Acceptance: a client associates to the AP and
gets an address + the approved name resolution, with isolation and SSID behavior
as approved.

## 8. Sources reviewed

`os/config/hostapd.conf.template`, `dnsmasq.conf.template`,
`networkd.conf.template`; `docs/evidence/findings/GAP-03/`,
`docs/evidence/findings/GAP-04/`; `FML-ADR-063`; `docs/evidence/TBR-SEC-01/2026-08-31-two-credentials-have-no-origin.md`;
REMEDIATION Phase 3, line 651.

## 9. Owner disposition

`AWAITING_USER_DECISION` -- approve the isolation / SSID-broadcast /
credential-origin / AP-down semantics. The DHCP range and DNS name derive from the
closed `TBR-NET-01`/`TBR-TAK-01`; interface naming touches the open `TBR-LINUX-01`;
the AP credential origin is the identity plane. No config is rendered until then.
