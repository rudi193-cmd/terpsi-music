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
