# Pi 4B image profile

The `pi4b-arm64` profile of the development image (`FML-ADR-088`): the same
Debian snapshot, mkosi builder and provenance rules as the x86-64 image, built
for the Raspberry Pi 4B. Select it with `--profile pi4b-arm64`; without that
the base `os/image/mkosi.conf` builds the x86-64 image unchanged.

| File | What it does |
| --- | --- |
| `mkosi.conf` | Overrides the architecture, image identity and seed; installs no bootloader (`Bootable=no`); empties the base console and sandbox settings. |
| `sandbox-target/` | APT sources with `non-free-firmware`, for `raspi-firmware`. |
| `mkosi.repart/` | A 512M FAT partition for `/boot/firmware`, then an ext4 root labelled `mule-root`. |
| `mkosi.postinst.chroot` | Writes `/etc/default/raspi-firmware` with explicit values and reruns the firmware hook, so nothing is derived from the build host. |
| `build-inputs.yml` | What this profile changes from `os/image/build-inputs.yml`, checked by `tools/validate-image.py`. |

The package lists are in `os/image/manifest/pi4b-arm64/`. A build here is not
acceptance: `FML-ADR-088` requires a boot on a physical Pi 4B (bench card BC-1).
