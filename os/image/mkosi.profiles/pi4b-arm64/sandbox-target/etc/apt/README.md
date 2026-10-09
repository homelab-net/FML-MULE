# Pi 4B target sandbox APT configuration

`sources.list.d/` holds the deb822 source definition for the dated Debian main
and security archives, with the `non-free-firmware` component `FML-ADR-088`
enables for this profile so `raspi-firmware` resolves. The base image's own
sandbox stays `main` only.
