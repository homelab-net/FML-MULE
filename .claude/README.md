# Claude Code session configuration

This directory configures Claude Code sessions opened on this repository. It
holds `settings.json` and nothing else. It changes no lint rule, no check and no
decision; it only makes sure a cloud session has the tools `tools/lint.sh` runs.

## Why it exists

`tools/lint.sh` skips every tool that is not installed and still exits zero
(`docs/dev-machine.md`). A Claude Code cloud session starts in a fresh container
without most of the toolchain, so without this hook its first lint run checks
almost nothing and looks green.

## What the hook does

`settings.json` registers one `SessionStart` command hook. In a cloud session it:

1. creates `.venv` with `python3.13` if it does not exist. The container's
   default `python3` is 3.11, and the pinned `ansible-core` in
   `tools/requirements-dev.txt` publishes no build for it. `tools/install-deps.sh`
   reuses an existing `.venv`, so creating it first selects the interpreter;
2. runs `tools/install-deps.sh`, the authoritative toolchain list
   (`FML-ADR-058`), which installs only what is missing;
3. runs `tools/install-deps.sh --check`, which exits non-zero if anything is
   still missing.

All output goes to standard error, because standard output of a `SessionStart`
hook is added to the session's context.

## The settings, against the Claude Code documentation

JSON carries no comments, so the documentation each setting rests on is quoted
here.

- **When it runs.** "Runs when Claude Code starts a new session or resumes an
  existing session." (`code.claude.com/docs/en/hooks`). The install is
  idempotent, so a resume costs one `--check`.
- **The cloud-only guard.** "hooks run in both local and cloud sessions. To skip
  local execution, exit early unless the `CLAUDE_CODE_REMOTE` environment
  variable is `true`" and "the session VM's environment carries that variable as
  `true`, it's never `true` locally" (`code.claude.com/docs/en/cloud-environments`).
  Omit the guard and the hook installs packages on a contributor's own machine
  every time a session opens there.
- **Standard output.** "`SessionStart` ... Claude Code adds plain-text stdout as
  context that Claude can see and act on." (`code.claude.com/docs/en/hooks`).
  Omit the redirection and several hundred lines of installer output enter every
  session's context.
- **A failed install.** For `SessionStart` a failing hook "Shows stderr to user
  only" and "the session ... proceeds" (`code.claude.com/docs/en/hooks`). The
  session is not blocked; the error is visible, and `tools/lint.sh` will then
  list what it skipped.
- **`timeout: 900`.** "Claude Code cancels a `command` hook after 600 seconds
  unless you set `timeout`, in seconds, on the hook entry."
  (`code.claude.com/docs/en/cloud-environments`). A cold install builds the
  Python toolchain and downloads three pinned binaries; 900 leaves headroom over
  the default rather than letting a slow mirror cancel it half-done.
- **Synchronous, not `async`.** The hook is deliberately not asynchronous, so
  the toolchain exists before the session runs its first command. Asynchronous
  hooks have no enforced timeout and race the session.

## What it does not do

It installs the tools that check the repository. It installs nothing the
network plane needs, builds no image, and verifies no hardware. A green
`tools/lint.sh` after it still means only that the files parse and the documents
agree (`test/README.md`).
