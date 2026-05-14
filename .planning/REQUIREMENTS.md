# Requirements: VideoZero

**Defined:** 2026-05-13  
**Revised:** 2026-05-13 (v1 · letra primero)  
**Core value:** Cada plano y export hereda contexto validado anclado en la **letra** y las **decisiones de dirección**, para producir en herramientas externas sin collage incoherente — con o sin audio.

## v1 Requirements

### Project & workspace

- [x] **PROJ-01**: User can create a new project (workspace) with a name
- [x] **PROJ-02**: User can reopen a saved project and continue the guided flow where they left off

### Ingestion (lyrics-first)

- [x] **ING-01**: User can paste or upload **lyrics** as the primary required input
- [x] **ING-02**: User can optionally upload an **audio** file (reference / future timing); not required to complete MVP path
- [x] **ING-03**: User can edit basic metadata (title, artist, language, target mood)
- [x] **ING-04**: User can set an optional **target duration** (e.g. seconds) as the primary “clock” when no audio exists

### Structure (lyric-native)

- [ ] **STR-01**: User can define, rename, and reorder **lyric sections** (intro/verse/chorus/custom) and attach them to lyric blocks or line ranges
- [ ] **STR-02**: User can choose a **pacing profile** (guided questions) that influences default shot density and edit rhythm without DSP

### Lyrics intelligence

- [ ] **LYR-01**: System parses lyrics into ordered lines/blocks suitable for structure linking
- [ ] **LYR-02**: System proposes visual motifs, symbols, places, and interpretive hooks (LLM-assisted, user-editable)

### Optional timing

- [ ] **ALN-01**: User can edit optional per-line timings (start/end nullable) **or** rely on section-relative placement when timestamps are unknown

### Creative intake & direction

- [ ] **CRE-01**: User can submit references and “vibes” translated into non-literal style attributes (no copyable artist/work names in compiled prompts)
- [ ] **DIR-01**: User can complete a guided director questionnaire with concrete options (answers persisted)
- [ ] **DIR-02**: User can compare creative routes, select or blend, and **lock** a creative direction snapshot before dense shot planning

### Documents

- [ ] **DOC-01**: System generates an exportable **Visual Bible** from locked direction and structured inputs
- [ ] **DOC-02**: System generates an exportable **Treatment** (professional tone)

### Timeline, scenes, shots

- [ ] **PLN-01**: User can review and edit **timeline blocks** anchored to lyric sections and lyric lines (narrative goal, primary visual, transitions, edit pace)
- [ ] **PLN-02**: User can define **scenes** linked to timeline blocks with mood and bible references
- [ ] **PLN-03**: User can review and edit **shot list** rows (timing optional, camera, action, continuity constraints, review criteria)

### Prompt compilation

- [ ] **PRM-01**: System compiles each shot into a **canonical / generic cinematic** prompt string from bible + scene + shot fields
- [ ] **PRM-02**: System compiles into **Runway**-oriented prompt text
- [ ] **PRM-03**: System compiles into **Kling**-oriented prompt text

### Generation plan & review

- [ ] **GEN-01**: System outputs a **generation plan** (ordered steps, dependencies, notes for i2v vs t2v where applicable)
- [ ] **GEN-02**: System outputs a **generation checklist** and **review matrix** criteria per shot

### Export

- [ ] **EXP-01**: User can download or copy a Markdown bundle (brief, questions, bible, treatment, timeline, edit plan)
- [ ] **EXP-02**: User can export shot list as **CSV** and **JSON**
- [ ] **EXP-03**: User can export **prompt packs** as Markdown per provider (generic, Runway, Kling)

### Compliance (MVP)

- [x] **OPS-01**: User must confirm rights to use the **lyrics** in this workflow before running the generative pipeline (checkbox + short copy)
- [x] **OPS-02**: If an audio file is uploaded, user must confirm rights to use that **audio** before any audio processing beyond trivial metadata (e.g. duration via ffprobe)

## v2 Requirements

### Audio Pro (DSP)

- **ANA-01**: Approximate BPM, onsets, per-window energy / intensity curve from audio
- **ANA-02**: Tentative musical segmentation suggestions (user-reviewed)
- **ANA-03**: Async job UX with progress for audio analysis jobs

### Assisted alignment

- **ING-10**: Assisted lyric-to-audio alignment suggestions (Whisper / WhisperX) with explicit low-confidence warnings

### Export & integration

- **EXP-10**: EDL / FCPXML / XML for NLEs
- **INT-10**: Optional API adapters for video providers

### Collaboration

- **COLL-01**: Multi-user project sharing and comments on shots

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full music-video render inside the app | v1 is planning + prompts for external tools |
| Heavy DSP-first workflow in v1 | Deferred to v2 *Audio Pro*; lyrics-first reduces cost and mismatched expectations |
| Perfect automatic lyric-to-vocal alignment | Unreliable; manual/assisted later |
| Real-time multi-user editing | Not required for initial niche |
| OAuth / billing / accounts | Defer unless cloud SaaS is immediate |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROJ-01 | Phase 1 | Done |
| PROJ-02 | Phase 1 | Done |
| ING-01 | Phase 1.5 | Done |
| ING-02 | Phase 1.5 | Done |
| ING-03 | Phase 1.5 | Done |
| ING-04 | Phase 1.5 | Done |
| OPS-01 | Phase 1.5 | Done |
| OPS-02 | Phase 1.5 | Done |
| STR-01 | Phase 2 | Pending |
| STR-02 | Phase 2 | Pending |
| LYR-01 | Phase 2 | Pending |
| LYR-02 | Phase 2 | Pending |
| ALN-01 | Phase 3 | Pending |
| CRE-01 | Phase 3 | Pending |
| DIR-01 | Phase 3 | Pending |
| DIR-02 | Phase 3 | Pending |
| DOC-01 | Phase 4 | Pending |
| DOC-02 | Phase 4 | Pending |
| PLN-01 | Phase 5 | Pending |
| PLN-02 | Phase 5 | Pending |
| PLN-03 | Phase 5 | Pending |
| PRM-01 | Phase 6 | Pending |
| PRM-02 | Phase 6 | Pending |
| PRM-03 | Phase 6 | Pending |
| GEN-01 | Phase 6 | Pending |
| GEN-02 | Phase 6 | Pending |
| EXP-01 | Phase 6 | Pending |
| EXP-02 | Phase 6 | Pending |
| EXP-03 | Phase 6 | Pending |

**Coverage:**

- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0 ✓

---

*Last updated: 2026-05-13 — Phase 1.5 requirements marked done in traceability*
