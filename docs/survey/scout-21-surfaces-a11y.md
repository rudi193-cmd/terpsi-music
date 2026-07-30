# Scout 21 — Surfaces and accessibility

Slice: the presentation layer, and the accessibility rules already committed to.
Answers toward `docs/ARCHITECTURE.md` §18 item 4 ("Which surfaces exist", **blocking for layout**).

Grounded in: §18.4, §15 "Rendering them", §4 + §4.1 + §4.2 (incl. the honest caveat about a
browser-delivered decryptor), `CLAUDE.md` 14 and "Working here".

**Provenance discipline (§15).** Every row below carries a rung. `P1` = I opened the repo/file and
read the thing itself. `P2` = named source read but not executed, with enough recorded to survive its
disappearance (commit-visible path, license string, or quoted type definition). Nothing here is `P3+`.
Star and commit figures are as fetched 2026-07-30 and are that page's claim, not a count I derived.

---

## 1. Ranked table

| # | Project | What it is | License | Activity (as fetched 2026-07-30) | Maps to | Verdict | Rung |
|---|---|---|---|---|---|---|---|
| 1 | **`votingworks/vxsuite` `libs/types/src/ui_theme.ts` + `libs/ui/src/themes/`** | A shipping voting system whose theme type is `ColorMode = Touch \| Desktop \| Print` and `SizeMode = Touch \| Desktop \| Print`, plus `isVisualModeDisabled`. Print is a *colour mode*, not an export. | GPL-3.0 | 10,182 commits on main; TS+Rust | §15 "Rendering them"; §4 judge kiosk; printed roster/program | **steal-the-idea** (GPL-3 blocks linking; the type is the prize) | P1 |
| 2 | **`catppuccin/whiskers`** | Tera-templated palette→port generator with `--check`: renders the template and *fails with exit 1 if it differs from the committed output*. | MIT | active; on crates.io, FreeBSD ports | §16 named middle for the token pair; §15 backend parity | **adopt the `--check` pattern** | P2 |
| 3 | **`freedomofpress/webcat`** | Blocking code-signing + transparency for browser apps: signed manifest, Sigsum/Sigstore log, CSP enforcement, Firefox extension. Self-described **alpha**, "might not yet provide the intended security guarantees." | MIT | 722 commits; TS; ext published on AMO | §4.2 honest caveat — the browser-delivered decryptor | **read-only-interest now, adopt the disclosure shape** | P1 |
| 4 | **`waict-wg/waict-integrity-spec` + `-transparency-spec`** | Cross-vendor (Mozilla, Cloudflare) browser-native spec: site-wide manifest hashing every file served, publicly logged. Integrity spec updated 2026-07-17. | spec drafts | active WG | §4.2; §16 declaration-vs-enforcement | **read-only-interest** (watch; not deployable) | P2 |
| 5 | **Atkinson Hyperlegible / Hyperlegible Next / Hyperlegible Mono** | Typeface engineered for maximum character *distinction* (not beauty) for low vision. Next adds variable weight + expanded charset; **there is a monospace cut**. | SIL OFL | active; `googlefonts/atkinson-hyperlegible` | one typeface family spanning TUI (mono), web, and print — a single vendor-independent asset | **adopt** | P2 |
| 6 | **Chartability** (Frank Elavsky) | 50 accessibility heuristics written as *testable questions*, POUR + Compromising/Assistive/Flexible. Peer-reviewed (EuroVis 2022). | CC BY-SA 3.0 | v2 (2022), stable | §15 no-colour-alone; the L/T/P badge; §10 acceptance-is-mutation | **adopt as the test-case source** | P2 |
| 7 | **Textual** + **`pytest-textual-snapshot`** | TUI framework, MIT. Snapshot plugin saves an SVG of the running app and fails the test on diff; `--snapshot-update` to re-bless. | MIT | active; Textualize | the staff/director/tech surface; the parity harness | **adopt** (framework + snapshot), see §3 caveat | P2 |
| 8 | **`muesli/termenv` colour profiles** (and lipgloss on top) | Four profiles — `Ascii` (b&w only), `ANSI`, `ANSI256`, `TrueColor` — with automatic degradation, and `SetColorProfile` to **force a profile in tests**. | MIT | active | the `TERM=dumb` ASCII path as a *forced* CI condition, not a hope | **steal-the-idea** (Go; the idea ports trivially) | P2 |
| 9 | **Typst** | Rust typesetting system, single ~40MB binary, integrated scripting, loads CSV/JSON/XML directly, designed for paged media. PDF accessibility work funded by NLnet NGI Zero. | Apache-2.0 | 55.2k stars; 4,835 commits | printed concert program + printed roster from roster data | **adopt** (pick one of #9/#10) | P1 |
| 10 | **WeasyPrint** | Pure-Python CSS Paged Media engine; *not* browser-based, so no JS, which here is a feature. | BSD-3-Clause | 9.4k stars; 6,547 commits; releases every 2–3 months | print backend that can share CSS with the web surface | **adopt** (alternative to #9) | P1 |
| 11 | **`AndyOGo/stylelint-declaration-strict-value`** | Stylelint plugin: makes a raw hex/named colour on a named property a **lint error**, forcing a token. | MIT | active; on npm | §15 "twenty-one TUIs re-derived the palette; `story-timeline/app.py` has sixty hardcoded colours" | **adopt** | P2 |
| 12 | **Okabe–Ito (8-colour) + Paul Tol qualitative schemes** | The de facto CVD-safe categorical palettes. Okabe–Ito is *empirically* safe, not mathematically guaranteed — and explicitly categorical, not ordinal. | public / permissive; many impls (incl. CTAN `colorblind`) | stable since 2002 / ongoing | the `L1–L5` / `T0–T4` / `P1–P5` palettes | **adopt, with the caveat in §2.5** | P2 |
| 13 | **`adobe/leonardo`** (`@adobe/leonardo-contrast-colors`) | Generates colours *from target contrast ratios* against a background, rather than picking hues and hoping. | Apache-2.0 | monorepo, published npm | makes an ordinal ladder monotonic in **luminance**, which survives greyscale and print | **steal-the-idea** | P2 |
| 14 | **GOV.UK Design System + Service Manual** | "One thing per page"; "build an experience that works well without JavaScript"; "government services should be functional using only HTML." Backed by research showing low-confidence users complete one-per-page forms better. | `govuk-frontend` MIT; guidance OGL | active | §4.2 "a workflow a non-technical guardian completes in under a minute" | **steal-the-idea** | P2 |
| 15 | **USWDS** (`designsystem.digital.gov`) | "Color should only be used as progressive enhancement — if color is the only signal, that signal won't get through as intended to everyone." Ships a **per-component `accessibility-tests/` page** enumerating the checks. | US Gov public domain | active | §15's one-requirement-this-document-adds, already written by someone else, plus a model for per-component test enumeration | **adopt the patterns and the accessibility-tests-per-component convention** | P2 |
| 16 | **htmx** (alt: Datastar, Unpoly) | Hypermedia sprinkles, no build step. htmx's own argument: "opting not to use a build step drastically minimizes the labor required to keep htmx up-to-date." Datastar is ~11KB covering both round-trips and local reactivity. | htmx BSD-2; Datastar MIT | all active | §11.1 exit plan; "readable by whoever inherits the box" | **adopt htmx** | P2 |
| 17 | **SimpleWebAuthn** | `@simplewebauthn/browser` + `@simplewebauthn/server`, split so the browser half holds no secrets. Handles the full registration/auth ceremony, platform + roaming authenticators. | MIT | active | §4.1/§4.2 passkey enrollment with no help desk | **adopt** | P2 |
| 18 | **`cage`** (Wayland kiosk compositor) | Displays exactly one maximised app; ignores move/resize/minimise/unmaximise. ~single-purpose, tiny. | MIT | low churn, stable | §4 judge kiosk the org owns and wipes | **adopt** | P2 |
| 19 | **Vale** (+ `papa` for grade level) | Go binary, no runtime deps, markup-aware prose linter with a `Readability` style; drops into CI or a pre-commit hook. `papa` exits non-zero above a max grade. | MIT | active | "plain language" as **enforcement**, not a style note (CLAUDE.md 18) | **adopt Vale** | P2 |
| 20 | **Evolu** | Local-first: SQLite + CRDT + E2E-encrypted sync/backup, works offline and without a specific server. | MIT | 3,087 commits; 1.9k stars | §4.2 option (b) PWA replica over the mailbox relay | **steal-the-idea** — toolchain cost is real (see §2.7) | P1 |
| 21 | **Anywhere Ballot** (Chisnell/Davies/Summers, U. Baltimore) | Responsive, standards-compliant ballot-marking front end designed and iteratively tested **with low-literacy voters and voters with mild cognitive disabilities** — a population usually skipped. USENIX JETS paper documents the method. | Creative Commons | 2014, static | the guardian form; the judge kiosk | **steal-the-idea** | P2 |
| 22 | **Center for Civic Design Field Guides Vols 1–10** | Ten pocket guides, each 10 research-backed guidelines with examples, on ballots, instructions voters understand, poll-worker materials, accessible online information. | **CC BY-NC-ND 3.0** | stable, in use by US election officials | plain-language guardian surface; printed materials | **read-only-interest** — ND forbids derivatives, so read and reimplement, never vendor | P2 |
| 23 | **`tinted-theming` / base16** | One YAML palette → mustache templates → 70+ terminal and GUI apps. The oldest, most-proven "one palette, many backends" pipeline. | MIT | active (base17/base24/BaseNext in flight) | prior art for the token pipeline half | **read-only-interest** (16 syntax slots is the wrong ontology for semantic tokens) | P2 |
| 24 | **Style Dictionary v4 / Terrazzo** | DTCG (W3C Design Tokens, first stable version Oct 2025) reference implementations; JSON tokens → many platform outputs. | Apache-2.0 / MIT | active | the token pipeline, if `safe-design` needs a standard interchange format | **read-only-interest** — neither has a terminal/ANSI or ASCII backend; you'd write it | P2 |
| 25 | **`liblouis`** | Braille translator/back-translator, C, no runtime, bindings for Python/Java/JS. Powers NVDA and Orca. Contracted/uncontracted, many languages, Nemeth math. | LGPL-2.1+ (lib), GPL-3+ (CLI tools) | active | a printed braille roster or call sheet as a *third* print target | **read-only-interest** (real, but not day one) | P2 |
| 26 | **Hanko** | Self-hostable Go passkey backend + web components, FIDO2-certified. | AGPL-3.0 | active | passkey enrollment | **read-only-interest** — AGPL plus a whole extra service you do not need next to #17 | P2 |
| 27 | **`Textualize/textual-serve` / `textual-web`** | Serves a Textual app in a browser: subprocess per session, custom protocol over a websocket, terminal-in-browser. | MIT | 396 stars, active | tempting shortcut for "TUI *and* browser" | **read-only-interest — and see §3, this is a trap for the guardian persona** | P1 |

---

## 2. The finds that matter, with the transplant and the cost

### 2.1 vxsuite's `UiTheme` is the answer to §18.4 that is already written down

I read `libs/types/src/ui_theme.ts`. The type is:

- `ColorMode = 'contrastHighDark' | 'contrastHighLight' | 'contrastMedium' | 'contrastLow' | 'desktop' | 'print'`
- `SizeMode = 'touchSmall' | 'touchMedium' | 'touchLarge' | 'touchExtraLarge' | 'desktop' | 'print'`
- `ScreenType = 'builtIn' | 'elo13' | 'elo15' | 'lenovoThinkpad15'`
- `UiTheme = { colorMode, colors, screenType, sizeMode, sizes, isVisualModeDisabled }`

Four things transfer, and each of them is a decision §18.4 is asking for:

1. **Print is a `ColorMode`, not an export.** `libs/ui/src/reports/layout.tsx` has
   `printedReportThemeFn` returning `makeTheme({ colorMode: 'contrastHighLight', sizeMode: 'touchSmall' })`,
   and `libs/ui/src/bmd_paper_ballot.tsx` wraps the printed ballot in
   `<VxThemeProvider colorMode="contrastHighLight" sizeMode="touchSmall">`. The paper artifact renders
   through the *same* provider as the screen. This is exactly what §15 means by structural parity, and it
   means the printed concert program is a rendering backend rather than a reporting feature — which
   answers "which of `safe-design`'s backends is load-bearing" with "all of them, because print is one."
2. **Kiosk is a `sizeMode` + `screenType`, not a separate app.** The judge tablet is `touchLarge` on a
   named `screenType`, under the same components. The `screenType` enum being a *list of specific
   hardware models* is the honest version: they name the panels they have tested on. Terpsi should name
   the judge tablet and the band-room screen the same way, because "responsive" is a claim nobody tests.
3. **`isVisualModeDisabled` is a first-class boolean in the theme.** A mode where the screen carries
   nothing and the interaction is entirely audio (VxMarkScan's accessible controller: volume, speech rate,
   pause/resume, headphone jack). That is a fifth backend, and having it in the theme type is what stops
   it rotting.
4. **`libs/printing/src/render.tsx` carries the drift comment**: *"Initial report ported from VxAdmin,
   thus `desktop` theme to match styles. TODO: Migrate older prints to print theme."* An unmigrated
   pair, named in a comment, with no test failing. That is §16's exact failure mode observed live in the
   best available prior art — worth citing in the app's own docs as the reason the parity test exists.

**Cost.** vxsuite is **GPL-3.0**, so this is a read-and-reimplement, not a dependency. It is a
TypeScript/React/styled-components monorepo with 10,182 commits and Storybook — do not try to extract
`libs/ui`. What you take is roughly 60 lines of type definitions and one architectural commitment.
Half a day to read, one afternoon to transcribe into whatever `safe-design` calls a backend.

### 2.2 `whiskers --check` is the named middle §16 demands, and it is 20 lines of CI

The project's rule is that the parity test matters more than the token pipeline, and `whiskers` is the
only tool I found that ships the test rather than the aspiration: it renders the template and, instead
of printing, *compares against the committed output and exits 1 on any difference*. Generated files
cannot change without a corresponding template change.

**Transplant.** One palette file (`tokens.yaml` or DTCG JSON). One template per backend: `tui.py` or
Textual `.tcss`, `web.css`, `print.css`, and — the load-bearing one — `text.txt`, the ASCII/`TERM=dumb`
table. Commit the rendered outputs. CI runs render-and-diff. Anyone who repaints a token without
regenerating all four fails. `safe-design`'s claim in §15 is that "the Textual and CSS backends resolve
every token through the same `xterm256()` … and a test exists to catch anyone who breaks it" — item 0
says treat that as a claim to check. `--check` is the shape that claim should have, and if `safe-design`
already has it, this is the artifact to compare it against.

**Cost.** Near zero: a Tera template per backend plus a CI step. The discipline cost is real though —
committed generated files mean every palette PR touches five files, which is the point.

**And the mutation the rule requires (CLAUDE.md 19).** `--check` proves the backends agree on *colour*.
It does not prove they agree on *information*. The guard that must be shown to fail is a separate one:
render every rung badge under a forced monochrome profile and assert the rendered text still contains
the literal prefix. Concretely — force `termenv` profile `Ascii` (or Textual's monochrome), render, and
assert `"L4"` and `"P5"` and `"T1"` appear as **strings** in the output. Then add a deliberately-broken
badge that emits only a colour, and assert the test fails. That is the acceptance test for §15's
one-requirement-this-document-adds, and it is the thing no off-the-shelf linter does.

### 2.3 WEBCAT closes part of §4.2's honest caveat, and the honest thing is to say which part

§4.2 says: *"A browser-delivered decryptor … means the code doing the decryption is served by the thing
you don't trust. That is a real weakening."* True, and until recently unimprovable. WEBCAT (MIT,
`freedomofpress/webcat`, 722 commits) changes the *category* of the weakness: with an enrolled domain, a
signed manifest, a Sigsum/Sigstore transparency log, and CSP-based runtime enforcement, a swapped
decryptor becomes **publicly logged and detectable** rather than invisible. WAICT (`waict-wg`, Mozilla +
Cloudflare, integrity spec updated 2026-07-17) is the browser-native version of the same idea, without
an extension.

Three honest limits, all of which must be written down rather than glossed:

- WEBCAT self-describes as **alpha**: *"might not yet provide the intended security guarantees."*
- It ships today as a **Firefox extension**. The guardian who "will not install anything" will not
  install this. So it does nothing for the population §4.2's caveat is about.
- Transparency is detection, not prevention. A logged malicious decryptor still decrypted.

**Transplant, and it costs almost nothing.** Adopt `corpus-lens`'s disclosure form that §4.2 already
praises — *state what the wall does not hide, and put a test on it.* Write, in the relay's README:
"the browser-delivered path's code integrity is unverifiable on an unextended browser; that is why L3+
never travels it." Then make it enforcement rather than ledger: a test that walks every route reachable
by the browser-decryptor path and asserts every one is classified `L1`/`L2`, and that a route
deliberately marked `L3` is refused. WEBCAT/WAICT enrollment becomes a later hardening on the same
statement, not a new design. Cost: one test file now, one enrollment day when WAICT lands in browsers.

### 2.4 Atkinson Hyperlegible Next ships a monospace cut, which makes the four-backend story typographic as well as chromatic

SIL OFL, Braille Institute, designed so every glyph is maximally distinguishable from every other —
which is the typographic form of "no scale encoded by colour alone." The 2025 Next release adds variable
weight, expanded language coverage, and **a monospaced version**. So one licence-clean family covers the
TUI (mono), the guardian PWA (sans), and the printed program and roster (sans) — no per-surface font
decision, no webfont from a CDN, no vendor. Cost: two font files in the tree; the licence permits it.
This is the cheapest single item on this list and it removes a whole category of drift.

### 2.5 Okabe–Ito is the right palette and the wrong ontology, and that distinction is a §15 finding

Okabe–Ito is *categorical*. `L1–L5`, `T0–T4`, `P1–P5` are **ordinal**. Handing an ordinal scale a
categorical palette is the colour-space version of the direction hazard §15 opens with: nothing in the
palette tells a reader which end is worse, so colour cannot carry ordinality even for a reader with
full colour vision. Combine with Adobe Leonardo (Apache-2.0): generate each rung from a *target contrast
ratio* so the ladder is monotonic in luminance. A luminance ladder survives greyscale, survives
protanopia and deuteranopia and achromatopsia, survives a black-and-white printed program, and survives
`TERM=dumb` as a shade ladder or a fill ladder. Then the prefix carries the identity and the luminance
carries the direction, and colour carries nothing on its own — which is the rule.

Also note the direction hazard reaches the palette: if `L5` (most restricted) and `T4` (most privileged)
are both rendered as "brightest," a reader learns the wrong reflex. One of the two ladders must run
visually opposite, deliberately, and documented in the mapping table §15 requires.

### 2.6 Chartability turns "no colour alone" from a rule into 50 test cases

CC BY-SA 3.0, peer-reviewed at EuroVis 2022, 50 heuristics phrased as *testable questions* across POUR
plus Compromising/Assistive/Flexible. It is the only artifact I found that treats visual accessibility
the way this project treats invariants — as something you attempt to violate and assert refusal. The
evaluated claim is that novice practitioners audited more confidently and more easily with it.

**Transplant.** Take the Perceivable and Robust heuristics that bear on redundant encoding and lift them
into the test suite as named tests, one per heuristic, each with a mutation. Attribution is required
(BY-SA) and the ShareAlike applies to the heuristic text you copy, so cite rather than silently vendor —
which is CLAUDE.md 12's pair problem in miniature. Cost: a day to select, then it is just tests.

### 2.7 Print: Typst or WeasyPrint, and it turns on whether print shares CSS with the web surface

- **Typst** (Apache-2.0, 55.2k stars): single ~40MB binary, own scripting language, loads CSV/JSON/XML
  natively, built for paged media. A printed concert program — variable-length movement lists, per-piece
  personnel, page-break rules that must not orphan a movement — is precisely what its layout engine is
  for. PDF accessibility work is NLnet/NGI-Zero-funded and in progress; **tagged PDF / PDF-UA status is
  not something I verified**, and if a screen-readable PDF roster is a requirement that must be checked
  before committing.
- **WeasyPrint** (BSD-3-Clause, 9.4k stars, pure Python, releases every 2–3 months): CSS Paged Media,
  no browser engine, **no JavaScript** — which here is a security property, not a limitation, since the
  print path then cannot execute anything. Its decisive advantage: the print backend and the web
  backend consume *the same CSS tokens*, so `whiskers --check` covers both with one template pair.

**Recommendation: WeasyPrint**, on the parity argument alone — it makes print a token consumer rather
than a second typesetting language, and one fewer language is the maintenance argument this project
keeps making. Choose Typst instead if the printed program's typography is a genuine deliverable people
will judge (it will be better) and accept that print then becomes a separately-verified backend needing
its own `--check` template. Do not choose both.

### 2.8 Evolu is right in shape and expensive in toolchain

E2E-encrypted SQLite + CRDT, works offline and without a specific server, MIT, 3,087 commits. That is
§4.2 option (b)'s PWA replica, built. The cost is the thing to weigh honestly against "readable by
whoever inherits the box": pnpm workspaces, Turbo, Playwright, Vitest, TypeScript. §11.1 wants an exit
line; a CRDT-encrypted-SQLite-WASM stack is a hard thing to hand to a successor and a hard thing to
export from. For a transactional 5% — pay a fee, sign a form, view a balance, upload a physical — the
CRDT is solving a problem you do not have. **Steal the encrypted-local-store idea; start with
server-rendered HTML plus a service worker and an IndexedDB outbox**, and reach for Evolu only if
genuine offline *editing* with merge appears.

### 2.9 The plain-language requirement is enforceable, and CLAUDE.md 18 says to say which it is

"Forms a guardian completes in under a minute" is currently a hope. Vale (MIT, Go, no runtime deps)
makes it a gate: a `Readability` style with a maximum grade level, run over every guardian-facing string
and every SMS template, in CI. GOV.UK's "one thing per page" and "functional using only HTML" give the
form structure; USWDS gives the per-component accessibility-test convention; Center for Civic Design's
field guides and Anywhere Ballot give the evidence base for the population that actually struggles.
Cost: a `.vale.ini`, a vocabulary file, and the willingness to fail a build over prose.

Note the licence trap: the CCD field guides are **CC BY-NC-ND 3.0**. NoDerivatives means you may read
them and may not adapt or vendor them. Read, reimplement, cite.

---

## 3. Recommendation on §18 item 4

**Four rendering backends, one presentation middle, three trust paths. Not "a TUI or a browser app."**

### The answer

| Backend | Serves | Delivery |
|---|---|---|
| **TUI** | staff, techs, on-site director, off-site director/staff over the tailnet | Textual over SSH / local terminal; `willow-mcp` serve mode for the staff path per §4.3 |
| **Server-rendered HTML** | (a) guardians, transactional 5% only; (b) judges and clinicians on kiosk | htmx sprinkles, works with JS off; kiosk = same HTML at `touchLarge`/high-contrast under `cage` |
| **Print** | printed concert program, printed roster, per-graduate lane export (W-6) | WeasyPrint consuming the same tokens |
| **Text/ASCII** | screen readers, `TERM=dumb`, the parity test, and every `--format=text` export | the same renderer at forced monochrome |

The **middle** (CLAUDE.md 12, §16) is a *presentation IR*: a domain view returns a structured
description — rows, fields, rung badges with their prefixes, seal state, disposition dates — and the
four backends are thin renderers over it. Nothing in a backend knows about students; nothing in the
domain knows about colour. The named reconciler shipped in the same commit is the `--check`
render-and-diff plus the forced-monochrome prefix assertion of §2.2.

### First directory layout this implies

```
presentation/          # the middle: IR, tokens, rung rendering, ONE mapping table (§15)
  tokens.yaml
  templates/{tui,web,print,text}.*
  rendered/            # committed; CI diffs against it
surfaces/
  tui/                 # Textual app        — staff, techs, director
  web/                 # server-rendered    — guardian (5%) + judge kiosk
  print/               # WeasyPrint         — program, roster, W-6 export
  text/                # ASCII/plain        — screen reader + export + parity
tests/presentation/    # --check, forced-monochrome, prefix-present, mutation cases
```

Not `frontend/` and `backend/`. `frontend/` would immediately absorb three surfaces with different
trust paths and different personas into one tree, and §4's opening instruction is *"Do not build one
door."* The layout should make the four doors visible on `ls`.

### Reasoning

1. **§4 already decided this and §18.4 has not noticed.** §4 assigns five different transports to six
   personas. A single surface would have to be reachable by all five transports, which is precisely the
   exposure §4.1 exists to avoid. The surface count follows from the transport count, so "both" is not a
   hedge — it is what §4 says.
2. **The 95/5 split (§4.1) collapses the hard case.** SMS takes notification and acknowledgment with no
   surface at all. What is left for guardians is four interactions a year. That does not justify a
   PWA-shaped engineering programme, and §4.1 says so explicitly: *"a different and much smaller
   engineering problem."* Server-rendered HTML with a service worker is the right size. The PWA manifest
   is an add-on to that, not an architecture.
3. **Judge and guardian share a backend and must not share a trust path.** Both get HTML. The judge is
   on-site, on org hardware, under the knock (§7.2), at `touchLarge` high-contrast, wiped after. The
   guardian is off-site on an unknown phone behind a passkey. One renderer, two entry points, two
   session models. vxsuite proves this composes: same components, `colorMode` and `sizeMode` differ.
4. **Print is load-bearing and is a backend, not a report.** A printed concert program and a printed
   roster are named deliverables. §15 already lists "the printed program" as a reason colour cannot
   carry meaning. If print is an export, it drifts — and vxsuite's own
   `// TODO: Migrate older prints to print theme` is the empirical proof, in the best prior art
   available.
5. **The text backend is not a fourth chore, it is the test instrument.** It doubles as the
   screen-reader path (see the caveat), the `TERM=dumb` path `safe-design` claims to support, and the
   surface on which "no scale encoded by colour alone" is *provable*. If a rung is legible in
   `surfaces/text/`, it is legible everywhere. If it is not, the invariant is broken and CI says so.

### What to reject, explicitly

- **Do not serve the TUI to guardians via `textual-serve`.** It is genuinely tempting — MIT, 396 stars,
  "3 lines of code," one codebase, two surfaces. It is wrong for this app on four counts. (i) It is
  terminal-in-browser; a guardian on a phone gets a fixed-cell grid, no native form controls, no
  autofill, no passkey conditional UI. (ii) A **subprocess per session** on the hub, driven by an
  inbound websocket, from 200 households, is the opposite of §4.1's zero-inbound posture. (iii) Terminal
  emulation in a browser is a screen-reader dead end — see the caveat below. (iv) It cannot print. Keep
  it in mind only for off-site *staff*, where it might save building a second staff surface, and even
  there the tailnet already solves the problem.
- **Do not build a native mobile app.** An app store is a third party interposed on access to a minor's
  records, with a review process that can withdraw the surface, and it fails §11.1's exit test.
- **Do not build one browser app for all six personas.** That is the collapse §4 opens by forbidding.

### The caveat that must be written into the decision, not discovered later

**A TUI is not accessible because it is text.** The strongest counter-evidence I found to my own
recommendation is xogium's "The text mode lie" (widely discussed; OSnews mirror, HN thread), and the
argument holds: there is no accessibility tree for terminals, no ARIA, no roles. Box-drawing borders are
announced glyph by glyph; braille-pattern spinners are read as *braille* on a braille display. Textual's
accessibility story — monochrome mode shipped, high-contrast and colour-blind themes and screen-reader
integration described as **planned** — is a roadmap, not a feature, and I could not find shipped
screen-reader integration. So:

- The screen-reader story for this app lives in `surfaces/text/` and in the HTML surface, **not** in the
  TUI. Say that in the decision record rather than letting "it's a TUI, it's text, it's fine" stand.
- The forced-monochrome/plain-text render is therefore doing double duty and should be treated as a
  shipped surface with its own tests, not a fallback.
- Budget for `liblouis` later if a braille roster is ever asked for; do not pretend the TUI covers it.

### What blocks what

Nothing here blocks §18 items 1 (`L1–L5` definitions) or 3 (lane schema) — but item 1 blocks *rendering*
the badges, since you cannot render a ladder nobody has defined. Sequence: define `L1–L5`, then the one
mapping table §15 requires, then `presentation/tokens.yaml`, then the four templates, then the parity and
mutation tests. The directory layout can be committed today; it does not depend on the definitions.

---

## 4. Weirdest things I found

**1. FAO pesticide label pictograms, and the comprehension studies that show they fail.** Pesticide
labels are the most redundantly-coded consumer artifact in existence: a colour band for hazard class,
*plus* a pictogram, *plus* a signal word, *plus* a three-panel layout mandated by FAO Guidance on Good
Labelling Practice. Triple redundancy, decades of iteration, life-or-death stakes. And the field studies
— South African farm workers' interpretation of pictogram risk data, a Lebanese validated questionnaire
on pictogram-and-colour-code comprehension, a cluster-randomised trial among Ugandan smallholders — keep
finding that comprehension is poor, and that the **colour band is the least-understood element**. This is
the best evidence I found for the project's own rule, and it is *negative* evidence: it does not say
"add a glyph," it says colour bands fail even when everything else is right, and glyphs are not
self-evident either. The operational conclusion for `L1–L5` is stronger than §15's: the prefix and the
**word** are the channel; colour and glyph are decoration. `field-acoustics` writing `ASSUMED` is not
merely getting it right, it is the only channel that measurably works.

**2. NASA CR-177605, "On the Typography of Flight-Deck Documentation" (Degani, 1992).** Degani and Wiener
set out to study checklist *procedures*, kept encountering flight plans and manifests that were
typographically unusable, and wrote a separate NASA contractor report on typography — because font size,
weight, italics and case have direct consequences for legibility "in low visibility situations such as
when smoke is in the cockpit." A public-domain government specification for typesetting documents that
must be read correctly by a stressed person in bad light. Which is a band director on a stadium sideline
at dusk holding a printed call sheet, or a judge under a press box light. It belongs in the print
backend's style notes. (Both the report and Degani & Wiener's *Human Factors* 35(2) paper circulate as
free PDFs; NTRS and a SINTEF mirror both 403'd my fetches, so I have this at `P2` from search
metadata — worth a manual download before citing.)

**3. IEC 60601-1-8 — the ordinal-scale rendering problem, already solved under regulation.** Medical
alarms have exactly three ordinal priorities, and the standard encodes each on **four** simultaneous
channels: colour (red/amber/green), flash rate, auditory pulse count and rhythm (10 fast pulses / 3
slower / 1–2 slower still), and pitch range. It also fixes the *ordering* across channels — low priority
must not be louder than medium, medium not louder than high — so the rungs cannot invert under
composition. And the standard says colour alone shall not convey important information. This is a
regulated, litigated, decades-refined answer to "how do you render `T0–T4` and `L1–L5` so a tired human
cannot misread them," and the transferable rule is: a rung is not one encoding with a fallback, it is
*n* encodings that must all agree and all be ordered the same way. That is a much sharper spec than
"add a glyph."

**4. Proquints (`draft-rayner-proquint`, on draft 11).** CVCVC pronounceable encoding of binary — every
16 bits becomes five letters chosen for pronounceability across Indo-European languages, reversibly. The
draft's own stated benefits are reduced transcription errors and friendliness to non-technical users.
Consider a guardian on the phone with the director reading a form reference, a judge reading a lane
identifier to a tabulator across a stadium, or a director dictating a student identifier over a
walkie-talkie at a competition — currently a UUID, ten seconds of "was that a B or a D." Proquint turns
a lane or disclosure-log identifier into two speakable syllables with no spelling alphabet. The
radio/teletype-era instinct, formalised as an IETF draft, with a permissive reference implementation.

**5. Hablamos Juntos / SEGD Universal Symbols in Health Care, and `isVisualModeDisabled`.** A pair. The
symbol set is ~50 vector pictograms developed 2003–2010 by SEGD and Hablamos Juntos with Robert Wood
Johnson funding, tested and iterated in two research phases *specifically* with limited-English and
limited-reading-proficiency populations, expanded from the original set after testing, free vector
download. It is the only tested, free, wayfinding-grade symbol vocabulary I found aimed squarely at the
"hundreds of guardian households spanning the whole range of tech literacy" persona — though the
downstream literature ("How universal are universal symbols?") is honest that cross-cultural adoption
varies, so it is read-only-interest until comprehension-tested with the actual families. Paired with
vxsuite's `isVisualModeDisabled` — a shipped, certified voting system in which "no screen at all" is a
boolean in the theme type — it suggests the guardian surface's real ladder is not
mobile→desktop but **audio → symbol+word → text → rich**, and that the top of that ladder is the
optional one.

---

## 5. Loose ends worth one more pass

- **Typst's tagged-PDF/PDF-UA status is unverified.** If a screen-readable PDF roster is a requirement,
  check before choosing between Typst and WeasyPrint (neither's a11y story did I confirm at `P1`).
- **`safe-design`'s claimed parity test is item-0 territory.** §15 asserts the Textual and CSS backends
  resolve through the same `xterm256()` and "a test exists." Open it. `whiskers --check` is the artifact
  to compare it against, and the forced-monochrome prefix assertion is almost certainly absent.
- **No tool anywhere detects colour-only encoding automatically.** I looked hard. axe-core, WAVE, and
  the commercial guided tests flag adjacent things (`link-in-text-block`, contrast) and every source
  concedes 1.4.1 needs human judgement. So the enforcement for §15's added requirement does not exist
  off the shelf and must be written: forced-monochrome render + assert-prefix-string-present +
  a mutation that removes the prefix and must fail. That is ~50 lines and it is the whole gate.
- **Prefixes should be structural, not stylistic.** The rule "prefix every rung so a bare integer cannot
  travel" is enforceable in the type system, not just the renderer: a rung type whose only string
  representation includes its prefix, with no integer coercion and no cross-type ordering. Python
  `enum.Enum` already refuses `<` between different enum classes; Rust `PartialOrd` is per-type. The
  units-of-measure libraries (`pint`, `astropy.units`, Rust `uom`) are the design pattern — a quantity
  that cannot be compared to a bare number. Cheap, and it kills `if level >= 3` at compile/import time
  rather than in review.
