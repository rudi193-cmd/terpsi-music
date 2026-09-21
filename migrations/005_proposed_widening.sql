-- 005_proposed_widening.sql
--
-- Migration 005. W-5's proposed state -- "the steward may propose a widening,
-- citing the record; it may never enact one."
--
-- docs/PART-III-READ.md item 1 opened this. `self_widening` (migration 001) is
-- the ENACTED widening: a guardian's signature lifts the ward's self-cap for one
-- enumerated matter, and its own header quotes the propose-never-enact sentence.
-- But only the enacted half existed. A steward that wanted to propose a widening
-- -- the ward's clean record is evidence for it -- had nowhere to write the
-- proposal except `self_widening`, and writing a `self_widening` row is
-- ENACTING one. So "propose, never enact" had no representation: proposing was
-- enacting. This is the same shape as W-3's missing crossing envelope, and it
-- takes the same fix, a table.
--
-- WHAT THIS TABLE IS, SAID PLAINLY (rule 18)
--
-- This is a LEDGER of proposals, not a gate. A row here **grants nothing** and
-- **widens nothing**: no read path consults it, and it carries no signature to
-- consult. The ENFORCEMENT of "never enact" is `records/standing.py::ratify`,
-- the named middle (rule 12): the only path from a proposal to an enacted
-- widening runs through a live guardian signature and yields a `self_widening`,
-- exactly as `records/serving.py::Grant` never widens by itself. Calling this
-- table enforcement would be the mistake the fleet keeps making; it is the
-- durable record a steward writes and a guardian reads before deciding.
--
-- WHO MAY PROPOSE. Anyone -- the steward, or the ward itself. W-4 is "a ward may
-- REQUEST, never authorize", and a proposal is a request: there is deliberately
-- no `proposed_by <> subject_id` CHECK, because a ward asking for its first
-- library card is the clause working, not defeated. Only the guardian's
-- signature that enacts it (on `self_widening`, W-4's `signed_by <> subject_id`)
-- is restricted. "A clean track record is evidence for a proposal, never a grant
-- in itself" is the whole distinction, and it lives in the gap between this
-- table and that one.
--
-- The columns mirror `self_widening` minus the signature, plus the evidence a
-- proposal cites. One enumerated category, not a wildcard (W-2 on the matter
-- axis); an expiry, because a stale proposal is not a standing one; and the
-- evidence, non-blank, because "citing the record" is the clause's own
-- requirement and a proposal with nothing behind it is drift wearing a form.

BEGIN;

CREATE TABLE proposed_widening (
    proposal_id  uuid PRIMARY KEY,
    subject_id   uuid        NOT NULL REFERENCES person(person_id),
    category     text        NOT NULL,
    purpose      text        NOT NULL,
    max_rung     text        NOT NULL,
    proposed_by  uuid        NOT NULL REFERENCES person(person_id),
    evidence     text        NOT NULL,
    proposed_at  timestamptz NOT NULL,
    expires_at   timestamptz NOT NULL,
    created_at   timestamptz NOT NULL,
    valid_at     timestamptz NOT NULL,
    invalid_at   timestamptz,
    CONSTRAINT proposed_widening_category_present
        CHECK (length(btrim(category)) > 0),
    CONSTRAINT proposed_widening_category_is_a_name
        CHECK (lower(btrim(category)) NOT IN ('*', 'all', 'any', 'every')),
    CONSTRAINT proposed_widening_purpose_present
        CHECK (length(btrim(purpose)) > 0),
    CONSTRAINT proposed_widening_evidence_present
        CHECK (length(btrim(evidence)) > 0),
    -- Same rung ceiling as self_widening: a widening below L4 is not a widening,
    -- and L5 is never served to anyone including the subject.
    CONSTRAINT proposed_widening_max_rung CHECK (max_rung IN ('L4')),
    CONSTRAINT proposed_widening_expiry_is_future
        CHECK (expires_at > proposed_at),
    CONSTRAINT proposed_widening_dates
        CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- Classification: every column, per §6, the same twice-over as migration 001.
-- evidence is HEALTH/L4 for lane_entry.payload's reason -- free text that can
-- hold anything about a named minor composes to the max. All text/uuid/temporal,
-- so store/sealing_plan.py excludes each (NOT_A_CONTAINER / KEY / TEMPORAL) and
-- no column here gains a sealed form; tests/test_sealing_plan.py checks that.
INSERT INTO field_classification (table_name, column_name, data_class, rung) VALUES
    ('proposed_widening','proposal_id','PII_MINOR','L3'),
    ('proposed_widening','subject_id','PII_MINOR','L3'),
    ('proposed_widening','category','HEALTH','L4'),
    ('proposed_widening','purpose','HEALTH','L4'),
    ('proposed_widening','max_rung','INTERNAL','L2'),
    ('proposed_widening','proposed_by','PII_GUARDIAN','L3'),
    ('proposed_widening','evidence','HEALTH','L4'),
    ('proposed_widening','proposed_at','INTERNAL','L2'),
    ('proposed_widening','expires_at','INTERNAL','L2'),
    ('proposed_widening','created_at','INTERNAL','L2'),
    ('proposed_widening','valid_at','INTERNAL','L2'),
    ('proposed_widening','invalid_at','INTERNAL','L2');

-- Row security, scoped by the ward's own lane through subject_id -- the same
-- seal self_widening carries (migration 003), because a proposal about a ward is
-- as disclosing as the widening it proposes. The definer functions it uses
-- (reaches_lane, acting_principal, lane_of_subject) are migration 003's and
-- exist by now. Ownership moves to the migrator like every other table.
ALTER TABLE proposed_widening OWNER TO terpsi_migrator;
ALTER TABLE proposed_widening ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposed_widening FORCE ROW LEVEL SECURITY;
CREATE POLICY proposed_widening_lane_seal ON proposed_widening FOR SELECT USING (
    reaches_lane(acting_principal(), lane_of_subject(subject_id)));
CREATE POLICY proposed_widening_insert_unsealed ON proposed_widening
    FOR INSERT WITH CHECK (true);

COMMIT;
