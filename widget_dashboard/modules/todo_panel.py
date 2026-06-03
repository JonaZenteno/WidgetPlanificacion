"""Panel de gestion de tareas."""

from __future__ import annotations

import tkinter as tk

from widget_dashboard.models import TaskItem
from widget_dashboard.ui.rounded_button import RoundedButton
from widget_dashboard.ui import theme


class TodoPanel(tk.Frame):
    """Panel compacto para agregar, completar y borrar tareas."""

    def __init__(self, master: tk.Misc, tasks: list[TaskItem], on_change, on_drag_start=None, on_drag_move=None) -> None:
        super().__init__(master, bg=theme.PANEL, bd=0, highlightthickness=0)
        self.tasks = tasks
        self.on_change = on_change
        self.on_drag_start = on_drag_start
        self.on_drag_move = on_drag_move
        self._vars: dict[str, tk.BooleanVar] = {}
        self._rows: dict[str, tk.Frame] = {}
        self._labels: dict[str, tk.Label] = {}
        self._checks: dict[str, tk.Button] = {}
        self._empty_label: tk.Label | None = None
        self.dialog: tk.Toplevel | None = None
        self.scrollbar_visible = False
        self.columnconfigure(0, weight=1)
        self._build()
        self.refresh()

    def _build(self) -> None:
        header = tk.Frame(self, bg=theme.PANEL)
        header.grid(row=0, column=0, sticky="ew", padx=theme.PADDING, pady=(0, 1))
        header.columnconfigure(0, weight=1)

        tk.Label(header, text="ToDo", bg=theme.PANEL, fg=theme.TEXT, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        RoundedButton(
            header,
            text="+ Tarea",
            command=self.open_add_dialog,
            bg=theme.ACCENT,
            fg="#111111",
            padx=7,
            pady=2,
            radius=3,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=1, sticky="e")
        self.list_shell = tk.Frame(self, bg=theme.PANEL)
        self.list_shell.grid(row=1, column=0, sticky="nsew", padx=(theme.PADDING, 2), pady=(0, theme.PADDING))
        self.rowconfigure(1, weight=1)
        self._bind_drag_surface(self)
        self._bind_drag_surface(header)
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
        self.items_frame.bind("<Configure>", self._on_items_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.canvas.pack(side="left", fill="both", expand=True)

    def open_add_dialog(self) -> None:
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.lift()
            return
        self.dialog = tk.Toplevel(self)
        self.dialog.title("Nueva tarea")
        self.dialog.configure(bg=theme.BACKGROUND)
        self.dialog.resizable(False, False)
        self.dialog.transient(self.winfo_toplevel())
        self.dialog.attributes("-topmost", True)

        body = tk.Frame(self.dialog, bg=theme.BACKGROUND)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=1)

        tk.Label(body, text="Tarea", bg=theme.BACKGROUND, fg=theme.TEXT, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.task_entry = tk.Entry(
            body,
            bg=theme.SOFT,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
        )
        self.task_entry.grid(row=1, column=0, sticky="ew", ipady=6)
        self.task_entry.bind("<Return>", lambda _: self.add_task())

        footer = tk.Frame(body, bg=theme.BACKGROUND)
        footer.grid(row=2, column=0, sticky="e", pady=(12, 0))
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
            text="Guardar tarea",
            command=self.add_task,
            bg=theme.ACCENT,
            fg="#111111",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
        ).pack(side="left")
        self.task_entry.focus_set()

    def add_task(self) -> None:
        if self.dialog is None:
            return
        text = self.task_entry.get().strip()
        if not text:
            return
        task = TaskItem(text=text)
        self.tasks.insert(0, task)
        self._hide_empty_state()
        self._create_task_row(task)
        self._reindex_rows()
        self.after_idle(self._close_dialog)
        self.after_idle(self._update_scrollbar_visibility)
        self.on_change(self.tasks)

    def _close_dialog(self) -> None:
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.destroy()
        self.dialog = None

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

    def _bind_drag_surface(self, widget: tk.Misc) -> None:
        if self.on_drag_start is None or self.on_drag_move is None:
            return
        widget.bind("<ButtonPress-1>", self.on_drag_start, add="+")
        widget.bind("<B1-Motion>", self.on_drag_move, add="+")

    def refresh(self) -> None:
        self._clear_rows()

        if not self.tasks:
            self._show_empty_state()
            self.after_idle(self._update_scrollbar_visibility)
            return

        for task in self.tasks:
            self._create_task_row(task)
        self._reindex_rows()
        self.after_idle(self._update_scrollbar_visibility)

    def toggle_task(self, task: TaskItem, state: tk.BooleanVar) -> None:
        state.set(not state.get())
        task.done = state.get()
        self._update_task_row(task)
        self.on_change(self.tasks)

    def delete_task(self, task: TaskItem) -> None:
        self.tasks[:] = [item for item in self.tasks if item.item_id != task.item_id]
        self._destroy_task_row(task.item_id)
        self._reindex_rows()
        if not self.tasks:
            self._show_empty_state()
        self.after_idle(self._update_scrollbar_visibility)
        self.on_change(self.tasks)

    def _show_empty_state(self) -> None:
        if self._empty_label is not None and self._empty_label.winfo_exists():
            return
        self._empty_label = tk.Label(
            self.items_frame,
            text="Sin tareas por ahora.",
            bg=theme.PANEL,
            fg=theme.MUTED,
            font=("Segoe UI", 10),
        )
        self._empty_label.grid(row=0, column=0, sticky="w")
        self._bind_drag_surface(self._empty_label)

    def _hide_empty_state(self) -> None:
        if self._empty_label is not None and self._empty_label.winfo_exists():
            self._empty_label.destroy()
        self._empty_label = None

    def _create_task_row(self, task: TaskItem) -> None:
        if task.item_id in self._rows:
            self._update_task_row(task)
            return
        row = tk.Frame(self.items_frame, bg=theme.PANEL)
        row.columnconfigure(1, weight=1)
        self._bind_drag_surface(row)

        var = tk.BooleanVar(value=task.done)
        self._vars[task.item_id] = var
        check = tk.Button(
            row,
            text="✓" if task.done else "",
            command=lambda item=task, state=var: self.toggle_task(item, state),
            bg=theme.SOFT,
            fg=theme.ACCENT,
            activebackground=theme.SOFT,
            activeforeground=theme.ACCENT,
            relief="flat",
            bd=0,
            width=2,
            padx=0,
            pady=0,
            font=("Segoe UI", 9, "bold"),
        )
        check.grid(row=0, column=0, sticky="nw", padx=(0, 4))

        label = tk.Label(
            row,
            text=task.text,
            bg=theme.PANEL,
            fg=theme.MUTED if task.done else theme.TEXT,
            font=("Segoe UI", 9, "overstrike" if task.done else "normal"),
            anchor="w",
            justify="left",
            wraplength=185,
        )
        label.grid(row=0, column=1, sticky="ew")
        self._bind_drag_surface(label)

        delete_button = tk.Button(
            row,
            text="x",
            command=lambda item=task: self.delete_task(item),
            bg=theme.PANEL,
            fg=theme.DANGER,
            relief="flat",
            bd=0,
            padx=2,
        )
        delete_button.grid(row=0, column=2, sticky="ne", padx=(2, 0))

        self._rows[task.item_id] = row
        self._labels[task.item_id] = label
        self._checks[task.item_id] = check

    def _update_task_row(self, task: TaskItem) -> None:
        label = self._labels.get(task.item_id)
        check = self._checks.get(task.item_id)
        var = self._vars.get(task.item_id)
        if var is not None:
            var.set(task.done)
        if check is not None:
            check.configure(text="✓" if task.done else "")
        if label is not None:
            label.configure(
                text=task.text,
                fg=theme.MUTED if task.done else theme.TEXT,
                font=("Segoe UI", 9, "overstrike" if task.done else "normal"),
            )

    def _destroy_task_row(self, item_id: str) -> None:
        row = self._rows.pop(item_id, None)
        self._labels.pop(item_id, None)
        self._checks.pop(item_id, None)
        self._vars.pop(item_id, None)
        if row is not None and row.winfo_exists():
            row.destroy()

    def _reindex_rows(self) -> None:
        for index, task in enumerate(self.tasks):
            row = self._rows.get(task.item_id)
            if row is not None:
                row.grid(row=index, column=0, sticky="ew", pady=0)

    def _clear_rows(self) -> None:
        self._hide_empty_state()
        for item_id in list(self._rows.keys()):
            self._destroy_task_row(item_id)
