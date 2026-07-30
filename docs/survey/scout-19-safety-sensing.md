# Scout 19 — Environmental & Physiological Safety Sensing, and Citing the Number

Slice: practice-field environmental and physiological safety monitoring (heat, lightning, noise, load),
and the discipline of citing a numeric safety threshold.

Read before searching: `docs/CAPABILITY-MAP.md` §12, `docs/ARCHITECTURE.md` §15, `CLAUDE.md`.

---

## 0. Method, and two honest limits on this report

**Limit 1 — WebSearch was exhausted before I started.** This session had already spent its
200-call WebSearch budget. All discovery below was done through the GitHub REST search API
(`search_repositories`, `search_code`) plus `WebFetch` against `raw.githubusercontent.com` and
`github.com`. That biases the haul toward things GitHub indexes well in a repo name, description,
or topic, and away from things that live on a project website, in a mailing list, on Codeberg or
GitLab, or in a paper. **Treat the absence of a candidate here as "not found by this method,"
not as "does not exist."** Two known-relevant ecosystems are almost certainly under-represented
as a direct result: Codeberg-hosted hardware (the `shred/kaminari` lightning detector is
explicitly tagged `moved-to-codeberg` and I could only see its GitHub tombstone), and
Sensor.Community / Luftdaten (`opendata-stuttgart/sensors-software`), which returned zero on
every query shape I tried.

**Limit 2 — and this one matters much more for Half Two — I could not reach a single
authoritative publisher.** This session's egress policy returned 403 on `cdc.gov`,
`osha.gov`, `ecfr.gov`, and `weather.gov`, via both `WebFetch` and `curl` through the agent
proxy. The proxy status endpoint confirms these are policy denials at the gateway, not TLS or
tooling faults, and the README says not to route around them.

So, per the instruction and per §15's own rules:

> **No numeric heat-index threshold and no numeric dB-exposure threshold in this report is
> asserted as fact.** I fetched none of them from a publisher. Every number that appears below
> is quoted as *"what this open-source repository claims the standard says,"* attributed to the
> repository, which in the project's vocabulary is a `P2 Cited` claim about a `P2 Cited` claim —
> i.e. **`P4` at best after `min` propagation**, and not something to put in a handbook.
> The publishers themselves are named in §2.6 with the status `unverified-this-session`.

This is not a graceful degradation, it is the correct one. It is also, unintentionally, a live
demonstration of the exact failure §15 is about: an authority that returns 403 today looks
identical to an authority that was deleted, and a citation that cannot be re-fetched has
silently stopped being a `P2`. A liveness sweep that recorded only `observed.http_status` would
have marked all four of these sources `dark` this morning and been wrong — which is precisely
why `almanac-template`'s split between `observed` (machine facts) and `status`
(`status_source: auto | curator`) is the right shape, and why a `403` from a corporate egress
proxy must not be allowed to auto-demote a citation.

**Recommendation to carry forward:** whatever runs the daily sweep needs to distinguish
*"the source is gone"* from *"we could not reach the source from here."* An `observed` record
that cannot tell those apart will generate false `dark` transitions on every network
restriction, and after the third false alarm nobody will read the flags. Add a
`reachability_context` (which egress path, whether other known-live control URLs also failed)
and require a curator to confirm any `live → dark` transition. A control URL that is expected
to always resolve, probed in the same pass, is the cheapest possible version of this.

---

# HALF ONE — SENSING AND HARDWARE

## 1.1 Ranked table

Activity dates are as reported by the GitHub API on 2026-07-30. Star counts likewise; they are
a weak signal and I include them only to distinguish "a community uses this" from "one person
wrote this last month."

| # | Project | What it is | License | Activity | Maps to (§12 item) | Verdict |
|---|---|---|---|---|---|---|
| 1 | [`jmrplens/phonometry`](https://github.com/jmrplens/phonometry) | Standards-conformant Python acoustics library. Claims IEC 61672-1 weighting, IEC 61260-1 filters, **IEC 61252 noise dose**, **ISO 9612 `LEX,8h` with Annex C uncertainty**, ISO 1999 hearing-loss modelling, IEC 60942 calibration stability. ~101★, updated the day I looked. | MIT | Very active (2026-07-30) | Hearing conservation & dB exposure | **Adopt** |
| 2 | [`ChelseaKR/olive-bark-logger`](https://github.com/ChelseaKR/olive-bark-logger) | Privacy-first RPi/PWA noise logger. **Never stores audio.** SQLite of derived levels only; calibration offset applied at *render*, append-only; mandatory methodology-and-limitations section in every report; states outright it is not a Type 1/2 meter. | MIT | New, active (2026-07-20) | Hearing conservation; §5 sidecar shape | **Adopt the architecture** |
| 3 | [`SmartQHSE/hse-calculators`](https://github.com/SmartQHSE/hse-calculators) (+ [`-py` port](https://github.com/SmartQHSE/hse-calculators-py)) | 30+ occupational-hygiene calculators, zero runtime deps, each annotated with the regulation it implements — WBGT (ACGIH TLV / ISO 7243), 8-hour noise dose (29 CFR 1910.95), NIOSH lifting, REBA/RULA, hand-arm vibration. | MIT | Active (2026-05/06) | Heat index; dB exposure; repetitive strain | **Adopt (with the gap named)** |
| 4 | [`FedericoTartarini/tool-sma-extreme-heat-policy`](https://github.com/FedericoTartarini/tool-sma-extreme-heat-policy) | A named sports-medicine body's **extreme heat policy for sport, implemented as software**, deployed at `sma-heat-policy.sydney.edu.au`. 490 commits, backend + frontend. | **None visible — blocker** | Active (2026-07-23) | Heat index → mandated water breaks | **Steal the idea** |
| 5 | [`Dizayer/heatsafe`](https://github.com/Dizayer/heatsafe) | ISO 7243 WBGT screening coupled to Gagge 2-node / ISO 7933 PHS / JOS-3, running **entirely in-browser via Pyodide — no server, nothing leaves the device** — and explicitly "states plainly where each model is NOT valid." | Check repo | New (2026-07-16) | Heat index; §15 provenance labelling | **Steal the idea** |
| 6 | [`OHcomplianceStrategies`](https://github.com/tonyderrico/OHcomplianceStrategies) | R implementation of industrial-hygiene **statistical** compliance testing of exposure measurements against an OEL (AIHA-style exceedance fraction / upper-percentile), not threshold-crossing. | Check repo | Dormant (2025-03) | Both thresholds — defensibility | **Steal the idea (important)** |
| 7 | [`Open-Air-Foundation/arduino`](https://github.com/Open-Air-Foundation/arduino) (AirGradient ONE / Open Air firmware) | Open-source firmware for open-hardware air monitors; PMS5003/5003T, SenseAir S8 CO₂, SGP41 VOC/NOx, SHT40 T/RH. Documents a **local server API**; MQTT/HA via PubSubClient. ~367★. | CC BY-SA 4.0 | Very active (2026-07-30) | Environmental stack, local logging | **Adopt (verify local-only mode)** |
| 8 | [`kmich/ha_ws_core`](https://github.com/kmich/ha_ws_core) | Home Assistant weather-station core: 170+ derived sensors incl. UTCI, WBGT, heat index, wet-bulb, Canadian FWI / McArthur FFDI / Fosberg FFWI, ET₀, lightning. Core computed on-box, "never leave your network"; uploads off by default. | See repo LICENSE | Very active (2026-07-29) | Heat index; lightning; local logging | **Adopt / read closely** |
| 9 | [`pythermalcomfort/pythermalcomfort`](https://github.com/pythermalcomfort/pythermalcomfort) | The mainstream thermal-comfort library (PMV/PPD, SET, adaptive, plus heat indices). ~219★, 90 forks, conda-forge feedstock. Same author ecosystem as #4. | Check repo | Active (2026-07-27) | Heat index | **Adopt as dependency** |
| 10 | [`ironsheep/lightning-detector-MQTT2HA-Daemon`](https://github.com/ironsheep/lightning-detector-MQTT2HA-Daemon) + [`SparkFun_AS3935_…_Library`](https://github.com/sparkfun/SparkFun_AS3935_Lightning_Detector_Arduino_Library) + [`lovelace-lightning-detector-card`](https://github.com/ironsheep/lovelace-lightning-detector-card) | The AS3935 Franklin-sensor stack: hardware library, MQTT daemon, and a display card. Local RF detection — **no network needed to detect a strike.** | Per repo | Active (2026-04) | Lightning & field evacuation | **Adopt** |
| 11 | [`mdljts/wbgt`](https://github.com/mdljts/wbgt) / [`QINQINKONG/PyWBGT`](https://github.com/QINQINKONG/PyWBGT) / [`kwodzicki/pywbgt`](https://github.com/kwodzicki/pywbgt) / [`zyf0717/HeatStress.jl`](https://github.com/zyf0717/HeatStress.jl) | Four independent implementations of the Liljegren WBGT model — estimating WBGT from ordinary met inputs when you have no black globe. `HeatStress.jl` advertises reproducible validation against published values. | Per repo | `mdljts` 2026-07; `HeatStress.jl` 2026-07-30 | Heat index (the modelled path) | **Read-only interest, with a caveat** |
| 12 | [`ropensci/Athlytics`](https://github.com/ropensci/Athlytics) | rOpenSci-peer-reviewed R package for training-load monitoring: ACWR, EWMA, TRIMP, aerobic decoupling. ~62★. | Per repo | Active (2026-06) | Repetitive strain / load | **Steal the idea, contest the metric** |
| 13 | [`openathleteorg/openathlete`](https://github.com/openathleteorg/openathlete) | Self-hostable AGPLv3 endurance-training platform, explicitly GDPR-shaped, "your data stays yours." ~57★. | AGPL-3.0 | Very active (2026-07-29) | Load logging without a vendor cloud | **Read-only interest** |
| 14 | [`umic-iitm/rebapose`](https://github.com/umic-iitm/rebapose) | Automated **REBA ergonomic scoring from video** via 18-keypoint pose estimation (HRNet-W32 + MotionBERT), with SME verification and expert shot curation in the pipeline. | Check repo | Active (2026-07-11) | Percussion/marching posture load | **Read-only interest — see §1.8, refusal risk** |
| 15 | [`Shadetail/HearingDose`](https://github.com/Shadetail/HearingDose) | Real-time dosimeter that reads the PC audio bus, estimates dBA at the ear, and tracks a daily noise dose with log-time recovery. | Check repo | New (2026-07-12) | dB exposure — the *dose accumulator* | **Steal the idea** |
| 16 | [`schappim/gm1356-recordings`](https://github.com/schappim/gm1356-recordings) | Pure-Python driver for the **Benetech GM1356** USB SPL meter, including the previously-undocumented on-board log-import protocol. | Check repo | New (2026-06-21) | Cheap defensible-ish dB hardware | **Adopt for the cheap tier** |
| 17 | [`roscoe81/northcliff_spl_monitor`](https://github.com/roscoe81/northcliff_spl_monitor) | Minimal SPL monitor on the Pimoroni Enviro+ (which carries a MEMS mic alongside T/RH/P/gas/light). | Per repo | Dormant (2025-10) | Cheapest sensing tier | **Read-only interest** |
| 18 | [`SmartQHSE/awesome-hse`](https://github.com/SmartQHSE/awesome-hse) | Curated HSE list — regulations, standards, datasets. Useful as a **map of the publisher landscape**, thin on software. Confirms industrial hygiene has an "exposure assessment strategies" tradition. | CC0 | Active (2026-07-20) | Orientation | **Read-only interest** |
| 19 | [`themorgantown/homeassistant-wbgt`](https://github.com/themorgantown/homeassistant-wbgt) | HA integration turning WBGT forecast into **work/rest recommendations and heat alerts**. | Per repo | Active (2026-07-25) | Heat index → activity modification | **Read-only interest** |
| 20 | [`Dizayer/RegulHeat`](https://github.com/Dizayer/RegulHeat) | Gagge + ISO 7933 heat-strain model with **population stratification**. | Per repo | Dormant (2026-04) | Heat index — the minors problem | **Read-only interest, cited for §1.7** |

---

## 1.2 `phonometry` — the only candidate that makes a dB number defensible

This is the top find of Half One and it is not close.

Everything else I looked at in the noise space computes "a number that looks like decibels."
`phonometry` computes numbers **against named standards, and tests that it did so.** Its README
claims implementations of IEC 61672-1:2013 class 1 frequency weighting, IEC 61260-1:2014 /
ANSI S1.11 class 1 octave filters, **IEC 61252 noise dose** (which is the personal
sound-exposure-meter standard — i.e. the dosimeter standard, not the sound-level-meter
standard), **ISO 9612 daily noise exposure `LEX,8h` including Annex C uncertainty**, ISO 1999
noise-induced-hearing-loss modelling, and IEC 60942 calibrator stability validation. License
MIT. Pushed the day I read it.

The transplant that matters most is not a function, it is a CI job. The README describes an
**auto-generated conformance report that validates hundreds of normative values against 250+
standards on every pull request.** That is exactly rule 19 — "a guard that cannot be shown to
fail has not been shown to work" — applied to a measurement chain rather than to a permission
gate. Terpsi should not merely depend on `phonometry`; it should copy the *artifact*: a
generated, committed, dated conformance report that says which normative reference values the
installed version reproduces and to what tolerance. That report is the difference between "our
app said 91 dB" and "our app said 91 dB, computed by a class-1-conformant weighting whose
conformance against the published normative values was verified on this commit."

Concretely, in terpsi's vocabulary: `phonometry` is what lets an `LEX,8h` reading carry
`provenance: P1 Measured` at all. Without a conformance claim it is `P3 Fitted` — derived from
local data by a stated model — and the handbook should say so.

Two cautions I did not resolve. First, ISO 9612's Annex C uncertainty is the honest part and
also the awkward part: it will hand you an exposure estimate with a **confidence interval wide
enough to straddle a trigger threshold.** §15 says provenance never gates and confidence is
continuous — this is where that pays off, because the right rendering is "`LEX,8h` estimated at
X, uncertainty ±Y, **the threshold falls inside the interval**", which is a `draft` for a human,
not an automatic trigger. Second, and this is the hard-stop: a software library cannot make a
**phone microphone** into a class-1 instrument, and `phonometry`'s own IEC 60942 calibration
support is the tell. See §1.5 on hardware tiers.

## 1.3 `olive-bark-logger` — the architecture, essentially already written

Somebody built terpsi's noise sidecar for a barking-dog dispute and it is a startlingly good
fit. Verified from its README: MIT; **never records, stores, or transmits audio** — frames are
processed in memory and discarded, only derived levels and event metadata persist to SQLite;
fully offline, no network required; runs on a Raspberry Pi or as a browser PWA.

Three design decisions are worth transplanting wholesale.

**Calibration is applied at render, not at capture.** Events are stored as raw dBFS; the
calibration offset lives separately with its own provenance, and — quoting the README —
"recalibrating never rewrites earlier events." This is append-only, and it is exactly rule 3
(never revoke by deleting) and rule 16 (a student's entries are as durable as entries about
them) arriving from an unrelated direction. It also solves a problem terpsi definitely has:
you *will* discover mid-season that the mic on the podium was 4 dB off, and you must be able to
correct the reported exposure without destroying the record of what was reported at the time.

**The methodology-and-limitations section is mandatory in every report.** Not a footer, not an
appendix — the README states it cannot be omitted. That is `field-acoustics`'s `ASSUMED`
headline generalised, which §15 explicitly asks for.

**It states what it is not.** "Uncalibrated dBFS is relative, not absolute sound pressure
level unless calibrated." "The device cannot prove a sound's source." "It is not a Type 1 or
Type 2 sound level meter." Those three sentences are the difference between a defensible
instrument and a liability, and they belong verbatim (adapted) in any dB report terpsi puts in
front of a guardian.

Cost: it does not publish a BOM. Realistically an RPi Zero 2 W plus a USB or I²S MEMS mic —
call it low tens of dollars — and its own README tells you that buys you a *relative* logger
until you calibrate it.

**One gap to close on transplant.** `olive-bark-logger` logs a place. Terpsi logs a *person's*
exposure. The moment a dB reading is attributed to a named student, rule 8 applies: it is a lane
entry, not a row in a shared table, and a section-wide reading is "two lane entries with one
referent," never one row with a roster column. A drumline dosimetry sweep is the exact case rule
5 forbids naming as `"the drumline"`.

## 1.4 `hse-calculators` — adopt it, and notice precisely what it is missing

MIT, zero runtime dependencies, pure TypeScript with a Python port, runs in a browser or on the
edge, no external calls. It has `calculateWBGT` and `calculateNoiseDose`. Each calculator names
its regulation. For terpsi this is a very cheap, very clean dependency.

And it is *the single best argument in this whole report for Half Two*, because of what it
does not do. Quoting my read of it: **the library documents regulations by reference — a CFR
number, an ISO number — but does not store version numbers or effective dates.** The citation
lives in prose in the docs, not in the data.

The two threshold-relevant details it exposes, reported here **as the repository's claims and
not as verified fact**: it attributes the WBGT formula to "ACGIH TLV / ISO 7243," and for noise
it records that the **exchange rate differs by authority — the repo states 5 dB for OSHA
(29 CFR 1910.95) versus 3 dB for ACGIH and EU Directive 2003/10/EC.**

Sit with that second one, because it is the whole problem in miniature. The exchange rate is
the parameter that decides how fast dose accumulates with level, and **two named authorities
disagree about it.** A handbook that writes down a dB trigger without saying *which authority
and which exchange rate* has not written down a threshold at all; it has written down an
ambiguity that a district's counsel can drive a truck through. Terpsi's threshold record
therefore cannot be a number. It has to be a tuple: `{publisher, document, version/date,
metric (LEX,8h vs TWA vs dose %), exchange rate, criterion level, canonical URL,
content hash}` — and the handbook renders from that tuple or renders nothing.

## 1.5 Hardware, honestly: what it costs and what the measurement is worth

I could not fetch vendor pages (egress). Prices below are **estimates from memory, marked as
such**, and every one of them needs a `P1` check against a live listing before it enters a
budget. What I *can* speak to with confidence is the *ordering* of the tiers and what each tier
can and cannot support as a claim.

**Noise.**

- *Tier 0 — a phone.* Free. Genuinely useful for triage and for showing a section leader that
  the ensemble is loud. Not defensible: uncalibrated, unknown frequency response, AGC in the
  path, and — decisively for terpsi — **the microphone is on a device in a minor's pocket**,
  which drags a dosimetry programme into `PII_MINOR` territory with no gate on it.
- *Tier 1 — a cheap USB SPL meter, logged.* This is where `schappim/gm1356-recordings` earns
  its place: a Benetech GM1356 is the commodity meter in this class (my estimate: low tens of
  dollars) and that repo gives you a pure-Python driver *plus the on-board log-import protocol*,
  so you can pull the meter's own recorded log rather than trusting a live serial stream. These
  meters are typically marketed around Type 2 / class 2; treat any such marketing claim as
  unverified until you see a calibration certificate.
- *Tier 2 — a class 2 meter with an acoustic calibrator.* This is the first tier at which the
  word "defensible" is honest, and it is honest **only because of the calibrator**, not the
  meter. `phonometry`'s IEC 60942 stability validation is the software half of this tier.
  My estimate: a few hundred dollars for meter plus calibrator.
- *Tier 3 — real personal dosimeters (IEC 61252 body-worn, one per exposed player).* Where
  occupational hygiene actually lives, and priced accordingly — my estimate is high hundreds to
  low thousands *per unit*, which for a drumline is not a purchase, it is a capital project.

The honest recommendation is **Tier 2 for the ensemble, borrowed Tier 3 for a one-off
characterisation study.** A single well-designed measurement campaign — one week, borrowed or
rented dosimeters, an athletic trainer or a district industrial hygienist present — produces a
`P1 Measured` characterisation of *this* ensemble's typical exposure by position, and from then
on Tier 2 monitoring plus a duration log is enough to say "today resembled the characterised
case." That converts a permanent instrumentation problem into a one-time study plus cheap
ongoing confirmation, which is both cheaper and *more* defensible than continuous cheap
monitoring, because the defensibility lives in the study.

**Heat.**

- *Tier 0 — forecast WBGT / heat index from a public feed.* Free, and `HSSBoston/wbgt` shows
  the pattern (RPi pulls the NOAA WBGT forecast to an e-paper display). It is a **forecast for
  a grid cell**, not a measurement of your field, and the difference between a grid cell and a
  black asphalt parking lot in full sun at 15:00 is exactly the difference that hurts a kid.
  `P4 Estimated` at best.
- *Tier 1 — modelled WBGT from your own T/RH/wind/solar.* This is what `mdljts/wbgt`,
  `PyWBGT`, `pywbgt` and `HeatStress.jl` implement (Liljegren). Genuinely good, and it means a
  standard weather station plus solar radiation gets you a WBGT estimate. But it is `P3
  Fitted` — *derived from local data by a stated model* — and the model's stated assumptions
  about surface, wind exposure and radiation geometry are assumptions about *your field* that
  nobody validated.
- *Tier 2 — an actual black globe thermometer.* This is the whole ballgame and it is
  surprisingly affordable: WBGT's defining measurement is a black-painted copper sphere
  (150 mm in the classical specification) with a temperature sensor at its centre, plus a
  natural-wet-bulb sensor. A competent maker can build this; the classical globe is a painted
  copper toilet float. My estimate is tens of dollars in parts. **The transition from `P3` to
  `P1` on the highest-liability threshold in the entire capability map costs about the price of
  a set of drumsticks**, and that is the single best value-for-money item in this report.
- *Tier 3 — a commercial WBGT meter (Kestrel-class).* My estimate: several hundred dollars.
  Buys you a calibration certificate and a defensible instrument out of the box, and for
  something this liability-laden that may simply be the right answer regardless of what you
  build.

**Do not build the globe and skip the shield.** The commonest way homebrew heat monitoring
produces a wrong number is a dry-bulb sensor in the sun or in a badly-aspirated enclosure. The
sensor stack in `Open-Air-Foundation/arduino` (SHT40 for T/RH) is fine; the radiation shield
and aspiration are what decide whether the reading means anything.

**Lightning.** The AS3935 Franklin sensor is the whole open-hardware story here and it is
cheap — my estimate is tens of dollars for a SparkFun Qwiic board — with
`ironsheep/lightning-detector-MQTT2HA-Daemon` giving you a working MQTT daemon and
`lovelace-lightning-detector-card` a display. `haklein/flashbee` is a notable recent handheld
port whose description mentions "safety-critical datasheet fixes" and antenna auto-tune, which
is a polite way of saying **the AS3935 is fiddly and easy to get wrong**: it needs antenna
tuning, it has a noise floor that must be calibrated per site, and it reports *estimated
distance to the storm front*, not to individual strikes.

And here is the part that decides the design: **an AS3935 must not be the thing that clears a
field.** For that decision the right architecture is *defence in depth with an explicit
`unknown`* — local AS3935 for immediate detection, a network source (the community
Blitzortung network is the open one; `keraunos` and `blitz` are recent consumers of its feed)
for corroboration and for the all-clear timer, and a human with the authority to call it. Rule
13 governs the failure mode precisely: **a lightning backend that errored returns
`unknown`, never "no strikes."** Silence from a detector that has lost its antenna tune is
indistinguishable from a clear sky, and that is the one place in this slice where a
degraded-to-quiet sensor kills someone.

## 1.6 The most useful thing I found, and it is not a sensor

`tonyderrico/OHcomplianceStrategies` is a small, dormant R app that compares a set of worker
exposure measurements against an Occupational Exposure Limit using **industrial hygiene
statistical compliance strategies** — the AIHA/BOHS tradition of exceedance fractions and
upper-tolerance-limit estimates on a lognormal exposure distribution.

Its value to terpsi is conceptual and large: **industrial hygiene does not decide compliance by
asking whether a reading crossed a line.** It treats exposure as a random variable, takes a
sample, and estimates the probability that the underlying distribution exceeds the limit. The
question is never "was today over?" but "what fraction of days does this job exceed the limit,
and how confident are we?"

Terpsi's §12 items are both written in threshold-crossing language — "at what heat index water
breaks become *mandatory*", "at what dB exposure hearing conservation is *triggered*". That
framing is correct for the *operational* decision (you need a bright line a 22-year-old staffer
can apply on a field at 14:00 with no judgement calls) and wrong for the *retrospective* claim.
The two must be separate objects:

- the **trigger** — a bright line, cited to a publisher, applied automatically, deliberately
  conservative, and rendered as an instruction, not a finding; and
- the **exposure characterisation** — a statistical statement about the ensemble's exposure
  distribution over a season, with an interval, which is what actually answers "did this
  programme protect these kids."

Conflating them produces the worst of both: a bright line that gets argued with because it is
presented as a measurement, and a season record that consists of threshold-crossing counts and
cannot support any claim about cumulative exposure. Rule 18 applies with unusual force —
a trigger that fires a notification is **enforcement**; a stored daily dose figure that nothing
routes through is a **ledger**; and hearing conservation needs both, named separately.

## 1.7 The caveat nobody in this haul handles: these models are not about children

Every heat-strain model I found — ISO 7243 WBGT screening, ISO 7933 PHS, ACGIH TLVs, the
work/rest tables in `homeassistant-wbgt`, and the NIOSH-lineage material in `hse-calculators`
— is **occupational**. It was developed for, and validated on, healthy adult workers, generally
acclimatised, generally with some control over their own pace.

A fifteen-year-old sophomore in a wool uniform carrying a contrabass, in week one of band camp,
unacclimatised, wearing a shako, being told when to stop by an adult, is not that population.
`Dizayer/RegulHeat` is the only project I found that even names the issue — its description
advertises "population stratification" for occupational *and sedentary* assessment — and
`Dizayer/heatsafe` is the only one that advertises **stating plainly where each model is not
valid.** Those two are low-star and new, and I list them for that property alone.

For terpsi this is not a nuance, it is a `P4` disclosure that has to travel with the number.
When the threshold in the handbook is derived from an occupational standard, the record must say
so: *the publisher's population is not this population, and the extrapolation is ours.* §15
has the exact rung for this — `P4 Estimated`, "extrapolated from analogous cases, not this
one" — and the sentence "and in this domain that distinction is the difference between a
defensible design decision and a guess wearing a number" was apparently written for precisely
this case. Note also that youth-athletics bodies publish their own heat guidance aimed at
adolescents (§2.6); where such guidance exists it is the better citation, and where terpsi
falls back to an occupational standard it should say why.

## 1.8 Repetitive strain and load — thin, and one candidate terpsi should probably refuse

The load-monitoring space is real but built for endurance athletes with power meters, not for a
snare player carrying 20 lbs on a harness for four hours.

`ropensci/Athlytics` is the credible piece: an rOpenSci-peer-reviewed R package computing ACWR
(acute:chronic workload ratio), EWMA-smoothed load, and TRIMP. Peer review by rOpenSci is a real
quality signal and rare in this space. **But ACWR itself is contested in the sports-science
literature** — there is a substantial methodological critique of the ratio as originally
formulated. Terpsi must not ship an ACWR number as a finding; if it computes one at all it is
`P3 Fitted` by a *disputed* model, which arguably needs a rung this project does not have.
Worth raising as an open question: §15's `P1–P5` has no way to say "computed by a named model
whose validity is actively disputed by the field that produced it," and that is a distinct
claim from `P3`.

`openathleteorg/openathlete` (AGPL-3.0, self-hostable, "your data stays yours") is the right
*shape* for a load log — no vendor cloud — but it is a cycling/running platform and the
transplant is architectural, not functional.

For ergonomics proper, `hse-calculators` already exposes REBA, RULA and the NIOSH lifting
equation, which map more naturally onto percussion carriage and instrument lifting than any
endurance metric does. Start there.

**And then there is `umic-iitm/rebapose`, which I am flagging as a refusal case rather than a
candidate.** It scores REBA ergonomic risk automatically from *video*, using pose estimation.
The technical fit to marching-arts posture load is genuinely excellent. The problem is that
running it means video of minors through a model:

- `MEDIA_MINOR` data through an inference pipeline engages refusal 1 — it must be a **local**
  model, no cloud fallback, and a stopped Ollama fails loudly rather than degrading to a third
  party. HRNet-W32 + MotionBERT is heavy enough that "just run it locally" is a real hardware
  commitment, not a config flag.
- A per-student posture score computed across rehearsals is *precisely* a durable rating of a
  student carried between contexts — **prohibited scope `SA-3`**, invalid even signed by root.
- And rule 6 lurks one step away: the instant two students' REBA scores are visible in the
  same view, someone will compute a priority between them.

I include it because the brief asked for candidates that would not otherwise be searched for,
and because **the most interesting thing about it is that terpsi's own rules already answer
it.** The correct disposition is not "no video ergonomics" but "video ergonomics is a
one-off, consented, aggregate-only *study* to inform drill design, run locally, producing no
per-student durable score" — which is the same shape as the dosimetry characterisation study in
§1.5. That is a genuinely useful pattern and it is worth naming: **for physiological load,
prefer a bounded consented study that yields a design change over continuous monitoring that
yields a per-student record.**

---

# HALF TWO — CITING THE NUMBER

## 2.1 Ranked table

| # | Project | What it is | License | Activity | Maps to | Verdict |
|---|---|---|---|---|---|---|
| 1 | [`openfisca/openfisca-core`](https://github.com/openfisca/openfisca-core) + [`-france`](https://github.com/openfisca/openfisca-france) | Legislation-as-code engine whose **parameters are dated YAML**: a threshold is stored as a series of effective dates, not a constant. Verified format below. ~234★ / ~308★. | AGPL-3.0 (verify) | Very active (2026-07) | Threshold storage + revision history | **Adopt the data model** |
| 2 | [`CatalaLang/catala`](https://github.com/CatalaLang/catala) | Literate-programming language for **law specification**: the statutory text and the code implementing it live interleaved in one file, so drift between authority and implementation is visible in the diff. ~2.35k★. | Apache-2.0 (verify) | Active (2026-07-27) | Guideline→policy traceability | **Steal the idea (strongly)** |
| 3 | [`usnistgov/OSCAL`](https://github.com/usnistgov/OSCAL) + [`oscal-deep-diff`](https://github.com/usnistgov/oscal-deep-diff) | NIST's model for **control catalogs, profiles (tailored baselines), and traceability** from upstream catalog → local baseline → implementation — plus a purpose-built **deep-differencing tool for catalog revisions**. ~932★ / ~42★. | NIST public domain / see repo | Very active (2026-07-29) | Flagging downstream docs on upstream change | **Adopt the pattern** |
| 4 | [`dgtlmoon/changedetection.io`](https://github.com/dgtlmoon/changedetection.io) | The mainstream self-hosted upstream-change watcher. ~32.5k★, pushed today. Content-change detection with notifications and RSS; runs in Docker on your own box. | See repo (Apache-family) | Very active (2026-07-30) | Liveness + drift sweep | **Adopt** |
| 5 | [`thp/urlwatch`](https://github.com/thp/urlwatch) | The scriptable, config-file-driven ancestor: watch parts of pages, filter, diff, notify. ~3.1k★. Config is a **file you commit**, which matters here. | See repo | Active (2026-07-28) | Liveness + drift sweep, in-repo | **Adopt (preferred over #4)** |
| 6 | [`COVID19Tracking/covid-tracking`](https://github.com/COVID19Tracking/covid-tracking) | **An urlwatch configuration for monitoring US state public-health data pages** — the precedent that this exact technique was used, at scale, against exactly this class of authority. ~105★. Archived. | See repo | **Archived** (2026-05) | Precedent + config to crib | **Steal the idea** |
| 7 | [`ComplianceAsCode/content`](https://github.com/ComplianceAsCode/content) | ~2.77k★, pushed today. Single rule definitions mapped to **many upstream standards at once** (NIST 800-53, PCI-DSS, STIG, CIS…), each with its own version, and built into per-profile artifacts. | See repo | Very active (2026-07-30) | One local rule, many cited authorities | **Adopt the pattern** |
| 8 | [`lycheeverse/lychee`](https://github.com/lycheeverse/lychee) + [`lychee-action`](https://github.com/lycheeverse/lychee-action) | Fast async link checker for Markdown/HTML, with a GitHub Action. ~3.8k★ / ~502★. | Apache/MIT (verify) | Very active (2026-07-29) | The daily liveness probe itself | **Adopt** |
| 9 | [`SmartQHSE/hse-calculators`](https://github.com/SmartQHSE/hse-calculators) | Listed again deliberately: it is the **best available example of the failure mode** — regulation named in prose, no version, no effective date, no liveness. | MIT | Active | The gap this half exists to fill | **Read as a cautionary example** |
| 10 | [`gsimchoni/yrbss`](https://github.com/gsimchoni/yrbss) | An R interface to CDC's **Youth Risk Behavior Surveillance System** — the obvious youth counterpart to BRFSS. ~2★, untouched since 2022. | See repo | **Dormant** | §12's missing youth-health baseline | **Read-only interest — and see §2.6** |
| 11 | [`velvetmonkey/canary`](https://github.com/velvetmonkey/canary) | A recent LangGraph pipeline for ESG **regulatory change monitoring**: fetch → detect → extract → **verify** → report, with a `citation-verification` topic. 0★. | See repo | New (2026-07-15) | The pipeline shape | **Read-only interest** |
| 12 | [`avanbremen/sample-ig`](https://github.com/avanbremen/sample-ig) | Minimal HL7 FHIR Implementation Guide with **semver'd GitHub Pages publishing** via the IG Publisher and Actions. | See repo | New (2026-06) | Versioned normative publishing | **Read-only interest** |

## 2.2 `openfisca`'s dated parameters — the smallest correct answer

I verified the parameter format directly. An OpenFisca parameter file is:

```yaml
description: Income tax rate
metadata:
  unit: /1
values:
  2012-01-01:
    value: 0.16
  2013-01-01:
    value: 0.13
  2014-01-01:
    value: 0.14
  2015-01-01:
    value: 0.15
  2016-01-01: expected
```

Three properties, all of which terpsi's threshold store needs.

**A threshold is a time series, not a constant.** You do not overwrite the heat-index trigger
when the guideline is revised; you append an effective date. Every past decision remains
computable against the rule that was actually in force when it was made — which is the same
argument as rule 3 (never revoke by deleting) and the same argument as `invalid_at`. When a
guardian asks in March why practice continued on a particular afternoon in August, you need the
threshold *as it stood that afternoon*, not today's.

**Every value has a `description` and a `metadata` block**, so the unit travels with the
number. Rule 14's "scales never compare as bare integers" generalises here: a bare `28` is not
a threshold. `28 °C WBGT` and `28 °C air temperature` are different claims and one of them
gets somebody hurt.

**`expected` is a first-class placeholder** for a date where a change is anticipated but the
value is not known, and it explicitly does not affect calculations. That is a genuinely elegant
encoding of "we know this is under revision," and it is the missing state in the liveness
model: `almanac-template` has `live · revised · moved · redirected · superseded · dark ·
frozen`, all of which are *retrospective*. `expected` is prospective — "a revision is
announced, we do not yet have it" — and a threshold sitting in that state should arguably
render with a warning even though nothing is broken yet. **I'd put this forward as a
recommended eighth state, or as an orthogonal `revision_announced` flag.**

What OpenFisca does not give you for free is the citation itself. The `country-template`
example above carries `description` and `metadata` but no source URL; real country packages
conventionally attach a `reference` to the legal text, and **I was unable to verify that field's
presence or schema** — a `search_code` query for it against `openfisca-france` returned zero,
which given the API's indexing behaviour I read as inconclusive rather than negative. Flagging
it as unverified rather than asserting it.

## 2.3 `Catala` — the traceability argument, made structurally

Catala (~2.35k★, active) is a language for writing law-derived code in which **the statutory
text and its implementation are interleaved in a single literate document**: each block of code
sits directly beneath the article it implements. The compiler builds executable code from it,
and the text is not a comment — it is the primary artifact.

Terpsi does not need an OCaml DSL. It needs the property: **the authority's own words live next
to the enforcement that claims to implement them, in one file, under version control, so that
a revision upstream produces a visible diff next to the code that must change.**

This is rule 12 — "every pair gets a named middle, in the same commit" — and the pair here is
exactly the one §16 calls out: **declaration plus enforcement.** The guideline is the
declaration; the trigger in the code is the enforcement; and without a named reconciler they
drift silently for three seasons. Catala's answer is to refuse the gap by putting both in one
document. Terpsi's cheaper answer, in the same spirit: a `thresholds/` directory where each
threshold is one file containing the quoted passage from the publisher, the citation tuple, the
effective-date series, and the test that exercises the trigger — and a CI check that fails if
the quoted passage's content hash no longer matches what the liveness sweep last fetched.

That last check is the whole mechanism the capability map is asking for, in one sentence.

## 2.4 OSCAL and ComplianceAsCode — upstream/downstream, already solved twice

These two are the closest things I found to "automatically flag a downstream document when an
upstream authority changes," and they solve it in complementary ways.

**OSCAL** models the chain explicitly: a *catalog* is an upstream authority's controls; a
*profile* is a tailored, downstream baseline that **imports** from a catalog and records its
modifications; an implementation traces to the profile. The upstream/downstream relation is
data, not documentation. And `usnistgov/oscal-deep-diff` exists — actively maintained, pushed
2026-07-29 — for exactly the operation terpsi needs: *diff two revisions of a catalog and
report what moved*. NIST built a specialised differ because generic text diff is useless on a
restructured normative document, and a handbook citing "§5(b)(2)" cares enormously whether that
paragraph was renumbered.

The transplant: model terpsi's handbook as a **profile over a catalog of external safety
guidance.** The handbook does not contain thresholds; it *imports* them and records its
tailoring ("we adopt the stricter of the two exchange rates"; "we apply the youth-athletics
guidance in preference to the occupational TLV"). When the upstream catalog revises, the
profile's imports are what get flagged — not the whole document, and not nothing.

**ComplianceAsCode/content** (~2.77k★, pushed today) contributes the other half: **one local
rule, many cited upstream authorities, each independently versioned.** A single hardening rule
carries mappings to NIST 800-53, PCI-DSS, STIG, CIS and others simultaneously, and the build
emits per-authority artifacts. This is directly applicable, because terpsi's heat and noise
thresholds are *exactly* multi-authority: §1.4 already showed OSHA and ACGIH/EU disagreeing on
the noise exchange rate, and a state athletic association's heat policy, a national
athletic-trainers' position statement and an occupational TLV will all have a view. The right
data model is not "the threshold" but **"our trigger, plus the set of authorities we can cite
for it, plus which one we chose and why"** — and when one of them revises, the flag says which.

That "and why" is a `sealed` decision with a named `verifier` (§15), not a config value. Which
authority a programme chooses to follow for minors' safety is a judgement a human must own.

## 2.5 The sweep itself: `urlwatch` over `changedetection.io`, and the COVID precedent

`changedetection.io` is the popular choice (~32.5k★, pushed today) and it is good. But for
terpsi I'd reach for **`thp/urlwatch`** (~3.1k★, active), for one structural reason:
urlwatch's watch list is **a config file you commit to the repository.** The set of authorities
terpsi depends on is not runtime state in a Docker volume — it is part of the design, it should
be reviewable in a pull request, and its history should be as durable as the thresholds it
watches. A watcher whose configuration lives only in a container's database is a ledger nobody
can audit. (`changedetection.io` remains the better fit if a non-engineer must maintain the
watch list, which is a real consideration for a programme run by a band director.)

**The precedent is the find here.** `COVID19Tracking/covid-tracking` (~105★, now archived) is
*an urlwatch configuration for monitoring US state public-health data pages.* A serious
public-health data project, under time pressure, reached for exactly this tool against exactly
this class of authority — government health pages that change without announcement. Its
companion `urlwatch-proxies` repo exists because some of those pages could not be scraped
without a headless browser, which is a useful advance warning about what monitoring
government health sources actually costs in practice.

Layer `lycheeverse/lychee` (~3.8k★) plus `lychee-action` underneath as the cheap daily
reachability probe over every citation in the docs, and the fleet's existing
`scripts/check_links.py` / `link-check.yml` shape — which §15 already says to adopt wholesale —
gets a faster, better-maintained engine without changing the design.

And per §0: whatever runs this must distinguish "gone" from "unreachable from here." My own
403s this morning are the argument.

## 2.6 The publishers — named, and explicitly not verified

The brief asked me to establish that authoritative publishers exist for the heat and noise
thresholds and to name them, while stating no numeric limits I had not fetched. **I fetched
none.** Every entry below is therefore recorded at `P4/P5` with `status: unverified —
egress-blocked 2026-07-30`, and the first task for whoever picks this up is to resolve each one
from a permitted network and record a content hash.

**Noise exposure.**
- **NIOSH** — *Criteria for a Recommended Standard: Occupational Noise Exposure, Revised
  Criteria* (the 1998 revision, DHHS/NIOSH publication numbered in the 98-1xx series). This is
  the recommended-exposure-limit authority in the US and the one that publishes a
  recommended exchange rate. The *fact of a 1998 revision* is itself the point: this document
  has a superseded predecessor, which is precisely why a citation needs a version.
  `cdc.gov` — 403 this session.
- **OSHA** — *29 CFR 1910.95, Occupational noise exposure*, the enforceable standard, with its
  permissible-exposure table. Two liveness affordances worth building against: `ecfr.gov`
  publishes **versioned XML with amendment dates through an API** (`/api/versioner/v1/...`),
  which is a machine-readable revision record rather than a page to scrape — the single best
  citation target in this whole report — and `osha.gov` mirrors the standard with its own
  amendment history. Both 403 this session.
- **ACGIH** — the TLV for noise, on a different exchange rate from OSHA per §1.4. Note that
  ACGIH TLVs are **copyrighted and sold**, which is a genuine problem for a citation model
  built on canonical URLs and content hashes: you may be able to cite it but not quote it, and
  the tuple needs a field for that.
- **EU** — *Directive 2003/10/EC* on noise at work (named by `hse-calculators`).
- **ISO** — *ISO 1999* (estimation of noise-induced hearing loss) and *ISO 9612* (determination
  of occupational noise exposure); *IEC 61672* (sound level meters), *IEC 61252* (personal sound
  exposure meters), *IEC 60942* (calibrators). All paywalled — same copyright caveat.
- **WHO/ITU** have a safe-listening standard aimed at recreational and personal-audio exposure,
  which is arguably a *better-matched* authority for adolescent musicians than an occupational
  standard is. Worth chasing; I could not reach `who.int`.

**Heat.**
- **NIOSH** — *Criteria for a Recommended Standard: Occupational Exposure to Heat and Hot
  Environments* (revised 2016, DHHS/NIOSH 2016-1xx series). Again, a revision with a superseded
  predecessor.
- **NWS / NOAA** — the **heat index** itself, with its published caution/danger categories, and
  its critical stated assumptions (shade, light wind) which are false on a practice field in
  full sun. NOAA also publishes a **WBGT forecast product** (which `HSSBoston/wbgt` consumes).
  `weather.gov` — 403.
- **ACGIH** — heat stress and heat strain TLVs, WBGT-based (cited by `hse-calculators` and
  named in `awesome-hse`, which also lists an ACGIH heat stress calculator and a CCOHS one).
- **ISO 7243** — the WBGT standard proper; **ISO 7933** — predicted heat strain. Paywalled.
- **The youth-athletics publishers, which are the right ones for this population** and which no
  repository in my haul cites: national athletic-trainers' and sports-medicine bodies publish
  position statements on exertional heat illness in secondary-school athletics, and **state high
  school athletic associations publish WBGT-based activity-modification policies that are
  binding on member schools** — several states mandate WBGT measurement and prescribe
  work:rest and hydration-break schedules by zone. For a school music programme these are
  simultaneously the best-matched guidance *and* very likely the applicable rule, and a
  district's counsel will look there first. `FedericoTartarini/tool-sma-extreme-heat-policy` is
  the only project I found that implements a sport-specific body's heat policy as code, and it
  is the model.
- **CCOHS** (Canada) — cited in `awesome-hse` as publishing a heat stress calculator.

**Youth-health baseline** (§12's explicit gap).
- **CDC YRBSS** — Youth Risk Behavior Surveillance System, the adolescent counterpart to BRFSS,
  which §12 correctly identifies as the obvious missing catalogue entry. Related CDC school-health
  instruments (School Health Profiles, SHPPS) sit alongside it.
- Tooling is genuinely thin, which corroborates the capability map's claim rather than
  contradicting it: the only interface I found is `gsimchoni/yrbss`, ~2★, untouched since 2022.
  **A dormant wrapper is not a baseline**, and per rule 20 it should be catalogued with a
  tombstone-shaped note if terpsi points at it.

---

## 3. Weirdest things I found

**1. A barking-dog dispute produced terpsi's noise architecture.**
`ChelseaKR/olive-bark-logger` was built so somebody could document a neighbour's dog without
recording their neighbour. That constraint — *log the level, never the audio* — is identical to
terpsi's constraint about recording minors, and it independently produced append-only
calibration with render-time offsets, mandatory limitations sections, and an explicit "this is
not a Type 1 or Type 2 meter." A residential noise complaint and a FERPA-governed youth
programme converged on the same design because they share one property: **the derived measure
is the record, and the raw signal is a liability.** That is the most directly transplantable
thing in this entire report and it came from the least likely place.

**2. Tax law solved threshold versioning, and safety software did not.**
`openfisca` stores a tax rate as a dated series with a description and a unit, and treats an
announced-but-unknown future change as a first-class `expected` state. `hse-calculators` — a
2026 library whose entire selling point is being "regulation-cited" — stores its heat and noise
thresholds as constants with the regulation's name in a prose doc. The domain where getting the
number wrong means a rounding error on a benefit payment has better provenance machinery than
the domain where getting it wrong means a child collapses on a field. There is no technical
reason for this; benefits software gets audited annually and safety handbooks get read once.

**3. NIST built a diff tool because normative documents get renumbered.**
`usnistgov/oscal-deep-diff` exists, is actively maintained, and does one thing: structurally
diff two revisions of a control catalog. The existence of that tool is an admission that
**generic text diff is inadequate for tracking authority revisions**, because the thing that
breaks a downstream citation is not usually a changed word — it is §5(b)(2) becoming §5(b)(3).
A liveness sweep that only fingerprints page content will report `match` on a document whose
paragraph numbering shifted underneath every citation pointing into it.

**4. Dairy cows have better-instrumented heat-stress research than high-school marching bands.**
`zerotonin/digimuh` does heat-stress *repeatability* analysis on dairy cattle — broken-stick
breakpoint estimation, profile-RSS confidence intervals, ICC(1,1) for
between-individual variation — and `guozitai/dairy-heat-anomaly-early-warning` runs deployed
early warning across eight commercial farms. Precision livestock farming has individual
heat-response variability as a *solved measurement problem* with statistical machinery attached,
because the economic loss is legible. The methodological transplant is real and slightly
horrifying: **individual variation in heat response is large, and a single field-level WBGT
threshold applied to a hundred students is a population average being used as an individual
decision.** The cows get individualised. Nobody has done this for kids, and terpsi's rule 6 is
what stops the obvious next step — ranking students by heat susceptibility — from being built.

**5. A Windows app for protecting your own ears from your own headphones implements the dose model.**
`Shadetail/HearingDose` taps the WASAPI loopback, estimates dBA at the ear, and tracks a daily
noise dose "with front-loaded log-time recovery." It is one person's recent project with zero
stars, and it is nonetheless the clearest small implementation I found of the thing that is
actually hard about hearing conservation: **dose is a cumulative integral with recovery, not a
level.** A trumpet section that hits a high level for eight minutes and a drumline that sits
just under a trigger for four hours are different exposures, and only a dose accumulator sees
the difference. A gamer worried about tinnitus wrote the accumulator; the ensemble-safety world,
by §12's own account, "almost nobody tracks" it.

*Runner-up, for the file:* `haklein/flashbee`'s description advertises "safety-critical
datasheet fixes" to a lightning detector, ported from an Instructables project. Somebody
found bugs in a hobbyist build of the device that tells you whether to leave a field. That is
both reassuring and not.

---

## 4. Four things I would do first

1. **Buy or build a black globe.** Tens of dollars converts terpsi's highest-liability
   threshold from `P3 Fitted` to `P1 Measured` (§1.5). Nothing else in this report has that
   return.
2. **Adopt `phonometry` and copy its conformance report.** A dated, committed artifact
   asserting which normative values the installed version reproduces is what makes a dB number
   survive a lawyer (§1.2, rule 19).
3. **Store thresholds as `openfisca`-shaped dated parameters with an OSCAL-shaped
   upstream/downstream link, in a Catala-shaped file that carries the quoted passage.** Then
   the CI check that fails when the quoted passage's hash diverges from the last sweep is the
   entire "flagged rather than silently stale" mechanism (§2.2–2.4).
4. **Resolve the publisher list in §2.6 from a permitted network and hash every one.** Until
   that happens every threshold in terpsi is `P5`, and this report says so rather than
   pretending otherwise.
