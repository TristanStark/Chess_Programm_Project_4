import customtkinter as ctk
from src.views.player_info_card_input_view import PlayerInfoCardInput


class CreatePlayerPopup(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback

        self.title("Add Player")
        self.geometry("500x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.form_card = PlayerInfoCardInput(
            self,
            corner_radius=0,
            fg_color="#F7F7F7",
            border_width=2,
            border_color="black",
        )
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 8))

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
        player_data = self.form_card.get_player_info()
        success, message = self.on_save_callback(player_data)
        if success:
            self.destroy()
        else:
            self.error_label.configure(text=message)
