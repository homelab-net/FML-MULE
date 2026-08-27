# Common hardware material

Material that is **genuinely block-independent**: identical across any
plausible hardware block.

**Currently empty.** With no qualified block, and only one placeholder
candidate, nothing has been demonstrated to be block-independent. Something is
common because it has been shown to be, across at least two blocks, not because
it seems like it ought to be.

## Resist this directory

The pressure to use `common/` is strongest exactly when it is least justified:
early, with one candidate block, when everything looks universal because there
is nothing to compare it against.

Everything placed here that turns out to be block-specific has to be untangled
later, usually while adding the second block, usually under time pressure
because the first block's parts have gone end-of-life. **When in doubt, it
belongs to the block.**

## What could legitimately live here

- Conventions shared across blocks: labelling schemes, connector pinout
  conventions, wire colour codes.
- Shared documentation on a practice rather than a part: how to strain-relieve
  a harness, how to record an antenna measurement.
- Test and acceptance procedure fragments that genuinely do not depend on the
  configuration.

## What does not

- Any part number. Parts belong to a block's `bom/`.
- Any mechanical drawing. Enclosures differ between blocks by definition.
- Any RF measurement. Measurements are made on a configuration.
- Anything with a `TBD` that a block-level trade will resolve.
