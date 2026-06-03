"""Boton redondeado simple para interfaces Tkinter oscuras."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont


class RoundedButton(tk.Canvas):
    """Simula un boton con esquinas redondeadas usando Canvas."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command=None,
        bg: str = "#4ec9b0",
        fg: str = "#111111",
        hover_bg: str | None = None,
        radius: int = 5,
        padx: int = 8,
        pady: int = 3,
        font: tuple[str, int, str] | tuple[str, int] = ("Segoe UI", 9, "bold"),
        **kwargs,
    ) -> None:
        self.text = text
        self.command = command
        self.bg_color = bg
        self.fg_color = fg
        self.hover_bg = hover_bg or bg
        self.radius = radius
        self.padx = padx
        self.pady = pady
        self.text_font = tkfont.Font(font=font)
        text_width = self.text_font.measure(text)
        text_height = self.text_font.metrics("linespace")
        width = text_width + (padx * 2)
        height = text_height + (pady * 2)
        super().__init__(
            master,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=master.cget("bg"),
            cursor="hand2",
            **kwargs,
        )
        self._draw(bg)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda _event: self._draw(self.hover_bg))
        self.bind("<Leave>", lambda _event: self._draw(self.bg_color))

    def _draw(self, fill_color: str) -> None:
        self.delete("all")
        width = int(self.cget("width"))
        height = int(self.cget("height"))
        radius = min(self.radius, height // 2)
        points = [
            radius,
            0,
            width - radius,
            0,
            width,
            0,
            width,
            radius,
            width,
            height - radius,
            width,
            height,
            width - radius,
            height,
            radius,
            height,
            0,
            height,
            0,
            height - radius,
            0,
            radius,
            0,
            0,
        ]
        self.create_polygon(points, smooth=True, splinesteps=18, fill=fill_color, outline=fill_color)
        self.create_text(width // 2, height // 2, text=self.text, fill=self.fg_color, font=self.text_font)

    def _on_click(self, _event: tk.Event) -> None:
        if self.command is not None:
            self.command()
