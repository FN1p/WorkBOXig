"""
In-App Updater for WorkBOXig.
Provides asynchronous update checking via GitHub Releases API, asset downloading
with real-time progress, automatic database pre-update backup, and zero-data-loss installation.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.error
import urllib.parse
import subprocess
import tempfile
import shutil
from typing import Optional, Dict, Any, Tuple
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication

from src.version import __version__, GITHUB_REPO, APP_NAME
from src.i18n import t


def parse_version_tuple(version_str: str) -> Tuple[int, ...]:
    """Parse version string into an integer tuple for accurate semver comparison."""
    clean = re.sub(r'^[vV]', '', version_str.strip())
    # Extract leading numbers
    parts = []
    for piece in clean.split('.'):
        num_match = re.match(r'^\d+', piece)
        if num_match:
            parts.append(int(num_match.group(0)))
        else:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer_version(latest_tag: str, current_version: str = __version__) -> bool:
    """Check if latest_tag from GitHub is strictly newer than current_version."""
    try:
        remote_tuple = parse_version_tuple(latest_tag)
        local_tuple = parse_version_tuple(current_version)
        return remote_tuple > local_tuple
    except Exception:
        return False


def fetch_latest_release(repo: str = GITHUB_REPO, timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch latest release metadata from GitHub Releases API.
    Raises urllib.error.URLError or ValueError on failure.
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        "User-Agent": f"{APP_NAME}-Updater/{__version__}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Optional token support for private repos or higher rate limits
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(api_url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                raise ValueError(f"HTTP error {response.status}")
            raw_data = response.read().decode("utf-8")
            data = json.loads(raw_data)
    except urllib.error.HTTPError as he:
        if he.code in (403, 429):
            # Seamless fallback to web redirect when unauthenticated API rate limit is reached
            try:
                web_req = urllib.request.Request(
                    f"https://github.com/{repo}/releases/latest",
                    headers={"User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) {APP_NAME}"}
                )
                with urllib.request.urlopen(web_req, timeout=timeout) as web_resp:
                    redirected = urllib.parse.urlparse(web_resp.geturl())
                    expected_prefix = f"/{repo}/releases/tag/"
                    # The /latest URL may redirect to the releases index when
                    # no published release exists. Never treat 'latest' as a tag.
                    if (redirected.scheme == "https"
                            and redirected.netloc == "github.com"
                            and redirected.path.startswith(expected_prefix)):
                        latest_tag = urllib.parse.unquote(
                            redirected.path[len(expected_prefix):]
                        )
                        if re.fullmatch(r"v?\d+\.\d+(?:\.\d+)?", latest_tag, re.IGNORECASE):
                            return {
                                "tag_name": latest_tag,
                                "title": f"WorkBOXig {latest_tag}",
                                "body": t("update_available_generic"),
                                "html_url": f"https://github.com/{repo}/releases/tag/{latest_tag}",
                                "published_at": "",
                                # A redirect does not tell us which assets exist.
                                # Offer the release page instead of inventing EXE links.
                                "installer_url": None,
                                "installer_name": None,
                                "installer_size": 0,
                                "portable_url": None,
                                "portable_name": None,
                                "portable_size": 0,
                                "is_newer": is_newer_version(latest_tag, __version__),
                            }
            except Exception:
                pass
            raise RuntimeError(t("update_rate_limit_error")) from he
        elif he.code == 404:
            raise RuntimeError(t("update_private_error")) from he
        raise RuntimeError(t("update_api_error", code=he.code)) from he
    except urllib.error.URLError as ue:
        raise RuntimeError(t("update_network_error", reason=ue.reason)) from ue

    tag_name = data.get("tag_name", "")
    assets = data.get("assets", [])

    # Identify primary installer and portable assets
    installer_url = None
    installer_name = None
    installer_size = 0

    portable_url = None
    portable_name = None
    portable_size = 0

    for asset in assets:
        name = asset.get("name", "")
        url = asset.get("browser_download_url", "")
        size = asset.get("size", 0)
        
        if "setup" in name.lower() and name.endswith(".exe"):
            installer_url = url
            installer_name = name
            installer_size = size
        elif name.endswith(".exe") and "setup" not in name.lower():
            portable_url = url
            portable_name = name
            portable_size = size

    # Fallback to any .exe asset if specific names aren't matched
    if not installer_url and not portable_url:
        for asset in assets:
            if asset.get("name", "").endswith(".exe"):
                installer_url = asset.get("browser_download_url")
                installer_name = asset.get("name")
                installer_size = asset.get("size", 0)
                break

    return {
        "tag_name": tag_name,
        "title": data.get("name", tag_name),
        "body": data.get("body", ""),
        "html_url": data.get("html_url", f"https://github.com/{repo}/releases"),
        "published_at": data.get("published_at", ""),
        "installer_url": installer_url,
        "installer_name": installer_name,
        "installer_size": installer_size,
        "portable_url": portable_url,
        "portable_name": portable_name,
        "portable_size": portable_size,
        "is_newer": is_newer_version(tag_name, __version__)
    }


class CheckUpdateThread(QThread):
    """Background worker for asynchronous update checks."""
    update_available = pyqtSignal(dict)
    up_to_date = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, repo: str = GITHUB_REPO, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.repo = repo

    def run(self):
        try:
            info = fetch_latest_release(self.repo)
            if info["is_newer"]:
                self.update_available.emit(info)
            else:
                self.up_to_date.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class DownloadUpdateThread(QThread):
    """Background worker for downloading the update asset with real-time progress."""
    progress = pyqtSignal(int, int, float)  # downloaded, total, percentage
    completed = pyqtSignal(str)           # local file path
    error = pyqtSignal(str)

    def __init__(self, download_url: str, filename: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.download_url = download_url
        self.filename = filename
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        # Release metadata supplies the filename; never let it escape our
        # isolated download directory or reuse another update's partial file.
        if not re.fullmatch(r"[\w .()-]+\.exe", self.filename, re.IGNORECASE):
            self.error.emit("Invalid update filename")
            return
        temp_dir = tempfile.mkdtemp(prefix="workboxig_update_")
        dest_path = os.path.join(temp_dir, self.filename)
        partial_path = dest_path + ".download"

        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"{APP_NAME}-Updater/{__version__}"}
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                total_size = int(resp.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 65536  # 64 KB

                with open(partial_path, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            break

                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        pct = (downloaded / total_size * 100.0) if total_size > 0 else 0.0
                        self.progress.emit(downloaded, total_size, pct)

            if self._is_cancelled:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return
            if downloaded == 0 or (total_size > 0 and downloaded != total_size):
                raise IOError("Update download was empty or incomplete")
            os.replace(partial_path, dest_path)
            self.completed.emit(dest_path)

        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self.error.emit(str(e))


def launch_installer_and_quit(installer_path: str, storage=None) -> bool:
    """
    Safely backup user data and launch the installer executable, then quit the running app.
    All user data in ~/.workboxig is untouched by the installer.
    """
    try:
        if storage is not None and hasattr(storage, "create_pre_update_backup"):
            try:
                storage.create_pre_update_backup()
            except Exception as be:
                # Do not close the app or start an installer without a
                # recoverable copy of the user's current data.
                print(f"[Updater] Pre-update backup failed; update cancelled: {be}")
                return False

        # Launch the installer in detached mode
        if sys.platform == "win32":
            subprocess.Popen(
                [installer_path],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            subprocess.Popen([installer_path])

        # Gracefully quit current application
        app = QApplication.instance()
        if app:
            app.quit()
        return True
    except Exception as e:
        print(f"[Updater] Failed to launch installer: {e}")
        return False
