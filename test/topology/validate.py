#!/usr/bin/env python3
"""Check declared service topology, then the mutations that must fail.

Usage:
    python test/topology/validate.py

This reads the catalog and the Quadlet texts. It does not start a container.
Quadlet generation and the TAK software path are the other two layers.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).resolve().parent / "manifest.yml"
CATALOG = ROOT / "services" / "catalog" / "catalog.yml"
QUADLETS = ROOT / "services" / "quadlets"


def _assignments(text: str) -> list[str]:
    return [line for line in text.splitlines() if line and not line.startswith("#")]


def _systemd_name(logical: str) -> str:
    if logical.endswith(".network"):
        return logical[: -len(".network")] + "-network.service"
    if logical.endswith(".container"):
        return logical[: -len(".container")] + ".service"
    return logical


def _load_units(entry: dict[str, Any]) -> dict[str, str]:
    enabled = bool(entry["enabled"])
    logicals = [entry["unit"], *entry.get("bundle", [])]
    texts: dict[str, str] = {}
    for logical in logicals:
        disk = logical if enabled else f"{logical}.disabled"
        path = QUADLETS / disk
        if not path.is_file():
            raise FileNotFoundError(path)
        texts[logical] = path.read_text(encoding="utf-8")
    return texts


def _requires(text: str) -> set[str]:
    found: set[str] = set()
    for line in _assignments(text):
        if line.startswith("Requires="):
            found.update(line.split("=", 1)[1].split())
    return found


def _after(text: str) -> set[str]:
    found: set[str] = set()
    for line in _assignments(text):
        if line.startswith("After="):
            found.update(line.split("=", 1)[1].split())
    return found


def _keys(text: str, key: str) -> list[str]:
    prefix = f"{key}="
    return [
        line.split("=", 1)[1] for line in _assignments(text) if line.startswith(prefix)
    ]


def check_case(
    case: dict[str, Any],
    entry: dict[str, Any],
    texts: dict[str, str],
    mesh_gate: str,
) -> list[str]:
    """Return topology defects for one case. Empty means the case holds."""
    errors: list[str] = []
    bundle = list(entry.get("bundle", []))
    root = entry["unit"]
    if not str(root).endswith(".target"):
        errors.append(f"{case['id']}: bundle root {root!r} is not a .target")
    if root in bundle:
        errors.append(f"{case['id']}: root {root} is also listed as a member")

    known = {_systemd_name(name) for name in bundle}
    known.add(root)
    known.add(mesh_gate)

    for logical, text in texts.items():
        requires = _requires(text)
        after = _after(text)
        for token in sorted(requires | after):
            if token not in known:
                errors.append(
                    f"{case['id']}: {logical} depends on {token}, which is not "
                    "in the bundle or the unresolved mesh gate"
                )
        if logical == root:
            if mesh_gate in requires or mesh_gate in after:
                errors.append(
                    f"{case['id']}: mesh gate is on the target; that does not "
                    "hold the members it Wants="
                )
            for member in bundle:
                service = _systemd_name(member)
                if service not in requires or service not in after:
                    errors.append(
                        f"{case['id']}: target does not wait for member {service}"
                    )
            continue
        if mesh_gate not in requires or mesh_gate not in after:
            errors.append(
                f"{case['id']}: member {logical} does not require the mesh gate"
            )
        if logical.endswith(".container"):
            networks = _keys(text, "Network")
            if case["network"] not in networks:
                errors.append(
                    f"{case['id']}: {logical} is not on network {case['network']}"
                )
            if any(line.startswith("PublishPort=") for line in _assignments(text)):
                errors.append(f"{case['id']}: {logical} publishes a host port")
            for port in case["forbidden_host_ports"]:
                for line in _assignments(text):
                    published = (
                        line.startswith("PublishPort=")
                        and port in line.split("=", 1)[1]
                    )
                    if published:
                        errors.append(
                            f"{case['id']}: {logical} exposes host port {port}"
                        )
            for line in _assignments(text):
                if "127.0.0.1" in line or "localhost" in line:
                    errors.append(f"{case['id']}: {logical} uses a loopback endpoint")

    for edge in case["required_requires"]:
        requires = _requires(texts[edge["from"]])
        if edge["to"] not in requires:
            errors.append(f"{case['id']}: {edge['from']} does not require {edge['to']}")
    for edge in case["forbidden_requires"]:
        if edge["to"] in _requires(texts[edge["from"]]):
            errors.append(
                f"{case['id']}: {edge['from']} requires {edge['to']}, "
                "which is forbidden"
            )

    for logical in bundle:
        if not logical.endswith(".container"):
            continue
        if case["rabbit_env"] not in texts[logical] and logical.startswith(
            ("opentakserver", "eud-handler", "cot-parser")
        ):
            errors.append(f"{case['id']}: {logical} does not name the broker endpoint")
        if logical.startswith(("opentakserver", "eud-handler", "cot-parser")):
            if case["sql_host_marker"] not in texts[logical]:
                errors.append(f"{case['id']}: {logical} does not name the SQL host")

    graph: dict[str, set[str]] = {}
    for logical in [root, *bundle]:
        graph[logical] = set()
        for token in _requires(texts[logical]):
            for other in [root, *bundle]:
                if token == _systemd_name(other) or token == other:
                    graph[logical].add(other)

    def _walk(node: str, seen: list[str]) -> None:
        if node in seen:
            cycle = " -> ".join([*seen, node])
            errors.append(f"{case['id']}: dependency cycle {cycle}")
            return
        for nxt in graph.get(node, ()):
            _walk(nxt, [*seen, node])

    for node in graph:
        _walk(node, [])
    return errors


def _apply(text: str, mutation: dict[str, Any]) -> str:
    if "replace" in mutation:
        old = str(mutation["replace"])
        new = str(mutation["with"])
        if old not in text:
            raise ValueError(f"mutation {mutation['id']} did not match")
        return text.replace(old, new)
    needle = str(mutation["insert_after"])
    line = str(mutation["line"])
    if needle not in text:
        raise ValueError(f"mutation {mutation['id']} did not find {needle}")
    return text.replace(needle, needle + "\n" + line, 1)


def main() -> int:
    """Validate every manifest case and the mutations that must fail."""
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    services = {entry["name"]: entry for entry in catalog["services"]}
    mesh_gate = str(manifest["mesh_gate"])
    if manifest.get("mesh_gate_resolved"):
        print(
            "FAIL: mesh gate is marked resolved and TBR-LINUX-01 is open",
            file=sys.stderr,
        )
        return 1
    failed = False
    for case in manifest["cases"]:
        entry = services[case["catalog_service"]]
        texts = _load_units(entry)
        errors = check_case(case, entry, texts, mesh_gate)
        if errors:
            failed = True
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            continue
        print(f"{case['id']}: topology holds")
        for mutation in case.get("mutations", []):
            mutated = dict(texts)
            mutated[mutation["unit"]] = _apply(texts[mutation["unit"]], mutation)
            defects = check_case(case, entry, mutated, mesh_gate)
            if not defects:
                failed = True
                print(
                    f"FAIL: mutation {mutation['id']} was still accepted",
                    file=sys.stderr,
                )
            else:
                print(f"{case['id']}: mutation {mutation['id']} rejected")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
