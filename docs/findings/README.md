# Remediation findings register

`register.yml` is the machine-readable execution register for
`REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md`. It carries every parent finding
and every decomposed child exactly once. The plan remains the source for scope
and closure gates; this register makes ownership, dependencies, state, and
evidence links mechanically checkable.

## Files

| File | Purpose |
| --- | --- |
| `register.yml` | Current state, ownership, dependencies, and evidence links. |
| `register.schema.json` | Declared Draft 2020-12 shape of the register. |
| `closure-packet.schema.json` | Shape required in a closed finding's Markdown frontmatter. |

## State changes

Use only the lifecycle vocabulary declared in the schema and the remediation
plan. Parent states in the plan's execution table and this register must agree.
Child states live here because the plan decomposes them without duplicating a
second child-state table.

An item may not enter `CLOSED` unless its evidence list contains the single
canonical `docs/evidence/findings/<ID>/closure.md` packet and that packet
validates. Other listed evidence files are allowed; each artifact named by the
packet must also appear in the register. A closed parent also requires every
registered child and every declared dependency to be closed. Every recorded
test must have exited zero. For high-impact findings, the packet operator must
match the registered owner, and the reviewer and approver must be named and
different from that operator.

## Validation

Run:

```sh
tools/validate-findings.py
```

`tools/validate-docs.sh` runs the same check. It rejects missing or duplicate
plan items, title/priority/state drift, unresolved dependencies, dependency
cycles, escaping or missing evidence paths, invalid closure frontmatter,
incorrect artifact hashes, and a high-impact closure reviewed by its own
operator.

The register is hand-maintained and reviewed. It is not generated because its
owners, dependencies, and user-gate dispositions are program judgements rather
than facts that can be derived safely from filenames.
