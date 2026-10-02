# Three-node lab delivery and intervention boundaries

**Real-hardware lab observations; formal tier held as in the
[September radio record](2026-09-27-one-lora-hop-to-a-partner-node.md).**
This packet does not promote the program's evidence tier or close a trade.
It records what the October 1–2 experiments support under FML-ADR-048/070,
TBR-NET-02, TBR-RF-03 and TBR-HA-01. It is not a qualification-stage result.

## Configuration and provenance

The [sanitized observation record][data] holds measured values, local image
identifiers, source fingerprints and instrument provenance. Node A is Pi 1 with
a RAK4631 accessed over BLE; node B is Pi 2 with a T1000-E over USB serial;
node C is the existing bench. Both hosts are Pi 4B running Debian 13, with
firmware versions and kernels recorded in [data]. Antennas were confirmed
attached by the operator. Radio-reported RSSI/SNR are uncalibrated. Antenna
model, orientation, separation, ambient conditions and EIRP were not measured.
These omissions prevent range, coexistence or RF performance qualification.

The desktop orchestrator collected the logs; the Program Owner operated the
real phone EUD. The observations span October 1–2 in US Mountain time; precise
per-packet wall-clock timestamps were not collected. The Pi 1 boot record uses
systemd's monotonic timestamp since boot, not chat latency.

All three MULE source trees and installed package modules matched GitHub main
`326239026b609693bb10f16291cc8e904094cd64`; 21 module files were compared per node.
That is a package/source assertion, **not a whole-deployment assertion**.
TAK used release 1.7.13 with a local connection-state candidate from PR #208,
plus private recovery settings and test instrumentation. Local immutable image
IDs identify the tested bytes but are not published registry pull references.
No selected release-image build or promotion was exercised.

## Results and intervention

| Observation | Result supported | Intervention and limit |
| --- | --- | --- |
| Single radio hop before chat | Stock text and reply crossed actual LoRa between node B serial and node A BLE, with MQTT absent on received packets | Desktop opened both APIs; a physical RAK reset and retained bonded-device handling preceded success. No unattended radio reconnect claim. |
| A to B LoRa, B to bench Wi-Fi, bench to iTAK, and return | Addressed native ATAK payload crossed RF; phone reply returned to the continuously connected synthetic EUD on A. Both RF payload comparisons and native UID correlation passed. | Desktop started and coordinated the bridge and handed the actual phone reply back to the radio API. A temporary Wi-Fi host route and controlled codec/roster fixtures were used. |
| B to A LoRa, A to bench Wi-Fi, bench to iTAK | Operator confirmed the outward chat | Return clients expired while harness corrections consumed the fixed test windows. No completed return is asserted. |
| Native TAK worker/broker crash recovery | Automatic recovery followed intentional faults on all three hosts; intended-only native IP chat controls passed afterward | Private policy was installed before injection. See the [recovery record][recovery]. Real-phone chat was not run during these faults. |
| Pi 1 boot | Supervised TAK target became active automatically; native recipient controls passed afterward | Desktop requested one reboot; no service start was needed during recovery. Pi 2/bench reboot recovery and radio gateway startup were not exercised. |
| Pi 1 onboard AP, Pi 2 station | Native fake-EUD chat reached bench through the Pi AP | Reversible NetworkManager infrastructure trial, not selected 802.11s/batman-adv. No LoRa or real-phone delivery in this AP trial. |
| Bench SDR | Finite tuner/ADC sample acquisition completed | Disposable receive test to /dev/null; no decoded signal, calibrated RF result or mission throughput claim. |

The successful mixed-carrier RF message carried the intended real EUD UID in
upstream `GeoChat.to` before transmission, plus native sender contact fields.
The bridge decoded the actual received bytes, then used native TAK `marti`
destination routing for that same UID. It added no private recipient protocol.
The actual phone reply's source and recipient UID and unique reply token were
checked before encoding it for the return RF transmission. Message contents,
real UIDs and addresses are omitted from this publication.

Native TCP synthetic clients deliberately waited for asynchronous broker setup
before announcing their first identity. Immediate first-identity behavior during
cold startup was not validated by these delayed-client controls.

**One LoRa hop plus carrier transitions is not multiple RF relay hops.**
The IP leg used Wi-Fi infrastructure through a router, not a MULE IP mesh.
No MQTT relay appeared on the observed RF packets; desktop coordination still
made this an assisted integration test.

## Failures and bounds

- Pi 1's USB descriptor fault remained. Its BLE/LoRa success does not repair USB.
  A normal physical reset and retained BlueZ device-object connection restored
  the API; fresh name-only discovery had been an incorrect assumption.
- Pi 1 reported current undervoltage/throttling. It is a confound, not an
  isolated cause of the USB fault. No power envelope or supply diagnosis follows.
- An isolated container did not contain wlan0. A temporary host-network test
  container used the installed image instead; no production container moved.
- The initial Pi 2 Wi-Fi TCP attempt timed out. An explicit direct host route
  preceded the successful retry. This was not a controlled causal isolation of
  the timeout. Route/profile test changes were removed afterward.
- Known-field codec allocation and a synthetic roster bounded the decoder path.
  General unknown-payload decoding and persistent roster behavior were not
  validated. Detailed integration findings remain in the private repair packet.
- One failed preparation log was overwritten on retry. Its failure survives
  only in the operator transcript; the replacement log is not cited as proof of
  that failure. This limits auditability of that attempt.

## What a fresh checkout cannot yet demonstrate

Current main does not install this test's persistent LoRa-to-TAK bridge,
private recovery policy or candidate image bytes. Its configuration templates
and selected upstream interfaces do not constitute a running gateway. The
private harness suppresses decoder database insertion, supplies a synthetic
roster and starts a temporary native CoT connection. It is not mission trust,
autonomous carrier selection or a deployed gateway service.

Independent agent `qualify_lora_boot` confirmed that boundary from the current
main service/catalog/template sources. It also found a supported integration
route: Meshtastic's host MQTT client proxy over the working BLE/serial PhoneAPI
into stock OTS translation. It requires implementation and supervision; no new
radio purchase was identified as a prerequisite. This route was source-read,
not installed or tested here. Sources: [firmware][firmware] and [Python API][api].

The next demonstration is a supervised upstream integration from boot, followed
by radio disconnect/reconnect, intended-only and unknown-recipient RF controls,
and carrier-loss recovery. Multi-hop RF, selected IP mesh, endurance, load,
coexistence, failover and mission availability remain unverified by this packet.
This records the integration backlog; it does not implement placeholder services
or decide their open trades.

## Publication and review

[Data][data] is an allowlisted extraction of measurements and predicates, not
a copied traffic capture. It excludes identities, addresses, keys, credentials,
locations, OAuth/session links and private vulnerability details. Original
logs and the test harness remain private; their hashes identify provenance,
**not publicly reproducible raw proof**. A reviewer can inspect the published
scope and measurements but cannot rerun the private harness from this checkout.
No owner acceptance or trade closure is inferred from the Program Owner's chat
receipt confirmation.

[data]: 2026-10-02-three-node-lab-observations.json
[recovery]: ../TBR-HA-01/2026-10-02-supervised-recovery-three-nodes.md
[firmware]: https://github.com/meshtastic/firmware/blob/v2.7.15.567b8ea/src/mqtt/MQTT.cpp
[api]: https://github.com/meshtastic/python/blob/2.7.11/meshtastic/mesh_interface.py
