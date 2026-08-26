# Example mission packages

**Every identity in every file in this directory is fake, and deliberately
obviously so.**

No real mission configuration, deployment location, member identity, callsign,
credential, or operational capture is ever committed to this repository. See
`SECURITY.md`. A real package goes in `mission/local/`, which is git-ignored.

Every example file carries a header comment saying its identities are fake.
That comment is required, not decorative: it is what stops a file being copied
out of here and mistaken for a real configuration, and what stops a reviewer
assuming a plausible-looking name is a placeholder.

## Valid examples

Packages that the schema accepts. Used in CI to confirm the schema does not
reject legitimate configurations.

| File | Demonstrates |
| --- | --- |
| `valid-minimal.json` | The smallest package the schema accepts. |
| `valid-full.json` | Every field populated, including the optional ones. |

## Invalid examples

Packages the validator **must reject**. Each names, in its own header, exactly
which rule it violates.

| File | Must be rejected because | Caught by |
| --- | --- | --- |
| `invalid-missing-required.json` | Omits a required field. | Schema |
| `invalid-unknown-field.json` | Contains a field the schema does not define. | Schema |
| `invalid-bad-profile.json` | Uses a mission profile outside the permitted set. | Schema |
| `invalid-real-flag.json` | Sets `example: false`, marking it a real configuration. | Repository rule |

The last one is deliberately not a schema violation. A real package legitimately
sets `example: false`, and the schema describes packages generally, not only
committed ones. What it violates is the **publication rule**: nothing under
`mission/examples/` may be a real configuration. That is checked by
`tools/validate-mission.py`, which applies the schema and then the repository
rules on top of it.

Keeping the two layers distinct matters. A schema that forbade real packages
outright would be a schema that could not validate the packages the system
actually runs.

**Invalid examples matter as much as valid ones.** A schema that accepts
everything passes every valid example and catches nothing. Naming the violated
rule in each file means that a change which stops catching it shows up as a
regression rather than as a test that quietly started passing.

## Adding an example

- Fake identities only, and obviously fake: `example-`, `fake-`, `training-`.
- The header comment stating that identities are fake is mandatory.
- Documentation-range addresses only, where an address is needed. Never a real
  or plausible allocation.
- No passphrase, key, certificate or token, in any form, including a
  placeholder that looks like one. Secret scanning does not distinguish a real
  credential from a convincing fake, and neither does a reader in a hurry.
- An invalid example states which rule it violates, in its header.
