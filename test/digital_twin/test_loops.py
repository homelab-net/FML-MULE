"""Tests for `mule.loops`.

`FML-ADR-056` gave up automatic loop protection and asked for a detector. A
detector nobody has watched fire is worth less than the protection it replaced,
so every signature here is produced by a planted condition rather than asserted.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mule.loops import Signature, loop_signatures

OURS = "aa:bb:cc:dd:ee:01"
#: The mesh hard interface. A loop on the bench announced this one FIRST,
#: before the bridge address, which is why the detector watches both.
OURS_MESH_IF = "aa:bb:cc:dd:ee:0f"
PEER = "aa:bb:cc:dd:ee:02"
OTHER = "aa:bb:cc:dd:ee:03"
CLIENT = "11:22:33:44:55:66"


@dataclass
class FakeTranslation:
    """Scripted translation-table readings.

    Simulates: what `batctl` would report about who is reachable where, and
    the case where it cannot be read at all.

    Does not simulate: `batman-adv`'s timing. Entries here are a snapshot; a
    real table has ageing, and a stale entry is exactly the innocent
    explanation `mule.loops` warns a caller about.
    """

    entries: tuple[tuple[str, str], ...] | None = ()
    own: tuple[str, ...] | None = (OURS, OURS_MESH_IF)
    calls: list[str] = field(default_factory=list)

    def global_translation_entries(self) -> tuple[tuple[str, str], ...] | None:
        """Report (client, originator) pairs."""
        self.calls.append("entries")
        return self.entries

    def own_addresses(self) -> tuple[str, ...] | None:
        """Report every address belonging to this node."""
        self.calls.append("own")
        return self.own


def test_a_healthy_table_shows_no_signature() -> None:
    """Accept one client announced by one originator."""
    observed = FakeTranslation(entries=((CLIENT, PEER),))

    assert loop_signatures(observed) == []


def test_a_client_under_two_originators_is_a_signature() -> None:
    """Catch two nodes both claiming to reach one client.

    That is what a bridged loop looks like from the outside, and it is the
    first of the two signatures FML-ADR-056 names.
    """
    observed = FakeTranslation(entries=((CLIENT, PEER), (CLIENT, OTHER)))

    assert "client_under_more_than_one_originator" in loop_signatures(observed)


def test_our_own_address_coming_back_from_the_mesh_is_a_signature() -> None:
    """Catch a frame that left this node and returned.

    Nothing legitimate announces this node's own bridge address to this node.
    It is the second signature FML-ADR-056 names and the less ambiguous one.
    """
    observed = FakeTranslation(entries=((OURS, PEER),))

    assert "own_address_announced_by_a_peer" in loop_signatures(observed)


def test_the_bridge_address_match_ignores_case() -> None:
    """Match regardless of case.

    batctl and ip print lower case, but a caller assembling these from
    elsewhere may not, and a missed match here is a loop nobody sees.
    """
    observed = FakeTranslation(entries=((OURS.upper(), PEER),), own=(OURS,))

    assert "own_address_announced_by_a_peer" in loop_signatures(observed)


def test_both_signatures_are_reported_together() -> None:
    """Report every signature present, not the first.

    A caller diagnosing a node needs the whole picture.
    """
    observed = FakeTranslation(entries=((CLIENT, PEER), (CLIENT, OTHER), (OURS, PEER)))

    found = loop_signatures(observed)

    assert len(found) == 2


def test_an_unreadable_table_is_not_a_loop() -> None:
    """Report nothing when batctl cannot answer.

    A node with no batctl is not a node with a broken network, and conflating
    them is the T | None confusion AGENTS.md records four instances of.
    """
    assert loop_signatures(FakeTranslation(entries=None)) == []


def test_a_node_that_cannot_list_its_addresses_yields_no_signature() -> None:
    """Skip the second check when the node has no bridge at all."""
    observed = FakeTranslation(entries=((OURS, PEER),), own=None)

    assert loop_signatures(observed) == []


def test_an_unreadable_table_is_not_even_asked_about_the_bridge() -> None:
    """Return early, so a caller cannot read a bridge signature into nothing."""
    observed = FakeTranslation(entries=None)

    loop_signatures(observed)

    assert "own" not in observed.calls


def test_the_signature_vocabulary_names_observations_not_conclusions() -> None:
    """Keep the names describing what was seen.

    Neither says "loop", because neither observation proves one: a roamed
    client with a stale entry produces the first without any loop existing.
    """
    names: tuple[Signature, ...] = (
        "client_under_more_than_one_originator",
        "own_address_announced_by_a_peer",
    )

    assert not any("loop" in name for name in names)


def test_the_mesh_interface_address_is_watched_not_only_the_bridge() -> None:
    """Catch the address a real loop announced first.

    FML-ADR-056 names "the node's own bridge address". A loop reproduced on
    the bench put the mesh hard interface's address into the table before the
    bridge address arrived, so watching only the bridge detects the same loop
    later. See docs/evidence/TBR-NET-01/.
    """
    observed = FakeTranslation(entries=((OURS_MESH_IF, PEER),))

    assert "own_address_announced_by_a_peer" in loop_signatures(observed)
