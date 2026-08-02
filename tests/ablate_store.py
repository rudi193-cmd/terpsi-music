"""Ablate the guards that need a cluster, and require the attacks to land.

Rule 19 — *a guard that cannot be shown to fail has not been shown to work* —
for the half of the read predicate that lives in SQL and for the half of it that
does not. `tests/ablate.py` covers the guards that can be mutated with no
database; these cannot, so they are ablated here and this file is run by
`.github/workflows/tests.yml`'s schema job rather than by the guards job.

**Two files are mutated and that is the whole design.** S-2 creates §16's pair —
one read predicate, two implementations — and a middle is only worth anything if
breaking *either side* turns it red. So the table below breaks
`migrations/003_row_security.sql` and `records/serving.py` and
`records/crossing.py`, and each row names which suite must notice.

**A mutation that kills no gate is a failed mutation, not a passing one**
(scout-13 row B, and the workflow's own ablation step says it in the same
words). Every row is checked to have changed the file before its result counts:
a pattern that no longer matches leaves the file untouched, the suite green, and
a naive harness reporting `SURVIVES` for a mutation that never happened. `NOT
APPLIED` and `AMBIGUOUS` are errors here, not passes.

**The control runs first.** A suite that is already red reports `caught` for
every mutation aimed at it while proving nothing — `tests/ablate.py` lost
eighteen results to exactly that on 2026-07-31. Both suites are run unmutated
before anything is touched, and a red control ends the run.

**One survivor is recorded here rather than hidden**, because a table of all
`caught` invites nobody to read it: **the compiled envelope's direction cannot
be ablated through the differential**, and the row that tries declares
`survives` with the assertion that does catch it in the row beneath it. Reversing an
envelope changes a *reach* only for a principal who is a ward of one lane and
holds an entitlement edge into another, and a crossing does not widen the
entitlement edge — so in this domain no such principal exists. It is caught by
`tests/test_store_rowsecurity.py::test_the_compiled_envelope_is_directional`,
one level below reach, and that row is in the table too.

**Needs a cluster, and says so.** With none, this exits `2` with a loud
`UNKNOWN` — never a skip, never a pass (`tests/cluster.py`).

    python3 tests/ablate_store.py
"""

from __future__ import annotations

import atexit
import json
import signal
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from cluster import ClusterUnknown, available  # noqa: E402

#: What is mutated right now, and what it was. Written **before** the edit, so a
#: run killed between the write and the restore leaves a breadcrumb rather than
#: a mutated migration on disk — `tests/ablate.py`'s mechanism, for its reason: a
#: `SIGTERM` does not run a `finally`, and a mutated
#: `migrations/003_row_security.sql` left behind is a store with no seal.
INFLIGHT = ROOT / ".ablate-store-inflight.json"

DIFFERENTIAL = "tests/test_store_differential.py"
ROWSECURITY = "tests/test_store_rowsecurity.py"
#: G-D's own suite. Here rather than in `tests/ablate.py` for that table's
#: stated reason — it needs a cluster, and `tests/ablate.py` derives its control
#: list from its mutations, so a row pointing here would turn the whole
#: no-database guards job red rather than ablate anything.
ROLES = "tests/test_store_roles.py"

#: (file, pattern, replacement, label, suite that must catch it, expected)
#:
#: `expected` is `"caught"` for every row but one, and the exception is written
#: down rather than left out — a survivor nobody declared is a hole, and a
#: survivor a table declares is a boundary. See the module docstring.
MUTATIONS: Tuple[Tuple[str, str, str, str, str, str], ...] = (
    # --- the compiled half: migrations/003_row_security.sql ------------------
    ("migrations/003_row_security.sql",
     "CREATE POLICY lane_entry_lane_seal ON lane_entry FOR SELECT USING (\n"
     "    reaches_lane(acting_principal(), lane_id));",
     "CREATE POLICY lane_entry_lane_seal ON lane_entry FOR SELECT USING (true);",
     "the lane seal stops consulting the principal", ROWSECURITY, "caught"),
    ("migrations/003_row_security.sql",
     "CREATE POLICY lane_entry_lane_seal ON lane_entry FOR SELECT USING (\n"
     "    reaches_lane(acting_principal(), lane_id));",
     "CREATE POLICY lane_entry_lane_seal ON lane_entry FOR SELECT USING (true);",
     "…and the two layers stop agreeing about it", DIFFERENTIAL, "caught"),
    ("migrations/003_row_security.sql",
     "    IF own IS NOT NULL AND own <> target AND NOT envelope_permits(own, target) THEN\n"
     "        RETURN false;                 -- W-3(b): between wards, default deny\n"
     "    END IF;",
     "    IF false THEN\n        RETURN false;\n    END IF;",
     "W-3(b): between wards, default deny", DIFFERENTIAL, "caught"),
    ("migrations/003_row_security.sql",
     "       AND l.subject_id = e.holder_id\n       AND e.valid_at <= now()",
     "       AND e.valid_at <= now()",
     "ward_lane stops checking is_self_edge", DIFFERENTIAL, "caught"),
    ("migrations/003_row_security.sql",
     "           AND (e.kind <> 'self' OR EXISTS (\n"
     "                   SELECT 1 FROM lane l\n"
     "                    WHERE l.lane_id = e.target_lane_id\n"
     "                      AND l.subject_id = e.holder_id)))",
     "           AND (true))",
     "holds_live_edge stops filtering forged self edges", DIFFERENTIAL, "caught"),
    ("migrations/003_row_security.sql",
     "           AND (e.invalid_at IS NULL OR e.invalid_at > now())\n"
     "           AND (e.kind <> 'self' OR EXISTS (",
     "           AND (true)\n           AND (e.kind <> 'self' OR EXISTS (",
     "an edge dated closed keeps entitling (refusal 3)", DIFFERENTIAL, "caught"),
    ("migrations/003_row_security.sql",
     "           AND (ce.invalid_at IS NULL OR ce.invalid_at > now())",
     "           AND (true)",
     "an envelope dated closed stays live (refusal 3)", DIFFERENTIAL, "caught"),
    ("migrations/003_row_security.sql",
     "           AND ce.expires_at > now()",
     "           AND (true)",
     "an expired envelope stays live (W-5)", DIFFERENTIAL, "caught"),
    ("migrations/003_row_security.sql",
     "                      AND (g.invalid_at IS NULL OR g.invalid_at > now())))",
     "                      AND (true)))",
     "the signer's standing stops being checked at use", DIFFERENTIAL, "caught"),
    ("migrations/003_row_security.sql",
     "           AND ce.from_lane_id = origin\n           AND ce.to_lane_id = target",
     "           AND (ce.from_lane_id = origin OR ce.to_lane_id = origin)\n"
     "           AND (ce.to_lane_id = target OR ce.from_lane_id = target)",
     "the envelope becomes symmetric [survivor: see the row below]",
     DIFFERENTIAL, "survives"),
    ("migrations/003_row_security.sql",
     "           AND ce.from_lane_id = origin\n           AND ce.to_lane_id = target",
     "           AND (ce.from_lane_id = origin OR ce.to_lane_id = origin)\n"
     "           AND (ce.to_lane_id = target OR ce.from_lane_id = target)",
     "…and the assertion that does catch direction", ROWSECURITY, "caught"),
    ("migrations/003_row_security.sql",
     "ALTER TABLE lane_entry FORCE ROW LEVEL SECURITY;",
     "-- FORCE ROW LEVEL SECURITY removed by tests/ablate_store.py",
     "FORCE removed: the owner is exempt again", ROWSECURITY, "caught"),
    ("migrations/003_row_security.sql",
     "ALTER TABLE person             OWNER TO terpsi_migrator;",
     "-- ownership left with the bootstrap role by tests/ablate_store.py",
     "the owner stays a superuser, so FORCE binds nobody", ROWSECURITY, "caught"),
    ("migrations/003_row_security.sql",
     "GRANT EXECUTE ON FUNCTION reaches_lane(uuid, uuid)     TO terpsi_app, terpsi_migrator;",
     "GRANT EXECUTE ON FUNCTION reaches_lane(uuid, uuid) TO PUBLIC;",
     "the reach helper becomes a public oracle", ROWSECURITY, "caught"),

    # --- the Python half: records/, ablated against the same middle ----------
    ("records/serving.py",
     "    if (lane_id is not None and lane_id != fld.lane_id) or (\n"
     "            ward is not None and ward != fld.subject_id):",
     "    if (lane_id is not None and lane_id != fld.lane_id) or (\n"
     "            False):",
     "serve() stops sealing a ward out by ward", DIFFERENTIAL, "caught"),
    ("records/serving.py",
     "        if (e.subject_id == subject_id and e.principal_id == principal_id\n"
     "                and e.live_at(at) and e.known_at(horizon)):",
     "        if (e.subject_id == subject_id and e.principal_id == principal_id\n"
     "                and e.known_at(horizon)):",
     "_entitling_edge stops checking liveness", DIFFERENTIAL, "caught"),
    ("records/serving.py",
     "        if e.kind == SELF and e.principal_id != e.subject_id:",
     "        if False:",
     "_entitling_edge stops filtering forged self edges", DIFFERENTIAL, "caught"),
    ("records/serving.py",
     "        if is_self_edge(e) and e.principal_id == principal_id and e.live_at(at):",
     "        if e.kind == SELF and e.principal_id == principal_id and e.live_at(at):",
     "_acting_ward trusts a forged self edge", DIFFERENTIAL, "caught"),
    ("records/crossing.py",
     "        if env.from_lane != from_lane or env.to_lane != to_lane:",
     "        if env.to_lane != to_lane:",
     "permits() stops checking direction", DIFFERENTIAL, "caught"),
    ("records/crossing.py",
     "        if not env.live_at(at):",
     "        if False:",
     "permits() stops checking the expiry", DIFFERENTIAL, "caught"),

    # --- G-D: what the role state reports, against what it read --------------
    #
    # The retired `app_privileges`, restored at the one site that brings it
    # back. A field with this default is not a caricature of the defect, it is
    # the defect: the value was `APP_HOLDS` and it was constructed by
    # `ensure_roles`, which `store/migrate.py`'s `run()` calls *before*
    # `apply_all` and `apply_grants` — so the app role held neither privilege at
    # the moment the field claimed both.
    #
    # It has to be ablated against a cluster because that is what makes the row
    # a lie rather than merely an assumption: the assertion is that the cluster
    # reports nothing held while the value reports two, and only a cluster can
    # be asked the first half.
    ("store/roles.py",
     "    created: Tuple[str, ...]      # roles that did not exist before this call",
     "    created: Tuple[str, ...]      # roles that did not exist before this call\n"
     '    app_privileges: Tuple[str, ...] = ("SELECT", "INSERT")',
     "the role state asserts a privilege nobody read", ROLES, "caught"),
)


def _restore(record) -> str:
    path = ROOT / record["target"]
    path.write_text(record["original"], encoding="utf-8")
    return record["target"]


def _recover() -> str:
    if not INFLIGHT.exists():
        return ""
    try:
        record = json.loads(INFLIGHT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    name = _restore(record)
    INFLIGHT.unlink(missing_ok=True)
    return name


def _restore_on_signal() -> None:
    """`SIGTERM` does not run a `finally`. A CI timeout is a `SIGTERM`."""
    def bail(signum, _frame):
        raise SystemExit(f"killed by signal {signum}")
    for sig in (signal.SIGTERM, signal.SIGINT, getattr(signal, "SIGHUP", None)):
        if sig is not None:
            try:
                signal.signal(sig, bail)
            except (OSError, ValueError):  # pragma: no cover
                pass
    atexit.register(lambda: _recover())


def run(suite: str) -> Tuple[bool, int]:
    """`(green, exit code)`. Exit 2 is the cluster's UNKNOWN and is not green."""
    r = subprocess.run([sys.executable, suite], cwd=ROOT,
                       capture_output=True, text=True)
    return r.returncode == 0, r.returncode


def ablate(target: str, pattern: str, repl: str, suite: str) -> str:
    path = ROOT / target
    original = path.read_text(encoding="utf-8")
    seen = original.count(pattern)
    if seen == 0:
        return "NOT APPLIED"           # an error, not a pass
    if seen > 1:
        return f"AMBIGUOUS x{seen}"    # the first site mutates, another reports
    INFLIGHT.write_text(json.dumps({"target": target, "original": original}),
                        encoding="utf-8")
    try:
        path.write_text(original.replace(pattern, repl, 1), encoding="utf-8")
        green, code = run(suite)
        if code == 2:
            return "UNKNOWN (no cluster)"
        return "survives" if green else "caught"
    finally:
        path.write_text(original, encoding="utf-8")
        INFLIGHT.unlink(missing_ok=True)


def main() -> int:
    ok, why = True, ""
    try:
        ok, why = available()
    except ClusterUnknown as exc:  # pragma: no cover
        ok, why = False, str(exc)
    if not ok:
        print(f"\nUNKNOWN — tests/ablate_store.py: {why}")
        print("  No ablation ran. That is not a pass (rule 13).")
        return 2

    _restore_on_signal()
    recovered = _recover()
    if recovered:
        print(f"  recovered {recovered} — a previous run was killed mid-mutation")

    print("  control".ljust(56), end="", flush=True)
    healthy = all(run(s)[0] for s in (DIFFERENTIAL, ROWSECURITY, ROLES))
    print("green" if healthy else "RED — every result below is meaningless")
    if not healthy:
        return 1

    bad: List[str] = []
    for target, pattern, repl, label, suite, expected in MUTATIONS:
        result = ablate(target, pattern, repl, suite)
        note = "" if result == expected else f"   WANTED {expected}"
        print(f"  {label:<54}{result}{note}")
        if result != expected:
            bad.append(f"{label}: {result}, wanted {expected}")

    print()
    if bad:
        for line in bad:
            print(f"  FAIL {line}")
        return 1
    survivors = [m[3] for m in MUTATIONS if m[5] != "caught"]
    print(f"  {len(MUTATIONS) - len(survivors)} of {len(MUTATIONS)} mutations "
          "die where the table says they should")
    if survivors:
        print(f"  {len(survivors)} declared survivor(s), each with the assertion "
              "that does catch it in the row beneath it:")
        for label in survivors:
            print(f"    - {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
