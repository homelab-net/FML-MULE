# Power and Bluetooth follow-up on node A

## Purpose and provenance

This follows the earlier infrastructure-WiFi trial and reduces uncertainty at
the Linux/radio boundary under TBR-LINUX-01. Native bench SSL startup also
informs TBR-HA-01. It changes no decision or selected field configuration.
The [metadata](2026-10-01-power-ble-followup-node-a.json) records the node,
software, instrument, operator and unrecorded conditions. The
[selected output](2026-10-01-power-ble-followup-node-a.txt) contains only
allowlisted diagnostic lines. Original and public section hashes are recorded;
node records, channel keys, identities and addresses are excluded.

## Observations

After the operator changed node A's power supply and it rebooted,
`vcgencmd get_throttled` reported `0x0`. The current boot still contains USB
descriptor/address errors `-32` and `-71`, ending in failure to enumerate the
attached radio. No serial device appeared. The supply rating was not recorded;
these observations do not establish the cause of the USB failure.

BlueZ pairing requested the operator-provided passkey and reported success.
The Meshtastic API read hardware `RAK4631`, firmware `2.7.15.567b8ea`, region
`US` and modem preset `LONG_FAST`. Its helper printed these fields but exceeded
the outer process limit during shutdown. A separate bounded GATT diagnostic
using upstream Meshtastic UUIDs and protobufs completed a configuration
request, received the matching completion identifier, and disconnected cleanly.
The same complete exchange passed a second time. This is BLE API evidence,
not LoRa delivery evidence or an integrated MULE gateway demonstration.

An earlier diagnostic stopped after 40 responses. The complete exchange
contains 50 node records plus configuration responses, so that response-count
limit could report a false failure. The corrected diagnostic uses a bounded
elapsed-time window and reports only response counts, never record contents.

The x86 bench also rebooted. Its existing startup path started the separate
native SSL container and port 8089 was listening afterward. A sampled socket
listing had no established EUD connection; the operator reported iTAK
disconnected. This is startup evidence, not a host-movement or recovery
qualification.
The temporary BATMAN trial was not recreated after these reboots.

The DNS startup journal shows the default resolver occupying port 53 and
rejecting a phone query as non-local. The configured AP/overlay resolver failed
to bind because the address was already in use. The bench subsequently stopped
responding at its known LAN addresses. A separate agent,
`/root/verify_pi_discovery`, independently found no alternative bench SSH address
in a timed LAN sweep. This does not identify the cause of that reachability
loss, establish its power state, or confirm execution of the proposed repair.

## Bench restoration and receiver inventory

After the operator restored bench access, the current-boot journal established
that it had suspended and resumed, rather than shut down. The default DNS
daemon remained enabled, proving the interrupted repair had not disabled it.
The completed repair disables that competing service and starts the existing
AP/overlay resolver with its existing settings. A new startup guard was
exercised against the occupied port and returned failure instead of announcing
success. The updated live script passes `bash -n`. Overlay A queries now return
the overlay address, AP queries return the AP address, and overlay AAAA queries
return NOERROR with no answer. This remains the existing single-bench DNS
deviation; it does not solve multi-MULE discovery.

The operator authorized preventing automatic sleep during testing. A persistent
sleep configuration disables suspend, hibernation, hybrid sleep and
suspend-then-hibernate. The four login1 capability queries returned `no` after
configuration, compared with `yes` for suspend/hibernate before it. The settings
carry the upstream documentation quote and default/omission explanation in
the live file. No sleep operation was invoked to test this policy. A whole-host
reboot with both repairs has not been exercised.

Node B then sent a new synthetic standard spot-map marker over Ethernet. The
bench SQL row exists and the EUD native SSL session is established; a fresh
phone UI confirmation was pending at collection. This path does not exercise
node A transit, the temporary WiFi overlay or LoRa.

The operator added an RTL-SDR to the bench. USB enumerates a NESDR SMArt v5
with vendor/product `0bda:2838`; the kernel attaches `dvb_usb_rtl28xxu`, reports
RTL2832 and R820T, and creates `swradio0`. This records an available test
instrument, not a selected MULE bearer or a receiver implementation. Tuning,
IQ capture, calibration and reception were not exercised. No frequency range,
sample-rate, sensitivity or signal-classification claim follows.

## Repetition and limits

Check current voltage flags and kernel USB messages after a supply change.
For BLE, discover the intended radio, pair with the confirmed passkey, request
configuration using upstream `ToRadio.want_config_id`, and require a matching
`FromRadio.config_complete_id` before disconnecting. Retain the bond and avoid
logging node records or channel configuration. Test RF delivery separately.

Neither trade closes on these observations. Antenna, ambient, supply and image
build details remain unrecorded; no range, throughput or endurance claim follows.
