"""Persistencia local en JSON y TXT."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from widget_dashboard.models import ReminderItem, TaskItem


class AppStorage:
    """Centraliza las rutas y operaciones de lectura y escritura."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.legacy_data_dir = self.base_dir / "data"
        self.data_dir = self._get_runtime_data_dir()
        self.tasks_path = self.data_dir / "tasks.json"
        self.reminders_path = self.data_dir / "reminders.json"
        self.config_path = self.data_dir / "config.json"
        self._ensure_layout()

    def _get_runtime_data_dir(self) -> Path:
        if os.name == "nt":
            appdata = Path(os.environ.get("APPDATA", ""))
            if appdata.exists():
                return appdata / "WidgetDashboard"
        return self.base_dir / ".widget_dashboard"

    def _ensure_layout(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        self._migrate_legacy_data()
        if not self.config_path.exists():
            self.save_config(
                {
                    "autostart": False,
                    "widget_mode": "workerw",
                    "position": "bottom_right",
                    "opacity": 0.94,
                    "background_color": "#1e1e1e",
                    "always_on_top": False,
                    "lock_position": False,
                }
            )
        if not self.tasks_path.exists():
            self._write_json(self.tasks_path, [])
        if not self.reminders_path.exists():
            self._write_json(self.reminders_path, [])

    def _migrate_legacy_data(self) -> None:
        if not self.legacy_data_dir.exists() or self.legacy_data_dir == self.data_dir:
            return
        for file_name in ("tasks.json", "reminders.json", "config.json"):
            legacy_path = self.legacy_data_dir / file_name
            current_path = self.data_dir / file_name
            if legacy_path.exists() and not current_path.exists():
                shutil.copy2(legacy_path, current_path)

    def _read_json(self, path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _write_json(self, path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_tasks(self) -> list[TaskItem]:
        return [TaskItem.from_dict(item) for item in self._read_json(self.tasks_path, [])]

    def save_tasks(self, tasks: list[TaskItem]) -> None:
        self._write_json(self.tasks_path, [task.to_dict() for task in tasks])

    def load_reminders(self) -> list[ReminderItem]:
        return [ReminderItem.from_dict(item) for item in self._read_json(self.reminders_path, [])]

    def save_reminders(self, reminders: list[ReminderItem]) -> None:
        self._write_json(self.reminders_path, [reminder.to_dict() for reminder in reminders])

    def load_config(self) -> dict[str, Any]:
        return self._read_json(self.config_path, {})

    def save_config(self, config: dict[str, Any]) -> None:
        self._write_json(self.config_path, config)
