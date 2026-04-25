import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from src.controllers.settings import debug_print


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


class PlayerPairingFrame(ctk.CTkFrame):
    def __init__(self, parent, players: list[str]):
        super().__init__(parent)
        self.configure(fg_color="#F7F7F7")

        self.all_players = list(players)

        self.pairs: dict[str, str] = {}

        self.left_available = set(players)
        self.right_available = set(players)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.left = ScrollableTree(self, "Left players")
        self.canvas = tk.Canvas(
            self,
            width=220,
            highlightthickness=0,
            bg="#F7F7F7",
        )
        self.right = ScrollableTree(self, "Right players")

        self.left.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        self.canvas.grid(row=0, column=1, sticky="ns", pady=10)
        self.right.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)

        controls = ctk.CTkFrame(self)
        controls.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))
        controls.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            controls,
            text="Create pair",
            command=self.create_pair,
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            controls,
            text="Remove selected pair",
            command=self.remove_selected_pair,
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            controls,
            text="Reset",
            command=self.reset_pairs,
        ).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.pair_list = PairList(self)
        self.pair_list.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="nsew",
            padx=10,
            pady=(0, 10),
        )

        self.left.tree.bind("<<TreeviewSelect>>", lambda event: self.redraw_links())
        self.right.tree.bind("<<TreeviewSelect>>", lambda event: self.redraw_links())

        self.left.tree.bind("<Configure>", lambda event: self.redraw_links())
        self.right.tree.bind("<Configure>", lambda event: self.redraw_links())
        self.canvas.bind("<Configure>", lambda event: self.redraw_links())

        self.left.tree.bind("<MouseWheel>", self._on_scroll, add="+")
        self.right.tree.bind("<MouseWheel>", self._on_scroll, add="+")

        self.pair_list.tree.bind("<<TreeviewSelect>>", self.on_pair_list_selection)

        self.populate()

    def _on_scroll(self, event):
        self.after(10, self.redraw_links)

    def populate(self):
        left_selection = self.left.selected_player()
        right_selection = self.right.selected_player()

        self.left.clear()
        self.right.clear()

        for player in self.all_players:
            if player in self.left_available:
                self.left.insert_player(player)

        for player in self.all_players:
            if player in self.right_available:
                self.right.insert_player(player)

        if left_selection and self.left.exists(left_selection):
            self.left.tree.selection_set(left_selection)

        if right_selection and self.right.exists(right_selection):
            self.right.tree.selection_set(right_selection)

        self.populate_pair_list()

        self.after(10, self.redraw_links)

    def populate_pair_list(self):
        self.pair_list.clear()

        for left_player, right_player in self.pairs.items():
            self.pair_list.insert_pair(left_player, right_player)

    def create_pair(self):
        left_player = self.left.selected_player()
        right_player = self.right.selected_player()

        if not left_player or not right_player:
            debug_print("Select one player in each list.")
            return

        if left_player == right_player:
            debug_print("A player cannot be paired with themselves.")
            return

        if left_player in self.pairs:
            debug_print(f"{left_player} is already paired.")
            return

        if right_player in self.pairs.values():
            debug_print(f"{right_player} is already paired.")
            return

        self.pairs[left_player] = right_player

        # Remove both paired players from both lists.
        self.left_available.discard(left_player)
        self.left_available.discard(right_player)
        self.right_available.discard(left_player)
        self.right_available.discard(right_player)

        self.populate()

    def remove_selected_pair(self):
        selected_pair = self.pair_list.selected_pair()

        if selected_pair is not None:
            pair_left, pair_right = selected_pair
            self.remove_pair(pair_left, pair_right)
            return

        left_player = self.left.selected_player()
        right_player = self.right.selected_player()

        pair_left = None

        if left_player in self.pairs:
            pair_left = left_player

        if pair_left is None and right_player:
            for left, right in self.pairs.items():
                if right == right_player:
                    pair_left = left
                    break

        if pair_left is None:
            debug_print("No pair selected.")
            return

        pair_right = self.pairs[pair_left]

        self.remove_pair(pair_left, pair_right)

    def remove_pair(self, left_player: str, right_player: str):
        if left_player not in self.pairs:
            return

        if self.pairs[left_player] != right_player:
            return

        del self.pairs[left_player]

        # Re-add both players to both lists.
        self.left_available.add(left_player)
        self.left_available.add(right_player)
        self.right_available.add(left_player)
        self.right_available.add(right_player)

        self.populate()

    def reset_pairs(self):
        self.pairs.clear()
        self.left_available = set(self.all_players)
        self.right_available = set(self.all_players)
        self.populate()

    def on_pair_list_selection(self, event):
        selected_pair = self.pair_list.selected_pair()

        if selected_pair is None:
            return

        left_player, right_player = selected_pair

        if self.left.exists(left_player):
            self.left.tree.selection_set(left_player)
            self.left.tree.see(left_player)

        if self.right.exists(right_player):
            self.right.tree.selection_set(right_player)
            self.right.tree.see(right_player)

        self.after(10, self.redraw_links)

    def redraw_links(self):
        self.canvas.delete("all")

        width = self.canvas.winfo_width()

        for left_player, right_player in self.pairs.items():
            if not self.left.exists(left_player):
                continue

            if not self.right.exists(right_player):
                continue

            left_bbox = self.left.bbox(left_player)
            right_bbox = self.right.bbox(right_player)

            if not left_bbox or not right_bbox:
                continue

            _, left_y, _, left_h = left_bbox
            _, right_y, _, right_h = right_bbox

            y1 = left_y + left_h / 2
            y2 = right_y + right_h / 2

            self.canvas.create_line(
                0,
                y1,
                width * 0.35,
                y1,
                width * 0.65,
                y2,
                width,
                y2,
                smooth=True,
                width=2,
                fill="#1F1F1F",
            )

