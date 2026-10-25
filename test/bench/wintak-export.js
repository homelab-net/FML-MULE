// Export what WinTAK itself recorded during a partition trial, as JSON lines.
//
//   node wintak-export.js FROM_ISO TO_ISO OUT.jsonl
//
// Reads, on the WinTAK host, read-only:
//  - %APPDATA%\WinTAK\Logs\Log-WinTAK-<date>*.txt: when the server stream
//    went quiet, each reconnect attempt, and when it came back up;
//  - %APPDATA%\WinTAK\Databases\ChatDb2.sqlite (a copy): each chat's
//    messageId, sender and receive or send time.
// WinTAK writes both in LOCAL time without a zone (the database stores local
// wall-clock milliseconds as if they were UTC), so each time is converted to
// UTC here with this host's zone. Message text and sender callsigns are kept
// (the trial's are synthetic); raw CoT, uids and positions are not exported.
// Needs Node 22.5 or later (node:sqlite).
"use strict";
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { DatabaseSync } = require("node:sqlite");

const [from, to, out] = process.argv.slice(2);
if (!out) {
  console.error("usage: node wintak-export.js FROM_ISO TO_ISO OUT.jsonl");
  process.exit(64);
}
const t0 = Date.parse(from);
const t1 = Date.parse(to);
const appdata = process.env.APPDATA;
const lines = [];

// A local wall-clock reading, as "YYYY-MM-DD HH:MM:SS,mmm", to a UTC Date.
function localToUtc(s) {
  const m = s.match(/^(\d{4})-(\d\d)-(\d\d)[ T](\d\d):(\d\d):(\d\d)[,.](\d{3})/);
  if (!m) return null;
  return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6], +m[7]);
}

const LOG_EVENTS = [
  [/No data received from (\S+) in (\d+) seconds/, "stream-silent"],
  [/Initiating streaming network connection/, "connect-attempt"],
  [/Error trying to make network connection.*\((.*)\)/, "connect-failed"],
  [/Stream connection to \S+ is up!/, "stream-up"],
];

const logDir = path.join(appdata, "WinTAK", "Logs");
for (const f of fs.readdirSync(logDir).filter((n) => n.startsWith("Log-WinTAK-"))) {
  for (const line of fs.readFileSync(path.join(logDir, f), "utf8").split(/\r?\n/)) {
    const t = localToUtc(line);
    if (!t || t < t0 || t > t1) continue;
    for (const [re, event] of LOG_EVENTS) {
      if (re.test(line)) lines.push({ t: t.toISOString(), who: "wintak", path: "server", event });
    }
  }
}

// The database is open in WinTAK, so read a copy.
const tmp = path.join(os.tmpdir(), `chatdb-${process.pid}.sqlite`);
fs.copyFileSync(path.join(appdata, "WinTAK", "Databases", "ChatDb2.sqlite"), tmp);
const db = new DatabaseSync(tmp, { readOnly: true });
const q = "select messageId, receiveTime, sentTime, senderCallsign, message from Chat";
for (const r of db.prepare(q).all()) {
  const rx = r.receiveTime != null;
  const wall = new Date(Number(rx ? r.receiveTime : r.sentTime));
  const t = localToUtc(wall.toISOString().replace("Z", ""));
  if (!t || t < t0 || t > t1) continue;
  lines.push({
    t: t.toISOString(), who: "wintak", path: null,
    event: rx ? "rx-chat" : "tx-chat",
    messageId: r.messageId, sender: r.senderCallsign, text: r.message,
  });
}
db.close();
fs.unlinkSync(tmp);

lines.sort((a, b) => a.t.localeCompare(b.t));
fs.writeFileSync(out, lines.map((l) => JSON.stringify(l)).join("\n") + "\n");
console.log(`${lines.length} WinTAK events, ${from} to ${to} -> ${out}`);
