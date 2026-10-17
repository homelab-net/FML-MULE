#!/bin/bash
# Independent RF energy witness for a sub-GHz transmission, using a
# receive-only RTL-SDR as the instrument.
#
# Usage, from the node the SDR is attached to:
#
#   test/bench/sdr-rf-witness.sh <start-epoch> <low-Hz> <high-Hz> <tag>
#
# It waits until 20 s before <start-epoch>, then captures for 150 s, writing
# $HOME/sdr-witness/<tag>.csv and a <tag>.meta beside it. Pass the same
# <start-epoch> to test/bench/lora-tx-burst.py on the transmitting node and the
# two runs line up on NTP time without either end signalling the other.
#
# WHY THIS EXISTS. The bench has one LoRa radio, so a send proves hand-off to
# the radio and nothing more, and `airUtilTx` does not prove transmission
# either -- it arrives in periodic telemetry. Every sub-GHz record in this
# repository up to now rests on the transmitting device's own account of
# itself. This is the first instrument that does not.
#
# WHAT A RESULT HERE IS, EXACTLY. Energy, in a frequency span, in a one-second
# interval. That is all. It is the TRANSMISSION half of a link and only that
# half:
#
#   * it does NOT show a peer received anything;
#   * it does NOT show a peer decoded anything;
#   * it does NOT identify WHICH device transmitted. Any radio in range on
#     that span raises the same bins. Attribution comes from timing against a
#     known send schedule, and from the controls below, never from the
#     presence of energy alone.
#
# THE dB FIGURES ARE NOT dBm. rtl_power reports uncalibrated FFT bin
# magnitude. Nothing on this bench calibrates it, so a value here supports a
# within-capture contrast -- this interval against that interval, same gain,
# same span, same antenna -- and supports no absolute power, path loss, link
# budget or receiver sensitivity claim whatsoever.
#
# GAIN IS PINNED AT 0 dB ON PURPOSE. At minimum gain a local transmitter a few
# metres away is tens of dB clear while distant third-party traffic on a
# shared ISM channel stays under the noise floor. That makes this a LOCAL
# witness: it isolates the device under test, and it is correspondingly blind
# to the ambient band occupancy a coexistence survey would also want. A survey
# needs its own run at higher gain, and must then expect to see other people.
#
# THE SPAN MUST NOT EXCEED THE DONGLE BANDWIDTH. rtl_power hops the tuner when
# the span is wider than it can cover at once, and a hopping capture can be
# pointed elsewhere while a short burst happens. Keep the span at or under
# 2 MHz and confirm "Number of frequency hops: 1" in <tag>.err. A wider span
# trades the guarantee of catching a burst for coverage, which is the wrong
# trade for a witness.
#
# TWO CONTROLS ARE REQUIRED, NOT OPTIONAL. A capture showing energy where it
# was expected proves nothing on its own; the same spike would appear if the
# instrument simply responded to any nearby transmitter.
#
#   frequency control  same send schedule, span moved several MHz away.
#                      Expect nothing. A detection here means the instrument
#                      is seeing broadband coupling, not a channel.
#   idle control       same span, no sends at all. Expect nothing. This
#                      measures how often the channel lights up by itself,
#                      which is the method's false-positive rate.
#
# TIMESTAMPS ARE INTERVAL ENDS. rtl_power stamps a row when its integration
# interval closes, so the row covering an event at T is labelled T+1 at
# -i 1. Correlate against the row AFTER a send, not the row bearing its
# second. Reading the label as the interval start shifts every detection by
# one row and makes a correct capture look like a near miss.

set -eu

INTERVAL=1
DURATION=150
GAIN=0
BIN_HZ=25000
LEAD_IN=20

fail() {
  printf 'sdr-rf-witness: %s\n' "$1" >&2
  exit 1
}

[ "$#" -eq 4 ] || fail "usage: $0 <start-epoch> <low-Hz> <high-Hz> <tag>"

start_epoch=$1
low_hz=$2
high_hz=$3
tag=$4

command -v rtl_power >/dev/null 2>&1 ||
  fail "rtl_power not found. Install the rtl-sdr package."

case $tag in
  *[!A-Za-z0-9._-]*) fail "tag '$tag' must be a bare filename" ;;
esac

span=$((high_hz - low_hz))
[ "$span" -gt 0 ] || fail "high-Hz must exceed low-Hz"
if [ "$span" -gt 2000000 ]; then
  fail "span ${span} Hz exceeds 2 MHz; rtl_power would hop the tuner and
  could be pointed away while a burst happens. See the header."
fi

out=$HOME/sdr-witness
mkdir -p "$out"

begin=$((start_epoch - LEAD_IN))
now=$(date +%s)
if [ "$now" -gt "$begin" ]; then
  fail "start-epoch $start_epoch is already within ${LEAD_IN}s; the capture
  would miss its lead-in. Choose a later start."
fi

while [ "$(date +%s)" -lt "$begin" ]; do
  sleep 0.2
done

{
  printf 'tag=%s\n' "$tag"
  printf 'rx_start_epoch=%s utc=%s\n' "$(date +%s)" "$(date -u +%FT%TZ)"
  printf 'span_hz=%s:%s bin_hz=%s gain_db=%s interval_s=%s duration_s=%s\n' \
    "$low_hz" "$high_hz" "$BIN_HZ" "$GAIN" "$INTERVAL" "$DURATION"
  printf 'expected_tx_start_epoch=%s\n' "$start_epoch"
  printf 'host=%s kernel=%s\n' "$(hostname)" "$(uname -r)"
} >"$out/$tag.meta"

# TZ=UTC so the CSV timestamps need no timezone reasoning when they are
# compared against a transmit log recorded in UTC on another host.
TZ=UTC rtl_power \
  -f "$low_hz:$high_hz:$BIN_HZ" \
  -i "$INTERVAL" \
  -g "$GAIN" \
  -e "$DURATION" \
  "$out/$tag.csv" 2>"$out/$tag.err"

printf 'rx_done_epoch=%s\n' "$(date +%s)" >>"$out/$tag.meta"

if ! grep -q 'Number of frequency hops: 1' "$out/$tag.err"; then
  fail "rtl_power hopped the tuner; this capture cannot be trusted to have
  been listening continuously. See $out/$tag.err."
fi

printf 'wrote %s (%s rows)\n' "$out/$tag.csv" "$(wc -l <"$out/$tag.csv")"
