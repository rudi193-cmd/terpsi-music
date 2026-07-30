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
-- Ward clauses W-1..W-7 are quoted from CLAUDE.md's summary of Willow's
-- PROTECTED_AGENTS.md Part III, which has not been read at source. See the
-- provenance note in docs/LANE-MODEL.md.

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

-- -------------------------------------------------------------------- edge
--
-- Relational facts (§7). An edge may point at a scope object -- an ensemble,
-- an event -- because "Chris is staff of the drumline" is true and worth
-- recording. An edge authorizes nothing on its own; see access_grant.
--
-- Termination is by setting invalid_at, never by DELETE (§7.1). A court order
-- arriving mid-season is the case that proves it, and a deleted edge cannot
-- answer "who could see this on October 12, and why."

CREATE TABLE edge (
    edge_id     uuid PRIMARY KEY,
    kind        text        NOT NULL,
    holder_id   uuid        NOT NULL REFERENCES person(person_id),
    target_kind text        NOT NULL,   -- Lane | Ensemble | Event | Session | Program
    target_id   uuid        NOT NULL,
    source      text        NOT NULL,   -- how this became true; never blank
    created_at  timestamptz NOT NULL,
    valid_at    timestamptz NOT NULL,
    invalid_at  timestamptz,
    CONSTRAINT edge_kind CHECK (kind IN (
        'guardian_of', 'staff_of', 'director_of', 'judge_at', 'clinician_for'
    )),
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
-- ============================================================================

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

COMMIT;
