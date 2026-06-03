"""Integracion Win32 para aproximar el comportamiento de widget."""

from __future__ import annotations

import ctypes
import os
import tkinter as tk
from ctypes import wintypes


class WindowsWidgetManager:
    """Aplica estilos Win32 para un widget de escritorio en Windows."""

    GWL_STYLE = -16
    GWL_EXSTYLE = -20
    WS_CHILD = 0x40000000
    WS_POPUP = 0x80000000
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_APPWINDOW = 0x00040000
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOACTIVATE = 0x0010
    SWP_FRAMECHANGED = 0x0020
    HWND_BOTTOM = 1
    SMTO_NORMAL = 0x0000
    PROGMAN_MESSAGE = 0x052C

    def __init__(self) -> None:
        self.available = os.name == "nt"
        self._workerw = None
        if self.available:
            self.user32 = ctypes.windll.user32

    def apply_widget_mode(self, window: tk.Tk, mode: str = "workerw") -> None:
        if not self.available:
            return
        window.update_idletasks()
        hwnd = window.winfo_id()
        self._apply_toolwindow_style(hwnd)
        if mode == "workerw" and self._attach_to_workerw(hwnd):
            return
        self._send_to_bottom(hwnd)

    def _apply_toolwindow_style(self, hwnd: int) -> None:
        ex_style = self.user32.GetWindowLongW(hwnd, self.GWL_EXSTYLE)
        ex_style = (ex_style | self.WS_EX_TOOLWINDOW) & ~self.WS_EX_APPWINDOW
        self.user32.SetWindowLongW(hwnd, self.GWL_EXSTYLE, ex_style)
        self.user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOACTIVATE | self.SWP_FRAMECHANGED,
        )

    def _send_to_bottom(self, hwnd: int) -> None:
        self.user32.SetWindowPos(
            hwnd,
            self.HWND_BOTTOM,
            0,
            0,
            0,
            0,
            self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOACTIVATE,
        )

    def _attach_to_workerw(self, hwnd: int) -> bool:
        workerw = self._find_workerw()
        if not workerw:
            return False
        style = self.user32.GetWindowLongW(hwnd, self.GWL_STYLE)
        style = (style | self.WS_CHILD) & ~self.WS_POPUP
        self.user32.SetWindowLongW(hwnd, self.GWL_STYLE, style)
        ctypes.set_last_error(0)
        previous_parent = self.user32.SetParent(hwnd, workerw)
        if not previous_parent and ctypes.get_last_error() != 0:
            return False
        self._workerw = workerw
        self._send_to_bottom(hwnd)
        return True

    def _find_workerw(self) -> int | None:
        progman = self.user32.FindWindowW("Progman", None)
        if not progman:
            return None
        result = wintypes.DWORD()
        self.user32.SendMessageTimeoutW(
            progman,
            self.PROGMAN_MESSAGE,
            0,
            0,
            self.SMTO_NORMAL,
            1000,
            ctypes.byref(result),
        )
        found = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def enum_windows(hwnd: int, lparam: int) -> bool:
            shell_view = self.user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
            if shell_view:
                workerw = self.user32.FindWindowExW(0, hwnd, "WorkerW", None)
                if workerw:
                    found.append(workerw)
                    return False
            return True

        self.user32.EnumWindows(enum_windows, 0)
        return found[0] if found else None
