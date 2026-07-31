-- A decoy migration. NEVER APPLIED, and not a schema anybody should copy.
--
-- It exists so `tools/registry.py` can be pointed at a classification registry
-- that has drifted from `records/classify.py` and shown to complain — rule 19,
-- and the reason the middle is worth having before the seed drifts for real.
-- `tests/test_registry.py` asserts every row below is caught, by name.
--
-- Every drift here is one a reviewer would wave through. That is the point:
-- the seed is 116 rows of four short strings, and none of them looks wrong on
-- its own.
--
--   person.chair                 the control — PII_MINOR/L3, and correct
--   person.sis_legal_name        also correct, and only through classify.py:
--                                the class says L3 and the decided field-name
--                                case says L4, so a table lookup would report
--                                this as an unexplained elevation
--   person.chosen_name           the other half of the inversion — L3, and a
--                                checker that elevated it would be inverting
--                                the guarantee while appearing to strengthen it
--   person.allergy_note          HEALTH served at L3: a rung BELOW what the
--                                class derives, which is the direction a
--                                mistake discloses in
--   person.safeguarding_note     a class nobody has decided; classify.py
--                                returns UNDECIDED and this must not become a
--                                rung (rule 13)
--   person.chair_assignment      an elevation to L4 with nothing recording
--                                which rule reaches it
--   person.favourite_colour      declared, and absent from the seed
--   person.a_column_that_moved   seeded, and declared by nothing

CREATE TABLE person (
    person_id        uuid PRIMARY KEY,
    chair            text,
    sis_legal_name   text,
    chosen_name      text,
    allergy_note     text,
    safeguarding_note text,
    chair_assignment text,
    favourite_colour text
);

INSERT INTO field_classification (table_name, column_name, data_class, rung) VALUES
    ('person','person_id','PII_MINOR','L3'),
    ('person','chair','PII_MINOR','L3'),
    ('person','sis_legal_name','PII_MINOR','L4'),
    ('person','chosen_name','PII_MINOR','L3'),
    ('person','allergy_note','HEALTH','L3'),
    ('person','safeguarding_note','SAFEGUARDING','L4'),
    ('person','chair_assignment','PII_MINOR','L4'),
    ('person','a_column_that_moved','INTERNAL','L2');
