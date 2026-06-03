"""Servicio de notificaciones con fallback discreto."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from widget_dashboard.ui import theme

try:
    from plyer import notification
except ImportError:  # pragma: no cover
    notification = None


class Notifier:
    """Envia notificaciones nativas y usa un popup minimo si fallan."""

    def __init__(self) -> None:
        self._popups: list[tk.Toplevel] = []

    def notify(
        self,
        title: str,
        message: str,
        parent: tk.Misc | None = None,
        on_snooze=None,
        on_done=None,
    ) -> None:
        if notification is not None:
            try:
                notification.notify(title=title, message=message, app_name="Widget Dashboard", timeout=5)
            except Exception:
                pass
        if parent is not None:
            self._show_popup(parent, title, message, on_snooze=on_snooze, on_done=on_done)

    def _show_popup(self, parent: tk.Misc, title: str, message: str, on_snooze=None, on_done=None) -> None:
        popup = tk.Toplevel(parent)
        popup.overrideredirect(True)
        popup.configure(bg=theme.TRANSPARENT)
        popup.attributes("-topmost", True)
        try:
            popup.wm_attributes("-transparentcolor", theme.TRANSPARENT)
            popup.attributes("-alpha", 0.98)
        except tk.TclError:
            pass

        width = 300
        height = 150
        margin = 18
        index = len(self._popups)
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        x = screen_w - width - margin
        y = screen_h - height - margin - (index * (height + 10))
        popup.geometry(f"{width}x{height}+{x}+{y}")

        shell = tk.Canvas(popup, bg=theme.TRANSPARENT, highlightthickness=0, bd=0, width=width, height=height)
        shell.pack(fill="both", expand=True)
        self._draw_round_rect(shell, 0, 0, width - 1, height - 1, 12, fill=theme.PANEL, outline=theme.BORDER)

        shell.create_text(16, 16, anchor="nw", text=title, fill=theme.TEXT, font=("Segoe UI", 11, "bold"))
        shell.create_text(
            16,
            42,
            anchor="nw",
            text=message,
            fill=theme.MUTED,
            font=("Segoe UI", 10),
            width=width - 32,
        )

        self._create_action_button(
            shell,
            text="Posponer 5 min",
            x=16,
            y=108,
            width=118,
            bg=theme.SOFT,
            fg=theme.TEXT,
            command=lambda current=popup, callback=on_snooze: self._handle_action(current, callback),
        )
        self._create_action_button(
            shell,
            text="Marcar listo",
            x=146,
            y=108,
            width=118,
            bg=theme.ACCENT,
            fg="#111111",
            command=lambda current=popup, callback=on_done: self._handle_action(current, callback),
        )

        self._popups.append(popup)

    def _handle_action(self, popup: tk.Toplevel, callback: Callable | None) -> None:
        if callback is not None:
            callback()
        self._destroy_popup(popup)

    def _create_action_button(
        self,
        shell: tk.Canvas,
        text: str,
        x: int,
        y: int,
        width: int,
        bg: str,
        fg: str,
        command: Callable,
    ) -> None:
        button = tk.Button(
            shell,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            relief="flat",
            bd=0,
            activebackground=bg,
            activeforeground=fg,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=8,
            pady=4,
        )
        shell.create_window(x, y, anchor="nw", window=button, width=width, height=28)

    def _destroy_popup(self, popup: tk.Toplevel) -> None:
        if popup in self._popups:
            self._popups.remove(popup)
        if popup.winfo_exists():
            popup.destroy()
        self._reflow_popups()

    def _reflow_popups(self) -> None:
        width = 300
        height = 150
        margin = 18
        for index, popup in enumerate(self._popups):
            if not popup.winfo_exists():
                continue
            screen_w = popup.winfo_screenwidth()
            screen_h = popup.winfo_screenheight()
            x = screen_w - width - margin
            y = screen_h - height - margin - (index * (height + 10))
            popup.geometry(f"{width}x{height}+{x}+{y}")

    def _draw_round_rect(
        self,
        canvas: tk.Canvas,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        **kwargs,
    ) -> None:
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        canvas.create_polygon(points, smooth=True, splinesteps=20, **kwargs)
