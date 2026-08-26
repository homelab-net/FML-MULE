# Test

## What CI actually verifies

**CI has no radios, no battery, and no enclosure.**

A green pipeline means:

- The files parse.
- The linters are satisfied.
- The fakes pass.
- The documents are internally consistent: identifiers are unique, cited trades
  exist, `STATUS.md` is not stale, and no image reference uses a mutable tag.

**It says nothing about whether the system works.** Not whether a radio
enumerates, whether a mesh forms, whether the node survives a day on battery,
whether it stays cool in an enclosure, or whether an operator can use it.

This is worth stating plainly because a green badge on a repository is read as
evidence of function, and here it is not. That is also why this repository
carries no badges. See `AGENTS.md`.

Hardware-in-the-loop verification belongs to the **qualification stages**, and
to nothing else. The first hardware gate that exists today is the promotion
gate in `os/release/README.md`.

## Layout

| Directory | Contents |
| --- | --- |
| `unit/` | Unit tests. `bats` for shell, `pytest` for Python. Run in CI. |
| `fixtures/` | Recorded output captured from real hardware, replayed against fakes. |
| `stages/` | Qualification stage definitions. One directory per stage. |
| `bench/` | Bench procedures and instrumentation notes. |
| `results/` | Measured data from stage execution. Structured, currently empty. |

Trade evidence is **not** here. It lives in `docs/evidence/<TRADE-ID>/`. A
trade closes a question during design; a stage validates a requirement against
a build. Where the same measurement serves both, one cites the other rather
than being copied.

## Running the tests

```sh
tools/lint.sh          # linters and repository checks
pytest                 # Python unit tests
bats test/unit         # shell unit tests
```

`tools/lint.sh` skips any linter that is not installed and says which. CI
installs all of them.

## Fakes and fixtures

Two or three physical nodes will exist for a long time, and **contributors will
have none**. The hardware abstraction rule in `AGENTS.md` and
`services/README.md` follows from that:

- Every function that reads or controls radio, power, thermal, or time state
  **shall** sit behind a narrow interface with a fake or recorded-fixture
  implementation.
- Service-plane and status code **shall** run and be testable on an ordinary
  laptop against fakes, with no radios present.

**Fixtures** in `test/fixtures/` are recorded output captured from real
hardware: `dmesg`, `iw`, `batctl`, power and thermal readings. Each is stored
with the **node identifier, capture date, and image build** recorded alongside
it. A fixture with no provenance is not a fixture; it is a file someone
remembers making.

Scrub before committing. A captured log can contain a credential, an
identifier, or a location. See `SECURITY.md`.

**A test that passes against a fake proves the code handles that recorded
input.** It does not prove the hardware behaves that way, and it never proves a
physical property. Evidence produced against a fake never supports a claim
about physical behaviour.

## What is tested today

| Subject | How |
| --- | --- |
| Documentation consistency | `tools/validate-docs.sh` |
| `STATUS.md` freshness | `tools/gen-status.sh --check` |
| Requirement traceability | `tools/gen-traceability.sh --check` |
| Mission package schema and repository rules | `tools/validate-mission.py`, and `test/unit/` |
| Shell tooling | `bats`, in `test/unit/` |
| Ansible playbook syntax | `ansible-playbook --check` |
| Secrets | `gitleaks` |

There is no application code to test, because none has been written. See
`AGENTS.md`: build system before application code, and the four placeholder
services must not be implemented.
