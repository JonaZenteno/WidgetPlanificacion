"""Ventana principal del dashboard minimalista."""

from __future__ import annotations

from datetime import datetime, timedelta
import os
import tkinter as tk

from widget_dashboard.models import ReminderItem, TaskItem
from widget_dashboard.modules.reminder_panel import ReminderPanel
from widget_dashboard.modules.todo_panel import TodoPanel
from widget_dashboard.ui import theme


class MainWindow(tk.Tk):
    """Construye y coordina la interfaz principal."""

    OPACITY_OPTIONS = [("20%", 0.2), ("40%", 0.4), ("60%", 0.6), ("80%", 0.8)]
    BACKGROUND_OPTIONS = [
        ("Grafito", "#1e1e1e"),
        ("Carbon", "#181818"),
        ("Azul Noche", "#16202a"),
        ("Oliva Oscuro", "#20261e"),
    ]

    def __init__(self, storage, notifier, startup_service, window_manager) -> None:
        super().__init__()
        self.storage = storage
        self.notifier = notifier
        self.startup_service = startup_service
        self.window_manager = window_manager
        self.tasks: list[TaskItem] = self.storage.load_tasks()
        self.reminders: list[ReminderItem] = self.storage.load_reminders()
        self.config_data = self.storage.load_config()
        self.background_color = self.config_data.get("background_color", theme.BACKGROUND)
        self.opacity = float(self.config_data.get("opacity", theme.ALPHA))
        self.always_on_top = bool(self.config_data.get("always_on_top", False))
        self.lock_position = bool(self.config_data.get("lock_position", False))
        self.drag_offset = (0, 0)

        self._configure_window()
        self._build_layout()
        self._build_context_menu()
        self._schedule_reminder_check()

    def _configure_window(self) -> None:
        self.title("Widget Dashboard")
        self.overrideredirect(True)
        self.configure(bg=theme.TRANSPARENT)
        if os.name == "nt":
            self.wm_attributes("-transparentcolor", theme.TRANSPARENT)
            self.attributes("-alpha", self.opacity)
        self.attributes("-topmost", self.always_on_top)
        self.resizable(False, False)
        self.geometry(self._get_window_geometry())
        self.after(150, self._apply_widget_behavior)

    def _get_window_geometry(self) -> str:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = screen_w - theme.WINDOW_WIDTH - 24
        y = screen_h - theme.WINDOW_HEIGHT - 48
        return f"{theme.WINDOW_WIDTH}x{theme.WINDOW_HEIGHT}+{x}+{y}"

    def _apply_widget_behavior(self) -> None:
        mode = self.config_data.get("widget_mode", "workerw")
        self.window_manager.apply_widget_mode(self, mode=mode)

    def _build_layout(self) -> None:
        self.shell = tk.Canvas(
            self,
            bg=theme.TRANSPARENT,
            highlightthickness=0,
            bd=0,
            width=theme.WINDOW_WIDTH,
            height=theme.WINDOW_HEIGHT,
        )
        self.shell.pack(fill="both", expand=True)
        self.shell.bind("<Configure>", self._redraw_shell)

        self.content_card = tk.Frame(self.shell, bg=self.background_color, bd=0, highlightthickness=0)
        self.content_window = self.shell.create_window(
            theme.INNER_PADDING,
            theme.INNER_PADDING,
            anchor="nw",
            window=self.content_card,
        )
        self.shell.bind("<ButtonPress-1>", self._start_drag, add="+")
        self.shell.bind("<B1-Motion>", self._on_drag, add="+")
        self.shell.bind("<Button-3>", self._show_context_menu, add="+")
        self.content_card.bind("<ButtonPress-1>", self._start_drag, add="+")
        self.content_card.bind("<B1-Motion>", self._on_drag, add="+")
        self.content_card.bind("<Button-3>", self._show_context_menu, add="+")

        close_button = tk.Button(
            self.content_card,
            text="x",
            command=self.destroy,
            bg=self.background_color,
            fg=theme.TEXT,
            relief="flat",
            bd=0,
            padx=2,
            pady=0,
            cursor="hand2",
            font=("Segoe UI", 11),
            activebackground=self.background_color,
            activeforeground=theme.DANGER,
        )
        close_button.bind("<Button-3>", self._show_context_menu, add="+")
        close_button.place(relx=1.0, x=-4, y=-1, anchor="ne")
        self.close_button = close_button

        content = tk.Frame(self.content_card, bg=self.background_color)
        content.pack(fill="both", expand=True, padx=theme.PADDING, pady=(0, theme.PADDING))
        content.columnconfigure(0, weight=1, uniform="modules")
        content.columnconfigure(1, weight=1, uniform="modules")
        content.rowconfigure(0, weight=1)
        content.bind("<ButtonPress-1>", self._start_drag)
        content.bind("<B1-Motion>", self._on_drag)
        content.bind("<Button-3>", self._show_context_menu, add="+")
        self.content = content

        self.todo_panel = TodoPanel(content, self.tasks, self._save_tasks, self._start_drag, self._on_drag)
        self.todo_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.todo_panel.bind("<Button-3>", self._show_context_menu, add="+")

        self.reminder_panel = ReminderPanel(content, self.reminders, self._save_reminders, self._start_drag, self._on_drag)
        self.reminder_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.reminder_panel.bind("<Button-3>", self._show_context_menu, add="+")

    def _build_context_menu(self) -> None:
        self.bind_all("<Button-3>", self._show_context_menu, add="+")
        self.always_on_top_var = tk.BooleanVar(value=self.always_on_top)
        self.lock_position_var = tk.BooleanVar(value=self.lock_position)
        self.context_menu = tk.Menu(self, tearoff=0, bg=theme.PANEL, fg=theme.TEXT, activebackground=theme.SOFT)
        opacity_menu = tk.Menu(self.context_menu, tearoff=0, bg=theme.PANEL, fg=theme.TEXT, activebackground=theme.SOFT)
        for label, value in self.OPACITY_OPTIONS:
            opacity_menu.add_command(label=label, command=lambda current=value: self._set_opacity(current))

        background_menu = tk.Menu(self.context_menu, tearoff=0, bg=theme.PANEL, fg=theme.TEXT, activebackground=theme.SOFT)
        for label, color in self.BACKGROUND_OPTIONS:
            background_menu.add_command(label=label, command=lambda current=color: self._set_background_color(current))

        self.context_menu.add_checkbutton(
            label="Siempre visible",
            variable=self.always_on_top_var,
            command=self._toggle_always_on_top,
        )
        self.context_menu.add_checkbutton(
            label="Bloquear posición",
            variable=self.lock_position_var,
            command=self._toggle_lock_position,
        )
        self.context_menu.add_separator()
        self.context_menu.add_cascade(label="Cambiar opacidad", menu=opacity_menu)
        self.context_menu.add_cascade(label="Cambiar color de fondo", menu=background_menu)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Restaurar estilo por defecto", command=self._restore_default_style)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cerrar", command=self.destroy)

    def _show_context_menu(self, event: tk.Event) -> None:
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _toggle_always_on_top(self) -> None:
        self.always_on_top = self.always_on_top_var.get()
        self.attributes("-topmost", self.always_on_top)
        self.config_data["always_on_top"] = self.always_on_top
        self.storage.save_config(self.config_data)

    def _toggle_lock_position(self) -> None:
        self.lock_position = self.lock_position_var.get()
        self.config_data["lock_position"] = self.lock_position
        self.storage.save_config(self.config_data)

    def _set_opacity(self, value: float) -> None:
        self.opacity = value
        if os.name == "nt":
            self.attributes("-alpha", self.opacity)
        self.config_data["opacity"] = value
        self.storage.save_config(self.config_data)

    def _set_background_color(self, color: str) -> None:
        self.background_color = color
        self.config_data["background_color"] = color
        self.storage.save_config(self.config_data)
        self._apply_background_color()

    def _apply_background_color(self) -> None:
        self.content_card.configure(bg=self.background_color)
        self.content.configure(bg=self.background_color)
        self.close_button.configure(bg=self.background_color, activebackground=self.background_color)
        self._redraw_shell()

    def _restore_default_style(self) -> None:
        self.background_color = theme.BACKGROUND
        self.opacity = theme.ALPHA
        self.always_on_top = False
        self.lock_position = False
        self.always_on_top_var.set(False)
        self.lock_position_var.set(False)
        if os.name == "nt":
            self.attributes("-alpha", self.opacity)
        self.attributes("-topmost", False)
        self.config_data["background_color"] = self.background_color
        self.config_data["opacity"] = self.opacity
        self.config_data["always_on_top"] = False
        self.config_data["lock_position"] = False
        self.storage.save_config(self.config_data)
        self._apply_background_color()

    def _redraw_shell(self, event: tk.Event | None = None) -> None:
        width = event.width if event else theme.WINDOW_WIDTH
        height = event.height if event else theme.WINDOW_HEIGHT
        self.shell.delete("shell-bg")
        self._create_round_rect(0, 0, width - 1, height - 1, theme.RADIUS, fill=self.background_color, outline=theme.BORDER)
        inner_width = max(1, width - (theme.INNER_PADDING * 2))
        inner_height = max(1, height - (theme.INNER_PADDING * 2))
        self.shell.coords(self.content_window, theme.INNER_PADDING, theme.INNER_PADDING)
        self.shell.itemconfigure(self.content_window, width=inner_width, height=inner_height)

    def _create_round_rect(self, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs) -> None:
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
        self.shell.create_polygon(points, smooth=True, splinesteps=24, tags="shell-bg", **kwargs)

    def _start_drag(self, event: tk.Event) -> None:
        if self.lock_position:
            return
        self.drag_offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _on_drag(self, event: tk.Event) -> None:
        if self.lock_position:
            return
        x = event.x_root - self.drag_offset[0]
        y = event.y_root - self.drag_offset[1]
        self.geometry(f"{theme.WINDOW_WIDTH}x{theme.WINDOW_HEIGHT}+{x}+{y}")

    def _save_tasks(self, tasks: list[TaskItem]) -> None:
        self.storage.save_tasks(tasks)

    def _save_reminders(self, reminders: list[ReminderItem]) -> None:
        self.storage.save_reminders(reminders)

    def _schedule_reminder_check(self) -> None:
        self._check_due_reminders()
        self.after(5000, self._schedule_reminder_check)

    def _check_due_reminders(self) -> None:
        now = datetime.now()
        changed = False
        for reminder in self.reminders:
            if reminder.is_due(now):
                self.notifier.notify(
                    "Recordatorio",
                    reminder.message,
                    parent=self,
                    on_snooze=lambda reminder_id=reminder.reminder_id: self._snooze_reminder(reminder_id),
                    on_done=lambda reminder_id=reminder.reminder_id: self._complete_reminder(reminder_id),
                )
                reminder.notified = True
                self.reminder_panel.update_reminder(reminder)
                changed = True
        if changed:
            self.storage.save_reminders(self.reminders)

    def _snooze_reminder(self, reminder_id: str) -> None:
        for reminder in self.reminders:
            if reminder.reminder_id == reminder_id:
                reminder.due_at = (datetime.now() + timedelta(minutes=5)).isoformat(timespec="seconds")
                reminder.notified = False
                self.reminder_panel.update_reminder(reminder)
                break
        self.storage.save_reminders(self.reminders)

    def _complete_reminder(self, reminder_id: str) -> None:
        for reminder in self.reminders:
            if reminder.reminder_id == reminder_id:
                reminder.completed = True
                reminder.notified = True
                self.reminder_panel.update_reminder(reminder)
                break
        self.storage.save_reminders(self.reminders)
