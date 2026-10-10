# Bench card: AWUS036ACM one-hop 802.11s and batman-adv on the two Pi 4Bs

## Trade and authority

- **Trade:** `TBR-RF-01`, "Can high-rate Wi-Fi operate reliably as a second
  802.11s/batman interface?". This card is the single-step case under that
  question, not its closure evidence.
- **Roadmap:** `docs/ROADMAP-DEV.md` item 1.7, which records that no radio in
  the lab advertises `mesh point`, "so 802.11s on real RF has no hardware to run
  on yet and the simulated association result is the ceiling until an adapter
  arrives". On 2026-10-10 the Program Owner reported buying two ALFA AWUS036ACM
  adapters.
- **Runbook:** `docs/bench-hardware-bringup.md` step 2.1, "two real ... nodes on
  one 802.11s mesh, joined into `batman-adv` per the template; assert **one**
  ICMP echo crosses", run here on the AWUS036ACM rather than HaLow.
- **Decisions the bench follows:** `FML-ADR-053` (BATMAN-IV), `FML-ADR-056`
  (bridge loop avoidance off, and the mesh interface is never bridged with an
  uplink), `FML-ADR-061` (the field mesh is keyed with SAE), and
  `FML-ADR-025` (the high-rate interface as an additional batman-adv hard
  interface).

## What uncertainty this reduces

802.11s has formed in this program only over `mac80211_hwsim`, and batman-adv
has run over real radio only through an infrastructure access point
(`docs/evidence/TBR-LINUX-01/2026-10-01-infrastructure-wifi-prototype.md`). The
question is whether the kernel's 802.11s, SAE and batman-adv stack forms a link
and carries traffic over real RF on a Pi 4B. It is the "single step first" case
for every later mesh result.

## Status

This is a procedure to run, not a result. Nothing has been run. When it is run,
it produces real-RF evidence about this adapter, on the kernel recorded, between
two nodes at the recorded geometry, and nothing wider. It does not make anything
verified by itself; the record states what was observed and the trade owner
decides what it supports.

## What the adapter is, and is not

The AWUS036ACM is a bench radio. It is not a MULE candidate: the high-rate radio
is `TBR-RF-03`'s question, and HaLow is the baseline bearer (`FML-ADR-024`,
`FML-ADR-053`). A pass shows the Linux mesh stack working over real RF with an
in-tree USB driver. It does not qualify the QCA6174A, the HaLow bearer, range,
coexistence, or any channel or power value. M2 asks for "the selected IP mesh".
Whether a two-node AWUS036ACM mesh counts toward M2 is the Program Owner's
decision, and this card does not claim it.

## What the source says the adapter should do

Read from the kernel source, not from hardware. Each line is a prediction for
step 2 or 3 to confirm or refute.

| Fact | Source |
| --- | --- |
| USB ID `0e8d:7612`, driven by the in-tree `mt76x2u` module | `drivers/net/wireless/mediatek/mt76/mt76x2/usb.c`, line 16 (tab shown as two spaces): `{ USB_DEVICE(0x0e8d, 0x7612) },  /* Aukey USBAC1200 - Alfa AWUS036ACM */`. Identical in Linux `v6.12.48` and Raspberry Pi `rpi-6.18.y`. |
| `mesh point` is offered only in a kernel built with `CONFIG_MAC80211_MESH` | `mt76x02_util.c`, `mt76x02u_if_limits`: `#ifdef CONFIG_MAC80211_MESH` / `BIT(NL80211_IFTYPE_MESH_POINT) \|` |
| Both kernels the lab could run build it that way | `CONFIG_MAC80211_MESH=y` and `CONFIG_MT76x2U=m` in Raspberry Pi `rpi-6.18.y` `arch/arm64/configs/bcm2711_defconfig` and in Debian `6.12.48-1` `debian/config/config` |
| At most two interfaces, all on one channel | `mt76x02u_if_comb`: `.max_interfaces = 2,` and `.num_different_channels = 1,` |
| Mesh group keys are encrypted in software | `mt76x02_set_key`: "The hardware does not support per-STA RX GTK, fall back to software mode for these", for `NL80211_IFTYPE_MESH_POINT` with CCMP group keys |
| Firmware files `mt7662.bin` and `mt7662_rom_patch.bin` | `mt76x2/mt76x2.h`: `#define MT7662_FIRMWARE "mt7662.bin"` and `#define MT7662_ROM_PATCH "mt7662_rom_patch.bin"` |
| Debian ships them in `firmware-mediatek` (non-free-firmware) | packages.debian.org, trixie, `firmware-mediatek` `20250410-2`, file list includes `/usr/lib/firmware/mediatek/mt7662.bin` and `mt7662_rom_patch.bin` |

The one-channel limit means a mesh interface and an access point on this adapter
would share a channel. This card uses one mesh interface per adapter and no
access point on it.

## Where and as whom

The two lab Pi 4B nodes, as root, on the operating system they already run. On
2026-10-01 both reported Debian 13.7 with kernel `6.18.50+rpt-rpi-v8`; record
what they run on the day. The MULE image is not used: its arm64 lock
(`os/image/manifest/pi4b-arm64/target-lock.json`) contains none of
`firmware-mediatek`, `iw`, `wpasupplicant` or `batctl`. Adding them is an image
change for the Program Owner to approve.

Keep each node's management connection on a radio or port other than the
adapter. The onboard radio uses `brcmfmac`, and the adapter is selected by
driver, never by interface name.

Each node needs a checkout of `main` for step 8's capture tools.

## Step 0: record the configuration before the first packet

A signal figure read without its geometry cannot be published
(`docs/evidence/README.md`), and check 25 of `tools/validate-docs.sh` refuses
an artifact that publishes one while disclaiming the geometry. Separation,
orientation and ambient conditions cannot be reconstructed afterwards. Write
these down first, for each node:

- date, time, and who ran the card, in the `**Taken by:**` form the existing
  records use. Name only someone already public in this repository as a
  contributor, such as the trade's named owner, or give a role. No other
  person's name goes in: `SECURITY.md`'s publication rule keeps out who
  participates;
- `grep PRETTY_NAME /etc/os-release` and `uname -r`;
- `dpkg-query -W iw wpasupplicant batctl firmware-mediatek` (after step 1);
- `iw reg get`: the country the kernel applies. The region profile's
  `country_code` is `"US"`. If the kernel reports another, stop: the radio is
  not operating under the rules the profile cites;
- which Pi 4B port holds the adapter: one of the USB 2.0 ports or one of the
  USB 3.0 ports;
- the antennas: the two supplied with the adapter or others, with any model or
  gain marking on them, and their orientation;
- separation between the two adapters in metres, line of sight or not, indoors
  or outdoors, and ambient temperature;
- every other transmitter on the bench and its channel, including either Pi's
  onboard access point if it is up.

Leave transmit power at the driver's default under the applied regulatory
domain. Do not set it. Step 5 records what the driver reports.

## Step 1: install the tools and firmware

`apt-get install iw wpasupplicant batctl firmware-mediatek`, and record the
versions. `firmware-mediatek` is in Debian's `non-free-firmware` component. If
apt cannot find it, record `apt-cache policy firmware-mediatek` and stop.

## Step 2: identify the adapter by driver

Plug the adapter in, then:

1. `lsusb -d 0e8d:7612` prints exactly one line.
2. Find its interface by driver, and keep the name in `IF`:

   ```sh
   IF=$(for d in /sys/class/net/*; do
     [ "$(basename "$(readlink -f "$d/device/driver")")" = mt76x2u ] &&
       basename "$d"
   done)
   printf '%s\n' "$IF" | grep -c .
   PHY=phy$(cat "/sys/class/net/$IF/phy80211/index")
   ```

   The count is exactly `1`. If it is `0` or more than `1`, stop: `IF` does not
   name one adapter, and nothing below can be trusted. A name of the form
   `wlx...` carries the adapter's hardware address, so the record calls it
   `<adapter>`. `tools/scrub-telemetry.py` redacts such a name in step 8's
   capture, keys included, and the evidence identifier check refuses one.
3. `dmesg | grep -i -e mt76x2u -e mt7662` shows the firmware loading with no
   error. Record the lines, minus any address.

**Gate:** one adapter, bound to `mt76x2u`, firmware loaded. Otherwise stop and
record what was seen.

## Step 3: the three questions the adapter survey asks

`docs/evidence/TBR-LINUX-01/2026-08-30-wireless-adapter-survey.md` asks these of
any candidate adapter. No radio in the lab has answered the first one yes.

1. `iw phy "$PHY" info`: under **Supported interface modes**, a line
   `* mesh point`. A `mesh point` under frame types or a `join_mesh` command is
   not this, as the survey found.
2. `iw dev "$IF" interface add mesh0 type mp` succeeds. Then
   `iw dev mesh0 del`.
3. `modinfo mt76x2u` lists an `alias:` line for `v0E8Dp7612`.

Also record the **valid interface combinations** block from `iw phy "$PHY"
info`, to compare with the source's two interfaces on one channel.

**Gate:** all three answer yes on both nodes. This part of the record also
belongs to `TBR-LINUX-01`'s driver question.

## Step 4: take the adapter from the network manager and pick a channel

1. Record whether NetworkManager runs and whether it already manages the
   adapter, then take it only if it does:

   ```sh
   systemctl is-active NetworkManager
   nmcli --version
   NM_BEFORE=$(nmcli -g GENERAL.STATE device show "$IF")
   echo "NM_BEFORE=$NM_BEFORE"
   ```

   If NetworkManager is active and `NM_BEFORE` does not read
   `10 (unmanaged)`, run `nmcli device set "$IF" managed no` and record that
   step 4 changed it. If the adapter was already unmanaged, by a keyfile, a
   udev rule or anything else, change nothing, and step 8 changes nothing
   back. The nmcli manual: "The managed property accepts a --permanent option
   to persist the managed state to disk, and not only in runtime." Without
   `--permanent`, the change here lasts only until NetworkManager restarts or
   step 8 reverses it. The card uses neither `--permanent` nor `reset`.
2. Count the networks on the three non-overlapping 2.4 GHz channels, without
   recording any names:

   ```sh
   ip link set "$IF" up
   iw dev "$IF" scan | awk '$1 == "freq:" {print int($2)}' | sort | uniq -c
   ```

3. Use the least occupied of 2412, 2437 and 2462 MHz, at HT20. The region
   profile permits 2.4 GHz and lists channels 1, 6 and 11 as neither DFS nor
   indoor-only. This is a bench setting. `wifi.mesh_channel` stays `TBD` under
   `TBR-RF-01`. Assign the choice, for example `FREQ=2412`, on both nodes.
4. Set `N=1` on node 1 and `N=2` on node 2. Steps 5 to 7 address the nodes as
   `10.60.0.$N`.
5. `export IF FREQ`, so the waits below can read them, and confirm none of the
   three is empty: `echo "IF=$IF FREQ=$FREQ N=$N"`.

## Waiting for a condition, not for a time

Peering, SAE with AMPE, and batman-adv neighbour discovery take no fixed time.
An assertion made the moment a link comes up can fail on a healthy radio.
`test/bench/keyed-mesh.sh` waits up to 60 seconds for authentication for that
reason, and `test/bench/80211s-mesh.sh` polls for traffic. Steps 5 to 7 grade
every gate through this function, defined once in each node's shell:

```sh
# wait_for SECONDS COMMAND...: rerun COMMAND every 2 s until it succeeds,
# or return 1 once SECONDS have passed.
wait_for() {
  limit=$1
  shift
  end=$(($(date +%s) + limit))
  until "$@"; do
    [ "$(date +%s)" -lt "$end" ] || return 1
    sleep 2
  done
}
```

A gate fails only when its condition is still false at the bound. Record the
bound each gate used.

## Step 5: single step, open mesh, no batman-adv

This step separates the radio from SAE. `FML-ADR-061` prohibits an open field
mesh, so this is a diagnostic step on the bench, never a configuration. Node 1
uses `10.60.0.1` and node 2 uses `10.60.0.2`, the bench addresses
`test/bench/keyed-mesh.sh` uses. Choose another `/24` if the lab already uses
that one, and record it.

On each node:

```sh
ip link set "$IF" down
iw dev "$IF" set type mp
ip link set "$IF" mtu 1560
ip link set "$IF" up
iw dev "$IF" mesh join fml-bench-mesh freq "$FREQ" HT20
ip addr add 10.60.0.$N/24 dev "$IF"
```

`HT20` is not optional either. iw `v6.9`, the version Debian trixie ships as
`iw 6.9-1`, documents `parse_freqchan` in `util.c`: "If the mode/channel width
is not given the NOHT is assumed." Dropping it would run the mesh non-HT, a
different experiment, with no error. Record the width `iw dev "$IF" info`
reports.

`1560` is the template's `hard_interface_mtu`. If the driver refuses it, record
the error and continue at 1500. Whether a radio carries a 1560-byte frame is an
open question the template names, so the refusal is a result.

Assert, in order:

1. The station dump lists the peer with `mesh plink: ESTAB` within 60 s:
   `wait_for 60 sh -c 'iw dev "$IF" station dump | grep -q "mesh plink:[[:space:]]*ESTAB"'`.
2. From node 1, `wait_for 30 ping -c 1 -W 2 10.60.0.2` succeeds. From node 2,
   `wait_for 30 ping -c 1 -W 2 10.60.0.1` succeeds. Both ends originate, because a
   node can see its peer and send while losing everything
   (`test/bench/80211s-mesh.sh`).
3. Record `iw dev "$IF" info` (channel, width and the reported `txpower`) and,
   for the peer, the `signal`, `tx bitrate` and `rx bitrate` lines of the
   station dump.

Then leave the mesh and return the interface to the state step 6 starts from:

```sh
iw dev "$IF" mesh leave
ip addr flush dev "$IF"
ip link set "$IF" down
iw dev "$IF" set type managed
```

**Gate:** one echo each way. A failure here is the radio, the driver, the
channel or the configuration, never routing.

## Step 6: keyed mesh with SAE (`FML-ADR-061`)

1. On node 1, generate a credential:
   `head -c 18 /dev/urandom | od -An -tx1 | tr -d ' \n'`. Carry it to node 2 by
   hand or over the management connection. Never commit it, paste it into the
   record, or reuse it.
2. On each node, write `/run/fml-mesh.conf` with mode `600`:

   ```text
   network={
       ssid="fml-bench-mesh"
       mode=5
       frequency=<$FREQ>
       key_mgmt=SAE
       sae_password="<the credential>"
   }
   ```

   This is `test/bench/keyed-mesh.sh`'s configuration. Each line decides
   whether the run is a keyed 802.11s experiment at all, so none may be
   trimmed. From hostap `hostap_2_10`, the release Debian trixie ships as
   `wpasupplicant` `2:2.10-24`:

   | Line | Upstream | Default, and what omitting it does |
   | --- | --- | --- |
   | `ssid="fml-bench-mesh"` | `wpa_supplicant.conf`: "ssid: SSID (mandatory)". In mesh mode it is the mesh ID: `mesh.c` copies it to `conf->meshid`. | No default. `mesh.c` refuses to join: `if (!ssid \|\| !ssid->ssid \|\| !ssid->ssid_len \|\| !ssid->frequency \|\| ...` returns `-ENOENT`. |
   | `mode=5` | `config_ssid.h`: `WPAS_MODE_MESH = 5,`. The reference `wpa_supplicant.conf` lists modes 0 to 2 only. | `0`: "infrastructure (Managed) mode, i.e., associate with an AP (default)". Omitted, the supplicant looks for an access point and never forms a mesh. |
   | `frequency=<$FREQ>` | `wpa_supplicant.c`: "Initial frequency for IBSS/mesh". | No default for mesh. The same `mesh.c` check refuses to join without it. |
   | `key_mgmt=SAE` | `wpa_supplicant.conf`: "SAE = Simultaneous authentication of equals". `mesh.c`: `if (ssid->key_mgmt & WPA_KEY_MGMT_SAE) conf->security \|= MESH_CONF_SEC_AUTH \| MESH_CONF_SEC_AMPE; else conf->security \|= MESH_CONF_SEC_NONE;` | "If not set, this defaults to: WPA-PSK WPA-EAP". In mesh mode anything without SAE takes the `else`: an **open** mesh, with no error. This is the line whose loss would silently turn step 6 into step 5. |
   | `sae_password="..."` | `wpa_supplicant.conf`: "sae_password: SAE password". | "By default, the passphrase from the psk parameter is used if this separate parameter is not used". With neither set there is no credential, and the negative control cannot pass for the right reason. |

3. On each node:

   ```sh
   ip link set "$IF" down
   wpa_supplicant -i "$IF" -c /run/fml-mesh.conf -D nl80211 -B \
     -P /run/fml-mesh.pid -f /run/fml-mesh.log
   ip addr add 10.60.0.$N/24 dev "$IF"
   ip link set "$IF" up
   ```

4. Wait up to 60 s for authentication, as `test/bench/keyed-mesh.sh` does:
   `wait_for 60 sh -c 'iw dev "$IF" station dump | grep -q "authenticated:[[:space:]]*yes"'`.
   Then assert that node 1's station dump for the peer reads
   `authenticated: yes`, `authorized: yes` and `mesh plink: ESTAB`. A `Station`
   line alone is not success: a node that failed authentication still appears,
   in `LISTEN` (`test/bench/keyed-mesh.sh`).
5. One ping each way, as in step 5.
6. **Negative control.** Stop `wpa_supplicant` on **both** nodes by the PID
   it wrote, and wait for that process to exit. `kill` only sends the signal,
   and a supplicant still holding the interface would spoil the restart:

   ```sh
   pid=$(cat /run/fml-mesh.pid)
   kill "$pid"
   wait_for 15 sh -c "! kill -0 $pid 2>/dev/null"
   ```

   This stops the one supplicant step 3 started, by its number, rather than any
   process whose name matches. If it is still running at 15 s, that is a stop.
   Node 1 restarts it from the same
   file. Node 2 writes `/run/fml-mesh-wrong.conf` with a newly generated
   credential and restarts it from that file. Both use step 3's `ip link set`
   and `wpa_supplicant` lines and skip the `ip addr add`, because the address
   is still on the interface. Restarting node 1 too clears its station table:
   a node can keep an entry for a peer that has gone, and a stale
   `authenticated: yes` would fail this control on a healthy radio. Then
   watch node 1 for the full 60 s:

   ```sh
   wait_for 60 sh -c 'iw dev "$IF" station dump | grep -q "authenticated:[[:space:]]*yes"'
   ```

   It is expected to return 1. Then confirm that the station dump shows no
   `ESTAB` for node 2 and that `ping -c 3 -W 2 10.60.0.2` gets no reply. A
   shorter watch proves nothing, because a correct peer could still be
   converging. Finally stop node 2's supplicant the same way, by its PID file
   and with its wait,
   restart it from `/run/fml-mesh.conf`, and repeat step 4, with its wait.

If step 5 passed and this step fails, that is a result about SAE on this adapter
and this kernel. Record the tail of `/run/fml-mesh.log` with addresses removed,
and stop. It says nothing about SAE on HaLow, which is `FML-ADR-062`'s and
`TBR-LINUX-01`'s question.

**Gate:** both nodes authenticated, one echo each way, and the node holding the
wrong credential excluded.

## Step 7: batman-adv over the keyed mesh, one hop

Leave `wpa_supplicant` running from step 6. On each node, configured from
`os/config/batman-adv.conf.template`:

```sh
modprobe batman-adv
batctl routing_algo BATMAN_IV
ip link add name bat0 type batadv
batctl meshif bat0 bridge_loop_avoidance 0
batctl meshif bat0 distributed_arp_table 0
batctl meshif bat0 multicast_mode 0
ip addr flush dev "$IF"
batctl meshif bat0 interface add "$IF"
ip addr add 10.60.0.$N/24 dev bat0
ip link set bat0 up
```

The three settings after `ip link add`, read from the source rather than the
help text. Each one's kernel default is the opposite of what the template
decides, so omitting a line runs the option the program rejected.

| Line | What batctl `v2024.0` sends | What the kernel does with it | Kernel default when the line is omitted |
| --- | --- | --- | --- |
| `bridge_loop_avoidance 0` | `bridge_loop_avoidance.c`: `nla_put_u8(msg, BATADV_ATTR_BRIDGE_LOOP_AVOIDANCE_ENABLED, data->val);` | `netlink.c`: `atomic_set(&bat_priv->bridge_loop_avoidance, !!nla_get_u8(attr));`, so `0` turns it off | On: `atomic_set(&bat_priv->bridge_loop_avoidance, 1);` |
| `distributed_arp_table 0` | `distributed_arp_table.c`: `nla_put_u8(msg, BATADV_ATTR_DISTRIBUTED_ARP_TABLE_ENABLED, data->val);` | `netlink.c`: `atomic_set(&bat_priv->distributed_arp_table, !!nla_get_u8(attr));`, so `0` turns it off | On: `atomic_set(&bat_priv->distributed_arp_table, 1);` |
| `multicast_mode 0` | `multicast_mode.c`: `nla_put_u8(msg, BATADV_ATTR_MULTICAST_FORCEFLOOD_ENABLED, !data->val);`, so `0` sends force-flood on | `netlink.c`: `atomic_set(&bat_priv->multicast_mode, !nla_get_u8(attr));`, so the optimisation is off | On: `atomic_set(&bat_priv->multicast_mode, 1);` |

The kernel lines are from Raspberry Pi `rpi-6.18.y` `net/batman-adv/netlink.c`
and `mesh-interface.c`. The three defaults read the same in Linux `v6.12.48`
`soft-interface.c`. Run `batctl meshif bat0 <setting>` with no value afterwards
and record what each reads back.

`multicast_mode` does not appear in `batctl -h`, but batctl accepts it:
`multicast_mode.c` registers it with no help text
(`COMMAND_NAMED(SUBCOMMAND_MIF, multicast_mode, "mm", ...)`). It is the
template's "Multicast optimisation OFF", and the spelling
`.github/workflows/mesh-probe.yml` uses.

Why each value: the template's comments give the reasons, and the bridge loop
avoidance one is measured. Left on, it held every client frame for 31.5 s on
this program's veth mesh while every `batctl` table read correct
(`FML-ADR-056`). Distributed ARP is off on the template's partition argument,
not on a measurement.

Assert, in order:

1. `bridge link` shows neither `bat0` nor `$IF` in any bridge (`FML-ADR-056`).
2. `batctl meshif bat0 neighbors` lists the peer on `$IF` within 60 s:
   `wait_for 60 sh -c 'batctl meshif bat0 neighbors -H | grep -q "$IF"'`.
   The `-H` matters: the table's header line names the mesh's main interface,
   `$IF` here, so without it the check passes before any neighbour exists.
   batctl `v2024.0` `debug.c`: "-H don't show the header". With it, only
   neighbour rows remain, and BATMAN-IV prints the interface on each row
   (`neighbors.c`, tab written as `\t`: `printf("   %10s\t  ", ifname);`).
3. From node 1, `ping -c 30 -i 1 -W 1 10.60.0.2`. Record the summary line
   with its loss count. One reply or more passes this assertion.
4. From node 2, `wait_for 30 ping -c 1 -W 2 10.60.0.1` succeeds.
5. Record `batctl meshif bat0 originators` with addresses replaced by
   `<node1>` and `<node2>`.

**Gate:** one echo each way over `bat0`. This is runbook step 2.1 on this
adapter.

## Step 8: capture, then restore

Every stop comes here. A gate that fails, a stop condition, or the end of step 7
all run this step on both nodes before anything else, so the failing state is
captured before it is torn down, and neither node is left in mesh mode, with a
supplicant running, or with a credential in `/run`.

1. On each node, from the checkout of `main`:
   `test/bench/capture-telemetry.py --label awus036acm-one-hop --out /run/capture.json`,
   then
   `python3 tools/scrub-telemetry.py /run/capture.json -o /run/capture.scrubbed.json`.
   The scrubber is committed without the executable bit, so it runs through
   `python3`.
   Read the scrubbed file before filing it. The scrubber does not read firmware
   strings or every SSID.
2. Restore, only if step 4 has run. Steps 0 to 3 change nothing on the
   adapter, and a stop there may come before `IF` holds one name, so a stop in
   steps 0 to 3 ends at item 1. Confirm `echo "IF=$IF"` prints the adapter, and
   define `wait_for` (the section before step 5) if the stop came in step 4:

   ```sh
   ip link del bat0 2>/dev/null
   if [ -f /run/fml-mesh.pid ]; then
     pid=$(cat /run/fml-mesh.pid)
     kill "$pid"
     wait_for 15 sh -c "! kill -0 $pid 2>/dev/null"
   fi
   rm -f /run/fml-mesh*.conf /run/fml-mesh.pid
   ip addr flush dev "$IF"
   ip link set "$IF" down
   iw dev "$IF" set type managed
   ```

   A stop before step 7 leaves less to undo, so `ip link del` may find no
   `bat0` and there may be no PID file; that is expected. The supplicant is
   stopped only by the PID it wrote, never by name, so nothing else on the node
   is touched. Then, only if step 4 recorded that it changed NetworkManager,
   run `nmcli device set "$IF" managed yes`. If step 4 changed nothing, leave
   NetworkManager alone: forcing `managed yes` onto an adapter it did not
   manage before would hand it over. Confirm with `iw dev "$IF" info` that the
   type reads `managed`, and that `nmcli -g GENERAL.STATE device show "$IF"`
   matches `NM_BEFORE`'s managed or unmanaged state.

## What to record

Commit one record beside this card, named
`<date>-awus036acm-one-hop-mesh-two-pi4b.md`, carrying:

- everything from step 0, for both nodes;
- each gate's outcome, and the first one that failed if any did;
- step 3's three answers and the interface combinations block;
- step 4's `nmcli --version`, `NM_BEFORE`, and whether step 4 changed it;
- the MTU outcome from step 5;
- the station-dump fields from steps 5 and 6 and the ping summary lines;
- step 7's 30-ping summary line;
- the scrubbed captures, as `.json` files beside the record.

Do not commit any hardware address, serial number, hostname, SSID other than
`fml-bench-mesh`, or the credential. The equipment-identifier check in
`tools/validate-docs.sh` refuses universally administered MAC addresses and
EUI-64 link-local addresses in evidence.

Then add the record to this directory's README, update `docs/ROADMAP-DEV.md`
item 1.7's State, and note the result in the `TBR-RF-01` trade's Progress
section in the same change.

## Stop conditions

Stop, run step 8, and record, rather than change the procedure, if: the regulatory domain is
not the profile's country, the firmware does not load, `mesh point` is absent,
any gate's condition is still false at its bound, or a step needs a setting the
template or an ADR does not give. A failure is a result worth committing.
Before "cannot", "blocked" or "needs other hardware" goes into the record, a
separate agent qualifies it (Done 7).

## What a pass shows, and what it does not

A pass shows that this adapter, on this kernel, forms an authenticated 802.11s
peer link with another over real RF, and that batman-adv carries traffic in both
directions over it with the program's configuration. It is the first real-RF
802.11s result in this program.

It does not show multi-hop. Runbook step 2.2's line needs three mesh-capable
nodes, and the lab has two adapters. It does not show throughput, range,
coexistence with the onboard access point, behaviour under load, or anything
about HaLow or the QCA6174A. The transport measurement in runbook step 2.3 is a
separate card, run after this one passes.
