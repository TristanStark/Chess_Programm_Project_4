from src.views.label_frame import CtkLabelFrame
import customtkinter as ctk  # pyright: ignore[reportMissingImports]
import re


class TournamentMatchesPanel(CtkLabelFrame):
    _STATUS_COLORS = {
        "not_started": "#FFFFFF",
        "ongoing": "#EAF3FF",
        "finished": "#FFF1E6",
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Matches:", **kwargs)
        self._on_match_selected = None
        self._match_row_frames = []
        self._match_row_statuses = []
        self._selected_match_index = None
        self._selected_match_indices = set()
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.match_scrollable = ctk.CTkScrollableFrame(
            self.content,
            fg_color="#F7F7F7",
            corner_radius=0,
        )
        self.match_scrollable.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self._update_scrollbar_visibility()

    def set_on_match_selected(self, callback):
        self._on_match_selected = callback

    def clear_matches(self):
        for widget in self.match_scrollable.winfo_children():
            widget.destroy()
        self._match_row_frames = []
        self._match_row_statuses = []
        self._selected_match_index = None
        self._selected_match_indices = set()
        self._update_scrollbar_visibility()
        if self._on_match_selected is not None:
            self._on_match_selected(None)

    def add_match(
        self,
        player_1_name,
        player_1_score,
        player_2_name,
        player_2_score,
        status="not_started",
    ):
        left_text = f"{player_1_name} : {player_1_score}"
        right_text = f"{player_2_score} : {player_2_name}"
        self._render_match_row(left_text, right_text, status)

    def add_match_row(self, text, status="not_started"):
        left_text, right_text = self._split_match_text(text)
        self._render_match_row(left_text, right_text, status)

    def update_match_status(self, index, status):
        if not 0 <= index < len(self._match_row_frames):
            return
        self._match_row_statuses[index] = self._normalize_status(status)
        self._apply_row_style(index)

    def select_match(self, index):
        if index is None:
            self._selected_match_index = None
            self._selected_match_indices = set()
            for idx in range(len(self._match_row_frames)):
                self._apply_row_style(idx)
            if self._on_match_selected is not None:
                self._on_match_selected(None)
            return
        if 0 <= index < len(self._match_row_frames):
            self._select_match(index, keep_existing=False)

    def get_selected_match_indices(self):
        return sorted(self._selected_match_indices)

    def _render_match_row(self, left_text, right_text, status):
        row = ctk.CTkFrame(
            self.match_scrollable,
            corner_radius=0,
            fg_color="#FFFFFF",
            border_width=2,
            border_color="black",
            height=60,
        )
        row.pack(fill="x", padx=(4, 18), pady=5)
        row.grid_propagate(False)
        row.grid_rowconfigure(0, weight=1)
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)
        row.grid_columnconfigure(2, weight=1)
        match_index = len(self._match_row_frames)
        self._match_row_frames.append(row)
        self._match_row_statuses.append(self._normalize_status(status))

        left_label = ctk.CTkLabel(
            row,
            text=left_text,
            text_color="black",
            anchor="w",
            font=ctk.CTkFont(size=16),
        )
        left_label.grid(row=0, column=0, sticky="w", padx=(10, 8), pady=(10, 10))

        separator_label = ctk.CTkLabel(
            row,
            text="-",
            text_color="black",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        separator_label.grid(row=0, column=1, padx=4, pady=(10, 10))

        right_label = ctk.CTkLabel(
            row,
            text=right_text,
            text_color="black",
            anchor="e",
            font=ctk.CTkFont(size=16),
        )
        right_label.grid(row=0, column=2, sticky="e", padx=(8, 10), pady=(10, 10))

        row.bind("<Button-1>", lambda event, idx=match_index: self._on_match_clicked(event, idx))
        left_label.bind(
            "<Button-1>", lambda event, idx=match_index: self._on_match_clicked(event, idx)
        )
        separator_label.bind(
            "<Button-1>", lambda event, idx=match_index: self._on_match_clicked(event, idx)
        )
        right_label.bind(
            "<Button-1>", lambda event, idx=match_index: self._on_match_clicked(event, idx)
        )
        self._apply_row_style(match_index)
        self._update_scrollbar_visibility()

    def _on_match_clicked(self, event, index):
        keep_existing = bool(getattr(event, "state", 0) & 0x0004)
        self._select_match(index, keep_existing=keep_existing)

    def _select_match(self, index, keep_existing=False):
        if keep_existing:
            if index in self._selected_match_indices:
                self._selected_match_indices.discard(index)
            else:
                self._selected_match_indices.add(index)
        else:
            self._selected_match_indices = {index}

        if self._selected_match_indices:
            self._selected_match_index = max(self._selected_match_indices)
        else:
            self._selected_match_index = None

        for idx in range(len(self._match_row_frames)):
            self._apply_row_style(idx)
        if self._on_match_selected is not None:
            self._on_match_selected(self._selected_match_index)

    def _apply_row_style(self, index):
        if not 0 <= index < len(self._match_row_frames):
            return
        row = self._match_row_frames[index]
        status = self._match_row_statuses[index]
        is_selected = index in self._selected_match_indices
        base_color = self._STATUS_COLORS.get(status, self._STATUS_COLORS["not_started"])

        row.configure(
            fg_color=base_color,
            border_color=("#3B82F6" if is_selected else "black"),
        )

    @staticmethod
    def _normalize_status(status):
        normalized = str(status).strip().lower()
        if normalized not in {"not_started", "ongoing", "finished"}:
            return "not_started"
        return normalized

    def _update_scrollbar_visibility(self):
        scrollbar = getattr(self.match_scrollable, "_scrollbar", None)
        if scrollbar is None:
            return
        if len(self._match_row_frames) > 4:
            scrollbar.grid()
        else:
            scrollbar.grid_remove()

    @staticmethod
    def _split_match_text(text):
        """Return left and right text parts from a match display string."""
        parts = re.split(r"\s*-\s*", text, maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return text.strip(), ""
