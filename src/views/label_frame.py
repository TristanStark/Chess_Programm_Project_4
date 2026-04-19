import customtkinter as ctk  # pyright: ignore[reportMissingImports]


class CtkLabelFrame(ctk.CTkFrame):
    """CTkLabelFrame custom pour remplacer ttk.LabelFrame."""

    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, **kwargs)

        # Titre posé en haut
        self._title = ctk.CTkLabel(self, text=text, anchor="w")
        self._title.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))

        # Frame interne pour mettre les widgets
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)


# Backward-compatible alias.
LabelFrame = CtkLabelFrame
