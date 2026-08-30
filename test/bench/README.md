# Bench

Bench procedures and instrumentation notes: how a measurement is taken, with
what, and what makes it repeatable.

**One procedure. No measurement has been taken.**

`80211s-mesh.sh` exercises 802.11s association and batman-adv over it using
`mac80211_hwsim`, with no radio. It is a procedure rather than a measurement:
it asserts that the stack composes and that a mesh point reports carrier only
once joined, which `FML-ADR-059` depends on. It produces no number.

It does not run in CI and cannot: a hosted runner's kernel has no wireless
stack at all. Run it on a development machine, as root. See
`docs/dev-machine.md`.

## Bench, stage, evidence

Three related things, kept apart on purpose:

- **`test/bench/`**, here: *how* to take a measurement. A procedure, reusable
  across many runs.
- **`test/stages/`**: *what* must be demonstrated to qualify a build, with pass
  criteria.
- **`docs/evidence/<TRADE-ID>/`**: the results that close a trade.
  **`test/results/`**: the results of a stage run.

A bench procedure is written once and cited from wherever it is used. A
procedure copied into three trade documents will diverge in three directions.

## What a bench procedure must contain

- **What is measured**, in terms someone else could repeat.
- **Instrumentation**: instrument class, model, and where calibration matters,
  the calibration expectation. A measurement whose instrument is unrecorded
  cannot be compared with another.
- **Setup**, including a diagram where the physical arrangement matters. For RF
  it always matters: antenna type, orientation, separation, and what else is in
  the room.
- **Conditions to record**: ambient temperature, supply voltage, image build,
  region profile, what else was transmitting.
- **Procedure**, step by step.
- **What to record**, and in what form. Raw output is preferred over a summary.
- **Known sources of error**, and how to avoid them.

## Procedures this program will need

None is written. The trades that will demand them:

| Procedure | Trade |
| --- | --- |
| Throughput and latency between nodes at recorded separation | `TBR-RF-01`, `TBR-RF-03` |
| Receiver sensitivity with and without an in-band interferer | `TBR-RF-02` |
| Current draw at idle, at duty cycle, and at sustained maximum | `TBR-PWR-01` |
| Pack discharge to protection cutoff under representative load | `TBR-PWR-01` |
| Internal, component, cell and surface temperature under load | `TBR-THERM-01` |
| Real-time clock drift over a recorded interval and temperature range | `TBR-TIME-01` |
| Service and network plane resource use under load and at peak | `TBR-COMP-01` |

## The measurement rule

An unlabelled number in a text file is not evidence. Every measurement records
what was measured, the instrument, the date, the node, the image build, the
configuration, the ambient conditions, and who took it. See
`docs/evidence/README.md`.

Coexistence measurements in particular must be taken **in the assembled
enclosure**, at the antenna separations physically achievable there. A bench
measurement with the radios far apart does not answer `TBR-RF-02`.
