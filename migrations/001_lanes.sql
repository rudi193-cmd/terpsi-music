-- 001_lanes.sql
--
-- Migration 001. Promoted from docs/schema/001_lanes.proposed.sql, which now
-- carries a tombstone and is non-authoritative. Fourteen tables.
--
-- Governed by docs/LANE-MODEL.md, which is canonical for the reasoning, and
-- by docs/SENSITIVITY.md for the rungs. Where this file and those disagree,
-- they win and this file is the defect.
--
-- Target: PostgreSQL. That follows §6's mention of a Postgres store and
-- willow-2.0's .sql migrations; it is an assumption, not a decision.
--
-- Ward clauses W-1..W-7 are quoted from Willow's PROTECTED_AGENTS.md Part III
-- **read at source** (`c8c96b4`), which is what cleared the paraphrase gate
-- §18 item 3 held this file behind. Reading it also produced the two tables
-- added at promotion: W-3's second sentence names a permission the first
-- twelve tables could not represent, and W-5's names another.
--
--   * crossing_envelope -- W-3: "a crossing requires a guardian-signed
--     envelope naming both lanes, purpose, and expiry."
--   * self_widening     -- W-5: "envelopes name the ward as co-signer for
--     enumerated matters, widened only by new guardian-signed envelopes."
--
-- Both exist as Python types first -- records/crossing.py and
-- records/standing.py -- and the columns below are those types. Where the SQL
-- says something the type does not, the comment above the column says which
-- and why (§7.2: say which).

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
    -- not expressible as a CHECK, which cannot reach through target_lane_id to
    -- lane.subject_id. It was carried in LANE-MODEL.md's stated-and-unenforced
    -- list on that basis, with records/standing.py's is_self_edge() as the
    -- named middle and a note that "a trigger is the DDL-side answer when this
    -- migration stops being proposed."
    --
    -- This migration stopped being proposed. The trigger is at the foot of
    -- this file (edge_self_holder_is_subject), so a row reading
    -- ('self', <staff person>, <Ben's lane>) is now refused at write time as
    -- well as at the read.
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

-- ------------------------------------------------------- crossing_envelope
--
-- W-3, second sentence, at source: "Between wards, default deny; a crossing
-- requires a guardian-signed envelope naming both lanes, purpose, and expiry."
--
-- The first twelve tables encoded the prohibition and not the permission, so a
-- legitimate sibling crossing was **unrepresentable** -- there was nowhere to
-- put the guardian's signature, the purpose or the expiry, and the only way to
-- serve a real case was to not record that it happened. That is the worse of
-- the two failures, and this table is the fix. records/crossing.py is the same
-- object as a type; these columns are its fields.
--
-- Four things the clause names, and none has a default, because each is the one
-- a hurried implementation omits:
--
--   * BOTH lanes -- two NOT NULL columns, each a foreign key to one lane. An
--     envelope naming one lane is a wildcard over the other, so a nullable
--     column here would be a group grant wearing a NULL (W-2, refusal 5).
--   * a purpose -- NOT NULL with a non-blank CHECK, the same shape as
--     lane.exit_terms. A crossing "because it is convenient" is W-7's
--     territory, not this table's.
--   * an expiry -- NOT NULL, and CHECKed to be after the signature. An
--     envelope without a future expiry is a standing grant, which W-5 forbids.
--   * a guardian's signature -- signed_by is a person, never a role, and the
--     trigger at the foot of this file requires that person to hold a live
--     guardian_of edge over the lane whose seal is being opened.
--
-- **Direction is a property of the row, not of a flag.** (from, to) is ordered:
-- an envelope permitting A to read B does not permit B to read A. There is no
-- `symmetric boolean` and no second direction column, because one signature
-- opening two seals is the cheap violation W-3 exists to make unwritable.
--
-- **There is deliberately no rung column.** The envelope crosses a seal; it
-- does not widen a rung, an edge or a purpose -- records/serving.py applies all
-- three below the crossing, unchanged. L5 is therefore unreachable through an
-- envelope the way a group grant is unreachable through access_grant: not
-- excluded by a CHECK but absent from the table, so there is nothing to put it
-- in (§6's egress move, applied to the ladder).
--
-- Ended by invalid_at, never by DELETE (refusal 3). A revoked envelope that was
-- deleted cannot answer "who could see Ben's file on October 12, and why."

CREATE TABLE crossing_envelope (
    envelope_id   uuid PRIMARY KEY,
    from_lane_id  uuid        NOT NULL REFERENCES lane(lane_id),
    to_lane_id    uuid        NOT NULL REFERENCES lane(lane_id),
    purpose       text        NOT NULL,
    signed_by     uuid        NOT NULL REFERENCES person(person_id),
    basis_edge_id uuid        NOT NULL REFERENCES edge(edge_id),
    signed_at     timestamptz NOT NULL,
    expires_at    timestamptz NOT NULL,
    created_at    timestamptz NOT NULL,
    valid_at      timestamptz NOT NULL,
    invalid_at    timestamptz,
    CONSTRAINT crossing_envelope_names_two_lanes
        CHECK (from_lane_id <> to_lane_id),
    CONSTRAINT crossing_envelope_purpose_present
        CHECK (length(btrim(purpose)) > 0),
    CONSTRAINT crossing_envelope_expiry_is_future
        CHECK (expires_at > signed_at),
    CONSTRAINT crossing_envelope_dates
        CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
);

-- ----------------------------------------------------------- self_widening
--
-- W-5 at source: "Graduated co-signature: envelopes name the ward as co-signer
-- for enumerated matters, widened only by new guardian-signed envelopes. The
-- steward may propose a widening, citing the record; it may never enact one."
--
-- §18 item 12 decided the subject holds a `self` edge capped at L3 until W-6's
-- threshold. This table is the only thing that lifts that cap, and it lifts it
-- for **one enumerated matter at a time**. records/standing.py's Widening is
-- the same object as a type.
--
--   * one named category -- NOT NULL, non-blank, and CHECKed against the
--     wildcard vocabulary. "Everything" is not a matter; a name is. That is
--     W-2's "'the children' is not a scope; a name is" applied to the other
--     axis, and it is why refusal 5 is unexpressible here in both directions:
--     the subject is one person by foreign key, the matter is one string that
--     cannot be a star.
--   * a purpose -- non-blank, as on the envelope.
--   * an expiry -- after the signature. W-5 forbids the standing grant.
--   * a guardian's signature -- and NOT the ward's. signed_by <> subject_id is
--     W-4 ("a ward may request, never authorize") as a CHECK: a ward signing
--     its own widening is the whole clause defeated in one field. That the
--     signer is a *guardian* rather than merely a third party is the trigger's
--     half, for the same reason the self edge's is.
--
--     Say which (§7.2): with the edge trigger in place this CHECK is defence in
--     depth and cannot fire through an ordinary path, because a ward can only
--     reach signed_by = subject_id by first holding guardian_of over its own
--     lane, which the edge trigger refuses. It is kept because the clause
--     belongs where the clause applies and because the edge trigger is one
--     DROP away, and it is demonstrated in CI with the outer guard disabled --
--     otherwise it would be a constraint nobody has ever seen fire.
--
-- **max_rung is the one column the Python type does not carry, and this is the
-- pair's middle.** In records/standing.py the rung is supplied by control flow:
-- widens() is reached only for a field at L4, because L5 returns before the
-- edge check and L1-L3 are already served to the subject in full. A table has
-- no control flow, so what the type leaves implicit becomes a CHECK -- and it
-- admits L4 and nothing else. L5 is absent for the same reason it is absent
-- from access_grant.max_rung: never served to any principal under any grant,
-- including the subject. L1-L3 are absent because a widening to a rung the
-- subject already reads in full is not a widening.

CREATE TABLE self_widening (
    widening_id   uuid PRIMARY KEY,
    subject_id    uuid        NOT NULL REFERENCES person(person_id),
    category      text        NOT NULL,
    purpose       text        NOT NULL,
    max_rung      text        NOT NULL,
    signed_by     uuid        NOT NULL REFERENCES person(person_id),
    basis_edge_id uuid        NOT NULL REFERENCES edge(edge_id),
    signed_at     timestamptz NOT NULL,
    expires_at    timestamptz NOT NULL,
    created_at    timestamptz NOT NULL,
    valid_at      timestamptz NOT NULL,
    invalid_at    timestamptz,
    CONSTRAINT self_widening_category_present
        CHECK (length(btrim(category)) > 0),
    CONSTRAINT self_widening_category_is_a_name
        CHECK (lower(btrim(category)) NOT IN ('*', 'all', 'any', 'every')),
    CONSTRAINT self_widening_purpose_present
        CHECK (length(btrim(purpose)) > 0),
    CONSTRAINT self_widening_max_rung CHECK (max_rung IN ('L4')),
    CONSTRAINT self_widening_ward_cannot_sign_its_own
        CHECK (signed_by <> subject_id),
    CONSTRAINT self_widening_expiry_is_future
        CHECK (expires_at > signed_at),
    CONSTRAINT self_widening_dates
        CHECK (invalid_at IS NULL OR invalid_at >= valid_at)
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
-- ROW SHAPE THAT A CHECK CANNOT REACH.
--
-- A CHECK sees one row of one table. Three of this schema's rules are about the
-- relationship between a row and a row somewhere else, and every one of them is
-- a rule about *whose signature counts*:
--
--   * a `self` edge's holder must be the lane's subject;
--   * a crossing envelope's signer must be a guardian of the lane it opens;
--   * a widening's signer must be a guardian of the ward it widens.
--
-- All three were carried in docs/LANE-MODEL.md's stated-and-unenforced list
-- while this file sat in docs/schema/, with predicates in records/ as the named
-- middles. The list said a trigger was the DDL-side answer "when this migration
-- stops being proposed", and this is that. The predicates stay -- the store is
-- not the only path to a row, and defence in depth is not a duplicate.
--
-- Same caveat as the append-only triggers: proof against ordinary application
-- code, an ORM's cascade and a migration written in a hurry, not against a
-- superuser who can drop them. Revoking rights from the application role
-- belongs in the install (§11).
--
-- **A BEFORE ROW trigger fires before every CHECK, NOT NULL and foreign key on
-- the same row, and that changes what an attack proves.** Found by running the
-- attacks and reading the error text rather than the exit status: an envelope
-- pointed at an ensemble instead of a lane was refused by the signature trigger
-- and never reached the foreign key, so the guard that was being tested had not
-- fired. That is `EXTERNAL-ARM.md`'s *"a gate green because a different
-- constraint was catching it"*, arriving through execution order.
--
-- The consequence for anything attacking this schema: assert on the constraint
-- named in the error, never on the fact of a refusal. `.github/workflows/tests.yml`
-- does, and three of its cases now approach through a column the trigger does
-- not read, so the intended guard is the one that speaks.
-- ============================================================================

-- The rule is an equivalence and not an implication, which the first draft of
-- this function got wrong in the direction that matters. Refusing only a
-- forged `self` edge leaves the mirror row insertable: ('guardian_of', Ben,
-- Ben's lane) is a ward holding guardianship over itself, and every other
-- guard in this file that asks "is the signer a guardian of this lane" then
-- answers yes for the ward. That is W-4 defeated one table down -- a ward
-- signing its own crossing envelope, which carries no signer CHECK of its own
-- because the clause puts the signature requirement on the guardian, not on a
-- column. Exactly one edge kind may name its own subject as holder.

CREATE FUNCTION refuse_forged_self_edge() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    holder_is_subject boolean;
BEGIN
    holder_is_subject := EXISTS (
        SELECT 1 FROM lane l
        WHERE l.lane_id = NEW.target_lane_id
          AND l.subject_id = NEW.holder_id
    );
    IF NEW.kind = 'self' AND NOT holder_is_subject THEN
        RAISE EXCEPTION
            'a self edge holder must be the lane''s own subject; % is not the '
            'subject of lane % (§18 item 12)',
            NEW.holder_id, NEW.target_lane_id;
    ELSIF NEW.kind <> 'self' AND holder_is_subject THEN
        RAISE EXCEPTION
            'only a self edge may name its own subject as holder; % over their '
            'own lane % is the ward authorizing itself (W-4)',
            NEW.kind, NEW.target_lane_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER edge_self_holder_is_subject
    BEFORE INSERT OR UPDATE ON edge
    FOR EACH ROW EXECUTE FUNCTION refuse_forged_self_edge();

-- "guardian-signed" is a claim about the signer's standing over a lane, at the
-- moment of signature. One function for both tables rather than two nearly
-- identical ones (§16): they differ only in how the lane is named -- the
-- envelope names it, the widening names its subject and lane.subject_id is
-- UNIQUE, so one person is one lane and a set cannot be smuggled through
-- either.
--
-- Standing is evaluated at signed_at. Standing at *use* is records/crossing.py
-- and records/standing.py's job and is deliberately not duplicated here: a
-- guardian whose standing later ends cannot keep an envelope open by having
-- signed it, and that is a predicate over the reading instant, not over the row.

CREATE FUNCTION refuse_unsigned_by_guardian() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    opened_lane uuid;
BEGIN
    IF TG_TABLE_NAME = 'crossing_envelope' THEN
        opened_lane := NEW.to_lane_id;
    ELSE
        SELECT l.lane_id INTO opened_lane
        FROM lane l WHERE l.subject_id = NEW.subject_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM edge e
        WHERE e.kind = 'guardian_of'
          AND e.holder_id = NEW.signed_by
          AND e.target_lane_id = opened_lane
          AND e.valid_at <= NEW.signed_at
          AND (e.invalid_at IS NULL OR e.invalid_at > NEW.signed_at)
    ) THEN
        RAISE EXCEPTION
            'a guardian-signed % is signed by a guardian; % held no live '
            'guardian_of edge over lane % at % (W-3, W-5)',
            TG_TABLE_NAME, NEW.signed_by, opened_lane, NEW.signed_at;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER crossing_envelope_guardian_signed
    BEFORE INSERT OR UPDATE ON crossing_envelope
    FOR EACH ROW EXECUTE FUNCTION refuse_unsigned_by_guardian();

CREATE TRIGGER self_widening_guardian_signed
    BEFORE INSERT OR UPDATE ON self_widening
    FOR EACH ROW EXECUTE FUNCTION refuse_unsigned_by_guardian();

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
--   * self_widening.category is HEALTH/L4 where lane_entry.kind is PII_MINOR/L3,
--     and the difference is forced by the row rather than chosen. A widening
--     only ever exists for a matter above the self edge's L3 cap -- its own
--     max_rung CHECK admits L4 and nothing else -- so the category string names,
--     by construction, a category the law follows about a named minor. That is
--     SENSITIVITY.md's L4 definition exactly.
--   * crossing_envelope's two lane columns are L3 and not L5. An envelope
--     discloses that two lanes are connected, which is a family fact and sits
--     with edge.target_lane_id; it is not a refusal, which is what puts
--     declination and consent_chain.disposition at L5.
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

    ('crossing_envelope','envelope_id','PII_MINOR','L3'),
    ('crossing_envelope','from_lane_id','PII_MINOR','L3'),
    ('crossing_envelope','to_lane_id','PII_MINOR','L3'),
    ('crossing_envelope','purpose','HEALTH','L4'),
    ('crossing_envelope','signed_by','PII_GUARDIAN','L3'),
    ('crossing_envelope','basis_edge_id','PII_GUARDIAN','L3'),
    ('crossing_envelope','signed_at','INTERNAL','L2'),
    ('crossing_envelope','expires_at','INTERNAL','L2'),
    ('crossing_envelope','created_at','INTERNAL','L2'),
    ('crossing_envelope','valid_at','INTERNAL','L2'),
    ('crossing_envelope','invalid_at','INTERNAL','L2'),

    ('self_widening','widening_id','PII_MINOR','L3'),
    ('self_widening','subject_id','PII_MINOR','L3'),
    ('self_widening','category','HEALTH','L4'),
    ('self_widening','purpose','HEALTH','L4'),
    ('self_widening','max_rung','INTERNAL','L2'),
    ('self_widening','signed_by','PII_GUARDIAN','L3'),
    ('self_widening','basis_edge_id','PII_GUARDIAN','L3'),
    ('self_widening','signed_at','INTERNAL','L2'),
    ('self_widening','expires_at','INTERNAL','L2'),
    ('self_widening','created_at','INTERNAL','L2'),
    ('self_widening','valid_at','INTERNAL','L2'),
    ('self_widening','invalid_at','INTERNAL','L2'),

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
