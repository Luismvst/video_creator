---
phase: 12
slug: cinematic-prompting-direction-quality-f6
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-29
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Todo se valida con **tests puros: sin red, sin binarios, sin FAL_KEY/OpenAI** (estilo
> `test_render_client.py` / `test_music_planner.py`). Fuente: 12-RESEARCH.md §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend/tests/*.py) |
| **Config file** | ninguno dedicado; tests importan `from app.X import ...` |
| **Quick run command** | `cd backend && .venv/Scripts/python.exe -m pytest tests/test_<módulo>.py -x -q` |
| **Full suite command** | `cd backend && .venv/Scripts/python.exe -m pytest -q` (≥48 verdes + nuevos) |
| **Estimated runtime** | ~2 s |

---

## Sampling Rate

- **After every task commit:** Run quick command para el módulo tocado
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite verde (≥48 + nuevos)
- **Max feedback latency:** ~2 s

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists |
|--------|----------|-----------|-------------------|-------------|
| DIRQ-01 | Biblia con todos los campos; heurística sin key; sanitizador elimina nombres de obra/artista | unit | `pytest tests/test_visual_bible.py -x` | ❌ W0 |
| DIRQ-02 | Prompt incluye en orden sujeto+cámara+biblia+negativos+aspect; biblia en TODOS los segmentos | unit | `pytest tests/test_prompt_compile.py -x` | ❌ W0 |
| DIRQ-03 | Ruta heurística genera 8–15 shots con `intent`/`shot_size`, sin key | unit | `pytest tests/test_onboarding_ai.py -k shots_richness -x` | ❌ W0 |
| DIRQ-04 | `camera_for_energy` mapea high/mid/low/neutral; sin audio → neutral | unit | `pytest tests/test_camera_language.py -x` | ❌ W0 |
| DIRQ-05 | Plan encadena (`reference_image`=kf anterior; 1º None); render real pasa `image_url` (dry-run) | unit | `pytest tests/test_keyframes.py -k chain -x` | ⚠️ keyframes sin test hoy |
| DIRQ-06 | Kling sujeto-primero+negativos sufijo; Veo cámara-primero; Runway sin negativos | unit | `pytest tests/test_prompt_compile.py -k provider -x` | ❌ W0 |
| DIRQ-07 | `render_timeline(reroll_indices=[...])` renderiza solo esos; estimación sobre el subconjunto | unit | `pytest tests/test_render_client.py -k reroll -x` | ⚠️ extender existente |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_visual_bible.py` — DIRQ-01 (campos, heurística, sanitizador legal)
- [ ] `tests/test_prompt_compile.py` — DIRQ-02/06 (orden de capas, branch por proveedor)
- [ ] `tests/test_camera_language.py` — DIRQ-04 (mapa energía→cámara, neutral sin audio)
- [ ] `tests/test_keyframes.py` — DIRQ-05 (encadenado; hoy `keyframes.py` no tiene test)
- [ ] `tests/test_onboarding_ai.py` — DIRQ-03 (riqueza de shots; hoy sin test unit dedicado)
- [ ] Extender `tests/test_render_client.py` — DIRQ-07 (`reroll_indices`) y DIRQ-05 (`image_url` en payload dry-run)
- [ ] Extender `tests/test_music_planner.py` — biblia inyectada en cada `prompt_*`; cámara-por-energía en `shot`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Calidad subjetiva "cinematográfica" del prompt | DIRQ-02/06 | El juicio estético no es automatizable | Mini-demo antes/después: emitir `segments.json` con prompts F6 vs plantilla previa y comparar lado a lado (artefacto recomendado en CONTEXT.md) |
| Continuidad real entre clips generados | DIRQ-05 | Requiere render real (gasta) | Tras `--run` con FAL_KEY, revisar 2 clips encadenados |

*El resto de comportamientos tienen verificación automatizada en dry-run.*

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (7 ítems arriba)
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
