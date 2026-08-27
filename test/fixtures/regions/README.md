# Synthetic region fixtures

Region profiles with **invented numbers**, used only to exercise the
configuration generator and the flat-sat.

## Why these are not under `regions/`

`regions/` holds profiles a builder could operate under. Every value in every
one of them is `TBD`, because no channel plan has been selected and no module
has been qualified.

The generator cannot be tested against a profile that is entirely `TBD` — the
only path it would ever take is the refusal path. Testing the resolution and
validation paths needs a profile with real-looking numbers, and a real-looking
number in `regions/` is exactly the "plausible-looking figure that gets copied,
quoted, and eventually believed" that `AGENTS.md` forbids.

Keeping them here makes the distinction structural rather than a matter of
someone reading a header:

- Nothing under `test/fixtures/` is loadable by region identifier. The generator
  resolves a bare identifier under `regions/` only; a fixture must be passed as
  an explicit path.
- The identifier prefix `xx-` is reserved for fixtures and is not a valid
  economic area or country code.

## Contents

| Fixture | Purpose |
| --- | --- |
| `xx-testfixture/profile.yml` | Fully resolved. Exercises the success path. |
| `xx-testfixture/profile-out-of-band.yml` | Channel outside its own declared band. Must be rejected. |
| `xx-testfixture/profile-amateur-enabled.yml` | Amateur integration enabled. Must be rejected. |

## The rule these fixtures exist to test

**No value in these files describes any real regulatory allocation anywhere.**
They are chosen to be obviously synthetic. If any of them ever appears in a
`regions/` profile, in a configuration file, or in a document as though it were
a real limit, that is the failure this separation exists to prevent.
