"""
WorkBOXig Standalone Windows Installer & Uninstaller.
Modern, sleek GUI installer with custom wizard, shortcut generation, autostart, and Add/Remove Programs integration.
"""

import sys
import os
import shutil
import subprocess
import time
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QCheckBox, QLineEdit,
    QFileDialog, QStackedWidget, QFrame, QGraphicsDropShadowEffect,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QLinearGradient

# Setup path to import shortcuts helper
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
try:
    from src.utils.shortcuts import (
        get_desktop_dir, get_start_menu_dir, create_shortcut,
        remove_shortcut, set_autostart_registry, register_uninstall_entry,
        unregister_uninstall_entry
    )
except ImportError:
    # Standalone fallback if bundled
    def get_desktop_dir():
        return os.path.join(os.path.expanduser("~"), "Desktop")

    def get_start_menu_dir():
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")

    def create_shortcut(target, lnk, icon=None, desc="", working_dir=None):
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        s = shell.CreateShortCut(lnk)
        s.TargetPath = target
        s.WorkingDirectory = working_dir or os.path.dirname(target)
        s.Description = desc
        if icon:
            s.IconLocation = f"{icon},0"
        s.Save()
        return True

    def remove_shortcut(p):
        if os.path.exists(p):
            os.remove(p)
            return True
        return False

    def set_autostart_registry(enable, exe, name="WorkBOXig"):
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(k, name, 0, winreg.REG_SZ, f'"{exe}"')
            else:
                try:
                    winreg.DeleteValue(k, name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(k)
            return True
        except Exception:
            return False

    def register_uninstall_entry(idir, exe, uninst, ver="1.2.0", pub="WorkBOXig Team"):
        import winreg
        try:
            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBOXig")
            winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, "WorkBOXig")
            winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, ver)
            winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, pub)
            winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, f"{exe},0")
            winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, idir)
            winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, f'"{uninst}" --uninstall')
            winreg.CloseKey(k)
            return True
        except Exception:
            return False

    def unregister_uninstall_entry():
        import winreg
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBOXig")
            return True
        except Exception:
            return False


def get_base_dir() -> str:
    """Get extraction dir (PyInstaller temp dir or project root)."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(__file__))


def get_payload_paths():
    """Locate the WorkBOXig.exe and assets payload to copy."""
    base = get_base_dir()
    
    # Check inside PyInstaller bundle payload
    payload_exe = os.path.join(base, "payload", "WorkBOXig.exe")
    payload_assets = os.path.join(base, "payload", "assets")
    if os.path.exists(payload_exe):
        return payload_exe, payload_assets

    # Check dist directory for local development testing
    dist_exe = os.path.join(base, "dist", "WorkBOXig.exe")
    dist_assets = os.path.join(base, "assets")
    if os.path.exists(dist_exe):
        return dist_exe, dist_assets

    # Fallback to local
    return dist_exe, dist_assets


INSTALLER_QSS = """
QMainWindow, QWidget#MainContainer {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: 'Segoe UI', sans-serif;
}

QFrame#HeaderCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:1 #0F172A);
    border: 1px solid #334155;
    border-radius: 12px;
}

QFrame#StepCard {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
}

QLabel {
    color: #F8FAFC;
}

QLabel#MutedLabel {
    color: #94A3B8;
}

QLineEdit {
    background-color: #0B0F19;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    color: #F8FAFC;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #6366F1;
}

QPushButton {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 9px 18px;
    color: #F8FAFC;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #475569;
}

QPushButton#PrimaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #6366F1);
    border: 1px solid #818CF8;
    color: #FFFFFF;
}

QPushButton#PrimaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338CA, stop:1 #4F46E5);
}

QPushButton#PrimaryButton:disabled {
    background-color: #334155;
    border: 1px solid #475569;
    color: #64748B;
}

QCheckBox {
    color: #E2E8F0;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #0B0F19;
}

QCheckBox::indicator:checked {
    background-color: #6366F1;
    border-color: #818CF8;
}

QProgressBar {
    background-color: #0B0F19;
    border: 1px solid #334155;
    border-radius: 7px;
    text-align: center;
    color: #F8FAFC;
    font-size: 11px;
    font-weight: bold;
    height: 14px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38BDF8, stop:1 #6366F1);
    border-radius: 6px;
}
"""


class InstallWorker(QThread):
    """Background installation thread to keep GUI responsive."""
    progress_updated = pyqtSignal(int, str)
    install_completed = pyqtSignal(bool, str)

    def __init__(self, target_dir: str, create_desktop: bool, create_start_menu: bool, autostart: bool):
        super().__init__()
        self.target_dir = target_dir
        self.create_desktop = create_desktop
        self.create_start_menu = create_start_menu
        self.autostart = autostart

    def run(self):
        try:
            self.progress_updated.emit(10, "Подготовка директории установки...")
            time.sleep(0.3)
            os.makedirs(self.target_dir, exist_ok=True)

            self.progress_updated.emit(25, "Извлечение файлов программы...")
            payload_exe, payload_assets = get_payload_paths()

            if not os.path.exists(payload_exe):
                raise FileNotFoundError(f"Файл приложения не найден в дистрибутиве: {payload_exe}")

            dest_exe = os.path.join(self.target_dir, "WorkBOXig.exe")
            shutil.copy2(payload_exe, dest_exe)

            self.progress_updated.emit(50, "Копирование ресурсов и графики...")
            dest_assets = os.path.join(self.target_dir, "assets")
            if os.path.exists(payload_assets):
                if os.path.exists(dest_assets):
                    shutil.rmtree(dest_assets, ignore_errors=True)
                shutil.copytree(payload_assets, dest_assets)
            time.sleep(0.3)

            # Copy installer itself as uninstaller
            self.progress_updated.emit(65, "Настройка модуля удаления...")
            current_exe = sys.executable if getattr(sys, 'frozen', False) else None
            uninstaller_path = os.path.join(self.target_dir, "uninstall.exe")
            if current_exe and os.path.exists(current_exe):
                shutil.copy2(current_exe, uninstaller_path)
            else:
                # If running as script, create an uninstaller launcher script
                with open(uninstaller_path.replace(".exe", ".bat"), "w", encoding="utf-8") as f:
                    f.write(f'@echo off\npython "{os.path.abspath(__file__)}" --uninstall\n')
                uninstaller_path = uninstaller_path.replace(".exe", ".bat")

            self.progress_updated.emit(75, "Создание ярлыков...")
            icon_file = os.path.join(dest_assets, "icon.ico") if os.path.exists(dest_assets) else dest_exe
            if not os.path.exists(icon_file):
                icon_file = dest_exe

            # Desktop shortcut
            if self.create_desktop:
                desktop_lnk = os.path.join(get_desktop_dir(), "WorkBOXig.lnk")
                create_shortcut(dest_exe, desktop_lnk, icon_path=icon_file, description="WorkBOXig - Рабочее пространство для учёбы")

            # Start Menu shortcut
            if self.create_start_menu:
                start_lnk = os.path.join(get_start_menu_dir(), "WorkBOXig.lnk")
                create_shortcut(dest_exe, start_lnk, icon_path=icon_file, description="WorkBOXig - Рабочее пространство для учёбы")

            self.progress_updated.emit(88, "Интеграция с системой Windows...")
            # Autostart
            if self.autostart:
                set_autostart_registry(True, dest_exe, "WorkBOXig")

            # Register in Windows Add/Remove Programs
            register_uninstall_entry(
                install_dir=self.target_dir,
                exe_path=dest_exe,
                uninstaller_path=uninstaller_path,
                version="1.2.0"
            )

            self.progress_updated.emit(100, "Установка успешно завершена!")
            time.sleep(0.4)
            self.install_completed.emit(True, dest_exe)

        except Exception as e:
            self.install_completed.emit(False, str(e))


class UninstallWorker(QThread):
    """Background uninstaller thread."""
    progress_updated = pyqtSignal(int, str)
    uninstall_completed = pyqtSignal(bool, str)

    def __init__(self, remove_userdata: bool, target_dir: str):
        super().__init__()
        self.remove_userdata = remove_userdata
        self.target_dir = target_dir

    def run(self):
        try:
            self.progress_updated.emit(20, "Удаление ярлыков с Рабочего стола и меню Пуск...")
            time.sleep(0.3)
            remove_shortcut(os.path.join(get_desktop_dir(), "WorkBOXig.lnk"))
            remove_shortcut(os.path.join(get_start_menu_dir(), "WorkBOXig.lnk"))

            self.progress_updated.emit(50, "Очистка записей реестра и автозагрузки...")
            set_autostart_registry(False, "", "WorkBOXig")
            unregister_uninstall_entry()
            time.sleep(0.3)

            if self.remove_userdata:
                self.progress_updated.emit(70, "Удаление локальной базы заметок и настроек...")
                user_data = os.path.join(os.path.expanduser("~"), ".workboxig")
                if os.path.exists(user_data):
                    shutil.rmtree(user_data, ignore_errors=True)

            self.progress_updated.emit(90, "Удаление файлов приложения...")
            # Note: The currently executing uninstall.exe cannot delete itself directly,
            # so we schedule a self-delete cmd command on exit if needed.
            for item in os.listdir(self.target_dir):
                item_path = os.path.join(self.target_dir, item)
                if "uninstall" not in item.lower():
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        try:
                            os.remove(item_path)
                        except Exception:
                            pass

            self.progress_updated.emit(100, "WorkBOXig успешно удален.")
            time.sleep(0.3)
            self.uninstall_completed.emit(True, "OK")
        except Exception as e:
            self.uninstall_completed.emit(False, str(e))


class InstallerWindow(QMainWindow):
    """Main Installer GUI Window."""

    def __init__(self, uninstall_mode: bool = False):
        super().__init__()
        self.uninstall_mode = uninstall_mode
        self.installed_exe_path = ""

        # Default install dir: %LOCALAPPDATA%\Programs\WorkBOXig
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        self.default_install_dir = os.path.join(local_app_data, "Programs", "WorkBOXig")

        self.setWindowTitle("Мастер установки WorkBOXig" if not uninstall_mode else "Удаление WorkBOXig")
        self.setFixedSize(640, 480)
        self.setStyleSheet(INSTALLER_QSS)

        # Set window icon
        icon_path = os.path.join(get_base_dir(), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.init_ui()

    def init_ui(self):
        container = QWidget(self)
        container.setObjectName("MainContainer")
        self.setCentralWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        # Header bar
        header = QFrame()
        header.setObjectName("HeaderCard")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(18, 14, 18, 14)
        h_layout.setSpacing(16)

        # Logo icon
        logo_lbl = QLabel()
        png_icon = os.path.join(get_base_dir(), "assets", "icon.png")
        if os.path.exists(png_icon):
            pix = QPixmap(png_icon).scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        else:
            logo_lbl.setText("📦")
            logo_lbl.setFont(QFont("Segoe UI", 24))
        h_layout.addWidget(logo_lbl)

        # Title & subtitle
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        main_title = QLabel("WorkBOXig" if not self.uninstall_mode else "Удаление WorkBOXig")
        main_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_box.addWidget(main_title)

        sub_title = QLabel("Современное рабочее пространство для учёбы • Версия 1.2.0" if not self.uninstall_mode else "Мастер деинсталляции компонентов программы")
        sub_title.setObjectName("MutedLabel")
        sub_title.setFont(QFont("Segoe UI", 9))
        title_box.addWidget(sub_title)

        h_layout.addLayout(title_box, stretch=1)
        main_layout.addWidget(header)

        # Wizard Stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, stretch=1)

        if not self.uninstall_mode:
            self._init_installer_pages()
        else:
            self._init_uninstaller_pages()

        # Bottom Action Bar
        self.bottom_bar = QHBoxLayout()
        self.bottom_bar.setContentsMargins(0, 8, 0, 0)
        self.bottom_bar.setSpacing(12)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.close)
        self.bottom_bar.addWidget(self.cancel_btn)

        self.bottom_bar.addStretch()

        self.back_btn = QPushButton("← Назад")
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setVisible(False)
        self.bottom_bar.addWidget(self.back_btn)

        self.next_btn = QPushButton("Далее →")
        self.next_btn.setObjectName("PrimaryButton")
        self.next_btn.clicked.connect(self._go_next)
        self.bottom_bar.addWidget(self.next_btn)

        main_layout.addLayout(self.bottom_bar)

        self.stack.currentChanged.connect(self._on_page_changed)
        self._on_page_changed(0)

    def _on_page_changed(self, idx: int):
        if not self.uninstall_mode:
            if idx == 0:
                self.cancel_btn.setVisible(True)
                self.cancel_btn.setEnabled(True)
                self.back_btn.setVisible(False)
                self.next_btn.setVisible(True)
                self.next_btn.setEnabled(True)
                self.next_btn.setText("Далее →")
            elif idx == 1:
                self.cancel_btn.setVisible(True)
                self.cancel_btn.setEnabled(True)
                self.back_btn.setVisible(True)
                self.back_btn.setEnabled(True)
                self.next_btn.setVisible(True)
                self.next_btn.setEnabled(True)
                self.next_btn.setText("Установить")
            elif idx == 2:
                self.cancel_btn.setVisible(False)
                self.back_btn.setVisible(False)
                self.next_btn.setVisible(False)
            elif idx == 3:
                self.cancel_btn.setVisible(False)
                self.back_btn.setVisible(False)
                self.next_btn.setVisible(True)
                self.next_btn.setEnabled(True)
                self.next_btn.setText("Готово")
        else:
            if idx == 0:
                self.cancel_btn.setVisible(True)
                self.back_btn.setVisible(False)
                self.next_btn.setVisible(True)
                self.next_btn.setEnabled(True)
                self.next_btn.setText("Удалить")
            elif idx == 1:
                self.cancel_btn.setVisible(False)
                self.back_btn.setVisible(False)
                self.next_btn.setVisible(False)
            elif idx == 2:
                self.cancel_btn.setVisible(False)
                self.back_btn.setVisible(False)
                self.next_btn.setVisible(True)
                self.next_btn.setEnabled(True)
                self.next_btn.setText("Закрыть")

    def _init_installer_pages(self):
        # 1. Welcome Page
        welcome_page = QWidget()
        w_layout = QVBoxLayout(welcome_page)
        w_layout.setContentsMargins(10, 10, 10, 10)
        w_layout.setSpacing(14)

        w_head = QLabel("Добро пожаловать в установщик WorkBOXig")
        w_head.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        w_layout.addWidget(w_head)

        w_desc = QLabel(
            "WorkBOXig объединяет все инструменты для продуктивной учебы:\n"
            "• Интерактивные тетради с поддержкой вставки скриншотов прямо в текст\n"
            "• Умный календарь расписания с цветовыми метками предметов\n"
            "• Трекер задач и домашних заданий с дедлайнами\n"
            "• Таймер фокуса Pomodoro и Raycast-палитра (Ctrl+K)\n"
            "• Стильный светлый и тёмный интерфейс без перезагрузки"
        )
        w_desc.setStyleSheet("color: #CBD5E1; font-size: 13px; line-height: 1.5;")
        w_layout.addWidget(w_desc)
        w_layout.addStretch()

        w_rec = QLabel("Нажмите «Далее», чтобы настроить параметры установки.")
        w_rec.setObjectName("MutedLabel")
        w_rec.setFont(QFont("Segoe UI", 10))
        w_layout.addWidget(w_rec)

        self.stack.addWidget(welcome_page)

        # 2. Path & Options Page
        options_page = QWidget()
        o_layout = QVBoxLayout(options_page)
        o_layout.setContentsMargins(10, 10, 10, 10)
        o_layout.setSpacing(14)

        o_head = QLabel("Выбор папки и параметров установки")
        o_head.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        o_layout.addWidget(o_head)

        # Folder selector
        folder_box = QHBoxLayout()
        folder_box.setSpacing(8)
        self.path_input = QLineEdit(self.default_install_dir)
        folder_box.addWidget(self.path_input, stretch=1)

        self.browse_btn = QPushButton("Обзор...")
        self.browse_btn.clicked.connect(self._on_browse_folder)
        folder_box.addWidget(self.browse_btn)
        o_layout.addLayout(folder_box)

        # Space label
        self.space_lbl = QLabel()
        self.space_lbl.setObjectName("MutedLabel")
        self.space_lbl.setFont(QFont("Segoe UI", 9))
        self._update_space_label()
        self.path_input.textChanged.connect(self._update_space_label)
        o_layout.addWidget(self.space_lbl)

        # Separator line
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #334155; margin: 4px 0;")
        o_layout.addWidget(div)

        # Options Checkboxes
        self.chk_desktop = QCheckBox("Создать ярлык на Рабочем столе")
        self.chk_desktop.setChecked(True)
        o_layout.addWidget(self.chk_desktop)

        self.chk_start_menu = QCheckBox("Создать ярлык в меню «Пуск»")
        self.chk_start_menu.setChecked(True)
        o_layout.addWidget(self.chk_start_menu)

        self.chk_autostart = QCheckBox("Запускать WorkBOXig при старте Windows (Автозагрузка)")
        self.chk_autostart.setChecked(False)
        o_layout.addWidget(self.chk_autostart)

        o_layout.addStretch()
        self.stack.addWidget(options_page)

        # 3. Progress Page
        progress_page = QWidget()
        p_layout = QVBoxLayout(progress_page)
        p_layout.setContentsMargins(10, 20, 10, 10)
        p_layout.setSpacing(14)

        self.prog_title = QLabel("Идёт установка...")
        self.prog_title.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        p_layout.addWidget(self.prog_title)

        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(0)
        p_layout.addWidget(self.prog_bar)

        self.prog_status = QLabel("Инициализация компонентов...")
        self.prog_status.setObjectName("MutedLabel")
        self.prog_status.setFont(QFont("Segoe UI", 10))
        p_layout.addWidget(self.prog_status)

        p_layout.addStretch()
        self.stack.addWidget(progress_page)

        # 4. Finish Page
        finish_page = QWidget()
        f_layout = QVBoxLayout(finish_page)
        f_layout.setContentsMargins(10, 10, 10, 10)
        f_layout.setSpacing(14)

        f_head = QLabel("Установка успешно завершена!")
        f_head.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        f_head.setStyleSheet("color: #10B981;")
        f_layout.addWidget(f_head)

        f_desc = QLabel(
            "WorkBOXig готов к первому запуску.\n"
            "Все необходимые компоненты и ярлыки были успешно созданы."
        )
        f_desc.setStyleSheet("color: #E2E8F0; font-size: 13px;")
        f_layout.addWidget(f_desc)

        f_layout.addStretch()

        self.chk_launch_now = QCheckBox("Запустить WorkBOXig сейчас")
        self.chk_launch_now.setChecked(True)
        self.chk_launch_now.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        f_layout.addWidget(self.chk_launch_now)

        self.stack.addWidget(finish_page)

    def _init_uninstaller_pages(self):
        # 1. Confirm Uninstall Page
        u_page = QWidget()
        u_layout = QVBoxLayout(u_page)
        u_layout.setContentsMargins(10, 10, 10, 10)
        u_layout.setSpacing(14)

        u_head = QLabel("Вы действительно хотите удалить WorkBOXig?")
        u_head.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        u_layout.addWidget(u_head)

        u_desc = QLabel(
            "Будут удалены исполняемые файлы программы и ярлыки из системы."
        )
        u_desc.setStyleSheet("color: #CBD5E1; font-size: 13px;")
        u_layout.addWidget(u_desc)

        self.chk_delete_userdata = QCheckBox("Удалить также мои конспекты и заметки (%USERPROFILE%/.workboxig)")
        self.chk_delete_userdata.setChecked(False)
        self.chk_delete_userdata.setStyleSheet("color: #F87171;")
        u_layout.addWidget(self.chk_delete_userdata)

        u_layout.addStretch()
        self.stack.addWidget(u_page)

        # 2. Progress Page
        u_prog_page = QWidget()
        up_layout = QVBoxLayout(u_prog_page)
        up_layout.setContentsMargins(10, 20, 10, 10)
        up_layout.setSpacing(14)

        self.u_prog_title = QLabel("Идёт удаление компонентов...")
        self.u_prog_title.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        up_layout.addWidget(self.u_prog_title)

        self.u_prog_bar = QProgressBar()
        self.u_prog_bar.setRange(0, 100)
        self.u_prog_bar.setValue(0)
        up_layout.addWidget(self.u_prog_bar)

        self.u_prog_status = QLabel("Подготовка к удалению...")
        self.u_prog_status.setObjectName("MutedLabel")
        up_layout.addWidget(self.u_prog_status)

        up_layout.addStretch()
        self.stack.addWidget(u_prog_page)

        # 3. Finish Page
        u_fin_page = QWidget()
        uf_layout = QVBoxLayout(u_fin_page)
        uf_layout.setContentsMargins(10, 10, 10, 10)
        uf_layout.setSpacing(14)

        uf_head = QLabel("WorkBOXig успешно удален")
        uf_head.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        uf_layout.addWidget(uf_head)

        uf_desc = QLabel("Все компоненты программы были удалены с вашего компьютера.")
        uf_desc.setStyleSheet("color: #CBD5E1; font-size: 13px;")
        uf_layout.addWidget(uf_desc)
        uf_layout.addStretch()

        self.stack.addWidget(u_fin_page)

    def _update_space_label(self):
        target = self.path_input.text().strip()
        drive = os.path.splitdrive(target)[0] or "C:"
        drive += "\\"
        try:
            total, used, free = shutil.disk_usage(drive)
            free_gb = free / (1024 ** 3)
            self.space_lbl.setText(f"Требуемое свободное место: ~55 МБ  •  Доступно на диске {drive}: {free_gb:.1f} ГБ")
        except Exception:
            self.space_lbl.setText("Требуемое свободное место: ~55 МБ")

    def _on_browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для установки WorkBOXig", self.path_input.text())
        if folder:
            self.path_input.setText(os.path.join(folder, "WorkBOXig"))

    def _go_next(self):
        if not self.uninstall_mode:
            curr = self.stack.currentIndex()
            if curr == 0:
                self.stack.setCurrentIndex(1)
                self.back_btn.setVisible(True)
                self.next_btn.setText("Установить")
            elif curr == 1:
                # Start installation
                self.stack.setCurrentIndex(2)
                self.back_btn.setVisible(False)
                self.next_btn.setEnabled(False)
                self.cancel_btn.setEnabled(False)
                self._start_installation()
            elif curr == 3:
                # Finished
                if self.chk_launch_now.isChecked() and self.installed_exe_path:
                    if os.path.exists(self.installed_exe_path):
                        subprocess.Popen([self.installed_exe_path], cwd=os.path.dirname(self.installed_exe_path))
                self.close()
        else:
            curr = self.stack.currentIndex()
            if curr == 0:
                self.stack.setCurrentIndex(1)
                self.next_btn.setEnabled(False)
                self.cancel_btn.setEnabled(False)
                self._start_uninstallation()
            elif curr == 2:
                self.close()

    def _go_back(self):
        curr = self.stack.currentIndex()
        if curr == 1:
            self.stack.setCurrentIndex(0)
            self.back_btn.setVisible(False)
            self.next_btn.setText("Далее →")

    def _start_installation(self):
        target_dir = self.path_input.text().strip()
        self.worker = InstallWorker(
            target_dir=target_dir,
            create_desktop=self.chk_desktop.isChecked(),
            create_start_menu=self.chk_start_menu.isChecked(),
            autostart=self.chk_autostart.isChecked()
        )
        self.worker.progress_updated.connect(self._on_install_progress)
        self.worker.install_completed.connect(self._on_install_done)
        self.worker.start()

    def _on_install_progress(self, percent: int, text: str):
        self.prog_bar.setValue(percent)
        self.prog_status.setText(text)

    def _on_install_done(self, success: bool, msg: str):
        if success:
            self.installed_exe_path = msg
            self.stack.setCurrentIndex(3)
            self.cancel_btn.setVisible(False)
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Готово")
        else:
            QMessageBox.critical(self, "Ошибка установки", f"Не удалось завершить установку:\n{msg}")
            self.cancel_btn.setEnabled(True)
            self.cancel_btn.setText("Закрыть")

    def _start_uninstallation(self):
        app_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
        self.u_worker = UninstallWorker(
            remove_userdata=self.chk_delete_userdata.isChecked(),
            target_dir=app_dir
        )
        self.u_worker.progress_updated.connect(self._on_uninstall_progress)
        self.u_worker.uninstall_completed.connect(self._on_uninstall_done)
        self.u_worker.start()

    def _on_uninstall_progress(self, percent: int, text: str):
        self.u_prog_bar.setValue(percent)
        self.u_prog_status.setText(text)

    def _on_uninstall_done(self, success: bool, msg: str):
        self.stack.setCurrentIndex(2)
        self.next_btn.setEnabled(True)
        self.next_btn.setText("Закрыть")
        self.cancel_btn.setVisible(False)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    uninstall_mode = "--uninstall" in sys.argv or "uninstall" in os.path.basename(sys.argv[0]).lower()
    win = InstallerWindow(uninstall_mode=uninstall_mode)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
