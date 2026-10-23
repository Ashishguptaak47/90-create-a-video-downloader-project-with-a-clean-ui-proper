from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from downloader import download_media, is_valid_url, sanitize_destination


class VideoDownloaderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Video Downloader")
        self.geometry("580x360")
        self.minsize(520, 320)
        self.configure(padx=16, pady=16)

        self.download_queue: queue.Queue = queue.Queue()
        self.output_directory = tk.StringVar(value=os.path.abspath("downloads"))
        self.media_url = tk.StringVar()
        self.download_mode = tk.StringVar(value="video")
        self.status_msg = tk.StringVar(value="Ready")
        self.is_downloading = False

        self._setup_ui()
        self._poll_queue()

    def _setup_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        # Header
        header = ttk.Label(self, text="Universal Media Downloader", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w", pady=(0, 14))

        # URL Entry
        url_frame = ttk.LabelFrame(self, text=" Media URL ", padding=10)
        url_frame.pack(fill="x", pady=(0, 10))
        url_entry = ttk.Entry(url_frame, textvariable=self.media_url)
        url_entry.pack(fill="x", expand=True)

        # Destination Folder
        dest_frame = ttk.LabelFrame(self, text=" Save Location ", padding=10)
        dest_frame.pack(fill="x", pady=(0, 10))
        dest_entry = ttk.Entry(dest_frame, textvariable=self.output_directory)
        dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        browse_btn = ttk.Button(dest_frame, text="Browse...", command=self._browse_directory)
        browse_btn.pack(side="right")

        # Options Frame
        opts_frame = ttk.Frame(self)
        opts_frame.pack(fill="x", pady=(0, 12))

        ttk.Radiobutton(
            opts_frame,
            text="Video (MP4)",
            variable=self.download_mode,
            value="video"
        ).pack(side="left", padx=(0, 15))

        ttk.Radiobutton(
            opts_frame,
            text="Audio Only (MP3)",
            variable=self.download_mode,
            value="audio"
        ).pack(side="left")

        # Progress Bar & Status
        self.prog_bar = ttk.Progressbar(self, orient="horizontal", mode="determinate", maximum=100)
        self.prog_bar.pack(fill="x", pady=(0, 6))

        self.status_label = ttk.Label(self, textvariable=self.status_msg, font=("Segoe UI", 9))
        self.status_label.pack(anchor="w", pady=(0, 12))

        # Action Button
        self.action_btn = ttk.Button(self, text="Start Download", command=self._start_download_thread)
        self.action_btn.pack(fill="x", ipady=4)

    def _browse_directory(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.output_directory.get())
        if folder:
            self.output_directory.set(folder)

    def _start_download_thread(self) -> None:
        url = self.media_url.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please provide a media URL.")
            return
        if not is_valid_url(url):
            messagebox.showerror("Invalid URL", "The URL provided is not formatted correctly.")
            return

        dest = sanitize_destination(self.output_directory.get())
        audio_only = self.download_mode.get() == "audio"

        self.is_downloading = True
        self.action_btn.config(state="disabled")
        self.prog_bar["value"] = 0
        self.status_msg.set("Connecting...")

        thread = threading.Thread(
            target=self._worker,
            args=(url, dest, audio_only),
            daemon=True
        )
        thread.start()

    def _worker(self, url: str, dest: str, audio_only: bool) -> None:
        def hook(d: dict) -> None:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                percent = (downloaded / total * 100) if total else 0
                speed = d.get("_speed_str", "")
                eta = d.get("_eta_str", "")
                self.download_queue.put((
                    "progress",
                    percent,
                    f"Downloading: {percent:0.1f}% | Speed: {speed} | ETA: {eta}"
                ))
            elif d.get("status") == "finished":
                self.download_queue.put(("progress", 100.0, "Processing and finishing file..."))

        try:
            download_media(url, dest, audio_only=audio_only, progress_hook=hook)
            self.download_queue.put(("complete", 100.0, "Download completed successfully!"))
        except Exception as exc:
            self.download_queue.put(("error", 0.0, str(exc)))

    def _poll_queue(self) -> None:
        try:
            while True:
                msg_type, percent, text = self.download_queue.get_nowait()
                self.prog_bar["value"] = percent
                self.status_msg.set(text)

                if msg_type == "complete":
                    self.is_downloading = False
                    self.action_btn.config(state="normal")
                    messagebox.showinfo("Success", "File downloaded successfully!")
                elif msg_type == "error":
                    self.is_downloading = False
                    self.action_btn.config(state="normal")
                    messagebox.showerror("Download Failed", f"An error occurred:\n{text}")
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)


def main() -> None:
    app = VideoDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
