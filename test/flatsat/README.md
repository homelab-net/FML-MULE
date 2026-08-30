# The flat-sat

A spacecraft flat-sat is the flight hardware laid out on a bench: the real
avionics, the real harness, the real software, wired up where an engineer can
reach every connector, with the things that cannot be brought indoors replaced
by stimulators. It exists so that integration problems are found while they are
cheap, and so the flight article is not the first place the system is assembled.

This is the software equivalent. It is the real node logic, composed and run end
to end, with the hardware layer replaced by fakes behind the narrow interfaces
in `interfaces.py`.

## What it covers

The `ROADMAP.md` v0.0.1 flow, which is the same flow the milestone is accepted
on: power on, configuration resolution, bearer bring-up, and whether the
services a mission package enables are the services a device can resolve.

Plus the refusal paths, which are the reason the rest is worth having:

- A region profile whose values are still `TBD` refuses to generate, naming the
  trade. No lawful configuration means no transmission.
- A profile that resolves to something the region forbids is rejected.
- Retained local time that cannot be trusted refuses admission rather than
  failing open, per `FML-ADR-042`.
- A node that cannot serve users reports a fault rather than GREEN.

## What it does not cover

CONOPS section 82 runs **power on -> connect -> authenticate -> authorized
services appear -> operate**. The flat-sat covers the first two and a stub of
the third. This section exists because an earlier draft of this file claimed
the whole flow, which was not true and would have been baselined against.

| Step | State | Blocked on |
| --- | --- | --- |
| Authenticate | **Absent.** `admit()` accepts any device identifier. There is no credential, no identity, no enrollment. | `TBR-ID-01`, `services/mission-trust/` |
| Authorized services appear | **Absent.** Every admitted device resolves every enabled service. There is no role, no scope, no per-user catalog. | `TBR-ID-01`, `TBR-TAK-01` |
| Operate | **Absent.** Service resolution returns a name. No request is made and nothing answers. | `services/` components remain placeholders |

CONOPS section 68 stacks six controls - network admission, user identity, role
and scope, application authorization, TAK authorization, administrative
authorization. The flat-sat exercises part of the first. Do not read a passing
run as evidence about any of the other five.

Nor does a fake produce evidence about physical behaviour, at any level of
effort, because the fake is where the physics was removed:

| Supports a claim about | Supports no claim about |
| --- | --- |
| Software logic and integration | RF propagation, range, throughput |
| The covered flow and its ordering | Power draw, endurance, battery behaviour |
| Failure handling and refusal paths | Thermal behaviour in an enclosure |
| Configuration resolution and region validation | Driver attachment, firmware behaviour |
| Operator-facing status and its vocabulary | Timing, latency or jitter under load |

Those belong to the ITEP campaigns in `docs/verification/`, on rig R1 and above.

## Where the decisions actually live

`node.py` decides nothing. It gathers what the fakes report and asks `mule/`,
which is production code held to production standards:

| Question | Answered by |
| --- | --- |
| Can the clock be trusted? | `mule/timekeeping.py` |
| May this device join? | `mule/admission.py` |
| What does this node offer, and by what name? | `mule/services.py` |
| Which operating modes is the node in? | `mule/modes.py` |
| What do we tell the operator? | `mule/status.py` |
| Which radios matter? | `mule/bearers.py` |

This split is `FML-ADR-051`, and it is the reason the flat-sat is worth
anything: the same decisions run on a real node with real drivers behind the
same interfaces. When a decision lived in the test tree, a fake could answer it
and no test could tell.

## The four rules

1. **It runs the real artifacts, not parallel copies.** `node.py` loads
   `tools/gen-config.py` by path and imports every decision from `mule/`. A
   flat-sat that has drifted from the node is worse than none, because "it
   works on the flat-sat" becomes a permanent excuse.
2. **Every fake is named below**, and `tools/validate-docs.sh` fails if one is
   not. An unlisted fake is a hidden assumption.
3. **A fake reports; it does not conclude.** Anything the node has to *decide*
   is decided by code under test. A fake that returns a verdict makes the
   verdict untestable, because the test then agrees with the fixture.
4. **A passing scenario yields `SIMULATED`, never more.**

## Every fake, named

All four live in `fakes.py`. Each is scripted, not modelled: it returns what the
scenario told it to return. None contains a curve, a model, or a constant
derived from anything but the scenario, because no measured value exists to
derive one from.

| Fake | Interface | Simulates | Does not simulate | Trade that replaces it |
| --- | --- | --- | --- | --- |
| `FakeRadio` | `RadioState` | Driver attachment, link formation, peer visibility | RF propagation, throughput, desense, multicast scaling, coexistence | `TBR-RF-01`, `TBR-RF-02`, `TBR-RF-03` |
| `FakePower` | `mule.power.PowerReadings` | Pack presence, pack health, reported charge, pack temperature | Discharge behaviour, capacity fade, load, endurance | `TBR-PWR-01` |
| `FakeThermal` | `mule.thermal.ThermalReadings` | What each fitted sensor reports, and whether the compute element says it is throttling | Heat flow, ambient sensitivity, solar load, the enclosure | `TBR-THERM-01` |
| `FakeTranslation` | `mule.loops.TranslationReadings` | What batctl reports about who is reachable where, including being unreadable, and which of the node's own addresses came back | batman-adv's ageing; a real table expires entries, and a stale one is the innocent explanation for a signature | `TBR-NET-01` |
| `FakeMeshState` | `mule.bringup.MeshReadings` | What a finished node reports about its mesh, including the platform being unable to answer | Bring-up itself, and the order it happened in; a snapshot cannot show an order | `TBR-LINUX-01` |
| `FakeLoRaPlane` | `LoRaPlane` | Whether the LoRa stack answers, including the platform being unable to tell | Airtime, duty cycle, range, collisions, and any message actually crossing | `TBR-NET-02` |
| `FakeClock` | `mule.timekeeping.TimeReadings` | What the RTC and system clock report, and whether time was set upstream | Drift, holdover duration, skew accumulation | `TBR-TIME-01` |

`FakePower` no longer answers how long the node will run. That is
`mule.power.assess`, which returns `None` with a reason naming `TBR-PWR-01`
while no measured model exists, and a real estimate once one is supplied. The
scenarios assert both: that the node refuses today, and that the same code
answers the day the trade closes.

`FakeRadio` **rejects hardware that cannot exist** - a bearer linked without
being present, or reporting peers while absent - by raising
`ImpossibleHardwareState` at construction. Without that, a scenario can pass
against a node state no hardware can produce, which voids the only claim the
flat-sat makes.

### Why the fakes report rather than conclude

`FakeClock`, `FakePower` and `FakeThermal` all supply raw readings and reach no
verdict. Whether the readings mean anything is decided by `mule/timekeeping.py`,
`mule/power.py` and `mule/thermal.py`, which are production code under test.

It supplies raw readings and reaches no verdict. Whether they are credible is
decided by `mule.timekeeping.assess`, which is production code in the sense
`FML-ADR-051` gives the word: it lives outside this tree, in `mule/`, and is
held to production lint and docstring standards rather than the test tree's
relaxations.

None of them started that way, and each cost something before it changed:

- `FakeClock` returned `CREDIBLE` or `DEGRADED` directly, so the fail-closed
  tests asserted that a fixture agreed with itself. No code decided anything, so
  `FML-ADR-042` could not fail a test.
- `FakePower` returned `None` for projected runtime unconditionally, which was
  the right answer for the wrong reason: it was a stub, not a refusal, and it
  would have kept returning `None` after `TBR-PWR-01` closed.
- `FakeThermal` returned `within_envelope=True` by default, so a node with no
  defined thermal envelope **asserted it was inside one**. That is a claim about
  a limit nobody has measured.

The last is the clearest case for the rule. A fake that concludes does not just
make the conclusion untestable; it can make the node state something untrue.

## Stand-ins, which are not fakes

A fake replaces hardware. A **stand-in** occupies the place of software not yet
written, and there is one:

- **The service plane.** `FlatSatNode` resolves the service names a mission
  package enables to a local stand-in. `services/status-aggregator/`,
  `services/mission-trust/`, `services/service-controller/` and
  `services/gateways/` are approved but blocked on trades that have not closed,
  and `AGENTS.md` forbids implementing them to make a scenario pass.

Exercising their **interfaces** with a stand-in is what a flat-sat is for:
bringing up the bus while the payload does not exist yet.

## Checking that the tests can fail

A passing suite proves the tests agree with the code. It does not prove they
would notice if the code were wrong. `tools/mutation-check.py` checks the second
claim: it breaks the node one specific way at a time and expects the suite to
fail each time. A break the suite does not notice is a **survivor**.

```sh
tools/mutation-check.py          # every mutation must be caught
tools/mutation-check.py --list   # what the suite is required to detect
```

The mutations live in `mutations.yml` as reviewable data. Adding one records
"the suite must notice this"; if it survives, write the missing test or delete
the mutation with a reason. Line coverage is deliberately not the measure here:
this suite once ran at 96% line coverage while failing to notice that battery,
network, LoRa and thermal state could all be hardcoded healthy.

## Region fixtures

Scenarios generate against `test/fixtures/regions/xx-testfixture/`, which is
synthetic. Every number in it is invented and none of it describes any real
allocation. It lives outside `regions/` on purpose, so a fixture value can never
be mistaken for a deployable regulatory profile.

Some scenarios generate against `regions/us-915/profile.yml` instead and assert
that the node **refuses to come up**, because every value there is still `TBD`.
That refusal is the behaviour under test, not an obstacle to it.

## Layout

| File | Contents |
| --- | --- |
| `interfaces.py` | Narrow Protocols over radio, power and thermal state. They stay here deliberately; see the location note in the file. |
| `fakes.py` | The four fakes above, and nothing else. |
| `node.py` | `FlatSatNode`: **assembly, not judgement.** It reads the fakes, hands plain values to `mule/`, and reports what came back. |
| `conftest.py` | The fixture time policy and the node factory, so no scenario carries a literal another scenario must match. |
| `test_modes.py` | Unit tests for `mule/modes.py`, the nine CONOPS section 50 axes. |
| `test_timekeeping.py` | Unit tests for `mule/timekeeping.py`. Moves with it if it moves again. |
| `scenarios/` | The user-visible flows, written in CONOPS vocabulary. |
| `mutations.yml` | What the suite is required to be able to detect. |

## Running it

```sh
python -m pytest test/flatsat
tools/mutation-check.py
```

No radios, no battery, no enclosure, no network. If a scenario ever needs one of
those, the boundary is in the wrong place and the fix is a narrower interface,
not a skipped test.
