"""Stable/beta release selection and update channel UI regressions."""

import json
import hashlib
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel

from src.storage import StorageManager
from src.utils.updater import (
    CheckUpdateThread, compare_release_versions, fetch_latest_release,
    is_newer_version, parse_release_version,
)
from src.views.settings_view import SettingsView
from src.components.update_dialog import UpdateDialog


app = QApplication.instance() or QApplication([])


def api_response(data):
    response = MagicMock()
    value = response.__enter__.return_value
    value.status = 200
    value.read.return_value = json.dumps(data).encode("utf-8")
    return response


def release(tag, prerelease=False, draft=False, assets=None):
    return {
        "tag_name": tag,
        "name": f"WorkBOXig {tag}",
        "prerelease": prerelease,
        "draft": draft,
        "html_url": f"https://github.com/FN1p/WorkBOXig/releases/tag/{tag}",
        "assets": assets or [],
    }


class UpdateChannelsTest(unittest.TestCase):
    def test_semver_prerelease_precedence(self):
        for older, newer in (
            ("1.4.7", "1.5.0-beta.1"),
            ("1.5.0-alpha.9", "1.5.0-beta.1"),
            ("1.5.0-beta.1", "1.5.0-beta.2"),
            ("1.5.0-beta.2", "1.5.0-rc.1"),
            ("1.5.0-rc.1", "1.5.0"),
            ("1.5.0", "1.5.1"),
            ("1.5.0-beta.9", "1.5.0-beta.10"),
        ):
            with self.subTest(older=older, newer=newer):
                self.assertLess(compare_release_versions(older, newer), 0)
                self.assertTrue(is_newer_version(newer, older))
                self.assertFalse(is_newer_version(older, newer))
        self.assertEqual(compare_release_versions("v1.5.0", "1.5.0+build.4"), 0)
        self.assertIsNone(parse_release_version("not a version"))
        self.assertFalse(is_newer_version("nonsense", "1.4.7"))

    def test_stable_channel_uses_only_github_latest(self):
        with patch("src.utils.updater.urllib.request.urlopen",
                   return_value=api_response(release("v1.4.7"))) as urlopen:
            info = fetch_latest_release("FN1p/WorkBOXig", channel="stable")
        self.assertTrue(urlopen.call_args.args[0].full_url.endswith("/releases/latest"))
        self.assertEqual(info["channel"], "stable")
        self.assertFalse(info["prerelease"])

    def test_beta_channel_selects_highest_non_draft_semver(self):
        options = [
            release("v2.0.0-beta.1", prerelease=True, draft=True),
            release("v1.4.7"),
            release("v1.5.0-beta.2", prerelease=True),
            release("v1.5.0-beta.10", prerelease=True),
            release("v1.5.0-beta.3", prerelease=True),
            release("v0.invalid"),
        ]
        with patch("src.utils.updater.urllib.request.urlopen",
                   return_value=api_response(options)) as urlopen:
            info = fetch_latest_release("FN1p/WorkBOXig", channel="beta")
        self.assertIn("/releases?per_page=100", urlopen.call_args.args[0].full_url)
        self.assertEqual(info["tag_name"], "v1.5.0-beta.10")
        self.assertTrue(info["prerelease"])
        self.assertEqual(info["channel"], "beta")

    def test_beta_channel_includes_newer_stable_release(self):
        options = [
            release("v1.5.0-beta.2", prerelease=True),
            release("v1.5.0"),
        ]
        with patch("src.utils.updater.urllib.request.urlopen",
                   return_value=api_response(options)):
            info = fetch_latest_release("FN1p/WorkBOXig", channel="beta")
        self.assertEqual(info["tag_name"], "v1.5.0")
        self.assertFalse(info["prerelease"])

    def test_portable_executable_not_misidentified_as_installer(self):
        assets = [{
            "name": "WorkBOXig.exe",
            "browser_download_url": "https://github.com/FN1p/WorkBOXig/releases/download/v1.5.0/WorkBOXig.exe",
            "size": 123,
        }]
        with patch("src.utils.updater.urllib.request.urlopen",
                   return_value=api_response(release("v1.5.0", assets=assets))):
            info = fetch_latest_release("FN1p/WorkBOXig", channel="stable")
        self.assertIsNone(info["installer_url"])
        self.assertIsNotNone(info["portable_url"])

    def test_release_metadata_exposes_installer_sha256(self):
        digest = hashlib.sha256(b"installer").hexdigest()
        assets = [{
            "name": "WorkBOXig_Setup.exe",
            "browser_download_url": "https://github.com/FN1p/WorkBOXig/releases/download/v1.5.0/WorkBOXig_Setup.exe",
            "digest": "sha256:" + digest,
            "size": 9,
        }]
        with patch("src.utils.updater.urllib.request.urlopen",
                   return_value=api_response(release("v1.5.0", assets=assets))):
            info = fetch_latest_release("FN1p/WorkBOXig")
        self.assertEqual(info["installer_sha256"], digest)

    def test_download_rejects_invalid_checksum(self):
        from src.utils.updater import DownloadUpdateThread
        response = MagicMock()
        resp = response.__enter__.return_value
        resp.headers = {"content-length": "3"}
        resp.read.side_effect = [b"abc", b""]
        worker = DownloadUpdateThread(
            "https://example.invalid/setup.exe", "WorkBOXig_Setup.exe",
            expected_size=3, expected_sha256="0" * 64,
        )
        errors, completed = [], []
        worker.error.connect(errors.append)
        worker.completed.connect(completed.append)
        with patch("src.utils.updater.urllib.request.urlopen", return_value=response):
            worker.run()
        self.assertIn("checksum mismatch", " ".join(errors))
        self.assertFalse(completed)

    def test_download_accepts_matching_checksum(self):
        from src.utils.updater import DownloadUpdateThread
        import shutil
        response = MagicMock()
        resp = response.__enter__.return_value
        resp.headers = {}
        resp.read.side_effect = [b"abc", b""]
        worker = DownloadUpdateThread(
            "https://example.invalid/setup.exe", "WorkBOXig_Setup.exe",
            expected_size=3, expected_sha256=hashlib.sha256(b"abc").hexdigest(),
        )
        errors, completed = [], []
        worker.error.connect(errors.append)
        worker.completed.connect(completed.append)
        with patch("src.utils.updater.urllib.request.urlopen", return_value=response):
            worker.run()
        self.assertFalse(errors)
        self.assertEqual(len(completed), 1)
        shutil.rmtree(os.path.dirname(completed[0]), ignore_errors=True)

    def test_worker_passes_beta_channel(self):
        with patch("src.utils.updater.fetch_latest_release",
                   return_value={"is_newer": False}) as fetcher:
            worker = CheckUpdateThread(channel="beta")
            worker.run()
        self.assertEqual(fetcher.call_args.kwargs["channel"], "beta")

    def test_beta_opt_in_persists_and_displays_in_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = StorageManager(storage_dir=tmp)
            with patch("src.views.settings_view.get_storage", return_value=storage):
                view = SettingsView()
                self.assertFalse(view.beta_updates_cb.isChecked())
                view.beta_updates_cb.setChecked(True)
                self.assertEqual(storage.get_setting("update_channel"), "beta")
                self.assertTrue(storage.save_immediately())
                view.close()
                view.deleteLater()
            storage._debounce_timer.stop()
            reloaded = StorageManager(storage_dir=tmp)
            self.assertEqual(reloaded.get_setting("update_channel"), "beta")
            reloaded._debounce_timer.stop()

    def test_prerelease_shows_warning(self):
        dialog = UpdateDialog(release("v1.5.0-beta.2", prerelease=True))
        notice = dialog.findChild(QLabel, "update_beta_warning")
        self.assertIsNotNone(notice)
        self.assertTrue(notice.text())
        dialog.close()
        dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
