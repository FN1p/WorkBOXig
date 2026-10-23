"""
Storage Engine for WorkBOXig.
Provides robust JSON-based persistence with atomic writes, auto-save debounce,
and PyQt signals for reactive multi-view synchronization.
"""

import os
import json
import uuid
import tempfile
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from src.i18n import t
from src.version import __version__
from src.utils.backup import is_archive, write_archive, read_archive, rewrite_attachment_urls, new_attachment_name


DEFAULT_DATA = {
    "version": __version__,
    "settings": {
        "theme": "dark",
        "language": "en",
        "font_size": 14,
        "auto_save_interval": 1000,
        "check_updates_on_startup": True,
        "google_calendar_url": "",
        "google_calendar_auto_sync": True
    },
    "notebooks": [],
    "notes": [],
    "tasks": [],
    "calendar_events": [],
    "recurring_lessons": []
}


def _validated_data(value: Any, require_complete: bool = False) -> Dict[str, Any]:
    """Accept older backups while checking top-level collection types."""
    if not isinstance(value, dict):
        raise ValueError("Storage must be a JSON object")
    if require_complete:
        required = {"settings", "notebooks", "notes", "tasks", "calendar_events"}
        if not required.issubset(value):
            raise ValueError("Backup is missing required data collections")
    result = dict(value)
    for key, default in DEFAULT_DATA.items():
        if key not in result:
            result[key] = json.loads(json.dumps(default))
        elif not isinstance(result[key], type(default)):
            raise ValueError(f"Invalid storage field: {key}")
        elif isinstance(default, list) and not all(isinstance(item, dict) for item in result[key]):
            raise ValueError(f"Invalid storage entries: {key}")
    return result


class StorageManager(QObject):
    """
    Central storage manager for WorkBOXig.
    Emits data_changed signals when records are added, modified, or removed.
    """
    data_changed = pyqtSignal(str) # entity_type: 'tasks', 'notebooks', 'notes', 'events', 'all'
    save_completed = pyqtSignal()

    def __init__(self, storage_dir: Optional[str] = None):
        super().__init__()
        
        # Priority: explicit storage_dir -> local 'data' dir if present -> ~/.workboxig
        if storage_dir:
            self.base_dir = storage_dir
        else:
            local_data_dir = os.path.join(os.getcwd(), "data")
            if os.path.isdir(local_data_dir):
                self.base_dir = local_data_dir
            else:
                self.base_dir = os.path.join(os.path.expanduser("~"), ".workboxig")
                
        os.makedirs(self.base_dir, exist_ok=True)
        self.file_path = os.path.join(self.base_dir, "storage.json")
        self.attachments_dir = os.path.join(self.base_dir, "attachments")
        os.makedirs(self.attachments_dir, exist_ok=True)
        
        # Debounced save timer (500 ms)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(500)
        self._debounce_timer.timeout.connect(self._do_atomic_save)

        self._data: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Loads data from disk or populates default data if missing."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._data = _validated_data(loaded)
                    return
            except Exception as e:
                print(f"[StorageManager] Error reading {self.file_path}: {e}. Initializing backup...")
                # Backup corrupted file
                try:
                    backup_path = self.file_path + f".bak-{int(datetime.now().timestamp())}"
                    os.rename(self.file_path, backup_path)
                except Exception:
                    pass

        # Populate with fresh default data
        self._data = json.loads(json.dumps(DEFAULT_DATA))
        self.save_immediately()

    def schedule_save(self, entity_type: str = "all"):
        """Schedules debounced save and notifies listeners."""
        self._debounce_timer.start()
        self.data_changed.emit(entity_type)

    def save_immediately(self):
        """Forces an immediate atomic save without waiting for timer."""
        self._debounce_timer.stop()
        return self._do_atomic_save()

    def _do_atomic_save(self):
        """Performs atomic file write to prevent corruption."""
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(dir=self.base_dir, prefix="save_", suffix=".tmp")
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.file_path)
            self.save_completed.emit()
            return True
        except Exception as e:
            print(f"[StorageManager] Failed to save data: {e}")
            return False
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def get_attachments_dir(self) -> str:
        """Returns directory path where notebook images and screenshots are stored."""
        os.makedirs(self.attachments_dir, exist_ok=True)
        return self.attachments_dir

    # ---------------- Settings & Backups ----------------
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieve a user setting with fallback default."""
        return self._data.get("settings", {}).get(key, default)

    def set_setting(self, key: str, value: Any):
        """Update a user setting and persist immediately."""
        if "settings" not in self._data:
            self._data["settings"] = {}
        self._data["settings"][key] = value
        self.save_immediately()
        self.data_changed.emit("settings")

    def export_full_backup(self, target_filepath: str):
        """Export a portable archive, or a legacy data-only JSON file."""
        target_dir = os.path.dirname(os.path.abspath(target_filepath))
        fd, temporary = tempfile.mkstemp(dir=target_dir, prefix="backup_", suffix=".tmp")
        os.close(fd)
        try:
            if is_archive(target_filepath):
                write_archive(temporary, self._data, self.attachments_dir)
            else:
                with open(temporary, "w", encoding="utf-8") as handle:
                    json.dump(self._data, handle, ensure_ascii=False, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())
            os.replace(temporary, target_filepath)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)

    def create_pre_update_backup(self) -> str:
        """Create an automatic timestamped backup of all user data before updating."""
        backup_name = f"storage.pre_update_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.workboxig"
        backup_path = os.path.join(self.base_dir, backup_name)
        self.export_full_backup(backup_path)
        return backup_path

    def import_full_backup(self, source_filepath: str) -> bool:
        """Import a portable archive or legacy JSON backup."""
        attachments = {}
        if is_archive(source_filepath):
            new_data, attachments = read_archive(source_filepath)
        else:
            with open(source_filepath, "r", encoding="utf-8") as f:
                new_data = json.load(f)
        try:
            new_data = _validated_data(new_data, require_complete=True)
        except ValueError:
            return False
        backup_path = os.path.join(
            self.base_dir,
            f"storage.pre_import_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.workboxig",
        )
        self.export_full_backup(backup_path)
        restored_paths = []
        try:
            replacements = {}
            for name, content in attachments.items():
                new_path = os.path.join(self.attachments_dir, new_attachment_name(name))
                restored_paths.append(new_path)
                with open(new_path, "xb") as handle:
                    handle.write(content)
                replacements[name] = new_path
            rewrite_attachment_urls(new_data, replacements)
        except Exception:
            for path in restored_paths:
                if os.path.exists(path):
                    os.remove(path)
            raise
        previous_data = self._data
        self._data = new_data
        if not self.save_immediately():
            self._data = previous_data
            for path in restored_paths:
                os.remove(path)
            return False
        self.data_changed.emit("all")
        return True

    # ==================== TASKS & HOMEWORK ====================

    def get_tasks(self) -> List[Dict[str, Any]]:
        return self._data.get("tasks", [])

    def add_task(self, title: str, description: str = "", subject: str = "",
                 due_date: Optional[str] = None, due_time: str = "12:00",
                 priority: str = "medium") -> Dict[str, Any]:
        task = {
            "id": str(uuid.uuid4()),
            "title": title.strip(),
            "description": description.strip(),
            "subject": subject.strip() or t("general"),
            "due_date": due_date or date.today().isoformat(),
            "due_time": due_time or "12:00",
            "priority": priority,
            "completed": False,
            "completed_at": None,
            "created_at": datetime.now().isoformat()
        }
        self._data.setdefault("tasks", []).append(task)
        self.schedule_save("tasks")
        return task

    def update_task(self, task_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        for task in self._data.get("tasks", []):
            if task["id"] == task_id:
                for k, v in kwargs.items():
                    task[k] = v
                self.schedule_save("tasks")
                return task
        return None

    def toggle_task(self, task_id: str) -> Optional[bool]:
        for task in self._data.get("tasks", []):
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
                task["completed_at"] = datetime.now().isoformat() if task["completed"] else None
                self.schedule_save("tasks")
                return task["completed"]
        return None

    def delete_task(self, task_id: str) -> bool:
        tasks = self._data.get("tasks", [])
        before_count = len(tasks)
        self._data["tasks"] = [t for t in tasks if t["id"] != task_id]
        if len(self._data["tasks"]) < before_count:
            self.schedule_save("tasks")
            return True
        return False

    # ==================== NOTEBOOKS (ТЕТРАДИ) ====================

    def get_notebooks(self) -> List[Dict[str, Any]]:
        return self._data.get("notebooks", [])

    def add_notebook(self, title: str, color: str = "#6366F1", icon: str = "book") -> Dict[str, Any]:
        nb = {
            "id": str(uuid.uuid4()),
            "title": title.strip() or t("nb_dialog_new_title"),
            "color": color,
            "icon": icon,
            "created_at": datetime.now().isoformat(),
            "pages": [
                {
                    "id": str(uuid.uuid4()),
                    "title": t("nb_page_default_title"),
                    "content_html": f"<p>{t('editor_empty_prompt')}</p>",
                    "content_plain": t('editor_empty_prompt'),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
        }
        self._data.setdefault("notebooks", []).append(nb)
        self.schedule_save("notebooks")
        return nb

    def update_notebook(self, nb_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        for nb in self._data.get("notebooks", []):
            if nb["id"] == nb_id:
                for k, v in kwargs.items():
                    nb[k] = v
                self.schedule_save("notebooks")
                return nb
        return None

    def delete_notebook(self, nb_id: str) -> bool:
        nbs = self._data.get("notebooks", [])
        before = len(nbs)
        self._data["notebooks"] = [n for n in nbs if n["id"] != nb_id]
        if len(self._data["notebooks"]) < before:
            self.schedule_save("notebooks")
            return True
        return False

    def add_page(self, nb_id: str, title: str = "", content_html: str = "") -> Optional[Dict[str, Any]]:
        for nb in self._data.get("notebooks", []):
            if nb["id"] == nb_id:
                page = {
                    "id": str(uuid.uuid4()),
                    "title": title.strip() or t("nb_page_default_title"),
                    "content_html": content_html or "<p></p>",
                    "content_plain": "",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                nb.setdefault("pages", []).append(page)
                self.schedule_save("notebooks")
                return page
        return None

    def update_page(self, nb_id: str, page_id: str, title: Optional[str] = None,
                    content_html: Optional[str] = None, content_plain: Optional[str] = None) -> bool:
        for nb in self._data.get("notebooks", []):
            if nb["id"] == nb_id:
                for page in nb.get("pages", []):
                    if page["id"] == page_id:
                        if title is not None:
                            page["title"] = title
                        if content_html is not None:
                            page["content_html"] = content_html
                        if content_plain is not None:
                            page["content_plain"] = content_plain
                        page["updated_at"] = datetime.now().isoformat()
                        self.schedule_save("notebooks")
                        return True
        return False

    def delete_page(self, nb_id: str, page_id: str) -> bool:
        for nb in self._data.get("notebooks", []):
            if nb["id"] == nb_id:
                pages = nb.get("pages", [])
                before = len(pages)
                nb["pages"] = [p for p in pages if p["id"] != page_id]
                if len(nb["pages"]) < before:
                    self.schedule_save("notebooks")
                    return True
        return False

    # ==================== NOTES (ЗАМЕТКИ) ====================

    def get_notes(self) -> List[Dict[str, Any]]:
        # Return sorted: pinned first, then by updated_at descending
        notes = self._data.get("notes", [])
        newest_first = sorted(notes, key=lambda n: n.get("updated_at", ""), reverse=True)
        return sorted(newest_first, key=lambda n: bool(n.get("pinned", False)), reverse=True)

    def add_note(self, title: str = "", content: str = "",
                 color: str = "#6366F1", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        note = {
            "id": str(uuid.uuid4()),
            "title": title.strip() or t("untitled_page"),
            "content": content,
            "color": color,
            "pinned": False,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._data.setdefault("notes", []).insert(0, note)
        self.schedule_save("notes")
        return note

    def update_note(self, note_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        for note in self._data.get("notes", []):
            if note["id"] == note_id:
                for k, v in kwargs.items():
                    note[k] = v
                note["updated_at"] = datetime.now().isoformat()
                self.schedule_save("notes")
                return note
        return None

    def toggle_pin_note(self, note_id: str) -> Optional[bool]:
        for note in self._data.get("notes", []):
            if note["id"] == note_id:
                note["pinned"] = not note.get("pinned", False)
                note["updated_at"] = datetime.now().isoformat()
                self.schedule_save("notes")
                return note["pinned"]
        return None

    def delete_note(self, note_id: str) -> bool:
        notes = self._data.get("notes", [])
        before = len(notes)
        self._data["notes"] = [n for n in notes if n["id"] != note_id]
        if len(self._data["notes"]) < before:
            self.schedule_save("notes")
            return True
        return False

    # ==================== CALENDAR EVENTS & LESSONS ====================

    def get_events(self) -> List[Dict[str, Any]]:
        return self._data.get("calendar_events", [])

    def add_event(self, title: str, date_str: str, time_str: str = "10:00",
                  end_time_str: str = "11:00", description: str = "",
                  color: str = "#6366F1", event_type: str = "lesson",
                  subject: str = "", badge: str = "", room: str = "") -> Dict[str, Any]:
        evt = {
            "id": str(uuid.uuid4()),
            "title": title.strip() or t("cal_badge_lesson"),
            "subject": subject.strip() or title.strip(),
            "description": description.strip(),
            "date": date_str,
            "time": time_str,
            "end_time": end_time_str or time_str,
            "color": color,
            "type": event_type,
            "badge": badge.strip(),
            "room": room.strip()
        }
        self._data.setdefault("calendar_events", []).append(evt)
        self.schedule_save("events")
        return evt

    def update_event(self, event_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        for evt in self._data.get("calendar_events", []):
            if evt["id"] == event_id:
                for k, v in kwargs.items():
                    if k != "id":
                        evt[k] = v
                self.schedule_save("events")
                return evt
        return None

    def delete_event(self, event_id: str) -> bool:
        events = self._data.get("calendar_events", [])
        before = len(events)
        self._data["calendar_events"] = [e for e in events if e["id"] != event_id]
        if len(self._data["calendar_events"]) < before:
            self.schedule_save("events")
            return True
        return False

    # ==================== RECURRING LESSONS (Постоянное расписание) ====================

    def get_recurring_lessons(self) -> List[Dict[str, Any]]:
        """Return all recurring (weekly) lessons without a specific date."""
        return self._data.get("recurring_lessons", [])

    def add_recurring_lesson(self, title: str, weekday: int, time_str: str = "09:00",
                              end_time_str: str = "10:30", description: str = "",
                              color: str = "#6366F1", badge: str = "", room: str = "") -> Dict[str, Any]:
        """Add a recurring weekly lesson stored only with weekday (0=Mon..6=Sun), no specific date."""
        lesson = {
            "id": str(uuid.uuid4()),
            "title": title.strip(),
            "weekday": weekday,  # 0=Mon..6=Sun
            "time": time_str,
            "end_time": end_time_str,
            "description": description.strip(),
            "color": color,
            "badge": badge.strip(),
            "room": room.strip(),
            "recurring": True
        }
        self._data.setdefault("recurring_lessons", []).append(lesson)
        self.schedule_save("recurring")
        return lesson

    def update_recurring_lesson(self, lesson_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update fields of a recurring lesson by its id."""
        for lesson in self._data.get("recurring_lessons", []):
            if lesson["id"] == lesson_id:
                for k, v in kwargs.items():
                    if k != "id":
                        lesson[k] = v
                self.schedule_save("recurring")
                return lesson
        return None

    def delete_recurring_lesson(self, lesson_id: str) -> bool:
        """Delete a recurring lesson by its id. Returns True if deleted."""
        lessons = self._data.get("recurring_lessons", [])
        before = len(lessons)
        self._data["recurring_lessons"] = [l for l in lessons if l["id"] != lesson_id]
        if len(self._data["recurring_lessons"]) < before:
            self.schedule_save("recurring")
            return True
        return False


# Global singleton instance provider
_instance: Optional[StorageManager] = None

def get_storage() -> StorageManager:
    global _instance
    if _instance is None:
        _instance = StorageManager()
    return _instance

def set_storage_instance(inst: Optional[StorageManager]):
    """Set or clear the global storage singleton (useful for isolated tests)."""
    global _instance
    _instance = inst
