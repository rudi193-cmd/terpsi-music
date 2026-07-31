-- 003_row_security.sql
--
-- Migration 003. Adds no table and no column -- five functions, eleven row
-- security policies per protected table, and an ownership transfer -- which is
-- why it seeds no field_classification rows and why tools/registry.py's parse
-- of 001 stays complete. (002 said the same thing for the same reason; the
-- sentence is repeated rather than cross-referenced because a reader of this
-- file should not have to open another to know whether the registry moved.)
--
-- Governed by docs/PLAN-STORE.md decision 4 and by docs/ARCHITECTURE.md §7 /
-- docs/LANE-MODEL.md's W-3. Where this file and those disagree, they win and
-- this file is the defect.
--
-- ===========================================================================
-- WHAT THIS COMPILES, AND WHAT STAYS IN PYTHON (rule 18: say which layer)
-- ===========================================================================
--
-- `records/serving.py::serve()` is one function making six decisions in order.
-- This migration compiles TWO of them and deliberately compiles none of the
-- other four. Stated as a list, because "the read predicate is compiled at the
-- store" is the kind of sentence that gets read as "all of it".
--
-- COMPILED HERE, in SQL, enforced by the cluster on every statement:
--
--   1. **The lane seal, both clauses of W-3.**
--      (a) a read reaching a lane the principal has no live edge into is
--          refused -- `holds_live_edge`, the row-shaped half of
--          `serving._entitling_edge`;
--      (b) *between wards, default deny* -- a principal who is themselves the
--          subject of a lane (a live, GENUINE self edge: `serving._acting_ward`
--          via `standing.is_self_edge`) reaches no other lane except under a
--          live guardian-signed envelope naming both lanes. This clause
--          DOMINATES clause (a): a ward holding a live edge into another lane
--          is still refused without an envelope, exactly as `serve()` refuses
--          it, and `tests/test_store_differential.py` drives that case through
--          both layers because it is the one where the two clauses disagree.
--   2. **The crossing envelope** -- `records/crossing.py::permits`: direction is
--      a property of the row (an envelope A->B does not permit B->A), liveness
--      is `signed_at <= now() < expires_at` with `invalid_at` truncating it,
--      and the signer's guardian standing is evaluated **at the instant of use**
--      and not at signature.
--   3. **The one structural rung** -- `access_grant.max_rung <> 'L5'`. It is the
--      only rung logic in this file. It is structural because a grant's ceiling
--      is a column on a row and RLS filters rows; it is defence in depth behind
--      `access_grant_max_rung`, which already makes an L5 grant unwritable, and
--      it is NOT the ceiling comparison.
--
-- NOT COMPILED, and Python-only. `records/serving.py` remains the only place
-- these are decided, and a caller that reaches a row through RLS has not
-- thereby been served it:
--
--   * **The ceiling comparison itself** (`serving._ceiling` against the field's
--     rung). A row does not know which rung the caller is asking for; the field
--     rung lives in `field_classification` per COLUMN, and RLS is per ROW.
--   * **The derive floor** (`rungs.DERIVE_AT`) and the payload/instruction
--     split. Below the floor `serve()` serves a payload with no edge at all --
--     so at L1/L2 the PREDICATE is more permissive than these policies, and the
--     store is the binding layer. Above it the two answer the same question,
--     which is why the differential suite drives an `L3` field.
--   * **`L5` is never served.** Absent here on purpose: `declination` and
--     `consent_chain.disposition` are L5 and their rows are still reachable
--     under the lane seal, because the enforcement path has to read what it
--     enforces. Nothing may render them; that is the predicate's job and §7's
--     indistinguishability guarantee, not a policy's.
--   * **L4's declared purpose, the self-edge cap and W-5's widening.** All three
--     turn on the field's category and on `principal.purposes`, neither of which
--     is a column on the row being read.
--   * **The second clock.** `serving._entitling_edge` asks *live at `at`, known
--     by `horizon`*; these policies evaluate at `now()` with the horizon equal
--     to it, which is the ordinary case and not the as-of-knowledge query an
--     audit asks. A March order delivered in October is answerable from the
--     rows and is not answerable from a policy.
--
-- The pair this creates is §16's, and the middle ships in the same commit:
-- `tests/test_store_differential.py` drives one case set through
-- `records/serving.py` with real rows AND through this cluster under RLS as the
-- app role, and fails on any disagreement in either direction.
--
-- ===========================================================================
-- SESSION IDENTITY
-- ===========================================================================
--
-- The acting principal is a per-transaction GUC, `terpsi.principal_id`, set by
-- `store/session.py::acting` with `set_config(..., is_local => true)` -- which
-- is `SET LOCAL` in a form that takes a bound parameter. A connection is not an
-- identity: the app role is one role for every principal, and the principal is
-- named per transaction and ends with it.
--
-- **An unset GUC reads NO rows, and that is rule 13 applied to a session.** An
-- anonymous session is not an entitled one, and the fail-closed direction is
-- the only one available here -- there is no "and this is what there was" for a
-- reader nobody named. `acting_principal()` returns NULL for unset, blank and
-- unparseable alike, and every policy below is false on a NULL principal.
--
-- ===========================================================================
-- FORCE ROW LEVEL SECURITY, AND WHY OWNERSHIP MOVES IN THIS FILE
-- ===========================================================================
--
-- FORCE ROW LEVEL SECURITY is set on every protected table so the table owner
-- is not exempt from its own policies. That flag names *the owner* -- and until
-- this migration the owner was whoever bootstrapped the cluster, which in every
-- environment this repository runs in is a SUPERUSER, and RLS is bypassed for
-- superusers whether FORCE is set or not. So `relforcerowsecurity = true` would
-- have been a true fact about the catalogue and evidence of nothing: the
-- attempted owner bypass would have been refused by *nobody having tried it as
-- a role the flag can bind*. That is the house lesson -- a refusal that could be
-- a different guard's is not evidence -- arriving through role attributes
-- rather than through trigger ordering.
--
-- `store/roles.py` already says "terpsi_migrator **owns** the tables. It runs
-- DDL and nothing else runs DDL." This migration makes that sentence true:
-- ownership of the fourteen public tables moves to `terpsi_migrator`, a
-- NOSUPERUSER role, and `tests/test_store_rowsecurity.py` then attempts the
-- owner bypass as that role and asserts zero rows -- with the ablation in
-- `.github/workflows/tests.yml` requiring the attack to LAND once FORCE is
-- removed, because a mutation that kills no gate is a failed mutation.
--
-- Same caveat as 001 and 002, stated again rather than assumed carried: this is
-- not proof against a superuser, who bypasses RLS, can drop a policy and can
-- take ownership back. It is proof against the application's own connection,
-- against a query somebody pastes into a running instance as the migrator, and
-- against an ORM that forgot the WHERE clause -- which is where a lane crossing
-- would actually happen.
--
-- ===========================================================================
-- THE RECURSION, AND THE THIRD ROLE
-- ===========================================================================
--
-- A policy on `edge` that asks "does this principal reach this lane" has to
-- read `edge`. PostgreSQL applies `edge`'s policies to that read too, so the
-- predicate calls itself -- forever, or until the stack ends.
--
-- The escape is a SECURITY DEFINER function whose definer sees the reference
-- tables through a policy that asks nothing: `terpsi_reach`, a NOLOGIN role
-- that owns the five functions below and holds `SELECT` plus a `USING (true)`
-- policy on exactly the three tables they read -- `edge`, `lane` and
-- `crossing_envelope`. Nothing else in the cluster grants it anything, and it
-- cannot log in.
--
-- **Its cost, named rather than discovered.** Any role that can `SET ROLE
-- terpsi_reach` reads every lane's edges, lanes and envelopes. That is the same
-- boundary the paragraph above draws: a superuser and the role that created
-- these roles are already outside it. The escape hatch does not widen the set
-- of principals who can defeat the seal; it moves the seal's own bookkeeping
-- out from under itself.
--
-- The alternative -- `ALTER ROLE ... BYPASSRLS` -- was rejected: it needs a
-- superuser at migration time, and a login role in the cluster carrying
-- BYPASSRLS is a permanent hole in exchange for one function's convenience.
--
-- ===========================================================================
-- WHAT THIS FILE DOES NOT DO
-- ===========================================================================
--
-- **It does not seal the write path**, and that is stated rather than implied.
-- Each protected table gets an `..._insert_unsealed` policy with
-- `WITH CHECK (true)`, because a table with RLS enabled and no INSERT policy
-- refuses every insert -- and this migration compiles the READ predicate.
-- Writes are held by the app role's privileges (S-1's `store/roles.py`: SELECT
-- and INSERT, no UPDATE, no DELETE), by 002's sealed-row trigger and by
-- `store/classification.py`'s registry. The policy is named for what it is so
-- that a reader of `pg_policies` sees the hole rather than inferring a seal.
-- A write predicate is a decision this migration does not make.
--
-- **It does not widen a single privilege of the app role.** No GRANT below
-- names `terpsi_app` except the EXECUTE on the five functions its own policies
-- call, which is the narrowest grant that makes the policies evaluable.

BEGIN;

-- ---------------------------------------------------------------- the roles
--
-- Created here, idempotently, because this migration is applied two ways: by
-- `store/migrate.py::run`, which calls `store/roles.py::ensure_roles` first, and
-- by `psql -f` in `.github/workflows/tests.yml`'s schema job, which does not.
-- A migration whose effect depended on which path applied it is the two-schemas-
-- one-ledger failure `store/migrate.py` exists to refuse.
--
-- `store/roles.py` is the Python spelling of the first two and is the one an
-- install runs; that is a pair, and its middle is
-- `tests/test_store_rowsecurity.py::test_the_roles_this_migration_creates_are_the_ones_store_roles_names`,
-- which reads the names out of both and fails on a disagreement in either
-- direction. `CREATE ROLE` has no `IF NOT EXISTS`, hence the DO blocks.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'terpsi_migrator') THEN
        CREATE ROLE terpsi_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'terpsi_app') THEN
        CREATE ROLE terpsi_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
    -- NOLOGIN: nothing authenticates as the definer role. It exists to be the
    -- owner of five functions and the grantee of one permissive policy.
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'terpsi_reach') THEN
        CREATE ROLE terpsi_reach NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END
$$;

GRANT USAGE, CREATE ON SCHEMA public TO terpsi_migrator;
GRANT USAGE ON SCHEMA public TO terpsi_app, terpsi_reach;

-- ------------------------------------------------------- the acting principal
--
-- `current_setting(..., missing_ok => true)` returns NULL for a GUC nobody set.
-- Blank and unparseable both return NULL too, and all three mean the same thing
-- at this layer: no principal has been named, so no row is reachable. The
-- exception block is what keeps a malformed GUC from raising in the middle of
-- somebody else's SELECT -- it fails closed rather than loudly, and the loud
-- half belongs at the seam that sets it (`store/session.py::acting` refuses a
-- blank or non-uuid principal at the call site, where a human can read it).

CREATE FUNCTION acting_principal() RETURNS uuid
    LANGUAGE plpgsql STABLE AS $$
DECLARE
    raw text;
BEGIN
    raw := current_setting('terpsi.principal_id', true);
    IF raw IS NULL OR btrim(raw) = '' THEN
        RETURN NULL;
    END IF;
    BEGIN
        RETURN btrim(raw)::uuid;
    EXCEPTION WHEN others THEN
        RETURN NULL;
    END;
END
$$;

-- --------------------------------------------------------- the reach helpers
--
-- All four read one of the three reference tables and are SECURITY DEFINER for
-- the reason in the header. They are STABLE and not IMMUTABLE: every one of
-- them reads `now()`.

-- `records/serving.py::_acting_ward`, in SQL.
--
-- The `l.subject_id = e.holder_id` join condition is `standing.is_self_edge`:
-- a row claiming `self` for somebody who is not the lane's subject is not a
-- weaker edge, it is not an edge -- and here it would be a *restriction* rather
-- than a widening, so letting a forged row decide either direction is the same
-- defect. 001's `edge_self_holder_is_subject` trigger refuses such a row at
-- write time; this refuses it at read time, and the differential suite inserts
-- one with that trigger disabled to show both layers ignore it.
--
-- `lane.subject_id` is UNIQUE, so a principal is the subject of at most one
-- lane and the LIMIT 1 is the shape of the data rather than a truncation.
CREATE FUNCTION ward_lane(principal uuid) RETURNS uuid
    LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT e.target_lane_id
      FROM edge e
      JOIN lane l ON l.lane_id = e.target_lane_id
     WHERE principal IS NOT NULL
       AND e.kind = 'self'
       AND e.holder_id = principal
       AND l.subject_id = e.holder_id
       AND e.valid_at <= now()
       AND (e.invalid_at IS NULL OR e.invalid_at > now())
     LIMIT 1
$$;

-- One lane per person (`lane.subject_id` is UNIQUE and NOT NULL), so this is a
-- lookup and not a choice. NULL for a person with no lane -- a staff member
-- nobody opened one for -- and NULL propagates to "unreachable".
CREATE FUNCTION lane_of_subject(subject uuid) RETURNS uuid
    LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT l.lane_id FROM lane l WHERE l.subject_id = subject
$$;

-- `records/serving.py::_entitling_edge`, at the granularity a row has: does
-- this principal hold a live edge into this lane at this instant. The
-- `known_at` half is not here -- see the header's list.
--
-- Scope edges (`target_scope_id` set, `target_lane_id` NULL) never match, which
-- is correct and is the fail-closed direction: "Nguyen is staff of the
-- drumline" is true and entitles nothing about any particular student's lane.
CREATE FUNCTION holds_live_edge(principal uuid, target uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT EXISTS (
        SELECT 1
          FROM edge e
         WHERE principal IS NOT NULL
           AND target IS NOT NULL
           AND e.holder_id = principal
           AND e.target_lane_id = target
           AND e.valid_at <= now()
           AND (e.invalid_at IS NULL OR e.invalid_at > now())
           AND (e.kind <> 'self' OR EXISTS (
                   SELECT 1 FROM lane l
                    WHERE l.lane_id = e.target_lane_id
                      AND l.subject_id = e.holder_id)))
$$;

-- `records/crossing.py::permits`, in SQL. Three properties, each of which the
-- Python is explicit about and each of which a hurried SQL version drops:
--
--   * **direction** -- (from, to) is ordered. An envelope permitting A to read
--     B does not permit B to read A, so there is no OR here and no symmetric
--     spelling. One signature opening two seals is the cheap violation W-3
--     exists to make unwritable.
--   * **liveness, with `invalid_at` truncating the expiry.** The Python
--     `Envelope` carries no `invalid_at` at all, so the differential suite's
--     row-to-type adapter maps an ended envelope by taking
--     `least(expires_at, invalid_at)` -- and `expires_at > now() AND (invalid_at
--     IS NULL OR invalid_at > now())` is that same statement here. The
--     equivalence is named in both places because it is a mapping decision and
--     mapping decisions are where two implementations drift.
--   * **standing at the instant of USE.** A guardian whose standing ended in
--     March cannot keep a September envelope open by having signed it. 001's
--     `crossing_envelope_guardian_signed` trigger checks standing at
--     `signed_at`; this checks it at `now()`, and they are deliberately
--     different questions.
CREATE FUNCTION envelope_permits(origin uuid, target uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT EXISTS (
        SELECT 1
          FROM crossing_envelope ce
         WHERE origin IS NOT NULL
           AND target IS NOT NULL
           AND ce.from_lane_id = origin
           AND ce.to_lane_id = target
           AND ce.signed_at <= now()
           AND ce.expires_at > now()
           AND (ce.invalid_at IS NULL OR ce.invalid_at > now())
           AND EXISTS (
                   SELECT 1 FROM edge g
                    WHERE g.kind = 'guardian_of'
                      AND g.holder_id = ce.signed_by
                      AND g.target_lane_id = ce.to_lane_id
                      AND g.valid_at <= now()
                      AND (g.invalid_at IS NULL OR g.invalid_at > now())))
$$;

-- The seal, assembled. The order of the two clauses is the order `serve()`
-- applies them and the order matters: W-3(b) is checked FIRST and can refuse a
-- principal who would pass W-3(a). A ward holding a live `guardian_of` edge
-- into a sibling's lane reaches nothing there without an envelope, which is
-- `serve()`'s behaviour exactly -- the seal sits above the entitlement check in
-- that function, and it sits above it here.
CREATE FUNCTION reaches_lane(principal uuid, target uuid) RETURNS boolean
    LANGUAGE plpgsql STABLE SECURITY DEFINER AS $$
DECLARE
    own uuid;
BEGIN
    IF principal IS NULL OR target IS NULL THEN
        RETURN false;                 -- an unnamed reader reaches nothing
    END IF;
    own := ward_lane(principal);
    IF own IS NOT NULL AND own <> target AND NOT envelope_permits(own, target) THEN
        RETURN false;                 -- W-3(b): between wards, default deny
    END IF;
    -- `own = target` falls through: the subject's own lane is reached by the
    -- self edge, which `holds_live_edge` finds. There is no separate branch,
    -- so there is no second spelling of "the subject reaches their own lane".
    RETURN holds_live_edge(principal, target);
END
$$;

ALTER FUNCTION ward_lane(uuid)        OWNER TO terpsi_reach;
ALTER FUNCTION lane_of_subject(uuid)  OWNER TO terpsi_reach;
ALTER FUNCTION holds_live_edge(uuid, uuid) OWNER TO terpsi_reach;
ALTER FUNCTION envelope_permits(uuid, uuid) OWNER TO terpsi_reach;
ALTER FUNCTION reaches_lane(uuid, uuid)     OWNER TO terpsi_reach;

-- A SECURITY DEFINER function executable by PUBLIC is an oracle: anyone with a
-- connection could ask "does principal X reach lane Y" and read a guardianship
-- out of a boolean. EXECUTE is revoked from PUBLIC and granted to the two roles
-- whose statements the policies run inside.
--
-- **The consequence is rule 13 and is worth stating**: a role that holds SELECT
-- on a sealed table and does NOT hold EXECUTE here gets
-- `permission denied for function reaches_lane` -- an error -- rather than zero
-- rows. A reader who cannot evaluate the seal has not established that there is
-- nothing to see, and the loud version is the right one. It was found by
-- running the workflow's S-1 ablation step with these grants in place, where an
-- ad-hoc role's DELETE stopped silently matching nothing and started saying why.
REVOKE EXECUTE ON FUNCTION ward_lane(uuid)              FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION lane_of_subject(uuid)        FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION holds_live_edge(uuid, uuid)  FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION envelope_permits(uuid, uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION reaches_lane(uuid, uuid)     FROM PUBLIC;
GRANT EXECUTE ON FUNCTION ward_lane(uuid)              TO terpsi_app, terpsi_migrator;
GRANT EXECUTE ON FUNCTION lane_of_subject(uuid)        TO terpsi_app, terpsi_migrator;
GRANT EXECUTE ON FUNCTION holds_live_edge(uuid, uuid)  TO terpsi_app, terpsi_migrator;
GRANT EXECUTE ON FUNCTION envelope_permits(uuid, uuid) TO terpsi_app, terpsi_migrator;
GRANT EXECUTE ON FUNCTION reaches_lane(uuid, uuid)     TO terpsi_app, terpsi_migrator;

-- What the definer role may read: the three reference tables, and nothing else.
GRANT SELECT ON edge, lane, crossing_envelope TO terpsi_reach;

-- ------------------------------------------------------- ownership, then FORCE
--
-- All fourteen, not only the eleven that get policies: "the migrator owns the
-- DDL" is a claim about the schema and a table left behind is a table a later
-- migration can alter without it.
ALTER TABLE person             OWNER TO terpsi_migrator;
ALTER TABLE lane               OWNER TO terpsi_migrator;
ALTER TABLE referent           OWNER TO terpsi_migrator;
ALTER TABLE lane_entry         OWNER TO terpsi_migrator;
ALTER TABLE scope_object       OWNER TO terpsi_migrator;
ALTER TABLE edge               OWNER TO terpsi_migrator;
ALTER TABLE access_grant       OWNER TO terpsi_migrator;
ALTER TABLE crossing_envelope  OWNER TO terpsi_migrator;
ALTER TABLE self_widening      OWNER TO terpsi_migrator;
ALTER TABLE declination        OWNER TO terpsi_migrator;
ALTER TABLE field_classification OWNER TO terpsi_migrator;
ALTER TABLE disclosure_log     OWNER TO terpsi_migrator;
ALTER TABLE consent_chain      OWNER TO terpsi_migrator;
ALTER TABLE reconciled_session OWNER TO terpsi_migrator;

-- ------------------------------------------------------------- the policies
--
-- Every policy is named, and the name is the evidence: a SELECT refused by RLS
-- returns zero rows rather than raising, so "this was refused" cannot be read
-- off an error string the way 001's and 002's refusals can. What a test can
-- assert instead is (a) zero rows for the app role, (b) the same query
-- returning the row for a reader outside the policy, and (c) the policy present
-- in `pg_policies` under this exact name with this exact expression. Those
-- three together are what keeps a zero from being some other guard's -- an
-- empty table, a missing grant, a typo in the WHERE clause.
--
-- No policy carries a TO clause, so every one applies to PUBLIC: the app role,
-- the owner under FORCE, and any role a later install adds. A policy scoped to
-- `terpsi_app` would leave the next login role reading everything.

-- person: your own row, or the row of somebody whose lane you reach. A person
-- with no lane is reachable only by themselves, which is the fail-closed answer
-- for a staff member nobody opened a lane for.
ALTER TABLE person ENABLE ROW LEVEL SECURITY;
ALTER TABLE person FORCE ROW LEVEL SECURITY;
CREATE POLICY person_lane_seal ON person FOR SELECT USING (
    person_id = acting_principal()
    OR reaches_lane(acting_principal(), lane_of_subject(person_id)));
CREATE POLICY person_insert_unsealed ON person FOR INSERT WITH CHECK (true);

ALTER TABLE lane ENABLE ROW LEVEL SECURITY;
ALTER TABLE lane FORCE ROW LEVEL SECURITY;
CREATE POLICY lane_lane_seal ON lane FOR SELECT USING (
    reaches_lane(acting_principal(), lane_id));
CREATE POLICY lane_insert_unsealed ON lane FOR INSERT WITH CHECK (true);
-- The definer role's window onto its own reference table. Permissive policies
-- are OR-ed, so this is the whole of what `terpsi_reach` sees.
CREATE POLICY lane_reach_definer ON lane FOR SELECT TO terpsi_reach USING (true);

-- lane_entry: the unit of storage, and the table the differential suite reads.
ALTER TABLE lane_entry ENABLE ROW LEVEL SECURITY;
ALTER TABLE lane_entry FORCE ROW LEVEL SECURITY;
CREATE POLICY lane_entry_lane_seal ON lane_entry FOR SELECT USING (
    reaches_lane(acting_principal(), lane_id));
CREATE POLICY lane_entry_insert_unsealed ON lane_entry FOR INSERT WITH CHECK (true);

-- edge: your own edges, plus the edges into a lane you reach. A scope edge
-- (`target_lane_id` NULL) is visible to its holder alone -- there is no lane to
-- seal it by, and inventing one would be a wildcard (W-2).
ALTER TABLE edge ENABLE ROW LEVEL SECURITY;
ALTER TABLE edge FORCE ROW LEVEL SECURITY;
CREATE POLICY edge_lane_seal ON edge FOR SELECT USING (
    holder_id = acting_principal()
    OR reaches_lane(acting_principal(), target_lane_id));
CREATE POLICY edge_insert_unsealed ON edge FOR INSERT WITH CHECK (true);
CREATE POLICY edge_reach_definer ON edge FOR SELECT TO terpsi_reach USING (true);

-- access_grant: the lane seal, and the one structural rung in this file.
ALTER TABLE access_grant ENABLE ROW LEVEL SECURITY;
ALTER TABLE access_grant FORCE ROW LEVEL SECURITY;
CREATE POLICY access_grant_lane_seal ON access_grant FOR SELECT USING (
    reaches_lane(acting_principal(), lane_id)
    AND max_rung <> 'L5');
CREATE POLICY access_grant_insert_unsealed ON access_grant FOR INSERT WITH CHECK (true);

-- crossing_envelope: reachable from either end. An envelope names two lanes and
-- both of them are parties to it; a guardian who signed it must be able to read
-- back what they signed.
ALTER TABLE crossing_envelope ENABLE ROW LEVEL SECURITY;
ALTER TABLE crossing_envelope FORCE ROW LEVEL SECURITY;
CREATE POLICY crossing_envelope_lane_seal ON crossing_envelope FOR SELECT USING (
    reaches_lane(acting_principal(), from_lane_id)
    OR reaches_lane(acting_principal(), to_lane_id));
CREATE POLICY crossing_envelope_insert_unsealed ON crossing_envelope
    FOR INSERT WITH CHECK (true);
CREATE POLICY crossing_envelope_reach_definer ON crossing_envelope
    FOR SELECT TO terpsi_reach USING (true);

-- self_widening: scoped by the ward's own lane, reached through `subject_id`.
ALTER TABLE self_widening ENABLE ROW LEVEL SECURITY;
ALTER TABLE self_widening FORCE ROW LEVEL SECURITY;
CREATE POLICY self_widening_lane_seal ON self_widening FOR SELECT USING (
    reaches_lane(acting_principal(), lane_of_subject(subject_id)));
CREATE POLICY self_widening_insert_unsealed ON self_widening
    FOR INSERT WITH CHECK (true);

-- declination: L5 throughout. The lane seal applies and the never-served rule
-- does not live here -- see the header. A surface able to render this table has
-- re-created the signal §7's guarantee suppresses, and that is a fact about the
-- surface.
ALTER TABLE declination ENABLE ROW LEVEL SECURITY;
ALTER TABLE declination FORCE ROW LEVEL SECURITY;
CREATE POLICY declination_lane_seal ON declination FOR SELECT USING (
    reaches_lane(acting_principal(), lane_id));
CREATE POLICY declination_insert_unsealed ON declination FOR INSERT WITH CHECK (true);

-- disclosure_log: FERPA §99.32's record, sealed by the lane it is about. A row
-- whose `lane_id` is NULL is reachable by no principal through this policy;
-- that is deliberate and fail-closed, and it is why `store/narration.py` writes
-- the lane on every entry.
ALTER TABLE disclosure_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE disclosure_log FORCE ROW LEVEL SECURITY;
CREATE POLICY disclosure_log_lane_seal ON disclosure_log FOR SELECT USING (
    reaches_lane(acting_principal(), lane_id));
CREATE POLICY disclosure_log_insert_unsealed ON disclosure_log
    FOR INSERT WITH CHECK (true);

ALTER TABLE consent_chain ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_chain FORCE ROW LEVEL SECURITY;
CREATE POLICY consent_chain_lane_seal ON consent_chain FOR SELECT USING (
    reaches_lane(acting_principal(), lane_id));
CREATE POLICY consent_chain_insert_unsealed ON consent_chain
    FOR INSERT WITH CHECK (true);

-- reconciled_session carries NO lane, so this is NOT the lane seal and the
-- policy's name says so. Its scoping is the session's own principal, which is
-- the nearest honest answer while §18 item 4's surface is unbuilt. Leaving an
-- L4 table with no policy at all in a migration named "row security" would be
-- the ledger/enforcement confusion rule 18 is about.
ALTER TABLE reconciled_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciled_session FORCE ROW LEVEL SECURITY;
CREATE POLICY reconciled_session_principal_seal ON reconciled_session FOR SELECT USING (
    principal_id = acting_principal());
CREATE POLICY reconciled_session_insert_unsealed ON reconciled_session
    FOR INSERT WITH CHECK (true);

-- ------------------------------------------------- the three left unprotected
--
-- Named here rather than left to be noticed, because a table with no policy and
-- a table nobody thought about look identical from `pg_policies`.
--
--   * `referent` -- W-3's "a shared event is two lane entries with one
--     referent". It carries no person reference and no roster column by
--     construction, and `tests/test_lane_model.py` asserts that absence. A
--     rehearsal's label and time are L1/PUBLIC. Sealing it by lane would
--     require a lane column, which is the roster column the table exists to
--     forbid.
--   * `scope_object` -- §8's Org/Program/Ensemble/Season/Event spine, holding
--     no participants for the same reason.
--   * `field_classification` -- the registry. INTERNAL/L2, and it is the thing
--     the store checks writes against; a policy over it would make the check
--     depend on who is asking.
--
-- `tests/test_store_rowsecurity.py` asserts this list is exactly the set of
-- public tables without RLS, so a table added later without a decision fails
-- the build rather than arriving unprotected.

COMMIT;
