"""
Shortcut and Windows integration utilities for WorkBOXig.
Handles Desktop / Start Menu .lnk creation, Autostart registry, and Windows Add/Remove registration.
"""

import os
import sys
import subprocess
import winreg
from typing import Optional


def get_desktop_dir() -> str:
    """Get the user's Desktop directory."""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    # Also check registry for relocated Desktop
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        val, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        val = os.path.expandvars(val)
        if os.path.exists(val):
            return val
    except Exception:
        pass
    return desktop


def get_start_menu_dir() -> str:
    """Get the user's Start Menu Programs directory."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    programs = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        val, _ = winreg.QueryValueEx(key, "Programs")
        winreg.CloseKey(key)
        val = os.path.expandvars(val)
        if os.path.exists(val):
            return val
    except Exception:
        pass
    return programs


def create_shortcut(
    target_path: str,
    shortcut_path: str,
    icon_path: Optional[str] = None,
    description: str = "WorkBOXig - Executive Work & Study OS",
    working_dir: Optional[str] = None
) -> bool:
    """Create a Windows .lnk shortcut with icon and description."""
    os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
    target_path = os.path.abspath(target_path)
    if working_dir is None:
        working_dir = os.path.dirname(target_path)
    if icon_path is None:
        icon_path = target_path

    # Method 1: win32com
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target_path
        shortcut.WorkingDirectory = working_dir
        shortcut.Description = description
        if icon_path and os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        shortcut.Save()
        return True
    except Exception:
        pass

    # Method 2: PowerShell fallback
    try:
        ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{shortcut_path}')
$s.TargetPath = '{target_path}'
$s.WorkingDirectory = '{working_dir}'
$s.Description = '{description}'
"""
        if icon_path and os.path.exists(icon_path):
            ps_script += f"\n$s.IconLocation = '{icon_path},0'"
        ps_script += "\n$s.Save()"

        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        return res.returncode == 0 and os.path.exists(shortcut_path)
    except Exception:
        return False


def remove_shortcut(shortcut_path: str) -> bool:
    """Remove a shortcut file if it exists."""
    try:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            return True
    except Exception:
        pass
    return False


def set_autostart_registry(enable: bool, exe_path: str, app_name: str = "WorkBOXig") -> bool:
    """Configure Windows Run registry key for user autostart."""
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            reg_path,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )
        if enable:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{os.path.abspath(exe_path)}"')
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_autostart_enabled(app_name: str = "WorkBOXig") -> bool:
    """Check if app autostart is enabled in registry."""
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
        _, _ = winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def register_uninstall_entry(
    install_dir: str,
    exe_path: str,
    uninstaller_path: str,
    version: str = "1.0.0",
    publisher: str = "PFT Studio"
) -> bool:
    """Register application in Windows Add/Remove Programs (Programs & Features)."""
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBOXig"
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "WorkBOXig")
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, version)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, publisher)
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f"{os.path.abspath(exe_path)},0")
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, os.path.abspath(install_dir))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{os.path.abspath(uninstaller_path)}"')
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def unregister_uninstall_entry() -> bool:
    """Remove application registration from Windows Add/Remove Programs."""
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBOXig"
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
        return True
    except FileNotFoundError:
        return True
    except Exception:
        return False


def clear_layout(layout):
    """Safely and immediately detaches and schedules deletion for all widgets in a QLayout."""
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        if item is not None:
            w = item.widget()
            if w is not None:
                # Hiding before detaching prevents a visible widget from
                # flashing as a separate top-level Windows window. Detach it
                # after hiding so stale children are not returned by Qt
                # findChildren() during the same refresh.
                w.hide()
                w.setParent(None)
                w.deleteLater()
            else:
                # A layout item may contain another layout (for example, a
                # subtask row). Its child widgets must be removed as well,
                # otherwise orphaned controls remain on screen after refresh.
                nested_layout = item.layout()
                if nested_layout is not None:
                    clear_layout(nested_layout)
                    nested_layout.deleteLater()
