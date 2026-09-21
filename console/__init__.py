"""The operator/director console: a local terminal session over the store.

`docs/PLAN-STORE.md` S-4 — the first surface with real data behind it, and where
§7.2's knock is wired in enforcement mode. Three files, each thin:

* `session.py` — the vertical: knock (`records/commentary.py`'s session model),
  acting principal (`store/session.py`), a read through row-level security *and*
  `records/serving.py`'s predicate (`store/narration.py::serve_field`), narration
  in the same transaction, and an exit that reconciles declared against observed
  and lands the `reconciled_session` row (`store/reconcile.py`).
* `render.py` — the `presentation/` IR into `surfaces/text`/`surfaces/tui`, with
  monochrome as the exact floor.
* `__main__.py` — the terminal driver loop. No framework (decision 8, note 4).

**Why this is not under `surfaces/`.** A surface renders the IR and knows nothing
about students; `tests/test_surfaces.py` asserts by AST that `surfaces/` imports
`presentation/` and never `records/` or `store/`. This session must reach the
store, so it sits one layer above the surfaces and drives them — it is the wiring
§4's *"do not build one door"* keeps out of the doors themselves.

**Read-first (R16).** Nothing here calls the record-write path
(`store/writing.py`); it reads, narrates, and reconciles. The write surface —
attendance marks, a human sealing a draft — waits on install acceptance and the
escrow rehearsal (§11.1) and is named there, not built here.
"""
