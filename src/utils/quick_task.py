"""Parse the small, explicit syntax used by quick task entry."""

import re
from datetime import date


_DATE = re.compile(r"(?:^|\s)@(\d{4}-\d{2}-\d{2})(?=\s|$)")
_PRIORITY = re.compile(r"(?:^|\s)!(urgent|high|medium|low)(?=\s|$)", re.IGNORECASE)


def parse_quick_task(text: str) -> dict:
    """Return title, optional due date, and priority; reject invalid dates."""
    due = _DATE.search(text)
    priority = _PRIORITY.search(text)
    due_date = date.fromisoformat(due.group(1)).isoformat() if due else None
    cleaned = _DATE.sub(" ", text, count=1)
    cleaned = _PRIORITY.sub(" ", cleaned, count=1)
    title = " ".join(cleaned.split())
    if not title:
        raise ValueError("Task title is empty")
    return {
        "title": title,
        "due_date": due_date,
        "priority": priority.group(1).lower() if priority else "medium",
    }
