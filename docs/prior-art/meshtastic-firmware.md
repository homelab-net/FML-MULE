# Meshtastic firmware

**Evaluated:** 2026-09-10 at release `v2.7.26.54e0d8d`, commit
`54e0d8d0ab2ff56b3a9ce967e53f79e49af560fb`. **Verdict:** adopt only within the
separate degraded bearer selected by `FML-ADR-026`, subject to board, security
and hardware gates.

## Fit

Meshtastic firmware supplies LoRa mesh text, position and telemetry transport on
ESP32, nRF52, RP2040/RP2350 and Linux-native profiles. Its client API is
available over platform-dependent serial, Bluetooth and IP paths, with optional
MQTT integration. This supports `FML-REQ-013`, `FML-REQ-014` and
`FML-REQ-030` without pretending that LoRa is an IP bearer.

`FML-ADR-026` selects Meshtastic for the separate non-IP degraded plane.
`FML-ADR-048` requires existing OpenTAKServer and Meshtastic interfaces before
custom glue, and `FML-ADR-070` keeps recipient semantics in upstream
`GeoChat.to` and `Contact.callsign`. This evaluation does not select a board,
radio, channel plan or power envelope.

## Runtime and data

When an IP interface is enabled, pinned source starts the Meshtastic client API
on TCP 4403. Other profiles expose USB serial, UART or Bluetooth, and MQTT is
optional. Secrets include channel pre-shared keys, device private keys, optional
MQTT credentials and Linux-native TLS material. The firmware controls the MCU,
radio and board peripherals, so its privilege boundary is the device itself.

Configuration, keys, node state and optional messages persist in board flash;
Linux-native profiles use host files. Exact paths, capacity, export and rollback
are board dependent. Promotion therefore needs one immutable board artifact and
a demonstrated upgrade and recovery path, not a generic source tag.

The stock default is not an acceptable confidentiality profile. Existing FML
source analysis established that unconfigured nodes converge on a common channel
using a published, compiled-in key, and the same behavior is present in the
evaluated commit. The stock default therefore blocks profile approval; an
owner-approved separation and confidentiality control remains to be selected.
The presence of encryption does not make default-channel traffic confidential.

The existing FML flat-sat used digest-pinned `meshtasticd` from the 2.7.26
family on two simulated nodes. It demonstrated that `Contact.callsign` and
`GeoChat.to` survived the software bearer. That result is `SIMULATED`: it says
nothing about RF, range, timing, power, thermal behavior or an MCU build, and it
does not qualify this Git artifact as prototyped.

## Security intake

GitHub's repository advisory endpoint returned 16 advisories on 2026-09-10.
Most older runtime advisories declare patched releases earlier than 2.7.26.
`GHSA-7ph5-2mjv-69h8` affects releases through 2.7.22.96dd647, placing the
evaluated release outside its stated range even though no patched version is
declared. `GHSA-mjx5-98jq-q736` concerns arbitrary code execution in a
`pull_request_target` workflow and declares no affected or patched range, so a
firmware version comparison does not resolve that build-pipeline issue.

`GHSA-h79j-c836-5j74` remains directly relevant: it declares all Linux-native
versions affected because generated TLS private-key material is world-readable,
with no patched version. An FML Linux-native profile cannot ignore that issue.
The registry names every remaining advisory identifier and its relationship to
the evaluated release. No independent audit or repository SBOM was identified.

## Intake result

- License: GPL-3.0. A board image also combines PlatformIO libraries,
  bootloaders and vendor components, so redistribution review remains pending.
- Maintenance: the latest non-prerelease GitHub release was published
  2026-06-24; newer 2.8.0 prereleases and development commits continued through
  September. There were 216 open issues on 2026-09-10. Several high-volume
  maintainers and a broad contributor base reduce concentration risk.
- Platform: broad upstream board coverage, but no selected profile yet supports
  a MULE compatibility claim.
- Resources: not measured on a selected MCU, radio or MULE host.
- Prototype: the exact Git release was not built. Existing simulation evidence
  is retained separately and is not hardware evidence.

## Exit strategy and questions

Keep TAK-to-Meshtastic integration at upstream protocol boundaries so the
degraded bearer can change without custom EUD or TAK protocols. Before hardware
promotion, select the exact board and radio profile, generate and review its
firmware SBOM, resolve Linux-native key permissions where applicable, and
demonstrate configuration backup, update rollback and the required RF behavior.

## Sources

- [Pinned firmware overview](https://github.com/meshtastic/firmware/blob/54e0d8d0ab2ff56b3a9ce967e53f79e49af560fb/README.md)
- [Pinned build configuration](https://github.com/meshtastic/firmware/blob/54e0d8d0ab2ff56b3a9ce967e53f79e49af560fb/platformio.ini)
- [Pinned TCP client API](https://github.com/meshtastic/firmware/blob/54e0d8d0ab2ff56b3a9ce967e53f79e49af560fb/src/mesh/api/ethServerAPI.cpp)
- [Pinned public default key](https://github.com/meshtastic/firmware/blob/54e0d8d0ab2ff56b3a9ce967e53f79e49af560fb/src/mesh/Channels.h)
- [Pinned default-channel initialization](https://github.com/meshtastic/firmware/blob/54e0d8d0ab2ff56b3a9ce967e53f79e49af560fb/src/mesh/Channels.cpp)
- [Pinned persistent node database](https://github.com/meshtastic/firmware/blob/54e0d8d0ab2ff56b3a9ce967e53f79e49af560fb/src/mesh/NodeDB.cpp)
- [FML default-channel source analysis](../evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md)
- [FML simulated bearer evidence](../evidence/TBR-NET-02/2026-09-06-geochat-to-survives-the-meshtastic-bearer.md)
- [Release history](https://github.com/meshtastic/firmware/releases)
- [Contributor summary](https://api.github.com/repos/meshtastic/firmware/contributors)
- [Repository security advisories](https://github.com/meshtastic/firmware/security/advisories)
