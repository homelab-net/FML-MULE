# Region template

Copy this directory to `regions/<region-id>/` and fill it in. Use a short,
stable identifier: economic area or country code, hyphen, band common name.
For example `us-915`, `eu-868`, `au-915`.

Replace this file with a README describing the region. Keep the structure
below; configuration generation expects `profile.yml`, and readers expect the
rest.

## What to write in the region README

1. **Which administration and which regulator.** Name them.
2. **Which band, and the rule that permits it.** Cite the regulation with its
   section number. A citation a reader can look up is the difference between a
   profile and a rumour.
3. **What you have verified and what you have not.** Be explicit. A profile
   written by someone who cannot operate in the region should say so in its
   first paragraph.
4. **What is `TBD`**, and which trade will supply it.
5. **Known constraints that have design consequences**, not only configuration
   consequences. A duty-cycle limit is the obvious example: it may mean the
   bearer cannot support the same operational concept, which is a bigger
   statement than a configuration value.

## Rules

- **Cite the rule, not a summary of it.** Not a forum post, not a vendor page,
  not another project's configuration.
- **Archive the regulatory document** into `docs/evidence/` with its URL and
  retrieval date. Regulators reorganise their sites and renumber their rules.
- **`TBD` for anything unverified.** Never a plausible-looking power limit.
- **Nothing here authorises operation.** A channel plan describes an
  allocation; it does not grant permission to transmit.
- **Nothing here makes a device compliant.** See `REGULATORY.md`.

## Files

| File | Purpose |
| --- | --- |
| `README.md` | This file, replaced with the region description. |
| `profile.yml` | Machine-readable parameters consumed by configuration generation. |
| `channel-plan.md` | Channel plan, each entry traced to the rule it derives from. |
| `modules.md` | Permitted radio modules with approval identifiers. |
| `constraints.md` | Duty cycle, power, antenna gain, and other binding limits. |

## Checklist before opening a pull request

- [ ] Region identifier is short, stable, and follows the existing pattern.
- [ ] `profile.yml` validates and every unknown is `TBD`, not a guess.
- [ ] Every parameter cites the rule it comes from.
- [ ] Regulatory documents archived under `docs/evidence/` with retrieval date.
- [ ] `REGULATORY.md` gains a country note pointing at this profile.
- [ ] `regions/README.md` regions table gains a row.
- [ ] You have stated whether you can operate and test in this region.
