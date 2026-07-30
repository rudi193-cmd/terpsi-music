# Terpsi Music — Capability Map

**Status:** ideation sweep. Nothing here is committed scope; the point is to see the whole surface before choosing.
**Method:** enumerate everything a music program actually does, including the parts that currently live in spreadsheets, group texts, filing cabinets, and one person's memory.

A note on the shape of the domain: a "music program" is not one ensemble. A single high school program can simultaneously run marching band, indoor percussion, winter guard, three concert bands, orchestra, two jazz bands, chamber groups, pep band, pit orchestra for the musical, solo & ensemble, AP Music Theory, and a feeder relationship with two middle schools — under one director, one budget, and one calendar. Most tooling assumes one ensemble. **The multiplicity is the problem.**

---

## 1. Practice

The largest genuinely untapped surface, and the one that touches students daily. Everything else in this document is infrastructure around an hour a day of someone alone in a room with an instrument.

**Logging and accountability**
- Timer-based and self-reported practice logging
- The practice card, digitized — weekly minutes with guardian acknowledgment, replacing the signature ritual
- Streaks, goals, cumulative-hours milestones
- Practice as a graded component, with the log feeding the gradebook
- Guardian visibility without guardian surveillance — a distinction worth designing deliberately
- Session notes: what I worked on, what didn't improve, what I want help with

**Assigned and structured practice**
- Director- or tech-assigned passages with due dates
- Scale, rudiment, and etude check-off trees; all-state requirement tracking
- Long-tone, breathing, and stick-control routines with guided timers
- Sight-reading generator with difficulty scaling
- Assigned reference recordings and play-along/accompaniment tracks
- Slow-down and loop tooling for a specific hard passage
- Drone and tuning-tendency practice by instrument

**Recording and feedback**
- Submitted recordings against an assignment
- Pitch/rhythm accuracy analysis on submissions
- Longitudinal self-comparison: the same 16 bars in September and in May, side by side
- Asynchronous director/tech feedback anchored to a point in the student's own recording
- Peer review pairs and accountability partners
- Portfolio of best takes across a student's whole career

**Leverage:** practice plans generated *from adjudication and clinician commentary* (§8.1 of the architecture). A judge says something about the low brass at measure 112; every affected student's practice queue updates with that passage, that comment, and the audio of what the judge was reacting to. That closed loop is the single most defensible feature in this document — it makes the commentary primitive pay for itself and it is the thing no existing product does.

**An existing answer to the surveillance problem.** `ask-jeles`'s learning-event capture is off by default *every launch*, is never persisted across launches, and records only the shape of an activity — query class, hit count, citation count, answer length — never the content. Applied to practice logging that resolves most of the tension with UTETY's no-leaderboard rule: duration, passage, and self-rating are the work; a recording's contents and a ranked standing are not. Guardian visibility should be built on the same distinction.

> **One caution from how that plays out in practice.** Those events land in `~/.willow/jeles_learning_events/`, and `~/.willow` is a tracked git repository with a remote — so a `jeles_learning_events/` directory appears in its committed tree. Consent scoped to *this session* has produced a permanent, pushed history. The capture design is right; the storage location quietly outlived it.
>
> The lesson for practice logs, which are the same shape and about minors: **decide the retention of consented data at the same moment you decide the consent.** A session-scoped grant whose output lands somewhere durable and replicated is not a session-scoped grant. Write practice and activity data to a path explicitly excluded from version control, and from any backup replication outliving the consent window.

**Physical practice**
- Practice room booking, occupancy, and utilization analytics
- Sectional scheduling, attendance, and student-led sectional plans

---

## 2. Assessment

- Playing tests: assignment, recording, rubric scoring, return
- Rubric authoring and reuse across ensembles
- Written theory quizzes and ear training
- Standards-based grading alignment; participation and attendance components
- Gradebook sync to the SIS (PowerSchool, Infinite Campus, Skyward) — one-way, gated
- Chair auditions and challenge systems
- **Blind evaluation** — identity stripped from recordings before judges see them, restored after scoring
- Multi-judge score reconciliation and outlier flagging
- Sight-reading assessment
- Self-assessment and reflection prompts; peer assessment
- Ensemble-level assessment: how is the *group* doing on this piece, by section
- Multi-year growth arcs — a student from sixth grade to senior year in one view
- Make-up and retake workflow
- Progress reporting to guardians

**Question banks have a settled workflow.** `civics-check` keeps authoritative JSON under `data/sources/`, compiles it to a catalog, and states the rule plainly: *never hand-edit the compiled output.* Theory quizzes, sight-reading item sets, and scale requirements all want that shape — edit the source, rebuild, test — rather than a database somebody maintains by hand.

---

## 3. Scheduling, Calendar, Attendance

The highest-frequency pain and the highest-frequency source of family conflict.

**Attendance**
- Rehearsal, sectional, and performance attendance; QR/NFC check-in, roll, or geofence
- Excused/unexcused policy engine with configurable rules
- Absence requests with reason, documentation, and approval chain
- Appeals workflow
- Attendance patterns as an early-warning signal (§19)

**The conflict problem**
- Multi-activity students: band + soccer + theater + robotics + a job
- Shared-student negotiation with athletics and drama — the recurring interdepartmental fight
- Religious observance conflicts (Friday-night football and Shabbat; band camp inside Ramadan)
- IEP/504 service pull-outs
- **Rotating pull-out lesson scheduling** so a student never misses the same academic class twice — a genuinely hard constraint-satisfaction problem that directors currently solve by hand on graph paper
- Course-scheduling advocacy: data showing which academic conflicts are costing enrollment, aimed at counselors

**Calendar**
- Publish/subscribe (iCal) into family calendars
- Call time vs. downbeat vs. dismissal as distinct fields — conflating them causes real chaos
- Change propagation with tiered notification; weather-driven changes
- Multi-day itineraries; band camp and two-a-day schedules
- A/B day and block-schedule awareness
- Countdown planning backward from a competition date

**Booking and assignment**
- Facility booking: band room, auditorium, practice field, stadium, cafeteria
- Field conflicts with athletics — the perennial territorial dispute
- Clinician visit scheduling against the rehearsal calendar
- Private/studio lesson scheduling with outside teachers
- Chaperone and volunteer shift signup with skill matching (CDL, first aid, sewing, truck driving)
- Availability polling for staff and volunteers

**Rehearsal planning**
- Block plans (15 warm-up / 30 opener / 20 closer), templated and reusable
- Plan vs. actual: what did we intend to rehearse, and what did we get to
- Rehearsal efficiency analytics across a season
- Set lists and run order

---

## 4. Music Library

- Full catalog: title, composer, arranger, publisher, grade level, duration, instrumentation
- **Physical location** down to cabinet and drawer number
- Part-level inventory — do we actually have all eight second clarinet parts
- Missing-part tracking, reprint authorization, purchase records with PO numbers
- **A citable-source backend already exists.** `jeles-remote` fronts ~65 institutional APIs — Library of Congress, Crossref, Internet Archive, Chronicling America, Europeana, plus a specialty long tail that explicitly includes **music** — and pointedly excludes Wikipedia from its defaults because *"results here are meant to be citable in an academic bibliography."* That is the right posture for programme notes, composer research, and public-domain determination, and it pairs with the `status` + `observed` liveness discipline the `P2` rung needs.
- **Copyright and licensing status**, tracked as a first-class field
- Performance rights reporting (ASCAP/BMI/SESAC) for concerts
- Sync/mechanical licensing for anything posted publicly — the gap that produces takedowns
- **Custom arrangement permissions** for marching shows, which programs violate constantly and unknowingly
- Commission management: composer, contract, milestone deadlines, payments, premiere rights
- Rental music with return dates and late-fee exposure
- Digital scores and parts with per-student distribution and personalized watermarking
- Director's score markings pushed to student parts
- Programming history — have we played this in the last five years, and which current students were here
- **Four-year repertoire rotation planning** so no student repeats a piece
- Instrumentation gap analysis: can this ensemble actually play this chart with two bassoons and no oboe
- Cross-cue and adaptation notes for missing instruments
- Difficulty calibration against measured ensemble ability
- Folder assignment, return check, lost-music fees
- Program notes and composer bios for printed programs

**Digitizing the filing cabinet has a built pipeline.** `nest-seed` walks a folder, extracts text by type (OCR for scans, `pdfplumber` for PDFs), and classifies by *meaning* through a three-tier cascade — regex facts, then local embeddings matched to category centroids where the similarity score *is* the confidence, then a generative model **only on the ambiguous tail**, handed the embedding's top candidates as a constrained choice. Every tier degrades gracefully when its model is absent. For a library of scanned scores and parts on a modest hub, that cost discipline is the difference between a weekend job and an unusable one.

---

## 5. Inventory — Instruments and Equipment

**School instruments**
- Catalog with serial numbers, purchase date, value, and condition history
- Assignment with photographic condition documentation at issue and return
- Repair tickets: vendor, cost, turnaround, warranty
- Per-instrument repair history — identifying the horn that is a money pit
- Loaner tracking during repairs
- Depreciation and replacement-cycle planning; insurance schedules and claims
- Summer checkout agreements
- Usage rotation to spread wear
- Barcode/QR/RFID tagging; annual audit workflow; missing-instrument escalation
- Damage fee assessment with an appeal path

**Everything that is not a band instrument**
- Percussion: timpani, marimbas, vibes, concert bass, gongs, traps, heads, mallets, sticks
- Marching: harnesses, carriers, shakos, plumes, gauntlets, gloves
- Guard: flags, silks, poles, rifles, sabres, tape, weather covers
- Electronics: mics, mixers, amps, DIs, cables, batteries, synths, subs, playback rigs
- **Cable and battery tracking**, which sounds trivial and is the single most common day-of failure
- Props, set pieces, and their construction/storage/transport
- Trailer and truck: load diagrams, load lists, maintenance, registration, insurance
- Field equipment: yard markers, ladders, scaffolding, pylons, tarps
- Podiums, shells, chairs, stands, stand lights
- Golf carts, gators, tool kits, first aid kits
- Consumables with reorder thresholds: reeds, valve oil, cork grease, drum heads, gaff tape

---

## 6. Uniforms and Attire

- Piece-level catalog (jacket, bibs, shako, gauntlets, shoes, gloves) rather than one "uniform" record
- Sizing, alteration, and hemming records — students grow four inches between seasons
- Issue/return with condition; cleaning schedule and vendor management
- Alteration queue and uniform-crew volunteer coordination
- Concert attire: tuxedos, dresses, all-black policies, and the inclusive-options question
- **Attire policy and gender presentation** — needs an explicit, humane design rather than an accidental one
- Guard costumes, typically custom per show
- Show shirts and spirit wear ordering with size collection
- Size-inheritance planning year over year
- Pre-performance inspection checklists
- Personal-item tracking: shoes, gloves, socks, black socks specifically, the eternal pre-show panic
- Garment bag assignment; lost/damage fees

---

## 7. Finance

**Student-facing**
- Fee schedules by ensemble and activity; per-student ledger and running balance
- Payment plans, installments, and automated reminders
- Tokenized online payment (no card data in the system, ever)
- **Invisible financial aid** — waivers and scholarships applied so that no student, and no other family, can tell who is on assistance. Dignity is a design requirement, not a nicety.
- Anonymous hardship application with a director-only queue
- **Total cost transparency**: the real all-in cost of a season stated up front, before commitment

**Fundraising**
- Campaign management, per-student credit accounts, product distribution logistics
- The IRS constraint on individual fundraising accounts in 501(c)(3) boosters — a genuine legal minefield the software should steer around rather than into
- Concessions, ticket sales, program ad sales, sponsorship tiers
- Donation tracking, acknowledgment letters, tax receipts

**Institutional**
- Three-way reconciliation: district account, activity account, booster account — **`Nestor`'s `Reconciler` is this, already built**: a figure checked against a human-sealed baseline with absolute and percentage tolerance, reporting variation and flagging deviations, every seal and check landing in a hash-chained ledger. Substitute "ceiling" for "trip account balance" and the example runs unchanged.
- Purchase orders and approval chains; vendor invoices and payment tracking
- Multi-year budget planning by category; capital replacement planning
- Grant discovery, application, and reporting
- Contractor payments for techs and clinicians, 1099 tracking, honoraria
- Entry fees, travel deposits, refund policy when a student quits after commitment
- **Audit trail sufficient to survive a booster treasurer turnover** — annual volunteer turnover destroys institutional memory, and embezzlement in booster organizations is common enough to design against
- Treasurer handoff packet, generated

---

## 8. Travel

- Itinerary building: lodging, meals, transport, timing
- Permission forms, medical releases, passport/ID tracking for international travel
- **Rooming lists** with constraint rules: grade, gender, requested roommates, staff adjacency
- Bus assignments and manifests
- **Head counts at every transition**, reconciled against the manifest — the thing that actually keeps directors awake at night
- Chaperone ratios, assignments, and emergency packets
- Medication administration on trips: nurse delegation, controlled substances, dosing logs
- Dietary restrictions and allergy management through every meal
- Room keys, curfew checks, incident reporting
- Charter contracts, driver hours, vehicle compliance
- Luggage, equipment, and uniform transport manifests
- Weather contingency and emergency action plans; reunification procedure
- Bus location visibility for families — with an explicit privacy tradeoff decision, since it is also a live location feed for a bus full of minors
- Return-time notification ("thirty minutes out")
- Trip accounting and reconciliation
- **Alternative programming for non-traveling students**, which is both an equity issue and a supervision requirement

---

## 9. Competition and Performance Operations

**Season**
- Competition calendar, registration, entry fees
- Circuit rules compliance: member counts, prop dimensions, electronics rules, time limits
- **Timing violation tracking** — an avoidable and expensive penalty category
- Performance order, draw, warm-up block scheduling, gate and hold-area movement plans
- Equipment truck arrival and load-in windows

**Adjudication** (builds on the commentary primitive)
- Judge sheet ingestion; caption and sub-caption breakdowns
- Score progression across a season; comparison against other units
- Recap analysis and caption-level growth trends
- Commentary archive, searchable across seasons
- Multi-angle video capture, synchronized to commentary and score position

**Design and execution**
- Show design versioning: drill revisions, music cuts, effect changes
- Drill chart distribution; per-student coordinate lookup; digital dot books
- Set-by-set rehearsal marking and cleaning tracking
- Show timeline aligning music, visual, and effect
- Pit setup diagrams, load-in sequences, cable runs
- Sound check settings per venue; wind and weather logs
- Prop and costume reveal timing

**Concerts**
- Program printing, proofing, and personnel lists generated from the roster
- Stage setup diagrams and riser configurations per piece
- Livestream operations; recording rights and distribution
- Concert etiquette information for families
- Awards and placement history

---

## 10. Auditions

- All-state, all-district, and region audition management
- Per-instrument etude and scale requirements, published and tracked
- Registration, fees, deadline cascades
- Recording submission with retake policy
- **Blind evaluation** with identity restoration after scoring
- Multi-judge panels, score reconciliation, ranking, and seating results
- Chair placement and challenge processes
- Drum major, section leader, and captain auditions including interview and teaching components
- Guard and percussion auditions with movement evaluation
- College audition tracking: prescreens, repertoire, deadlines, travel
- Honor band applications, recommendation letter requests, scholarship auditions

---

## 11. Recruitment and Retention

- Feeder pipeline tracking from elementary through middle school
- Instrument demonstrations, petting zoos, recruitment events
- Instrument fitting and aptitude assessment; matching beginners to instrumentation needs
- Rental coordination with local dealers
- **Enrollment projection by year**, which drives staffing, budget, and repertoire feasibility
- **Attrition analysis: who leaves, when, and why** — usually the ninth-grade transition and usually a schedule conflict
- At-risk flagging on attendance, practice, engagement, or balance signals
- Re-engagement workflows and structured check-ins
- Sibling and family-history tracking; multi-year cohort views
- Alumni network, alumni band events, senior recognition

---

## 12. Health and Safety

- Medical forms, allergies, conditions, medications, emergency instructions
- Emergency action plans per venue and per activity
- **Heat index monitoring with mandated water breaks** — the highest-liability part of band camp
- Hydration tracking; heat illness protocols
- **Hearing conservation and dB exposure monitoring** — a real, documented occupational risk in ensembles that almost nobody tracks
- Repetitive strain and load-related injury, especially percussion and marching
- Concussion protocol and athletic trainer coordination
- Injury accommodation: marching in a boot, alternate assignments, drill adjustment
- Instrument sanitation and shared-mouthpiece hygiene
- Mental health resources, referral pathways, performance anxiety support
- Lightning and severe weather protocols, field evacuation, shelter plans
- Bus incident procedures
- Mandated reporting workflows — handled with extreme care around who sees what
- **Anonymous concern reporting** for hazing and harassment
- Rookie/veteran culture monitoring; hazing prevention
- IEP/504 accommodations translated into a music context
- Adaptive instruments and inclusive participation planning

**There is no youth-health baseline in the fleet, and this is the section that most needs one.** `almanac-data/health-almanac` holds seven entries — CDC BRFSS, WONDER, PLACES, FluView, the CDC data portal, CMS, and WHO GHO — and **none of them cover schools, minors, youth, or student populations.** The obvious counterpart to the adult-focused BRFSS is CDC's youth surveillance programme, and it is not catalogued; neither is any occupational noise-exposure or heat-illness authority.

That matters more here than in most sections, because two of the items above are **numeric safety thresholds**: at what heat index water breaks become mandatory, and at what dB exposure and duration hearing conservation is triggered. A program that writes those numbers into a handbook is making a safety claim on a minor's behalf, and an uncited threshold is a `P5` assumption (§15 of the architecture) sitting in a policy that a district's counsel may one day read closely.

So this is a cataloguing job before it is a software job: the noise-exposure limit, the heat-index protocol, and the youth-health baseline each need a named publisher, a canonical URL, and a `status` + `observed` record on the almanac's daily sweep — so that when a guideline is revised, the handbook that cites it is flagged rather than silently stale.

---

## 13. Academics, Eligibility, Compliance

- Eligibility checking against grades and attendance, pulled from the SIS
- Probation, appeal, and study-hall requirement tracking
- Tutoring coordination for at-risk performers
- Credit tracking: fine arts requirement, PE waiver for marching band
- Instructional-minutes documentation
- Standards alignment and evidence collection for program review
- Teacher evaluation evidence (student growth data)
- **Volunteer background check tracking with expiration alerts** — legally required, universally chaotic
- Mandated training completion: bloodborne pathogens, heat safety, Title IX, transportation
- Staff and contractor agreement management
- Booster bylaws, filing calendar, and compliance deadlines
- State and federal reporting

---

## 14. Communication

- Segmented announcements by audience with acknowledgment tracking
- Urgency tiering across push, SMS, and email; emergency broadcast
- **Translation for multilingual families** — the most commonly missing feature in this category and a genuine access barrier
- Weather and cancellation cascades
- Guardian help desk and Q&A
- Staff-only and section-leader channels
- Student-to-student communication with appropriate supervision and retention — a safeguarding design problem, not a chat feature
- Communication logs sufficient for FERPA disclosure records
- Newsletter generation from the calendar and roster
- Public site content: concert dates, ticket links, directions
- Social media asset generation with **consent-filtered photo selection**
- Handbook distribution with acknowledgment
- Board agendas and minutes; alumni and donor communications

---

## 15. Clinicians, Staff, Professional Development

- Clinician roster with specialties, rates, and availability
- Booking, contracts, honoraria, and travel reimbursement
- **Pre-visit briefing packet**, generated: what to work on, current recordings, roster, prior commentary
- Post-visit commentary capture flowing into the same primitive as adjudication
- Follow-up assignments auto-generated from clinician notes into student practice queues
- Clinician effectiveness tracked over time — did the thing they worked on actually improve
- Masterclasses, residencies, guest artists
- **Studio teacher network**: private lesson teachers coordinated with the program, with structured progress sharing in both directions
- Staff PD tracking, certifications, conference attendance
- Tech onboarding materials and evaluation

---

## 16. Student Leadership and Culture

- Leadership applications, interviews, rubrics, and selection
- Leadership curriculum and training modules
- Section leader tooling: their section's attendance, sectional planning, peer feedback
- Mentorship pairing between veterans and rookies
- Goal setting and structured reflection
- Service hours; Tri-M points and requirements
- **Letter and pin criteria tracking** — the band letter point system, currently a shoebox of index cards
- Banquet planning, senior recognition, superlatives
- Culture and climate surveys; anonymous feedback to staff
- Section identity and tradition documentation

---

## 17. Administration and District View

- Multi-school rollup for a fine arts director or district administrator
- Enrollment trends and projections across the district
- **Program equity analysis** — which schools have which resources, staffing, and facilities
- Cost per student; budget comparison across programs
- Facility utilization
- **Participation demographics against school demographics** — the gap analysis that reveals who is not in the program
- Free/reduced-lunch participation rates in fee-based activities, which is where cost barriers become visible
- Outcome data: retention, achievement, post-secondary music participation
- Advocacy dashboards built for board presentations, not for administrators
- Grant opportunity matching; district-wide capital replacement planning
- Substitute and emergency coverage for a specialized role that is hard to sub

---

## 18. Equity and Access

Cross-cutting, and worth stating separately because it is usually an afterthought that shows up as an accidental exclusion.

- Fee waivers that are structurally invisible to peers
- Instrument lending prioritized by need rather than by who asked first
- Transportation assistance for students without a ride to a 6 a.m. call
- Meal provision at long rehearsals for students who would otherwise not eat
- Language access across every parent-facing surface
- Adaptive participation pathways
- Identification of scheduling conflicts that disproportionately affect specific student populations
- Anonymous need identification, so a student never has to ask publicly

---

## 19. Insight and Assistance

All of this runs behind the egress gate on local models, since nearly every input is `PII_MINOR` or `MEDIA_MINOR`.

- Natural-language query for directors: "who hasn't turned in a physical," "who owes more than $200 and hasn't set up a plan"
- **Practice plans generated from adjudication and clinician commentary** — the flagship loop
- Score progression forecasting and caption-level trend analysis
- Attendance and engagement risk prediction, surfaced as a check-in prompt rather than a flag
- Instrumentation gap forecasting to inform repertoire selection two years out
- Repertoire recommendation calibrated to measured ensemble ability
- Budget and enrollment forecasting
- Rehearsal and meeting summarization
- Commentary summarization sliced by section
- Longitudinal growth narratives for conferences, drafted from real data
- Program notes and newsletter drafting
- Schedule conflict detection and proposed resolutions
- Anomaly detection: a student whose practice and attendance both drop is a human being to check on, not a metric

---

## 20. Lifecycle and Edge Cases

The section that separates software written by someone who has run a program from software written from a feature list.

**Roster churn**
- Mid-year transfer in and out
- **A student quits mid-season** — uniform return, fee proration, equipment recovery, and a hole in the drill
- **Drill rewrites when someone leaves**, propagating to every affected coordinate sheet
- Injury mid-season requiring alternate assignment
- Instrument switching mid-year
- Doubling students playing different instruments in different ensembles
- Students in multiple ensembles with structurally conflicting rehearsals
- Homeschool and co-op participants
- Open-enrollment and cross-district students
- Fifth-year seniors and age-out rules

**Family situations requiring care**
- **Custody arrangements**: which guardian receives which notification
- **Court orders restricting contact** — a safety issue where a bug is a serious harm, and the reason guardianship must be individually revocable edges
- Estranged or no-contact parents
- Confidential address programs (Safe at Home)
- Foster placement changes mid-year
- Students experiencing homelessness under McKinney-Vento: fee waiver, transport, instrument storage
- Undocumented families and the ID requirements of travel
- **Chosen name and pronouns** distinct from the SIS legal record, handled deliberately, including what appears on a printed concert program

**Operational disasters**
- Weather cancellation cascading into forty downstream plan changes
- Bus or equipment truck breakdown
- Judge or clinician no-show; venue change day-of; power failure at a competition
- Instrument stolen or damaged at an away event
- Rain-shortened competition and its rating implications
- Copyright takedown of a posted performance video
- Staff departure mid-season; director on extended leave with a long-term substitute
- Fundraiser vendor failure
- Booster financial irregularity
- A pandemic-style shutdown and the remote fallback

**Data and institutional**
- FERPA records request from a guardian, with a 45-day clock
- Litigation hold
- Data breach response and notification obligations
- Graduation: disposition of a student's records, recordings, and portfolio
- Alumni requesting archived performances years later
- **The death of a student** — bereavement, memorial, and the handling of their records and their seat, which programs do face and which no software handles gracefully
- Program dissolution, school closure, or district merger

---

## 24. Composition and Craft Feedback

> **Numbered last, placed here on purpose.** It belongs beside §2, and inserting it there would renumber twenty-one sections and break every reference in three documents. Appended rather than inserted; the number records when it arrived, not where it sits.

The twenty-three sections above are about **performing** music. None is about writing it. That is a third of the domain missing — Create, alongside Perform and Respond — and it covers AP Theory composition assignments, arranging, the student who writes the pep-band chart, and the kid with a notebook of lyrics nobody has ever given feedback on.

**It is a teaching instrument that happens to work by diagnosis.** That distinction is the whole design and it is easy to lose.

A critic reports defects. What this does is deliver the lesson **at the only moment it can land** — when the student already cares, because it is their line, in their song, and they are stuck on it now. Motivation is the scarce resource in music education and the task supplies it for free. Most tooling in this space bolts a lesson onto a task; here the task is the delivery vehicle, and the pedagogy is not a companion module.

The literature has been settled on this for decades and music software has largely ignored it: scaffolding within the zone of proximal development; cognitive apprenticeship, which makes expert *thinking* visible rather than only its output; Hattie and Timperley's finding that task-level and process-level feedback work while praise does not; and productive failure — let the student get it wrong first, because the attempt is what makes the explanation stick. Order matters. Teach before the attempt and it is a lecture.

It does not write the song and it does not grade it.

**Lyric diagnosis**
- Prosody: where natural speech stress lands on a weak beat, which is the single most common defect and the least visible to the writer
- Structure: section lengths, how long the hook is withheld, whether the final chorus varies or repeats
- Line-count parity — even groups resolve, odd groups propel — and whether that matches the section's intent
- Rhyme scheme and rhyme *type*: perfect closes a section, slant leaves it open, and all-perfect reads as nursery rhyme
- Concreteness: the ratio of sensory detail to stated abstraction, per section
- Singability: closed vowels on long or high notes, consonant clusters at speed

**Music diagnosis**
- Melodic contour: range, where the peak sits, whether it is approached or stumbled into
- Motivic development — one idea examined from several angles, or four unrelated ideas
- Voice leading in a student's harmonization, which is the skill nobody notices until it is wrong
- Repetition analysis: state, restate, depart
- Tension placement against the sections that are supposed to carry it

**Revision is the actual product**
- Draft-to-draft diff, because the revision is where the craft lives and the first draft never is
- "What changed and did it help" — the question a teacher asks and has no time to ask thirty times

**The mechanic: flag, then let the student declare intent**

Not flag-and-fix. Half of these rules are not laws, they are descriptions of a tradition, and the good songs break them deliberately. **The tool cannot tell an error from a choice** and must stop pretending it can.

> *Line 3 — "because" is stressed BE-cause against the beat here. Usually a mistake. Sometimes deliberate.*
> → `I'll fix it` · `I meant it, and here is why`

That turns the limitation into the best assessment signal in the system. **Whether a student can say "I know, I meant it" — and defend it — is a better measure of craft than whether the line follows the rule.** It is also the question a teacher grading thirty songs never has time to ask, and the answer is precisely what they want to know. The declaration is the artifact worth keeping, not the corrected line.

**Fading is mandatory, and the success metric is inverted**

A scaffold that never withdraws manufactures dependency, which is the opposite of teaching. If this flags the same stress mismatch in draft forty that it flagged in draft one, it has **failed while working perfectly.**

So the measure is not defects found. It is **defects the student caught before the tool did, trending up** — and the tool's goal is its own obsolescence, one student at a time. Worth stating as a design target because every incentive in software points the other way.

The related trap is the expertise reversal effect: worked examples help novices and actively harm people who have internalised the thing. Explaining prosody to a student who now hears it makes them worse at the task, not better.

**Hard constraints, all of them already specified elsewhere**
- **Diagnose, never score.** *"Line 3's stress falls on a weak beat"* is checkable and true whether or not the song is any good. A quality score is the thing with a documented record of failing at scale, and it would be poison in a classroom regardless.
- A craft note is **commentary anchored to a position** — §8.1 of the architecture already models this, and a measure number or a line number is the same primitive as a judge's remark at bar 112.
- A machine critique is a **`draft` until a named human seals it** (§8.2 of the architecture). It may inform a teacher; it is never shown to a student as a teacher's judgment.
- **No comparison between two students, ever.** W-7 in §7.4 of the architecture: the system presents, a human decides. No ranking of whose song is better, in any surface, under any grant.
- Local inference only. A student's unfinished song is `MEDIA_MINOR` and `PII_MINOR` at once.
- **Scaffolds do not fade by themselves.** W-5 in §7.4 of the architecture — *agency grows by signature, never by drift; a clean track record is evidence for a proposal, never a grant in itself.* Dropping a student's hints because their record looks good is exactly drift. The system surfaces the case — *this student has caught their own prosody four drafts running, consider reducing the hints* — and a teacher signs it. Slower, and correct, and it keeps the teacher in a loop that adaptive software otherwise quietly removes them from.
- **The rules are Anglo-American popular song craft, and the tool must know that.** Stress-timed prosody does not transfer to a syllable-timed language. Flagging a Spanish or Mandarin lyric against English stress rules is not a limitation, it is a wrong answer delivered confidently to a child. §18's language-access requirement bites harder here than anywhere else in this map, and a rule set that cannot name the tradition it encodes should refuse rather than guess (§6 of the architecture — absence surfaces as unknown, never as a result).
- **Homogenisation is the failure mode nobody will notice.** Thirty students corrected toward the same tradition write the same song. The declare-intent mechanic is the only defence in the design, which is thin, and it should be watched rather than assumed sufficient.

**Most of the substrate exists and is open.** `music21` for symbolic analysis, ChoCo for harmony, WASABI and LyricSense for lyric corpora, Essentia and `librosa` for audio. The pedagogy is formalized — Pattison's prosody and object writing have been taught at Berklee since the 1970s — and the cognition has a research program in Huron's ITPRA model of expectation. What is missing is the wiring: the taught rule has never been connected to the corpus that could check it, and the generation tools went from blank page to finished track without stopping to build the critic. **This is the part that does not exist yet, which is the only reason it is worth building here.**

---

## 21. Persona index

| Domain | Student | Guardian | Staff/Tech | Director | Clinician/Judge | Admin/District |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Practice | ●●● | ●● | ●● | ●● | ● | |
| Assessment | ●●● | ●● | ●● | ●●● | ● | ● |
| Scheduling | ●●● | ●●● | ●● | ●●● | ● | ● |
| Library | ● | | ●● | ●●● | | ● |
| Inventory | ●● | ● | ●●● | ●●● | | ● |
| Uniforms | ●● | ●● | ●●● | ●● | | |
| Finance | ● | ●●● | | ●●● | | ●● |
| Travel | ●● | ●●● | ●●● | ●●● | | ● |
| Competition | ●●● | ●● | ●●● | ●●● | ●●● | |
| Auditions | ●●● | ● | ●● | ●●● | ●●● | |
| Recruitment | | ● | ● | ●●● | | ●●● |
| Health/Safety | ●● | ●●● | ●●● | ●●● | | ●● |
| Compliance | ● | ● | ● | ●●● | | ●●● |
| Communication | ●●● | ●●● | ●● | ●●● | ● | ● |
| Clinicians | ●● | | ●● | ●●● | ●●● | |
| Leadership | ●●● | ● | ●● | ●●● | | |
| District view | | | | ●● | | ●●● |
| Insight | ● | | ●● | ●●● | | ●● |

---

## 22. Where the leverage actually is

Most of this list is table stakes — necessary, unglamorous, and already served (badly, expensively, in five disconnected products). A smaller set is genuinely differentiating:

1. **Commentary → practice loop.** Judge or clinician feedback becomes individual practice assignments automatically. Nothing on the market does this, and it is only possible because commentary is modeled as an anchored primitive rather than a PDF.
2. **One program, many ensembles.** Existing tools assume one group. The multiplicity — a student in marching band, jazz band, and the pit orchestra with three conflicting calendars — is the actual daily experience.
3. **The rotating pull-out scheduler.** A hard constraint problem that directors solve by hand, that software solves well, and that saves hours every single week.
4. **Longitudinal student arcs.** Six years of recordings, commentary, and growth in one view. Impossible when data lives in five vendors' silos and gets deleted at graduation.
5. **Copyright and licensing as first-class data.** An unglamorous liability that programs carry unknowingly and that no tool tracks.
6. **Equity mechanics built in.** Invisible waivers, need-based lending, cost transparency. Design decisions, not features, and impossible to bolt on later.
7. **Institutional memory across volunteer turnover.** Boosters turn over annually; the treasurer handoff and the audit trail are the difference between continuity and an annual restart.
8. **Genuine offline operation.** Stadiums and buses have no signal, and that is exactly when the roster and headcount matter most.
9. **Local-only sensitive processing.** Commentary transcription, recordings of minors, medical data — a privacy posture that is architecturally true rather than promised in a policy page.
10. **Handling the hard human cases well.** Custody restrictions, chosen names, homelessness, bereavement. Programs remember which tools made a terrible week worse.

---

## 23. Notes toward sequencing

Not a roadmap — an observation about dependency. Practice, assessment, and commentary form one coherent cluster that delivers value to students and directors immediately and depends on very little. Finance, travel, and compliance form a second cluster that is higher-stakes, more regulated, and more painful to get wrong. Inventory and library are largely independent and can arrive whenever. The district view is meaningless until several programs exist on one hub.

Whatever the first module is, the foundation list from the architecture (§9) still holds: relationship graph, classification, envelope, egress broker, audit log. Every capability above assumes those exist.
