# Fixtures

Recorded output captured from real hardware, replayed so that code can be
tested without that hardware.

**Empty. No fixture has been captured, because no node exists.**

## Why fixtures matter here more than usual

Two or three physical nodes will exist for a long time, and **contributors will
have none**. A change that can only be exercised by the person holding the
hardware can only be reviewed by that person.

Fixtures are how someone with hardware makes their observations usable by
everyone else. Capturing them is one of the most valuable things a person with
a node can do for this program, and it can be done long before anything is
built on top of them.

## What a fixture records

Every fixture is stored with its provenance. A fixture with no provenance is
not a fixture; it is a file someone remembers making.

| Field | Why |
| --- | --- |
| Node identifier | Behaviour differs between nodes, even within a block. |
| Capture date | So a fixture can be recognised as stale. |
| Image build | The compatibility set version. Radio behaviour is coupled to it. |
| Hardware block | Fixtures are not portable between blocks. |
| Region profile | Radio output depends on it. |
| Command or interface captured | So it can be recaptured. |
| Conditions | Ambient, antenna, separation, what else was transmitting. |

Store provenance in a `.SOURCE.md` beside the fixture, or as a header comment
where the format permits one without breaking a parser.

## Naming

`YYYY-MM-DD-<node>-<what>.<ext>`

## Expected fixture kinds

- `dmesg` and driver output during radio bring-up.
- `iw` interface and station output.
- `batctl` originator tables, neighbour lists, and metric output. Whether
  BATMAN-V obtains a throughput estimate from the HaLow driver is `UNVERIFIED`
  and is part of `TBR-LINUX-01`; a fixture is how that becomes checkable.
- Power readings at idle and under load.
- Thermal sensor output over a run.
- Real-time clock behaviour across a power cycle, including the dead-backup-cell
  case that `FML-ADR-042` requires a node to report.

## Scrub before committing

A captured log can contain a credential, an identifier, a callsign, or a
location. The publication rule applies without exception; see `SECURITY.md`.

Record what you scrubbed. A log with an obvious redaction is honest; a log
silently trimmed is not reviewable.

## What a fixture proves

**A test passing against a fixture proves the code handles that recorded
input.** It does not prove the hardware behaves that way in general, and it
never proves a physical property. Evidence produced against a fake or a fixture
never supports a claim about physical behaviour. See `docs/evidence/README.md`.
