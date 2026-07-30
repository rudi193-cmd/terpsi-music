# Scout 06 — Sandboxing & Making Egress Inexpressible

Read before searching: `docs/ARCHITECTURE.md` §5.1 (kartikeya, `kart-sandbox.json`, the
`allow_localhost` admission), all of §6 (three rings, the filesystem-shaped blind spot,
`willow-gate`, the residual, enforcement tiers), plus `CLAUDE.md`.

Every project named below was fetched from its actual repository or package page. License,
language, and activity figures are what those pages said at fetch time (2026-07-30). Where a
project is archived, alpha, or has an unmerged feature I depend on, I say so in the row.
Nothing is named that I could not open.

**One-line thesis per gap:**

1. **Gap 1 is two problems, and the smaller one dissolves.** For *transcription* specifically
   there is no reason to have a server at all — `whisper.cpp` is a CLI over local model files,
   so `--unshare-net` costs nothing and the tier problem disappears. For the general
   local-inference case (Ollama), the answer is a **pathname unix socket bind-mounted into a
   `--unshare-net` sandbox with `socat` re-presenting it on the sandbox's private loopback** —
   and there is a working, Apache-2.0, 4.8k-star implementation of exactly that shape to read.
2. **Gap 2 has no Python tool. Anywhere.** Nothing statically checks declared write paths for a
   Python module. What exists instead is (a) kernel enforcement that takes a path list —
   Landlock, unprivileged, 5.13+ — and (b) one tool in another language, Google's Capslock, that
   is the right *shape*: transitive capability classes (FILES / NETWORK / EXEC) with a CI
   baseline file. The transplant is to declare paths once and enforce twice.
3. **Gap 3 is solved and cheap.** `import-linter` is a 20-line config file that replaces the
   aspirational `assert_does_not_import` call §6 corrects itself about, with a real exit code.
   `tach` adds the part §6's seam row actually wants: enforcement of the *surface*, not just the
   direction.

---

## GAP 1 — Network-isolated local inference

The requirement: a task holding `MEDIA_MINOR` audio reaches a local model **and cannot reach
anything else** — not "cannot reach anything else authenticated."

The load-bearing kernel fact that makes this tractable: **pathname `AF_UNIX` sockets are
filesystem objects, not network-namespace objects.** A socket bind-mounted into a sandbox that
has `--unshare-net` still connects to its peer outside. (Abstract sockets — `@name` — *are*
netns-scoped and will not cross; do not use them.) This is why the pattern works and why it
needs no privilege.

| # | Project / mechanism | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **whisper.cpp** (`ggml-org/whisper.cpp`) | Offline C/C++ Whisper. `whisper-cli` over local model files; no server, no client, no socket | MIT | 52.4k ★, 4,838 commits, v1.9.1 | §8.2 commentary transcription; §6 inner ring | **Adopt.** Deletes the gap for the actual workload |
| 2 | **bwrap `--unshare-net` + UDS bind-in + `socat`** | New sandbox tier: full netns isolation, one pathname unix socket bound in, `socat TCP-LISTEN:11434,fork UNIX-CONNECT:/run/model.sock` inside so unmodified HTTP clients work | bwrap: LGPL-family (C, 8.2k ★, 688 commits); socat: GPL | bwrap active | Replaces `allow_localhost` in `kart-sandbox.json` | **Adopt.** The named fix in §5.1, buildable this week |
| 3 | **anthropic-experimental/sandbox-runtime** | Reference implementation of exactly #2: bwrap netns isolation + socat over UDS + host-side proxy as the only reachable peer | Apache-2.0 | 4.8k ★, 647 commits, active | Proof #2 works; read for the socat wiring | **Read, don't vendor.** TypeScript; Kart is not |
| 4 | **systemd `PrivateNetwork=yes` + `JoinsNamespaceOf=`** | Two units share one ad-hoc netns with only `lo`. Ollama and the worker both inside; loopback works, internet does not exist | systemd (LGPL-2.1) | Core systemd | The "loopback-only namespace" option §5.1 names | **Strong second.** Most inheritable. See caveats below |
| 5 | **systemd-socket-proxyd** | Bidirectional proxy for IPv4/IPv6/UNIX stream sockets, socket-activated (`Accept=no`). Documented pattern for reaching a `PrivateNetwork=yes` service | LGPL-2.1 | Core systemd | Host-side half of #2 without shipping socat | **Adopt as the glue.** Already on the box |
| 6 | **Landlock ABI v4 network rules** (`landrun`, `Zouuup/landrun`) | Unprivileged per-process TCP `connect`/`bind` port restriction. `landrun --connect-tcp 11434 -- task` | MIT (Go) | 2.2k ★; needs kernel 6.7+ | A narrowing, not a proof | **Defense in depth only.** Port-based, not address-based — see caveat |
| 7 | **libkrun** (`containers/libkrun`) | Library: run a process in a KVM microVM. With no network interface added it uses "Transparent Socket Impersonation" over virtio-vsock | Apache-2.0 (Rust) | 2.5k ★, 1,461 commits | The vsock option §5.1 names | **Later.** Real, heavier, GPU passthrough is the fight |
| 8 | **Firecracker** | microVM with exactly 5 emulatable devices; omit `virtio-net` entirely, keep `virtio-vsock`. Guest has no IP, no routes, no network stack | Apache-2.0 (Rust) | Very active | Air-gap-grade local inference | **Overkill on one box.** Note as the limit case |
| 9 | **nsjail** (`google/nsjail`) | Namespaces + cgroups + rlimits + seccomp-bpf (Kafel), configured by a **protobuf config file** — same shape as `kart-sandbox.json` | Apache-2.0 (C++) | 4.0k ★, 1,403 commits | Alternative execution layer | **Read the config schema.** Needs root for most features |
| 10 | **Ollama native unix socket** (PR #8072) | `OLLAMA_HOST=unix:///run/ollama.sock` | MIT | **PR still OPEN, last activity Feb 2026** | Would remove socat | **Do not depend on it.** Front Ollama externally instead |
| 11 | **xdg-dbus-proxy** | Flatpak's filtering proxy: bind a socket in, the proxy is the only peer, rules applied at the proxy | LGPL | Mature | Prior art for "the proxy is the only reachable peer" | **Cite as precedent** for the shape §6 already believes in |

### Top find, with transplant and cost

**Delete the problem for transcription first.** `whisper.cpp` (MIT, 52.4k stars, v1.9.1, 4,838
commits) is `whisper-cli audio.wav -m models/ggml-*.bin`. It has no runtime network dependency
of any kind; the only network event in its whole lifecycle is downloading a model file once,
which is an install act, not a task act. §8.2's commentary transcription — the exact workload
§5.1 says "is running one policy tier weaker than §6 claims" — needs neither `allow_localhost`
nor `allow_net` nor a socket. It runs under plain `--unshare-net` with `--ro-bind` on the model
directory and one `--bind` on the sidecar output path. There *is* a `whisper-server` example in
the repo; the recommendation is specifically not to use it. **Cost:** one afternoon, plus model
download and a GPU-backend decision. The saving is that the hardest tier in §5.1 never has to
exist for the highest-sensitivity job in the system.

**Then build the tier properly, for everything else.** Embeddings, the director's assistant, the
Jeles-style verified-corpus front end (§6) — those want a real LLM server, and Ollama does not
speak unix sockets in a released build. The pattern:

```
# host side, outside the sandbox, as a uid the app does not run as
systemd-socket-proxyd --exit-idle-time=... 127.0.0.1:11434      # activated by
                                                                 # ListenStream=/run/terpsi/model.sock
# sandbox side, kart tier `allow_local_model`
bwrap --unshare-all --unshare-net \
      --ro-bind /usr /usr --proc /proc --dev /dev \
      --tmpfs /tmp --tmpfs /dev/shm \
      --ro-bind $STORE $STORE --bind $SIDECAR $SIDECAR \
      --bind /run/terpsi/model.sock /run/model.sock \
      -- /usr/bin/env sh -c 'socat TCP-LISTEN:11434,fork,reuseaddr \
                                   UNIX-CONNECT:/run/model.sock & exec "$@"' -- "$@"
```

The task sees `http://127.0.0.1:11434` and needs no code change. The netns contains exactly one
interface, `lo`, and one reachable peer, reached through a filesystem object. There is no route,
no DNS, no default gateway — **"cannot leave," not "cannot leave authenticated."** Credentials
stay unbound as they already are under `allow_localhost`.

`anthropic-experimental/sandbox-runtime` (Apache-2.0, 4.8k stars, 647 commits) implements this
exact composition — bwrap `--unshare-net`, socat over a bound UDS, host-side proxies as the sole
peer, no root beyond unprivileged user namespaces — which is worth reading precisely because it
proves the composition works in production rather than only in principle. Do not vendor it: it
is TypeScript and Kart is not, and vendoring it would create a §16 pair with no middle.

**Cost of the tier:** a new `kart-sandbox.json` entry, a systemd socket + service unit pair, a
one-line socat wrapper, and — non-negotiable per `CLAUDE.md` rule 19 — a mutation test that runs
`curl https://example.com` inside the tier and asserts it fails, plus one that asserts the model
call succeeds. Call it two days including the acceptance tests. The install-acceptance artifact
is the diff between the school profile and the operator-desk profile, which §5.1 already asks
for.

### The systemd alternative, and why it might win on the "inheritable" axis

`PrivateNetwork=yes` "runs a service in a new network namespace and adds a loopback device to
it, but nothing else"; `JoinsNamespaceOf=` puts a second unit in that same namespace. Two unit
files, zero new software, and a successor reading `/etc/systemd/system/` can see the whole policy
without knowing what bubblewrap is. That is a real advantage for a box that gets inherited.

Two verified caveats: systemd issue **#17485** reports `JoinsNamespaceOf=` silently failing to
join — the joining unit lands in an unrelated fresh namespace — until the units are restarted in
the right order or the box reboots; and **#29429** reports user units cannot join another unit's
network namespace at all, so these must be system units. Both are the kind of failure that reads
as success, which is the worst kind for a guarantee. If you take this route, install acceptance
must *positively* check the two processes share a netns (compare `/proc/<pid>/ns/net`
readlinks) rather than assume the directive took.

### The Landlock caveat, stated plainly because it is easy to get wrong

Landlock ABI v4 (kernel 6.7+) network rules restrict TCP `bind` and `connect` **by port
number, not by address**. `landrun --connect-tcp 11434` does not stop a task connecting to port
11434 on a host in another country, and Landlock has no rules at all for UDP, raw sockets, or
unix sockets. It is a useful extra layer inside a netns-isolated sandbox; it is **not** a
substitute for one, and describing it as one would be exactly the enforcement/ledger conflation
`CLAUDE.md` rule 18 forbids.

---

## GAP 2 — Write-path declaration

The requirement from §6: *"an outward module declares the paths it writes as well as the modules
it imports,"* and anything outside the store root is an egress event. Plus: treat `subprocess`
as an egress channel where the rule currently exists but is unenforced.

| # | Project / mechanism | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Landlock LSM** | Kernel primitive: unprivileged process restricts its own filesystem access to a declared path list. FS from 5.13; TCP ports from 6.7 (ABI v4) | GPL-2.0 (kernel) | In-tree, actively extended | The enforcement half of §6's second rule | **Adopt as the enforcement layer** |
| 2 | **`landrun`** (`Zouuup/landrun`) | Landlock as a CLI: `--ro`, `--rw`, `--rwx`, `--bind-tcp`, `--connect-tcp`, `--best-effort` | MIT (Go) | 2.2k ★; 5.13+ / 6.7+ | Wrap a worker without touching its code | **Adopt.** No root, no containers |
| 3 | **`landlock`** (PyPI / `Edward-Knight/landlock`) | Python binding: `Ruleset().allow(path).apply()` | MIT | 28 ★, active CI; **1.0.0.dev5, alpha**; ABI 1–3 & 5 only, **no TCP (v4)** | Self-sandbox inside a Python worker at import time | **Adopt with eyes open.** Alpha; pin and test |
| 4 | **bwrap `--ro-bind /` + one `--bind <store>`** | Write-path declaration by construction: nothing is writable unless named | already in the toolchain | — | Inverts `kart-sandbox.json`'s default | **Cheapest change in this document** |
| 5 | **systemd `ProtectSystem=strict` + `ReadWritePaths=` + `PrivateTmp=` + `InaccessiblePaths=` + `IPAddressDeny=any`** | Declarative write-path and egress policy in a unit file | LGPL-2.1 | Core systemd | Long-running services, not tasks | **Adopt for daemons.** Best inheritability score of anything here |
| 6 | **Google Capslock** (`google/capslock`) | Static transitive capability analysis for Go packages: **FILES, NETWORK, EXEC**, SYSTEM_CALLS, UNSAFE_POINTER, ARBITRARY_EXECUTION. `capslock compare` diffs against a committed baseline | BSD-3-Clause (Go) | 1.2k ★, 267 commits | The *shape* §6 wants; and it makes `EXEC` first-class | **The model to copy.** Go-only, so copy the design, not the binary |
| 7 | **Pysa** (`facebook/Pysa`) | Taint analysis: sources → sinks over Python dataflow. Model `PII_MINOR` accessors as sources; `open(...,'w')`, `Path.write_*`, `os.replace`, `subprocess.*`, `socket.*` as sinks | MIT | Active, 21,032 commits. **Moved out of `facebook/pyre-check`, which was archived 26 Jun 2026.** Needs Pyrefly, Python 3.9+ | "Did student data reach a write outside the store?" as a *flow* | **Adopt for the seam files.** Heavy; scope it narrowly |
| 8 | **Semgrep taint mode** | `mode: taint` with `pattern-sources` / `pattern-sinks` / `pattern-sanitizers` in YAML | LGPL-2.1 (OSS engine) | Very active | Lighter version of #7; encode "subprocess is a sink" in ten lines | **Adopt first.** Ship Semgrep, graduate to Pysa if it pays |
| 9 | **WASI preopens / wasmtime `--dir` / WASI-Virt** (`bytecodealliance/WASI-Virt`) | Capability filesystem: a component can touch *only* preopened dirs. WASI-Virt bakes the policy into the artifact — "deny all subsystems, panic on any attempt"; `--mount /=./dir`, `--preopen /=/restricted/path`; Allow/Deny for Sockets, HTTP, Filesystem, Env, Stdio | Apache-2.0 w/ LLVM exception (Rust) | 230 ★, 111 commits; Config subsystem experimental | The strongest form of "declared, and the declaration travels with the code" | **Watch closely.** Real, but a language rewrite for the seam |
| 10 | **Deno** | `--allow-write=/path`, `--allow-read=`, `--allow-net=host:port`, `--deny-*`, `--allow-run`. README: "no file, network or environment access unless explicitly enabled" | MIT (Rust) | ~108k ★ | If a seam gets written fresh, write it here | **Consider for new seams only** |
| 11 | **Node.js permission model** | `--permission --allow-fs-write=/a,/b` with wildcards; `process.permission.has('fs.write', path)` queryable at runtime. **Stable since v23.5.0** (was `--experimental-permission`) | MIT | Core Node | Same as #10 | **Consider for new seams only** |
| 12 | **jart/pledge** | OpenBSD `pledge()` + `unveil()` on Linux via seccomp-bpf + Landlock. `pledge("stdio rpath", 0)` instead of hand-rolled BPF | ISC (C) | 139 ★, **23 commits — low activity** | `unveil()` *is* write-path declaration, as an API | **Read, don't depend.** Best vocabulary in the field |
| 13 | **Cilium Tetragon** | eBPF: kernel-enforced policies that can block a write or SIGKILL the process; also runs as pure audit. "blocking writes to immutable file paths" is a named use case. Runs on plain Linux, not only Kubernetes | Apache-2.0 / BSD-2 / GPL-2.0 (Go) | 4.9k ★, 6,927 commits; needs root + eBPF kernel | §6's enforcement-vs-ledger distinction, as one policy file with two modes | **Strong, but heavy.** Root and eBPF on a school box is a real cost |
| 14 | **LavaMoat** (`LavaMoat/LavaMoat`) | Per-package `policy.json` declaring `globals`, `builtins`, `packages`; SES compartments enforce it; `--autopolicy` generates it, `policy-override.json` amends it | MIT (JS) | Active | The *workflow*: generate the manifest, review the diff, fail on drift | **Copy the workflow.** See below |
| 15 | **`pytest-socket`** (`miketheman/pytest-socket`) | `--disable-socket` makes any socket use raise `SocketBlockedError`; `--allow-unix-socket`; `@pytest.mark.allow_hosts` | MIT | 342 ★, active; pytest 7+, Python 3.10+ | `CLAUDE.md` rule 19 — a guard shown to fail | **Adopt. One line in `pytest.ini`.** Cheapest item in this file |
| 16 | **nsjail** | Bind mounts declared `-R` read-only / `-B` read-write in a protobuf config; seccomp via Kafel can deny `execve` outright | Apache-2.0 (C++) | 4.0k ★ | Alternative to bwrap where you want the policy in a schema'd file | **Read the schema.** Root for most features |

### The honest finding

**There is no tool, in any ecosystem I could find, that statically checks a Python module against
a declared list of writable paths.** Capslock is the closest in spirit and it answers a coarser
question (*does this package touch FILES at all?*) in a different language. Semgrep and Pysa can
answer a related question (*does tainted data reach a write sink?*) but not the path question,
because the path is usually a runtime value. WASI, Landlock, bwrap, and systemd all take an exact
path list — but they enforce at runtime, not at review time.

So the honest recommendation is **declare once, enforce twice, and prove it with mutation.**

1. **Declare.** Extend the existing `safe_app_common` seam declaration with a `writes:` list, in
   the same file that already names the seam. One declaration, two enforcers — which satisfies
   `CLAUDE.md` rule 12 only if the reconciler is named in the same commit: a test that reads the
   declaration and derives both the AST allowlist and the Landlock ruleset from it, so they
   cannot drift.
2. **Enforce statically.** Extend the existing AST walk. It already walks for imports; add a
   collector for write-shaped call targets (`open` with a write mode, `pathlib.Path.write_bytes`
   / `write_text` / `open`, `os.replace`, `os.rename`, `shutil.*`, `tempfile.mkstemp` with a
   `dir=`) and flag any *literal or constant-derived* path not under the declared roots. This
   will not catch computed paths — say so in the docstring rather than overclaiming, which is the
   defect §6 keeps recording about itself. Add `subprocess`, `os.system`, `os.exec*`, `os.posix_spawn`
   and `multiprocessing` with a non-fork start method to `DEFAULT_FORBIDDEN`'s neighbourhood, and
   **run the checker in the repos where the bridges actually live** — §6 notes the `subprocess`
   rule is right and enforced nowhere it would bite.
3. **Enforce at runtime.** At worker start, before any student data is opened, apply a Landlock
   ruleset derived from the same declaration (`landlock` on PyPI for in-process, or wrap the
   worker in `landrun`). Belt: the bwrap mount policy already gives you this if you invert its
   default to `--ro-bind /` plus named `--bind`s. This is the layer that catches the computed
   path the AST walk cannot see.
4. **Prove.** A test that writes to `~/.willow/signals/x.json` from inside a seam and asserts
   `PermissionError`. That single test is the difference between §6's claim and §6's guarantee,
   and it is the direct answer to the `willow_bridge.py` finding — both implementations write
   outside the app's vault root into a directory another process reads, and the AST scan cannot
   see it because it is not an import.

**Cost:** the declaration and the AST extension are maybe 300 lines and a day. Landlock wiring is
an afternoon. The mutation tests are the point and should be written first.

### Two designs worth stealing wholesale

**Capslock's baseline-diff workflow.** `capslock compare` reads a committed baseline of what
capabilities the tree is allowed to have and fails when a dependency update grants a new one.
Applied here: commit a file listing, per module, its capability classes — and fail the build when
a module gains `NETWORK`, `EXEC`, or a write root it did not have. This is strictly better than a
boolean purity check because it makes the *change* visible rather than only the violation, and it
gives the `§16` middle something to be *about*. It also independently confirms §6's instinct:
Capslock treats `EXEC` as a capability class equal in standing to `NETWORK`, which is the same
judgement as *"an out-of-process shell is egress by another door."*

**LavaMoat's generate-review-freeze loop.** `--autopolicy` writes `policy.json` from the code;
a human reviews it; thereafter any drift fails. That inverts the usual failure mode where a
declaration is written once by hand, is wrong from week two, and nobody notices — which §16 calls
the only declaration in the fleet that is checked for rot. Generating the write-path manifest and
reviewing the *diff* is much more likely to survive a season than asking a developer to keep a
hand-written list accurate.

---

## GAP 3 — Import / dependency-direction enforcement

The requirement: seam→core, never the reverse, seams named explicitly. §6 already records that the
three-seam `assert_does_not_import` call exists only in a docstring, that `private-ledger` splits
it into three single-element calls, and that `oakenscrolls-office` names only `willow_bridge`.
That is a declaration problem, and it has an off-the-shelf answer.

| # | Project | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **import-linter** (`seddonym/import-linter`) | Python import contracts in a config file: **layers** (unidirectional, optional `independent` siblings), **forbidden** (source must not import target, *including through chains*), **independence**. Built on `grimp`'s import graph. Ships pre-commit hooks | BSD-2-Clause | 1.1k ★, 527 commits, active CI | Directly replaces the aspirational `assert_does_not_import` | **Adopt.** Top pick for gap 3 |
| 2 | **tach** (`tach-org/tach`) | Modules declare dependencies *and* a **public interface** (via `__all__`); enforces declared deps, layers, no cycles, and that cross-module calls go through the interface. Rust core, no runtime impact | MIT | 2.8k ★, 2,456 commits | The seam row's *"typed so sensitive values are not passable"* | **Adopt alongside #1.** Interfaces are the part import-linter lacks |
| 3 | **Google Capslock** | (see Gap 2 #6) direction *and* capability in one baseline | BSD-3 | 1.2k ★ | Both gaps at once | **Copy the design** |
| 4 | **ArchUnit** (`TNG/ArchUnit`) | The reference implementation: dependencies between packages/classes, layers, slices, cycles, via a fluent API run as ordinary unit tests | Apache-2.0 (Java) | 3.8k ★, v1.4.2, 2,691 commits | Vocabulary to borrow | **Read even if you never write Java** |
| 5 | **dependency-cruiser** (`sverweij/dependency-cruiser`) | `forbidden` rules over `from`/`to` with `pathNot`; JS/TS/CoffeeScript; text/dot/JSON/CSV/HTML/Mermaid reporters; exit codes for CI | MIT | 7.0k ★ | If any seam is ever JS/TS | **Adopt there** |
| 6 | **go-arch-lint** (`fe3dback/go-arch-lint`) | `.go-arch-lint.yml`: components by path glob, explicit allowed dependency edges, `canUse` for external imports; exit 1 on violation | MIT (Go) | 527 ★, 175 commits | Any Go component in the fleet | **Adopt there** |
| 7 | **arch-go** (`arch-go/arch-go`) | `shouldOnlyDependsOn` / `shouldNotDependsOn` in YAML | (Go) | Smaller than #6 | Alternative to #6 | **Second choice to #6** |
| 8 | **Deptrac** | Layers over classes with **deny-by-default**: "all dependencies between layers are forbidden," the ruleset is a whitelist. Graphviz/Mermaid output | MIT (PHP) | `deptrac/deptrac-src` **archived 17 Jul 2025**; package is `deptrac/deptrac` | The deny-by-default *design*, not the tool | **Steal the default.** Do not build on an archived repo |
| 9 | **Fuchsia component manifests (`.cml`)** | Not a linter — an OS. `use` / `offer` / `expose`; **directory capabilities with rights that must be a subset of the declaration** | BSD-3 (Google) | Active | Merges gap 2 and gap 3 into ONE declaration | **Read as prior art.** See "weirdest" |

### Top find, with transplant and cost

**import-linter** (BSD-2-Clause, Python, 1.1k stars, 527 commits) is the fix for the exact defect
§6 corrects itself about. The three-seam set that "is aspirational documentation" becomes a file
that either passes or exits non-zero:

```ini
[importlinter]
root_packages = terpsi

[importlinter:contract:core-cannot-reach-seams]
name = Core never imports a seam
type = forbidden
source_modules = terpsi.core.*
forbidden_modules =
    terpsi.seams.web
    terpsi.seams.serve
    terpsi.seams.willow_bridge
    terpsi.seams.export

[importlinter:contract:layering]
name = Roster/Library/Attendance/Ledger/Adjudication over core
type = layers
layers =
    terpsi.seams
    terpsi.domain
    terpsi.core
```

Three properties make this the right tool rather than merely an available one. **It checks
chains, not just direct edges** — `forbidden` catches `core → helper → seam`, which a
single-element `assert_does_not_import` call does not, and indirect reachability is how a purity
boundary actually rots. **The declaration is one file**, so the "which seams exist" question has
a single answer instead of being spread across three call sites that disagree, which is precisely
how `private-ledger` and `oakenscrolls-office` diverged. And **it has a pre-commit hook and an
exit code**, so it is enforcement rather than a ledger — a distinction `CLAUDE.md` rule 18
requires you to state, and this one you get to state on the strong side.

Add **tach** (MIT, 2.8k stars, 2,456 commits, Rust core) for the thing import-linter does not do:
public-interface enforcement. §6's seam row asks for seams "typed so sensitive values are not
passable," and cites UTETY's `knowledge.py` — *"Student PII cannot be transmitted because it is
not a parameter."* Tach enforces that any import not going through a module's declared interface
is an error, which is the mechanism that keeps a seam's surface from quietly widening from
`send(concept_query: str)` to `send(concept_query: str, context: StudentRecord)` six months in.
Direction enforcement stops the wrong import; interface enforcement stops the wrong *argument*,
and the argument is where the student data is.

**Cost:** genuinely small. Both are pip-installable, both run in CI and pre-commit, both adopt
incrementally. Half a day for the config, plus — rule 19 again — a test fixture containing a
deliberate `core → seam` import that asserts a non-zero exit. Without that mutation test you have
installed a linter, not a guarantee.

One warning that applies to all eight tools: **an architecture linter is enforcement only in the
repo that runs it.** §6 already documents the failure — every bridge in `willow-2.0`,
`willow-mcp`, `safe-app-willow-grove`, and `willow-bot` is undeclared because those repos have no
purity checker of any kind, and three of the fleet's `subprocess`-using bridges sit outside any
repo that checks. Adding `import-linter` here does not fix them, and terpsi-music should not
claim inherited coverage it does not have.

---

## Weirdest things I found

**1. Pony's `AmbientAuth` — "egress is inexpressible" as a *type*, not a lint.**
Pony has no global variables, no global functions, and no ambient authority. The `Main` actor
receives an `AmbientAuth` token at startup; `NetAuth` is a strictly smaller authority derived
from it, and `TCPAuth` smaller still. You cannot open a socket without a capability threaded to
you explicitly from the program's entry point. This is UTETY's insight — *PII cannot be
transmitted because it is not a parameter* — generalised from one function signature to an entire
language, and it is the cleanest existing statement of §6's inner ring. The transplantable idea
is not "rewrite in Pony." It is: **make the authority a parameter that must be passed, and give
the pure core no way to obtain one.** In Python that means the core never imports the seam and
never receives a client object; it receives data. That is a design rule import-linter can
actually check, and it converts a language feature into a contract line.

**2. Fuchsia's `.cml` manifests already are the artifact terpsi-music is trying to invent.**
Google shipped, in production, the exact declaration §6 asks for as a second half. A Fuchsia
component's manifest declares in one file both the capabilities it `use`s and the **directory
capabilities** it is offered — with explicit `rights`, and a framework rule that rights in a
`use`/`offer`/`expose` must be a *subset* of what the providing capability declared. `offer` even
supports `subdir` to narrow a directory to a sub-path. That is import-direction enforcement and
write-path declaration in one reviewable file, with monotone narrowing enforced by the runtime
rather than by convention. Nobody is porting Fuchsia to a school hub. But if you are going to
design the declaration format that unifies gaps 2 and 3, **read `.cml` first**, because the hard
parts — rights subsetting, sub-path narrowing, routing rather than granting — are already
solved there and are easy to get subtly wrong from scratch.

**3. The air-gap community has a shipping answer to "gate the export."**
The **Open Source Data Diode** (Apache-2.0, Rust, 44 stars, 108 commits) is a real, maintained
project of the **Netherlands Ministry of Defence's Cyber Innovation Hub**, built with Technolution,
Fox-IT and others: hardware schematics for a physically unidirectional link plus a proxy
framework on each side. **hairgap** (CEA — the French Alternative Energies and Atomic Energy
Commission; GPL-3.0, C, **archived Oct 2023**, needs root, explicitly no authentication or
encryption) does >200 MB/s over a one-way link using Wirehair error correction, because with no
return path you cannot retransmit. Also confirmed in this space: `pydiode`, `BlindFTP`, and two
Raspberry-Pi builds. This community starts from a premise §6 keeps reaching for and never quite
states: **the strongest export gate is one where the reverse channel does not physically exist.**
You will not buy a diode for a band program. But the *shape* — an export is a distinct
unidirectional transfer through a named proxy with no reply path, not a function call in the app
— is exactly §7.2's "gate the export, narrate the read," and these projects have already worked
out what breaks (no acks, no retries, so integrity must be forward-error-corrected and the
receipt must come out of band). That is directly reusable reasoning for the export gate's design.

**4. `unveil()` was polyfilled onto Linux — and then pointed at `make`.**
Justine Tunney's **jart/pledge** (ISC, C, 139 stars, 23 commits) implements OpenBSD's `pledge()`
and `unveil()` on Linux over seccomp-bpf plus Landlock, so a program declares `pledge("stdio
rpath", 0)` instead of hand-writing BPF. `unveil()` is *literally* the API gap 2 is asking for:
a process declares the filesystem paths it may touch and everything else stops existing. The
companion **jart/landlock-make** then applies it to GNU Make, so a *build step* declares its own
writable paths. That second one is the weirdly apt part: the way a transcript sidecar actually
escapes into a shared directory is not a heroic exfiltration, it is a build script or a helper
invocation writing somewhere nobody declared. Low commit count means read it for the vocabulary
and depend on `landrun` or the `landlock` binding instead — but "pledge/unveil" is the clearest
naming anyone has found for this idea, and clear naming is what gets inherited with the box.

**5. LavaMoat: the capability manifest as a generated, reviewed, frozen build artifact.**
MetaMask's **LavaMoat** (MIT) runs each npm package in an SES `Compartment` and enforces a
`policy.json` that declares, *per package*, which `globals`, which `builtins`, and which other
`packages` it may reach — with `--autopolicy` to generate it from the code and
`policy-override.json` to amend it. The mechanism is JavaScript-specific and irrelevant here.
**The workflow is the find.** §16 says the fleet's declarations rot and that only one is checked
for rot; §14's "Exists" column is unverified for the same reason. LavaMoat's answer is that a
capability declaration should be *derived from the code, diffed, and reviewed as a diff* — never
hand-maintained. Apply that to the write-path manifest and the seam list: generate, commit,
review the diff, fail CI on drift. That is `CLAUDE.md` rule 12's named middle, existing as a
file with a checksum instead of as an intention.

*Runner-up, for completeness:* **Genode OS Framework** (AGPL-3.0, releases 26.02 and 26.05,
migrating from GitHub to Codeberg) — a capability-based component OS where no component has
ambient authority and every access right is explicitly delegated. And **libkrun's "Transparent
Socket Impersonation"**, where a guest with *no network interface at all* still makes outbound
connections, over vsock, mediated entirely by the host. Both are the limit case of "there is no
client to call a destination."

---

## Things I checked that you should not build on

- **Ollama unix-socket support** — PR #8072 open since Dec 2024, rebased Jan 2026, still unmerged
  as of Feb 2026. Works for users who patch it. Front Ollama with `systemd-socket-proxyd`,
  `socat`, or nginx instead of waiting.
- **`facebook/pyre-check`** — archived 26 Jun 2026. Pyre → Pyrefly for typing; **Pysa moved to
  `facebook/Pysa`** (MIT, active). Cite the new location.
- **`deptrac/deptrac-src`** — archived 17 Jul 2025. Steal the deny-by-default ruleset design; do
  not adopt the tool.
- **`cea-sec/hairgap`** — archived Oct 2023, requires root, no authentication or encryption by
  design.
- **`landlock-lsm/island`** — Rust, Apache-2.0/MIT, TOML profiles (nice shape), but the README
  says "under active development and not yet ready for production use," 40 commits. Watch.
- **`landlock` on PyPI** — `1.0.0.dev5`, alpha, ABI 1–3 and 5 only, no TCP (v4), no abstract-socket
  or audit support. Usable; pin the version and own a test.
- **nsjail** — needs root for most features; unprivileged only via `--use_pasta`. Its protobuf
  config schema is still worth reading next to `kart-sandbox.json`.
- **Tetragon** — needs root and a recent eBPF-capable kernel. Powerful and genuinely dual-mode
  (audit *or* kill), which is the enforcement/ledger distinction as a config flag. Weigh against
  "understandable by whoever inherits the box."
- **`systemd JoinsNamespaceOf=`** — issues #17485 (silent failure to join until restart/reboot)
  and #29429 (user units cannot join). Verify shared netns positively in install acceptance.
- **Landlock network rules** — port-based, not address-based; TCP only. A layer, not a boundary.

## Sources

- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) · [bubblewrap](https://github.com/containers/bubblewrap) · [anthropic-experimental/sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime)
- [systemd-socket-proxyd(8)](https://www.man7.org/linux/man-pages/man8/systemd-socket-proxyd.8.html) · [PrivateNetwork](https://linux-audit.com/systemd/settings/units/privatenetwork/) · [systemd#17485](https://github.com/systemd/systemd/issues/17485) · [systemd#29429](https://github.com/systemd/systemd/issues/29429)
- [Ollama #739](https://github.com/ollama/ollama/issues/739) · [Ollama PR #8072](https://github.com/ollama/ollama/pull/8072)
- [Landlock kernel docs](https://docs.kernel.org/userspace-api/landlock.html) · [landlock.io](https://landlock.io/) · [landrun](https://github.com/Zouuup/landrun) · [island](https://github.com/landlock-lsm/island) · [landlock (PyPI)](https://pypi.org/project/landlock/) · [Edward-Knight/landlock](https://github.com/Edward-Knight/landlock)
- [jart/pledge](https://github.com/jart/pledge) · [jart/landlock-make](https://github.com/jart/landlock-make)
- [nsjail](https://github.com/google/nsjail) · [libkrun](https://github.com/containers/libkrun) · [Firecracker vsock](https://github.com/firecracker-microvm/firecracker/blob/main/docs/vsock.md)
- [google/capslock](https://github.com/google/capslock) · [capslock capabilities](https://github.com/google/capslock/blob/main/docs/capabilities.md) · [facebook/Pysa](https://github.com/facebook/Pysa) · [Pysa basics](https://pyre-check.org/docs/pysa-basics/) · [Semgrep taint mode](https://semgrep.dev/docs/writing-rules/data-flow/taint-mode/overview)
- [WASI-Virt](https://github.com/bytecodealliance/WASI-Virt) · [Deno](https://github.com/denoland/deno) · [Node permissions](https://nodejs.org/api/permissions.html) · [LavaMoat policy](https://github.com/LavaMoat/LavaMoat/blob/main/docs/policy.md)
- [Tetragon](https://github.com/cilium/tetragon) · [pytest-socket](https://github.com/miketheman/pytest-socket)
- [import-linter](https://github.com/seddonym/import-linter) · [docs](https://import-linter.readthedocs.io/en/stable/) · [tach](https://github.com/tach-org/tach) · [ArchUnit](https://github.com/TNG/ArchUnit) · [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) · [go-arch-lint](https://github.com/fe3dback/go-arch-lint) · [arch-go](https://github.com/arch-go/arch-go) · [deptrac-src](https://github.com/deptrac/deptrac-src)
- [Pony object capabilities](https://tutorial.ponylang.io/object-capabilities/object-capabilities.html) · [AmbientAuth](https://stdlib.ponylang.io/builtin-AmbientAuth/) · [Fuchsia capabilities](https://fuchsia.dev/fuchsia-src/concepts/components/v2/capabilities) · [Fuchsia directory capabilities](https://fuchsia.dev/fuchsia-src/concepts/components/v2/capabilities/directory) · [Genode 26.02](https://genode.org/news/genode-os-framework-release-26.02)
- [Open Source Data Diode](https://github.com/CyberInnovationHub-NLD/OpenSourceDataDiode) · [hairgap](https://github.com/cea-sec/hairgap) · [pydiode](https://github.com/ClarkuCSCI/pydiode) · [Bubblewrap examples (ArchWiki)](https://wiki.archlinux.org/title/Bubblewrap/Examples)
