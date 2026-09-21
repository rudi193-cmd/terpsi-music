"""The declaration, reconciled against the tree, in this repository's own CI.

§18 item 4's closing note makes two things obligations of the first surfaces
commit. This file is the second: *"rule 12's socket-reconciliation test lands in
the same commit as the manifest, in this repository's own CI rather than the
store's."* The reason it is here rather than upstream is measured, not
preferred — `safe-app-store/tools/catalog_lint.py:71-73` errors on a missing
manifest **only when the catalog entry carries a local `path`**, and the
enforcing ACL lives in a different repository again, so an external-repo app
falls between the declaration surface and the enforcement surface. That is a
middle which exists and cannot fire for a whole class of entries.

**What this reconciles, and each half has a way to be wrong.**

* **Listeners.** Delegated whole to `tools/sockets.py`, which existed before this
  manifest so the manifest could not be born wrong. No second implementation:
  one AST scanner, called from here.
* **Surfaces, both directions.** Every directory under `surfaces/` is declared,
  and every declared surface has a directory. A fifth door added without a line
  in the manifest fails the build, and a door removed while its declaration
  stays fails it too — a stale declaration reads as a real one.
* **Permissions, by allowlist.** An unrecognised permission is a finding rather
  than a shrug, which is the only failure direction that survives someone
  adding one. Cloud-shaped permissions are named separately because refusal 1
  is about them by name.
* **Coverage.** The scanned set is derived from the tree, so a new top-level
  package is scanned the moment it exists. Two paths are excused, each with its
  reason recorded below and asserted in `tests/test_manifest.py` — an exclusion
  nobody can enumerate is how a lint comes to skip by construction.

**The vacuous case is not a pass.** No manifest, or a manifest that cannot be
read, or a scan that covered no files, reports `UNKNOWN` (`tools/conform.py`'s
convention, and `sockets.py`'s). A check with nothing to check has not checked
anything, and the moment a listener appears anywhere in the scanned tree the
result is `FAIL` — nobody has to remember to switch anything on.

    python3 tools/manifest.py

Stdlib only. No network.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sockets import Finding, check as socket_check  # noqa: E402

MANIFEST = ROOT / "manifest.json"
SURFACES = ROOT / "surfaces"

#: Exactly the keys, and nothing else. A typo'd key is worse than a missing one:
#: `"listners": [...]` declares nothing, and `sockets.declared_from` would read
#: the manifest as *declares no listeners* — a claim that happens to be true
#: today and would be silently false the moment a surface listens.
REQUIRED_KEYS: Tuple[str, ...] = (
    "app", "manifest_version", "surfaces", "listeners", "outbound",
    "permissions", "inference", "write_paths",
)

#: Permissions this application may ask for. An allowlist, because the failure
#: direction of a denylist is that anything nobody thought of is permitted.
ALLOWED_PERMISSIONS = frozenset({
    "local_storage",   # the hub's own disk
    "lan_listen",      # a listener on the local segment — none declared today
    "lan_send",        # a send on the local segment — none declared today
    "local_inference", # a model on program hardware (refusal 1)
})

#: Named separately so the message can name the refusal rather than say
#: "unrecognised". Substring match: `cloud_fallback_inference` is caught.
CLOUD_SHAPED = ("cloud", "remote", "internet", "external", "hosted", "api_key")

#: Python that is deliberately outside the socket scan, and why. Each entry is
#: asserted in `tests/test_manifest.py`, so the list cannot grow quietly.
EXCUSED: Dict[str, str] = {
    "tests/fixtures/decoys": (
        "source written to open sockets, so the checker can be shown to catch "
        "one; scanning it would make every run report the decoys"
    ),
    "docs": (
        "documents, not the application. docs/survey/trigger_mutation_demo.py "
        "calls sqlite3.connect(), which tools/sockets.py reads as an outbound "
        "network connection — a false positive pinned by a test rather than "
        "hidden by this exclusion"
    ),
}


@dataclass(frozen=True)
class Reconciliation:
    """What the manifest claims, against what the tree does."""

    present: bool
    scanned: int
    findings: Tuple[Finding, ...]
    surfaces_declared: Tuple[str, ...] = ()
    surfaces_present: Tuple[str, ...] = ()

    @property
    def vacuous(self) -> bool:
        """Nothing was checked. Not a pass — `conform.py` renders it UNKNOWN."""
        return not self.present or self.scanned == 0

    @property
    def ok(self) -> bool:
        return not self.vacuous and not self.findings


def _excused(rel: Path) -> Optional[str]:
    text = rel.as_posix()
    for prefix, why in EXCUSED.items():
        if text == prefix or text.startswith(prefix + "/"):
            return why
    return None


def _all_python(root: Optional[Path] = None) -> Tuple[Path, ...]:
    base = ROOT if root is None else root
    return tuple(p for p in sorted(base.rglob("*.py"))
                 if not any(part.startswith(".") for part in p.relative_to(base).parts))


def sources(root: Optional[Path] = None) -> Tuple[Path, ...]:
    """Every Python file the scan covers. **Derived from the tree**, so a new
    package is covered the moment it lands rather than when somebody remembers
    to add it to a list. `root` exists so a caller judging a *different* tree
    (`conform.py`'s unreachable-tree sweep) scans that tree and not this one —
    a scan that quietly fell back to the installed copy would report health
    out of a source that is not there (rule 13)."""
    base = ROOT if root is None else root
    return tuple(p for p in _all_python(base) if _excused(p.relative_to(base)) is None)


def excused(root: Optional[Path] = None) -> Tuple[Path, ...]:
    """The complement of `sources()` — enumerable, so it can be reviewed."""
    base = ROOT if root is None else root
    return tuple(p for p in _all_python(base) if _excused(p.relative_to(base)) is not None)


def surface_dirs(where: Optional[Path] = None) -> Tuple[str, ...]:
    """The doors that exist on disk. `ls surfaces/`, in one function."""
    base = SURFACES if where is None else where
    if not base.exists():
        return ()
    return tuple(sorted(p.name for p in base.iterdir()
                        if p.is_dir() and not p.name.startswith((".", "_"))))


def read(path: Optional[Path] = None) -> Tuple[Optional[dict], Tuple[Finding, ...]]:
    p = MANIFEST if path is None else Path(path)
    if not p.exists():
        return None, (Finding("MANIFEST_ABSENT",
                              f"{p.name} does not exist; nothing declares what this "
                              "application opens or shows"),)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        return None, (Finding("MANIFEST_UNREADABLE",
                              f"{p.name} is not JSON ({exc}); a manifest that cannot "
                              "be read declares nothing, and declaring nothing is "
                              "not the same as declaring none"),)
    if not isinstance(data, dict):
        return None, (Finding("MANIFEST_UNREADABLE", f"{p.name} is not an object"),)
    return data, ()


def _check_keys(data: dict) -> List[Finding]:
    out = []
    for key in REQUIRED_KEYS:
        if key not in data:
            out.append(Finding("MISSING_KEY",
                               f"the manifest declares no {key!r}; an absent "
                               "declaration is unknown, never empty"))
    for key in data:
        if key not in REQUIRED_KEYS:
            out.append(Finding("UNKNOWN_KEY",
                               f"{key!r} is not a manifest field. A typo'd key "
                               "declares nothing and reads like a declaration"))
    return out


def _check_surfaces(data: dict, where: Optional[Path] = None) -> List[Finding]:
    out = []
    declared = tuple(sorted(str(s) for s in data.get("surfaces", [])))
    present = surface_dirs(where)
    for name in present:
        if name not in declared:
            out.append(Finding(
                "SURFACE_UNDECLARED",
                f"surfaces/{name}/ exists and the manifest does not declare it"))
    for name in declared:
        if name not in present:
            out.append(Finding(
                "SURFACE_ABSENT",
                f"the manifest declares the {name!r} surface and there is no "
                f"surfaces/{name}/ — a stale declaration reads as a real one"))
    return out


def _base_of(files: Sequence[Path]) -> Path:
    """The root the scanned files are relative to.

    `reconcile()` is called on other trees than this one — `conform.py`'s
    unreachable-tree sweep, and every test that points it at a temporary
    directory. Reporting a module path relative to `ROOT` for a file that is not
    under `ROOT` raises, and a checker that raises where it should report is a
    checker with a gap in exactly the case `tests/test_rule13_acceptance.py`
    exists to cover.
    """
    for f in files:
        try:
            f.relative_to(ROOT)
        except ValueError:
            # Not under this tree. Walk up to the common ancestor of the batch.
            base = f.parent
            while not all(str(o).startswith(str(base)) for o in files):
                base = base.parent
            return base
    return ROOT


def _covers(declared: str, module: str) -> bool:
    here = str(module).replace("\\", "/")
    there = str(declared).replace("\\", "/").rstrip("/")
    return here == there or here.startswith(there + "/")


def _check_write_paths(data: dict, files: Sequence[Path],
                       base: Optional[Path] = None) -> List[Finding]:
    """Gate G-C: **every write path is declared, and every declaration writes.**

    `docs/PLAN-STORE.md` decision 7 makes this an obligation of the same commit
    as the store — *"the manifest gains a write-paths declaration and the
    reconciliation lands in the same commit (rule 12; the
    declaration-without-enforcement pair is the one §16 is written about)"* —
    and the last acceptance item is explicit about the failure direction:
    *"a write path appears that the manifest does not declare — the build fails
    without anyone remembering to check."*

    **The detection is `tools/purity.py`'s and is not re-implemented here.** That
    module owns the question *where does this write*, and it now answers it for a
    database as well as for a disk, because a write is a write whether the bytes
    land on a local file or in a cluster. This function does the reconciling and
    none of the finding.

    **Both directions, for `_check_surfaces`'s reason.** An undeclared write
    fails; so does a declared path that writes nothing, because a stale
    declaration reads as a real one and the next module added under it inherits
    a permission nobody re-examined.
    """
    from purity import scan_source  # noqa: E402 — the tool that owns writes

    declared = data.get("write_paths", [])
    if not isinstance(declared, list):
        return [Finding("WRITE_PATHS_SHAPE", "write_paths is not a list")]

    paths, out = [], []
    for entry in declared:
        if not isinstance(entry, dict) or not str(entry.get("path", "")).strip():
            out.append(Finding(
                "WRITE_PATH_SHAPE",
                f"{entry!r} is not a write-path declaration; each names a path, a "
                "kind and a why. A declaration with no reason is one nobody can "
                "review, and it is the kind that outlives its reason"))
            continue
        if not str(entry.get("why", "")).strip():
            out.append(Finding(
                "WRITE_PATH_UNEXPLAINED",
                f"{entry['path']!r} is declared as a write path with no reason"))
        paths.append(str(entry["path"]))

    root = ROOT if base is None else base
    writing: Dict[str, List[str]] = {}
    for p in files:
        rel = str(p.relative_to(root)).replace("\\", "/")
        for t in scan_source(p.read_text(encoding="utf-8"), rel):
            if t.is_write:
                writing.setdefault(rel, []).append(t.detail)

    for module, why in sorted(writing.items()):
        if not any(_covers(d, module) for d in paths):
            out.append(Finding(
                "WRITE_UNDECLARED",
                f"{module} writes and the manifest does not declare it: {why[0]}"))

    for d in paths:
        if not any(_covers(d, module) for module in writing):
            out.append(Finding(
                "WRITE_PATH_ABSENT",
                f"the manifest declares {d!r} as a write path and nothing under it "
                "writes — a stale declaration reads as a real one"))
    return out


def _check_permissions(data: dict) -> List[Finding]:
    out = []
    perms = data.get("permissions", [])
    if not isinstance(perms, list):
        return [Finding("PERMISSIONS_SHAPE", "permissions is not a list")]
    for perm in perms:
        name = str(perm)
        if any(shape in name.lower() for shape in CLOUD_SHAPED):
            out.append(Finding(
                "CLOUD_PERMISSION",
                f"{name!r} reaches a third party. Refusal 1: anything touching a "
                "student's record is served locally, and a stopped local model "
                "fails loudly rather than degrading to somebody else's"))
        elif name not in ALLOWED_PERMISSIONS:
            out.append(Finding(
                "UNKNOWN_PERMISSION",
                f"{name!r} is not in this application's permission vocabulary "
                f"({', '.join(sorted(ALLOWED_PERMISSIONS))})"))

    inference = data.get("inference")
    if not isinstance(inference, dict):
        out.append(Finding("INFERENCE_SHAPE",
                           "inference is not declared as an object"))
        return out
    provider = str(inference.get("provider", "")).lower()
    if provider != "local":
        out.append(Finding(
            "NON_LOCAL_INFERENCE",
            f"inference provider is {provider!r}; refusal 1 admits one value, and "
            "'auto' is the spelling that produced the fallback chain it forbids"))
    if inference.get("cloud_fallback") is not False:
        out.append(Finding(
            "CLOUD_FALLBACK",
            "cloud_fallback is not declared false. This is the declaration half "
            "only — asserting the provider actually used at run time is a "
            "separate gate and is not built yet"))
    return out


def reconcile(manifest: Optional[Path] = None,
              paths: Optional[Sequence[Path]] = None,
              surfaces_at: Optional[Path] = None) -> Reconciliation:
    """The whole check. `()` findings and a nonzero scan is the only pass."""
    data, problems = read(manifest)
    if data is None:
        return Reconciliation(False, 0, problems)

    findings: List[Finding] = []
    findings += _check_keys(data)
    findings += _check_surfaces(data, surfaces_at)
    findings += _check_permissions(data)

    files = tuple(paths) if paths is not None else sources()
    if not files:
        return Reconciliation(True, 0, tuple(findings) + (Finding(
            "NOTHING_SCANNED",
            "no Python was scanned, so no listener could have been found. A scan "
            "of nothing is not a scan that passed"),))

    # One AST scanner, called — never a second implementation of it here.
    socket_side = socket_check(list(files), MANIFEST if manifest is None else manifest)
    findings += list(socket_side.findings)
    findings += _check_write_paths(data, files, base=_base_of(files))

    return Reconciliation(
        True, len(files), tuple(findings),
        tuple(sorted(str(s) for s in data.get("surfaces", []))),
        surface_dirs(surfaces_at),
    )


def main(argv: Sequence[str]) -> int:
    r = reconcile()
    for f in r.findings:
        print(f"  {f.code:<20} {f.detail}")
    if r.vacuous:
        print("\n  UNKNOWN — nothing was checked. That is not a pass: it is the "
              "state where a listener could exist and nothing would say so.")
        return 2
    if r.findings:
        print(f"\n  FAIL — {len(r.findings)} finding(s) over {r.scanned} source file(s)")
        return 1
    data, _ = read()
    out = len((data or {}).get("outbound", []))
    paths = len((data or {}).get("write_paths", []))
    print(f"  PASS — {r.scanned} source file(s) scanned; "
          f"{len(r.surfaces_declared)} surface(s) declared and present; "
          f"no listener; {out} outbound path(s) and {paths} write path(s) "
          "declared and reconciled; no cloud permission")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
