# Tools

Small, dependency-free scripts for documentation validation, identifier
allocation, and generation.

Everything here is POSIX `sh` except `validate-mission.py`, which is Python
because JSON Schema validation in shell would be worse for everyone. No script
requires anything beyond coreutils, `grep`, `sed`, `awk` and `git`.

## Scripts

| Script | Purpose |
| --- | --- |
| `lint.sh` | Run every configured linter. Skips what is not installed. |
| `validate-docs.sh` | Validate the ADR and trade registers, the fork ledger, and image references. |
| `new-adr.sh` | Allocate the next unused ADR identifier and create the file. |
| `new-trade.sh` | Allocate the next unused trade identifier and create the file. |
| `gen-status.sh` | Generate `STATUS.md`. Never hand-edit that file. |
| `gen-traceability.sh` | Generate the requirement traceability matrix. |
| `validate-mission.py` | Validate mission packages against the schema and the repository rules. |

## Before opening a pull request

```sh
tools/lint.sh
```

That runs the linters and the repository checks together. Install what it
reports as skipped if you want the same coverage CI has.

## `validate-docs.sh`

```sh
tools/validate-docs.sh
```

Checks:

1. Every ADR has the eight required sections.
2. Every ADR has its frontmatter fields, with a status from the vocabulary.
3. No ADR identifier is duplicated, and each matches its filename.
4. Every trade an ADR cites exists in `docs/trades/`.
5. Every trade has the six required sections and its frontmatter fields.
6. No trade identifier is duplicated, and each matches its filename.
7. Every trade's evidence directory exists, and a `CLOSED` trade's directory
   holds actual evidence. **A trade does not close on wording alone.**
8. **Every patch file in `os/kernel/patches/` has an entry in `docs/forks/`.**
   Every carried patch is a liability with a name attached, and the failure
   this catches is otherwise silent: a patch lands, works, and is forgotten
   until the day it does not apply.
9. **No OCI image reference anywhere uses a mutable tag.** Matched on reference
   shape rather than on a keyword, so a tag cannot slip in through a syntax the
   check did not anticipate. Documentation counter-examples under
   `example.org` and `example.invalid` are exempt, narrowly and deliberately:
   those hostnames cannot resolve to a real registry.

## `new-adr.sh` and `new-trade.sh`

```sh
tools/new-adr.sh "Short decision title in sentence case"
tools/new-trade.sh RF "Short question in sentence case"
```

**Identifiers are permanent and never reused.** These scripts take the highest
identifier ever recorded, from the working tree **and from the full git
history**, and add one. They do not count files and they do not fill gaps: a
gap in the numbering is information, and filling it destroys that information.

`new-trade.sh` also creates the trade's evidence directory, so that the closure
gate is written before evidence is gathered and the result cannot be graded
against a standard invented after seeing it.

One limitation, stated rather than hidden: the history check reads committed
files. An identifier allocated and then deleted **before being committed** can
be reissued. In the normal workflow, where a new record is committed on the
branch that introduces it, this does not arise.

## `gen-status.sh`

```sh
tools/gen-status.sh            # write STATUS.md
tools/gen-status.sh --check    # fail if the committed copy is stale
```

**`STATUS.md` is generated and never hand-edited.** A stale status page is how
a repository signals abandonment, so CI runs `--check` and fails the build if
the committed copy differs from freshly generated output.

Reads ADR and trade frontmatter and the roles table in `MAINTAINERS.md`, and
reports decisions by status, open trades with owners, the critical path, and
vacant maintainer roles. A critical-path trade with owner `TBD` is reported as
a program risk, because it is one.

## `gen-traceability.sh`

```sh
tools/gen-traceability.sh            # write docs/verification/traceability.md
tools/gen-traceability.sh --check    # fail on any untraced binding requirement
```

**Traceability is a build artifact, not a document someone maintains.**

Reads requirement frontmatter from documents under `docs/` and produces the
matrix. `--check` **fails the build** when any `shall` requirement lacks either
an architecture allocation or a validating stage.

The requirement set is not yet populated, because the CONOPS has not been
transcribed. The generator and its check are wired up regardless, so that the
first requirement to land arrives into working machinery. Hand-extracted
traceability has already failed once in this program's history.

## `validate-mission.py`

```sh
tools/validate-mission.py                       # every example
tools/validate-mission.py path/to/package.json  # a specific package
```

Two layers, deliberately kept apart:

- **Schema**, from `mission/schema/`. Describes packages generally, including
  real ones.
- **Repository rules.** Constraints on packages *committed here*, chiefly the
  publication rule: nothing under `mission/examples/` may be a real
  configuration.

A schema that forbade real packages outright could not validate the packages
the system actually runs, which is why the two are separate.

Files named `valid-*.json` are expected to pass and `invalid-*.json` to fail,
and that expectation is itself checked. A counter-example that stops being
caught is a regression, not a test that quietly started passing.

Requires `jsonschema`. Without it, the schema layer is skipped and says so.

## Writing a new tool

- POSIX `sh` where possible, `bash` where not.
- Open with `set -eu` and a usage comment.
- `shellcheck` clean, `shfmt -i 2 -ci` formatted.
- No dependency a contributor would have to install to run the repository's
  basic checks.
- A `--check` mode for anything that generates a file, so CI can verify the
  committed copy without writing to the tree.
