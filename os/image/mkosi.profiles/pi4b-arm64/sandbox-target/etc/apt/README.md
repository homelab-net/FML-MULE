# Pi 4B target sandbox APT configuration

`sources.list.d/` holds the deb822 source definition for the dated Debian main
and security archives, with the `non-free-firmware` component `FML-ADR-088`
enables for this profile so `raspi-firmware` resolves. The base image's own
sandbox stays `main` only.

`apt.conf.d/` holds one setting, `50-keep-tools-tree-lists`, which stops
`apt-get update` for this arm64 profile from erasing the amd64 package lists
the tools tree synced into the same package cache. Without it the
network-isolated build cannot rebuild the tools tree. The file explains the
mechanism and quotes `apt-get(8)`. It has no README of its own because APT
reads every file in that directory.
