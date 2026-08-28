#!/bin/sh
# Require full statement coverage of the production package.
#
# Usage: tools/coverage-check.sh
#
# WHY THIS IS 100% AND NOT A PERCENTAGE SOMEBODY LIKED
#
# An uncovered statement in `mule/` is one of two things, and both are defects:
#
#   - a decision no test exercises, which is a decision nobody has checked;
#   - a line that cannot be reached, which is dead code.
#
# This repository has shipped the second kind twice. `validate()` compared a
# resolved EIRP against the profile field it had just been copied from, and read
# as a regulatory control while being unreachable. `mule/sysfs.py` guarded
# `Path.glob` with `except OSError`, which does not raise for a missing
# directory. Both looked like safety nets. Coverage is what found the second.
#
# A threshold below 100% would have hidden both, because both were single lines
# in otherwise well-covered files.
#
# `mule/` is small and is decision logic with one reader in it. If holding it at
# 100% ever requires a contrived test, that is a signal the code is wrong rather
# than the rule: either the line is unreachable and should go, or the decision
# deserves a real test. A line that genuinely cannot be exercised carries an
# explicit `# pragma: no cover` with a reason, which is a visible decision
# rather than a silent gap.
#
# This deliberately does NOT cover `tools/` or `test/`. Repository tooling has
# error paths that are tedious to reach and cheap to be wrong about; the
# production package does not.

set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

if ! python3 -c "import coverage" 2>/dev/null; then
  printf 'coverage is not installed; skipping.\n'
  exit 0
fi

python3 -m coverage run --source=mule -m pytest -q >/dev/null 2>&1 || {
  printf 'FAIL: the test suite does not pass, so coverage means nothing.\n' >&2
  exit 1
}

# --fail-under=100 exits non-zero below the threshold. Report first so a
# failure names the lines rather than only the number.
python3 -m coverage report -m --fail-under=100 || {
  printf '\n' >&2
  printf 'FAIL: mule/ is not fully covered.\n' >&2
  printf 'An uncovered line is a decision nobody tested, or dead code.\n' >&2
  printf 'See the reasoning at the top of tools/coverage-check.sh.\n' >&2
  rm -f .coverage
  exit 1
}

rm -f .coverage
