-- 002_seal_history.sql
--
-- Migration 002. Adds no table and no column: one function and one trigger,
-- which is why it seeds no field_classification rows and why
-- tools/registry.py's parse of 001 stays complete.
--
-- Governed by docs/PLAN-STORE.md decision 2 and by docs/ARCHITECTURE.md §8.2.
-- Where this file and those disagree, they win and this file is the defect.
--
-- THE RULE
--
-- "Sealed rows are insert-only history: readable by the app role, rewritable by
-- nobody, invalid_at the only ending (refusal 3)."
--
-- The privilege half is store/roles.py: terpsi_app holds SELECT and INSERT and
-- holds no UPDATE, DELETE or TRUNCATE on any table. That is proof against the
-- application and it is not proof about *sealed rows* — with no UPDATE grant at
-- all, an attempt on a sealed row and an attempt on a draft are refused
-- identically, so nothing in the cluster distinguishes the two and the claim
-- "sealed rows are rewritable by nobody" would rest on a role's grants rather
-- than on the row's state. This trigger is what makes the sentence true of the
-- row, including for the owner role and for a migration written in a hurry.
--
-- Same caveat as 001's triggers, stated again rather than assumed carried: not
-- proof against a superuser, who can drop it. Nothing in a schema is.
--
-- WHAT IT PERMITS, AND WHY THAT IS NOT A HOLE
--
-- invalid_at may be set on a sealed row, and nothing else may change. Refusal 3
-- is explicit that standing ends by a date and never by a delete, so a schema
-- that froze sealed rows completely would leave a court order arriving
-- mid-season with nowhere to land -- and the only remaining spelling would be a
-- DELETE. Permitting exactly the dated ending is what keeps the deletion
-- unnecessary.
--
-- The comparison is column by column rather than `NEW IS DISTINCT FROM OLD`
-- with invalid_at nulled out, because the second reads as clever and stops
-- being true the moment a column is added: a new column would be silently
-- editable on a sealed row. Listing them means a column added without a thought
-- for this rule is refused by default, which is the direction that fails safe.
--
-- A DELETE is refused unconditionally. There is no state in which the history
-- of a seal should stop existing (rule 16: a student's entries are as durable
-- as entries about them, and no role's authority extends to deleting the record
-- of its own exercise).
--
-- ORDER, STATED BECAUSE 001 LEARNED IT THE EXPENSIVE WAY
--
-- A BEFORE ROW trigger fires ahead of every CHECK, NOT NULL and foreign key on
-- the same row, so an attack that asserts only "this was refused" can be
-- satisfied by a guard other than the one under test. Everything attacking this
-- trigger asserts on the string it raises -- 'sealed lane_entry' -- and the
-- app-role attacks assert on SQLSTATE 42501 and the table named in it, because
-- a privilege refusal happens before any trigger runs and the two must not be
-- allowed to stand in for each other.

BEGIN;

CREATE FUNCTION refuse_sealed_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
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

    IF NEW.entry_id    IS DISTINCT FROM OLD.entry_id
    OR NEW.lane_id     IS DISTINCT FROM OLD.lane_id
    OR NEW.referent_id IS DISTINCT FROM OLD.referent_id
    OR NEW.kind        IS DISTINCT FROM OLD.kind
    OR NEW.payload     IS DISTINCT FROM OLD.payload
    OR NEW.author_id   IS DISTINCT FROM OLD.author_id
    OR NEW.seal_state  IS DISTINCT FROM OLD.seal_state
    OR NEW.sealed_by   IS DISTINCT FROM OLD.sealed_by
    OR NEW.created_at  IS DISTINCT FROM OLD.created_at
    OR NEW.valid_at    IS DISTINCT FROM OLD.valid_at
    THEN
        RAISE EXCEPTION
            'a sealed lane_entry is insert-only history; only invalid_at may be '
            'set on it, and a named human sealed this body (records/sealing.py, '
            'ARCHITECTURE §8.2)';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER lane_entry_sealed_is_history
    BEFORE UPDATE OR DELETE ON lane_entry
    FOR EACH ROW EXECUTE FUNCTION refuse_sealed_mutation();

COMMIT;
