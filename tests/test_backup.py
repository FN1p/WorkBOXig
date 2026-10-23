"""Portable backup format tests without a Qt dependency."""

import json
import os
import tempfile
import unittest
import zipfile
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
