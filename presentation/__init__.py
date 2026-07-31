"""The middle between the domain and the four doors.

§18 item 4 closed on `docs/survey/scout-21-surfaces-a11y.md` §3: four rendering
backends over **one** presentation IR. This package is that IR, the one mapping
table rule 14 requires, the tokens, and the render-and-diff that keeps the
templates and their committed output from drifting.

The division of knowledge is the whole point and it runs both ways:

* **Nothing in a backend knows about students.** `surfaces/*` import this
  package and never `records`; `tests/test_surfaces.py` asserts it by AST.
* **Nothing in the domain knows about colour.** `records/*` carry rungs, seal
  states and dates; no hex, no ANSI, no token name. This package is the only
  place the two vocabularies meet.

Stdlib only. No network, no store, no model.
"""
