import customtkinter as ctk


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
