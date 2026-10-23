from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest

from downloader import build_ydl_options, download_media, is_valid_url, sanitize_destination


class TestDownloaderUtils:
    def test_url_validation_valid(self):
        assert is_valid_url("https://www.example.com/watch?v=12345")
        assert is_valid_url("http://example.org/video.mp4")

    def test_url_validation_invalid(self):
        assert not is_valid_url("")
        assert not is_valid_url("not_a_valid_url")
        assert not is_valid_url("ftp://")

    def test_sanitize_destination(self, tmp_path):
        target = str(tmp_path / "nested_folder")
        result = sanitize_destination(target)
        assert os.path.exists(result)
        assert os.path.isabs(result)

    def test_build_ydl_options_video(self):
        opts = build_ydl_options("/tmp/downloads", audio_only=False)
        assert "/tmp/downloads" in opts["outtmpl"]
        assert "bestvideo" in opts["format"]
        assert opts["noplaylist"] is True

    def test_build_ydl_options_audio(self):
        opts = build_ydl_options("/tmp/downloads", audio_only=True)
        assert opts["format"] == "bestaudio/best"
        assert any(p.get("key") == "FFmpegExtractAudio" for p in opts["postprocessors"])

    @patch("yt_dlp.YoutubeDL")
    def test_download_media_invocation(self, mock_ydl, tmp_path):
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance

        download_media("https://example.com/video", str(tmp_path))
        mock_instance.download.assert_called_once_with(["https://example.com/video"])

    def test_download_media_invalid_url_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid media URL"):
            download_media("invalid-url", str(tmp_path))
