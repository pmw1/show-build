"""GPU-first / CPU-failover ffmpeg helper (worker-multi-image refactor, DRAFT).

Single place that decides HOW a video encode runs: try the GPU encoder (NVENC)
first, and if the GPU is unavailable or saturated, transparently fall back to the
software (libx264) encoder with the same output spec. The job completes either
way; only the speed differs.

WHY a helper (not per-task ad-hoc): the failover decision must be uniform across
every media task (SOT, episode mp4, thumbnails-with-encode, future media-prep
conversions). Centralizing it means one tested code path and one place to tune.

HARDWARE CONTEXT: NVIDIA consumer cards cap concurrent NVENC *encode sessions*
(historically 3-5; recent drivers/nvidia-patch lift it). Past that ceiling nvenc
fails fast with a recognizable error — which is exactly the failover trigger. On a
CPU-only host (media-cpu flavor) nvenc is simply never present, so we always take
the libx264 path; same code, graceful degrade.

This module is encoder-policy only — it does NOT change WHAT each task encodes,
just the codec flags + the run-with-failover wrapper. Tasks build their filter
graph / io as before and call `run_encode()` instead of `subprocess.run([...])`.
"""
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

# Recognizable nvenc-unavailable / saturated signatures in ffmpeg stderr. If any
# appears, the GPU path is not usable for this job -> fall back to CPU.
_NVENC_FAIL_MARKERS = (
    "Cannot load nvcuda",
    "no NVENC capable devices",
    "No capable devices found",
    "OpenEncodeSessionEx failed",
    "InitializeEncoder failed",
    "Cannot init CUDA",
    "Error while opening encoder",        # generic; nvenc often surfaces here
    "Function not implemented",           # nvenc on a driver missing the codec
    "out of memory",                      # GPU OOM under load -> spill to CPU
)

# Allow ops to force a path via env (debug / pin a host to CPU):
#   FFMPEG_ENCODER_POLICY = auto | gpu | cpu   (default auto = gpu-first)
_POLICY = os.environ.get("FFMPEG_ENCODER_POLICY", "auto").lower()


@dataclass
class EncodeResult:
    ok: bool
    encoder: str            # 'h264_nvenc' | 'libx264'
    returncode: int
    stderr: str = ""
    fell_back: bool = False  # True if GPU was tried and we dropped to CPU


def _nvenc_video_flags(quality: str = "medium") -> list[str]:
    """h264_nvenc encode flags. Kept conservative + broadly compatible."""
    return [
        "-c:v", "h264_nvenc",
        "-preset", "p4",          # balanced nvenc preset
        "-rc", "vbr", "-cq", "23",
        "-b:v", "0",
        "-pix_fmt", "yuv420p",
    ]


def _libx264_video_flags(quality: str = "medium") -> list[str]:
    """Software encode flags, output-equivalent to the nvenc path."""
    return [
        "-c:v", "libx264",
        "-preset", quality,       # e.g. 'medium'
        "-crf", "23",
        "-pix_fmt", "yuv420p",
    ]


def video_encoder_flags(prefer_gpu: bool, quality: str = "medium") -> tuple[str, list[str]]:
    """Return (encoder_name, flags) for the chosen path."""
    if prefer_gpu:
        return "h264_nvenc", _nvenc_video_flags(quality)
    return "libx264", _libx264_video_flags(quality)


def _looks_like_nvenc_failure(stderr: str) -> bool:
    s = stderr or ""
    return any(m.lower() in s.lower() for m in _NVENC_FAIL_MARKERS)


def run_encode(
    *,
    ffmpeg: str,
    input_args: list[str],
    output_args: list[str],
    output_path: str,
    filter_args: Optional[list[str]] = None,
    audio_args: Optional[list[str]] = None,
    quality: str = "medium",
    timeout: Optional[int] = None,
) -> EncodeResult:
    """Run an ffmpeg ENCODE with GPU-first / CPU-failover.

    The caller supplies everything EXCEPT the video-codec flags (this helper owns
    those, since it owns the GPU-vs-CPU decision):
      input_args  : e.g. ['-i', src]  (plus any '-ss'/'-t' before -i)
      filter_args : e.g. ['-vf', 'scale=1920:-2']  (optional)
      audio_args  : e.g. ['-c:a', 'aac', '-b:a', '192k']  (optional)
      output_args : container/muxing flags BEFORE the output path (e.g. ['-movflags','+faststart'])
      output_path : final file

    Returns EncodeResult with which encoder actually ran (recorded by tasks into
    the job ledger as `encoder`, so saturation is observable).
    """
    filter_args = filter_args or []
    audio_args = audio_args or []

    def _build(encoder_name: str, vflags: list[str]) -> list[str]:
        return [ffmpeg, "-y", *input_args, *filter_args, *vflags, *audio_args,
                *output_args, output_path]

    # Decide order based on policy.
    if _POLICY == "cpu":
        attempts = [("libx264", _libx264_video_flags(quality))]
    elif _POLICY == "gpu":
        attempts = [("h264_nvenc", _nvenc_video_flags(quality))]
    else:  # auto = gpu-first, cpu-failover
        attempts = [
            ("h264_nvenc", _nvenc_video_flags(quality)),
            ("libx264", _libx264_video_flags(quality)),
        ]

    last: Optional[EncodeResult] = None
    for idx, (enc, vflags) in enumerate(attempts):
        cmd = _build(enc, vflags)
        log.info("ffmpeg encode attempt enc=%s: %s", enc, " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode == 0:
            return EncodeResult(ok=True, encoder=enc, returncode=0,
                                stderr=proc.stderr or "",
                                fell_back=(idx > 0))
        last = EncodeResult(ok=False, encoder=enc, returncode=proc.returncode,
                            stderr=proc.stderr or "")
        # Only fall through to CPU if this was the GPU attempt AND the failure
        # looks like an nvenc-availability issue (not a real input/filter error).
        more = idx + 1 < len(attempts)
        if enc == "h264_nvenc" and more:
            if _looks_like_nvenc_failure(proc.stderr):
                log.warning("nvenc unavailable/saturated -> failing over to libx264")
                continue
            # A non-nvenc error (bad input, bad filter) won't be fixed by CPU —
            # don't waste a second full encode; surface the real error.
            log.error("ffmpeg GPU encode failed (not an nvenc-availability error); "
                      "NOT failing over. stderr tail: %s", (proc.stderr or "")[-400:])
            break
        else:
            log.error("ffmpeg encode failed enc=%s rc=%s", enc, proc.returncode)
            break

    return last or EncodeResult(ok=False, encoder="?", returncode=1,
                                stderr="no attempt ran")
