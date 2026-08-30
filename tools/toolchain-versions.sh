# shellcheck shell=sh
#
# SC2034, "appears unused", is disabled for this file alone and deliberately.
# Defining variables for a sourcing script is the entire purpose of the file,
# so every assignment in it is unused by definition when it is read on its own.
# The rule still applies everywhere else. Scoped here rather than in
# .shellcheckrc, where it would stop catching real dead assignments in the
# scripts that do the work.
# shellcheck disable=SC2034
# Pinned versions of the tools that are not installed from apt or from the
# Python lock file. Sourced, never executed.
#
# WHY THIS IS ITS OWN FILE. tools/install-deps.sh installs these and
# tools/check-toolchain-arm64.sh verifies them for a second architecture. A
# version recorded in two places is a version that will be updated in one, so
# it is recorded here once and read by both.
#
# The Python toolchain is NOT here: it is pinned in tools/requirements-dev.txt
# (FML-ADR-058), which is generated and much longer.
#
# To change a version, change it here and update BOTH digests beside it, by
# downloading the published artifacts and recording what they hash to. Never
# by hand, and never one architecture at a time: an unverified binary from the
# network is the supply-chain problem SECURITY.md declines to accept.

# shfmt ships no apt package at the version CI uses, so it is fetched from its
# release page. The version is pinned and the download is checksummed: an
# unverified binary from the network is exactly the supply-chain problem
# SECURITY.md declines to accept. Both digests were recorded by downloading
# the published artifacts; update them together with the version.
SHFMT_VERSION=3.10.0
SHFMT_SHA256_amd64=1f57a384d59542f8fac5f503da1f3ea44242f46dff969569e80b524d64b71dbc
SHFMT_SHA256_arm64=9d23013d56640e228732fd2a04a9ede0ab46bc2d764bf22a4a35fb1b14d707a8

# gitleaks, for the same reason and from the same kind of source. It is NOT
# taken from apt: Debian's build answers "version is set by build process" when
# asked, so a contributor cannot tell which scanner ran, and the version
# differs between Debian and Ubuntu anyway. A secret scanner whose version is
# unknown is the wrong tool to be casual about. Digests recorded from the
# published archives.
GITLEAKS_VERSION=8.30.1
GITLEAKS_SHA256_amd64=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
GITLEAKS_SHA256_arm64=e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080

# markdownlint-cli2. npm installs the newest release unless told otherwise, so
# an unpinned install here is the same drift the Python lock exists to prevent:
# a linter that adds a rule fails a tree nobody changed.
MDLINT_VERSION=0.23.2
