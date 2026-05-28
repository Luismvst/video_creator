"""Tests de los helpers puros de v2-F1 (sin binarios: yt-dlp/demucs/whisperx/librosa)."""

from app.audio_ingest import words_to_line_timings
from app.music_analysis import sections_from_energy, snap_times_to_beats


def _w(word, start, end):
    return {"word": word, "start": start, "end": end}


def test_words_to_line_timings_basic() -> None:
    words = [
        _w("Caía", 1.0, 1.4), _w("la", 1.4, 1.5), _w("nieve", 1.5, 2.0),
        _w("sobre", 2.0, 2.3), _w("el", 2.3, 2.4), _w("puerto", 2.4, 3.0),
        _w("y", 3.2, 3.3), _w("nadie", 3.3, 3.7), _w("hablaba", 3.7, 4.4),
    ]
    lines = ["Caía la nieve sobre el puerto", "y nadie hablaba"]
    rows = words_to_line_timings(words, lines)
    assert len(rows) == 2
    assert rows[0]["start"] == 1.0
    assert rows[0]["end"] == 3.0
    assert rows[1]["start"] == 3.2
    assert rows[1]["end"] == 4.4
    assert rows[0]["matched"] == rows[0]["tokens"] == 6


def test_words_to_line_timings_accents_and_punctuation() -> None:
    # La transcripción puede venir sin tildes / con signos: el matching normaliza.
    words = [_w("caia", 0.5, 0.9), _w("LA", 0.9, 1.0), _w("nieve,", 1.0, 1.6)]
    lines = ["Caía la nieve"]
    rows = words_to_line_timings(words, lines)
    assert rows[0]["start"] == 0.5
    assert rows[0]["end"] == 1.6
    assert rows[0]["matched"] == 3


def test_words_to_line_timings_blank_line_interpolated() -> None:
    words = [_w("uno", 0.0, 0.5), _w("tres", 2.0, 2.5)]
    # línea del medio sin palabras casables → debe interpolar entre anclas
    lines = ["uno", "dos inexistente", "tres"]
    rows = words_to_line_timings(words, lines)
    assert rows[0]["start"] == 0.0
    assert rows[2]["end"] == 2.5
    mid = rows[1]
    assert mid["start"] is not None and mid["end"] is not None
    assert 0.5 <= mid["start"] <= 2.0


def test_snap_times_to_beats() -> None:
    beats = [0.0, 0.5, 1.0, 1.5, 2.0]
    # con max_shift 0.1: 0.58→0.5 (0.08 ok); 1.95→2.0 (0.05 ok); 0.8 dista 0.2 de 1.0 → queda igual
    out = snap_times_to_beats([0.58, 1.95, 0.8], beats, max_shift_sec=0.1)
    assert out[0] == 0.5
    assert out[1] == 2.0
    assert out[2] == 0.8


def test_snap_times_no_beats_passthrough() -> None:
    assert snap_times_to_beats([1.234, 5.678], []) == [1.234, 5.678]


def test_sections_from_energy_splits_on_jump() -> None:
    times = [0.0, 4.0, 8.0, 12.0, 16.0, 20.0]
    energy = [0.1, 0.1, 0.1, 0.5, 0.5, 0.5]  # salto x5 en t=12 (>= min 8s)
    secs = sections_from_energy(energy, times, min_section_sec=8.0, threshold_ratio=1.35)
    assert len(secs) >= 2
    assert secs[0]["start_sec"] == 0.0
    assert secs[-1]["end_sec"] == 20.0


def test_sections_from_energy_empty() -> None:
    assert sections_from_energy([], []) == []
