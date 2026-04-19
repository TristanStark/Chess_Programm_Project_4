from src.views.label_frame import CtkLabelFrame
import customtkinter as ctk  # pyright: ignore[reportMissingImports]
from tkinter import ttk


class TournamentInfoPanel(CtkLabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Tournament details", **kwargs)
        self.grid_propagate(False)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        infos_frame = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=0)
        infos_frame.grid(row=0, column=0, sticky="new", padx=0, pady=0)
        self._section_title(infos_frame, "Status:")

        self._info_value_labels = {
            "status": self._add_info_row(infos_frame, "Status"),
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
        self._set_info_value("status", status)
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
            self.players_tree.insert("", "end", text=player_name)

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

        ctk.CTkLabel(
            players_frame,
            text="Players:",
            anchor="w",
            text_color="black",
            font=ctk.CTkFont(size=16),
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        tree_container = ctk.CTkFrame(players_frame, fg_color="transparent")
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        self.players_tree = ttk.Treeview(
            tree_container,
            columns=("player_name",),
            show="tree",
            height=6,
        )
        self.players_tree.grid(row=0, column=0, sticky="nsew")

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
        ctk.CTkLabel(
            parent,
            text=text,
            text_color="black",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).pack(anchor="w", pady=(0, 6))

        line = ctk.CTkFrame(parent, fg_color="black", height=2, corner_radius=0)
        line.pack(fill="x", pady=(0, 8))


class TournamentInfoPanelInput(CtkLabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Tournament details", **kwargs)
        self.content.grid_columnconfigure(0, weight=0)
        self.content.grid_columnconfigure(1, weight=0)
        self.content.grid_columnconfigure(2, weight=1)
        self.content.grid_rowconfigure(7, weight=1)

        self._build_form()

    def _build_form(self):
        self.name_entry = self._add_entry_row(0, "Name")
        self.venue_entry = self._add_entry_row(1, "Venue")
        self.start_date_entry = self._add_entry_row(2, "Start date", "YYYY-MM-DD")
        self.end_date_entry = self._add_entry_row(3, "End date", "YYYY-MM-DD")
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

        ctk.CTkLabel(self.content, text="Description", anchor="w").grid(
            row=6, column=0, sticky="nw", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=6, column=1, sticky="nw", padx=(0, 8), pady=4
        )
        self.description_textbox = ctk.CTkTextbox(self.content, height=100, wrap="word")
        self.description_textbox.grid(row=6, column=2, rowspan=2, sticky="nsew", pady=4)

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
