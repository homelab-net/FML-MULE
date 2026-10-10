# Pi 4B partition layout

systemd-repart definitions for the `pi4b-arm64` profile (`FML-ADR-088`): a
512M FAT partition holding `/boot/firmware` for the Pi's EEPROM bootloader,
then an ext4 root labelled `mule-root`, which the kernel command line names.
