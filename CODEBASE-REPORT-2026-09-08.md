# FML-MULE Codebase Assessment

**Assessment date:** 2026-09-08
**Source commit:** `d849ed40ff5bdbeef2def3eb6f982762768764c1`
**Repository reviewed:** `/home/mule1/FML-MULE` on `192.168.8.158`
**Local review copy:** `C:\Users\camer\Feral Mule`

## Executive conclusion

FML-MULE is a rigorous pre-PDR design-and-evidence project with a well-tested runtime decision
kernel. It is not yet a deployable MULE appliance.

The repository has unusually strong traceability, decision records, simulation evidence, tests, and
explicit evidence classifications. Its primary gap is the boundary between design/runtime modeling
and a reproducible product: there is no installable node process, operating-system image, populated
package manifest, deployable service catalog, enabled service unit, real regional profile, or
qualified hardware configuration.

## Governing documents and roadmap

`AGENTS.md` establishes the repository rules:

- The project is pre-PDR.
- CONOPS v1.01 is the operational-requirements source.
- SAD v0.31 is the architectural source.
- ADRs and trade records control decisions and open questions.
- `STATUS.md` is generated from document frontmatter.
- Evidence must remain classified as UNVERIFIED, SIMULATED, or HARDWARE-VERIFIED.
- Hardware-dependent behavior should be behind narrow interfaces with fakes.
- Placeholder services and invented specifications are prohibited.
- Related documentation should be updated whenever a decision changes.

The root `ROADMAP.md` defines exactly one milestone, v0.0.1: one node, one real service, reachable
from a phone. Its acceptance criterion is a cold-start drill performed by someone other than the
builder. The milestone requires only a local Wi-Fi access point and explicitly excludes HaLow, mesh,
LoRa, TAK, identity, rollback, and placeholder services.

No subsequent product milestone is scheduled. `docs/ROADMAP-DEV.md` instead describes engineering
tracks and decision sequencing.

Current generated status identifies 17 open trades. The critical path is:

- TBR-PWR-01
- TBR-COMP-01
- TBR-THERM-01

TBR-TAK-01 is closed. All maintainer roles are vacant, and one open trade, TBR-NET-04, has no named
owner.

## Claimed system functionality

MULE is intended to be a portable, local-first disaster-response communications and edge-services
appliance running on one Linux host.

Planned bearer plane:

- Sub-GHz HaLow IP mesh using 802.11s and batman-adv BATMAN-IV.
- Conventional Wi-Fi high-rate mesh.
- A separate Wi-Fi end-user-device access point.
- Independent LoRa/Meshtastic degraded communications.
- Optional WAN sharing.

Planned mission-service plane:

- TAK-compatible server functions.
- Browser-accessible local services.
- Offline maps and tiles.
- Identity, admission, authorization, and trust.
- Local DNS and HAProxy ingress.
- Operator status and service-control functions.
- Rootless Podman services managed through systemd Quadlets.

## Implemented functionality

### Runtime decision kernel

The `mule/` Python package contains approximately 475 production statements covering:

- Time credibility.
- Admission readiness.
- Bearer-state vocabulary.
- Radio bring-up ordering and invariants.
- Loop signatures.
- Power-runtime estimation.
- Thermal state.
- Operating-mode selection.
- Service-name composition.
- Operator-status composition.
- Sysfs-backed readers.

This code is importable and well tested, but it is not installed by the repository. There is no
daemon, command-line entry point, systemd unit, package artifact, or image integration for it.

### Configuration generation

`tools/gen-config.py` combines a region profile and mission package into resolved parameter JSON. It
detects unresolved `TBD` values and performs selected value checks.

Only the synthetic fixture region is fully resolvable. The real US-915 profile contains unresolved
regulatory and configuration values. The generator does not render the templates under `os/config/`.

### Flat-sat simulation

`test/flatsat/` integrates the runtime kernel with fake radio, power, thermal, time, WAN, and
service implementations. It tests state transitions and fault behavior without physical hardware.

The service plane is a stand-in: service names resolve to `local`, no actual HTTP request is made,
admission accepts an arbitrary device identifier, and all admitted devices see all enabled services.

### Operating system and services

The operating-system tree is a skeleton:

- No image build definition exists.
- The package manifest is empty.
- Kernel, driver, firmware, and userspace pins remain TBD.
- The common Ansible role only asserts that a region was configured.

The services tree is mostly documentation:

- The service catalog is empty.
- No enabled Quadlet units exist.
- No ingress configuration exists.
- Martin has been selected and benchmarked as the map-server implementation, but it has no catalog
  entry or deployment unit.
- OpenTAKServer was studied and exercised on a bench, but the repository does not deploy it.

### Hardware and evidence

The hardware material describes candidate prototype and test BOMs, not a qualified production block.
No completed image, assembled node, or qualification-stage result is present, and `test/results/` is
empty.

Available evidence includes:

- A simulated three-node batman-adv mesh over virtual Ethernet.
- 802.11s and WAN-sharing bench scripts using virtual wireless facilities.
- Two Meshtastic daemon containers exchanging a message over a Docker bridge.
- A reported real iTAK end-user device rendering a map from a development node with WAN
  disconnected.
- OpenTAKServer state-layout study and bench work.

These results are useful but do not demonstrate HaLow RF, LoRa RF, qualified hardware, or a
reproducibly built appliance.

## Clear and reproducible gaps

### 1. Mission schema validation is bypassed

`mission-package.schema.json` rejects unknown fields with `additionalProperties: false`.
`tools/gen-config.py`, however, directly loads mission JSON and resolves it without invoking the
schema validator.

Reproduction: the repository's deliberately invalid `mission/examples/invalid-unknown-field.json`,
containing `transmit_power_dbm`, was passed to the generator and accepted successfully.

The flat-sat boot path calls the same generator function and therefore inherits the bypass.

### 2. Service-catalog enforcement is absent

The mission schema states that every service name must have a catalog entry and that a separate
validator will enforce this. No such validator is present in `tools/`, `test/`, or `mule/`.

The catalog is empty, while example missions name services such as `example-service-a` and
`example-service-b`; the generator and flat-sat accept them.

### 3. `address_prefix` is discarded

The mission schema defines `address_prefix`, and ADR FML-ADR-063 selects a per-deployment prefix.
The generator's resolved `network` object contains `mesh_id`, `local_domain`, and `ap_ssid`, but not
`address_prefix`.

A direct generation probe confirmed the omission.

### 4. The AP-only milestone is over-gated

The root roadmap requires only a Wi-Fi access point for v0.0.1. The generator nevertheless requires
resolved values for HaLow, LoRa, Wi-Fi mesh, and Wi-Fi AP parameters before producing any
configuration.

Consequently, a legitimate AP-only v0.0.1 configuration cannot be generated against the real US-915
profile until irrelevant bearer parameters are resolved.

### 5. Unknown radio enumeration can crash integration

The radio interface explicitly permits `enumerated()` to return either a list or `None`.
`FlatSatNode._enumerated()` applies `list()` directly to the result.

A probe using an implementation that returned `None` produced:

```text
TypeError: 'NoneType' object is not iterable
```

The existing fake always returns a list, so integration tests do not cover this allowed interface
state.

### 6. Operator status can contradict itself

If the required Wi-Fi access point is absent, node state correctly becomes `FAULT`, but
`operational` remains `true` because it is derived only from whether the node booted.

A direct probe returned an equivalent of:

```json
{
  "operational": true,
  "state": "FAULT",
  "fault": "RADIO_ABSENT"
}
```

The intended meaning of `operational` needs to be defined and tested. The flat-sat wrapper also
converts unknown WAN state (`None`) to `false`, although the operating-mode logic preserves unknown
state.

### 7. Integration workflow triggers are incomplete

The mesh-probe workflow runs automatically only when its own workflow file changes. The LoRa-probe
workflow has the same narrow trigger and lacks manual dispatch.

Changes to the bench scripts, configurations, and the Meshtastic container digest in
`tools/toolchain-versions.sh` therefore do not automatically re-run the affected probes. The primary
lint workflow statically checks the shell scripts but does not execute these integration probes.

### 8. Documentation has widespread state drift

Verified examples include:

- `ROADMAP.md` says TBR-TAK-01 is open; its record, generated status, and development roadmap say it
  closed on 2026-09-06.
- `README.md` says sixteen trades are open and all are unowned; generated status reports seventeen
  open and one unowned.
- `README.md` and `STATUS.md` say nothing has been tested, despite 240 automated tests and extensive
  simulated evidence. "Nothing hardware-verified" would be accurate.
- Numerous trade and evidence documents retain `Named owner: TBD-SRR` in their prose while
  frontmatter assigns Cameron Zobrist.
- `pyproject.toml` says no Python package exists, although `mule/` is production code.
- `test/README.md` says no application code has been written.
- Service documentation says both that no service has been selected and that Martin was selected and
  measured.
- `docs/ROADMAP-DEV.md` introduces "three tracks" but contains four.

The documentation validator passes because it primarily validates structure, frontmatter, and
selected known patterns. It explicitly cannot detect arbitrary stale prose state.

### 9. There is no deployable product path

The repository currently lacks all of the following:

- A reproducible OS/image build.
- A populated and pinned package manifest.
- Installation of the `mule` package.
- A long-running node process.
- Rendered host networking configuration.
- A real service-catalog entry.
- An enabled service Quadlet.
- Configured local DNS or ingress.
- A deployable region profile.
- A completed hardware configuration.
- A recorded cold-start acceptance result.

### 10. Security and service boundaries remain intentionally unresolved

The ingress design proposes authenticating OpenTAKServer through an `X-Ssl-Cert` header. Correct
deployment therefore must strip any client-provided copy of that header, set a trusted replacement,
isolate the application port, and implement revocation.

Identity, authorization, offline TLS trust, revocation, the service controller, and the
status-aggregation daemon have not been implemented. These are documented open areas rather than
newly discovered hidden defects.

## Verification performed

Read-only verification was run on the remote repository as the normal project user.

Results:

- Dependency check: all required tools present.
- Pytest: 240 passed.
- Mutation testing: 70 of 70 mutations caught.
- Production `mule/` statement coverage: 100%.
- Bats shell tests: 35 passed.
- Shellcheck: passed.
- shfmt: passed.
- Ruff lint: passed.
- Ruff formatting: all 305 files already formatted when a writable cache was used.
- YAML lint: passed.
- Ansible lint and syntax validation: passed.
- Markdown lint: passed.
- Secrets scan: passed.
- Document, generated-status, traceability, and decision-index checks: passed.
- Mission validation and mutation checks: passed.

The top-level lint command exits with status 1 solely because `.ruff_cache` is owned by root and
cannot be updated by `mule1`. Pytest also warns that its root-owned cache is not writable.
`.ansible` and `.venv` are similarly root-owned. This is a remote workspace-hygiene problem rather
than a detected source failure, but it prevents a clean normal-user verification run.

The remote Git working tree remained clean throughout the assessment.

## Recommended future work

### P0: Make executable boundaries trustworthy

1. Invoke Draft 2020-12 mission-schema validation in every real mission-loading path.
2. Add catalog validation and reject unknown services before boot.
3. Preserve `address_prefix` in resolved configuration.
4. Make configuration requirements target-aware so the AP-only milestone does not require HaLow,
   LoRa, or mesh parameters.
5. Add regression and mutation tests for these boundaries.
6. Handle unknown radio enumeration without crashing.
7. Define and test `operational` semantics and preserve unknown WAN state.
8. Correct probe workflow path filters and add manual LoRa dispatch.
9. Repair remote cache ownership so normal-user verification is reproducible.
10. Reconcile documentation prose with authoritative frontmatter and generated status.

### P1: Deliver the defined v0.0.1 milestone

1. Select a development compute element as a milestone article without presenting it as qualified
   production hardware.
2. Create a reproducible Debian image/rootfs build and pinned package manifest.
3. Install `mule` and provide an actual node process and systemd integration.
4. Render AP-only hostapd, dnsmasq, and network configuration from validated mission and region
   inputs.
5. Use the already selected Martin map server as the likely single real service.
6. Add its catalog record, digest-pinned rootless Quadlet, local MBTiles content, DNS, and ingress
   path.
7. Document the build and cold-start process.
8. Perform and record the cold-start drill with an independent participant.

### P2: Resolve prototype hardware decisions

1. Complete RF-03 consolidation.
2. Select the carrier and M.2 arrangement.
3. Resolve the compute memory and storage decision.
4. Procure only after the documented prototype gates are satisfied.
5. Validate Linux and driver viability on the selected hardware.
6. Test RF coexistence, power, thermal behavior, RTC/BMS behavior, and hardware zone maps.
7. Produce a real US-915 regional profile from regulatory and hardware evidence.
8. Record qualification-stage results while preserving evidence-tier distinctions.

### P3: Implement the mission-service plane

1. Deploy OpenTAKServer as its three required processes: `opentakserver`, `eud_handler`, and
   `cot_parser`.
2. Implement the chosen high-availability mechanism for SQL plus `config.yml`, CA material, and
   uploads without relying on wall-clock conflict resolution.
3. Implement identity, admission, authorization, offline TLS, and revocation.
4. Build the service controller and operator-status aggregator.
5. Add gateway services and validate their isolation boundaries.
6. Complete map hardware/content/USB checks.
7. Implement rollback and at-rest key management.
8. Advance through the repository's qualification stages with reproducible evidence.

## Overall assessment

The repository is strongest as an engineering governance and executable-modeling foundation. Its
tests give meaningful confidence in the current pure decision logic, and its evidence discipline
prevents simulated results from being mistaken for physical validation.

The next valuable step is not broader architecture work. It is to close the generator and validation
defects, then establish the first narrow vertical product slice: validated AP-only configuration, a
bootable image, the installed node runtime, one real map service, and the independent cold-start
drill already specified by the roadmap.

## Local checkout note

The local clone may show `CLAUDE.md` as modified because its repository symlink could not be
reproduced correctly on the Windows checkout. This is a local filesystem artifact. The remote
repository was not changed.
