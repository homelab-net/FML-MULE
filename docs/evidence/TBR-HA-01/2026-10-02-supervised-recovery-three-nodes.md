# Supervised recovery on the three-node lab

**Prototype observations; TBR-HA-01 remains open.** This follows the
[manual worker-move record](2026-10-01-routed-marker-streaming-host.md).
The [shared observation record][data] identifies the source revision, candidate
images, operators, dates and private log hashes. It is a sanitized extraction,
not a public raw journal or a qualification-stage result.

## What recovered without intervention

After the desktop installed the private policy and injected worker or broker
faults, native supervision recovered the tested services on Pi 1, Pi 2 and
bench without a manual service restart during those observation windows.
Native TCP fake-EUD tests checked intended-only callsign and UID delivery plus
unknown-recipient rejection before faults and after each recovery. Those are
semantic delivery controls, separate from container/process health.

The synthetic clients waited for asynchronous broker setup before first identity.
Their success does not cover immediate first-client identity at cold startup.

| Host | Worker crash to observed healthy state, seconds | Broker crash to observed healthy state, seconds |
| --- | ---: | ---: |
| Pi 1 | 28.048 | 124.776 |
| Pi 2 | 24.337 | 64.948 |
| Bench | 17.887 | 15.488 |

These values come from the live fault logs fingerprinted in [data]. They are
single uncontrolled observations, not statistical distributions, recovery
deadlines or mission availability guarantees. The parser has process
supervision only; listener health does not by itself establish semantic chat
delivery. A real-phone chat was not exercised during these faults.

One later controlled Pi 1 reboot reached active TAK target state automatically
at 137.379645 seconds since boot, from systemd's monotonic active timestamp.
Intended-only native chat controls passed afterward. This does not measure
continuous service availability, a LoRa gateway starting on boot, or reboot
recovery on Pi 2 and bench. The desktop requested the reboot and ran the checks;
it did not manually start TAK during that recovery.

## Installed policy and administrative boundaries

The trial covered six rootless services on each Pi and seven rootful bench
containers. It used native restart, readiness, dependency and health handling,
including a five-total-start cap. Exhaustion is an intentional stop requiring
explicit administrative reset. A capability-target stop remains administration.
An individually stopped upheld client returns while its broker remains active.

Policy preparation was intervention: local unit/target edits, client image
replacement and readiness correction preceded the tests. A first drop-in
dependency reset did not work and was removed before the final target edit.
The lab policy is not a catalog decision or an installer delivered by main.
The source/package equality checks do not cover those configuration changes.

The disposable policy probe exercised crash, clean exit, health failure,
retry exhaustion and explicit reset. Its unchanged-policy control failed the
automatic-recovery assertion as expected. This establishes that the probe
noticed the absent policy; it does not establish a field recovery bound.

## Remaining limits

No network partition, selected IP mesh survival, radio reconnect, RF failover,
memory/storage exhaustion, fleet-wide reboot persistence or mission-state
restore was established. The [mixed-carrier chat][carriers] required desktop
coordination and is separate from automatic service recovery. TBR-HA-01 still
needs its selected production mechanism and owner-accepted closure evidence.

The candidate connection-state fix is tracked in PR #208. Its upstream
software regression result is not an automatic recovery result from main.
Neither this packet nor a green CI run installs the private supervision policy.

[data]: ../TBR-NET-02/2026-10-02-three-node-lab-observations.json
[carriers]: ../TBR-NET-02/2026-10-02-three-node-lab-boundaries.md
