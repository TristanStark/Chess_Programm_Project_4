import customtkinter as ctk
from tkinter import ttk


class PairList(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.label = ctk.CTkLabel(self, text="Created pairs")
        self.label.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 2))

        self.tree = ttk.Treeview(
            self,
            columns=("left_player", "right_player"),
            show="headings",
            selectmode="browse",
            height=6,
        )

        self.tree.heading("left_player", text="Left player")
        self.tree.heading("right_player", text="Right player")

        self.tree.column("left_player", anchor="center", stretch=True)
        self.tree.column("right_player", anchor="center", stretch=True)

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_pair(self, left_player: str, right_player: str):
        pair_id = self.make_pair_id(left_player, right_player)

        self.tree.insert(
            "",
            "end",
            iid=pair_id,
            values=(left_player, right_player),
        )

    def selected_pair(self) -> tuple[str, str] | None:
        selection = self.tree.selection()

        if not selection:
            return None

        item_id = selection[0]
        values = self.tree.item(item_id, "values")

        if len(values) != 2:
            return None

        return values[0], values[1]

    @staticmethod
    def make_pair_id(left_player: str, right_player: str) -> str:
        return f"{left_player}__PAIR__{right_player}"
