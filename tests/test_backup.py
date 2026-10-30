"""Portable backup format tests without a Qt dependency."""

import json
import os
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path

from src.utils.backup import read_archive, rewrite_attachment_urls, write_archive


class BackupArchiveTests(unittest.TestCase):
    def test_archive_contains_attachments_and_rewrites_image_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            attachments = Path(directory, "attachments")
            attachments.mkdir()
            (attachments / "image.png").write_bytes(b"image bytes")
            data = {"notebooks": [{"pages": [{"content_html":
                '<img src="file:///C:/old/attachments/image.png">'}]}]}
            path = str(Path(directory, "backup.workboxig"))
            write_archive(path, data, str(attachments))
            loaded, files = read_archive(path)
            self.assertEqual(files, {"image.png": b"image bytes"})
            restored = str(Path(directory, "restored.png"))
            rewrite_attachment_urls(loaded, {"image.png": restored})
            self.assertIn(Path(restored).as_uri(), loaded["notebooks"][0]["pages"][0]["content_html"])

    def test_export_rejects_metadata_that_import_cannot_read(self):
        with tempfile.TemporaryDirectory() as directory:
            attachments = Path(directory, "attachments")
            attachments.mkdir()
            target = str(Path(directory, "backup.workboxig"))
            with patch("src.utils.backup.MAX_STORAGE_BYTES", 24):
                with self.assertRaisesRegex(ValueError, "metadata is too large"):
                    write_archive(target, {"text": "é" * 32}, str(attachments))
            self.assertFalse(Path(target).exists())

    def test_export_rejects_attachment_over_import_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            attachments = Path(directory, "attachments")
            attachments.mkdir()
            (attachments / "photo.png").write_bytes(b"x" * 32)
            target = str(Path(directory, "backup.workboxig"))
            with patch("src.utils.backup.MAX_ATTACHMENT_BYTES", 16):
                with self.assertRaisesRegex(ValueError, "attachment is too large"):
                    write_archive(target, {}, str(attachments))
            self.assertFalse(Path(target).exists())

    def test_export_rejects_aggregate_size_over_import_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            attachments = Path(directory, "attachments")
            attachments.mkdir()
            (attachments / "first.png").write_bytes(b"a" * 12)
            (attachments / "second.png").write_bytes(b"b" * 12)
            target = str(Path(directory, "backup.workboxig"))
            with patch("src.utils.backup.MAX_ARCHIVE_BYTES", 20):
                with self.assertRaisesRegex(ValueError, "archive is too large"):
                    write_archive(target, {}, str(attachments))
            self.assertFalse(Path(target).exists())

    def test_export_rejects_attachment_name_import_would_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            attachments = Path(directory, "attachments")
            attachments.mkdir()
            (attachments / "photo with space.png").write_bytes(b"image")
            target = str(Path(directory, "backup.workboxig"))
            with self.assertRaisesRegex(ValueError, "Unsafe attachment name"):
                write_archive(target, {}, str(attachments))
            self.assertFalse(Path(target).exists())

    def test_archive_rejects_non_object_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "invalid.workboxig")
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("storage.json", "[]")
            with self.assertRaisesRegex(ValueError, "must be an object"):
                read_archive(path)

    def test_archive_rejects_oversized_metadata_before_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "huge.workboxig")
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("storage.json", "x" * 256)
            with patch("src.utils.backup.MAX_STORAGE_BYTES", 128):
                with self.assertRaisesRegex(ValueError, "metadata is too large"):
                    read_archive(path)

    def test_archive_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "bad.workboxig")
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("storage.json", json.dumps({}))
                archive.writestr("attachments/../outside.txt", "unsafe")
            with self.assertRaises(ValueError):
                read_archive(path)


if __name__ == "__main__":
    unittest.main()
