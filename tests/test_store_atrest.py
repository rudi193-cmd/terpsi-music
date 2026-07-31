"""Sealing, erasure and rotation against a real store, not against a memory.

`records/atrest.py` was built and tested with no store under it, and
`docs/AT-REST.md` says so in rule 18's words: *"a mechanism and a ledger of key
state. Not a gate. Nothing routes through it, because there is no store."*
There is one now. This is the file where that sentence stops being true — every
walkthrough `tests/test_atrest.py` performs in memory is performed here with
PostgreSQL underneath, reading the ciphertext back out of the database rather
than out of a variable.

Four of `docs/PLAN-STORE.md`'s forbidden acts are attempted here, and each
refusal asserts on the **guard named in the error**:

* a payload column read in the clear — the third clause of the acceptance
  list's first item, which S-1 recorded as S-3's because nothing was sealed yet;
* clear bytes written straight into the sealed column as `terpsi_app`, going
  round the seam entirely;
* a sealed row's envelope rewritten;
* a lane's erasure leaving the chain broken — attempted by checking that it does
  not, with `atrest.composes()` over rows read back from the live database.

Needs a database. No skip — see `tests/cluster.py`. Key material is minted per
test database by `cluster.Custody` and never written anywhere
(`tests/test_key_custody.py` is the tripwire).
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import (APP_PASSWORD, ClusterUnknown, Custody,  # noqa: E402
                     Database, available, installed, refused_by, report)

from records import atrest  # noqa: E402
from records.disclosure import Ledger  # noqa: E402
from records.rungs import Rung  # noqa: E402
from records.serving import Edge, Field, Grant, Outcome, Principal, serve  # noqa: E402

from store.narration import serve_field, unproject  # noqa: E402
from store.reading import EnvelopeBroken, envelope, envelope_columns_sql  # noqa: E402
from store.sealing_plan import envelope_columns  # noqa: E402
from store.writing import insert_draft  # noqa: E402

AT = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)

BEN = uuid.UUID("11111111-1111-1111-1111-111111111111")
CARA = uuid.UUID("11111111-2222-2222-2222-222222222222")
ANN = uuid.UUID("11111111-3333-3333-3333-333333333333")
LBEN = uuid.UUID("22222222-1111-1111-1111-111111111111")
LCARA = uuid.UUID("22222222-2222-2222-2222-222222222222")

BENS_NOTE = b'{"kind":"medical_note","body":"peanut allergy; epi-pen in the case"}'
CARAS_NOTE = b'{"kind":"medical_note","body":"asthma inhaler before rehearsal"}'

SELECT_ENVELOPE = (
    f"SELECT entry_id, lane_id, {envelope_columns_sql('payload')}, payload "
    "FROM lane_entry WHERE lane_id = %s ORDER BY entry_id")


def seed(owner):
    with owner.cursor() as cur:
        for who, born in ((BEN, "2010-05-01"), (CARA, "2012-09-14"),
                          (ANN, "1979-02-02")):
            cur.execute("INSERT INTO person VALUES (%s,%s,now(),now(),NULL)",
                        (who, born))
        for lane, subject in ((LBEN, BEN), (LCARA, CARA)):
            cur.execute("INSERT INTO lane VALUES (%s,%s,%s,now(),now(),now(),NULL)",
                        (lane, subject, "everything, as CSV, on request"))
        cur.execute(
            "INSERT INTO edge VALUES (%s,'guardian_of',%s,%s,NULL,'enrolment "
            "form',now(),now() - interval '1 year',NULL)",
            (uuid.uuid4(), ANN, LBEN))
    owner.commit()


def an_entry(lane, payload, **over):
    body = dict(entry_id=uuid.uuid4(), lane_id=lane, kind="medical_note",
                payload=payload, author_id=ANN, created_at=AT, valid_at=AT)
    body.update(over)
    return body


def custody_over(*lanes):
    return Custody(*[str(lane) for lane in lanes], at=AT)


def sealed_rows(conn, lane, custody=None):
    """Every sealed payload for a lane, rebuilt from the **database's** bytes.

    Deliberately not the objects the write returned: the claim under test is
    about what is on disk, and comparing the seam's own output to itself would
    be a round trip through a variable.
    """
    with conn.cursor() as cur:
        cur.execute(SELECT_ENVELOPE, (lane,))
        rows = cur.fetchall()
    out = []
    for entry_id, lane_id, sealed, key_id, scheme, sealed_at, clear in rows:
        assert clear is None, (
            f"{entry_id} carries a clear payload; migration 004 tombstoned it")
        out.append(envelope(lane_id=str(lane_id), sealed=sealed, key_id=key_id,
                            scheme=scheme, sealed_at=sealed_at))
    return out


def write_both(app, custody):
    for lane, note in ((LBEN, BENS_NOTE), (LCARA, CARAS_NOTE)):
        insert_draft(app, "lane_entry", an_entry(lane, note),
                     lane_key=custody.key(lane), at=AT)
    app.commit()


# --- the payload is ciphertext on disk --------------------------------------


def test_a_payload_written_through_the_seam_is_ciphertext_in_the_database():
    """The forbidden act S-1 could not attempt: **a payload column read in the
    clear.** Read as the app role, straight out of the table, with no key."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN)
            insert_draft(app, "lane_entry", an_entry(LBEN, BENS_NOTE),
                         lane_key=custody.key(LBEN), at=AT)
            app.commit()

            with app.cursor() as cur:
                cur.execute("SELECT payload, payload_sealed, payload_scheme "
                            "FROM lane_entry")
                clear, ciphertext, scheme = cur.fetchone()
            assert clear is None
            assert scheme in atrest.OPENABLE
            assert b"peanut" not in bytes(ciphertext)
            assert b"epi-pen" not in bytes(ciphertext)
            assert bytes(ciphertext)[:5] == b"gAAAA"

            # And the whole table, byte for byte: no column anywhere holds it.
            with app.cursor() as cur:
                cur.execute("SELECT lane_entry::text FROM lane_entry")
                whole = cur.fetchone()[0]
            assert "peanut" not in whole, (
                "the payload is readable somewhere in the row: " + whole[:200])
        finally:
            app.close()
            owner.close()


def test_the_read_returns_an_envelope_and_the_key_holder_opens_it():
    """Reads return `Sealed`; unsealing is the caller's, with the key."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN)
            insert_draft(app, "lane_entry", an_entry(LBEN, BENS_NOTE),
                         lane_key=custody.key(LBEN), at=AT)
            app.commit()

            got = sealed_rows(app, LBEN)
            assert len(got) == 1
            assert isinstance(got[0], atrest.Sealed)
            opened = atrest.unseal(got[0], keyring=custody.keyring,
                                   master=custody.master)
            assert opened.opened, opened
            assert opened.plaintext == BENS_NOTE
        finally:
            app.close()
            owner.close()


def test_the_keyring_without_the_master_says_the_key_is_available_not_missing():
    """Rule 13 across the store boundary: *held under a master nobody offered*
    is not *unreadable*, and a guardian is owed the difference."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN)
            insert_draft(app, "lane_entry", an_entry(LBEN, BENS_NOTE),
                         lane_key=custody.key(LBEN), at=AT)
            app.commit()
            got = atrest.unseal(sealed_rows(app, LBEN)[0], keyring=custody.keyring)
            assert got.state is atrest.Readable.MASTER_MISMATCH, got
            assert "was not asked for" in got.reason
        finally:
            app.close()
            owner.close()


def test_a_row_moved_into_another_lane_reads_as_misbound_not_as_that_lanes():
    """The envelope has no `lane_id` column and this is why.

    `Sealed` is rebuilt with the **row's** lane, so a payload relabelled by
    moving the row authenticates against a header naming the lane it was sealed
    for and refuses. A duplicate `payload_lane_id` column would have moved with
    the row and opened.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN, LCARA)
            insert_draft(app, "lane_entry", an_entry(LBEN, BENS_NOTE),
                         lane_key=custody.key(LBEN), at=AT)
            app.commit()
            with owner.cursor() as cur:
                cur.execute("UPDATE lane_entry SET lane_id = %s", (LCARA,))
            owner.commit()

            relabelled = sealed_rows(app, LCARA)[0]
            assert relabelled.lane_id == str(LCARA)
            got = atrest.unseal(relabelled, keyring=custody.keyring,
                                master=custody.master)
            assert got.state is atrest.Readable.MISBOUND, got
            assert "relabelled" in got.reason or "one lane, one key" in got.reason
        finally:
            app.close()
            owner.close()


# --- forbidden: clear bytes into the sealed column, as the app role ---------


def test_the_app_role_cannot_insert_clear_bytes_into_the_sealed_column():
    """**Going round the seam entirely**, which is the act that matters: the
    adapter cannot spell a clear payload, and this is a hand-written `INSERT`
    as `terpsi_app` that tries anyway. Refused by the constraint **named**."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            def attack():
                with app.cursor() as cur:
                    cur.execute(
                        "INSERT INTO lane_entry (entry_id, lane_id, kind, "
                        " payload_sealed, payload_key_id, payload_scheme, "
                        " payload_sealed_at, author_id, created_at, valid_at) "
                        "VALUES (%s,%s,'medical_note',%s,'lane-1','fernet-v1',"
                        " now(),%s,now(),now())",
                        (uuid.uuid4(), LBEN, BENS_NOTE, ANN))
            refused_by(attack, "lane_entry_payload_sealed_is_ciphertext")
            app.rollback()

            def in_the_clear_column():
                with app.cursor() as cur:
                    cur.execute(
                        "INSERT INTO lane_entry (entry_id, lane_id, kind, "
                        " payload, author_id, created_at, valid_at) "
                        "VALUES (%s,%s,'medical_note','{}'::jsonb,%s,now(),now())",
                        (uuid.uuid4(), LBEN, ANN))
            refused_by(in_the_clear_column, "lane_entry_payload_is_tombstoned")
            app.rollback()

            def half_an_envelope():
                got = atrest.seal_bytes(BENS_NOTE, lane_key=custody.key(LBEN),
                                        at=AT)
                with app.cursor() as cur:
                    cur.execute(
                        "INSERT INTO lane_entry (entry_id, lane_id, kind, "
                        " payload_sealed, author_id, created_at, valid_at) "
                        "VALUES (%s,%s,'medical_note',%s,%s,now(),now())",
                        (uuid.uuid4(), LBEN, got.ciphertext, ANN))
            custody = custody_over(LBEN)
            refused_by(half_an_envelope, "lane_entry_payload_envelope_is_whole")
            app.rollback()

            def a_scheme_this_build_cannot_open():
                got = atrest.seal_bytes(BENS_NOTE, lane_key=custody.key(LBEN),
                                        at=AT)
                with app.cursor() as cur:
                    cur.execute(
                        "INSERT INTO lane_entry (entry_id, lane_id, kind, "
                        " payload_sealed, payload_key_id, payload_scheme, "
                        " payload_sealed_at, author_id, created_at, valid_at) "
                        "VALUES (%s,%s,'medical_note',%s,'lane-1','rot13',"
                        " now(),%s,now(),now())",
                        (uuid.uuid4(), LBEN, got.ciphertext, ANN))
            refused_by(a_scheme_this_build_cannot_open,
                       "lane_entry_payload_scheme_is_openable")
            app.rollback()

            assert app.execute("SELECT count(*) FROM lane_entry").fetchone()[0] == 0
        finally:
            app.rollback()
            app.close()
            owner.close()


def test_a_legitimate_sealed_write_still_lands():
    """A guard that refuses everything is not a guard. Four constraints refused
    four acts above; this is the act they must not refuse."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN)
            got = insert_draft(app, "lane_entry", an_entry(LBEN, BENS_NOTE),
                               lane_key=custody.key(LBEN), at=AT,
                               returning="entry_id")
            app.commit()
            assert got is not None
            assert app.execute(
                "SELECT count(*) FROM lane_entry").fetchone()[0] == 1
        finally:
            app.close()
            owner.close()


def test_a_sealed_rows_envelope_cannot_be_rewritten_even_by_the_owner():
    """The hole migration 004 found and closed, attacked as the **owner**,
    because a privilege check runs ahead of every trigger and would otherwise
    stand in for it."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN)
            entry = insert_draft(app, "lane_entry", an_entry(LBEN, BENS_NOTE),
                                 lane_key=custody.key(LBEN), at=AT,
                                 returning="entry_id")
            app.commit()
            with owner.cursor() as cur:
                cur.execute("UPDATE lane_entry SET seal_state='sealed', "
                            "sealed_by=%s WHERE entry_id=%s", (ANN, entry))
            owner.commit()

            for column in envelope_columns("payload"):
                def attack(column=column):
                    with owner.cursor() as cur:
                        cur.execute(
                            f"UPDATE lane_entry SET {column} = NULL "
                            "WHERE entry_id = %s", (entry,))
                refused_by(attack, "insert-only history")
                owner.rollback()

            # Refusal 3's dated ending still works, or the trigger is a freeze.
            with owner.cursor() as cur:
                cur.execute("UPDATE lane_entry SET invalid_at = %s "
                            "WHERE entry_id = %s",
                            (AT + timedelta(days=1), entry))
            owner.commit()
        finally:
            app.close()
            owner.close()


# --- serve() at L3+ never needs the payload --------------------------------


def test_serve_at_L4_completes_without_a_single_unseal():
    """**The design's point, asserted rather than argued.**

    §5's `L3`+ rule serves a derived instruction and never the payload, so a
    store that cannot open a payload can still answer every question the
    resolver asks. If that were untrue, the seal would cost a key lookup on
    every read and somebody would eventually remove it.

    `records.atrest`'s three opening verbs are instrumented and required to be
    called zero times while a real `L4` decision is made over a row whose
    payload is ciphertext in the database.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN)
            insert_draft(app, "lane_entry", an_entry(LBEN, BENS_NOTE),
                         lane_key=custody.key(LBEN), at=AT)
            app.commit()

            calls = []
            originals = {name: getattr(atrest, name)
                         for name in ("unseal", "unseal_with", "unwrap")}

            def counted(name, fn):
                def wrapper(*a, **k):
                    calls.append(name)
                    return fn(*a, **k)
                return wrapper

            for name, fn in originals.items():
                setattr(atrest, name, counted(name, fn))
            try:
                # The row, read the way the store reads it: predicates clear,
                # payload absent. `Field.payload` is None because the store
                # never had it, not because it was dropped.
                with app.cursor() as cur:
                    cur.execute("SELECT lane_id, kind FROM lane_entry")
                    lane_id, kind = cur.fetchone()
                fld = Field(lane_id=str(lane_id), subject_id=str(BEN), name=kind,
                            rung=Rung.L4, category="health", payload=None,
                            instruction="a health note is on file; ask the nurse")
                began = AT - timedelta(days=365)
                edge = Edge("guardian_of", str(ANN), str(BEN), began,
                            created_at=began)
                grant = Grant(str(ANN), str(LBEN), Rung.L4, str(ANN), began,
                              AT + timedelta(days=30), created_at=began,
                              purpose="health")
                got = serve(fld, Principal(str(ANN), frozenset()), [edge], AT,
                            grants=[grant])
            finally:
                for name, fn in originals.items():
                    setattr(atrest, name, fn)

            assert got.outcome is Outcome.INSTRUCTION, got
            assert got.value == "a health note is on file; ask the nurse"
            assert calls == [], (
                f"serve() at L4 opened a payload {len(calls)} time(s): {calls}. "
                "The L3+ path is supposed to need the instruction and nothing "
                "else, which is what makes sealing free at read time")
        finally:
            app.close()
            owner.close()


# --- erasure, against the real store ---------------------------------------


def narrate_a_read(app, lane, subject):
    """One disclosure entry per lane, written the way the store writes them."""
    from records.serving import Serving

    return serve_field(
        app, query="SELECT entry_id FROM lane_entry WHERE lane_id = %s",
        params=(lane,),
        decide=lambda rows: Serving(Outcome.INSTRUCTION, "a note is on file",
                                    Rung.L4, "L4 with edge and purpose"),
        principal_id=str(ANN), subject_id=str(subject), lane_id=str(lane),
        field_name="medical_note", at=AT, recipient="the school nurse",
        authority="guardian_of edge")


def ledger_from_store(app, *lanes):
    """`records/disclosure.Ledger` rebuilt from `disclosure_log` rows.

    The chain under test is the one on disk, not one this test assembled: the
    claim is that the *store's* chain survives an erasure of the *store's* keys.
    """
    subjects = {str(LBEN): str(BEN), str(LCARA): str(CARA)}
    lanes_out = []
    for lane in lanes:
        with app.cursor() as cur:
            cur.execute(
                "SELECT occurred_at, principal_id, lane_id, what, recipient, "
                "authority, prev_hash, hash FROM disclosure_log "
                "WHERE lane_id = %s ORDER BY seq", (lane,))
            rows = cur.fetchall()
        entries = tuple(unproject(
            dict(occurred_at=r[0], principal_id=r[1], lane_id=r[2], what=r[3],
                 recipient=r[4], authority=r[5], prev_hash=r[6], hash=r[7]),
            subject_id=subjects[str(lane)]) for r in rows)
        from records.disclosure import Log
        lanes_out.append((str(lane), Log(entries)))
    return Ledger(tuple(sorted(lanes_out)))


def test_destroying_a_lanes_key_leaves_the_chain_verifying_over_the_live_store():
    """**F3's walkthrough, with the store underneath.**

    §5's hardest paragraph: a member's transitions are links in a chain the
    whole corps depends on, and per-subject erasure has to be possible anyway.
    `atrest.composes()` is the middle for that pair, and until now it had only
    ever been given payloads and a ledger built in memory. Here both come out of
    PostgreSQL: the sealed bytes are read back from `lane_entry`, the chain is
    rebuilt from `disclosure_log`, and the verdict must be `COMPOSES`.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN, LCARA)
            write_both(app, custody)
            for lane, subject in ((LBEN, BEN), (LCARA, CARA)):
                assert narrate_a_read(app, lane, subject).state.value == "served"

            before = ledger_from_store(app, LBEN, LCARA)
            ok, why = before.verify()
            assert ok, why
            anchor = dict(before.anchors())[str(LBEN)]

            bens = sealed_rows(app, LBEN)
            caras = sealed_rows(app, LCARA)
            assert bens and caras

            # Everything opens before the erasure, or the erasure proves nothing.
            assert atrest.unseal(bens[0], keyring=custody.keyring,
                                 master=custody.master).plaintext == BENS_NOTE

            keyring = atrest.destroy(
                custody.keyring, lane_id=str(LBEN), at=AT,
                by="Ann Whitfield", reason="records inspection request withdrawn "
                                          "and the family left the program")

            # The rows are untouched. An erasure that deleted them would be
            # refusal 3's forbidden shape and would also make the next assertion
            # vacuous, so both facts are checked.
            after = sealed_rows(app, LBEN)
            assert [s.ciphertext for s in after] == [s.ciphertext for s in bens]

            got = atrest.composes(ledger_from_store(app, LBEN, LCARA), keyring,
                                  lane_id=str(LBEN), sealed=after,
                                  master=custody.master, anchor=anchor)
            assert got.state is atrest.Composition.COMPOSES, got
            assert got.chain_ok and got.checked == len(after)
            assert got.unreadable == len(after) and got.still_readable == 0

            # Ben's payloads are ciphertext nobody can open; Cara's still open.
            for s in after:
                opening = atrest.unseal(s, keyring=keyring, master=custody.master)
                assert opening.state is atrest.Readable.KEY_DESTROYED, opening
                assert "Ann Whitfield" in opening.reason
                assert opening.plaintext is None
            assert atrest.unseal(caras[0], keyring=keyring,
                                 master=custody.master).plaintext == CARAS_NOTE

            # And the erasure record outlives the key it destroyed.
            erasure = keyring.erasure_for_lane(str(LBEN))
            assert erasure.by == "Ann Whitfield" and erasure.reason
            assert erasure.key_ids
        finally:
            app.close()
            owner.close()


def test_the_composition_notices_when_the_stores_chain_is_broken():
    """`COMPOSES` has to be a finding it can fail to reach, or it is a label.

    The erasure is real; the chain is then damaged in the database and the
    composition must report `CHAIN_BROKEN` rather than the key half alone.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN, LCARA)
            write_both(app, custody)
            for lane, subject in ((LBEN, BEN), (LCARA, CARA)):
                narrate_a_read(app, lane, subject)
                narrate_a_read(app, lane, subject)

            rows = sealed_rows(app, LBEN)
            keyring = atrest.destroy(custody.keyring, lane_id=str(LBEN), at=AT,
                                     by="Ann Whitfield", reason="court order")

            # disclosure_log is append-only and the app role holds no UPDATE, so
            # the damage is done as the owner with the trigger disabled — the
            # only way to produce a broken chain at all, which is itself the
            # store's answer to "could this happen by accident".
            with owner.cursor() as cur:
                cur.execute("ALTER TABLE disclosure_log DISABLE TRIGGER USER")
                cur.execute("UPDATE disclosure_log SET what = 'nothing | L4 | "
                            "instruction' WHERE lane_id = %s", (LBEN,))
                cur.execute("ALTER TABLE disclosure_log ENABLE TRIGGER USER")
            owner.commit()

            got = atrest.composes(ledger_from_store(app, LBEN, LCARA), keyring,
                                  lane_id=str(LBEN), sealed=rows,
                                  master=custody.master)
            assert got.state is atrest.Composition.CHAIN_BROKEN, got
            assert not got.chain_ok
            assert "§5's resolution requires both" in got.reason

            # Cara's lane is untouched by both halves.
            cara_ok, why = ledger_from_store(app, LCARA).log_for(str(LCARA)).verify()
            assert cara_ok, why
        finally:
            app.close()
            owner.close()


def test_a_lane_whose_keys_vanished_with_no_dated_act_is_a_finding():
    """`UNRECORDED`, over the live store. A key that disappeared and one a named
    person destroyed on a date are different answers to a guardian asking why a
    record will not open."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN, LCARA)
            write_both(app, custody)
            narrate_a_read(app, LBEN, BEN)

            # The wrappings dropped with no Erasure beside them — a restore from
            # a partial backup, or a keyring edited by hand.
            lost = atrest.Keyring(
                tuple(w for w in custody.keyring.wrappings
                      if w.lane_id != str(LBEN)),
                custody.keyring.erasures, custody.keyring.escrow)
            got = atrest.composes(ledger_from_store(app, LBEN), lost,
                                  lane_id=str(LBEN),
                                  sealed=sealed_rows(app, LBEN),
                                  master=custody.master)
            assert got.state is atrest.Composition.UNRECORDED, got
        finally:
            app.close()
            owner.close()


def test_a_lane_still_holding_its_keys_is_not_erased():
    """The control. `NOT_ERASED` must be reachable, or `COMPOSES` above is
    satisfied by a function that says `COMPOSES` for everything."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN, LCARA)
            write_both(app, custody)
            narrate_a_read(app, LBEN, BEN)
            got = atrest.composes(ledger_from_store(app, LBEN), custody.keyring,
                                  lane_id=str(LBEN),
                                  sealed=sealed_rows(app, LBEN),
                                  master=custody.master)
            assert got.state is atrest.Composition.NOT_ERASED, got
            assert got.still_readable == 1 and got.unreadable == 0
        finally:
            app.close()
            owner.close()


# --- rotation over the store ------------------------------------------------


def test_rotating_the_master_reseals_nothing_and_the_live_rows_still_open():
    """**The thing everyone gets wrong**, over real rows.

    A sealed payload names its *lane key* and never the master, so rotating the
    master is a new wrapping and nothing else: the cost is the number of lanes,
    not the number of records. `tests/test_atrest.py` compares the objects; this
    compares the **bytes in the table** before and after, which is the claim that
    matters — a rotation that quietly rewrote history would also have had to get
    past `lane_entry_sealed_is_history`.
    """
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN, LCARA)
            write_both(app, custody)

            with app.cursor() as cur:
                cur.execute("SELECT entry_id, payload_sealed, payload_key_id "
                            "FROM lane_entry ORDER BY entry_id")
                before = cur.fetchall()

            second = atrest.new_master()
            rotated = atrest.rewrap(custody.keyring, was=custody.master,
                                    now=second, at=AT)

            with app.cursor() as cur:
                cur.execute("SELECT entry_id, payload_sealed, payload_key_id "
                            "FROM lane_entry ORDER BY entry_id")
                after = cur.fetchall()
            assert before == after, "a master rotation moved a payload"

            # Every live row opens under the new master and not under the old.
            for lane, note in ((LBEN, BENS_NOTE), (LCARA, CARAS_NOTE)):
                got = sealed_rows(app, lane)[0]
                assert atrest.unseal(got, keyring=rotated,
                                     master=second).plaintext == note
                stale = atrest.unseal(got, keyring=rotated, master=custody.master)
                assert stale.state is atrest.Readable.MASTER_MISMATCH, stale

            # And the rotation carries no escrow forward — the shares held for
            # the old master do not reconstruct the new one.
            state, why = atrest.escrow_state(rotated, master_key_id=second.key_id,
                                             at=AT)
            assert state is atrest.EscrowState.ABSENT, why
        finally:
            app.close()
            owner.close()


def test_a_forward_only_lane_rotation_leaves_last_seasons_rows_readable():
    """§5's cheap, honest revocation, over the store: a new lane key is minted,
    the old wrapping is kept, and rows sealed last season still open — which is
    correct for the graduated senior's parent who legitimately saw them."""
    with Database() as db:
        owner, app = installed(db)
        seed(owner)
        try:
            custody = custody_over(LBEN)
            insert_draft(app, "lane_entry", an_entry(LBEN, BENS_NOTE),
                         lane_key=custody.key(LBEN), at=AT)
            app.commit()
            old_rows = sealed_rows(app, LBEN)

            keyring, fresh = atrest.rotate_lane_key(
                custody.keyring, lane_id=str(LBEN), master=custody.master, at=AT)
            later = AT + timedelta(days=200)
            insert_draft(app, "lane_entry",
                         an_entry(LBEN, b'{"kind":"note","body":"this season"}',
                                  created_at=later, valid_at=later),
                         lane_key=fresh, at=later)
            app.commit()

            assert atrest.unseal(old_rows[0], keyring=keyring,
                                 master=custody.master).plaintext == BENS_NOTE
            keys = {s.key_id for s in sealed_rows(app, LBEN)}
            assert len(keys) == 2, "the rotation did not produce a second key id"
        finally:
            app.close()
            owner.close()


# --- the store's own error channels, over the sealed columns ----------------


def test_half_an_envelope_read_back_is_a_finding_not_an_absent_payload():
    """The DDL makes it unwritable, so reaching it means the row came from
    somewhere else. Raised rather than returned as *no payload* (rule 13)."""
    try:
        envelope(lane_id=str(LBEN), sealed=b"gAAAA" + b"x" * 200,
                 key_id=None, scheme="fernet-v1", sealed_at=AT)
    except EnvelopeBroken as exc:
        assert "envelope_is_whole" in str(exc), exc
    else:
        raise AssertionError("half an envelope read as a payload")

    assert envelope(lane_id=str(LBEN), sealed=None, key_id=None, scheme=None,
                    sealed_at=None) is None


if __name__ == "__main__":
    ok, why = True, ""
    try:
        ok, why = available()
    except ClusterUnknown as exc:  # pragma: no cover
        ok, why = False, str(exc)
    tests = sorted((n, f) for n, f in globals().items()
                   if n.startswith("test_") and callable(f))
    if not ok:
        raise SystemExit(report("test_store_atrest", 0, len(tests), unknown=why))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(report("test_store_atrest", failures, len(tests)))
