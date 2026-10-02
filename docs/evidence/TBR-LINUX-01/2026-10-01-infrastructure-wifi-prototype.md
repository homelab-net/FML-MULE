# Physical infrastructure-WiFi prototype observations

## Question and scope

Can two Raspberry Pi 4 prototype nodes and the existing x86 bench exchange IP
traffic and synthetic TAK events through their onboard WiFi radios?

This reduces Linux/radio integration uncertainty for `TBR-LINUX-01` and
`TBR-RF-01`. The test uses real hosts and radios, with synthetic application
events. It is a limited physical observation, not field qualification or trade
closure. It does not complete M2: `FML-ADR-053` selects 802.11s association and
BATMAN_IV, while this trial uses an infrastructure access point.

The Program Owner instructed the desktop agent to continue this temporary
deviation after the driver limitation was reported. No production selection,
trade frontmatter or compatibility-set pin changed.

## Provenance

- Date: 2026-10-01. Command timestamps and desktop log modification timestamps
  are preserved separately; clocks were not calibrated for timing analysis.
- Operator: desktop SSH orchestration under Program Owner instruction.
- Node identifiers: `test-node-a` and `test-node-b` (Pi 4, identified by the
  owner), and `test-bench` (x86 development host). These are public pseudonyms.
- MULE source: `f898983ca0d4a80f20a8083db595b947a1a53608` on all three hosts.
- Host kernels, reported OS versions, observed OCI image IDs and tool versions
  are in the [provenance record](2026-10-01-infrastructure-wifi-prototype.json).
  Whole-host image build checksums were not captured. A provision-time
  deployment manifest in the raw outputs describes the initial LAN setup;
  the configuration below records the later WiFi trial.
- Instrument: Linux `ping`, `ip`, `iw`, `batctl`, PyTAK and bench PostgreSQL
  queries. Command outputs are in the
  [sanitized raw record](2026-10-01-infrastructure-wifi-prototype.txt).
- Antenna configuration, separation, orientation, ambient conditions, transmit
  power and regulatory profile were not recorded. No range, endurance,
  throughput, coexistence or timing-under-load claim follows from this sample.

## Configuration and deviations

Both Pi drivers rejected creation of a mesh-point interface with
`EOPNOTSUPP (-95)`. They used `brcmfmac`; the bench AP used `rtw89_8852be`.
The independently investigating `qualify_lora_boot` agent confirmed the Pi
driver limitation and the infrastructure alternative. This is a scoped
limitation of these tested host/driver combinations, not every Pi image.

The bench's existing WPA2/CCMP AP carried two Pi stations. Each onboard radio
was the sole hard interface of `fmlbat0`. Routing was explicitly BATMAN_IV
(`FML-ADR-053`); bridge loop avoidance was explicitly disabled
(`FML-ADR-056`). A random private prefix was selected after checking route
overlap on all three hosts (`FML-ADR-063`). Actual addresses are redacted.

This is an AP-dependent star. NetworkManager ownership was retained for the
trial, deviating from `FML-ADR-059`; it does not qualify keyed 802.11s under
`FML-ADR-061`. Pi management stayed on Ethernet; bench management used a
separate USB WiFi adapter. The trial was runtime-only, with Pi profiles under
`/run/NetworkManager/system-connections/` and autoconnect disabled.

Pi hard interfaces reported a maximum MTU of 1500 bytes. Both hard interfaces
and overlay used 1500, with BATMAN fragmentation enabled. Successful IPv4 DF
probes therefore do not prove absence of BATMAN-layer fragmentation. The
1560-byte hard-interface setting in the selected mesh bench was not exercised.

## Observations

1. The single bench/node-a pair passed before node-b joined. All six directed
   pairs then passed three-packet ICMP samples, with routes explicitly using
   `fmlbat0`. Repeated connectivity checks also passed.
2. All six directions received two of two IPv4 DF probes with 1472-byte ICMP
   payloads: 1500-byte IPv4 packets, derived from the observed overlay MTU.
3. Detaching node-a's WiFi hard interface stopped overlay ping: zero of two
   packets received. Its Ethernet/router and ordinary WiFi/AP checks each
   received one of one. Reattachment restored the trial. This checks the
   tested traffic's dependency on BATMAN rather than Ethernet fallback.
4. Both Pis sent synthetic PyTAK CoT to the bench's existing TCP listener over
   routes using `fmlbat0`. SQL recorded one row for each distinct test UID.
   UIDs and fake callsigns were replaced consistently in the public logs.
   Receipt of those specific events on an EUD was not confirmed.
5. All eight selected service units were active on each Pi; the three operator
   HTTP endpoints returned 200. Bench containers were running. This observes
   service availability, not every production mission/admission path.
6. Node-a's USB RAK failed enumeration with EPROTO (-71) and EPIPE (-32),
   including after host reboot. A separate power sample returned
   `throttled=0x50005`; power causality for the USB fault was not established.
7. The BLE target was inferred to be the RAK from the remaining advertisement
   after the owner identified the other device as the T1000. It was not matched
   to a RAK label or serial API identity. With the phone reported disconnected
   from the RAK, fresh BLE discovery corrected a
   helper lookup defect. BlueZ `Pair` then returned `ConnectionAttemptFailed`
   before any passkey callback. A clean target cancel/disconnect retry failed
   the same way, with `Connected=False` and `ServicesResolved=False` afterward.
   Node-b did not find that advertisement in its bounded scan.
   PIN rejection, permanent BLE unavailability and RF exchange are unproved.
   The independent agent qualified the failure as connection establishment,
   not authentication rejection. Original Bluetooth power/rfkill states were
   restored after attempts.

## Repeat and grade the next run

1. Record node/image identities, radio drivers, antennas, separation, ambient
   conditions, region and power settings before beginning. Use local mission
   credentials; do not publish them or a real mission package.
2. Preserve an independent management path. Check existing routes and interface
   ownership before configuring a temporary AP/station trial. Record every
   deviation from `FML-ADR-053`, `FML-ADR-056`, `FML-ADR-059` and `FML-ADR-061`.
3. Test ordinary radio connectivity first, then a single BATMAN pair, then all
   directed pairs. Confirm each route and the actual hard-interface membership.
4. Derive DF payload size from the observed MTU. Record BATMAN fragmentation
   state; do not equate IPv4 DF with an unfragmented radio transport.
5. Interrupt the test path while preserving management, confirm the expected
   failure, restore it, and repeat connectivity before application testing.
6. Send unique synthetic CoT events through the upstream listener. Check zero
   matching rows before sending, then matching SQL rows and specific EUD UIDs
   afterward. SQL arrival alone is not EUD delivery.
7. Save raw outputs and provenance, scrub identifiers, hash the public files,
   restore temporary state, and have the named owner grade the remaining gate.

The [later routed-marker trial][routed-marker] confirms usable iTAK rendering
through a forced transit node. That later artifact also records controlled
streaming-worker movement and its remaining EUD confirmation gate. The EUD
delivery limit above describes this earlier observation, not the later run.

The present observations leave selected 802.11s formation, RF multi-hop,
reboot-persistent trial recovery, automatic reconvergence, EUD delivery,
authenticated ingress, sustained load and multi-bearer coexistence unqualified.
The next demonstration is the selected association layer on supported hardware,
or a separately accepted trade changing that selection.

[routed-marker]: ../TBR-HA-01/2026-10-01-routed-marker-streaming-host.md

## Publication treatment

The raw record includes selected outputs, not a complete session capture.
Hostnames, account names, network/MAC/link-local addresses, MAC-derived
interface names and synthetic event identifiers were replaced. Colour escapes
and line endings/trailing whitespace were normalized. Credentials, full AP
configuration, real member inventories and operational captures were excluded.
Nonsecret AP security/channel settings were retained using an exact key
allowlist; the SSID and password were excluded. The JSON records hashes
of the private originals and of the public sections so omissions and changes
are explicit. Originals remain local and are not part of this packet.
