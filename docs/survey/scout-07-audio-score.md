# Scout 07 — Local audio pipeline and score-position anchoring

Scope: §8.1 (commentary primitive), §8.2 (local-only processing), §13 / §18 item 7 (stored-score
alignment vs tap-to-mark). Target pipeline: ingest judge audio + performance audio → align →
diarize → transcribe → **anchor to score position** → index.

## Method, and what I could not verify

Every repo below was opened on github.com and its license, star count, and where possible its
latest commit date read from the page or from `raw.githubusercontent.com`. Two limits, stated
plainly because §14 item 0 exists:

- **`huggingface.co` is unreachable from this session** (proxy denies CONNECT). Every model-weights
  license marked *(reported)* comes from a secondary source, not the model card. Those are `P2 Cited`
  claims in §15 terms and need one verification pass before anything is built on them. They are
  flagged individually.
- WebSearch budget ran out mid-scout; the second half of discovery was done via GitHub's own
  repository search, which finds repos but not papers. Two accuracy figures below (bootleg-score
  97.3%, Parakeet throughput) come from paper abstracts / secondary write-ups, not from running code.

No figure in this document is derived from running anything. Treat all of it as a claim to check.

---

## Ranked table

| # | Project | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | **jltr-alignment** (`irmakbky/jltr-alignment`) | Audio ↔ *sheet-music scans* alignment where the human labels only the repeats/jumps. ISMIR 2024. | MIT | 7★, 2024 | The anchor. §8.1 | **steal-the-idea** (workflow), read the code |
| 2 | **sheet-midi-sync** / bootleg score (`ttanprasert/sheet-midi-sync`) | Aligns scanned score images to MIDI by reducing both to notehead blobs. **No OMR.** 97.3% @1s on 68 scanned piano scores *(reported)*. | not verified | 2019 paper repo | The anchor, without a machine-readable library | **steal-the-idea** |
| 3 | **synctoolbox** (`groupmm/synctoolbox`) | Reference DTW music-sync toolbox: MsDTW, memory-restricted MrMsDTW, chroma+DLNCO features. Audio↔audio *and* audio↔score notebooks. | **MIT** | 138★, commits May 2026 | align step, both routes | **adopt** |
| 4 | **partitura** (`CPJKU/partitura`) | Symbolic music I/O: MusicXML / MEI / Kern / MIDI in; exposes measure numbers, `beat_map`, and synthesises score→audio (FluidSynth). | **Apache-2.0** | 367★, active | measure/beat addressing; score→audio for DTW | **adopt** |
| 5 | **verovio** (`rism-digital/verovio`) | MEI engraver with `RenderToTimemap()` / `GetTimesForElement()` (verified in `include/vrv/toolkit.h`), C++/WASM/Python/Java bindings. | LGPL-3.0 **+ GPL-3.0 dual** | 903★, active | measure↔time↔`xml:id` map; the judge-facing scrub UI | **adopt** (LGPL path only) |
| 6 | **sherpa-onnx** (`k2-fsa/sherpa-onnx`) | One native ONNX binary doing offline ASR **and** speaker diarization with no Python, no PyTorch, no GPU, no internet. Runs on Cortex-A7 / RPi / RISC-V. | **Apache-2.0** | 13.9k★, very active | transcribe + diarize, §8.2 | **adopt** — this is the Zone A engine |
| 7 | **audalign** (`benfmiller/audalign`) | "Align multiple recordings of the same event." Four recognisers: fingerprint, cross-correlation, correlation-spectrogram, visual. | **MIT** | 148★, commit May 2026 | judge tape ↔ performance recording | **adopt** |
| 8 | **linmdtw** (`ctralie/linmdtw`) | Linear-memory, parallel, optionally-CUDA DTW built and benchmarked *specifically on orchestral recording pairs*. | **Apache-2.0** | 62★, active | long-recording audio↔audio | **adopt** (fallback for full-show length) |
| 9 | **libltc** (`x42/libltc`) | Encode/decode SMPTE LTC as an audio signal. | LGPL-3.0 | 246★, active | makes audio↔audio alignment a lookup, not an inference | **adopt** if you control capture |
| 10 | **peaks.js** (`bbc/peaks.js`) + `audiowaveform` | BBC's browser waveform component with first-class **point markers and segments**; precomputed waveform data files. | LGPL-3.0 | 3.4k★ (dev moved to Codeberg) | the tap-to-mark + scrub-to-comment surface | **adopt** |
| 11 | **footswitch** (`rgerganov/footswitch`) | 400 lines of C that program a $25 USB foot pedal to emit keystrokes, on Linux, via udev, no vendor software. | **MIT** | 488★ | the tap-to-mark *control* | **adopt** |
| 12 | **matchmaker** (`pymatchmaker/matchmaker`) | The only maintained score-following library. Real-time + offline sim mode, MusicXML/MIDI, built on partitura. **Piano-only evaluation** ((n)ASAP, Batik, Vienna4x22). | **Apache-2.0** | 71★, commit **2026-07-23** | align step, stored-score route | **adopt with eyes open** — untested on ensembles |
| 13 | **whisper.cpp** (`ggml-org`) | MIT weights + MIT code, CPU-first, no runtime deps. | **MIT** (verified LICENSE) | huge, active | transcribe | **adopt** as the conservative default |
| 14 | **pyannote.audio** | Best-known diarizer. Code MIT; `community-1` weights **CC-BY-4.0** *(reported)*, gated behind an HF token. v4 also ships a `precision-2` path that **sends audio to pyannoteAI servers**. | MIT code / CC-BY-4.0 weights | active | diarize | **adopt only with the cloud path disabled and tested** — see flags |
| 15 | **whisper-diarization** (`MahmoudAshraf97`) | Whisper + NeMo TitaNet/MarbleNet + ctc-forced-aligner + Demucs, word-level speakers. | BSD-2-Clause | 5.6k★ | reference pipeline shape | **steal-the-idea**; its parallel mode wants ≥10 GB VRAM — do not adopt that path |
| 16 | **NVIDIA Parakeet TDT / NeMo** | NeMo code Apache-2.0 (verified). Parakeet TDT 0.6B weights **CC-BY-4.0** *(reported, unverified)*; ~30× realtime int8 CPU vs whisper-small ~8× *(reported)*. | Apache-2.0 / CC-BY-4.0? | very active | transcribe, if CPU budget is tight | **adopt after verifying the model card** |
| 17 | **Audiveris** | The mature OMR. MusicXML 4.0 out, editor for the errors it cannot avoid; README: *"a 100% recognition ratio is simply out of reach in many cases."* | **AGPL-3.0** | 2.7k★, release every 6–12 mo | legacy library digitisation only | **adopt, out-of-process, Phase C** |
| 18 | **homr** (`liebharc/homr`) | UNet segmentation (from oemer) → TrOMR transformer → MusicXML. **Detects barlines as a distinct segmentation output.** CPU-capable. | **AGPL-3.0** | 341★, commit **2026-07-29** | *barline map only* — see recommendation | **steal-the-idea** (stage 1 only) |
| 19 | **oemer** (`BreezeWhite/oemer`) | End-to-end OMR, ONNX, CPU-capable. README: *"will probably not work on transcribing hand-written scores."* | **MIT** | 779★ | printed-part digitisation | **adopt** where MIT matters more than accuracy |
| 20 | **Sheet Music Transformer** (`antoniorv6/SMT`) | Full-page polyphonic img2seq OMR. CER 3.9% GrandStaff-ideal / 5.3% GrandStaff-camera / 1.3% string quartets. **Printed only.** | **MIT** (weights stated same) | 80★ | the only published OMR error rates worth citing | **read-only-interest** (nearest thing to a number) |
| 21 | **olimpic-icdar24** (`ufal/`) | LMX (linearised MusicXML) + Zeus img2seq model + synthetic *and scanned* pianoform dataset. | MIT code / **CC BY-SA** data+model | 32★, 2024 | LMX is a good ML-friendly score serialisation | read-only-interest |
| 22 | **aeneas** (`readbeyond/aeneas`) | Text↔audio forced alignment with **no language model**: eSpeak-synthesise the text, then MFCC+DTW. Outputs EAF, TextGrid, VTT, SMIL, +8 more. | **AGPL-3.0** | 2.9k★, **dead since v1.7.3, Mar 2017** | the synthesise-then-DTW trick; the export vocabulary | **steal-the-idea** |
| 23 | **Montreal Forced Aligner** | Kaldi-based forced alignment, TextGrid out. | MIT (models separate, unverified) | 1.9k★, active | word-level anchoring *within* a sealed transcript | adopt later (enables scrub-to-word) |
| 24 | **ffsubsync** (`smacke/ffsubsync`) | Syncs subtitles to video by aligning **binary VAD streams** with an FFT offset search. 20–30 s per file. | **MIT** | 7.8k★ | audio↔audio alignment when features are hostile | **steal-the-idea** |
| 25 | **Panako** (`JorenSix/Panako`) | Granular acoustic fingerprinting **robust to ±10% time-scale and pitch drift**, built for ethnomusicology archives with speed-wrong digitisations. LMDB, local. | **AGPL-3.0** | 260★, last release 2022 | matching a drifting analog judge tape to a performance | **steal-the-idea** / read-only |
| 26 | **match-vamp** (`c4dm/match-vamp`) | Dixon & Widmer's MATCH audio-alignment algorithm as a Vamp plugin; batchable via Sonic Annotator. | GPL-2.0 | 2★, 2020 | audio↔audio baseline, 20 years of field use | read-only-interest |
| 27 | **ELAN / EAF** (MPI) + `pympi`, Praat TextGrid | GPLv3 desktop multi-tier time-aligned annotation with **hierarchical tiers**; EAF is a CLARIN-registered XML standard. | GPL-3.0 | maintained by MPI | interchange + **the §11.1 exit line** | **adopt as export format** |
| 28 | **Plover** (`openstenoproject/plover`) | Open-source stenography engine, >200 wpm, offline. | GPLv2+ | 2.6k★ | the court-record precedent, and a real accessibility option | read-only-interest |
| 29 | **cobalt / Akoma Ntoso** (`laws-africa/cobalt`) | Python lib for the OASIS legislative-XML standard, whose whole point is stable hierarchical `eId` addresses into a document. | Apache-ish (verify) | 26★ | how to name a position so a citation survives re-typesetting | **steal-the-idea** |
| 30 | **BirdNET-Analyzer** | MIT code, **CC BY-NC-SA 4.0 model weights** with a vendor carve-out. Runs a CNN over thousands of hours by chunking. | MIT / **CC BY-NC-SA** | 1.7k★ | the weights-license cautionary tale; batch-chunking pattern | **read-only-interest, cite as a flag** |
| 31 | `ahwitz/score-following` | *"Master's Thesis — Large Ensemble Score Alignment."* JavaScript, 4★, last touched **2016**. | — | dead | the entire published state of large-ensemble score following | read-only-interest, and a finding in itself |
| 32 | **Reverb** (`revdotcom/reverb`) | Rev's ASR + diarization inference code. README: *"the license in this repository applies only to the code not the models."* Model licence not stated in-repo. | Apache-2.0 code / **weights unknown** | 436★ | — | **disqualified until someone reads the model card** |

---

## Top finds, with the transplant and the cost

### 1. Bootleg score + "Just Label the Repeats" — the anchor without a machine-readable library

This is the most important thing in the report because it dissolves §18 item 7's premise. The 2019
bootleg-score work (Tanprasert, Jenrungrot, Müller, Tsai) aligns *scanned sheet-music images* to a
MIDI/audio rendition by throwing away almost everything: project the MIDI into pixel space as
rectangular notehead blobs, run a notehead detector on the scan, fill in the same blobs, and DTW the
two blob images. Reported 97.3% accuracy at a 1-second tolerance on 68 real scanned IMSLP piano
scores — **beating OMR-based baselines**. The 2024 follow-up (`jltr-alignment`, MIT) adds the piece
that matters operationally: the dominant failure mode of in-the-wild alignment is *jumps* — repeats,
D.S., cuts — so give a human a small UI and have them click the repeat signs, once, per piece.

**Transplant.** The anchor does not need the score to be *understood*; it needs the score to be
*ordered*. A marching show has cuts, tags, and repeats in abundance, and a band already maintains a
human-authored jump list — the cut sheet the arranger hands out. That artifact *is* the JLTR
annotation. Build the anchor around "ordered barline positions + a human-labelled jump list" and you
never need trustworthy pitch recognition.

**Cost.** The two repos are research code (7★ and a 2019 paper repo, license unverified on the
latter); this is a *read-the-method-and-reimplement* transplant, not a dependency. Estimate: the
notehead-blob path is a week of work on top of oemer/homr's existing segmentation stage; the
repeat-labelling UI is a peaks.js/verovio page and a day. Cheap relative to what it replaces.

### 2. sherpa-onnx — the whole local speech half, in one Apache-2.0 binary

`k2-fsa/sherpa-onnx` (13.9k★, Apache-2.0, very active) does offline ASR *and* offline speaker
diarization from a single native ONNX Runtime binary — no Python, no PyTorch, no GPU, explicitly
"without Internet connection," with builds down to Cortex-A7 and 14M-parameter models. It hosts
Whisper, Zipformer, SenseVoice, Moonshine, NeMo transducers, CAM++ speaker embeddings, and the
ONNX-exported pyannote segmentation model. There are twelve language bindings.

**Transplant.** This is the §8.2 engine. Because it is one process with no network stack of its own,
it is trivially wrappable in `kartikeya`'s bubblewrap sandbox with `allow_localhost` off entirely —
which directly addresses §14's open row *"Network-isolated local inference — `allow_localhost` shares
the host netns."* A Python inference stack cannot make that promise as cleanly.

**Cost.** Near zero for the code. The real cost is model curation: each model artifact arrives with
its own license, and sherpa-onnx's model zoo is a mix. Budget the install-acceptance work, not the
integration work.

### 3. `audalign` + `libltc` — the two-captures-of-one-event problem is solved, twice

`audalign` (MIT, 148★, commits May 2026) exists for exactly the stated problem: "process and align
multiple recordings of the same event," with four independent recognisers so you can escalate —
fingerprint first (fast, coarse), then cross-correlation (its README calls it "more precise than
fingerprints"). `linmdtw` (Apache-2.0) is the fallback for full-show lengths, since it was built and
benchmarked on orchestral recording *pairs* with linear rather than quadratic memory.

But the better answer is to not infer the offset at all. `libltc` (LGPL-3.0, 246★) encodes and
decodes SMPTE linear timecode as an audio signal. Print LTC onto a spare channel of both the judge
rig and the performance rig and the alignment becomes a subtraction. Film post has done this for
forty years; MIR treats it as a research problem because MIR does not control the capture. **Terpsi
does control the capture** — it is a school buying recorders.

**Cost.** `audalign` is a pip install and an afternoon. LTC is a hardware and procedure decision:
one channel per recorder, a jam-sync habit at call time, and a fallback to `audalign` for the judge
who brought their own gear. Budget the *training*, not the code.

### 4. peaks.js + a $25 foot pedal — tap-to-mark is a solved UI, not a feature to invent

`bbc/peaks.js` (LGPL-3.0, 3.4k★) is the BBC's waveform component, with **point markers and segments
as first-class objects** and a companion `audiowaveform` that precomputes waveform data so a
40-minute file scrubs instantly in a browser. `rgerganov/footswitch` (MIT, 488★, C) programs
PCsensor/Scythe USB pedals to emit keystrokes on Linux via udev with no vendor software. Bluetooth
page-turner pedals (the kind marching judges already own for tablet sheet music) present as HID
keyboards and need no driver at all.

**Transplant.** peaks.js is the scrub-to-comment surface of §8.1 ("scrub to a comment and hear the
ensemble at that instant") and simultaneously the repeat-labelling UI for JLTR and the sealing UI for
§8.2's grace period — three requirements, one component. The pedal is the anchor input for a judge
whose hands hold a clipboard and a microphone.

**Cost.** LGPL-3.0 on a browser component: fine if you don't fork it, but note upstream development
moved to Codeberg, so pin a version and record where you got it. Total integration: days.

### 5. ELAN / EAF and Praat TextGrid — the exit line, already standardised

ELAN (GPL-3.0, Max Planck Institute) is a twenty-year-old offline desktop tool for multi-tier,
time-aligned annotation of audio and video, with **hierarchically interconnected tiers** and a
CLARIN-registered XML format (EAF). `pympi` reads and writes it in Python. `aeneas` already exports
it. Linguists built it for precisely "many annotators, many layers, one recording, no internet."

**Transplant.** Two uses. (a) A tier hierarchy is the natural encoding of `addresses → [Ensemble |
Section | Part | Individual]` — parent tier per judge, child tiers per caption, referring annotations
for section-scoped remarks. (b) §18 item 5 says **the exit line is unwritten**. WAV + EAF + TextGrid
+ MusicXML is a complete, standardised, tool-supported exit format for the commentary corpus, and it
comes with a free desktop reader for the program that leaves. Writing that exporter closes an open
blocking-adjacent item for maybe two days of work.

**Cost.** EAF has no notion of score position, so measures ride in tier names or annotation values —
lossy, but an exit format is allowed to be lossy if the tombstone says so (§16, rule 20).

---

## Recommendation on stored-score vs tap-to-mark

**Tap-to-mark first and unconditionally. Stored-score alignment second, as a refinement that a tap
constrains, never as the primary anchor. OMR of the legacy library third, separable, and possibly
never.** The schema should make this ordering invisible to callers.

The reasoning, in the order that decided it:

**a. There is no maintained large-ensemble score follower in open source.** I looked hard. Every
maintained implementation — `matchmaker` (the only real library, and it is active as of a week ago),
`synctoolbox`'s worked examples, the (n)ASAP / Batik / Vienna4x22 evaluation sets — is piano, or
Schubert songs and a Chopin prelude. The single repo whose description says "Large Ensemble Score
Alignment" is a 4-star JavaScript master's thesis last touched in 2016. A 60-piece wind band
outdoors, wind-screened mic, PA bleed, crowd noise, and a drumline whose transients dominate the
onset features is the *adversarial* case for chroma-based DTW, and nobody has published a number on
it. Making stored-score alignment the primary anchor bets the whole value of §8.1 on unbenchmarked
ground.

**b. A tap is a record; an alignment is an inference.** This is the argument that should actually
settle it, because it is a trust argument and this project is organised around trust states. A judge
pressing a pedal produces `(wall_clock, judge_id, event_seq)` — a first-party observation by a named
human, `P1`-grade provenance, and it is *never* a `draft` in §8.2's sense. An alignment produces a
guess, at best `Estimated`, and it must carry the `draft`/`pending` cascade and the `reject_match`
affordance. §8.2 already says the common adjudication error is *"this correct remark is attached to
the wrong passage"* — that error is *created by* automatic alignment. Tap-to-mark does not have that
failure mode. Building the inference path first means the system's most sensitive artifact starts
life at the lowest available trust grade, and §8.2's whole point is that it should not.

**c. The machine-readable-library cost is asymmetric in a way that favours waiting.** No open-source
OMR project publishes an error rate on a hand-marked wind-band part, and both of the most honest
ones say why: oemer's README states it "will probably not work on transcribing hand-written scores,"
and Audiveris's says "a 100% recognition ratio is simply out of reach in many cases" and ships a
manual editor because of it. The best published numbers anywhere (SMT: 1.3–5.3% CER) are on printed
grand-staff piano and printed string quartets. A marching library is photocopied condensed scores,
pencilled rehearsal marks, taped-over cuts, and hand-renumbered measures — worse than every
published condition, in a way nobody has quantified. **Anyone who quotes an OMR accuracy figure for
this domain is quoting a piano number.** Meanwhile the *current show*'s score already exists as
MusicXML, because the arranger worked in Finale, Sibelius, or MuseScore. So machine-readable
repertoire for this season is nearly free; OMR buys only the retrospective query over the legacy
paper library — a genuine capability, but a nice-to-have, not the season's workflow. Keeping it in
Phase C is what makes §18 item 7's "large and separable body of work" actually stay separable.

**d. What you need from the score is much smaller than a score.** The anchor needs a monotone
barline map: `measure_number → x-position on page → approximate time`. It does not need pitches,
rhythms, dynamics, or instrumentation. Two cheap sources exist. Where a MusicXML source file exists:
`partitura` gives measure numbers and a `beat_map`, and `verovio`'s `RenderToTimemap()` /
`GetTimesForElement()` (verified in `include/vrv/toolkit.h`) gives measure↔time↔`xml:id` directly.
Where only a scan exists: **use stage 1 of homr/oemer and discard stage 2.** homr's documented
pipeline detects staff lines, barlines, clefs, and noteheads by segmentation *before* any transformer
runs. Barline detection is a vastly easier problem than transcription, and it is the only part you
need. Pair it with printed-measure-number OCR (Audiveris already delegates text to an external OCR)
and you have measure addressing from a scan without ever trusting an OMR transcription. That is the
concrete cost reduction, and it is why "how much of the library must be machine-readable" is the
wrong question — the answer is "none of it, in the sense you meant."

**e. Both routes converge if the anchor is a sum type.** The decision does not have to be made now,
and the schema is what buys that:

```
anchor
  kind            TAP | ALIGNED | MANUAL | UNKNOWN     # never absent, never guessed
  wall_clock      required, always                     # the record; survives everything
  span            start/end (wall_clock)
  measure         optional int                         # the addressing
  beat_in_measure optional
  rehearsal_mark  optional str
  score_ref       optional (score_id, element_xml_id)  # MEI xml:id via verovio
  provenance      P1–P5  (§15, prefixed, never bare)   # TAP is first-party; ALIGNED is Estimated
  state           draft | sealed | pending  (§8.2)
```

A tap is `kind=TAP`, `wall_clock` set, `measure` null. When a score arrives for that chart — next
week, next year, never — the same commentary record *gains* a measure without the remark changing,
and the `provenance` field records that the measure was derived rather than observed. `kind=UNKNOWN`
is what a failed alignment returns, satisfying rule 13: a rubric that failed to load returns
"unavailable," and an aligner that failed returns `UNKNOWN`, not measure 1. And `reject_match` on an
`ALIGNED` anchor must **fall back to the underlying `TAP` or wall-clock anchor, not delete the
remark** — which is only possible if the tap was captured in the first place. That is the clinching
argument for capturing taps even in a future where alignment works perfectly.

**Phasing that follows from this:**

- **Phase A (ship this).** Tap-to-mark with three interchangeable inputs — an on-screen button in the
  judge surface (peaks.js), a BT/USB pedal as HID (`footswitch`), and **the marker button on the
  judge's own field recorder**, read back out of the WAV's BWF/iXML/cue chunks. All three produce the
  same `TAP` record. Plus audio↔audio alignment (`audalign`, `linmdtw` for long shows, LTC where you
  control the rig), which is needed on every route and is the best-supported piece in the pipeline.
- **Phase B.** Measure map for the current repertoire from the arranger's MusicXML via
  `partitura` + `verovio` timemap. Then offline DTW (`synctoolbox` MrMsDTW against a FluidSynth
  render of the score) as a *refinement*, with taps as hard alignment constraints — which is exactly
  the JLTR result restated. Human-labelled jumps come from the cut sheet.
- **Phase C, separable.** Barline-only extraction from scans (homr/oemer stage 1 + measure-number
  OCR) for the legacy library; full OMR behind a human seal, output marked non-authoritative per
  §5's canonical/sidecar rule.

**One correction to the §8.2 pipeline order.** *"ingest → align → diarize → transcribe → anchor →
index"* puts diarization on the critical path, and for the primary artifact it does not belong there.
A judge's tape is single-speaker by construction: one judge, one mic, one recorder. Diarization is
needed only for clinic sessions and panels sharing a room. **The cheapest diarizer is a second XLR
input** — and per-channel capture has a privacy dividend that matters more than the CPU saving: one
file per judge means a judge's material is separable at the filesystem level from the first write,
which is the same shape as §7.4 W-1's lane rule. Make diarization conditional on channel count and
you remove the pipeline's most license-encumbered component (pyannote) from the default path
entirely.

---

## Resource caps — transcription must not starve attendance-taking

The pipeline is embarrassingly batchable and should never be interactive. Concrete posture:

1. **Never during the event.** The queue drains after the last performance, not on competition
   morning. Attendance is interactive and owns the box. This is a scheduling rule, not a tuning
   parameter — write it as a refusal, not a config default.
2. **One worker, one job.** Reject `whisper-diarization`'s parallel mode outright: its README asks for
   ≥10 GB VRAM. A school hub does not have a spare 10 GB.
3. **Enforcement, not a ledger** (rule 18). A `max_cpu` key in a YAML file is a ledger. The
   enforcement surfaces are: `kartikeya`'s existing cgroup/prlimit caps (already in the fleet, §14),
   a systemd slice with `CPUQuota=` / `MemoryMax=` / `IOWeight=`, plus `nice`/`ionice`, plus
   thread caps inside the engine (`OMP_NUM_THREADS`, ONNX Runtime intra-op threads, `whisper.cpp -t`).
   Say which one is load-bearing in the commit.
4. **Pick the model to fit the cap, not the cap to fit the model.** sherpa-onnx ships 14M and 20M
   parameter ASR models rated for a Cortex-A7 — the floor is very low, so "we need a GPU" is a
   choice, not a constraint. Parakeet TDT is *reported* at ~30× realtime int8 on CPU versus
   whisper-small at ~8× (unverified, secondary source) — worth measuring, since a 4× throughput win
   is a 4× smaller window of contention.
5. **The chunking pattern to copy is BirdNET's**, not an MIR toolkit's: segment long recordings into
   fixed windows, queue them, and process at whatever rate the box allows, so a job is always
   interruptible and always resumable. BirdNET does this across thousands of hours on modest
   hardware. A 12-hour competition day of judge audio is a smaller problem than a season of bird
   recordings.
6. **`field-acoustics` and this pipeline are the same budget.** §13 asks whether they can share
   coordinates; they must first share a queue, because both are the expensive things and both want
   the same afternoon.

---

## License flags that matter to a school install

**Read these before anything else in this document.**

- **AGPL-3.0 appears four times in the shortlist**: Audiveris, homr, Panako, aeneas. This is the one
  license family that can actually bite here, because §4.2 contemplates a parent PWA — serving an app
  over a network is what triggers AGPL's source obligation. Mitigation: invoke AGPL tools **as
  out-of-process CLIs over separate artifacts**, never as library imports. But note the trap: §6's
  purity checker is an AST import checker, and §14 already records that *"the AST checker sees
  imports, not filesystem writes."* **An AGPL subprocess is invisible to it.** That is a declaration
  without enforcement — a §16 pair needing a named middle. Whoever adds the first AGPL tool owes a
  test that fails when an AGPL binary is invoked from a path that isn't the sandboxed batch worker.
- **pyannote is a §6 cloud-fallback hazard living inside a library you would adopt.** Code is MIT and
  `community-1` weights are *reported* CC-BY-4.0 — but pyannote.audio 4 also ships `precision-2`,
  which its own README says "runs on pyannoteAI servers." That is `willow-seed`'s Groq/Cerebras
  problem again (§14: *"must be disabled, not unused"*), one import away from `MEDIA_MINOR` audio. If
  pyannote enters the tree it needs a test asserting the pyannoteAI code path **refuses to
  construct**, per rule 19 — a guard that cannot be shown to fail has not been shown to work.
  Separately, CC-BY-4.0 makes attribution a *UI* obligation, and the HF gate makes model download an
  install-time act with an account and a checksum, recorded as procurement — not a runtime fetch.
- **BirdNET is the cautionary shape.** MIT code, CC BY-NC-SA 4.0 weights, and a vendor statement that
  "all educational and research purposes are considered non-commercial use." That carve-out is the
  vendor's interpretation, not the license text, and a district's counsel reads the license.
  **Install-acceptance rule to add (§10/§11.1, 15-check rubric):** every model artifact carries a
  recorded SPDX identifier or license URL, plus a yes/no on *"school use permitted by the license
  text alone, without relying on a vendor FAQ."* NC weights fail that test even when the vendor says
  they pass.
- **Reverb (Rev) is disqualified until verified.** Its README states outright: *"the license in this
  repository applies only to the code not the models."* The model license is not in the repo. Do not
  let it into a build on the strength of an Apache-2.0 badge.
- **Two "reported" licenses I could not verify at source** (huggingface.co is blocked from this
  session): Parakeet TDT 0.6B weights (CC-BY-4.0?) and pyannote `community-1` (CC-BY-4.0?). Both are
  `P2 Cited` and both are load-bearing. One verification pass, recorded.
- **Verovio is LGPL-3.0 + GPL-3.0 dual-licensed** — use the LGPL binding path (WASM / Python / C++
  library) and don't vendor the GPL bits.
- **olimpic/Zeus model is CC BY-SA** — ShareAlike on a *model* means any fine-tune inherits the
  obligation. Relevant if anyone ever fine-tunes on the band's own library.
- **MFA's code is MIT; its pretrained acoustic models live in a separate repo** whose license I did
  not verify. Same rule as above.

---

## Weirdest things I found

**1. Subtitle synchronisation solves the judge-tape problem better than music alignment does.**
`ffsubsync` (MIT, 7.8k★) aligns a subtitle file to a video by discretising both into 10 ms windows,
reducing each to a **binary speech/no-speech stream**, and finding the offset with an FFT — O(n log n)
instead of O(n²), 20–30 seconds per file. The insight transplants directly and inverts the instinct:
a judge's lapel mic one inch from a talking human and a press-box stereo pair forty yards away share
almost no spectral content, so chroma DTW is fighting. But they share a *coarse envelope* — the band
is loud in both, the silences between movements are silent in both. Align on a deliberately
impoverished derived stream and the mismatch stops mattering. A robust bad feature beats a fragile
good one. Also worth noting: the same repo runs its browser build on ffmpeg.wasm and says plainly
that nothing is uploaded — a decent model for how to phrase §10's TRUST.md rows.

**2. Court reporters solved "the addressable unit of a spoken record" a century ago, and it looks
exactly like §8.2.** The court record's unit is `page:line` — stable, quotable, sayable out loud,
and it becomes *the* record only when a named human certifies it; before that it is a rough draft
with no evidentiary standing. That is §8.2's `draft`/`sealed` cascade, rediscovered from first
principles by a profession that has been sued over it. Two concrete artifacts fall out. `Plover`
(GPLv2+, 2.6k★) is a working open-source stenography engine doing >200 wpm fully offline — a real
option for a program that has a trained operator, and a genuine accessibility path. And
`rgerganov/footswitch` (MIT, 488★, ~400 lines of C) is the transcriptionist's foot pedal, programmable
on Linux via udev with zero vendor software: a judge holding a clipboard and a microphone has a spare
foot, and the pedal costs $25. The legislative-XML world (`laws-africa/cobalt`, Akoma Ntoso) supplies
the other half — stable hierarchical `eId` addresses designed so a citation survives re-typesetting,
which is the same requirement as a measure reference surviving a re-engraved part.

**3. The judges' recorders already implement tap-to-mark, in firmware, and nobody uses it.**
Zoom F6-class field recorders write cue **marks** plus BWF `bext` and iXML metadata chunks directly
into the WAV. A judge presses MARK on hardware they already own, already trust, and already know how
to operate with gloves on in November; you read the chunks off the card afterwards. No app, no
pairing, no battery anxiety, no "did it save." Combine with `libltc` (LGPL-3.0, 246★) striping SMPTE
timecode onto a spare channel of both rigs and the entire audio-to-audio alignment sub-problem
collapses from a research question into a subtraction. This is the film/dialogue-post answer, and it
is available today for the price of a recorder the program probably already owns. Open-source chunk
readers are thin (`metawav/chunk`, Go, 3★) — the RIFF parsing is a day of work, not a dependency.

**4. Bootleg score synthesis: align the *picture* of the score, and never do OMR at all.** Reduce a
MIDI file to rectangular notehead blobs, reduce a *scanned page* to the same blobs with a notehead
detector, and DTW the two images — 97.3% at 1 s on 68 real scanned piano scores, beating OMR
baselines *(reported)*. The generalisation is the valuable part and it reframes §18 item 7: **the
anchor needs the score to be ordered, not understood.** Everything OMR is bad at — pitch, rhythm,
accidentals, pencil marks, dynamics — is irrelevant to ordering. And the follow-up work's answer to
the one thing ordering *does* care about (jumps, repeats, cuts) is "have a human click the repeat
signs," which in this domain is a document the band already prints.

**5. The most privacy-clean component in the pipeline was abandoned in 2017 and needs no model at
all.** `aeneas` (AGPL-3.0, 2.9k★, dead since v1.7.3 in March 2017) does text-to-audio forced
alignment with **no language model, no acoustic model, and no weights**: it synthesises the text with
eSpeak, then aligns the synthetic audio to the real audio with MFCC + DTW. That is structurally
identical to score alignment — synthesise the MusicXML with FluidSynth (`partitura` already does
this), then DTW against the performance. Which means the stored-score route can be built with **zero
model weights, zero weights licenses, zero GPU, and nothing to gate behind a Hugging Face token.** In
a project whose central refusal is about non-local inference, the alignment stage can be made to
contain no inference at all. (Runner-up in the same vein: `Panako`, AGPL-3.0, built for the Royal
Museum for Central Africa's archive, fingerprints robustly across **±10% time-scale and pitch drift**
because ethnomusicology archives are full of tapes digitised at the wrong speed — which is also a
perfect description of a microcassette of a judge from 2003.)

---

## Gaps — what open source cannot do for you today

State these plainly, because the temptation is to assume the piano numbers transfer.

- **No maintained large-ensemble or wind-band score follower exists.** The only repo describing
  itself that way is dead since 2016 with 4 stars. `matchmaker` is alive and well-built and evaluated
  entirely on solo piano. Anyone who wants an ensemble number will have to produce it.
- **No published OMR error rate on hand-marked wind-band or marching parts.** Not one. The best
  numbers available (SMT's 1.3–5.3% CER) are printed grand-staff piano and printed string quartets;
  oemer and Audiveris both say in their own READMEs that handwriting and imperfect scores are out of
  scope or unreachable. Handwritten OMR resources exist as *datasets* (MUSCIMA++, `hajicj/muscima`,
  17★) but not as working transcription for this notation.
- **No open corpus of adjudicator commentary.** Every published WER is clean speech. A judge speaking
  over a 100 dB ensemble, outdoors, into a lapel mic, using domain jargon and measure numbers, is a
  condition with no baseline. Expect materially worse than any leaderboard figure, and — per rule 10 —
  that is precisely why the transcript must be a `draft` until the judge seals it. The `pending` state
  in §8.2 will get used more than the design probably assumes.
- **Measure-number OCR from a scan is not a solved, packaged thing.** Audiveris delegates text to an
  external OCR and homr/oemer detect barlines but do not read printed measure numbers as a named
  output. The barline-only path I recommend is a real (small) build, not an install.
