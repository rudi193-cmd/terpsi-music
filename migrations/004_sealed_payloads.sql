-- 004_sealed_payloads.sql
--
-- Migration 004. The at-rest sealing seam lands on the real store: the payload
-- columns §5 seals gain their sealed form, and the clear column they replace is
-- tombstoned rather than dropped.
--
-- Governed by docs/PLAN-STORE.md decision 3, docs/AT-REST.md, and
-- docs/ARCHITECTURE.md §5. Where this file and those disagree, they win and this
-- file is the defect. records/atrest.py is the mechanism and is not
-- reimplemented here by a single byte -- these columns are its `Sealed` envelope
-- with the fields spelled as columns.
--
-- ============================================================================
-- THE COLUMN-BY-COLUMN DECISION, AND WHERE IT COMES FROM
--
-- It is NOT the list below. The list below is what the derivation printed.
--
--     python3 store/sealing_plan.py
--
-- reads the classification registry (tools/registry.py over this directory's
-- seed) and the DDL, and reports every classified column as SEALED or clear
-- with **every exclusion that applied**, by name. Rule 17: a hand-written set of
-- sealed columns is right on the day it is written and silently wrong after the
-- next migration, so the set is derived and this migration is checked against
-- it -- tests/test_sealing_plan.py fails if the two disagree in either
-- direction. A column added to a sealable table without a decision goes red
-- instead of quietly landing in the clear.
--
-- The seven exclusions, each a fact read off the tree:
--
--   RUNG_BELOW_L3     below SENSITIVITY.md's derive floor; served in the clear
--                     anyway, so sealing buys nothing and costs a key per read.
--   KEY               a PRIMARY KEY, UNIQUE or REFERENCES. Fernet is randomised;
--                     a sealed foreign key is not a weaker join, it is no join.
--   TEMPORAL          a timestamptz/date. §7 is interval predicates end to end.
--   EVALUATED_BY_DDL  named inside a CHECK on its own table. A CHECK reads the
--                     value, and ciphertext satisfies or fails one meaninglessly.
--   NOT_A_CONTAINER   the declared type is not jsonb -- see the judgement below.
--   NO_SINGLE_LANE    the table names zero or two lanes, so there is no one key
--                     to seal under (W-1: one lane, one key).
--   CHAIN_MATERIAL    the table carries prev_hash/hash. atrest.composes() asserts
--                     the chain still verifies after the lane key is destroyed;
--                     sealing chain material under that key breaks the exact
--                     property the erasure exists to preserve.
--
-- WHAT THE DERIVATION RETURNS TODAY: **one column of 116.**
--
--   lane_entry.payload   HEALTH/L4   jsonb   -> SEALED
--
-- Said plainly rather than rounded up (rule 17): this migration seals one
-- column, because one column in this schema is a payload and the other 115 are
-- predicates, keys, dates, chain links or vocabulary the store selects on. That
-- is decision 3's argument -- *"the store never needs to read payload contents
-- to answer a query"* -- and a schema where it sealed forty columns would be one
-- where the predicates had been sealed too and every read unsealed the store.
--
-- THE TWO JUDGEMENT CALLS, NAMED SO A READER DISAGREES EXPLICITLY
--
--   * lane_entry.kind is L3 and stays CLEAR, excluded only by NOT_A_CONTAINER.
--     001's own seed comment already concedes the disclosure -- "lane_entry.kind
--     is L3. 'medical_note' discloses without its payload." It stays clear
--     because sealing it makes "which entries are in this lane" unanswerable
--     without unsealing every row, which is decision 3's argument switched off.
--     What is bought back is §5's actual claim: the *contents* of the medical
--     note are ciphertext at rest, and the fact that one exists is not.
--
--   * declination.subject_matter is L5 and stays CLEAR, also excluded only by
--     NOT_A_CONTAINER. It is the column the criterion most nearly reaches -- one
--     lane, no chain, no CHECK, L5 throughout -- and it is text rather than
--     jsonb. Named here rather than left to be discovered: if a later maintainer
--     wants a second sealed column, this is the one, and it needs a decision
--     about how a predicate that reads 'media_release' finds it afterwards.
--
-- ============================================================================
-- THE ENVELOPE, AS COLUMNS
--
-- records/atrest.py's Sealed carries five fields. Four become columns:
--
--     ciphertext -> payload_sealed     bytea
--     key_id     -> payload_key_id     text
--     scheme     -> payload_scheme     text
--     sealed_at  -> payload_sealed_at  timestamptz
--
-- **lane_id deliberately does not.** The row already names its lane, and a
-- second copy is a pair with no middle (rule 12). store/reading.py rebuilds the
-- envelope with the row's own lane_id, so a row moved between lanes produces a
-- payload that authenticates against a header naming the other lane and fails as
-- MISBOUND -- which is stronger than a duplicate column, because the duplicate
-- would simply have moved with the row.
--
-- payload_sealed is NULLABLE, and that is stated rather than assumed: a
-- lane_entry with no payload at all is refused at the seam (store/writing.py's
-- PayloadMissing), not here. The DDL cannot require it without making every
-- direct psql INSERT in .github/workflows/tests.yml carry a real Fernet token,
-- and a schema job that mints key material to satisfy a NOT NULL is a worse
-- trade than a refusal one layer up, named where it lives (§7.2: say which).
--
-- ============================================================================
-- THE TOMBSTONE (rule 20)
--
--   Status:       RETIRED as a place to put a payload. Non-authoritative.
--                 Constrained to NULL; nothing may be written to it, ever.
--   Successor:    lane_entry.payload_sealed + _key_id + _scheme + _sealed_at.
--   Reason:       docs/PLAN-STORE.md decision 3. An L4 payload in the clear on
--                 disk is §10's R16 open at S1 the moment anything is at rest.
--   Contents:     none carried forward -- the column is empty in every instance
--                 this tree has produced (it is written only by test databases
--                 that are dropped). An instance holding rows would need a
--                 dated, named migration act to seal them, and this migration
--                 deliberately does not invent one: promotion to canonical is a
--                 human act (rule 11) and so is sealing history.
--   Why the stub still exists, rather than DROP COLUMN:
--     (a) refuse_sealed_mutation() in 002 names it by hand. Dropping the column
--         would silently shorten that trigger's list, which is the defect this
--         migration found and fixes below.
--     (b) tools/registry.py's seed carries a row for it, and the CI step "every
--         column is classified" checks the cluster against that seed. A dropped
--         column classified in the seed is the registry describing a schema the
--         cluster stopped having.
--     (c) A DROP is a delete with no dated record. The house rule is refusal 3's
--         and it does not stop at rows.
--
-- ============================================================================
-- WHAT THIS MIGRATION FOUND, AND FIXES
--
-- 002's comment claims: "Listing them means a column added without a thought for
-- this rule is refused by default, which is the direction that fails safe."
--
-- **That claim is false of the code as written, and this was confirmed against a
-- live PostgreSQL 16 before it was written down.** refuse_sealed_mutation()
-- compares a hand-written list of columns; a column NOT in the list is not
-- compared, so an UPDATE touching only that column passes the trigger and lands
-- on a sealed row. Adding a column fails OPEN, not safe.
--
-- This migration is the commit that would have shipped the hole: four new
-- columns holding the sealed payload of a sealed row, every one of them freely
-- rewritable by the owner role. So the function is replaced with the four names
-- added -- and, because a list that must be maintained by hand is the pair that
-- just drifted, tests/test_sealing_plan.py now reconciles the trigger's list
-- against the table's columns minus invalid_at. The next column added to
-- lane_entry goes red rather than becoming quietly editable.
--
-- ORDER, AS 001 AND 002 BOTH STATE IT
--
-- A BEFORE ROW trigger fires ahead of every CHECK, NOT NULL and foreign key on
-- the same row, so an attack asserting only "this was refused" can be satisfied
-- by a guard other than the one under test. Every constraint below is named, and
-- every attack on it in tests/test_store_atrest.py and in the workflow asserts on
-- the name.

BEGIN;

-- ------------------------------------------------------------ the envelope

ALTER TABLE lane_entry ADD COLUMN payload_sealed bytea;
ALTER TABLE lane_entry ADD COLUMN payload_key_id text;
ALTER TABLE lane_entry ADD COLUMN payload_scheme text;
ALTER TABLE lane_entry ADD COLUMN payload_sealed_at timestamptz;

-- An envelope is four fields or it is nothing. A row carrying ciphertext with
-- no key id names no key, and records/atrest.py's Keyring answers KEY_UNKNOWN
-- for it -- which is honest and useless. num_nonnulls, not a chain of ORs,
-- because the chain is where the fifth field would be forgotten.
ALTER TABLE lane_entry ADD CONSTRAINT lane_entry_payload_envelope_is_whole
    CHECK (num_nonnulls(payload_sealed, payload_key_id, payload_scheme,
                        payload_sealed_at) IN (0, 4));

ALTER TABLE lane_entry ADD CONSTRAINT lane_entry_payload_key_id_names_a_key
    CHECK (payload_key_id IS NULL OR length(btrim(payload_key_id)) > 0);

-- The scheme this build seals with. records/atrest.py's FERNET_V1, spelled here
-- because a CHECK cannot import it -- and reconciled by
-- tests/test_sealing_plan.py against atrest.OPENABLE, so the two cannot drift.
-- A later build sealing under aes-gcm-v2 changes this constraint in its own
-- migration; a payload naming a scheme this build cannot open must read as
-- SCHEME_UNKNOWN and never as corruption, which is atrest's rule and is why the
-- column exists at all rather than the scheme being implied.
ALTER TABLE lane_entry ADD CONSTRAINT lane_entry_payload_scheme_is_openable
    CHECK (payload_scheme IS NULL OR payload_scheme = 'fernet-v1');

-- **This is the constraint that makes a clear payload unrepresentable.**
--
-- The forbidden act is an application, or anything else holding a connection,
-- writing readable bytes into the sealed column -- store/writing.py's seam is
-- the path that cannot spell it, and this is what refuses the path that goes
-- round the seam entirely (a hand-written INSERT as terpsi_app).
--
-- A Fernet token is urlsafe-base64 over 0x80 || 8-byte timestamp || 16-byte IV
-- || ciphertext || 32-byte HMAC. The leading 0x80 with a timestamp whose high
-- bytes are zero encodes as the ASCII prefix 'gAAAA' (hex 6741414141), and the
-- minimum token is 1+8+16+16+32 = 73 bytes, which is 100 base64 characters. So
-- both facts are structural rather than a guess: '{"note":"broken arm"}' fails
-- the prefix, and a short blob fails the length.
--
-- What this is NOT: it is not a proof that the bytes decrypt, which no CHECK can
-- be. It is a proof that they are not plaintext, which is the act being refused.
-- Say which (§7.2).
ALTER TABLE lane_entry ADD CONSTRAINT lane_entry_payload_sealed_is_ciphertext
    CHECK (payload_sealed IS NULL OR (
        octet_length(payload_sealed) >= 100
        AND substring(payload_sealed from 1 for 5) = '\x6741414141'::bytea));

-- ------------------------------------------------------------- the tombstone

ALTER TABLE lane_entry ALTER COLUMN payload DROP NOT NULL;

ALTER TABLE lane_entry ADD CONSTRAINT lane_entry_payload_is_tombstoned
    CHECK (payload IS NULL);

COMMENT ON COLUMN lane_entry.payload IS
    'RETIRED 2026-07-31 by migration 004. Non-authoritative and constrained to '
    'NULL. Successor: payload_sealed/_key_id/_scheme/_sealed_at, the Sealed '
    'envelope of records/atrest.py. Kept rather than dropped because '
    'refuse_sealed_mutation() names it, the classification seed carries it, and '
    'a DROP is a delete with no dated record. See this migration''s header.';

COMMENT ON COLUMN lane_entry.payload_sealed IS
    'Ciphertext of the L4 payload, sealed under this lane''s key before INSERT '
    '(records/atrest.py::seal_bytes). The store never unseals: reads return the '
    'envelope and the caller holding the key opens it.';

-- ------------------------------------- 002's trigger, with the hole closed

-- Replaced rather than amended: the function is the list, and a second function
-- comparing the four new columns beside the old one would be two lists to keep
-- in step. tests/test_sealing_plan.py reconciles this list against the table.
CREATE OR REPLACE FUNCTION refuse_sealed_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.seal_state = 'sealed' THEN
            RAISE EXCEPTION
                'a sealed lane_entry is history and is not deletable; end it by '
                'setting invalid_at (refusal 3, rule 16)';
        END IF;
        RETURN OLD;
    END IF;

    IF OLD.seal_state <> 'sealed' THEN
        RETURN NEW;   -- a draft is the sidecar; it is the app's to amend
    END IF;

    IF NEW.entry_id          IS DISTINCT FROM OLD.entry_id
    OR NEW.lane_id           IS DISTINCT FROM OLD.lane_id
    OR NEW.referent_id       IS DISTINCT FROM OLD.referent_id
    OR NEW.kind              IS DISTINCT FROM OLD.kind
    OR NEW.payload           IS DISTINCT FROM OLD.payload
    OR NEW.payload_sealed    IS DISTINCT FROM OLD.payload_sealed
    OR NEW.payload_key_id    IS DISTINCT FROM OLD.payload_key_id
    OR NEW.payload_scheme    IS DISTINCT FROM OLD.payload_scheme
    OR NEW.payload_sealed_at IS DISTINCT FROM OLD.payload_sealed_at
    OR NEW.author_id         IS DISTINCT FROM OLD.author_id
    OR NEW.seal_state        IS DISTINCT FROM OLD.seal_state
    OR NEW.sealed_by         IS DISTINCT FROM OLD.sealed_by
    OR NEW.created_at        IS DISTINCT FROM OLD.created_at
    OR NEW.valid_at          IS DISTINCT FROM OLD.valid_at
    THEN
        RAISE EXCEPTION
            'a sealed lane_entry is insert-only history; only invalid_at may be '
            'set on it, and a named human sealed this body (records/sealing.py, '
            'ARCHITECTURE §8.2)';
    END IF;

    RETURN NEW;
END;
$$;

-- ------------------------------------------- the seed for the new columns
--
-- docs/SENSITIVITY.md: an unclassified field is a build failure, not a default,
-- and CI's "every column is classified" step reads field_classification. Four
-- columns, four rows, and the reasoning for each stated rather than inherited:
--
--   * payload_sealed is HEALTH/L4 -- **the same class and rung as the column it
--     seals.** Sealing is a storage property and never a declassification: a
--     rung governs serving, and nothing about a payload becoming ciphertext at
--     rest makes it servable to a principal who could not read it before. A
--     sealed column at a lower rung than its clear form would be encryption used
--     as an argument for wider access, which is the trade §5 does not make.
--   * payload_key_id is PII_MINOR/L3. It names a key and does not contain one
--     (atrest._mint: "the id's job is to name a key, and naming does not require
--     knowing"), so it is not key material and not L5. It IS a stable
--     pseudonymous identifier per lane, and 001's first judgement call is that
--     such an identifier for a minor is an identifier.
--   * payload_scheme is INTERNAL/L2. 'fernet-v1' discloses nothing about anyone.
--   * payload_sealed_at is INTERNAL/L2, the same as created_at, which it tracks.
--     Note the contrast the seed already draws: declination's timestamps are L5
--     because *when* someone declined discloses *that* they did. A seal time
--     carries no such signal -- every lane_entry has one.

INSERT INTO field_classification (table_name, column_name, data_class, rung) VALUES
    ('lane_entry','payload_sealed','HEALTH','L4'),
    ('lane_entry','payload_key_id','PII_MINOR','L3'),
    ('lane_entry','payload_scheme','INTERNAL','L2'),
    ('lane_entry','payload_sealed_at','INTERNAL','L2');

COMMIT;
