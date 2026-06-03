"""Tests basicos para persistencia local."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from widget_dashboard.models import ReminderItem, TaskItem
from widget_dashboard.persistence.storage import AppStorage


class AppStorageTests(unittest.TestCase):
    def test_storage_uses_local_hidden_dir_without_windows_appdata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            original_appdata = os.environ.get("APPDATA")
            try:
                os.environ["APPDATA"] = str(base_dir / "missing_appdata")
                storage = AppStorage(base_dir)
            finally:
                if original_appdata is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = original_appdata

            self.assertEqual(storage.data_dir, base_dir / ".widget_dashboard")
            self.assertTrue(storage.config_path.exists())
            self.assertTrue(storage.tasks_path.exists())
            self.assertTrue(storage.reminders_path.exists())

    def test_storage_migrates_legacy_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            legacy_dir = base_dir / "data"
            legacy_dir.mkdir()
            (legacy_dir / "tasks.json").write_text(
                json.dumps([TaskItem(text="Migrada").to_dict()]), encoding="utf-8"
            )
            (legacy_dir / "reminders.json").write_text(
                json.dumps([ReminderItem(message="Migrado", due_at="2026-01-01T10:00:00").to_dict()]), encoding="utf-8"
            )
            (legacy_dir / "config.json").write_text(json.dumps({"opacity": 0.8}), encoding="utf-8")

            original_appdata = os.environ.get("APPDATA")
            try:
                os.environ["APPDATA"] = str(base_dir / "missing_appdata")
                storage = AppStorage(base_dir)
            finally:
                if original_appdata is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = original_appdata

            self.assertEqual(len(storage.load_tasks()), 1)
            self.assertEqual(storage.load_tasks()[0].text, "Migrada")
            self.assertEqual(len(storage.load_reminders()), 1)
            self.assertEqual(storage.load_config()["opacity"], 0.8)
