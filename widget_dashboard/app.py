"""Composicion principal de la aplicacion."""

from __future__ import annotations

from pathlib import Path

from widget_dashboard.persistence.storage import AppStorage
from widget_dashboard.services.notifier import Notifier
from widget_dashboard.services.startup import StartupService
from widget_dashboard.services.windows_integration import WindowsWidgetManager
from widget_dashboard.ui.main_window import MainWindow


class WidgetDashboardApp:
    """Coordina servicios, persistencia y ventana principal."""

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.storage = AppStorage(base_dir)
        self.notifier = Notifier()
        self.startup_service = StartupService(base_dir)
        self.window_manager = WindowsWidgetManager()
        self.window = MainWindow(
            storage=self.storage,
            notifier=self.notifier,
            startup_service=self.startup_service,
            window_manager=self.window_manager,
        )

    def run(self) -> None:
        self.window.mainloop()
