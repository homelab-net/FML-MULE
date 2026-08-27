# Results

Measured data from qualification stage execution.

**Empty. No stage has been defined and no stage has been run.**

The directory exists, structured and documented, so that the first result has
somewhere to go that already has rules. A results directory created on the day
of the first measurement acquires its conventions from whatever that
measurement happened to look like.

## Layout

```text
test/results/
  README.md
  <STAGE-ID>/
    YYYY-MM-DD-<node>-<run>/
      RUN.md                  what was run, on what, by whom, and the verdict
      <raw output files>
```

One directory per stage, one per run beneath it. Runs are never overwritten,
including failed ones. **A failed run is a result**, and deleting it removes
the evidence of what changed between then and the run that passed.

## What `RUN.md` records

| Field | Notes |
| --- | --- |
| Stage | The stage identifier from `test/stages/`. |
| Date and operator | Who ran it. |
| Configuration under test | Hardware block, compatibility set version, region profile, mission profile. |
| Node identifiers | Every node involved. |
| Instrumentation | Instrument, model, calibration where it matters. |
| Conditions | Ambient, antenna arrangement, what else was transmitting. |
| Deviations | Anything done differently from the stage procedure, and why. |
| Verdict | Pass or fail, per step, against the criteria written before the run. |
| Raw output | The files in this directory, listed and described. |

The **deviations** field is the one that gets left blank and is the one that
explains an anomalous result six months later.

## Results and evidence

`test/results/` holds stage results: a build validated against a requirement.
`docs/evidence/<TRADE-ID>/` holds trade evidence: a design question answered.

They are separate because they answer different questions and are consulted at
different times. Where the same measurement serves both, one cites the other
rather than being copied; a measurement that exists in two places will be
corrected in one.

## Publication rule

Results are captured from real equipment, so they are exactly where a location,
a callsign, or a credential leaks in. Scrub before committing, record what was
scrubbed, and strip metadata from photographs. See `SECURITY.md`.
