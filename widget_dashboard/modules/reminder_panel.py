"""Panel de recordatorios simples."""

from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import messagebox

from widget_dashboard.models import ReminderItem
from widget_dashboard.ui import theme
from widget_dashboard.ui.rounded_button import RoundedButton


class ReminderPanel(tk.Frame):
    """Permite agendar recordatorios por fecha y hora y ver su estado."""

    def __init__(self, master: tk.Misc, reminders: list[ReminderItem], on_change, on_drag_start=None, on_drag_move=None) -> None:
        super().__init__(master, bg=theme.PANEL, bd=0, highlightthickness=0)
        self.reminders = reminders
        self.on_change = on_change
        self.on_drag_start = on_drag_start
        self.on_drag_move = on_drag_move
        self._rows: dict[str, tk.Frame] = {}
        self._labels: dict[str, tk.Label] = {}
        self._empty_label: tk.Label | None = None
        self.dialog: tk.Toplevel | None = None
        self.scrollbar_visible = False
        self._build()
        self.refresh()

    def _build(self) -> None:
        header = tk.Frame(self, bg=theme.PANEL)
        header.grid(row=0, column=0, sticky="ew", padx=theme.PADDING, pady=(0, 1))
        header.columnconfigure(0, weight=1)

        tk.Label(header, text="Recordatorios", bg=theme.PANEL, fg=theme.TEXT, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        RoundedButton(
            header,
            text="+ Rec",
            command=self.open_add_dialog,
            bg=theme.ACCENT_ALT,
            fg=theme.TEXT,
            padx=6,
            pady=2,
            radius=3,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=1, sticky="e")
        self.columnconfigure(0, weight=1)
        self._bind_drag_surface(self)
        self._bind_drag_surface(header)

        self.list_shell = tk.Frame(self, bg=theme.PANEL)
        self.list_shell.grid(row=1, column=0, sticky="nsew", padx=theme.PADDING, pady=(0, theme.PADDING))
        self.rowconfigure(1, weight=1)
        self._bind_drag_surface(self.list_shell)

        self.canvas = tk.Canvas(
            self.list_shell,
            bg=theme.PANEL,
            highlightthickness=0,
            bd=0,
            height=theme.CONTENT_HEIGHT,
        )
        self.scrollbar = tk.Scrollbar(
            self.list_shell,
            orient="vertical",
            command=self.canvas.yview,
            bg=theme.SOFT,
            activebackground=theme.SCROLLBAR_ACTIVE,
            troughcolor=theme.PANEL,
            relief="flat",
            width=7,
            bd=0,
            highlightthickness=0,
            elementborderwidth=0,
            borderwidth=0,
        )
        self.items_frame = tk.Frame(self.canvas, bg=theme.PANEL)
        self.items_frame.columnconfigure(0, weight=1)
        self.items_frame.bind("<Configure>", self._on_items_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.canvas.pack(side="left", fill="both", expand=True)
        self._bind_drag_surface(self.items_frame)

    def _bind_drag_surface(self, widget: tk.Misc) -> None:
        if self.on_drag_start is None or self.on_drag_move is None:
            return
        widget.bind("<ButtonPress-1>", self.on_drag_start, add="+")
        widget.bind("<B1-Motion>", self.on_drag_move, add="+")

    def _on_items_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.after_idle(self._update_scrollbar_visibility)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)
        self.after_idle(self._update_scrollbar_visibility)

    def _update_scrollbar_visibility(self) -> None:
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        content_height = bbox[3] - bbox[1]
        viewport_height = self.canvas.winfo_height()
        needs_scroll = content_height > viewport_height + 2
        if needs_scroll and not self.scrollbar_visible:
            self.scrollbar.pack(side="right", fill="y")
            self.scrollbar_visible = True
        elif not needs_scroll and self.scrollbar_visible:
            self.scrollbar.pack_forget()
            self.scrollbar_visible = False

    def _bind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.scrollbar_visible:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def open_add_dialog(self) -> None:
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.lift()
            return
        self.dialog = tk.Toplevel(self)
        self.dialog.title("Nuevo recordatorio")
        self.dialog.configure(bg=theme.BACKGROUND)
        self.dialog.resizable(False, False)
        self.dialog.transient(self.winfo_toplevel())
        self.dialog.attributes("-topmost", True)

        body = tk.Frame(self.dialog, bg=theme.BACKGROUND)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=1)

        tk.Label(body, text="Mensaje", bg=theme.BACKGROUND, fg=theme.TEXT, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.message_entry = tk.Entry(
            body,
            bg=theme.SOFT,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
        )
        self.message_entry.grid(row=1, column=0, sticky="ew", ipady=6)

        tk.Label(body, text="Fecha", bg=theme.BACKGROUND, fg=theme.TEXT, font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky="w", pady=(10, 4)
        )
        self.date_entry = tk.Entry(
            body,
            bg=theme.SOFT,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
        )
        self.date_entry.grid(row=3, column=0, sticky="ew", ipady=6)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(body, text="Hora", bg=theme.BACKGROUND, fg=theme.TEXT, font=("Segoe UI", 10, "bold")).grid(
            row=4, column=0, sticky="w", pady=(10, 4)
        )
        self.time_entry = tk.Entry(
            body,
            bg=theme.SOFT,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
        )
        self.time_entry.grid(row=5, column=0, sticky="ew", ipady=6)
        self.time_entry.insert(0, datetime.now().strftime("%H:%M"))

        footer = tk.Frame(body, bg=theme.BACKGROUND)
        footer.grid(row=6, column=0, sticky="e", pady=(12, 0))
        tk.Button(
            footer,
            text="Cancelar",
            command=self._close_dialog,
            bg=theme.SOFT,
            fg=theme.TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
        ).pack(side="left", padx=(0, 6))
        tk.Button(
            footer,
            text="Guardar alerta",
            command=self.add_reminder,
            bg=theme.ACCENT,
            fg="#111111",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
        ).pack(side="left")

        self.message_entry.focus_set()

    def add_reminder(self) -> None:
        if self.dialog is None:
            return
        message = self.message_entry.get().strip()
        date_text = self.date_entry.get().strip()
        time_text = self.time_entry.get().strip()
        if not message:
            return
        try:
            due_at = datetime.strptime(f"{date_text} {time_text}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Fecha invalida", "Usa el formato YYYY-MM-DD y HH:MM.", parent=self.dialog)
            return
        if due_at <= datetime.now():
            messagebox.showerror("Hora invalida", "El recordatorio debe estar en el futuro.", parent=self.dialog)
            return
        reminder = ReminderItem(message=message, due_at=due_at.isoformat(timespec="seconds"))
        self.reminders.insert(0, reminder)
        self._hide_empty_state()
        self._create_reminder_row(reminder)
        self._reindex_rows()
        self.after_idle(self._close_dialog)
        self.on_change(self.reminders)

    def _close_dialog(self) -> None:
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.destroy()
        self.dialog = None

    def refresh(self) -> None:
        self._clear_rows()
        if not self.reminders:
            self._show_empty_state()
            self.after_idle(self._update_scrollbar_visibility)
            return

        for reminder in self.reminders:
            self._create_reminder_row(reminder)
        self._reindex_rows()
        self.after_idle(self._update_scrollbar_visibility)

    def delete_reminder(self, reminder: ReminderItem) -> None:
        self.reminders[:] = [item for item in self.reminders if item.reminder_id != reminder.reminder_id]
        self._destroy_reminder_row(reminder.reminder_id)
        self._reindex_rows()
        if not self.reminders:
            self._show_empty_state()
        self.after_idle(self._update_scrollbar_visibility)
        self.on_change(self.reminders)

    def update_reminder(self, reminder: ReminderItem) -> None:
        self._hide_empty_state()
        self._create_reminder_row(reminder)
        self._update_reminder_row(reminder)
        self._reindex_rows()
        self.after_idle(self._update_scrollbar_visibility)

    def _show_empty_state(self) -> None:
        if self._empty_label is not None and self._empty_label.winfo_exists():
            return
        self._empty_label = tk.Label(
            self.items_frame,
            text="No hay alertas activas.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=("Segoe UI", 9),
            wraplength=150,
            justify="left",
        )
        self._empty_label.grid(row=0, column=0, sticky="w")
        self._bind_drag_surface(self._empty_label)

    def _hide_empty_state(self) -> None:
        if self._empty_label is not None and self._empty_label.winfo_exists():
            self._empty_label.destroy()
        self._empty_label = None

    def _create_reminder_row(self, reminder: ReminderItem) -> None:
        if reminder.reminder_id in self._rows:
            self._update_reminder_row(reminder)
            return
        row = tk.Frame(self.items_frame, bg=theme.PANEL)
        row.columnconfigure(0, weight=1)
        self._bind_drag_surface(row)

        label = tk.Label(
            row,
            bg=theme.PANEL,
            anchor="w",
            justify="left",
            wraplength=150,
        )
        label.grid(row=0, column=0, sticky="ew")
        self._bind_drag_surface(label)

        tk.Button(
            row,
            text="x",
            command=lambda item=reminder: self.delete_reminder(item),
            bg=theme.PANEL,
            fg=theme.DANGER,
            relief="flat",
            bd=0,
            padx=2,
        ).grid(row=0, column=1, padx=(4, 0))

        self._rows[reminder.reminder_id] = row
        self._labels[reminder.reminder_id] = label
        self._update_reminder_row(reminder)

    def _update_reminder_row(self, reminder: ReminderItem) -> None:
        label = self._labels.get(reminder.reminder_id)
        if label is None:
            return
        due_text = datetime.fromisoformat(reminder.due_at).strftime("%d/%m %H:%M")
        label_text = f"{reminder.message} · {due_text}"
        label.configure(
            text=label_text,
            fg=theme.MUTED if reminder.notified or reminder.completed else theme.TEXT,
            font=("Segoe UI", 9, "overstrike" if reminder.completed else "normal"),
        )

    def _destroy_reminder_row(self, reminder_id: str) -> None:
        row = self._rows.pop(reminder_id, None)
        self._labels.pop(reminder_id, None)
        if row is not None and row.winfo_exists():
            row.destroy()

    def _reindex_rows(self) -> None:
        for index, reminder in enumerate(self.reminders):
            row = self._rows.get(reminder.reminder_id)
            if row is not None:
                row.grid(row=index, column=0, sticky="ew", pady=0)

    def _clear_rows(self) -> None:
        self._hide_empty_state()
        for reminder_id in list(self._rows.keys()):
            self._destroy_reminder_row(reminder_id)
