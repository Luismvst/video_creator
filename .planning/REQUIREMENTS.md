# Requirements: VideoZero

**Defined:** 2026-05-13  
**Core value:** Cada plano y export hereda contexto validado (letra, tiempo, biblia, continuidad, proveedor) para evitar collage incoherente en producción con IA externa.

## v1 Requirements

### Project & workspace

- [ ] **PROJ-01**: User can create a new song project (workspace) with a name
- [ ] **PROJ-02**: User can reopen a saved project and continue the guided flow where they left off

### Ingestion

- [ ] **ING-01**: User can upload an audio file for the song (stored per project)
- [ ] **ING-02**: User can paste lyrics as text or upload a lyrics file
- [ ] **ING-03**: User can edit song metadata (title, artist, language, target mood)

### Audio analysis

- [ ] **ANA-01**: System computes duration and approximate BPM from uploaded audio
- [ ] **ANA-02**: System produces tentative segments, onset markers, and per-window energy / intensity curve
- [ ] **ANA-03**: User can see analysis job progress (async) and a completed summary when done

### Lyrics analysis

- [ ] **LYR-01**: System parses lyrics into ordered lines/blocks suitable for alignment and downstream linking
- [ ] **LYR-02**: System proposes visual motifs, symbols, places, and interpretive hooks (LLM-assisted, user-editable)

### Alignment

- [ ] **ALN-01**: User can edit a table of line alignments (line id, start time, end time, section override, emotional intensity, visual notes)

### Creative intake & direction

- [ ] **CRE-01**: User can submit references and “vibes” that are translated into non-literal style attributes (no copyable artist/work names in compiled prompts)
- [ ] **DIR-01**: User can complete a guided director questionnaire with concrete options (answers persisted)
- [ ] **DIR-02**: User can compare multiple creative routes, select or blend, and **lock** a creative direction snapshot before dense shot planning

### Documents

- [ ] **DOC-01**: System generates an exportable **Visual Bible** from locked direction and structured inputs
- [ ] **DOC-02**: System generates an exportable **Treatment** (professional tone, presentable to artist/producer)

### Timeline, scenes, shots

- [ ] **PLN-01**: User can review and edit **timeline blocks** (time range, section, linked lyric lines, narrative goal, primary visual, transitions, edit pace)
- [ ] **PLN-02**: User can define **scenes** linked to timeline blocks with mood and location/character refs from the bible
- [ ] **PLN-03**: User can review and edit **shot list** rows (timestamps, camera, action, continuity constraints, review criteria)

### Prompt compilation

- [ ] **PRM-01**: System compiles each shot into a **canonical / generic cinematic** prompt string from bible + scene + shot fields
- [ ] **PRM-02**: System compiles the same shot into **Runway**-oriented prompt text (adapter profile)
- [ ] **PRM-03**: System compiles the same shot into **Kling**-oriented prompt text (adapter profile)

### Generation plan & review

- [ ] **GEN-01**: System outputs a **generation plan** (ordered steps, dependencies, notes for i2v vs t2v where applicable)
- [ ] **GEN-02**: System outputs a **generation checklist** and **review matrix** criteria per shot (e.g. lyric fit, bible fit, continuity, motion, emotion, edit usefulness, AI artifacts)

### Export

- [ ] **EXP-01**: User can download or copy a Markdown bundle including creative brief, director questions, visual bible, treatment, timeline, edit plan
- [ ] **EXP-02**: User can export shot list as **CSV** and **JSON** with stable column/key names
- [ ] **EXP-03**: User can export **prompt packs** as Markdown per provider (generic, Runway, Kling)

### Compliance (MVP minimum)

- [ ] **OPS-01**: User must confirm they have rights to use the uploaded audio for this workflow before heavy analysis runs (checkbox + short legal copy)

## v2 Requirements

### Ingestion & analysis

- **ING-10**: Assisted lyric-to-audio alignment suggestions (Whisper / WhisperX) with explicit low-confidence warnings

### Export & integration

- **EXP-10**: EDL / FCPXML / XML for Premiere or DaVinci Resolve
- **INT-10**: Optional API submission adapters for video providers (`submitGeneration`, job status, download)

### Collaboration

- **COLL-01**: Multi-user project sharing and comments on shots

## Out of Scope

| Feature | Reason |
|---------|--------|
| Fully automatic in-app video render of the full music video | v1 delivers planning + prompts for external tools; API render deferred |
| Perfect automatic lyric-to-vocal alignment | Unreliable on music; manual table is the source of truth in v1 |
| Real-time multi-user editing | Not required for initial creative niche |
| OAuth / billing / accounts | Defer unless product decision moves to cloud SaaS immediately |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROJ-01 | Phase 1 | Pending |
| PROJ-02 | Phase 1 | Pending |
| ING-01 | Phase 1 | Pending |
| ING-02 | Phase 1 | Pending |
| ING-03 | Phase 1 | Pending |
| OPS-01 | Phase 1 | Pending |
| ANA-01 | Phase 2 | Pending |
| ANA-02 | Phase 2 | Pending |
| ANA-03 | Phase 2 | Pending |
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

- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---

*Requirements defined: 2026-05-13*  
*Last updated: 2026-05-13 after GSD initialization*
