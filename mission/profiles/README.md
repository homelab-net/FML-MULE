# Mission profiles

A **mission profile** is the operating posture a node is placed in for a
deployment: what it may transmit, what it runs, and what it records.

**Definitions are `TBD`.** The three profile names below are fixed in the
package schema so that a package cannot select a posture the node does not
understand. What each one actually does is not decided.

## The three profiles

### `standard`

Normal operation. Every bearer available, services running, ordinary logging.

`TBD`: everything, because "normal" is defined by the CONOPS and the CONOPS has
not been transcribed. See `docs/conops/README.md`.

### `exercise`

Training and exercise use. Distinguished from `standard` so that exercise
traffic is not mistaken for real traffic, by people or by other systems.

`TBD`. Expected to cover: marking traffic as exercise, and whether an exercise
node may associate with a node in `standard`. The failure this profile exists
to prevent is an exercise position report reaching a real incident's common
picture, which is an operational problem rather than a technical one.

### `emcon`

Emission control: restricting or ceasing transmission to reduce detectability.

`TBD`, and the least well understood of the three.

## What EMCON can and cannot do

Stated plainly, because a profile named EMCON invites a belief it cannot
support.

**`THREAT_MODEL.md` records that the only reliable way not to be detected is
not to transmit.** MULE is a multi-bearer device by design: several distinct
emitters, in several bands, transmitting concurrently, in a pattern that is
close to a fingerprint for this class of device. Consequences no configuration
changes:

- Presence is detectable whenever anything transmits.
- Location is obtainable by direction finding with commodity equipment.
- Traffic analysis works on encrypted traffic, and position reporting is
  periodic, which is exactly the regularity that makes it easy.

So an EMCON profile can reduce emissions. It cannot make a transmitting node
undetectable, and it must not be documented as though it could. If a
participant's safety depends on their location not being discoverable, this
system does not provide that.

**What an EMCON profile can actually enforce is `TBR-RF-02`**, which is also
where the coexistence controls between the sub-GHz bearers are decided.

There is an enforcement question that has no answer yet: a service that
transmits despite the profile is a safety problem, not a bug, and where that is
enforced is undecided. `os/config/nftables.conf.template` notes a default-deny
output chain as one candidate, and flags that it may not be the right place.

## Adding a profile

The three names are an enumeration in `mission/schema/`. A node that met an
unrecognised profile would have an undefined emission posture, and a node that
silently fell back to a permissive default under a profile it did not
understand would be an EMCON failure. So the enumeration is closed on purpose.

Adding a profile means changing the schema, which means a package format
version change, which means older images running the known-good rollback path
may not understand it. See `mission/schema/README.md` and `TBR-REC-01`.
