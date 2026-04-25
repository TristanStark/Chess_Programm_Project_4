import customtkinter as ctk
from src.views.create_round_view import PlayerPairingFrame


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
