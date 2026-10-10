# Pi 4B profile manifests

Pins for the `pi4b-arm64` image profile (`FML-ADR-088`), beside the x86-64
manifests in the parent directory, which are unchanged. The tools tree is not
repeated here: the profile is cross-built on an amd64 host and uses the
parent's `tools-tree-lock.json`.

| File | Contents |
| --- | --- |
| `direct-packages.list` | The profile's owner-approved target package roles. |
| `target-lock.json` | Generated exact arm64 target closure and provenance. |
| `packages.list` | Generated exact target package specifications consumed by mkosi. |

Regenerate the two generated files with
`tools/resolve-image-packages.py --keyring <debian-archive-keyring.gpg> --profile pi4b-arm64 --write`.
