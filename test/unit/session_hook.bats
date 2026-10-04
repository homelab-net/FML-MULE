#!/usr/bin/env bats
# Tests for the Claude Code SessionStart hook in .claude/settings.json.
#
# The hook is one shell command stored in JSON, so it has no file of its own
# for shellcheck to read and nothing else exercises it. These tests extract the
# command from the settings file -- the text that actually runs -- and execute
# it against a stub tools/install-deps.sh, so a quoting, guard or
# exit-status regression in the JSON fails here rather than silently leaving a
# cloud session without its lint toolchain.

setup() {
  REPO="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK_CMD="$(python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
print(d["hooks"]["SessionStart"][0]["hooks"][0]["command"])
' "$REPO/.claude/settings.json")"
  export HOOK_CMD

  # A project directory holding only what the hook touches.
  PROJ="$BATS_TEST_TMPDIR/proj"
  LOG="$BATS_TEST_TMPDIR/calls"
  mkdir -p "$PROJ/tools" "$PROJ/.venv/bin" "$BATS_TEST_TMPDIR/bin"
  : >"$LOG"
  # Stub installer: records each call; --check fails when CHECK_FAILS is set.
  cat >"$PROJ/tools/install-deps.sh" <<EOF
#!/bin/sh
echo "install-deps \$*" >>"$LOG"
echo "installer output on stdout"
if [ "\${1:-}" = --check ] && [ -n "\${CHECK_FAILS:-}" ]; then exit 1; fi
exit 0
EOF
  chmod +x "$PROJ/tools/install-deps.sh"
  printf '#!/bin/sh\nexit 0\n' >"$PROJ/.venv/bin/python"
  chmod +x "$PROJ/.venv/bin/python"
  # Stub python3.13 on PATH: records that the venv bootstrap ran.
  cat >"$BATS_TEST_TMPDIR/bin/python3.13" <<EOF
#!/bin/sh
echo "python3.13 \$*" >>"$LOG"
EOF
  chmod +x "$BATS_TEST_TMPDIR/bin/python3.13"
  export PROJ LOG
}

run_hook() {
  run env PATH="$BATS_TEST_TMPDIR/bin:$PATH" CLAUDE_PROJECT_DIR="$PROJ" \
    "$@" sh -c "$HOOK_CMD"
}

@test "outside a cloud session the hook installs nothing" {
  run_hook CLAUDE_CODE_REMOTE=
  [ "$status" -eq 0 ]
  [ ! -s "$LOG" ]
}

@test "in a cloud session it installs, then checks, and succeeds" {
  run_hook CLAUDE_CODE_REMOTE=true
  [ "$status" -eq 0 ]
  [ "$(sed -n 1p "$LOG")" = "install-deps " ]
  [ "$(sed -n 2p "$LOG")" = "install-deps --check" ]
}

@test "it fails when the post-install check still finds something missing" {
  run_hook CLAUDE_CODE_REMOTE=true CHECK_FAILS=1
  [ "$status" -ne 0 ]
}

@test "it creates the virtualenv with python3.13 when none exists" {
  rm "$PROJ/.venv/bin/python"
  run_hook CLAUDE_CODE_REMOTE=true
  grep -q '^python3.13 -m venv .venv$' "$LOG"
}

@test "it writes nothing to stdout, which would enter the session context" {
  # The stub installer prints to stdout; the hook has to redirect it.
  stdout="$(env PATH="$BATS_TEST_TMPDIR/bin:$PATH" CLAUDE_PROJECT_DIR="$PROJ" \
    CLAUDE_CODE_REMOTE=true sh -c "$HOOK_CMD" 2>/dev/null)"
  [ -z "$stdout" ]
}
