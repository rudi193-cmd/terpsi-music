# Craft sources — what §24 claims already exists, and how weak the evidence is

**Status:** citation record. Governs nothing.

§24 of the capability map asserts that most of the substrate for a craft-feedback
tool already exists and names a dozen things. Naming a source without recording
what was read, when, and how well is exactly the `P2` defect §15 of the architecture spends a page
on: *a citation whose source has been deleted is a `P5` assumption still wearing
a `P2` label.* This file is the record that assertion needs.

**A bare `§N` here means `docs/CAPABILITY-MAP.md`**, because this file's
subject is that document's §24. References to the architecture are named.

---

## How these were actually read, which matters more than the list

**Every entry below was read as a web-search result summary on 2026-07-30. Not
one primary source was opened.** No paper was read, no repository was cloned,
no dataset was downloaded, no figure was reproduced.

In §15 of the architecture's register that is **weaker than `P2 Cited`** — the rung assumes a
resolvable reference with a named publisher, and what is recorded here is a
search engine's paraphrase of one. Call it cited-at-one-remove. The URLs are
recorded so a later reader can do the thing this session did not, and the
quoted claim is recorded beside each so the entry survives its link rotting,
which is that section's minimum bar.

**The consequence for §24 is specific and small.** The claim *"the substrate
exists"* is well supported at this strength. The claim *"the alignment between
lyric and symbolic-music corpora is thin"* is **not** — it is an absence
inferred from four searches, and absence is the hardest thing to establish this
way. §24 states it as the argument for building the seam. If someone has
already built it, that argument collapses, and finding out is one afternoon of
literature search by someone who reads the papers.

---

## Pedagogy

| Claim | Source | Read |
|---|---|---|
| Pat Pattison has taught lyric writing at Berklee since 1975 and helped develop the first college-level songwriting degree; object writing is his invention; his Coursera course has enrolled over 1.3 million students since 2013 | [Wikipedia](https://en.wikipedia.org/wiki/Pat_Pattison), [Berklee Online](https://online.berklee.edu/instructors/pat-pattison) | summary only |
| Prosody is "the right relationship between form and content," traced to Aristotle; all elements working together to support the song's central message | [Berklee Online — Prosody in Music and Songwriting](https://online.berklee.edu/takenote/prosody-in-music-and-songwriting/) | summary only |

**This is the direct source of six of the eight checks in `craft/`.** Worth
recording plainly: the package encodes a named pedagogy, not a general theory
of song, and §24's warning that the rules are Anglo-American popular-song craft
follows from exactly this.

## Cognition

| Claim | Source | Read |
|---|---|---|
| Huron's ITPRA theory: five functionally distinct response systems — reaction, tension, prediction, imagination, appraisal — with syncopation, cadence, meter, tonality and climax analysed as devices exploiting them | *Sweet Anticipation*, [MIT Press](https://direct.mit.edu/books/monograph/1961/Sweet-AnticipationMusic-and-the-Psychology-of) | summary only |

## Corpora

| Claim | Source | Read |
|---|---|---|
| `music21` — toolkit for computer-aided musicology; core corpus includes 383 chorales; `chordify` reduces polyphony to chords | [Tymoczko's MTO review (PDF)](https://dmitri.mycpanel.princeton.edu/music21.pdf) | summary only |
| ChoCo integrates harmonic data from **18 sources** across Harte, leadsheet, Roman-numeral and ABC representations | [Scientific Data](https://www.nature.com/articles/s41597-023-02410-w) | summary only |
| WASABI — 1.73M songs with lyrics, 1.41M unique, annotated for structure segmentation, topics, explicitness, salient passages and emotion | [GitHub](https://github.com/micbuffa/WasabiDataset) | summary only |
| LyricSense — 10,000 songs, 1,000 manually annotated, English / French / Mandarin / Hindi | [UBC MDS](https://masterdatascience.ubc.ca/why-data-science/data-stories/lyricsense-multilingual-song-lyrics-corpus) | summary only |

**LyricSense's multilingual scope is load-bearing for §24's language limit.**
The constraint that stress-timed prosody rules must not be applied to a
syllable-timed language needs a corpus that is not English-only to be
addressable at all.

## Analysis

| Claim | Source | Read |
|---|---|---|
| Essentia — open-source C++ audio analysis library with Python bindings; ACM Multimedia open-source award, 2013 | [essentia.upf.edu](https://essentia.upf.edu/), [GitHub](https://github.com/MTG/essentia) | summary only |
| ISMIR maintains a catalogue of MIR software tools; MIREX is the shared evaluation framework | [ISMIR software tools](https://ismir.net/resources/software-tools/) | summary only |

## The negative result

| Claim | Source | Read |
|---|---|---|
| Hit Song Science — term coined by Mike McCready, trademarked by Polyphonic HMI. Early studies claimed ML could learn popularity from audio; **a larger-scale evaluation contradicted this**, finding popularity cannot be learned effectively from known audio features. Still contested in the MIR community | [Wikipedia](https://en.wikipedia.org/wiki/Hit_Song_Science), [arXiv 2301.13507](https://arxiv.org/pdf/2301.13507) | summary only |

**This is the single most load-bearing citation in §24**, because *diagnose,
never score* rests on it. If the negative result is weaker than summarised —
or has been overturned since — the case against a quality score becomes a
design preference rather than a finding, and §24 should say so instead. **Read
this one first.**

## Generation

| Claim | Source | Read |
|---|---|---|
| Suno and Udio lead full-song generation as of 2026; Warner and UMG settled litigation and formed partnerships with them | [TLDL](https://www.tldl.io/resources/ai-music-generators-suno-udio-2026) | summary only, **and the weakest source here** |

**Flagged rather than relied on.** That last row came from a commercial
listicle, which is a category of source this repository would not accept
anywhere it mattered. The claim about label settlements is plausible and
consequential and it is **not** established by what was read. §24 does not
depend on it; nothing should be built on it without a real source.

---

## What would make this file honest rather than merely candid

One pass, by someone who opens things:

1. **Read the Hit Song Science survey.** It is the load-bearing one.
2. **Check whether aligned lyric/score corpora exist.** §24's central claim is
   an absence, and absences are the hardest thing to establish from search
   summaries. `Lyrics-MIDI-Dataset` on Hugging Face surfaced during the sweep
   and was not examined; it may already be the thing §24 says is missing.
3. **Downgrade or confirm each row above**, and record which — an unverified
   row and a verified one currently look identical, which is §18 item 0 of the architecture's
   complaint applied to this file.
4. **Replace the listicle** or delete the row.

Until then every claim here is at the strength of a search result, and §24
should be read with that in front of it.
