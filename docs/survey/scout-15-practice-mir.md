# Scout 15 — Practice, mastery modelling, and machine feedback on a student's own playing

**Slice:** §1 Practice / §2 Assessment — pitch-rhythm-intonation analysis, practice-room primitives,
slow-down/loop, sight-reading generation, check-off trees, mastery models, longitudinal self-comparison,
shape-not-content practice logging.

**Method note, and a limit to declare up front.** The session's WebSearch budget was already exhausted when
this slice started (200/200), so every entry below was verified by fetching the actual repository page or by
GitHub repo-search, not by reading blog posts about it. That is a stronger evidence base for licence and
activity than search snippets would have been. It is a *weaker* base for discovery: I could not sweep for
projects whose names I did not already have a reason to guess. **Three claims below are explicitly marked
unverified** because the source page returned 403/404; per CLAUDE.md #17 they are flagged as claims to check,
not facts to build on. Star counts and licences are as displayed on the repo page on 2026-07-30.

---

## 1. Ranked table

Verdict key: **adopt** = put it in the tree; **steal** = take the design, write our own;
**read** = read it once, do not depend on it.

### Tier 1 — the flagship loop (measure 112 → every affected student's queue)

| # | Project | What | Licence | Activity / size | Maps to | Verdict |
|---|---------|------|---------|-----------------|---------|---------|
| 1 | `sildater/parangonar` | Offline **and online** note-level alignment: symbolic score ↔ performance MIDI, plus audio-to-score. Hierarchical DTW, neural matchers, `OnlineTransformerMatcher`, `TOLTWMatcher` | Apache-2.0 | 62★, Python | §8.1 score-position anchoring; longitudinal self-comparison | **adopt** |
| 2 | `CPJKU/partitura` | Score IO + symbolic model: MusicXML, MEI, Humdrum `**kern`, MIDI in; MusicXML/MIDI out | Apache-2.0 | 367★, Python | The machine-readable score layer the whole anchoring question depends on (§14 open q.) | **adopt** |
| 3 | `pymatchmaker/matchmaker` | **Real-time** score following. OLTW (Arzt, Dixon), HMM variants (`hmm`, `outerhmm`, `pthmm`), switching Kalman filter | Apache-2.0 | 71★, Python | Play-along that waits for the student; live loop tooling; "where am I in the score" | **adopt** |
| 4 | `groupmm/synctoolbox` | Music synchronisation via DTW — MrMsDTW, memory-restricted multiscale; ships audio-audio and audio-score notebooks | MIT | 138★, Python | Aligning September's 16 bars to May's; aligning judge audio to performance audio | **adopt** |
| 5 | `spotify/basic-pitch` | Polyphonic audio→MIDI with pitch-bend output. Ships TF **plus** CoreML, TFLite and ONNX conversions; CPU-first (TFLite default on Linux, ONNX on Windows) | Apache-2.0 (code **and** weights) | 5.4k★, pushed 2025-11-13 | Pitch/rhythm accuracy on a submitted recording; works for piano/guitar/double-stops, not just monophonic | **adopt** |
| 6 | `SonyCSLParis/pesto` | Self-supervised monophonic pitch estimator. **2m51s of audio in ~13s on CPU (~12× real time)** vs CREPE's ~12 min; ~800× fewer parameters; streaming mode; JIT/ONNX export | **LGPL-3.0** | 297★, Python | The on-device pitch/intonation engine. The one engine here that is honestly fast enough for a student's own laptop | **adopt** (mind LGPL) |
| 7 | `mir-evaluation/mir_eval` | Peer-reviewed reference implementations of MIR metrics (ISMIR 2014) — raw pitch accuracy, voicing, onset, beat, transcription | MIT | 708★, Python | The *definition* of "accuracy" in a playing-test score. Stops us inventing a number nobody can audit | **adopt** |
| 8 | `CPJKU/beat_this` | Transformer beat/downbeat tracker, ISMIR 2024, no DBN post-processing. **MIT code and MIT weights.** CPU fallback via `--gpu=-1` | MIT | 345★, Python | Rhythm accuracy; tempo-stability metrics; the clean alternative to madmom (see #26) | **adopt** |

### Tier 2 — practice tooling that works today

| # | Project | What | Licence | Activity / size | Maps to | Verdict |
|---|---------|------|---------|-----------------|---------|---------|
| 9 | `Signalsmith-Audio/signalsmith-stretch` | Header-only C++11 pitch/time stretch. Ships a **WASM/AudioWorklet build on NPM**, plus Python and Rust wrappers. Reports `inputLatency()`/`outputLatency()`; split-computation mode to even out CPU | **MIT** | 528★, C++ | Slow-down-without-pitch-shift, in the browser, offline. The single cleanest licence in the time-stretch space | **adopt** |
| 10 | `snakers4/silero-vad` | Voice-activity detector. **~2MB JIT model, <1ms per chunk on one CPU thread**, ONNX runtime, real-time on-device. MIT code *and* MIT weights | MIT | 9.8k★ | Shape-not-content practice logging: detect *that* sound was produced and for how long, persist no audio. See §3 | **steal / adopt** |
| 11 | `CAHLR/pyBKT` | Bayesian Knowledge Tracing with multiprior / multilearn / multiguess and per-item guess-slip. C++ core ≈75× faster than pure Python (500 students: ~1.5s vs ~2m). CPU, offline | MIT | 271★, Python | The direct comparison target for UTETY's in-house BKT. Per-item guess/slip is the variant a scale check-off tree wants | **adopt or read** |
| 12 | `fasiha/ebisu` | Bayesian recall model — Beta conjugate prior on recall probability, exponential decay. **Explicitly tolerates over- and under-reviewing**; gives P(recall) for any fact at any moment rather than a due date | **Unlicense** (public domain) | 338★, Python (+JS/Java/Dart ports) | Mastery decay on scales/rudiments **without a streak**. The most important find in the whole slice for §1's surveillance question — see §3 | **adopt** |
| 13 | `open-spaced-repetition/fsrs-rs` | FSRS: DSR (difficulty/stability/retrievability) memory model with an optimiser that **fits parameters to the individual's own local review log** | BSD-3-Clause | 399★, Rust | Spaced repetition for theory/ear-training items; per-student parameter fitting that never leaves the device | **adopt** |
| 14 | `cuthbertLab/music21` | Symbolic toolkit: programmatic notation generation, MusicXML export, key/interval/scale and roman-numeral analysis. Offline. (BSD since v2, was LGPL) | BSD-3-Clause | 2.5k★, Python | Sight-reading item **generation**; theory-quiz item generation; difficulty features | **adopt** |
| 15 | `patzly/tack-android` | The best-maintained FOSS metronome: subdivisions, changeable emphases, count-in, duration, **incremental tempo change**, swing, muted beats; standalone Wear OS app with haptic beats. **No ads, no analytics**, works without Google services | GPL-3.0 | 465★, Kotlin, active | Metronome/click infrastructure on a student's own device; the speed-trainer primitive | **adopt or steal** |
| 16 | `JorenSix/TarsosDSP` | Pure-Java real-time DSP: YIN, McLeod Pitch Method, AMDF, dynamic-wavelet pitch detection; percussion onset detection; **WSOLA time-stretch** and pitch shift. **No native dependencies, runs on Android and JVM** | GPL-3.0 | 2.2k★, Java | A tuner, drone, intonation histogram, and slow-downer in one dependency on a student's Android phone, fully offline | **adopt (GPL-3)** |
| 17 | `facebookresearch/demucs` | Music source separation. MIT code **and** MIT weights. CPU inference ≈1.5× track duration. 4 stems, 6-source experimental model adds guitar/piano, `--two-stems` karaoke mode | MIT | 10.4k★, **archived 2025-01-01**; active fork `adefossez/demucs` | Play-along generation: take a reference recording, remove the student's part, hand back a minus-one track | **adopt the fork** |
| 18 | `sonic-visualiser/sonic-annotator` | Batch CLI feature extraction over Vamp plugins → CSV, RDF/Turtle, JAMS JSON, MIDI, LAB. Active CI on Linux/macOS/Windows | GPL-2.0 | 47★, C++ | The offline batch layer for hub-side analysis of submitted recordings; pYIN via Vamp | **read / adopt** |
| 19 | `sonic-visualiser/tony` | Purpose-built GUI for extracting a pitch track from monophonic audio (pYIN), then **manually correcting it** note by note, with auditioning and snapping | GPL-2.0 | 63★, C++ | The teacher-review UI for a machine pitch analysis. Precisely CLAUDE.md #10: the machine's pitch track is a draft, a human seals it | **steal the interaction** |
| 20 | `infojunkie/mma` (Musical MIDI Accompaniment) | Chord chart → MIDI backing track with a groove/style library. Bob van der Poel, 2002–2021; this is a mirror | GPL-2.0 | 16★, Python | Accompaniment generation with zero model weights and zero licence risk. Ugly, deterministic, offline, and it works | **read / steal** |
| 21 | `interactiveaudiolab/penn` | FCNF0++ pitch and periodicity estimation; pretrained checkpoint ships (MDB-stem-synth + PTDB), MIT throughout | MIT | 279★, Python | Alternative to PESTO if LGPL is unacceptable. Weights are MIT, which PESTO's LGPL and Essentia's models are not | **adopt (fallback)** |
| 22 | `ctralie/linmdtw` | Linear-memory, parallelisable DTW for aligning two performances of the same piece; benchmarked against FastDTW and MrMsDTW at 23ms–1s thresholds | Apache-2.0 | 62★, Python | September vs May on the same 16 bars, on a hub with modest RAM | **adopt** |
| 23 | `rism-digital/verovio` | MEI/MusicXML → SVG engraving, compiles to **WebAssembly** (editor.verovio.org) | LGPL-3.0 / GPL-3.0 | 903★, C++20 | Rendering the passage next to the comment, offline in a browser. ⚠️ I could **not** confirm from the README that rendered elements carry stable measure/note IDs — that property is the whole reason to pick it, so verify before committing | **adopt, after verifying IDs** |
| 24 | `Abjad/abjad` | Python API over LilyPond for programmatic engraving with fine rhythmic/metric control | GPL-3.0 | 266★ | Sight-reading generation where the *look* of the page matters (beaming, tuplets) | **read** |
| 25 | `AudioKit/AudioKit` | Audio synthesis/processing/analysis for iOS, macOS, tvOS | MIT | 11.4k★, Swift | The drone generator and tuner substrate if there is ever an iOS client. ⚠️ I could not confirm `PitchTap` from the README | **read** |

### Tier 3 — licence traps, flagged loudly

| # | Project | The trap | Verdict |
|---|---------|----------|---------|
| 26 | `CPJKU/madmom` | Code is BSD. **The pretrained models are CC BY-NC-SA 4.0**, verbatim: *"If you want to include any of these files (or a variation or modification thereof) or technology which utilises them in a commercial product, please contact Gerhard Widmer."* madmom is the default recommendation for onset/beat/downbeat everywhere on the internet, and the models — the part that makes it work — are non-commercial | **do not adopt.** Use `beat_this` (MIT weights) |
| 27 | `birdnet-team/BirdNET-Analyzer` | MIT code, **CC BY-NC-SA 4.0 models**. The project states educational/research use is treated as non-commercial and freely permitted — which covers a school *using* it, but not a vendor *shipping* it | **read only** |
| 28 | `audeering/opensmile` | Dual-licensed. Verbatim: *"It is not allowed to use the open-source version of openSMILE for any sort of commercial product."* Free for private, research and educational use; commercial needs a paid audEERING licence | **do not adopt** |
| 29 | `CMU-Perceptual-Computing-Lab/openpose` | *"freely available for free non-commercial use"*; commercial licence via CMU FlintBox. 34.3k★, so it is the default thing anyone reaches for | **do not adopt.** Use `Sports2D` (#33) |
| 30 | `MTG/essentia` | AGPL-3.0 library — workable for an on-prem install, a real question for a distributed product. ⚠️ **UNVERIFIED:** `essentia.upf.edu/models.html` and `/licensing_information.html` both returned 403 to me, and neither the README nor `doc/sphinxdoc/machine_learning.rst` states a model licence. The pretrained-model licences are therefore **unknown**, and Essentia's models are widely believed to carry non-commercial terms. Treat as a blocking unknown, not as AGPL-only | **verify before any use** |
| 31 | `breakfastquay/rubberband` | GPL-2.0 + commercial. Verbatim: *"You may not legally distribute through any Apple App Store unless you have a commercial licence."* Best-in-class quality (R3 engine) | **read.** Use `signalsmith-stretch` (MIT) |
| 32 | `MontrealCorpusTools/Montreal-Forced-Aligner` | MIT code, 1.9k★, runs locally. ⚠️ Pretrained acoustic models live in a **separate** MFA Models repo and the README states no licence for them. Same shape as madmom | **verify weights** |

### Tier 4 — the weird ones (detail in §4)

| # | Project | What | Licence | Maps to | Verdict |
|---|---------|------|---------|---------|---------|
| 33 | `davidpagnon/Sports2D` | 2D joint angles from an ordinary video or webcam via RTMlib/RTMPose. Runs offline on CPU, "keeping data private" | BSD-3-Clause, 273★ | Embouchure, hand position, breathing posture, marching carriage — from a phone, no cloud | **steal** |
| 34 | `JorenSix/Olaf` | Acoustic fingerprinting that stores **fingerprints, not audio**. Runs on ESP32/ARM, desktop (LMDB), and **browser via WASM**; ~2000× real-time indexing | AGPL-3.0, 408★, C/Zig | Content-free proof that the assigned passage was practised. See §4.1 | **steal the idea** |
| 35 | `kitzeslab/opensoundscape` | Bioacoustics: CNN training on your own audio, pre-trained inference, sound localisation, and **RIBBIT** — detection of *periodic* sound. CPU, offline | MIT, 218★ | RIBBIT as a long-tone / steady-note / rudiment-periodicity detector. See §4.2 | **steal** |
| 36 | `GoldenCheetah/GoldenCheetah` | Desktop training analytics: **Banister impulse-response and PMC**, TRIMP, BikeStress, Critical Power, W'bal. Fully offline on local files | GPL-2.0, 2.2k★, C++ | Practice *load* rather than practice *compliance*; overuse-injury signal. See §4.3 | **steal the model** |
| 37 | `aradzie/keybr.com` | Typing tutor that "tracks every single keystroke and computes statistics for each individual key", "automatically generates lessons that focus on your weakest keys", and unlocks letters: *"More letters are added once you reach the target speed with the current ones."* | AGPL-3.0, 4.6k★ | The scale/rudiment/etude check-off tree, done as measured mastery gating rather than a teacher's checkbox. See §4.4 | **steal** |
| 38 | `iSoron/uhabits` (Loop Habit Tracker) | Habit "strength" formula instead of a chain. Verbatim: *"A few missed days after a long streak, however, will not completely destroy your progress, unlike many other don't-break-the-chain apps."* Offline, no account, *"Your confidential data is never sent to anyone."* | GPL-3.0, 10.1k★ | The anti-streak progress representation for the practice card. See §3 | **steal** |
| 39 | `jimbozhang/speechocean762` | Pronunciation-assessment corpus with a three-level rubric: **phone**-level goodness 0–2, **word**-level accuracy 0–10 plus stress, **sentence**-level accuracy / completeness / fluency / prosody. Kaldi GOP baseline included | ⚠️ licence not stated on README, 191★ | A ready-made, research-validated shape for a machine-scored playing-test rubric. See §4.5 | **steal the rubric** |
| 40 | `Voice-Lab/VoiceLab` | Clinical/reproducible voice analysis with a GUI for non-programmers: jitter, shimmer, HNR, cepstral peak prominence, formants, intensity, subharmonics, spectral tilt, LTAS. Standalone builds for Win/macOS/Ubuntu | MIT, 167★ | Tone-steadiness and long-tone quality metrics that are *not* pitch accuracy. Jitter/shimmer/HNR is what "wobbly tone" actually is | **steal** |
| 41 | `YannickJadoul/Parselmouth` | Praat's algorithms as a Python library | GPL-3.0, 1.3k★ | The engine under #40 if we want it in-process | **read** |
| 42 | `UltraStar-Deluxe/USDX` | Open-source karaoke game; scores "depending on the pitch of the voice and the rhythm of singing" against a reference note track, in real time, on low-end consumer hardware since 2007 | GPL-2.0, 1.2k★, Pascal | Two decades of shipped experience at scoring pitch+rhythm against a reference in real time. ⚠️ README gives no algorithmic detail — the value is in reading the source | **read** |
| 43 | `google-research/perch` | Bioacoustic embeddings + "Agile Modeling": search embeddings, active-learn, build a classifier for a novel concept from a handful of labels | Apache-2.0, 375★ | Few-shot detectors for *this program's* recurring problems ("that entrance", "that articulation") without training a model per school. GPU recommended — a real cost | **read** |
| 44 | `pykt-team/pykt-toolkit` / `bigdata-ustc/EduKTM` / `jilljenn/ktm` | Deep knowledge tracing zoos: DKT, DKT+, DKVMN, SAKT, SAINT, AKT, GKT, LPKT, DTransformer, stableKT (pykt, MIT, 423★; EduKTM Apache-2.0, 262★, no BKT). `ktm` (140★) is Knowledge Tracing Machines — factorisation machines, interpretable, not deep; ⚠️ licence unverified | mixed | The answer to "what else is out there besides BKT". Honest verdict below | **read only** |
| 45 | `ornicar/lichess-puzzler` | Chess puzzle generation + validation from a game database with Stockfish; puzzles get a rating and topic tags at review time | AGPL-3.0, 174★ | Item difficulty as an **earned rating** rather than an authored label. ⚠️ The live rating-from-play machinery is in `lila`, not here — I verified only that this repo assigns an initial rating and topic tags | **steal the idea** |
| 46 | `duolingo/halflife-regression` | Half-life regression: estimates the half-life of an item in a learner's memory from a learning trace | MIT, 574★ | Historical interest — the bridge between BKT and FSRS. 6 commits; do not depend on it | **read** |
| 47 | `jcdevaney/AMPACT` | Automatic Music Performance Analysis and Comparison Toolkit — score-informed extraction of performance parameters. The academic ancestor of everything in Tier 1 | ISC, 46★, **MATLAB, last push 2021-07-15** | Read the papers, take the parameter vocabulary. No Python port found | **read only** |
| 48 | `meditohq/medito-app` | Meditation app, *"free, forever: no ads, no spam, no need to sign up or pay"*. No streaks, gamification, subscription or analytics machinery visible | AGPL-3.0, 1.3k★, Dart | An existence proof that a daily-practice app can ship with no engagement mechanics at all | **read** |
| 49 | `dsacre/klick` | Advanced JACK metronome, CLI | GPL-2.0, 27★, **activity 2007–2013** | Dormant. Named only so nobody rediscovers it and thinks it is maintained | **read only** |

---

## 2. Negative findings — the boring primitives are genuinely unbuilt

These are the most decision-relevant results in the slice, and they are all derived from searches run against
the GitHub index today, not from prose:

- **There is no serious open-source instrument tuner.** `tuner in:name topic:music` returns 40 repos. The
  largest is `jpsim/ZenTuner` (573★, Swift, iOS/macOS only, AudioKit-based); the rest are 4–185★ guitar
  tuners in six different languages. **Nothing in the index does instrument-specific tuning-tendency work** —
  no per-instrument deviation profile, no "your third-space C is +14 cents flat" for a trumpet, which is the
  thing a band director actually wants and the thing Tonal Energy sells.
- **There is no open-source scale/rudiment/etude check-off tree.** `rudiments snare drum practice
  in:name,description` → **0 results**. All-state requirement tracking: nothing.
- **There is no open-source music practice log worth adopting.** `practice log musician journal
  in:name,description` → **2 repos, both 0★, both created in 2026**. One of them (`tomd0627/tempo`)
  advertises that it "surfaces streaks, totals, and instrument breakdowns" — i.e. the newest entrant in the
  space went straight for the mechanic UTETY's ground rule 2 forbids.
- **Sight-reading generation is a toy space.** `sight-reading in:name` → 171 repos; the top result has 26★
  and the rest are single-digit. The generation problem is real but nobody has solved it in the open; the
  raw materials (`music21`, `abjad`, `verovio`) are excellent and the item-generation layer does not exist.
- **AMPACT has no Python port** in the index. The one toolkit explicitly built for score-informed analysis of
  student performances is MATLAB and last saw a push in July 2021.

The shape of §1 that this implies: **the analysis engines are solved and the practice-room furniture is not.**
Tier 1 is largely a matter of wiring together well-licensed research code. Tiers 2–3 of the capability map's
"Assigned and structured practice" bullet list — the tuner, the drone, the tendency profile, the check-off
tree, the requirement tracker — have to be written here, and they are also the cheapest things in the
document. That is an unusually favourable cost profile and it argues for building the boring parts first.

---

## 3. The surveillance-versus-visibility design question

The capability map already has the right instinct (`ask-jeles`: record the shape, never the content;
off by default; not persisted) and the right caution (retention must be decided at the same moment as
consent, or a session-scoped grant leaks into a replicated git history). What the open-source world adds is
**three concrete mechanisms and one reframing**, plus one invariant conflict this project has not yet named.

### 3.1 Sense the shape on-device; never let the recording become the record

`silero-vad` (#10) is the existence proof that the sensing tier can be trivially cheap: a **2MB** model at
**<1ms per chunk on a single CPU thread**, MIT for both code and weights, real-time via ONNX. A VAD is a
detector for "is there voice here"; an instrument-activity detector is the same architecture with different
training data, and `opensoundscape`'s RIBBIT (#35) shows the non-learned version — detect *periodicity* —
which is what a long tone, a scale, and a rudiment all are.

The design consequence is the important part. If the detector runs on the student's device and emits
`{date, minutes_of_sound, tempo_band, passage_id}` while the audio buffer is discarded, then **there is no
recording of a minor to protect**, and the §6 problem the architecture worries about at line 304 (a
`MEDIA_MINOR` task sharing the host netns) never arises for the logging path at all. The audio never becomes
a `MEDIA_MINOR` artifact because it is never persisted. Compare that with the alternative everyone builds:
upload the recording, analyse it server-side, and now guardian visibility and student privacy are in direct
conflict forever.

`Olaf` (#34) extends this to *verification without content*: fingerprint match proves the assigned excerpt
was the thing played, while what is stored is a fingerprint, not audio. It runs on ESP32 and in the browser
via WASM. This is the mechanism that lets the system say "the assigned passage was practised" without ever
holding evidence of *how badly*.

### 3.2 Represent progress with a decaying average, not a chain

`uhabits` (#38) states the rule in one sentence: *"A few missed days after a long streak, however, will not
completely destroy your progress, unlike many other don't-break-the-chain apps."* A streak is a cliff
function — it converts one missed day into total loss, which is exactly the coercion the project is wary of,
and it punishes the student whose Tuesday was consumed by a 504 pull-out or a shift at a job. An exponentially
weighted strength score is forgiving by construction, and it is not a leaderboard because it is not
comparable: it is a statement about one student's own trajectory.

`ebisu` (#12) is the mathematically principled version, and it is the single best find in this slice for §1.
Its distinguishing property is that it **models recall probability as a posterior rather than scheduling a due
date**, so it "gracefully accommodates over- or under-reviewing". Translated into practice terms: a student
who practised nothing for nine days and then did ninety minutes is not *penalised*; the model simply has a
wider posterior and says so. Irregular timing becomes *information*, not *failure*. And it is
**public domain** (Unlicense), so there is no licence conversation at all.

### 3.3 Reframe the log from compliance evidence to a health instrument

This is the reframing, and it comes from cycling. `GoldenCheetah` (#36) implements Banister
impulse-response and the Performance Manager Chart: a decaying acute load, a decaying chronic load, and the
difference between them. Athletes do not use these to prove to a coach that they trained; they use them to
avoid injury. Musicians have a direct analogue — playing-related musculoskeletal disorders and embouchure
overuse are real, and a 240-minute Saturday after a week of nothing is exactly the pattern that causes them.

If the practice log's primary rendering is *load and recovery* rather than *minutes versus quota*, then the
guardian view answers a different question — "is my child overdoing it or drifting" — and the same numbers
stop functioning as an accusation. **The audience changes what the artifact is.** That is a cheaper and more
durable fix than any permission gate, because it removes the incentive to surveil rather than blocking it.

### 3.4 What the shape schema should and should not contain

Recordable (the work): date bucket, minutes of detected sound production, passage or item identifier,
tempo band attempted, whether a click was used, loop-repetition count, student's own self-rating and session
note, and a dated disposition on any assignment (CLAUDE.md #15).

Refused (the person, or the content): the audio itself; any transcript of it; a pitch- or rhythm-error trace
retained beyond the session that produced it; time-of-day precision finer than a date bucket (which reveals
household routine, and is the difference between a practice log and a movement log); location; any
cross-student comparison; any ranking.

Two derived rules follow from CLAUDE.md and are worth writing into the schema, not the prose:

- **Derived artifacts inherit both the classification and the retention of their source.** §8.2's rule that a
  transcript inherits its audio's classification is stated in the architecture; the retention half is not.
  A pitch-error trace derived from a `MEDIA_MINOR` recording must not outlive the recording, or the session-scoped
  grant has leaked again in a new shape.
- **A failed sensor surfaces as `unknown`, never as zero** (CLAUDE.md #13). A `0 minutes` that actually means
  "the detector did not load" is a false accusation against a child, delivered to a guardian, with a number
  attached. This needs a mutation test that breaks the detector and asserts the guardian view reads
  "unavailable" (CLAUDE.md #19).

### 3.5 The conflict this project has not yet named: a mastery estimate *is* a standing score

CLAUDE.md #4 forbids "no durable rating of a judge, clinician, student, or staff member carried between events
or contexts" — prohibited scope `SA-3`, invalid even signed by root. **A BKT posterior is a durable numeric
rating of a student that persists across events by design.** That is the entire point of knowledge tracing.
UTETY already holds one in-house, so the fleet has already crossed this line once, in a different subject area.

I do not think this is fatal, but it has to be decided explicitly rather than discovered later:

- Scope the estimate to a **skill and a context** (this scale, this requirement list, this season), never to
  the student as a general quantity. "Mastery of the B-flat concert scale" is about the work; "musicianship
  score" is a standing rating of a person and is `SA-3`.
- Give it an **`invalid_at`**, not a delete (CLAUDE.md #3), and let it expire at season boundaries.
- Make it **structurally non-comparable**: if the store can answer "sort the roster by mastery", CLAUDE.md #6
  has already been violated, because chair placement is exactly what someone will use it for. The strongest
  form of this — and the pattern the architecture already praises in UTETY's `knowledge.py` — is to make the
  comparison *unrepresentable* rather than gated: no query takes two student identifiers.
- **`ebisu`'s posterior is a better fit than a point estimate** for this, precisely because it carries its own
  uncertainty. A wide posterior is hard to misuse as a ranking; a single number invites it.

---

## 4. Weirdest things I found

### 4.1 Acoustic fingerprinting from music-identification research, as content-free proof of practice
`JorenSix/Olaf` (AGPL-3.0, 408★) exists to answer "what song is this" on an ESP32. Inverted, it answers a
question §1 needs and nobody has framed this way: *did the student practise the assigned excerpt?* — while
storing a fingerprint rather than audio, and running in the browser via WASM so the audio never leaves the
device. It turns "assigned passage compliance" from a surveillance feature into a hash comparison. The
transplant cost is real (fingerprinting is tuned for identifying identical recordings, not for matching a
beginner's rendition of a passage to a reference, so this likely needs the *idea* rather than the code), but
the framing alone reshapes the logging design. AGPL is a genuine consideration for the client tier.

### 4.2 A frog-call detector as a long-tone and rudiment analyser
`opensoundscape`'s RIBBIT algorithm (MIT, 218★) detects sounds that are *periodic* in amplitude, because
that is what frog and insect calls are. A long tone is a sustained sound whose amplitude should be
*aperiodic and flat*; a rudiment is a sound whose amplitude periodicity **is** the exercise. A detector built
for chorusing frogs is a startlingly direct fit for "was that sixteen even strokes or fourteen and a stumble",
it requires no model weights at all, and it runs on CPU. Bioacoustics is also the only field I found that
routinely does the exact thing this project needs — recognise a specific sound event in a long unsupervised
recording on cheap hardware in the field, with no cloud.

### 4.3 Cycling's Performance Manager Chart as the practice card
Covered in §3.3. The weird part is not the mathematics (Banister 1975, well documented in GoldenCheetah,
GPL-2.0) but that endurance sport solved the *social* problem this project is stuck on twenty years ago, and
solved it by changing who the chart is for. A training-load chart is not experienced as surveillance even
though it is a far more granular record than a practice minute count, because its purpose is the athlete's
own safety. Musicians have the same injury exposure and none of the tooling.

### 4.4 A typing tutor as the scale check-off tree
`keybr.com` (AGPL-3.0, 4.6k★) "tracks every single keystroke and computes statistics for each individual key",
generates lessons targeting the weakest keys, and gates new material on measured performance: *"More letters
are added once you reach the target speed with the current ones."* Substitute *note* for *key* and *scale* for
*letter* and that is an all-state requirement tracker that nobody has to check off by hand — and, notably, a
progression model with no streak and no comparison to other typists. It is the closest thing I found to a
working mastery-gated curriculum in any domain, and it is a typing website.

### 4.5 A language-learning pronunciation corpus as a playing-test rubric
`speechocean762` (191★) ships a human-annotated rubric with a structure §2 wants and has not specified:
phone-level goodness 0–2, word-level accuracy 0–10 plus a separate stress score, sentence-level accuracy /
completeness / fluency / prosody — with a Kaldi Goodness-of-Pronunciation baseline. That is a
research-validated decomposition of "how well did they say it" into sub-scores at three granularities, with
prosody separated from accuracy, and it maps almost one-to-one onto note / phrase / performance with rhythm
separated from pitch. Computer-assisted language learning has been peer-reviewing this rubric design for two
decades while music education has been using 1-to-5 holistic scales. The corpus licence is not stated on the
README, so **take the rubric structure, not the data**.

*(Runner-up, worth a line: `UltraStar-Deluxe/USDX` — a GPL-2.0 karaoke game from 2007 that has been scoring
pitch and rhythm against a reference note track in real time on low-end hardware for nearly twenty years.
It is the most battle-tested pitch-scoring loop in open source and nobody in music education cites it.)*

---

## 5. Concrete transplants and costs, for the top finds

**`parangonar` + `partitura` + `matchmaker` (all Apache-2.0) — the flagship loop's spine.**
Transplant: `partitura` parses the MusicXML/MEI score into a note array; `parangonar` aligns the performance
(audio or MIDI) to it and yields note-level correspondences; measure 112 becomes an addressable range of
sample offsets in every recording of that chart, in every year. That single capability is what makes "the
judge's comment, the passage, and the audio the judge was reacting to" a database join rather than a research
project — and it is also longitudinal self-comparison for free, because two performances aligned to the same
score are aligned to each other. `matchmaker` adds the real-time direction (OLTW, HMM, switching Kalman),
which is what a play-along that follows the student requires.
Cost: **the score must be machine-readable.** This is §14's own open question and it is the real bill —
MusicXML for marching arrangements and custom charts largely does not exist, so the fallback is the judge's
tap-to-mark control the architecture already proposes at line 709. These libraries are small-team academic
code (62, 367 and 71 stars); expect to read the source, pin versions, and own bug fixes. Three Apache-2.0
dependencies from two labs is a modest surface, and there is no non-commercial trap anywhere in it.

**`basic-pitch` (Apache-2.0, code and weights) — the analysis engine that clears the licence bar.**
Transplant: submitted recording → note events with pitch bend → compare against the `partitura` note array →
per-note pitch error in cents, onset error in ms, and missing/extra notes. Report through `mir_eval`'s
peer-reviewed metric definitions rather than an invented score.
Cost: it is polyphonic and general, which means it is less accurate on a single wind instrument than a
dedicated monophonic tracker; pair it with `pesto` or `penn` for monophonic submissions. Ships TFLite and ONNX
so the hub needs no GPU and no CUDA. **This is the one to build on**, because Apache-2.0 covers the weights —
which is precisely what madmom, BirdNET, openSMILE and (unverified) Essentia do not give us.

**`pesto` (LGPL-3.0) — the on-device pitch engine.**
Transplant: the tuner, the drone-and-tendency tool, and the intonation trace on a student's own laptop.
The claim that matters: **~12× faster than real time on CPU** for monophonic pitch, against CREPE's ~12
minutes for the same file. That is the difference between analysis-on-device and analysis-on-the-hub, and
analysis-on-device is the difference between needing a `MEDIA_MINOR` upload path and not needing one.
Cost: LGPL-3.0 means dynamic linking discipline and a licence conversation if it is ever statically bundled
into a mobile client. `penn` (MIT, weights included) is the fallback if that is unacceptable; `TarsosDSP`
(GPL-3.0, pure Java, YIN + MPM + WSOLA) is the fallback for Android specifically and buys the tuner, the
drone, and the slow-downer in one dependency.

**`ebisu` (public domain) — mastery without coercion.**
Transplant: one Beta posterior per (student, item) pair where item is a scale, rudiment, etude, or theory
concept. Query is "P(recall) right now", which drives what the practice queue offers next. No due dates, no
streaks, no penalty for irregular practice, no cross-student quantity.
Cost: essentially zero — a few hundred lines, no dependencies, public domain, and ports already exist in JS,
Java and Dart if the client is not Python. Compare against UTETY's in-house BKT on the same item set before
choosing; the honest expectation is that they perform similarly and `ebisu` wins on the *social* properties
(uncertainty-carrying, timing-agnostic) rather than on accuracy.

**`silero-vad` + a decaying strength score — the practice log.**
Transplant: on-device detector emits minutes-of-sound per date bucket; store the shape, discard the audio;
render as a `uhabits`-style strength curve and a GoldenCheetah-style load/recovery pair; guardian sees the
curve, never a recording, never a ranking, and reads "unavailable" when the detector failed.
Cost: silero-vad is trained on speech and will need either retraining for instruments (its architecture is
tiny, so this is tractable) or replacement with RIBBIT-style periodicity detection, which needs no training at
all. Budget the *policy* work, not the ML: the schema in §3.4 and the `SA-3` decision in §3.5 are the
expensive parts, and both are decisions rather than code.

**On deep knowledge tracing (`pykt`, `EduKTM`, DKT/SAKT/AKT/SAINT) — my recommendation is don't.**
There are at least 61 repos in the `knowledge-tracing` topic and the field is active, but for this project
they are all read-only interest. They need GPUs and large interaction logs to beat BKT; they produce
uninterpretable per-student embeddings, which is the worst possible artifact to hold about a minor under
CLAUDE.md #4 and the least explicable to a guardian exercising a records-inspection right; and a music
program's interaction volume is orders of magnitude below what these models need. `jilljenn/ktm`
(Knowledge Tracing Machines, factorisation machines, interpretable, non-deep) is the only one I would read
with intent — its licence is unverified. **Keep BKT or `ebisu`. Interpretability is a privacy feature here,
not a nice-to-have.**

---

## 6. Claims to check before anyone builds on this

1. **Essentia's pretrained-model licences.** `essentia.upf.edu/models.html` and `/licensing_information.html`
   both returned 403 to this session; the README and `machine_learning.rst` say nothing. Unknown, not AGPL-only.
   Blocking if Essentia is on the shortlist.
2. **Verovio's stable element IDs.** The reason to choose it over alternatives; not confirmed from the README.
3. **MFA pretrained acoustic model licences** — separate repo, no licence stated where I looked.
4. **`speechocean762` corpus licence** and **`jilljenn/ktm` licence** — not stated on the pages I fetched.
5. **`AudioKit`'s `PitchTap`** — asserted widely, not confirmed on the README.
6. Last-commit dates: GitHub's markdown rendering dropped the file-list commit timestamp on most fetches, so
   "activity" above is grounded in stars, CI status, and explicit archive/date statements. Dormancy is
   asserted only where the page said so (`klick` 2007–2013, `AMPACT` pushed 2021-07-15, `demucs` archived
   2025-01-01, `basic-pitch` pushed 2025-11-13).
