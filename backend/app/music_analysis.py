"""Análisis musical ligero (BPM, beats, duración, curva de energía) con librosa.

`librosa` es una dependencia pesada y opcional: si no está instalada, las funciones
devuelven un resultado degradado con `available=False` en lugar de fallar. Los helpers
puros (`snap_times_to_beats`, `sections_from_energy`) NO dependen de librosa y se testean
sin binarios.

Instalación del extra de audio: `pip install -r requirements-audio.txt`.
"""

from __future__ import annotations

from typing import Any, Optional


def snap_times_to_beats(
    times: list[float],
    beats: list[float],
    *,
    max_shift_sec: float = 0.25,
) -> list[float]:
    """Acerca cada tiempo al beat más cercano si está dentro de `max_shift_sec`.

    Si no hay beats, devuelve los tiempos sin tocar. Pensado para que los cortes
    de plano caigan en el pulso de la canción sin desplazarse demasiado.
    """
    if not beats:
        return [round(float(t), 3) for t in times]
    out: list[float] = []
    for t in times:
        t = float(t)
        nearest = min(beats, key=lambda b: abs(float(b) - t))
        if abs(float(nearest) - t) <= max_shift_sec:
            out.append(round(float(nearest), 3))
        else:
            out.append(round(t, 3))
    return out


def sections_from_energy(
    energy: list[float],
    times: list[float],
    *,
    min_section_sec: float = 8.0,
    threshold_ratio: float = 1.35,
) -> list[dict[str, Any]]:
    """Segmentación gruesa por saltos en la curva de energía RMS.

    Heurística simple (no DSP avanzado): marca un nuevo límite cuando la energía
    sube/baja por encima de `threshold_ratio` respecto a la media de la sección
    actual, respetando una duración mínima por sección. Puramente numérico → testeable.
    """
    if not energy or not times or len(energy) != len(times):
        return []
    sections: list[dict[str, Any]] = []
    start_idx = 0
    running_sum = energy[0]
    running_n = 1
    for i in range(1, len(energy)):
        mean = running_sum / max(1, running_n)
        elapsed = times[i] - times[start_idx]
        ratio = (energy[i] + 1e-9) / (mean + 1e-9)
        crossed = ratio >= threshold_ratio or ratio <= (1.0 / threshold_ratio)
        if crossed and elapsed >= min_section_sec:
            sections.append(
                {
                    "start_sec": round(times[start_idx], 2),
                    "end_sec": round(times[i], 2),
                    "mean_energy": round(mean, 4),
                }
            )
            start_idx = i
            running_sum = energy[i]
            running_n = 1
        else:
            running_sum += energy[i]
            running_n += 1
    # Cierre de la última sección
    sections.append(
        {
            "start_sec": round(times[start_idx], 2),
            "end_sec": round(times[-1], 2),
            "mean_energy": round(running_sum / max(1, running_n), 4),
        }
    )
    return sections


def analyze_music(wav_path: str) -> dict[str, Any]:
    """Extrae BPM, beat grid, duración y curva de energía con librosa.

    Devuelve siempre un dict; si librosa no está disponible o hay error, incluye
    `available=False` y `error`, para que el orquestador pueda seguir en modo degradado.
    """
    try:
        import librosa  # type: ignore
        import numpy as np  # type: ignore
    except Exception as e:  # noqa: BLE001
        return {
            "available": False,
            "error": f"librosa no instalado ({e}). Usa requirements-audio.txt.",
        }

    try:
        y, sr = librosa.load(wav_path, sr=None, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beats = librosa.frames_to_time(beat_frames, sr=sr)
        # Curva de energía RMS submuestreada (1 valor por ~0.5 s para mantenerlo ligero)
        hop = 512
        rms = librosa.feature.rms(y=y, hop_length=hop)[0]
        rms_times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=hop)
        step = max(1, int(round(0.5 * sr / hop)))
        energy = [float(x) for x in rms[::step]]
        energy_times = [float(t) for t in rms_times[::step]]
        bpm = float(np.atleast_1d(tempo)[0])
        return {
            "available": True,
            "duration_sec": round(duration, 3),
            "bpm": round(bpm, 2),
            "beats": [round(float(b), 3) for b in beats],
            "energy": energy,
            "energy_times": energy_times,
            "sections": sections_from_energy(energy, energy_times),
        }
    except Exception as e:  # noqa: BLE001
        return {"available": False, "error": f"Fallo en análisis librosa: {e}"}
