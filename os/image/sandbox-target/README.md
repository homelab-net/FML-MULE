# Target package-manager sandbox

This mkosi sandbox supplies build-time APT configuration for the target image.
It is not copied into the target filesystem.

`etc/` mirrors the canonical package-manager configuration path that mkosi
mounts into its build sandbox.
