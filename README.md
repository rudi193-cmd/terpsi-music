# terpsi-music

Music workspace for the Terpsi project. Fleet-wired as a **core** Willow project via **willow-mcp** (not willow-2.0).

Local fleet overlay (`.mcp.json`, `.willow/`, `.cursor/`) is gitignored — materialized by:

```bash
WILLOW_HOME=~/github/.willow willow-mcp project sync terpsi-music
```
