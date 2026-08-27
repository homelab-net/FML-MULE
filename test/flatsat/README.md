# The flat-sat

A spacecraft flat-sat is the flight hardware laid out on a bench: the real
avionics, the real harness, the real software, wired up where an engineer can
reach every connector, with the things that cannot be brought indoors replaced
by stimulators. It exists so that integration problems are found while they are
cheap, and so the flight article is not the first place the system is assembled.

This is the software equivalent. It is the real node logic, composed and run end
to end, with the hardware layer replaced by fakes behind the narrow interfaces
in `interfaces.py`.

## What it is for

To verify the **end user experience** described in CONOPS section 82 — power on,
connect, authenticate, authorized services appear, work — so that:

- what is developed matches how it will be used, and
- the end-to-end flow is free of logic bugs before hardware is scarce,
  expensive, and shared between two or three people.

The first scenario deliberately targets the same flow as the `ROADMAP.md` v0.0.1
acceptance criterion. One node, one service, reachable from a client. They are
the same flow, so they are verified once.

## What a passing run means

`SIMULATED`. Nothing more, and the word is doing work.

| It supports a claim about | It supports no claim about |
| --- | --- |
| Software logic and integration | RF propagation, range, throughput |
| The user-visible flow and its ordering | Power draw, endurance, battery behaviour |
| Failure handling and refusal paths | Thermal behaviour in an enclosure |
| Configuration resolution and region validation | Driver attachment, firmware behaviour |
| Operator-facing status and its vocabulary | Timing, latency or jitter under load |

The right-hand column is not a list of things nobody has got to yet. It is the
list of things a fake **cannot** produce evidence about, at any level of effort,
because the fake is where the physics was removed. Those belong to the ITEP
campaigns in `docs/verification/`, on rig R1 and above.

## The three rules

1. **It runs the real artifacts, not parallel copies.** `node.py` loads
   `tools/gen-config.py` by path and calls it. It does not reimplement region
   resolution. A flat-sat that has drifted from the node is worse than none,
   because "it works on the flat-sat" becomes a permanent excuse.
2. **Every fake is named below.** A reader must be able to see exactly which
   boundary is simulated. An unlisted fake is a hidden assumption.
3. **A passing scenario yields `SIMULATED`, never more.**

## Every fake, named

All four live in `fakes.py`. Each is scripted, not modelled: it returns what the
scenario told it to return. None of them contains a curve, a model, or a
constant derived from anything other than the scenario, because no measured
value exists to derive one from.

| Fake | Interface | Simulates | Does not simulate | Trade that replaces it |
| --- | --- | --- | --- | --- |
| `FakeRadio` | `RadioState` | Driver attachment, link formation, peer visibility | RF propagation, throughput, desense, multicast scaling, coexistence | `TBR-RF-01`, `TBR-RF-02`, `TBR-RF-03` |
| `FakePower` | `PowerState` | External source presence, pack presence, pack health flag | Consumption, endurance, projected runtime, charge behaviour | `TBR-PWR-01` |
| `FakeThermal` | `ThermalState` | A throttle flag and an in-envelope flag | Temperature, heat flow, ambient sensitivity, the enclosure | `TBR-THERM-01` |
| `FakeClock` | `TimeState` | Whether retained time is credible, and why not | Drift, holdover duration, skew, resynchronisation | `TBR-TIME-01` |

`FakePower.projected_runtime_minutes()` returns `None` unconditionally. That is
not a stub waiting to be filled in with a number; it is the correct answer until
`TBR-PWR-01` closes, and the scenarios assert it.

## Stand-ins, which are not fakes

A fake replaces hardware. A **stand-in** occupies the place of software that has
not been written, and there is one:

- **The service plane.** `FlatSatNode` resolves one logical service name to a
  local stand-in. `services/status-aggregator/`, `services/mission-trust/`,
  `services/service-controller/` and `services/gateways/` are approved but
  blocked on trades that have not closed, and `AGENTS.md` forbids implementing
  them to make a scenario pass.

Exercising their **interfaces** with a stand-in is what a flat-sat is for:
bringing up the bus while the payload does not exist yet. Implementing them
here to turn a scenario green would be the failure mode, not the fix.

## Region fixtures

Scenarios generate against `test/fixtures/regions/xx-testfixture/`, which is
synthetic. Every number in it is invented and none of it describes any real
allocation. It lives outside `regions/` on purpose, so a fixture value can never
be mistaken for a deployable regulatory profile. See
`test/fixtures/regions/README.md`.

Two scenarios generate against `regions/us-915/profile.yml` instead, and assert
that the node **refuses to come up**, because every value in that profile is
still `TBD`. That refusal is the behaviour under test, not an obstacle to it.

## Layout

| File | Contents |
| --- | --- |
| `interfaces.py` | The narrow Protocols over radio, power, thermal and time state. Production code that has nowhere to live yet; see the location note in the file. |
| `fakes.py` | The four fakes above, and nothing else. |
| `node.py` | `FlatSatNode`: the node composed from those interfaces, calling the real configuration tool. |
| `scenarios/` | The user-visible flows, written in CONOPS vocabulary. |

## Running it

```sh
python -m pytest test/flatsat
```

No radios, no battery, no enclosure, no network. If a scenario ever needs one of
those, the boundary is in the wrong place and the fix is a narrower interface,
not a skipped test.
