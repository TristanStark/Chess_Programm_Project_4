from src.views.label_frame import CtkLabelFrame
import customtkinter as ctk  # pyright: ignore[reportMissingImports]
from pathlib import Path
import tkinter as tk
from tkinter import ttk


class TournamentInfoPanel(CtkLabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Tournament details", **kwargs)
        self._current_status = ""
        self._players_sort_column = None
        self._players_sort_descending = False
        self.grid_propagate(False)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        infos_frame = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=0)
        infos_frame.grid(row=0, column=0, sticky="new", padx=0, pady=0)
        self.status_title_label = self._section_title(infos_frame, "Status: -")

        self._info_value_labels = {
            "start_date": self._add_info_row(infos_frame, "Start date"),
            "end_date": self._add_info_row(infos_frame, "End date"),
            "number_of_rounds": self._add_info_row(infos_frame, "Number of rounds"),
            "current_round": self._add_info_row(infos_frame, "Current round"),
        }
        self._build_players_tree(infos_frame)
        self._build_podium_section(infos_frame)

        desc_frame = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=0)
        desc_frame.grid(row=1, column=0, sticky="sew", padx=0, pady=(0, 10))
        self._section_title(desc_frame, "Description:")

        self.description_box = ctk.CTkTextbox(
            self.content,
            corner_radius=0,
            border_width=0,
            fg_color="#F7F7F7",
            text_color="black",
            wrap="word",
        )
        self.description_box.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, 0))
        self.description_box.insert(
            "1.0",
            "Tournament description goes here.\n\n"
            "You can display a summary, rules, context, or additional notes.",
        )

    def set_tournament_infos(
        self,
        *,
        status,
        start_date,
        end_date,
        number_of_rounds,
        current_round,
    ):
        self._current_status = str(status)
        self.status_title_label.configure(text=f"Status: {self._current_status}")
        self._set_info_value("start_date", start_date)
        self._set_info_value("end_date", end_date)
        self._set_info_value("number_of_rounds", number_of_rounds)
        self._set_info_value("current_round", current_round)
        self._update_podium_visibility()

    def set_description(self, text):
        self.description_box.delete("1.0", "end")
        self.description_box.insert("1.0", str(text))

    def set_players(self, players):
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)

        for player in players:
            player_name = self._format_player_name(player)
            total_points = self._extract_player_points(player)
            self.players_tree.insert(
                "",
                "end",
                values=(player_name, self._format_points(total_points)),
            )

        players_count = len(players)
        self.players_title_label.configure(text=f"Players ({players_count}):")
        self._apply_players_tree_sort()
        self._update_podium(players)

    def _set_info_value(self, key, value):
        self._info_value_labels[key].configure(text=str(value))

    @staticmethod
    def _add_info_row(parent, label_text):
        row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(
            row,
            text=f"{label_text}:",
            anchor="w",
            text_color="black",
            font=ctk.CTkFont(size=16),
        ).pack(side="left")

        value_label = ctk.CTkLabel(
            row,
            text="-",
            anchor="w",
            text_color="black",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        value_label.pack(side="left", padx=(6, 0))
        return value_label

    def _build_players_tree(self, parent):
        players_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        players_frame.pack(fill="both", expand=True, pady=(8, 0))
        players_frame.grid_rowconfigure(1, weight=1)
        players_frame.grid_columnconfigure(0, weight=1)

        self.players_title_label = ctk.CTkLabel(
            players_frame,
            text="Players (0):",
            anchor="w",
            text_color="black",
            font=ctk.CTkFont(size=16),
        )
        self.players_title_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        tree_container = ctk.CTkFrame(players_frame, fg_color="transparent")
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        self.players_tree = ttk.Treeview(
            tree_container,
            columns=("player_name", "total_points"),
            show="headings",
            height=6,
        )
        self.players_tree.heading(
            "player_name",
            text="Player",
            command=lambda: self._on_players_tree_heading_click("player_name"),
        )
        self.players_tree.heading(
            "total_points",
            text="Points",
            command=lambda: self._on_players_tree_heading_click("total_points"),
        )
        self.players_tree.column("player_name", anchor="w", stretch=True, width=150, minwidth=100)
        self.players_tree.column("total_points", anchor="e", stretch=False, width=64, minwidth=64)
        self.players_tree.grid(row=0, column=0, sticky="nsew")

    def _on_players_tree_heading_click(self, column: str):
        if self._players_sort_column == column:
            self._players_sort_descending = not self._players_sort_descending
        else:
            self._players_sort_column = column
            self._players_sort_descending = False
        self._apply_players_tree_sort()

    def _apply_players_tree_sort(self):
        columns_labels = {
            "player_name": "Player",
            "total_points": "Points",
        }

        for column, label in columns_labels.items():
            label_with_indicator = label
            if column == self._players_sort_column:
                indicator = "▼" if self._players_sort_descending else "▲"
                label_with_indicator = f"{label} {indicator}"
            self.players_tree.heading(
                column,
                text=label_with_indicator,
                command=lambda current=column: self._on_players_tree_heading_click(current),
            )

        if self._players_sort_column is None:
            return

        rows = []
        for item_id in self.players_tree.get_children(""):
            item_values = self.players_tree.item(item_id, "values")
            rows.append((item_id, item_values))

        if self._players_sort_column == "player_name":
            rows.sort(
                key=lambda row: str(row[1][0]).lower(),
                reverse=self._players_sort_descending,
            )
        else:
            rows.sort(
                key=lambda row: self._to_float(row[1][1]),
                reverse=self._players_sort_descending,
            )

        for index, (item_id, _) in enumerate(rows):
            self.players_tree.move(item_id, "", index)

    def _build_podium_section(self, parent):
        self.podium_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        self._section_title(self.podium_frame, "Podium:")

        self.podium_canvas = tk.Canvas(
            self.podium_frame,
            width=220,
            height=110,
            bg="#F7F7F7",
            bd=0,
            highlightthickness=0,
        )
        self.podium_canvas.pack(fill="x")

        self._podium_image = None
        image_path = Path(__file__).with_name("podium.png")
        if image_path.exists():
            try:
                self._podium_image = tk.PhotoImage(file=str(image_path))
                self.podium_canvas.configure(
                    width=self._podium_image.width(),
                    height=self._podium_image.height(),
                )
                self.podium_canvas.create_image(0, 0, image=self._podium_image, anchor="nw")
            except tk.TclError:
                self.podium_canvas.create_text(
                    110,
                    55,
                    text="Podium image unavailable",
                    fill="black",
                    font=("Arial", 10, "bold"),
                )

        self._podium_text_items = {
            1: self.podium_canvas.create_text(
                110,
                33,
                text="-",
                fill="black",
                font=("Arial", 10, "bold"),
                width=78,
                justify="center",
                anchor="s",
            ),
            2: self.podium_canvas.create_text(
                56,
                49,
                text="-",
                fill="black",
                font=("Arial", 10, "bold"),
                width=70,
                justify="center",
                anchor="s",
            ),
            3: self.podium_canvas.create_text(
                164,
                59,
                text="-",
                fill="black",
                font=("Arial", 10, "bold"),
                width=70,
                justify="center",
                anchor="s",
            ),
        }
        self._update_podium_visibility()

    def _update_podium_visibility(self):
        if str(self._current_status).strip().lower() == "completed":
            if not self.podium_frame.winfo_ismapped():
                self.podium_frame.pack(fill="x", pady=(10, 0))
        else:
            if self.podium_frame.winfo_ismapped():
                self.podium_frame.pack_forget()

    def _update_podium(self, players):
        if str(self._current_status).strip().lower() != "completed":
            for item_id in self._podium_text_items.values():
                self.podium_canvas.itemconfigure(item_id, text="-")
            return

        ordered_players = sorted(
            players,
            key=lambda player: (
                -self._extract_player_points(player),
                getattr(player, "last_name", "").lower(),
                getattr(player, "first_name", "").lower(),
                getattr(player, "national_chess_identifier", "").lower(),
            ),
        )

        for place in (1, 2, 3):
            player_index = place - 1
            label = "-"
            if player_index < len(ordered_players):
                label = self._format_player_name(ordered_players[player_index])
            self.podium_canvas.itemconfigure(self._podium_text_items[place], text=label)

    @staticmethod
    def _extract_player_points(player) -> float:
        if hasattr(player, "total_points"):
            return float(getattr(player, "total_points"))
        if hasattr(player, "_total_points"):
            return float(getattr(player, "_total_points"))
        return 0.0

    @staticmethod
    def _format_points(points: float) -> str:
        points_value = float(points)
        if points_value.is_integer():
            return str(int(points_value))
        return f"{points_value:.1f}"

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _format_player_name(player):
        first_name = getattr(player, "first_name", "")
        last_name = getattr(player, "last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            return full_name
        return str(player)

    @staticmethod
    def _section_title(parent, text):
        title_label = ctk.CTkLabel(
            parent,
            text=text,
            text_color="black",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        title_label.pack(anchor="w", pady=(0, 6))

        line = ctk.CTkFrame(parent, fg_color="black", height=2, corner_radius=0)
        line.pack(fill="x", pady=(0, 8))
        return title_label
