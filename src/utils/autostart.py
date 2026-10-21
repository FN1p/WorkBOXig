"""
Windows Autostart Integration for WorkBOXig.
Configures automatic launch at Windows user logon via the Registry:
HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
"""

import sys
import os

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

REG_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "WorkBOXig"


def is_autostart_supported() -> bool:
    """Return whether the current platform supports Windows registry autostart."""
    return sys.platform == "win32" and HAS_WINREG


def is_autostart_enabled() -> bool:
    """Check if WorkBOXig is currently registered in Windows Run key."""
    if not is_autostart_supported():
        return False

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_SUBKEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, APP_REG_NAME)
            return bool(value and len(value.strip()) > 0)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[Autostart Check Error]: {e}")
        return False


def set_autostart_enabled(enabled: bool) -> bool:
    """
    Enable or disable autostart in the Windows user registry.
    Returns True if operation succeeded, False otherwise.
    """
    if not is_autostart_supported():
        return False

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_SUBKEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                # Determine command string
                exe_path = os.path.abspath(sys.executable)
                # If running as uncompiled python script
                if exe_path.lower().endswith("python.exe") or exe_path.lower().endswith("pythonw.exe"):
                    main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "main.py"))
                    cmd = f'"{exe_path}" "{main_script}"'
                else:
                    # Compiled PyInstaller executable
                    cmd = f'"{exe_path}"'

                winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
                return True
            else:
                try:
                    winreg.DeleteValue(key, APP_REG_NAME)
                except FileNotFoundError:
                    pass
                return True
    except Exception as e:
        print(f"[Autostart Update Error]: {e}")
        return False
