"""Soporte para inicio automatico portable en Windows."""

from __future__ import annotations

import os
import sys
from pathlib import Path


class StartupService:
    """Crea o elimina un lanzador silencioso en Startup del usuario."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        self.startup_script = startup_dir / "widget_dashboard_start.vbs"
        self.legacy_cmd_script = startup_dir / "widget_dashboard_start.cmd"

    def is_supported(self) -> bool:
        return os.name == "nt" and self.startup_script.parent.exists()

    def is_enabled(self) -> bool:
        return self.startup_script.exists() or self.legacy_cmd_script.exists()

    def enable(self) -> bool:
        if not self.is_supported():
            return False
        python_exec = self._get_silent_python_executable()
        main_file = self.project_dir / "main.pyw"
        if not main_file.exists():
            main_file = self.project_dir / "main.py"
        self._remove_legacy_cmd()
        content = (
            'Set shell = CreateObject("WScript.Shell")\r\n'
            f'shell.CurrentDirectory = "{self.project_dir}"\r\n'
            f'shell.Run Chr(34) & "{python_exec}" & Chr(34) & " " & Chr(34) & "{main_file}" & Chr(34), 0, False\r\n'
            "Set shell = Nothing\r\n"
        )
        self.startup_script.write_text(content, encoding="utf-8")
        return True

    def _get_silent_python_executable(self) -> Path:
        python_exec = Path(sys.executable)
        if python_exec.name.lower() == "pythonw.exe":
            return python_exec
        pythonw_exec = python_exec.with_name("pythonw.exe")
        if pythonw_exec.exists():
            return pythonw_exec
        return python_exec

    def disable(self) -> bool:
        removed = False
        if self.startup_script.exists():
            self.startup_script.unlink()
            removed = True
        if self.legacy_cmd_script.exists():
            self.legacy_cmd_script.unlink()
            removed = True
        return removed

    def _remove_legacy_cmd(self) -> None:
        if self.legacy_cmd_script.exists():
            self.legacy_cmd_script.unlink()
