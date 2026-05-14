from fastapi import HTTPException

from .models import Song


def assert_song_unlocked_for_structure(song: Song) -> None:
    if song.creative_lock_at:
        raise HTTPException(
            status_code=400,
            detail="Creative Lock is active. Unlock before editing sections, timings or lyric structure.",
        )


def assert_song_unlocked_for_insights(song: Song) -> None:
    if song.creative_lock_at:
        raise HTTPException(
            status_code=400,
            detail="Creative Lock is active. Unlock before editing or regenerating lyric insights.",
        )
