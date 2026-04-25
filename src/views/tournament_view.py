from src.views.label_frame import CtkLabelFrame
from src.views.create_round_view import PlayerPairingFrame
import customtkinter as ctk  # pyright: ignore[reportMissingImports]
from datetime import datetime
from tkinter import ttk


class TournamentInfoPanel(CtkLabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Tournament details", **kwargs)
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
        self.status_title_label.configure(text=f"Status: {status}")
        self._set_info_value("start_date", start_date)
        self._set_info_value("end_date", end_date)
        self._set_info_value("number_of_rounds", number_of_rounds)
        self._set_info_value("current_round", current_round)

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
        self.players_tree.heading("player_name", text="Player")
        self.players_tree.heading("total_points", text="Points")
        self.players_tree.column("player_name", anchor="w", stretch=True, width=150, minwidth=100)
        self.players_tree.column("total_points", anchor="e", stretch=False, width=64, minwidth=64)
        self.players_tree.grid(row=0, column=0, sticky="nsew")

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


class TournamentInfoPanelInput(CtkLabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Tournament details", **kwargs)
        self.content.grid_columnconfigure(0, weight=0)
        self.content.grid_columnconfigure(1, weight=0)
        self.content.grid_columnconfigure(2, weight=1)
        self.content.grid_rowconfigure(8, weight=1)

        self._build_form()

    def _build_form(self):
        self.name_entry = self._add_entry_row(0, "Name")
        self.venue_entry = self._add_entry_row(1, "Venue")
        self.start_date_entry = self._add_entry_row(2, "Start date", "YYYY-MM-DD")
        self.end_date_entry = self._add_entry_row(3, "End date", "YYYY-MM-DD")
        today = datetime.today().strftime("%Y-%m-%d")
        self.start_date_entry.insert(0, today)
        self.end_date_entry.insert(0, today)
        self.number_of_rounds_entry = self._add_entry_row(4, "Number of rounds")
        self.number_of_rounds_entry.insert(0, "4")

        ctk.CTkLabel(self.content, text="Status", anchor="w").grid(
            row=5, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=5, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.status_var = ctk.StringVar(value="Preparation")
        self.status_menu = ctk.CTkOptionMenu(
            self.content,
            values=["Preparation", "Ongoing", "Completed"],
            variable=self.status_var,
        )
        self.status_menu.grid(row=5, column=2, sticky="ew", pady=4)

        ctk.CTkLabel(self.content, text="Pairings mode", anchor="w").grid(
            row=6, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=6, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.pairings_mode_var = ctk.StringVar(value="Automatic")
        self.pairings_mode_menu = ctk.CTkOptionMenu(
            self.content,
            values=["Automatic", "Manual"],
            variable=self.pairings_mode_var,
        )
        self.pairings_mode_menu.grid(row=6, column=2, sticky="ew", pady=4)

        ctk.CTkLabel(self.content, text="Description", anchor="w").grid(
            row=7, column=0, sticky="nw", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=7, column=1, sticky="nw", padx=(0, 8), pady=4
        )
        self.description_textbox = ctk.CTkTextbox(self.content, height=100, wrap="word")
        self.description_textbox.grid(row=7, column=2, rowspan=2, sticky="nsew", pady=4)

    def _add_entry_row(self, row, label_text, placeholder_text=""):
        ctk.CTkLabel(self.content, text=label_text, anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        entry = ctk.CTkEntry(self.content, placeholder_text=placeholder_text)
        entry.grid(row=row, column=2, sticky="ew", pady=4)
        return entry

    def get_tournament_info(self):
        return {
            "name": self.name_entry.get().strip(),
            "venue": self.venue_entry.get().strip(),
            "start_date": self.start_date_entry.get().strip(),
            "end_date": self.end_date_entry.get().strip(),
            "number_of_rounds": self.number_of_rounds_entry.get().strip(),
            "status": self.status_var.get().strip(),
            "automatic_pairings": self.pairings_mode_var.get().strip().lower() == "automatic",
            "description": self.description_textbox.get("1.0", "end").strip(),
        }


class CreateTournamentPopup(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback

        self.title("Create Tournament")
        self.geometry("620x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.form_panel = TournamentInfoPanelInput(
            self,
            corner_radius=0,
            fg_color="#F7F7F7",
            border_width=2,
            border_color="black",
        )
        self.form_panel.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 8))

        self.error_label = ctk.CTkLabel(self, text="", text_color="#B00020", anchor="w")
        self.error_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(actions, text="Save", command=self._on_save).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(actions, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

        self.bind("<Escape>", lambda _event: self.destroy())

    def _on_save(self):
        tournament_data = self.form_panel.get_tournament_info()
        success, message = self.on_save_callback(tournament_data)
        if success:
            self.destroy()
        else:
            self.error_label.configure(text=message)


class CreateRoundPopup(ctk.CTkToplevel):
    def __init__(self, parent, players, round_number: int, on_save_callback):
        super().__init__(parent)
        self.players = list(players)
        self.round_number = int(round_number)
        self.on_save_callback = on_save_callback
        self._player_options = [self._format_player_label(player) for player in self.players]

        self.title("Create Round")
        self.geometry("900x700")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Round name", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.round_name_entry = ctk.CTkEntry(header)
        self.round_name_entry.grid(row=0, column=1, sticky="ew")
        self.round_name_entry.insert(0, f"Round {self.round_number}")

        pairings_frame = ctk.CTkFrame(self, fg_color="#F7F7F7")
        pairings_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        pairings_frame.grid_columnconfigure(0, weight=1)
        pairings_frame.grid_rowconfigure(0, weight=1)

        self.pairing_view = PlayerPairingFrame(
            pairings_frame,
            players=self._player_options,
        )
        self.pairing_view.grid(row=0, column=0, sticky="nsew")

        self.error_label = ctk.CTkLabel(self, text="", text_color="#B00020", anchor="w")
        self.error_label.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(actions, text="Save", command=self._on_save).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(actions, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

        self.bind("<Escape>", lambda _event: self.destroy())

    def _on_save(self):
        round_name = self.round_name_entry.get().strip()
        if not round_name:
            self.error_label.configure(text="Round name is required.")
            return

        expected_matches_count = len(self.players) // 2
        created_pairs = list(self.pairing_view.pairs.items())
        if len(created_pairs) != expected_matches_count:
            self.error_label.configure(
                text=f"Please create exactly {expected_matches_count} pairs."
            )
            return

        pairings = [
            {
                "player_1_label": player_1_label,
                "player_2_label": player_2_label,
            }
            for player_1_label, player_2_label in created_pairs
        ]

        success, message = self.on_save_callback(
            {
                "name": round_name,
                "pairings": pairings,
            }
        )
        if success:
            self.destroy()
        else:
            self.error_label.configure(text=message)

    @staticmethod
    def _format_player_label(player):
        first_name = getattr(player, "first_name", "")
        last_name = getattr(player, "last_name", "")
        ncid = getattr(player, "national_chess_identifier", "")
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            return f"{full_name} [{ncid}]"
        return str(player)


class RenameRoundPopup(ctk.CTkToplevel):
    def __init__(self, parent, initial_name: str, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback

        self.title("Rename Round")
        self.geometry("460x160")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 8))
        content.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(content, text="Round name", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
        )
        self.round_name_entry = ctk.CTkEntry(content)
        self.round_name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 6))
        self.round_name_entry.insert(0, initial_name or "")

        self.error_label = ctk.CTkLabel(content, text="", text_color="#B00020", anchor="w")
        self.error_label.grid(row=1, column=0, columnspan=2, sticky="ew")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(actions, text="Save", command=self._on_save).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(actions, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

        self.bind("<Escape>", lambda _event: self.destroy())

    def _on_save(self):
        new_name = self.round_name_entry.get().strip()
        if not new_name:
            self.error_label.configure(text="Round name is required.")
            return
        success, message = self.on_save_callback(new_name)
        if success:
            self.destroy()
        else:
            self.error_label.configure(text=message)
