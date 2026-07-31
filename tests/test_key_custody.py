"""Refusal 2, as a scan: no key material in this tree, in any spelling.

*"Never commit the trust root. `mcp_apps/`, `_net_leases/`, and any grant
material stay out of the tree and off any remote."* S-3 is the commit where that
stops being about somebody else's directories: `records/atrest.py` mints keys,
`tests/cluster.py` mints them per test database, and the obvious convenience —
a fixture holding one key so the store tests do not have to make one — would put
a working decryption key in git history forever.

**A key that opens a sealed payload is the payload.** Rotating it does not help:
the tree is the history, the old commits keep the old key, and every sealed
payload ever written under it stays open to anyone with a clone. That is worse
than a committed password, which at least stops working when it is changed.

So this scans for the two spellings that matter and fails on either:

* **A Fernet key** — 32 random bytes as urlsafe-base64, so 43 characters from
  the alphabet followed by `=`. This is what `Fernet.generate_key()` returns and
  what a `MasterKey` or `LaneKey` carries.
* **A Fernet token** — the sealed payload itself, which begins `gAAAAA` and runs
  to at least 100 characters. A committed ciphertext is not as bad as a
  committed key, and it is still a student's record in the repository.

**The scan is over the whole tree, not just `tests/fixtures/`.** A fixture is
where somebody would put one deliberately; a debug print committed by accident,
a doctest, a pasted traceback, or a `docs/` example is where it would actually
end up. Scanning the narrow place would be the check that passes because it was
pointed somewhere clean.

**Every match must be shown to be a match**, so this file's own decoys are
run through the same patterns and must be caught: a scan whose regex silently
stopped matching would go green over a tree full of keys, which is scout-13's
row B one subject over.

Stdlib only. Runs under pytest or directly:

    python3 tests/test_key_custody.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: A Fernet key: 32 bytes, urlsafe-base64, padded. Anchored on both sides so a
#: longer base64 blob (a rendered image, a signature) does not read as one.
FERNET_KEY = re.compile(r"(?<![A-Za-z0-9_=-])[A-Za-z0-9_-]{43}=(?![A-Za-z0-9_=-])")

#: A Fernet token: version byte 0x80 plus a timestamp whose high bytes are zero
#: encodes as `gAAAAA`. Length is the floor from 1 + 8 + 16 + 16 + 32 bytes.
FERNET_TOKEN = re.compile(r"gAAAAA[A-Za-z0-9_-]{94,}")

#: Directories that are not the tree: git's own object store holds compressed
#: blobs that occasionally match by chance, and a virtualenv is not this
#: repository's contents.
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}

#: Anything that is not text is not something a person put a key into by
#: accident, and reading a large binary as utf-8 is a slow way to find nothing.
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".woff",
                 ".woff2", ".zip", ".gz", ".pyc"}

#: This file. It contains the decoys the scan is checked against, which are
#: **not** real key material — they are strings shaped like it — and excluding
#: the file by name rather than the strings by pattern is the honest way round:
#: an exclusion that matched by shape would exclude a real key with the same
#: shape anywhere.
SELF = Path(__file__).resolve()


def _files():
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.resolve() == SELF:
            continue
        if set(p.relative_to(ROOT).parts) & SKIP_DIRS:
            continue
        if p.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield p


def _scan(pattern):
    found = []
    for p in _files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                found.append(f"{p.relative_to(ROOT)}:{i}")
    return found


def test_no_key_material_anywhere_in_the_tree():
    """Refusal 2. The whole tree, not a directory somebody remembered."""
    found = _scan(FERNET_KEY)
    assert not found, (
        "key material in the tree: " + "; ".join(found[:5]) + ". A key that "
        "opens a sealed payload is the payload, and git history keeps it after "
        "any rotation (refusal 2)")


def test_no_sealed_payload_is_committed_either():
    """A student's record as ciphertext is still a student's record."""
    found = _scan(FERNET_TOKEN)
    assert not found, (
        "sealed payloads in the tree: " + "; ".join(found[:5]))


def test_the_fixtures_directory_in_particular_is_clean():
    """Named separately because it is where a key would be put *on purpose* —
    the convenient fixture that saves the store tests from minting one. The
    scan above already covers it; this is the row a reviewer looks for."""
    fixtures = ROOT / "tests" / "fixtures"
    assert fixtures.is_dir(), "tests/fixtures/ does not exist; this scan is vacuous"
    offenders = []
    for p in sorted(fixtures.rglob("*")):
        if not p.is_file() or p.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if FERNET_KEY.search(text) or FERNET_TOKEN.search(text):
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, f"key material under tests/fixtures/: {offenders}"


def test_the_scan_is_not_vacuous():
    """It read files, and enough of them to mean something."""
    n = sum(1 for _ in _files())
    assert n > 50, f"the key scan read {n} file(s); that is not this tree"


# --- the patterns, shown to fire (rule 19) ---------------------------------
#
# These are the decoys. Neither opens anything: the "key" is 44 characters of
# the right alphabet and was never generated, and the "token" is the prefix
# followed by padding. They exist so that a regex which stopped matching goes
# red here instead of going green over a tree full of real ones.

DECOY_KEY = "a" * 43 + "="
DECOY_TOKEN = "gAAAAA" + "B" * 100


def test_the_key_pattern_catches_a_real_shape():
    assert FERNET_KEY.search(DECOY_KEY)
    assert FERNET_KEY.search(f'MASTER = "{DECOY_KEY}"')
    # And does not fire on ordinary base64-ish text of the wrong length.
    assert not FERNET_KEY.search("a" * 42 + "=")
    assert not FERNET_KEY.search("a" * 44 + "=")


def test_the_token_pattern_catches_a_real_shape():
    assert FERNET_TOKEN.search(DECOY_TOKEN)
    assert not FERNET_TOKEN.search("gAAAAA" + "B" * 10)
    assert not FERNET_TOKEN.search("gAAAA" + "B" * 200)


def test_a_generated_key_would_be_caught():
    """The strongest form: mint one, and require the pattern to find it.

    Held in a local and never returned, printed or written — the scan asserts
    on a boolean, not on the material, so a failing run does not put the key in
    a CI log.
    """
    try:
        from cryptography.fernet import Fernet
    except Exception:  # noqa: BLE001 — pragma: no cover
        raise AssertionError(
            "the sealing primitive is not usable, so this tripwire cannot be "
            "shown to fire. That is UNKNOWN, not a pass (rule 13)")
    assert FERNET_KEY.fullmatch(Fernet.generate_key().decode())
    token = Fernet(Fernet.generate_key()).encrypt(b"x" * 64).decode()
    assert FERNET_TOKEN.search(token), "a real token does not match the pattern"


if __name__ == "__main__":
    tests = sorted((n, f) for n, f in globals().items()
                   if n.startswith("test_") and callable(f))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    print(f"\ntest_key_custody: {len(tests) - failures}/{len(tests)} passed")
    raise SystemExit(1 if failures else 0)
