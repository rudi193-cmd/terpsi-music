"""Guardian receipts: the property no anchor gives, and the one they cannot give.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from records import Edge, Field, Principal, Rung, serve  # noqa: E402
from records.disclosure import Ledger, Log  # noqa: E402
from records.receipts import (  # noqa: E402
    AsymmetricUnavailable, GuardianReceipt, HmacTagger, Issuance, NoSigner,
    Uncheckable, authentic, contradictions, gaps, held_by, issue, receipt_text,
    schemes,
)

T0 = datetime(2026, 3, 1)
KEY = b"program-issuing-key"
BEN, ANA = "student-ben", "student-ana"
LB, LA = "lane-ben", "lane-ana"


def guardians(subject=BEN, until=None):
    return [
        Edge("guardian_of", "g-mother", subject, T0, until, created_at=T0),
        Edge("guardian_of", "g-father", subject, T0, until, created_at=T0),
        Edge("staff_of", "staff-nguyen", subject, T0, created_at=T0),
    ]


def write(ledger, lane, subject, n=1, at=T0):
    fld = Field(lane, subject, "chair", Rung.L3, payload="x", instruction="y")
    edges = [Edge("guardian_of", "g-mother", subject, T0, created_at=T0)]
    for _ in range(n):
        ledger = ledger.record(serve(fld, Principal("g-mother"), edges, at),
                               lane_id=lane, principal_id="g-mother",
                               subject_id=subject, field_name="chair", at=at)
    return ledger


def issue_all(ledger, lane, subject, edges, n, at=T0):
    """Write n entries, receipting each — the ordinary operating loop."""
    out = []
    for _ in range(n):
        ledger = write(ledger, lane, subject, 1, at)
        out.extend(issue(ledger, lane, subject, edges, at, KEY))
    return ledger, tuple(out)


# --- who is owed one -------------------------------------------------------


def test_every_guardian_with_standing_gets_one_and_nobody_else():
    led, rs = issue_all(Ledger(), LB, BEN, guardians(), 1)
    assert {r.to_guardian for r in rs} == {"g-mother", "g-father"}, (
        "staff or a non-guardian received a receipt"
    )


def test_an_ended_guardianship_is_not_issued_new_receipts():
    ended = [Edge("guardian_of", "g-father", BEN, T0, invalid_at=T0, created_at=T0)]
    _led, rs = issue_all(Ledger(), LB, BEN, ended, 1, at=T0 + timedelta(days=30))
    assert rs == ()


def test_standing_not_reachability_decides():
    """A contact restriction suppresses *messages*. Whether it also revokes the
    ability to audit your own child's record is a different question with a
    different answer, and conflating them would let a restriction quietly
    remove someone's oversight. `issue()` takes edges, never restrictions."""
    import inspect
    params = set(inspect.signature(issue).parameters)
    assert "restrictions" not in params and "recipients" not in params


# --- the property no anchor gives -----------------------------------------


def test_a_guardian_can_see_a_hole_in_their_own_sequence_unaided():
    """The whole argument for an adverse witness.

    Holding 1, 2, 3, 5 proves 4 existed and is gone — without the institution's
    cooperation, without a third party, and without learning anything about any
    other student."""
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 5)
    mine = held_by(rs, "g-mother", LB)
    assert [r.position for r in mine] == [1, 2, 3, 4, 5]
    assert gaps(mine) == ()

    suppressed = tuple(r for r in mine if r.position != 4)
    assert gaps(suppressed) == (4,), "a removed entry left no visible hole"


def test_positions_are_per_lane_so_a_receipt_says_nothing_about_other_students():
    """The reason §5's partitioning is load-bearing here. A global chain would
    make a guardian's positions leak how many entries concerned other
    children."""
    led = Ledger()
    led = write(led, LA, ANA, 9)                     # a busy sibling lane
    led, rs = issue_all(led, LB, BEN, guardians(), 2)
    mine = held_by(rs, "g-mother", LB)
    assert [r.position for r in mine] == [1, 2], (
        "positions counted other lanes — the receipt leaks program-wide volume"
    )


def test_gaps_refuses_to_compare_sequences_that_are_not_sequences():
    led = Ledger()
    led, ben = issue_all(led, LB, BEN, guardians(), 1)
    led, ana = issue_all(led, LA, ANA, guardians(ANA), 1)
    for mixed in (ben + ana, held_by(ben + ana, "g-mother")):
        try:
            gaps(mixed)
        except ValueError:
            continue
        raise AssertionError("gaps() compared across lanes or guardians")


# --- contradiction with the institution's copy ----------------------------


def test_a_removed_entry_contradicts_the_receipt_held_for_it():
    led, rs = issue_all(Ledger(), LB, BEN, guardians(), 4)
    mine = held_by(rs, "g-mother", LB)
    lopped = Log(led.log_for(LB).entries[:2])
    bad = contradictions(lopped, mine)
    assert len(bad) == 2 and "log now ends at 2" in bad[0]


def test_a_coherently_rewritten_log_contradicts_the_receipts():
    """The realistic attack, and it shows the division of labour.

    An institution that edits an entry and leaves the digests alone produces a
    log `Log.verify()` rejects on its own — incoherent tampering needs no
    guardian. The version worth defending against is the careful one: rewrite
    the entry **and rebuild the chain** so the log verifies perfectly.

    That is exactly what receipts catch and internal verification cannot. The
    rebuilt chain's digests are all new, so the receipt held for position 2 no
    longer matches what sits there — and the guardian holds the only copy of
    the old digest.
    """
    led, rs = issue_all(Ledger(), LB, BEN, guardians(), 3)
    mine = held_by(rs, "g-mother", LB)

    # Rebuild the lane with one entry's principal changed, chaining honestly.
    fld = Field(LB, BEN, "chair", Rung.L3, payload="x", instruction="y")
    edges = [Edge("guardian_of", "g-mother", BEN, T0, created_at=T0)]
    rebuilt = Log()
    for i in range(3):
        who = "someone-else" if i == 1 else "g-mother"
        rebuilt = rebuilt.record(serve(fld, Principal("g-mother"), edges, T0),
                                 principal_id=who, subject_id=BEN,
                                 field_name="chair", at=T0)

    assert rebuilt.verify()[0], (
        "the rebuilt chain should verify perfectly — that is what makes this the "
        "attack worth defending against"
    )
    bad = contradictions(rebuilt, mine)
    assert bad and any("different entry" in b for b in bad), (
        "a coherently rewritten log matched every receipt"
    )


def test_incoherent_tampering_is_caught_by_verification_not_by_receipts():
    """The other half of the division of labour, asserted so neither mechanism
    is mistaken for covering the whole surface."""
    led, rs = issue_all(Ledger(), LB, BEN, guardians(), 3)
    log = led.log_for(LB)
    sloppy = Log(log.entries[:1] +
                 (dataclasses.replace(log.entries[1], principal_id="someone-else"),) +
                 log.entries[2:])
    assert not sloppy.verify()[0], "verification missed an edited entry"
    assert contradictions(sloppy, held_by(rs, "g-mother", LB)) == (), (
        "receipts compare digests and do not recompute them; if this changes, "
        "say so rather than deleting the assertion"
    )


def test_an_honest_log_contradicts_nothing():
    led, rs = issue_all(Ledger(), LB, BEN, guardians(), 3)
    assert contradictions(led.log_for(LB), held_by(rs, "g-mother", LB)) == ()


# --- authenticity, claimed no more strongly than it is --------------------


def test_a_receipt_carries_a_tag_the_issuer_can_check():
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 1)
    assert all(authentic(r, KEY) for r in rs)
    forged = dataclasses.replace(rs[0], position=99)
    assert not authentic(forged, KEY)
    assert not authentic(rs[0], b"a-different-key")


def test_the_receipt_carries_no_content_only_the_fact_of_a_record():
    """A receipt is handed to a person and must survive being handed to the
    wrong one. The digest is opaque; nothing about the entry travels.

    `issuance` joined this set on 2026-07-31 and is not content: it names what
    the receipt's own tag is worth, which the holder would otherwise have to
    assume. The set stays exact so the next field has to be argued for too.
    """
    fields = {f.name for f in dataclasses.fields(GuardianReceipt)}
    assert fields == {"lane_id", "position", "entry_digest", "issued_at",
                      "to_guardian", "tag", "issuance"}
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 1)
    assert "chair" not in repr(rs[0]) and "student-ben" not in repr(rs[0])


# --- what receipts CANNOT do ----------------------------------------------


def test_receipts_CANNOT_detect_an_entry_that_was_never_written_documented():
    """**A limitation, not a guarantee**, named so nobody later mistakes it for
    a bug and closes it by deleting the assertion.

    Receipts detect *removal*. They cannot detect *omission*: an entry the
    institution never wrote produces no receipt, and a guardian holding 1..N
    cannot tell whether N is everything. This is the attack that actually works
    against a record its author controls, and no witness scheme fixes it —
    receipts corroborate, they do not stand alone.
    """
    honest, rs_honest = issue_all(Ledger(), LB, BEN, guardians(), 3)
    partial, rs_partial = issue_all(Ledger(), LB, BEN, guardians(), 2)

    mine_h = held_by(rs_honest, "g-mother", LB)
    mine_p = held_by(rs_partial, "g-mother", LB)

    assert gaps(mine_h) == () and gaps(mine_p) == (), (
        "if a gap ever appears here, omission has become detectable and this "
        "test should be rewritten rather than deleted"
    )
    assert contradictions(honest.log_for(LB), mine_h) == ()
    assert contradictions(partial.log_for(LB), mine_p) == ()


def test_the_tag_is_not_claimed_to_be_a_signature_documented():
    """The stdlib has no asymmetric primitive, so issuance is HMAC-tagged. That
    lets the institution verify its own receipts and makes a mismatch a
    contradiction it must explain — but a third party cannot distinguish
    institution-issued from institution-forged, because anyone with the key can
    mint either.

    Asserted here so the module's evidentiary weight is never overstated: it
    comes from **distribution and adversity**, not from unforgeable maths.
    """
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 1)
    r = rs[0]
    minted = dataclasses.replace(
        r, position=42,
        tag=HmacTagger(KEY).tag("\x1f".join(
            [r.lane_id, "42", r.entry_digest, r.issued_at.isoformat(),
             r.to_guardian, r.issuance.value])))
    assert authentic(minted, KEY), (
        "anyone holding the key can mint a receipt; that is the known limit"
    )


# --- which scheme issued it, and what that is worth -----------------------


def test_a_receipt_says_what_its_own_tag_is_worth():
    """A holder told nothing assumes the strongest reading. So the weaker
    property is a field, it is on the printed slip in words, and it is covered
    by the tag."""
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 1)
    r = rs[0]
    assert r.issuance is Issuance.SELF_VERIFIABLE
    assert r.scheme == "hmac-sha256"
    page = receipt_text(r).text
    assert "Someone else cannot" in page
    assert "hmac-sha256" in page


def test_relabelling_a_receipt_as_attributable_breaks_its_tag():
    """The issuance claim is inside the tagged material, so a receipt cannot be
    promoted after issue by editing one field."""
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 1)
    promoted = dataclasses.replace(rs[0], issuance=Issuance.ATTRIBUTABLE)
    try:
        authentic(promoted, KEY)
    except Uncheckable:
        return          # the verifier refuses before it even checks the maths
    raise AssertionError("a relabelled receipt was checked as if nothing changed")


def test_the_issuance_claim_is_inside_the_tag():
    """Relabelling the receipt *and* the verifier to match still fails, because
    what a receipt says it is worth is part of what was tagged. Without this the
    seventh field would be a caption anyone could edit."""
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 1)
    promoted = dataclasses.replace(rs[0], issuance=Issuance.ATTRIBUTABLE)
    lenient = HmacTagger(KEY, "hmac-sha256", Issuance.ATTRIBUTABLE)
    assert not authentic(promoted, lenient), (
        "a receipt was promoted to attributable by editing a field"
    )
    assert authentic(rs[0], HmacTagger(KEY)), "the ordinary case stopped working"


def test_a_scheme_a_verifier_cannot_read_is_unknown_not_forged():
    """Rule 13 at a verifier. `False` would report *cannot check* and *forged*
    with the same word, and the difference is the whole of the question."""
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 1)
    signed = dataclasses.replace(rs[0], tag="ed25519:" + "0" * 128,
                                 issuance=Issuance.ATTRIBUTABLE)
    try:
        authentic(signed, KEY)
    except Uncheckable as exc:
        assert "unknown, not a mismatch" in str(exc)
        return
    raise AssertionError("an unreadable scheme came back as an ordinary boolean")


def test_an_absent_asymmetric_signer_refuses_rather_than_falling_back():
    """**The dependency §18 item 15 carries.** A deployment that asks for the
    attributable path and does not have the primitive must be told so. A silent
    HMAC underneath would make the two indistinguishable at every call site, and
    the first place anyone noticed would be a dispute."""
    led = write(Ledger(), LB, BEN, 1)
    try:
        issue(led, LB, BEN, guardians(), T0, signer=AsymmetricUnavailable())
    except NoSigner as exc:
        assert "not quietly issued under a weaker scheme" in str(exc)
        return
    raise AssertionError("an unavailable signer issued something anyway")


def test_issuance_is_chosen_rather_than_defaulted():
    """A key or a signer, never both and never neither: which scheme issued a
    receipt is always something somebody decided."""
    led = write(Ledger(), LB, BEN, 1)
    for kwargs in ({}, {"key": KEY, "signer": HmacTagger(KEY)}):
        try:
            issue(led, LB, BEN, guardians(), T0, **kwargs)
        except ValueError:
            continue
        raise AssertionError(f"issue() accepted {kwargs or 'neither'}")


def test_a_signer_and_a_bare_key_agree():
    """The seam is not a second implementation: passing the key is passing an
    `HmacTagger` around it."""
    led = write(Ledger(), LB, BEN, 1)
    by_key = issue(led, LB, BEN, guardians(), T0, KEY)
    by_signer = issue(led, LB, BEN, guardians(), T0, signer=HmacTagger(KEY))
    assert by_key == by_signer and by_key


def test_the_attributable_path_is_ABSENT_here_documented_not_hidden():
    """**A limitation, not a bug**, and it is the open half of §18 item 15.

    This tree performs one issuance scheme and it is symmetric. Ed25519 is a
    dependency decision — the stdlib has no asymmetric primitive, vendoring
    curve arithmetic into a records module would be the worst version of §16's
    copied pair, and CI installs nothing. So the socket exists (`Signer`,
    `Issuance.ATTRIBUTABLE`) and the plug does not, and `tools/conform.py`
    reports that as its own row rather than leaving it to be inferred.
    """
    assert schemes() == ("hmac-sha256",), (
        "if an asymmetric scheme has landed, this test should be rewritten "
        "rather than deleted, and §18 item 15's dependency struck"
    )
    assert Issuance.ATTRIBUTABLE.limit          # the words are ready for it
    assert AsymmetricUnavailable().issuance is Issuance.UNAVAILABLE


def test_the_module_is_not_broken_shut():
    _led, rs = issue_all(Ledger(), LB, BEN, guardians(), 2)
    assert len(rs) == 4 and all(authentic(r, KEY) for r in rs)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
