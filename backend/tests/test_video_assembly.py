"""Tests del ensamblado final (v2-F5). Puros + dry-run: sin ffmpeg ni ficheros reales."""

from app.video_assembly import (
    _fmt_ts,
    assemble,
    build_concat_list,
    build_ffmpeg_command,
    build_srt,
    resolve_clip_paths,
)


def test_fmt_ts() -> None:
    assert _fmt_ts(0) == "00:00:00,000"
    assert _fmt_ts(3661.5) == "01:01:01,500"
    assert _fmt_ts(-1) == "00:00:00,000"


def test_build_srt_orders_and_formats() -> None:
    lt = [
        {"line_index": 1, "line": "segunda", "start": 5.0, "end": 7.0},
        {"line_index": 0, "line": "primera", "start": 1.0, "end": 3.0},
        {"line_index": 2, "line": "  ", "start": 8.0, "end": 9.0},  # vacía → se ignora
        {"line_index": 3, "line": "sin tiempo", "start": None, "end": None},  # se ignora
    ]
    srt = build_srt(lt)
    assert "1\n00:00:01,000 --> 00:00:03,000\nprimera" in srt
    assert "2\n00:00:05,000 --> 00:00:07,000\nsegunda" in srt
    assert "sin tiempo" not in srt


def test_build_concat_list_normalizes_paths() -> None:
    out = build_concat_list(["render_out\\clip_001.mp4", "render_out/clip_002.mp4"])
    assert "file 'render_out/clip_001.mp4'" in out
    assert "file 'render_out/clip_002.mp4'" in out
    assert out.endswith("\n")


def test_build_ffmpeg_command_copy_when_no_subs() -> None:
    cmd = build_ffmpeg_command("list.txt", "song.wav", "out.mp4")
    assert cmd[0] == "ffmpeg"
    assert "-c:v" in cmd and cmd[cmd.index("-c:v") + 1] == "copy"
    assert "-shortest" in cmd
    assert cmd[-1] == "out.mp4"
    assert "1:a:0" in cmd  # mapea el audio original


def test_build_ffmpeg_command_reencodes_with_subs() -> None:
    cmd = build_ffmpeg_command("list.txt", "song.wav", "out.mp4", srt_path="subs.srt")
    assert "-vf" in cmd
    vf = cmd[cmd.index("-vf") + 1]
    assert "subtitles=" in vf
    assert "libx264" in cmd


def test_resolve_clip_paths() -> None:
    segs = [{"index": 1}, {"index": 2}, {"index": 10}]
    paths = resolve_clip_paths(segs, "render_out")
    assert paths[0].replace("\\", "/").endswith("render_out/clip_001.mp4")
    assert paths[2].replace("\\", "/").endswith("render_out/clip_010.mp4")


def test_assemble_dry_run_reports_missing_clips() -> None:
    res = assemble(
        out_path="final.mp4",
        audio_path="nope_song.wav",
        clip_paths=["nope_clip_001.mp4", "nope_clip_002.mp4"],
        dry_run=True,
    )
    assert res["dry_run"] is True
    assert res["ok"] is False  # clips y audio no existen → bloqueado
    assert len(res["missing_clips"]) == 2
    assert res["n_clips"] == 2
    assert res["command"][0] == "ffmpeg"


def test_assemble_requires_clips_source() -> None:
    res = assemble(out_path="o.mp4", audio_path="a.wav", dry_run=True)
    assert res["ok"] is False
    assert "clip_paths" in res["error"]
