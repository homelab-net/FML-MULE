# FML-ADR-048 option 2 on the bench: the TAK Meshtastic Gateway against a peer-mode WinTAK

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held.** A
time-boxed trial, run because FML-ADR-048 orders gateways upstream-first and
the proposed degraded-mode packet (`TBR-HA-01`, 2026-10-18) needs a
peer-ATAK-to-Meshtastic bridge on the partitioned side. The TAK Meshtastic
Gateway is exactly that bridge.

| Item | Value |
| --- | --- |
| Date | 2026-10-18, about 21:50 to 22:10 local |
| Taken by | Claude Code operating the bench at the Program Owner's direction |
| Software | TAK Meshtastic Gateway 1.1.0 from PyPI, in its own virtualenv on pi-mule-2 (Debian 13, Python 3.13, arm64) |
| Radio | the T1000-E |
| Client | WinTAK 5.8 in peer mode: server connection disabled, multicast SA and chat on |
| Far side | the RAK4631 on pi-mule-1, running `test/bench/fml-lora-gw.py` as a client of pi-mule-1's TAK Server |
| Hosts | pi-mule-2 under-voltage throughout (25 events in 6 minutes) |

## Findings

1. **It does not install as published on this platform.**
   - It pins `lxml==5.2.2`, which has no build for Python 3.13 on arm64. It was
     installed with its dependencies unpinned, and `lxml` 6.1.3 substituted.
   - `unishox2-py3` needs Python headers (`python3-dev`).
   - The `takproto` pull-request ref its README names no longer fetches. The
     released `takproto` 3.0.1 was used.
2. **Its `-t/--tx-interval` option crashes it.** argparse has no `type=int`, so
   any value given compares a float with a string (`TypeError`). The default
   works.
3. **It always transmits on the radio's primary channel.**
   - Every `sendData`/`sendText` uses the default channel index 0, and there is
     no option to change it.
   - On this bench index 0 is the public mesh, which bench traffic must never
     use. So for the trial the T1000-E's primary channel was set to the private
     `MULE-TEST` and its duplicate slot disabled. The originals were saved and
     restored afterwards; restore was checked by key fingerprint.
4. **It renames the radio after the TAK client, and that reboots the radio.**
   - The radio's long name became "`<callsign>` Mesh Node".
   - A Meshtastic owner change reboots the device: one USB re-enumeration each
     time, and restoring the original name caused exactly one more.
   - **It does not recover.** After the reboot it logged "Lost connection to the
     Meshtastic device, attempting to reconnect", failed with
     `FileNotFoundError`, and from then on treated the radio as disconnected. It
     forwarded **one** position per start and no more.
5. **What works.**
   - It takes the peer client's multicast SA, accepting only the configured
     client address and ignoring the same client's second interface.
   - It encodes the FML-ADR-070 `TAKPacket` with the client's **own uid** in
     `Contact.device_callsign`. That is the convention the bench gateway adopted
     the same day (PR #233). The far gateway accepted it and opened its proxy
     session under that real uid.

## What this means for the option-3 justification

Option 2 fits the partitioned side's job in design. But as published it:

- cannot be installed unattended on the target platform;
- would put traffic on whatever channel is primary;
- stops after its first position, because of the rename and reboot.

None of that is a protocol limit. All of it is fixable upstream: a channel
option, an opt-out from renaming, and reconnect after a USB reset. So the honest
record is "**not usable as published, fixable**", not "unsuitable".

## Not established

- DM behaviour through its socket.
- Chat in either direction.
- Its behaviour with iTAK.

All three were stopped by finding 4.

## Scrubbing

The client's uid and the radios' node ids are omitted, and so is the channel
key.
