import customtkinter as ctk
from tkinter import ttk


class ScrollableTree(ctk.CTkFrame):
    def __init__(self, parent, title: str):
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.label = ctk.CTkLabel(self, text=title)
        self.label.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 2))

        self.tree = ttk.Treeview(
            self,
            columns=("player",),
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("player", text="Player")
        self.tree.column("player", anchor="center", stretch=True)

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_player(self, player: str):
        self.tree.insert("", "end", iid=player, values=(player,))

    def selected_player(self) -> str | None:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def exists(self, player: str) -> bool:
        return self.tree.exists(player)

    def bbox(self, player: str):
        return self.tree.bbox(player)
