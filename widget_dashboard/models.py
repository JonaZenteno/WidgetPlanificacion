"""Modelos de dominio simples para la aplicacion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4


@dataclass
class TaskItem:
    """Representa una tarea del modulo ToDo."""

    text: str
    done: bool = False
    item_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskItem":
        return cls(
            text=data.get("text", ""),
            done=bool(data.get("done", False)),
            item_id=data.get("item_id", uuid4().hex),
            created_at=data.get("created_at", datetime.now().isoformat(timespec="seconds")),
        )


@dataclass
class ReminderItem:
    """Representa un recordatorio agendado por fecha y hora."""

    message: str
    due_at: str
    reminder_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    notified: bool = False
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReminderItem":
        due_at = data.get("due_at", "")
        if not due_at:
            minutes = max(1, int(data.get("minutes", 30)))
            due_at = (datetime.now() + timedelta(minutes=minutes)).isoformat(timespec="seconds")
        return cls(
            message=data.get("message", ""),
            due_at=due_at,
            reminder_id=data.get("reminder_id", uuid4().hex),
            created_at=data.get("created_at", datetime.now().isoformat(timespec="seconds")),
            notified=bool(data.get("notified", False)),
            completed=bool(data.get("completed", False)),
        )

    def is_due(self, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        return not self.notified and not self.completed and now >= datetime.fromisoformat(self.due_at)
