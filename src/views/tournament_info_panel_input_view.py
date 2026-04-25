import customtkinter as ctk
from datetime import datetime
from src.views.label_frame import CtkLabelFrame


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
