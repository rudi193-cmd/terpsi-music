#!/usr/bin/env bash
# Point this clone's git at the tracked hooks. Idempotent; run it once per
# clone. Until it is run, .githooks/pre-commit is a ledger, not a gate — which
# is why tests/test_trust_root_hook.py runs the hook directly rather than
# trusting that it was installed.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
git -C "$root" config core.hooksPath .githooks
chmod +x "$root/.githooks/pre-commit"
echo "core.hooksPath -> .githooks; the trust-root gate (refusal 2) is live in this clone."
