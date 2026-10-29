"""Portable WorkBOXig archives with notebook attachments."""

import json
import os
import re
import uuid
import zipfile
from pathlib import Path
from urllib.parse import unquote


ARCHIVE_SUFFIXES = {".zip", ".workboxig"}
MAX_STORAGE_BYTES = 20 * 1024 * 1024
MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_BYTES = 500 * 1024 * 1024
_ATTACHMENT_URL = re.compile(r"file://[^\s\"'<>]+/attachments/([^/\s\"'<>?#]+)", re.IGNORECASE)


def is_archive(path: str) -> bool:
    return Path(path).suffix.lower() in ARCHIVE_SUFFIXES


def write_archive(path: str, data: dict, attachments_dir: str) -> None:
    """Write a complete archive without following attachment symlinks."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("storage.json", json.dumps(data, ensure_ascii=False, indent=2))
        for entry in sorted(Path(attachments_dir).iterdir()):
            if entry.is_file() and not entry.is_symlink():
                archive.write(entry, f"attachments/{entry.name}")


def read_archive(path: str) -> tuple[dict, dict[str, bytes]]:
    """Read only the expected entries and cap decompressed attachment sizes."""
    attachments = {}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if sum(info.file_size for info in infos) > MAX_ARCHIVE_BYTES:
            raise ValueError("Backup archive is too large")
        if len([info for info in infos if info.filename == "storage.json"]) != 1:
            raise ValueError("Backup archive has no unique storage.json")
        storage_info = next(info for info in infos if info.filename == "storage.json")
        if storage_info.file_size > MAX_STORAGE_BYTES:
            raise ValueError("Backup metadata is too large")
        with archive.open(storage_info) as handle:
            raw = handle.read(MAX_STORAGE_BYTES + 1)
        if len(raw) > MAX_STORAGE_BYTES:
            raise ValueError("Backup metadata is too large")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Backup metadata must be an object")
        for info in infos:
            if info.filename == "storage.json" or info.is_dir():
                continue
            name = info.filename.removeprefix("attachments/")
            if (not info.filename.startswith("attachments/") or not name
                    or name in {".", ".."} or not re.fullmatch(r"[\w.-]+", name)
                    or info.file_size > MAX_ATTACHMENT_BYTES or name in attachments):
                raise ValueError("Unsafe attachment in backup archive")
            attachments[name] = archive.read(info)
    return data, attachments


def rewrite_attachment_urls(data: dict, old_to_new: dict[str, str]) -> dict:
    """Point notebook HTML at restored attachment files on this computer."""
    def replace(match):
        old_name = unquote(match.group(1))
        new_path = old_to_new.get(old_name)
        return Path(new_path).as_uri() if new_path else match.group(0)

    for notebook in data.get("notebooks", []):
        for page in notebook.get("pages", []):
            html = page.get("content_html")
            if isinstance(html, str):
                page["content_html"] = _ATTACHMENT_URL.sub(replace, html)
    return data


def new_attachment_name(original: str) -> str:
    return f"restored_{uuid.uuid4().hex}_{Path(original).name}"
