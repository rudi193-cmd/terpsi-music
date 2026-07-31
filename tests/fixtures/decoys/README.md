# Decoys

**These files are never imported and never run.** They exist so
`tools/sockets.py` can be pointed at code that genuinely opens sockets and shown
to complain — rule 19, and the reason this checker is worth having before there
is a manifest to check against.

They deliberately reproduce the failure §4.3 documents at source in
`safe-app-willow-grove`: an all-interface listener in an app whose manifest says
it has none, and a UDP probe to `8.8.8.8:80` opened for local-IP discovery
outside the component the declaration was scoped to.

`.py` extensions are kept so `ast.parse` sees real Python. `tests/test_sockets.py`
asserts they are parsed and not imported — a checker that imported these to
inspect them would open the sockets it was written to detect.

## What each one is for

| decoy | checker | the hole it proves is closed |
|---|---|---|
| `all_interfaces.py` | `tools/sockets.py` | `bind(("0.0.0.0", …))` and `HTTPServer(("", …))` — the second is all-interfaces spelled as a blank |
| `loopback_only.py` | `tools/sockets.py` | a bind a manifest can honestly declare; the control case |
| `outbound_probe.py` | `tools/sockets.py` | the `8.8.8.8:80` local-IP probe, outside the component the declaration was scoped to |
| `unresolved_bind.py` | `tools/sockets.py` | `bind((HOST, PORT))` from the environment — unresolvable is not a pass |
| `egress_dynamic.py` | `tools/purity.py` | `__import__("socket")` and `importlib.import_module` — invisible to the import graph |
| `egress_subprocess.py` | `tools/purity.py` | `subprocess.run(["curl", …])` — a network call with no network import |
| `egress_nested/leaky.py` | `tools/purity.py` | a subpackage; the old scan globbed `*.py`, not `**/*.py` |
| `writes_files.py` | `tools/purity.py` | every write shape: `open(…, "w")`, `write_text`, `makedirs`, `remove`, `rmtree` |
| `writes_unknown_mode.py` | `tools/purity.py` | `open(path, MODE)` — a non-literal mode counts as a write |
| `reads_only.py` | `tools/purity.py` | a read is not a write; a check that cries wolf gets switched off |
| `clean.py`, `egress_in_prose.py`, `writes_in_prose.py` | both | **decoys against the wrong implementation** — each names the forbidden thing in prose, so a grep-based checker fails them and an AST-based one does not |

Three of the four checkers these serve were shipped broken and passing. The
decoys found all three in one run.
