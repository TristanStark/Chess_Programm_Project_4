from src.views.label_frame import CtkLabelFrame
import customtkinter as ctk  # pyright: ignore[reportMissingImports]
from tkinter import ttk


class TournamentRoundsPanel(CtkLabelFrame):
    _STATUS_COLORS = {
        "not_started": "#FFFFFF",
        "ongoing": "#EAF3FF",
        "finished": "#FFF1E6",
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="List of rounds:", **kwargs)
        self._on_round_selected = None
        self._round_item_ids = []
        self._round_statuses = []
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.round_status_label = ctk.CTkLabel(
            self.content,
            text="",
            text_color="black",
            font=ctk.CTkFont(size=15),
        )
        self.round_status_label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        rounds_tree_container = ctk.CTkFrame(self.content, fg_color="transparent")
        rounds_tree_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 0))
        rounds_tree_container.grid_rowconfigure(0, weight=1)
        rounds_tree_container.grid_columnconfigure(0, weight=1)

        self.rounds_tree = ttk.Treeview(
            rounds_tree_container,
            columns=("round_name",),
            show="tree",
            height=5,
        )
        self.rounds_tree.grid(row=0, column=0, sticky="nsew")
        self.rounds_tree.bind("<<TreeviewSelect>>", self._handle_tree_selection)

    def set_on_round_selected(self, callback):
        self._on_round_selected = callback

    def clear_rounds(self):
        for item in self.rounds_tree.get_children():
            self.rounds_tree.delete(item)
        self._round_item_ids = []
        self._round_statuses = []

    def add_round_row(self, text, status="not_started"):
        round_index = len(self._round_item_ids)
        item_id = self.rounds_tree.insert("", "end", text=text)
        self._round_item_ids.append(item_id)
        self._round_statuses.append(self._normalize_status(status))
        self._apply_row_style(round_index)

    def update_round_status(self, index, status):
        if not 0 <= index < len(self._round_item_ids):
            return
        self._round_statuses[index] = self._normalize_status(status)
        self._apply_row_style(index)

    def select_round(self, index):
        if not 0 <= index < len(self._round_item_ids):
            self.rounds_tree.selection_remove(self.rounds_tree.selection())
            return

        item_id = self._round_item_ids[index]
        self.rounds_tree.selection_set(item_id)
        self.rounds_tree.focus(item_id)
        self.rounds_tree.see(item_id)

    def _handle_tree_selection(self, _event):
        """Select the round"""
        if self._on_round_selected is None:
            return
        selection = self.rounds_tree.selection()
        if not selection:
            self._on_round_selected(None)
            return
        all_items = self.rounds_tree.get_children("")
        selected_item = selection[0]
        selected_index = all_items.index(selected_item)
        self._on_round_selected(selected_index)

    def _apply_row_style(self, index):
        """Apply the correct color scheme"""
        if not 0 <= index < len(self._round_item_ids):
            return

        item_id = self._round_item_ids[index]
        status = self._round_statuses[index]
        tag_name = f"round_status_{index}"

        self.rounds_tree.item(item_id, tags=(tag_name,))
        self.rounds_tree.tag_configure(
            tag_name,
            background=self._STATUS_COLORS.get(status, self._STATUS_COLORS["not_started"]),
            foreground="black",
        )

    @staticmethod
    def _normalize_status(status):
        normalized = str(status).strip().lower()
        if normalized not in {"not_started", "ongoing", "finished"}:
            return "not_started"
        return normalized
