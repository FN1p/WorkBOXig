"""
Google Calendar Synchronization Engine for WorkBOXig.
Provides robust RFC 5545 iCalendar (.ics) parsing, timezone normalization,
smart de-duplication, and non-blocking background synchronization with Google Calendar.
"""

import os
import re
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from src.storage import StorageManager


def normalize_calendar_url(raw_url: str) -> str:
    """Ensure protocol is HTTPS and clean up webcal scheme."""
    url = raw_url.strip()
    if url.startswith("webcal://"):
        url = "https://" + url[9:]
    elif url.startswith("http://"):
        url = "https://" + url[7:]
    return url


def unfold_ical_lines(raw_text: str) -> List[str]:
    """Unfold RFC 5545 lines (lines starting with space or tab continue the previous line)."""
    raw_lines = raw_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    unfolded: List[str] = []
    for line in raw_lines:
        if (line.startswith(' ') or line.startswith('\t')) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return [l.strip() for l in unfolded if l.strip()]


def unescape_ical_text(val: str) -> str:
    """Decode standard RFC 5545 escaped characters."""
    val = val.replace('\\n', '\n').replace('\\N', '\n')
    val = val.replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')
    return val.strip()


def parse_ical_datetime(dt_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse RFC 5545 date/time into (YYYY-MM-DD, HH:MM).
    Converts UTC timestamps ('Z') to local system time.
    """
    clean = dt_str.split(':')[-1].strip()
    
    # All-day date format: YYYYMMDD
    if len(clean) == 8 and clean.isdigit():
        try:
            d = datetime.strptime(clean, "%Y%m%d")
            return d.strftime("%Y-%m-%d"), "00:00"
        except Exception:
            return None, None

    # Full timestamp: YYYYMMDDTHHMMSS[Z]
    if 'T' in clean:
        is_utc = clean.endswith('Z')
        raw = clean[:-1] if is_utc else clean
        try:
            dt = datetime.strptime(raw[:15], "%Y%m%dT%H%M%S")
            if is_utc:
                dt = dt.replace(tzinfo=timezone.utc).astimezone()
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except Exception:
            return None, None

    return None, None


def parse_ical_events(ics_content: str) -> List[Dict[str, Any]]:
    """Parse all VEVENT blocks in an iCalendar (.ics) string."""
    lines = unfold_ical_lines(ics_content)
    events: List[Dict[str, Any]] = []
    current_evt: Optional[Dict[str, str]] = None

    for line in lines:
        if line == "BEGIN:VEVENT":
            current_evt = {}
            continue
        elif line == "END:VEVENT":
            if current_evt and "SUMMARY" in current_evt and "DTSTART" in current_evt:
                # Process event
                raw_uid = current_evt.get("UID", "")
                uid = (raw_uid.split(":", 1)[-1].strip() if ":" in raw_uid else raw_uid) or str(uuid.uuid4())
                raw_summary = current_evt.get("SUMMARY", "Событие")
                summary = unescape_ical_text(raw_summary.split(":", 1)[-1] if ":" in raw_summary else raw_summary)
                raw_desc = current_evt.get("DESCRIPTION", "")
                desc = unescape_ical_text(raw_desc.split(":", 1)[-1] if ":" in raw_desc else raw_desc)
                raw_loc = current_evt.get("LOCATION", "")
                loc = unescape_ical_text(raw_loc.split(":", 1)[-1] if ":" in raw_loc else raw_loc)
                
                start_date, start_time = parse_ical_datetime(current_evt["DTSTART"])
                end_date, end_time = (None, None)
                if "DTEND" in current_evt:
                    end_date, end_time = parse_ical_datetime(current_evt["DTEND"])

                if start_date:
                    if not end_time or end_time == start_time:
                        # Default 1 hour duration if not specified
                        try:
                            st_h, st_m = map(int, start_time.split(':'))
                            end_time = f"{(st_h + 1) % 24:02d}:{st_m:02d}"
                        except Exception:
                            end_time = start_time

                    events.append({
                        "google_uid": uid,
                        "title": summary,
                        "subject": summary,
                        "description": desc,
                        "date": start_date,
                        "time": start_time or "10:00",
                        "end_time": end_time or "11:00",
                        "room": loc,
                        "color": "#4285F4",  # Google Calendar Signature Blue
                        "type": "event",
                        "badge": "Google",
                        "source": "google"
                    })
            current_evt = None
            continue

        if current_evt is not None:
            if ':' in line:
                key_part, val_part = line.split(':', 1)
                key = key_part.split(';')[0].upper()
                current_evt[key] = line  # Store full line for parameter inspection

    return events


def fetch_and_sync_google_calendar(
    url: str,
    storage: StorageManager,
    timeout: int = 15
) -> Tuple[int, int, int]:
    """
    Fetch live iCal feed from Google and merge into StorageManager.
    Returns (added_count, updated_count, total_count).
    """
    clean_url = normalize_calendar_url(url)
    req = urllib.request.Request(
        clean_url,
        headers={"User-Agent": "WorkBOXig-CalendarSync/1.0 (Windows NT 10.0; Win64; x64)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status} {resp.reason}")
            ics_content = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as he:
        raise RuntimeError(f"Ошибка доступа к календарю (HTTP {he.code}). Проверьте правильность ссылки.") from he
    except urllib.error.URLError as ue:
        raise RuntimeError(f"Не удалось подключиться к Google Календарю: {ue.reason}") from ue

    parsed_events = parse_ical_events(ics_content)
    if not parsed_events:
        raise ValueError("В календаре не найдено событий или неверный формат ссылки.")

    added = 0
    updated = 0
    existing_events = storage.get_events()
    existing_by_uid = {
        e.get("google_uid"): e for e in existing_events if e.get("google_uid")
    }

    for p in parsed_events:
        g_uid = p["google_uid"]
        if g_uid in existing_by_uid:
            # Update existing event in-place
            target = existing_by_uid[g_uid]
            target["title"] = p["title"]
            target["subject"] = p["subject"]
            target["description"] = p["description"]
            target["date"] = p["date"]
            target["time"] = p["time"]
            target["end_time"] = p["end_time"]
            target["room"] = p["room"]
            updated += 1
        else:
            # Add new synced event
            new_evt = dict(p)
            new_evt["id"] = str(uuid.uuid4())
            existing_events.append(new_evt)
            added += 1

    # Record sync metadata and persist immediately
    storage.set_setting("google_calendar_url", clean_url)
    storage.set_setting("google_calendar_last_sync", datetime.now().isoformat())
    storage.save_immediately()
    storage.data_changed.emit("events")

    return added, updated, len(parsed_events)


class GoogleCalendarSyncWorker(QThread):
    """Background thread to perform Google Calendar synchronization without freezing UI."""
    sync_finished = pyqtSignal(int, int, int)  # added, updated, total
    sync_error = pyqtSignal(str)

    def __init__(self, url: str, storage: StorageManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.url = url
        self.storage = storage

    def run(self):
        try:
            added, updated, total = fetch_and_sync_google_calendar(self.url, self.storage)
            self.sync_finished.emit(added, updated, total)
        except Exception as e:
            self.sync_error.emit(str(e))
