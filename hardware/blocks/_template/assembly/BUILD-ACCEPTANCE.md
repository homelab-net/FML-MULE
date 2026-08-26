# Build acceptance

**A build guide is not complete until someone other than its author has
followed it successfully.**

This checklist is worked through by a **first-time builder**, following the
block's build guide and nothing else. It is not a test of the builder. It is a
test of the documentation, and every point of confusion is a defect in the
documentation.

**Status: `TBD`. No block exists to build.** This template is here so that it
exists before the first build guide does, rather than being written afterwards
by someone who already knows how the node goes together.

## Rules for the builder

1. **Use only the repository.** No asking the author, no side channel, no
   private notes. If you need something that is not written down, that is the
   result.
2. **Record where you got stuck**, in the spaces below, as it happens. Not
   afterwards from memory.
3. **Do not fix the documentation as you go.** Record the problem and continue.
   Fixing it as you go destroys the evidence of how bad it was.
4. **Stopping is a valid outcome.** If you cannot proceed, record where and
   why. A build guide that stops a competent builder at step four is more
   useful to know about than one nobody attempted.

## Rules for the author

1. **Do not help during the build.** Answering a question destroys the data
   point.
2. **Do not defend the documentation** when you read the results.
3. **Every recorded point of confusion becomes an issue.** Not a note, not a
   conversation: an issue in the tracker, where it will be fixed.

## Record

| Field | Entry |
| --- | --- |
| Block | `TBD` |
| Build guide revision | `TBD` |
| Builder | |
| Prior experience with this project | |
| Date started | |
| Date finished, or stopped | |
| Total time | |

## Before starting

- [ ] The tools list was complete. I had everything before I started.
  - Anything missing:
- [ ] The consumables list was complete.
  - Anything missing:
- [ ] I could source every part on the bill of material.
  - Anything unobtainable, back-ordered, or ambiguous:
- [ ] The assumed skills were stated, and I have them.
  - Anything assumed that was not stated:
- [ ] I read `SAFETY.md` before starting.

## During the build

For each step where you paused, guessed, backtracked, or looked something up
outside the repository, record it. There is no such thing as too small.

| Step | What was unclear | What I did | How long it cost |
| --- | --- | --- | --- |
| | | | |
| | | | |
| | | | |

Add rows freely. A long table is a useful result.

- [ ] Every step's "done correctly" description matched what I actually saw.
  - Where it did not:
- [ ] Photographs matched the parts I had.
  - Where they did not:
- [ ] I never had to infer the orientation of a component.
  - Where I did:
- [ ] Cable routing and strain relief were specified, not left to judgement.
  - Where they were not:
- [ ] Safety warnings appeared at the step they applied to.

## First power-on

- [ ] The guide told me to verify polarity with a meter before applying power.
- [ ] The expected first-boot behaviour was described, so I could tell success
      from failure.
  - What I actually saw:
- [ ] The node reached the state the guide said it would.

## Acceptance

- [ ] I completed the block's acceptance procedure in `../acceptance/`.
  - Steps that failed:
- [ ] The node is a working member of the block.

## Outcome

- [ ] **Completed.** I built a working node from the repository alone.
- [ ] **Completed with difficulty.** I got there; the table above says at what
      cost.
- [ ] **Stopped.** I could not proceed.
  - Where:
  - Why:

## Builder's summary

In your own words: what would have made this easier? What did you expect to
find and not find?

## Author's follow-up

- Issues opened from this build:
- Build guide revision that addresses them:
- Next builder scheduled:

A build guide passes acceptance when a first-time builder completes it and the
table of confusions is short enough that the author is not embarrassed by it.
