# Service catalog

The set of services approved to run on a MULE node, and what each one is for.

**Two entries: `opentakserver` and `martin`** (`catalog.yml`, `FML-ADR-078`).
Each is approved as a *catalog contract*, but both are disabled and neither is a
deployable build: no loadable unit exists, and their image digests and measured
resource envelopes carry `TBD` until `TBR-COMP-01`, `TBR-MAP-01` and the
OpenTAKServer build close. A mission cannot enable either record in this state.

## Why a catalog exists

A node has a bounded compute and power budget (`TBR-COMP-01`, `TBR-PWR-01`) and
one compute element shared between the network plane and the mission-service
plane (`FML-ADR-021`). Every service competes with routing for resources, and
the failure mode is specific: a service takes memory, the routing daemon is
starved, mesh links flap, and the node appears to have a radio fault when it
has a scheduling fault.

A catalog makes adding a service a decision with a record, rather than a file
appearing in `quadlets/`.

## What a catalog entry records

| Field | Notes |
| --- | --- |
| Name | Stable identifier used by the Quadlet unit and the ingress configuration. |
| Enabled | True only when the deployment unit exists and a mission may select it. |
| Aliases | Optional alternate mission references; every alias resolves uniquely. |
| Unit | The exact `<name>.container` Quadlet, or `TBD` while the record is disabled. |
| Purpose | One line. Why a node runs this. |
| Image | OCI reference **by immutable digest**, never by tag. |
| Upstream | Project, licence, and where its source lives. |
| Rootless | Yes, or rootful with the reason recorded here. `FML-ADR-029`. |
| Resource envelope | Measured memory and CPU under representative load. `TBR-COMP-01`. |
| Exposed to | The mesh, the EUD access point, or the node only. These are different trust levels; see `os/config/nftables.conf.template`. |
| Durable state | What it stores, and whether that state must survive node loss. `TBR-TAK-01`. |
| Recovery | What a restart costs. `TBR-HA-01`. |
| Region dependency | Whether anything about it is region-specific. |
| ADR | The decision that approved it. |

The **resource envelope** field is deliberately "measured", not "estimated". An
entry with an estimated envelope has not been evaluated.

## Rules

- **Digest, never tag.** Anywhere in this repository. See `services/README.md`.
- **No service is added without a catalog entry.** A Quadlet unit with no entry
  is a defect.
- **No disabled service is enabled by a mission.** A contract with a `TBD` unit
  is retained for planning but cannot become generated configuration.
- **Aliases and units resolve exactly once.** Duplicate names, ambiguous aliases,
  absent units and loadable units with no enabled catalog entry fail CI.
- **No service is added without a resource measurement**, once `TBR-COMP-01`
  has established how the budget is measured.
- **Durable state is declared**, not discovered. `TBR-TAK-01` classifies
  mission state as transient or durable, and a service whose durable state was
  never declared will lose it during a rollback.

## Expected entries

OpenTAKServer and Martin are selected catalog contracts but are not enabled for
deployment. Other entries below name what the plane may eventually hold, not a
commitment:

- Browser-based field services beyond the selected map service.
- An identity and mission trust layer. See `services/identity/`.
- An operator status surface, fed by the status aggregator, which is a
  placeholder and must not be implemented yet.

None of those additional entries has been selected, sized, or approved.
