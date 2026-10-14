"""Shared APK artifact naming and path safety (fixes audit S5).

Rules:
- Final APK filenames derive from server-generated ids only; user-provided
  display names (watch face name, package, prompt...) never participate in
  filesystem paths.
- Every path is resolve()-checked to stay inside APK_OUTPUT_DIR.
- Download-facing filenames are whitelist-validated before any file access
  (defends GET /api/download and /api/qrcode against ``..`` traversal,
  absolute paths, Windows drive letters and URL-encoded payloads).
"""

import re
import tempfile
import uuid
from pathlib import Path

# Single output root shared by all build entry points.
APK_OUTPUT_DIR = Path(tempfile.gettempdir()) / "watchface-forge-apks"
APK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Server-generated task ids: uuid hex, truncated to 8..32 chars (build.py
# uses 8, tasks.py payload ids are 12, wff.py build ids are 12).
_TASK_ID_RE = re.compile(r"^[a-f0-9]{8,32}$")

# One path segment of a safe APK filename: no separators, no leading dot,
# no traversal sequences possible (first char must be alnum).
_APK_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class UnsafeArtifactPath(ValueError):
    """Raised when a derived or requested artifact path escapes the output root."""


def _resolve_within_root(candidate: Path) -> Path:
    root = APK_OUTPUT_DIR.resolve()
    resolved = candidate.resolve()
    if resolved != root and root not in resolved.parents:
        raise UnsafeArtifactPath(
            f"artifact path escapes output root: {candidate}"
        )
    return resolved


def task_id_dir(task_id: str) -> Path:
    """Per-task scratch directory ``APK_OUTPUT_DIR/<task_id>``.

    task_id must be a server-generated uuid hex id; anything else is rejected
    before it can influence a path.
    """
    task_id = str(task_id)
    if not _TASK_ID_RE.fullmatch(task_id):
        raise UnsafeArtifactPath(f"invalid task id: {task_id!r}")
    path = APK_OUTPUT_DIR / task_id
    _resolve_within_root(path)
    return path


def final_apk_path(task_id: str) -> Path:
    """Final APK path ``APK_OUTPUT_DIR/<task_id>.apk`` (display-name-free)."""
    task_id = str(task_id)
    if not _TASK_ID_RE.fullmatch(task_id):
        raise UnsafeArtifactPath(f"invalid task id: {task_id!r}")
    path = APK_OUTPUT_DIR / f"{task_id}.apk"
    _resolve_within_root(path)
    return path


def wff_final_apk_path(package_segment: str, build_id: str) -> Path:
    """wff.py v1 entry: ``<package-last-segment>-<build_id>.apk``.

    package_segment must already be whitelisted by the caller (lowercase Java
    package segment); build_id is a uuid hex id generated server-side.
    """
    build_id = str(build_id)
    if not _TASK_ID_RE.fullmatch(build_id):
        raise UnsafeArtifactPath(f"invalid build id: {build_id!r}")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", str(package_segment)):
        raise UnsafeArtifactPath(f"invalid package segment: {package_segment!r}")
    filename = f"{package_segment}-{build_id}.apk"
    if not _APK_SEGMENT_RE.fullmatch(filename):
        raise UnsafeArtifactPath(f"unsafe apk filename: {filename!r}")
    path = APK_OUTPUT_DIR / filename
    _resolve_within_root(path)
    return path


def resolve_download_filename(filename: str) -> Path:
    """Validate a download-facing filename and return its absolute path.

    Rejects traversal (``../``), absolute paths, Windows drive letters,
    separators and any non-whitelisted characters BEFORE any filesystem
    access, then re-checks via resolve() as defense in depth.
    """
    filename = str(filename)
    if not _APK_SEGMENT_RE.fullmatch(filename) or not filename.endswith(".apk"):
        raise UnsafeArtifactPath(f"unsafe download filename: {filename!r}")
    if filename.startswith("."):
        raise UnsafeArtifactPath(f"unsafe download filename: {filename!r}")
    # Belt and braces: '/','\\', ':' never pass the regex, but keep the intent
    # explicit against future regex edits.
    if any(ch in filename for ch in ("/", "\\", ":")):
        raise UnsafeArtifactPath(f"unsafe download filename: {filename!r}")
    path = APK_OUTPUT_DIR / filename
    return _resolve_within_root(path)


def new_task_id(length: int = 8) -> str:
    """Generate a fresh server-side task id (uuid hex, truncated)."""
    return uuid.uuid4().hex[:length]
