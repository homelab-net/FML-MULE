# Sources for the consumer reading

Retrieved 2026-09-24. Each file in this directory that this note names is an
excerpt, not the whole upstream file. The upstream lines are unchanged. A line
that begins `# --- omitted lines` is not upstream. It marks a gap between
two ranges in the same file. None is relicensed as CC BY 4.0.

OpenTAKServer excerpts are GPL-3.0-only, from `brian7704/OpenTAKServer` tag
`1.7.13`, commit `67903c26d95552738d85be4bc3c3ff3321378dbe`. The `LICENSE`
file at that commit is GPL-3.0-only. The text is
`docs/evidence/licenses/GPL-3.0.txt`.

Meshtastic firmware excerpts are GPL-3.0-only, from `meshtastic/firmware`
tag `v2.8.0.47db0e3`, commit `47db0e3020a608e06fb65cce70cd2f093021bd82`,
published 2026-09-01. That commit is not the protobufs pin in
`2026-09-24-upstream-snapshots.SOURCE.md`. The firmware `LICENSE` at that
commit is GPL-3.0-only. The same license text applies.

SHA-256 below is of the archived file, header included.

| File | Upstream lines | SHA-256 |
| --- | --- | --- |
| `2026-09-24-opentakserver-1.7.13-eudhandler-sender.py.txt` | `opentakserver/eud_handler/EudHandler.py` 329-337, 449-450, 458-483, 485-511 | `a55a5cf702f70ba981dbb2558ce533984781f67b7da84517303b3855cfd0c55f` |
| `2026-09-24-opentakserver-1.7.13-insert-cot.py.txt` | `opentakserver/cot_parser/cot_parser.py` 101-133, 1237-1242 | `d11aa9c8276cd8f7629cfc0679da68e167313ea093b46769d8a466d5c8757dbe` |
| `2026-09-24-opentakserver-1.7.13-route-cot.py.txt` | `opentakserver/cot_parser/cot_parser.py` 1142-1212 | `7430cb942713cbe42155235cb8c99ad23c94942be16b60cbe26460e42061bce7` |
| `2026-09-24-opentakserver-1.7.13-map-state.py.txt` | `opentakserver/blueprints/ots_api/api.py` 541-574 | `b844cb4e619e060d970225945bfda1cb667c47280f91f3d88a017ddf989d7de9` |
| `2026-09-24-opentakserver-1.7.13-get-cot.py.txt` | `opentakserver/blueprints/marti_api/cot_marti_api.py` 24-36 | `744768900a64ddf110112fb21aac536c968eff1e7b0d62a4ee80e17a9c2162b7` |
| `2026-09-24-opentakserver-1.7.13-eud-last-point.py.txt` | `opentakserver/models/EUD.py` 88-89 | `27f2a55a1f38c408fb265b06df4dc195d387eb8e1f2a6462b8dc8d2d2f8e6135` |
| `2026-09-24-opentakserver-1.7.13-meshtastic-cot.py.txt` | `opentakserver/controllers/meshtastic_controller.py` 235-260, 411-427, 632-641 | `72912520a2a53b3c4f644351794c1df6402f18e1fe02fe676b1402189ec1ed76` |
| `2026-09-24-opentakserver-1.7.13-marker-insert.py.txt` | `opentakserver/blueprints/ots_api/marker_api.py` 208-218 | `94375cc7c1875307dec42ad7146bc9218861d19c6c7d548a8c8b52c727b7625e` |
| `2026-09-24-meshtastic-firmware-2.8.0.47db0e3-neighbor.cpp.txt` | `src/modules/NeighborInfoModule.cpp` 61-78, 87-96 | `57ecf7c20187e4b793a8d38f02d667f9ebcc036225d786a9c3170de3604143cb` |
| `2026-09-24-meshtastic-firmware-2.8.0.47db0e3-position.cpp.txt` | `src/modules/PositionModule.cpp` 256-257 | `fa52ffd0f654ca2fd257e8062717569adb28971831a0c06ce30734b84d0610ac` |
| `2026-09-24-meshtastic-firmware-2.8.0.47db0e3-router.cpp.txt` | `src/mesh/Router.cpp` 314-324 | `29b49bcb5834d237bccf561a308caad90b174d0384f5966cbbcf9f14e46e85ad` |
