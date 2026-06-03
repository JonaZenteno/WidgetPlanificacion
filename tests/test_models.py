"""Tests basicos para modelos de dominio."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from widget_dashboard.models import ReminderItem, TaskItem


class TaskItemTests(unittest.TestCase):
    def test_task_roundtrip_preserves_fields(self) -> None:
        task = TaskItem(text="Probar tarea", done=True, item_id="abc123", created_at="2026-01-01T10:00:00")

        restored = TaskItem.from_dict(task.to_dict())

        self.assertEqual(restored.text, "Probar tarea")
        self.assertTrue(restored.done)
        self.assertEqual(restored.item_id, "abc123")
        self.assertEqual(restored.created_at, "2026-01-01T10:00:00")


class ReminderItemTests(unittest.TestCase):
    def test_reminder_is_due_only_when_pending_and_due_date_passed(self) -> None:
        due_at = (datetime.now() - timedelta(minutes=1)).isoformat(timespec="seconds")
        reminder = ReminderItem(message="Tomar agua", due_at=due_at)

        self.assertTrue(reminder.is_due())

        reminder.notified = True
        self.assertFalse(reminder.is_due())

    def test_completed_reminder_is_not_due(self) -> None:
        due_at = (datetime.now() - timedelta(minutes=1)).isoformat(timespec="seconds")
        reminder = ReminderItem(message="Cerrar tarea", due_at=due_at, completed=True)

        self.assertFalse(reminder.is_due())

    def test_legacy_minutes_field_is_migrated(self) -> None:
        restored = ReminderItem.from_dict({"message": "Legacy", "minutes": 10})

        self.assertEqual(restored.message, "Legacy")
        self.assertFalse(restored.notified)
        self.assertFalse(restored.completed)
        self.assertTrue(restored.due_at)
