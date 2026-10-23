from __future__ import annotations

import os
import re
from typing import Callable, Optional
import yt_dlp


def sanitize_destination(path: str) -> str:
    resolved = os.path.abspath(path.strip())
    os.makedirs(resolved, exist_ok=True)
    return resolved


def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r'^(https?://)?'
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'
        r'(:\d+)?(/.*)?$',
        re.IGNORECASE
    )
    return bool(url and regex.match(url.strip()))


def build_ydl_options(
    output_dir: str,
    audio_only: bool = False,
    progress_hook: Optional[Callable[[dict], None]] = None
) -> dict:
    out_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    ydl_opts: dict = {
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    if audio_only:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        ydl_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        })

    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]

    return ydl_opts


def download_media(
    url: str,
    output_dir: str,
    audio_only: bool = False,
    progress_hook: Optional[Callable[[dict], None]] = None
) -> None:
    if not is_valid_url(url):
        raise ValueError("Invalid media URL provided.")

    sanitized_dir = sanitize_destination(output_dir)
    options = build_ydl_options(sanitized_dir, audio_only=audio_only, progress_hook=progress_hook)

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
