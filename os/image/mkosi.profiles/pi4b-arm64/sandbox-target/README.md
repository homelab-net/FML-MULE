# Pi 4B target sandbox

Package-manager configuration mkosi uses when it installs the `pi4b-arm64`
profile's packages (`FML-ADR-088`). Nothing here is copied into the image.

`etc/` mirrors the package-manager configuration path that mkosi mounts into
its build sandbox; `etc/apt/` explains the one sources file.
