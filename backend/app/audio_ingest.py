"""Ingesta de audio y alineación letra↔tiempo (VideoZero v2 · Fase 1, local).

Pipeline (todo local, sin APIs de pago):
  1. download_audio()   — yt-dlp: URL de YouTube (o archivo propio) → WAV 44.1k
  2. separate_stems()   — Demucs: WAV → vocals.wav / no_vocals.wav  (opcional)
  3. align_lyrics()     — WhisperX: vocals + LETRA (tuya, source of truth) → palabras con tiempo
  4. words_to_line_timings() — agrupa palabras alineadas en líneas de la letra (PURO, testeable)

Las herramientas pesadas (yt-dlp, demucs, ffmpeg, whisperx) se invocan como subprocess
o import perezoso. Si faltan, cada paso devuelve un resultado degradado con `ok=False`
y un mensaje accionable — el orquestador nunca revienta y reporta qué pasos corrieron.

Notas legales: descarga solo contenido del que tengas derechos (tu canción / CC / dominio
público). Spotify NO sirve (audio cifrado); usa la URL de YouTube del tema.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# Helpers puros (testeables sin binarios)
# --------------------------------------------------------------------------- #

def _norm_token(s: str) -> str:
    """minúsculas, sin acentos, solo alfanumérico — para casar palabras alineadas con la letra."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _line_tokens(line: str) -> list[str]:
    return [t for t in (_norm_token(w) for w in re.findall(r"\S+", line)) if t]


def _interpolate_gaps(rows: list[dict[str, Any]]) -> None:
    """Rellena start/end None por interpolación lineal entre anclas conocidas (in place)."""
    n = len(rows)
    known = [i for i, r in enumerate(rows) if r["start"] is not None and r["end"] is not None]
    if not known:
        return
    # Bordes: extiende el primer/último ancla conocido
    first, last = known[0], known[-1]
    for i in range(0, first):
        rows[i]["start"] = rows[i]["start"] or rows[first]["start"]
        rows[i]["end"] = rows[i]["end"] or rows[first]["start"]
    for i in range(last + 1, n):
        rows[i]["start"] = rows[i]["start"] or rows[last]["end"]
        rows[i]["end"] = rows[i]["end"] or rows[last]["end"]
    # Huecos internos: reparte el tiempo entre dos anclas
    for a, b in zip(known, known[1:]):
        gap = [i for i in range(a + 1, b) if rows[i]["start"] is None]
        if not gap:
            continue
        t0 = rows[a]["end"]
        t1 = rows[b]["start"]
        span = max(0.0, t1 - t0)
        step = span / (len(gap) + 1)
        for k, i in enumerate(gap, start=1):
            s = round(t0 + step * (k - 1), 3)
            e = round(t0 + step * k, 3)
            rows[i]["start"] = s
            rows[i]["end"] = e


def words_to_line_timings(
    words: list[dict[str, Any]],
    lines: list[str],
    *,
    lookahead: int = 6,
) -> list[dict[str, Any]]:
    """Agrupa palabras alineadas (con start/end) en las líneas de la letra.

    `words`: lista ordenada de {"word","start","end"} (salida de WhisperX).
    `lines`: líneas de la letra (la fuente de verdad; pueden incluir líneas en blanco).

    Casa los tokens de cada línea en secuencia contra el flujo de palabras con una
    ventana de `lookahead` (tolera pequeñas discrepancias de transcripción). El
    `start` de la línea = primera palabra casada; `end` = última. Líneas sin casar
    se rellenan por interpolación. PURO: no depende de binarios.
    """
    rows: list[dict[str, Any]] = []
    wi = 0
    n = len(words)
    for li, raw_line in enumerate(lines):
        toks = _line_tokens(raw_line)
        if not toks:
            rows.append(
                {"line_index": li, "line": raw_line, "start": None, "end": None,
                 "matched": 0, "tokens": 0}
            )
            continue
        start: Optional[float] = None
        end: Optional[float] = None
        matched = 0
        for tok in toks:
            found = None
            for j in range(wi, min(n, wi + lookahead)):
                if _norm_token(str(words[j].get("word", ""))) == tok:
                    found = j
                    break
            if found is not None:
                w = words[found]
                if start is None and w.get("start") is not None:
                    start = float(w["start"])
                if w.get("end") is not None:
                    end = float(w["end"])
                wi = found + 1
                matched += 1
        rows.append(
            {
                "line_index": li,
                "line": raw_line,
                "start": round(start, 3) if start is not None else None,
                "end": round(end, 3) if end is not None else None,
                "matched": matched,
                "tokens": len(toks),
            }
        )
    _interpolate_gaps(rows)
    return rows


# --------------------------------------------------------------------------- #
# Comprobación de herramientas externas
# --------------------------------------------------------------------------- #

def check_tools() -> dict[str, bool]:
    """Qué herramientas externas están disponibles en el entorno."""
    def _bin(name: str) -> bool:
        return shutil.which(name) is not None

    def _mod(name: str) -> bool:
        try:
            __import__(name)
            return True
        except Exception:  # noqa: BLE001
            return False

    return {
        "yt_dlp": _bin("yt-dlp") or _mod("yt_dlp"),
        "ffmpeg": _bin("ffmpeg"),
        "demucs": _mod("demucs") or _bin("demucs"),
        "whisperx": _mod("whisperx"),
        "librosa": _mod("librosa"),
    }


# --------------------------------------------------------------------------- #
# Pasos del pipeline (envoltorios sobre binarios / libs pesadas)
# --------------------------------------------------------------------------- #

def download_audio(url: str, out_dir: str, *, basename: str = "song") -> dict[str, Any]:
    """Descarga el audio de una URL (YouTube) a WAV con yt-dlp + ffmpeg."""
    if shutil.which("yt-dlp") is None:
        return {"ok": False, "error": "yt-dlp no está en PATH. pip install yt-dlp"}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{basename}.wav"
    cmd = [
        "yt-dlp", "-x", "--audio-format", "wav", "--audio-quality", "0",
        "-o", str(out / f"{basename}.%(ext)s"), url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"yt-dlp falló: {e}"}
    if proc.returncode != 0 or not target.exists():
        return {"ok": False, "error": f"yt-dlp rc={proc.returncode}: {proc.stderr[-500:]}"}
    return {"ok": True, "wav_path": str(target)}


def separate_stems(wav_path: str, out_dir: str) -> dict[str, Any]:
    """Separa voz/instrumental con Demucs (htdemucs). Opcional."""
    if not (shutil.which("demucs") or _module_available("demucs")):
        return {"ok": False, "error": "demucs no instalado. pip install demucs (extra de audio)"}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cmd = ["demucs", "--two-stems", "vocals", "-o", str(out), wav_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"demucs falló: {e}"}
    if proc.returncode != 0:
        return {"ok": False, "error": f"demucs rc={proc.returncode}: {proc.stderr[-500:]}"}
    vocals = next(out.rglob("vocals.wav"), None)
    no_vocals = next(out.rglob("no_vocals.wav"), None)
    if not vocals:
        return {"ok": False, "error": "demucs no produjo vocals.wav"}
    return {
        "ok": True,
        "vocals_path": str(vocals),
        "no_vocals_path": str(no_vocals) if no_vocals else None,
    }


def align_lyrics(
    audio_path: str,
    lyrics_text: str,
    *,
    language: str = "es",
) -> dict[str, Any]:
    """Transcribe + alinea a nivel de palabra con WhisperX. Opcional.

    Devuelve {"ok":True,"words":[{word,start,end},...]} o un error degradado.
    """
    try:
        import whisperx  # type: ignore
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"whisperx no instalado ({e}). Ver requirements-audio.txt"}
    try:
        device = "cpu"
        model = whisperx.load_model("small", device, compute_type="int8")
        audio = whisperx.load_audio(audio_path)
        result = model.transcribe(audio, language=language)
        align_model, metadata = whisperx.load_align_model(
            language_code=language, device=device
        )
        aligned = whisperx.align(
            result["segments"], align_model, metadata, audio, device,
            return_char_alignments=False,
        )
        words: list[dict[str, Any]] = []
        for seg in aligned.get("segments", []):
            for w in seg.get("words", []):
                if w.get("start") is None:
                    continue
                words.append(
                    {"word": w.get("word", ""), "start": w.get("start"), "end": w.get("end")}
                )
        return {"ok": True, "words": words}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"WhisperX falló: {e}"}


def _module_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------- #
# Orquestador
# --------------------------------------------------------------------------- #

def ingest_and_align(
    *,
    lyrics_text: str,
    url: Optional[str] = None,
    audio_file: Optional[str] = None,
    work_dir: str = "audio_work",
    language: str = "es",
    do_stems: bool = True,
) -> dict[str, Any]:
    """Pipeline completo de audio local. Degrada con elegancia si faltan herramientas.

    Devuelve un dict con `steps` (qué corrió/qué se saltó), `line_timings`, `music`,
    y `degraded` (True si algún paso clave no estuvo disponible).
    """
    from .music_analysis import analyze_music  # import local para no acoplar

    steps: list[dict[str, Any]] = []
    degraded = False
    lines = lyrics_text.splitlines()

    # 1) Conseguir un WAV
    wav_path: Optional[str] = audio_file
    if not wav_path and url:
        dl = download_audio(url, work_dir)
        steps.append({"step": "download", **dl})
        wav_path = dl.get("wav_path")
        if not dl.get("ok"):
            degraded = True
    elif audio_file:
        steps.append({"step": "download", "ok": True, "wav_path": audio_file, "note": "archivo local"})

    # Sin audio → solo letra: no hay tiempos reales, el planner usará heurística aguas abajo.
    if not wav_path:
        steps.append({"step": "audio", "ok": False, "error": "Sin URL ni archivo de audio."})
        return {
            "degraded": True, "steps": steps, "wav_path": None,
            "line_timings": [], "music": {"available": False},
            "note": "Modo solo-letra: usa timed_segments heurístico sobre target_duration_seconds.",
        }

    # 2) Stems (opcional)
    vocals_path = wav_path
    if do_stems:
        st = separate_stems(wav_path, str(Path(work_dir) / "stems"))
        steps.append({"step": "stems", **st})
        if st.get("ok"):
            vocals_path = st["vocals_path"]
        else:
            degraded = True  # seguimos alineando sobre la mezcla

    # 3) Alineación letra↔tiempo
    al = align_lyrics(vocals_path, lyrics_text, language=language)
    steps.append({"step": "align", "ok": al.get("ok"), "error": al.get("error"),
                  "n_words": len(al.get("words", []))})
    line_timings: list[dict[str, Any]] = []
    if al.get("ok"):
        line_timings = words_to_line_timings(al["words"], lines)
    else:
        degraded = True

    # 4) Análisis musical (BPM/beats/energía)
    music = analyze_music(wav_path)
    steps.append({"step": "music", "ok": music.get("available", False),
                  "error": music.get("error")})
    if not music.get("available"):
        degraded = True

    return {
        "degraded": degraded,
        "steps": steps,
        "wav_path": wav_path,
        "vocals_path": vocals_path,
        "line_timings": line_timings,
        "music": music,
    }
