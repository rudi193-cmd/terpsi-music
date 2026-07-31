"""Four doors, visible on `ls`.

`scout-21` §3, adopted as §18 item 4's answer: **four rendering backends over
one presentation middle, three trust paths.** Not `frontend/` and `backend/` —
that layout would absorb three surfaces with different personas and different
trust paths into one tree, and §4 opens by forbidding exactly that: *"Do not
build one door."*

| door | serves | trust path |
|---|---|---|
| `tui` | staff, techs, on-site and off-site directors | org hardware, or the tailnet |
| `web` | guardians (the transactional 5%), and judges and clinicians on a kiosk | one renderer, two entry points, two session models |
| `print` | the printed program, the printed roster, the W-6 lane export | paper, which is a backend and not an export |
| `text` | screen readers, `TERM=dumb`, every `--format=text` export, and the parity test | the instrument the other three are checked against |

**Nothing in here knows about students.** These modules import
`presentation/` and never `records/`; `tests/test_surfaces.py` asserts it by
AST, in both the import statement and the `from` form. A backend that could
reach a record would be a second read path, and the second one never has the
rules.

**Skeletons, deliberately.** Each door is a renderer over the IR and nothing
else — no framework, no server, no session. The frameworks `scout-21` names
(Textual, htmx, WeasyPrint) consume what these produce; choosing them is not
this commit, and the manifest declares no listener because none of these opens
one.

Stdlib only. No network — `manifest.json` declares no listeners and
`tools/manifest.py` reconciles that against the source on every run.
"""
