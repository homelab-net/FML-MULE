# Services

The mission-service plane: the applications running above the network plane on
the same compute element (`FML-ADR-021`).

**Almost nothing here is implemented, and four components must not be.** See
the placeholder rule below.

## Execution model

Services run as OCI containers under **rootless Podman**, declared as **Podman
Quadlet** units and supervised by systemd. `FML-ADR-029`.

- Service definitions are files in this repository, so the service plane is
  part of the image build and the promotion gate rather than being configured
  by hand on a device.
- A service that genuinely cannot run rootless may run rootful, with the reason
  recorded in its catalog entry.
- Restart and recovery policy is **not** decided. `TBR-HA-01` is open, and a
  naive restart policy on a resource-constrained node turns one failed service
  into a dead node.

## Container images are referenced by digest, never by tag

**Every OCI image reference in this repository uses an immutable digest.**

```text
# Correct
image=registry.example.org/project/service@sha256:<64 hex characters>

# Never
image=registry.example.org/project/service:latest
image=registry.example.org/project/service:1.2.3
```

A tag is a mutable pointer. The image behind it can change without any file in
this repository changing, which means the artifact that was reviewed is not
necessarily the artifact that runs. That is unacceptable under the
compatibility-set rule in `FML-ADR-040`, and it is exactly the kind of silent
substitution `THREAT_MODEL.md` lists the supply-chain controls against.

A digest reference also means updates do not happen by themselves. That is the
intent, not a side effect: promotion of a dependency is a decision.

## The placeholder rule

**Four components in this directory hold a `README.md` and nothing else, by
decision:**

| Component | Blocked on |
| --- | --- |
| `status-aggregator/` | `TBR-TAK-01`, `TBR-HA-01` |
| `mission-trust/` | `TBR-SEC-01`, `TBR-TIME-01`, `TBR-TAK-01` |
| `service-controller/` | `TBR-HA-01`, `TBR-TAK-01` |
| `gateways/` | `TBR-TAK-01`, `TBR-RF-02` |

Their interfaces depend on trades that have not closed. Writing them now means
writing against an interface that will change, and the code will be defended
rather than rewritten, because it works.

Adding code to those four directories is the most likely way to waste weeks of
work in this repository. Each README names what must close first. See
`AGENTS.md`, constraint one.

## Hardware abstraction: the governing code rule

Two or three physical nodes will exist for a long time. **Contributors will
have none.** A change that can only be exercised by the person holding the
hardware can only be reviewed by that person, and a project with that property
has one contributor by construction.

Therefore:

- Every function that reads or controls **radio, power, thermal, or time
  state** **shall** sit behind a narrow interface with a fake or
  recorded-fixture implementation.
- Service-plane and status code **shall** be runnable and testable on an
  **ordinary laptop against fakes, with no radios present**.
- Fixtures captured from real hardware go in `test/fixtures/` with the node
  identifier, capture date, and image build recorded alongside them.

An interface with no fake is not complete. This is the difference between a
project one person can work on and one other makers can contribute to.

## Logging and error handling

Established now, before there is code to apply it to, because retrofitting
logging conventions is tedious and retrofitting a "no location data in logs"
rule after a leak is impossible.

- **Structured logging to the journal.** Not to files a service manages itself.
- **No credential or location data in logs by default.** Participant location
  is the asset whose compromise causes direct physical harm to a person
  (`THREAT_MODEL.md`), and it is generated continuously by design. A debug log
  that records position reports is a location history in plain text on a device
  expected to be captured.
- **Log level configurable per service**, at runtime where practical. A field
  fault that can only be diagnosed by rebuilding the image is a fault that does
  not get diagnosed.
- **Any function that can fail returns an explicit error rather than exiting
  the process.** A service that exits on an unexpected condition invokes the
  restart policy, and `TBR-HA-01` is open precisely because a restart loop on a
  constrained node is a way to lose the whole node.

## Directory map

| Directory | Contents |
| --- | --- |
| `catalog/` | Approved service catalog definitions. |
| `quadlets/` | Podman Quadlet and systemd unit definitions. |
| `tak/` | TAK-compatible service deployment and state notes. |
| `ingress/` | Local DNS and proxy configuration. |
| `identity/` | PKI, admission, and mission trust material handling. |
| `status-aggregator/` | Placeholder. Do not implement. |
| `mission-trust/` | Placeholder. Do not implement. |
| `service-controller/` | Placeholder. Do not implement. |
| `gateways/` | Placeholder. Do not implement. |
