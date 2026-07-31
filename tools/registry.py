"""The classification registry, reconciled three ways.

§9 item 2 records the state of this as *"the class-to-L mapping is **written but
unenforced**, and enforcement is the work."* Since that was written enforcement
landed **twice, independently**:

* `records/classify.py` implements `docs/SENSITIVITY.md`'s five-step procedure
  and returns `UNDECIDED` where the clause needs a human;
* `migrations/001_lanes.sql` seeds `field_classification` with a `(class, rung)`
  pair for every column the DDL declares.

Two implementations of one mapping, with nothing between them, is the shape
rule 12 and §16 exist to forbid — and the drift it produces is silent in the
disclosure direction. **This module is the middle.** It parses the seed out of
the migration as text, asks `records/classify.py` what the same field derives,
and holds both against `docs/SENSITIVITY.md`'s class-to-`L` table.

**What is compared, and against what.**

* **registry ↔ classify.** Every seeded row is turned back into a
  `Descriptor` — via `CLASS_FACTS`, which records what each §6 class *asserts
  about a field* and no rungs at all — and `classify()` decides the rung. The
  column name goes in too, so the decided field-name cases (`chosen_name`,
  `sis_legal_name`) are applied rather than bypassed. A registry rung that is
  not what the procedure derives is a disagreement naming the field.
* **classify ↔ SENSITIVITY.md.** `bridge()` runs each class's facts through
  `classify()` and requires the answer to be the rung the document's table
  gives. That is the leg which keeps `CLASS_FACTS` from becoming a third copy
  of the mapping: it declares facts, and the rungs come from the procedure.
* **registry ↔ the DDL.** A declared column with no row is `UNCLASSIFIED`; a
  row for a column nothing declares is `STALE`. Both are findings.

**Elevation is not disagreement, and it is not a free pass either.**
`SENSITIVITY.md` provides two routes to a rung above the one a class implies —
step 4's three `L5` rules, and step 3's general clause reaching `L4` — and says
of the second that *"the clause stays human-evaluated at schema-definition time
and the enumeration of decided cases is what the build checks."* `ELEVATIONS` is
that enumeration. It carries no mapping: one entry per elevated column, naming
the rule and quoting where the reason is recorded. An elevation with an entry is
reconciled; an elevation with none is `UNDECIDED` — **named, with both values,
and not a pass** (rule 13). Deciding it is a human act and this module does not
make judgments, for the same reason `classify.py` does not.

Only *upward* differences can be elevations. A rung below what the class derives
is a disagreement whatever is written beside it, because that is the direction
in which a mistake discloses.

**One parser.** `strip_comments`, `tables`, `columns` and `classified` live here
and `tests/test_lane_model.py` imports them. They were written there first; a
second copy in this file would have been the pair this file exists to close.

    python3 tools/registry.py

Stdlib only. No network. No database — the migration is read as text.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records.classify import Classification, Decision, Descriptor, classify  # noqa: E402
from records.rungs import Rung, outranks  # noqa: E402

MIGRATIONS = ROOT / "migrations"
SCHEMA = MIGRATIONS / "001_lanes.sql"
SENSITIVITY = ROOT / "docs" / "SENSITIVITY.md"


# --- the SQL text parse ----------------------------------------------------
#
# Moved here from `tests/test_lane_model.py`, which now imports it. The DDL is
# read as text on purpose: the checks are structural, and requiring a database
# would mean they ran where a database happened to be rather than on every push.

_TABLE = re.compile(r"CREATE TABLE (\w+)\s*\((.*?)\n\);", re.DOTALL)
_NOT_A_COLUMN = ("constraint", "primary", "unique", "check", "foreign", "exclude")

#: `ALTER TABLE t ADD COLUMN …;` / `ALTER TABLE t ADD CONSTRAINT … CHECK (…);`
#:
#: **The schema is every migration, not the first one.** Until migration 004 the
#: two were the same file and nothing distinguished them; 004 adds columns by
#: `ALTER`, and a parser that reads only `CREATE TABLE` would report a schema
#: this tree stopped having — silently, and in the direction that widens what a
#: checker believes is classified. Folded into the table body rather than kept
#: beside it, so `columns()` and every `CHECK`-reading caller see one text.
_ALTER = re.compile(
    r"ALTER TABLE (\w+)\s+ADD\s+(COLUMN\s+.*?|CONSTRAINT\s+.*?);", re.DOTALL | re.I)

# "    ('lane_entry','payload','HEALTH','L4'),"
_CLASSIFIED = re.compile(
    r"\(\s*'(\w+)'\s*,\s*'(\w+)'\s*,\s*'([A-Z_]+)'\s*,\s*'(L[1-5])'\s*\)")

# "| `PII_MINOR` | `L3` | Anything identifying a student |"
_CLASS_ROW = re.compile(r"^\|\s*`([A-Z][A-Z_]+)`\s*\|\s*`(L[1-5])`\s*\|", re.M)


def strip_comments(sql: str) -> str:
    """`--` to end of line. No string literal in this file contains `--`; a
    future one would need this to become a real tokenizer."""
    return "\n".join(line.split("--")[0].rstrip() for line in sql.splitlines())


def schema_text(where: Optional[Path] = None) -> str:
    """Every migration, in filename order, as one text.

    **One place composes it.** The registry, `store/classification.py` and
    `store/sealing_plan.py` all need *the schema this tree defines*, and three
    concatenations of `migrations/*.sql` would be three chances to read a
    different schema — the pair §16 is about, three times over. `store/migrate.py`
    applies the same files in the same order, which is what makes this text and
    a migrated cluster the same schema.
    """
    base = MIGRATIONS if where is None else Path(where)
    return "\n".join(p.read_text(encoding="utf-8")
                     for p in sorted(base.glob("*.sql"), key=lambda p: p.name))


def tables(sql: str) -> Dict[str, str]:
    """`{table: body}`, with every `ALTER TABLE … ADD` folded into the body.

    A column added by a later migration is a column of the table, and a reader
    that only saw `CREATE TABLE` would classify a schema that no longer exists.
    """
    stripped = strip_comments(sql)
    out = {m.group(1): m.group(2) for m in _TABLE.finditer(stripped)}
    for m in _ALTER.finditer(stripped):
        table, clause = m.group(1), " ".join(m.group(2).split())
        if table not in out:
            continue
        if clause.lower().startswith("column "):
            clause = clause[len("column "):]
        out[table] = out[table] + f"\n    {clause},"
    return out


def columns(body: str) -> Dict[str, str]:
    """{column name: the rest of its definition}.

    Paren-aware. A line-based reader treats the continuation lines of a
    multi-line CHECK as columns — `edge_kind`'s value list yields a phantom
    column named `'guardian_of',` and another named `))`. Harmless while
    nothing iterated the column set; wrong the moment something did."""
    out: Dict[str, str] = {}
    depth = 0
    for line in body.splitlines():
        s = line.strip()
        candidate = s.rstrip(",")
        if depth == 0 and candidate:
            first = candidate.split()[0]
            if first.lower() not in _NOT_A_COLUMN and first.isidentifier():
                name, _, rest = candidate.partition(" ")
                out[name] = rest.strip()
        depth = max(0, depth + s.count("(") - s.count(")"))
    return out


def classified(sql: str) -> Dict[Tuple[str, str], Tuple[str, str]]:
    """{(table, column): (class, rung)} from the classification seed."""
    return {
        (m.group(1), m.group(2)): (m.group(3), m.group(4))
        for m in _CLASSIFIED.finditer(strip_comments(sql))
    }


def declared_columns(sql: str) -> Tuple[Tuple[str, str], ...]:
    """Every (table, column) the DDL declares."""
    return tuple(sorted((tn, cn) for tn, body in tables(sql).items()
                        for cn in columns(body)))


def documented_rungs(text: str) -> Dict[str, str]:
    """`docs/SENSITIVITY.md`'s class-to-`L` table, as {class: "L3"}.

    Empty is a fact and not a default: a document whose table has moved out of
    reach of this regex makes the whole reconciliation vacuous rather than
    clean."""
    return dict(_CLASS_ROW.findall(text))


# --- the bridge: what a class asserts about a field ------------------------
#
# **No rungs here.** Each entry is the §6 class's own one-line definition
# expressed as the facts `Descriptor` carries, and the rung is whatever
# `classify()` then derives. `bridge()` requires that answer to equal
# SENSITIVITY.md's table for all eight, so this cannot quietly become a second
# copy of the mapping — if it drifts, the rung it produces stops matching the
# document and the check says so.

CLASS_FACTS: Dict[str, dict] = {
    # "Performance dates, venue, ensemble name" — survives publication.
    "PUBLIC": dict(publishable=True),
    # "Non-identifying operational data."
    "INTERNAL": dict(identifies_a_person=False),
    # "Aggregates that survive a re-identification check." Both halves are
    # recorded: derived, and the check passed. A derived field whose check has
    # *not* passed is not this class — it is a state, and it inherits the max
    # of its inputs (§18 item 14). The input rung below is immaterial once the
    # check has passed, and `tests/test_registry.py` pins that by flipping it.
    "DERIVED_ANON": dict(identifies_a_person=False,
                         derived_from=(Rung.L3,),
                         passed_reidentification_check=True),
    # "Anything identifying a student."
    "PII_MINOR": dict(identifies_a_person=True),
    # "Contacts, addresses, relationships."
    "PII_GUARDIAN": dict(identifies_a_person=True),
    # The three that carry one of step 3's four familiar categories.
    "HEALTH": dict(identifies_a_person=True, category="health"),
    "FINANCIAL": dict(identifies_a_person=True, category="money"),
    "MEDIA_MINOR": dict(identifies_a_person=True, category="likeness"),
}

#: A name no decided field-name case matches, for probing a class on its own.
_PROBE = "a_field"


def derive(column: str, data_class: str) -> Classification:
    """What `records/classify.py` makes of a field of this class with this name.

    The column name is passed through rather than dropped, so `chosen_name` and
    `sis_legal_name` reach their decided cases. That is the difference between
    routing through the procedure and looking up a table — a lookup would report
    the legal record's `L4` as an unexplained elevation.

    A class outside the vocabulary is handed to `classify()` as an undecided
    *category*, which is what it is: nobody has decided what it means, so the
    answer is `UNDECIDED` and not a rung.
    """
    facts = CLASS_FACTS.get(data_class)
    if facts is None:
        return classify(Descriptor(column, identifies_a_person=True,
                                   category=data_class.lower()))
    return classify(Descriptor(column, **facts))


# --- the enumeration of decided elevations ---------------------------------


class Route(Enum):
    """How a field reaches a rung above the one its class implies.

    `SENSITIVITY.md` provides exactly these. Each reaches exactly one rung, and
    `reconcile()` refuses an entry that claims otherwise — an `L5` rule cannot
    justify an `L4`, and the clause cannot justify `L5`, which no purpose
    unlocks and no signature widens.
    """

    L5_KEY_MATERIAL = "L5 rule 1: key material and authentication secrets"
    L5_ENFORCEMENT_CONTENT = "L5 rule 2: the content of an external restriction"
    L5_REVEALS_A_REFUSAL = "L5 rule 3: rendering it would reveal a refusal"
    CLAUSE = "step 3's general clause, per Protected status"
    COMPOSITION = ("composition is max: the column can hold anything, so it "
                   "inherits the max of what it can hold (SENSITIVITY.md, "
                   "'Composition is max, everywhere')")


REACHES: Dict[Route, Rung] = {
    Route.L5_KEY_MATERIAL: Rung.L5,
    Route.L5_ENFORCEMENT_CONTENT: Rung.L5,
    Route.L5_REVEALS_A_REFUSAL: Rung.L5,
    Route.CLAUSE: Rung.L4,
    Route.COMPOSITION: Rung.L4,
}


@dataclass(frozen=True)
class Elevation:
    """One decided case. Not a mapping — a rung, a rule, and where it is said."""

    rung: Rung
    route: Route
    recorded: str


_REFUSAL = (
    "migrations/001_lanes.sql, classification seed: \"a disposition is where a "
    "refusal lives, and rendering it re-creates the signal §7's "
    "indistinguishability guarantee suppresses\"; SENSITIVITY.md L5 rule 3"
)
_DECLINED = (
    "migrations/001_lanes.sql, classification seed: \"every column of "
    "`declination` is L5 for the same reason, including its timestamps: when "
    "someone declined is nearly as disclosing as that they did\"; "
    "SENSITIVITY.md L5 rule 3"
)

_SESSION = (
    "decided 2026-07-31 by the maintainer, recorded in the seed comment beside the three columns and in §18 item 18's G-B: a jsonb column holds whatever a session declared, and the rung follows the max of what it can hold — the same rule the seed already applies to lane_entry.payload. The class stays PII_MINOR: the rung moved; the class did not (Protected status)"
)

#: Every column whose seeded rung is above what its class derives, with the rule
#: that permits it. Checked **both ways**: an entry with no elevated row behind
#: it is a finding, so this list cannot outlive the seed it explains.
ELEVATIONS: Dict[Tuple[str, str], Elevation] = {
    ("consent_chain", "disposition"):
        Elevation(Rung.L5, Route.L5_REVEALS_A_REFUSAL, _REFUSAL),
    ("declination", "declination_id"):
        Elevation(Rung.L5, Route.L5_REVEALS_A_REFUSAL, _DECLINED),
    ("declination", "lane_id"):
        Elevation(Rung.L5, Route.L5_REVEALS_A_REFUSAL, _DECLINED),
    ("declination", "subject_matter"):
        Elevation(Rung.L5, Route.L5_REVEALS_A_REFUSAL, _DECLINED),
    ("declination", "created_at"):
        Elevation(Rung.L5, Route.L5_REVEALS_A_REFUSAL, _DECLINED),
    ("declination", "valid_at"):
        Elevation(Rung.L5, Route.L5_REVEALS_A_REFUSAL, _DECLINED),
    ("declination", "invalid_at"):
        Elevation(Rung.L5, Route.L5_REVEALS_A_REFUSAL, _DECLINED),
    ("reconciled_session", "declared"):
        Elevation(Rung.L4, Route.COMPOSITION, _SESSION),
    ("reconciled_session", "observed"):
        Elevation(Rung.L4, Route.COMPOSITION, _SESSION),
    ("reconciled_session", "diff"):
        Elevation(Rung.L4, Route.COMPOSITION, _SESSION),
}


# --- what the reconciliation says about one field --------------------------


class Agreement(Enum):
    AGREES = "agrees"              # the seeded rung is what the procedure derives
    ELEVATED = "elevated"          # above it, by a decided rule, recorded
    UNDECIDED = "undecided"        # differs upward with no rule, or the class is
                                   # outside the decided vocabulary — not a pass
    DISAGREES = "disagrees"        # any other difference; a finding
    UNCLASSIFIED = "unclassified"  # declared and not seeded
    STALE = "stale"                # seeded and not declared


@dataclass(frozen=True)
class Judgement:
    """One field, and the three answers about it."""

    table: str
    column: str
    data_class: str
    seeded: Optional[str]      # the rung in the registry
    derived: Optional[str]     # the rung records/classify.py returns
    documented: Optional[str]  # the rung SENSITIVITY.md's class table gives
    agreement: Agreement
    note: str = ""

    @property
    def field(self) -> str:
        return f"{self.table}.{self.column}"


class Verdict(Enum):
    CLEAN = "clean"
    UNDECIDED = "undecided"  # nothing contradicts and something is unresolved
    FINDINGS = "findings"
    VACUOUS = "vacuous"      # nothing was read — not a pass (rule 13)


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


@dataclass(frozen=True)
class Reconciliation:
    verdict: Verdict
    findings: Tuple[Finding, ...]
    judgements: Tuple[Judgement, ...]

    def of(self, state: Agreement) -> Tuple[Judgement, ...]:
        return tuple(j for j in self.judgements if j.agreement is state)

    @property
    def agreed(self) -> int:
        return len(self.of(Agreement.AGREES)) + len(self.of(Agreement.ELEVATED))

    @property
    def ok(self) -> bool:
        return self.verdict is Verdict.CLEAN


# --- the three legs --------------------------------------------------------


def bridge(documented: Dict[str, str]) -> List[Finding]:
    """classify.py against SENSITIVITY.md's table, class by class.

    The leg that stops `CLASS_FACTS` becoming a third copy. It also catches the
    document moving under the code: a table row edited from `L3` to `L2` fails
    here rather than silently re-classifying thirty-five columns.
    """
    out: List[Finding] = []
    if not documented:
        return [Finding("vocabulary",
                        "no class-to-L table parsed out of docs/SENSITIVITY.md; "
                        "nothing was compared")]
    if set(documented) != set(CLASS_FACTS):
        only_doc = sorted(set(documented) - set(CLASS_FACTS))
        only_code = sorted(set(CLASS_FACTS) - set(documented))
        out.append(Finding(
            "vocabulary",
            f"the class vocabulary differs — only in SENSITIVITY.md: "
            f"{only_doc or 'none'}; only in tools/registry.py: "
            f"{only_code or 'none'}"))
    for data_class in sorted(set(documented) & set(CLASS_FACTS)):
        got = derive(_PROBE, data_class)
        if got.rung is None or str(got.rung) != documented[data_class]:
            out.append(Finding(
                "bridge",
                f"{data_class}: SENSITIVITY.md says {documented[data_class]} and "
                f"records/classify.py derives {got.rung} from the same facts "
                f"({got.reason})"))
    return out


def _judge(table: str, column: str, data_class: str, seeded: str,
           documented: Dict[str, str]) -> Judgement:
    got = derive(column, data_class)
    doc = documented.get(data_class)

    if got.decision is Decision.UNDECIDED or got.rung is None:
        return Judgement(
            table, column, data_class, seeded, None, doc, Agreement.UNDECIDED,
            f"records/classify.py cannot classify a field of class "
            f"{data_class!r}: {got.reason}")

    derived = str(got.rung)
    if seeded == derived:
        return Judgement(table, column, data_class, seeded, derived, doc,
                         Agreement.AGREES, got.via)

    try:
        seeded_rung = Rung[seeded]
    except KeyError:  # pragma: no cover — the regex admits L1..L5 only
        return Judgement(table, column, data_class, seeded, derived, doc,
                         Agreement.DISAGREES, f"{seeded!r} is not a rung")

    if not outranks(seeded_rung, got.rung):
        return Judgement(
            table, column, data_class, seeded, derived, doc, Agreement.DISAGREES,
            f"the registry serves this at {seeded} and the procedure derives "
            f"{derived}; a rung below what the class derives is the direction a "
            f"mistake discloses in, and no rule in SENSITIVITY.md lowers one")

    decided = ELEVATIONS.get((table, column))
    if decided is None:
        return Judgement(
            table, column, data_class, seeded, derived, doc, Agreement.UNDECIDED,
            f"the registry serves this at {seeded} and the procedure derives "
            f"{derived}. An elevation is permitted by step 3's clause (to L4) or "
            f"step 4's rules (to L5), both human-evaluated — and nothing records "
            f"which applies here")
    if str(decided.rung) != seeded:
        return Judgement(
            table, column, data_class, seeded, derived, doc, Agreement.DISAGREES,
            f"the recorded elevation says {decided.rung} and the registry says "
            f"{seeded}")
    if REACHES[decided.route] is not decided.rung:
        return Judgement(
            table, column, data_class, seeded, derived, doc, Agreement.DISAGREES,
            f"{decided.route.value} reaches {REACHES[decided.route]}, not "
            f"{decided.rung}")
    return Judgement(table, column, data_class, seeded, derived, doc,
                     Agreement.ELEVATED, f"{decided.route.value} — {decided.recorded}")


def reconcile(sql: str, doc: str) -> Reconciliation:
    """The registry, the procedure and the document, held against each other."""
    seed = classified(sql)
    declared = declared_columns(sql)
    documented = documented_rungs(doc)

    if not seed or not declared or not documented:
        why = []
        if not declared:
            why.append("no CREATE TABLE parsed out of the migration")
        if not seed:
            why.append("no classification seed parsed out of the migration")
        if not documented:
            why.append("no class-to-L table parsed out of SENSITIVITY.md")
        return Reconciliation(Verdict.VACUOUS,
                              (Finding("unreadable", "; ".join(why)),), ())

    findings: List[Finding] = list(bridge(documented))
    judgements: List[Judgement] = []

    for table, column in declared:
        row = seed.get((table, column))
        if row is None:
            judgements.append(Judgement(
                table, column, "", None, None, None, Agreement.UNCLASSIFIED,
                "declared by the DDL and absent from the classification seed; "
                "SENSITIVITY.md: an unclassified field is a build failure, not "
                "a default"))
            continue
        judgements.append(_judge(table, column, row[0], row[1], documented))

    for (table, column), (data_class, rung) in sorted(seed.items()):
        if (table, column) not in set(declared):
            judgements.append(Judgement(
                table, column, data_class, rung, None,
                documented.get(data_class), Agreement.STALE,
                "classified and not declared; the registry is describing a "
                "schema that has moved"))

    for state in (Agreement.DISAGREES, Agreement.UNCLASSIFIED, Agreement.STALE):
        for j in judgements:
            if j.agreement is state:
                findings.append(Finding(state.value, f"{j.field} — {j.note}"))

    # The other direction, so the enumeration cannot outlive the seed it
    # explains. Scoped to tables this SQL declares: an entry for a table that
    # is not in the file being read says nothing about that file, and firing on
    # it would make every reconciliation of a partial schema report seven
    # elevations it was never shown.
    seen = {(j.table, j.column) for j in judgements
            if j.agreement is Agreement.ELEVATED}
    present = set(tables(sql))
    for key in sorted(set(ELEVATIONS) - seen):
        if key[0] in present:
            findings.append(Finding(
                "stale elevation",
                f"{key[0]}.{key[1]} is recorded as an elevation and the registry "
                f"does not elevate it; a reason for a decision nobody made"))

    undecided = [j for j in judgements if j.agreement is Agreement.UNDECIDED]
    if findings:
        verdict = Verdict.FINDINGS
    elif undecided:
        verdict = Verdict.UNDECIDED
    else:
        verdict = Verdict.CLEAN
    return Reconciliation(verdict, tuple(findings), tuple(judgements))


def check(schema: Optional[Path] = None, doc: Optional[Path] = None) -> Reconciliation:
    """Read both sources and reconcile. A source that is not there is vacuous.

    **`schema` may be a directory**, and with none given it is
    `migrations/`: a seed row landing in a later migration is still a seed row,
    and a reconciliation that stopped at 001 would report agreement about a
    registry it had not read. A single file is still honoured, which is what the
    decoy fixtures need.
    """
    doc = SENSITIVITY if doc is None else doc
    if not doc.is_file():
        return Reconciliation(
            Verdict.VACUOUS, (Finding("unreadable", f"missing: {doc}"),), ())
    where = MIGRATIONS if schema is None else Path(schema)
    if where.is_dir():
        sql = schema_text(where)
        if not sql.strip():
            return Reconciliation(
                Verdict.VACUOUS,
                (Finding("unreadable", f"no migrations under {where}"),), ())
    elif where.is_file():
        sql = where.read_text(encoding="utf-8")
    else:
        return Reconciliation(
            Verdict.VACUOUS, (Finding("unreadable", f"missing: {where}"),), ())
    return reconcile(sql, doc.read_text(encoding="utf-8"))


def main(argv: List[str]) -> int:
    r = check()
    for j in r.judgements:
        if j.agreement is not Agreement.AGREES:
            print(f"  {j.agreement.value:<13} {j.field:<38} "
                  f"registry={j.seeded} derived={j.derived} doc={j.documented}")
            print(f"                {j.note[:150]}")
    counts = {s.value: len(r.of(s)) for s in Agreement}
    print(f"\n  {r.verdict.value}: {len(r.judgements)} field(s) — "
          + ", ".join(f"{v} {k}" for k, v in counts.items() if v))
    for f in r.findings:
        print(f"  finding  {f}")
    return 1 if r.findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
