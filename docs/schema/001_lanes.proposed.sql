-- 001_lanes.proposed.sql
--
-- PROPOSED, NOT ADOPTED. This file is not in a migrations/ directory on
-- purpose: promoting it is gated on §18 blocker 2 (the disposition of
-- apps/marching-arts) and blocker 4 (which surfaces exist). It is here so
-- that "migration 001 cannot be written from what is on the page" stops
-- being true.
--
-- Governed by docs/LANE-MODEL.md, which is canonical for the reasoning, and
-- by docs/SENSITIVITY.md for the rungs. Where this file and those disagree,
-- they win and this file is the defect.
--
-- Target: PostgreSQL. That follows §6's mention of a Postgres store and
-- willow-2.0's .sql migrations; it is an assumption, not a decision.
--
-- Ward clauses W-1..W-7 were quoted from CLAUDE.md's summary of Willow's
-- PROTECTED_AGENTS.md Part III. THAT IS NO LONGER TRUE: Part III was read at
-- source 2026-09-11 (willows-grove, blob 2886a41) and the read is recorded in
-- docs/PART-III-READ.md. W-1, W-2 and W-6 came through the translation whole
-- and what this file encodes for them stands unchanged.
--
-- What the read added, and none of it is enforced here yet:
--   * access_grant.signer_id may be the lane's own subject -- W-4 and I-2,
--     and NOT a flat rule: after W-6's threshold a grant signed by the subject
--     is how a graduate re-admits their guardian.
--   * access_grant has one signer and no proposed state, so W-5's "envelopes
--     name the ward as co-signer" is unrepresentable -- W-3's missing-envelope
--     shape again.
--   * edge has neither expires_at nor exit_terms, and is arguably the office
--     I-3 requires an exit from at entry. Arguable, and unargued: see the read.

BEGIN;

-- ------------------------------------------------------------------ person
--
-- Identity anchor only. Nothing *about* a person lives here; that is what
-- lanes are for. Deliberately absent: any is_minor / is_adult column. Minor
-- status is a birthdate evaluated inside the grant lookup (§7), because a
-- flag stays true until somebody remembers to run the job that clears it.

CREATE TABLE person (
    person_id   uuid PRIMARY KEY,
    birthdate   date        NOT NULL,
    created_at  timestamptz NOT NULL,   -- immutable; when this system learned
    valid_at    timestamptz NOT NULL,   -- when the record became true
    invalid_at  timestamptz,            -- NULL means still active
    CONSTRAINT person_dates CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- -------------------------------------------------------------------- lane
--
-- W-1: a lane, not an account -- separate storage, permissions and audit
-- trail from the steward's first act. One per person, wards and non-wards
-- alike; see LANE-MODEL.md for why this goes further than W-1 requires.
--
-- W-6: "a lane opened without a written exit is invalidly opened." That is
-- why exit_terms is NOT NULL with a non-blank CHECK rather than a nullable
-- column somebody fills in later -- the same shape as §7's source column.

CREATE TABLE lane (
    lane_id     uuid PRIMARY KEY,
    subject_id  uuid        NOT NULL UNIQUE REFERENCES person(person_id),
    exit_terms  text        NOT NULL,
    opened_at   timestamptz NOT NULL,
    created_at  timestamptz NOT NULL,
    valid_at    timestamptz NOT NULL,
    invalid_at  timestamptz,
    CONSTRAINT lane_exit_terms_present CHECK (length(btrim(exit_terms)) > 0),
    CONSTRAINT lane_dates CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- ---------------------------------------------------------------- referent
--
-- W-3: "a shared event is two lane entries with one referent." This table is
-- the referent. It carries NO person reference and NO roster column, and that
-- absence is the schema rule -- a rehearsal attended by 150 students is 150
-- lane_entry rows against one referent, never one row with a member list.
--
-- Anything added here that names or counts participants reintroduces the
-- shared partition W-1 forbids. tests/test_lane_model.py asserts the absence.

CREATE TABLE referent (
    referent_id uuid PRIMARY KEY,
    kind        text        NOT NULL,   -- Rehearsal | Event | Charge | MediaAsset | ...
    occurs_at   timestamptz,
    label       text        NOT NULL,   -- L1: "Regional Championship, Oct 12"
    created_at  timestamptz NOT NULL,
    valid_at    timestamptz NOT NULL,
    invalid_at  timestamptz,
    CONSTRAINT referent_dates CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- -------------------------------------------------------------- lane_entry
--
-- The unit of storage. Every fact about a person is a row here, in that
-- person's lane. lane_id is NOT NULL because there is no such thing as a
-- ward fact outside a lane (W-1, from the first write).
--
-- seal_state is Nestor's cascade (§8.2): a machine transcription is a draft
-- until a named human seals it. sealed-without-a-sealer is refused by CHECK
-- rather than by convention, mirroring §7's treatment of unsigned grants.
--
-- author_id carries I-7: entries authored by the governed about the office
-- are as durable as entries authored by the office about the governed. The
-- supersession policy that enforces it is stated in LANE-MODEL.md and is not
-- expressible as a column CHECK.

CREATE TABLE lane_entry (
    entry_id    uuid PRIMARY KEY,
    lane_id     uuid        NOT NULL REFERENCES lane(lane_id),
    referent_id uuid        REFERENCES referent(referent_id),
    kind        text        NOT NULL,
    payload     jsonb       NOT NULL,
    author_id   uuid        NOT NULL REFERENCES person(person_id),
    seal_state  text        NOT NULL DEFAULT 'draft',
    sealed_by   uuid        REFERENCES person(person_id),
    created_at  timestamptz NOT NULL,
    valid_at    timestamptz NOT NULL,
    invalid_at  timestamptz,
    CONSTRAINT lane_entry_seal_state
        CHECK (seal_state IN ('draft', 'sealed', 'pending')),
    CONSTRAINT lane_entry_sealed_has_sealer
        CHECK (seal_state <> 'sealed' OR sealed_by IS NOT NULL),
    CONSTRAINT lane_entry_dates
        CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- ------------------------------------------------------------ scope_object
--
-- The non-lane things an edge can point at: §8's Org -> Program -> Ensemble
-- -> Season -> Event spine. Holds no participants, for the same reason
-- `referent` does not.
--
-- This table exists because the first draft of `edge` carried a polymorphic
-- (target_kind, target_id) pair with no foreign key, which accepted a UUID
-- referring to nothing and a target_kind of 'Sandwich'. Both were confirmed
-- against a live PostgreSQL 16 instance before this table was added.

CREATE TABLE scope_object (
    scope_id   uuid PRIMARY KEY,
    kind       text        NOT NULL,
    label      text        NOT NULL,
    created_at timestamptz NOT NULL,
    valid_at   timestamptz NOT NULL,
    invalid_at timestamptz,
    CONSTRAINT scope_object_kind CHECK (kind IN (
        'Org', 'Program', 'Ensemble', 'Season', 'Event', 'Session'
    )),
    CONSTRAINT scope_object_dates CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- -------------------------------------------------------------------- edge
--
-- Relational facts (§7). An edge may point at a scope object -- an ensemble,
-- an event -- because "Chris is staff of the drumline" is true and worth
-- recording. An edge authorizes nothing on its own; see access_grant.
--
-- The target is two nullable foreign keys with exactly one populated, rather
-- than a (kind, id) pair. That buys real referential integrity in both
-- directions and removes the free-text kind column entirely: which column is
-- set *is* the kind, so it cannot disagree with the row it points at.
--
-- Termination is by setting invalid_at, never by DELETE (§7.1). A court order
-- arriving mid-season is the case that proves it, and a deleted edge cannot
-- answer "who could see this on October 12, and why."

CREATE TABLE edge (
    edge_id         uuid PRIMARY KEY,
    kind            text        NOT NULL,
    holder_id       uuid        NOT NULL REFERENCES person(person_id),
    target_lane_id  uuid        REFERENCES lane(lane_id),
    target_scope_id uuid        REFERENCES scope_object(scope_id),
    source          text        NOT NULL,   -- how this became true; never blank
    created_at      timestamptz NOT NULL,
    valid_at        timestamptz NOT NULL,
    invalid_at      timestamptz,
    -- 'self' added 2026-07-30 (§18 item 12): the subject's own standing in
    -- their own lane, capped at L3 until W-6's threshold.
    --
    -- Its defining property -- holder_id must be the lane's subject_id -- is
    -- NOT enforceable here. A CHECK cannot reach through target_lane_id to
    -- lane.subject_id, so 'self' is the one kind whose meaning this table
    -- states and cannot hold. Named in LANE-MODEL.md's stated-and-unenforced
    -- list beside the other three, and enforced in records/standing.py's
    -- is_self_edge(), which the read predicate calls before any edge matches.
    -- Rule 12: the pair has a named middle. A trigger is the DDL-side answer
    -- when this migration stops being proposed.
    CONSTRAINT edge_kind CHECK (kind IN (
        'self', 'guardian_of', 'staff_of', 'director_of', 'judge_at', 'clinician_for'
    )),
    CONSTRAINT edge_exactly_one_target
        CHECK (num_nonnulls(target_lane_id, target_scope_id) = 1),
    CONSTRAINT edge_source_present CHECK (length(btrim(source)) > 0),
    CONSTRAINT edge_dates CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- ------------------------------------------------------------ access_grant
--
-- W-2: "'The children' is not a scope; a name is." Wildcard and group scopes
-- are invalid at issuance -- so this table cannot express one. lane_id is a
-- single NOT NULL column, there is no grant-to-lane join table, and there is
-- no scope-pattern column. A staff member covering forty students holds forty
-- rows. That is the intended cost.
--
-- max_rung ties this to docs/SENSITIVITY.md. L5 is absent from the CHECK
-- because L5 is never served to anyone under any grant -- the ladder's top
-- rung is unreachable through this table by construction rather than by
-- policy. L4 additionally requires a declared purpose.

CREATE TABLE access_grant (
    grant_id      uuid PRIMARY KEY,
    holder_id     uuid        NOT NULL REFERENCES person(person_id),
    lane_id       uuid        NOT NULL REFERENCES lane(lane_id),
    basis_edge_id uuid        NOT NULL REFERENCES edge(edge_id),
    max_rung      text        NOT NULL,
    purpose       text,
    signer_id     uuid        NOT NULL REFERENCES person(person_id),
    expires_at    timestamptz NOT NULL,
    created_at    timestamptz NOT NULL,
    valid_at      timestamptz NOT NULL,
    invalid_at    timestamptz,
    CONSTRAINT access_grant_max_rung CHECK (max_rung IN ('L1', 'L2', 'L3', 'L4')),
    CONSTRAINT access_grant_l4_needs_purpose
        CHECK (max_rung <> 'L4' OR (purpose IS NOT NULL AND length(btrim(purpose)) > 0)),
    CONSTRAINT access_grant_dates CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- ------------------------------------------------------------- declination
--
-- L5 throughout. A media release refused, a fee waiver taken, a consent
-- withdrawn. Read only by the predicate; joined by no view, returned by no
-- query, exported by nothing.
--
-- §7's indistinguishability guarantee is that a member who declined and a
-- member who is absent produce the same rows, the same count and the same
-- subject list. A surface able to render this table has re-created the signal
-- the guarantee exists to suppress, which is why it is a separate table
-- rather than a column on lane_entry -- a column travels in SELECT *.

CREATE TABLE declination (
    declination_id uuid PRIMARY KEY,
    lane_id        uuid        NOT NULL REFERENCES lane(lane_id),
    subject_matter text        NOT NULL,   -- 'media_release' | 'fee_waiver' | ...
    created_at     timestamptz NOT NULL,
    valid_at       timestamptz NOT NULL,
    invalid_at     timestamptz,
    CONSTRAINT declination_dates CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- ------------------------------------------------ field_classification
--
-- docs/SENSITIVITY.md requires that an unclassified field be a build failure
-- rather than a default. This is the registry that makes the check possible:
-- every column of every table above needs a row, and the test asserts it.
--
-- Two attributes, not one. The rung governs serving; the class governs egress
-- policy and retention; neither is derivable from the other in the general
-- case (§6).

CREATE TABLE field_classification (
    table_name  text NOT NULL,
    column_name text NOT NULL,
    data_class  text NOT NULL,
    rung        text NOT NULL,
    PRIMARY KEY (table_name, column_name),
    CONSTRAINT field_classification_class CHECK (data_class IN (
        'PUBLIC', 'INTERNAL', 'PII_MINOR', 'PII_GUARDIAN',
        'HEALTH', 'FINANCIAL', 'MEDIA_MINOR', 'DERIVED_ANON'
    )),
    CONSTRAINT field_classification_rung
        CHECK (rung IN ('L1', 'L2', 'L3', 'L4', 'L5'))
);

-- ============================================================================
-- APPEND-ONLY. History, not state.
--
-- §7.1's exclusion list is the instructive half of willow-2.0's bitemporal
-- migration: frank_ledger, hook_executions and routing_decisions are left out
-- because a historical fact is not mutable state. The same split applies here.
-- These three tables deliberately carry NO valid_at / invalid_at pair, and
-- tests/test_lane_model.py asserts they never grow one.
--
-- Omitting the pair is NOT what makes a table append-only. The first draft of
-- this file said "append-only" in this comment and did nothing else, and an
-- UPDATE followed by a DELETE against disclosure_log on a live instance both
-- succeeded -- silently rewriting the FERPA §99.32 record of disclosures. A
-- label is not an enforcement (§7.2: say which). The trigger below is the
-- enforcement.
--
-- It is not proof against a superuser, who can drop it; nothing in a schema
-- is. It is proof against ordinary application code, an ORM's cascade, and a
-- migration written in a hurry, which is where this would actually happen.
-- Revoking UPDATE and DELETE from the application role belongs in the install
-- (§11) and is the other half.
-- ============================================================================

CREATE FUNCTION refuse_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'append-only: % on % is refused; history is not mutable state (§7.1)',
        TG_OP, TG_TABLE_NAME;
END;
$$;

CREATE TABLE disclosure_log (
    seq          bigserial PRIMARY KEY,
    occurred_at  timestamptz NOT NULL,
    principal_id uuid        NOT NULL REFERENCES person(person_id),
    lane_id      uuid        REFERENCES lane(lane_id),
    what         text        NOT NULL,
    recipient    text        NOT NULL,
    authority    text        NOT NULL,   -- which grant, which edge, which order
    prev_hash    bytea,
    hash         bytea       NOT NULL
);

CREATE TABLE consent_chain (
    seq         bigserial PRIMARY KEY,
    occurred_at timestamptz NOT NULL,
    lane_id     uuid        NOT NULL REFERENCES lane(lane_id),
    asked_by    uuid        NOT NULL REFERENCES person(person_id),
    answered_by uuid        REFERENCES person(person_id),
    disposition text        NOT NULL,   -- I-6: silence is not a disposition
    timebound   timestamptz NOT NULL,
    prev_hash   bytea,
    hash        bytea       NOT NULL
);

CREATE TABLE reconciled_session (
    seq          bigserial PRIMARY KEY,
    opened_at    timestamptz NOT NULL,
    closed_at    timestamptz,
    principal_id uuid        NOT NULL REFERENCES person(person_id),
    declared     jsonb       NOT NULL,  -- 13 fields in
    observed     jsonb,                 -- 13 fields out
    diff         jsonb,
    prev_hash    bytea,
    hash         bytea       NOT NULL
);

CREATE TRIGGER disclosure_log_append_only
    BEFORE UPDATE OR DELETE ON disclosure_log
    FOR EACH ROW EXECUTE FUNCTION refuse_mutation();

CREATE TRIGGER consent_chain_append_only
    BEFORE UPDATE OR DELETE ON consent_chain
    FOR EACH ROW EXECUTE FUNCTION refuse_mutation();

CREATE TRIGGER reconciled_session_append_only
    BEFORE UPDATE OR DELETE ON reconciled_session
    FOR EACH ROW EXECUTE FUNCTION refuse_mutation();

-- ============================================================================
-- CLASSIFICATION SEED
--
-- docs/SENSITIVITY.md: "an unclassified field is a build failure, not a
-- default." That rule needs a populated registry to check against, and the
-- first draft of this file shipped the table empty -- 87 columns, 0 rows,
-- nothing requiring them. Declaration without enforcement, in the migration
-- whose own document names that defect.
--
-- Every column below is classified twice, per §6: a data class governing
-- egress and retention, and a rung governing serving. Neither is derivable
-- from the other. tests/test_lane_model.py asserts the registry covers every
-- column the DDL declares, so adding a column without classifying it fails.
--
-- Judgement calls worth naming, because a reader should disagree with them
-- explicitly rather than inherit them silently:
--
--   * Surrogate primary keys of person-bearing rows are L3, not L2. A stable
--     pseudonymous identifier for a minor is an identifier.
--   * lane_entry.kind is L3. "medical_note" discloses without its payload.
--   * consent_chain.disposition is L5 by SENSITIVITY.md's rule 3 -- a
--     disposition is where a refusal lives, and rendering it re-creates the
--     signal §7's indistinguishability guarantee suppresses.
--   * Every column of `declination` is L5 for the same reason, including its
--     timestamps: when someone declined is nearly as disclosing as that they
--     did.
--   * lane_entry.payload is HEALTH/L4 because composition is by max and that
--     column can hold anything. Per-kind columns would let it fall.
-- ============================================================================

INSERT INTO field_classification (table_name, column_name, data_class, rung) VALUES
    ('person','person_id','PII_MINOR','L3'),
    ('person','birthdate','PII_MINOR','L3'),
    ('person','created_at','INTERNAL','L2'),
    ('person','valid_at','INTERNAL','L2'),
    ('person','invalid_at','INTERNAL','L2'),

    ('lane','lane_id','PII_MINOR','L3'),
    ('lane','subject_id','PII_MINOR','L3'),
    ('lane','exit_terms','PII_MINOR','L3'),
    ('lane','opened_at','INTERNAL','L2'),
    ('lane','created_at','INTERNAL','L2'),
    ('lane','valid_at','INTERNAL','L2'),
    ('lane','invalid_at','INTERNAL','L2'),

    ('referent','referent_id','INTERNAL','L2'),
    ('referent','kind','INTERNAL','L2'),
    ('referent','occurs_at','PUBLIC','L1'),
    ('referent','label','PUBLIC','L1'),
    ('referent','created_at','INTERNAL','L2'),
    ('referent','valid_at','INTERNAL','L2'),
    ('referent','invalid_at','INTERNAL','L2'),

    ('lane_entry','entry_id','PII_MINOR','L3'),
    ('lane_entry','lane_id','PII_MINOR','L3'),
    ('lane_entry','referent_id','INTERNAL','L2'),
    ('lane_entry','kind','PII_MINOR','L3'),
    ('lane_entry','payload','HEALTH','L4'),
    ('lane_entry','author_id','PII_MINOR','L3'),
    ('lane_entry','seal_state','INTERNAL','L2'),
    ('lane_entry','sealed_by','PII_MINOR','L3'),
    ('lane_entry','created_at','INTERNAL','L2'),
    ('lane_entry','valid_at','INTERNAL','L2'),
    ('lane_entry','invalid_at','INTERNAL','L2'),

    ('scope_object','scope_id','INTERNAL','L2'),
    ('scope_object','kind','INTERNAL','L2'),
    ('scope_object','label','PUBLIC','L1'),
    ('scope_object','created_at','INTERNAL','L2'),
    ('scope_object','valid_at','INTERNAL','L2'),
    ('scope_object','invalid_at','INTERNAL','L2'),

    ('edge','edge_id','PII_GUARDIAN','L3'),
    ('edge','kind','PII_GUARDIAN','L3'),
    ('edge','holder_id','PII_GUARDIAN','L3'),
    ('edge','target_lane_id','PII_MINOR','L3'),
    ('edge','target_scope_id','INTERNAL','L2'),
    ('edge','source','PII_GUARDIAN','L3'),
    ('edge','created_at','INTERNAL','L2'),
    ('edge','valid_at','INTERNAL','L2'),
    ('edge','invalid_at','INTERNAL','L2'),

    ('access_grant','grant_id','PII_MINOR','L3'),
    ('access_grant','holder_id','PII_GUARDIAN','L3'),
    ('access_grant','lane_id','PII_MINOR','L3'),
    ('access_grant','basis_edge_id','PII_GUARDIAN','L3'),
    ('access_grant','max_rung','INTERNAL','L2'),
    ('access_grant','purpose','HEALTH','L4'),
    ('access_grant','signer_id','PII_GUARDIAN','L3'),
    ('access_grant','expires_at','INTERNAL','L2'),
    ('access_grant','created_at','INTERNAL','L2'),
    ('access_grant','valid_at','INTERNAL','L2'),
    ('access_grant','invalid_at','INTERNAL','L2'),

    ('declination','declination_id','PII_MINOR','L5'),
    ('declination','lane_id','PII_MINOR','L5'),
    ('declination','subject_matter','PII_MINOR','L5'),
    ('declination','created_at','PII_MINOR','L5'),
    ('declination','valid_at','PII_MINOR','L5'),
    ('declination','invalid_at','PII_MINOR','L5'),

    ('field_classification','table_name','INTERNAL','L2'),
    ('field_classification','column_name','INTERNAL','L2'),
    ('field_classification','data_class','INTERNAL','L2'),
    ('field_classification','rung','INTERNAL','L2'),

    ('disclosure_log','seq','INTERNAL','L2'),
    ('disclosure_log','occurred_at','PII_MINOR','L3'),
    ('disclosure_log','principal_id','PII_GUARDIAN','L3'),
    ('disclosure_log','lane_id','PII_MINOR','L3'),
    ('disclosure_log','what','PII_MINOR','L3'),
    ('disclosure_log','recipient','PII_MINOR','L3'),
    ('disclosure_log','authority','PII_MINOR','L3'),
    ('disclosure_log','prev_hash','INTERNAL','L2'),
    ('disclosure_log','hash','INTERNAL','L2'),

    ('consent_chain','seq','INTERNAL','L2'),
    ('consent_chain','occurred_at','PII_MINOR','L3'),
    ('consent_chain','lane_id','PII_MINOR','L3'),
    ('consent_chain','asked_by','PII_GUARDIAN','L3'),
    ('consent_chain','answered_by','PII_GUARDIAN','L3'),
    ('consent_chain','disposition','PII_MINOR','L5'),
    ('consent_chain','timebound','INTERNAL','L2'),
    ('consent_chain','prev_hash','INTERNAL','L2'),
    ('consent_chain','hash','INTERNAL','L2'),

    ('reconciled_session','seq','INTERNAL','L2'),
    ('reconciled_session','opened_at','INTERNAL','L2'),
    ('reconciled_session','closed_at','INTERNAL','L2'),
    ('reconciled_session','principal_id','PII_GUARDIAN','L3'),
    ('reconciled_session','declared','PII_MINOR','L4'),
    ('reconciled_session','observed','PII_MINOR','L4'),
    ('reconciled_session','diff','PII_MINOR','L4'),
    ('reconciled_session','prev_hash','INTERNAL','L2'),
    ('reconciled_session','hash','INTERNAL','L2');

COMMIT;
