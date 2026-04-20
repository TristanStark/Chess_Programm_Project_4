import customtkinter as ctk
from pathlib import Path
import re
from tkinter import filedialog, messagebox
from src.controllers.match_controller import MatchController
from src.controllers.player_controller import PlayerController
from src.controllers.players_controller import PlayersController
from src.controllers.round_controller import RoundController
from src.controllers.tournament_controller import TournamentController
from src.models.players import Player
from src.models.tournaments import Tournament
from src.views.player_info_card_view import CreatePlayerPopup, PlayerInfoCard
from src.views.tournament_view import CreateTournamentPopup, TournamentInfoPanel
from src.views.rounds_view import TournamentRoundsPanel
from src.views.matches_view import TournamentMatchesPanel

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class TournamentView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="#EDEDED", **kwargs)
        self.current_tournament = None
        self.current_tournament_file_path = None
        self._selected_round_index = None
        self._selected_match_index = None
        self._active_round_index_for_matches = None
        self.players_controller = PlayersController(Path("data") / "players")
        self.create_player_popup = None
        self.create_tournament_popup = None
        self.match_result_popup = None
        self._button_disabled_reasons = {}
        self._tooltip_window = None
        self._tooltip_label = None
        self._tooltip_anchor_button = None
        self._tooltip_after_id = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # =========================
        # Main bordered container
        # =========================
        self.container = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="#EDEDED",
            border_width=2,
            border_color="black"
        )
        self.container.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_rowconfigure(2, weight=0)

        # =========================
        # Header
        # =========================
        header = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        header.grid(row=0, column=0, padx=10, pady=(8, 6), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        left_header = ctk.CTkFrame(header, fg_color="transparent")
        left_header.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            left_header,
            text="Tournament:",
            text_color="black",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=(0, 8))

        self.tournament_name_label = ctk.CTkLabel(
            left_header,
            text="Tournament Name",
            text_color="black",
            font=ctk.CTkFont(size=18)
        )
        self.tournament_name_label.pack(side="left")

        self.tournament_venue_label = ctk.CTkLabel(
            header,
            text="Tournament Venue",
            text_color="black",
            font=ctk.CTkFont(size=18)
        )
        self.tournament_venue_label.grid(row=0, column=1, sticky="e")

        # =========================
        # Body
        # =========================
        body = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        body.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        body.grid_columnconfigure(0, weight=0, minsize=256)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # =========================
        # Left panel
        # =========================
        self.left_panel = TournamentInfoPanel(
            body,
            corner_radius=0,
            fg_color="#F7F7F7",
            border_width=2,
            border_color="black",
            width=256,
        )
        self.left_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        self.left_panel.grid_propagate(False)
        self.description_box = self.left_panel.description_box

        # =========================
        # Right panel
        # =========================
        right_panel = ctk.CTkFrame(body, fg_color="transparent", corner_radius=0)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=3)
        right_panel.grid_rowconfigure(1, weight=2)
        right_panel.grid_columnconfigure(0, weight=1)

        # -------- Rounds section --------
        self.rounds_panel = TournamentRoundsPanel(
            right_panel,
            corner_radius=0,
            fg_color="#F7F7F7",
            border_width=2,
            border_color="black",
        )
        self.rounds_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.rounds_tree = self.rounds_panel.rounds_tree

        self.round_controller = RoundController(self.rounds_panel)
        self.round_controller.set_status("Round Name - Start date - End date")
        self.rounds_panel.set_on_round_selected(self._on_round_selected)

        # -------- Lower section (Matches + Player cards) --------
        lower_section = ctk.CTkFrame(right_panel, fg_color="transparent", corner_radius=0)
        lower_section.grid(row=1, column=0, sticky="nsew")
        lower_section.grid_rowconfigure(0, weight=1)
        lower_section.grid_columnconfigure(0, weight=7)
        lower_section.grid_columnconfigure(1, weight=3, minsize=220)

        # -------- Matches section --------
        self.matches_panel = TournamentMatchesPanel(
            lower_section,
            corner_radius=0,
            fg_color="#F7F7F7",
            border_width=2,
            border_color="black",
        )
        self.matches_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.match_scrollable = self.matches_panel.match_scrollable

        self.match_controller = MatchController(self.matches_panel)
        self.matches_panel.set_on_match_selected(self._on_match_selected)

        # -------- Selected players cards --------
        player_cards_frame = ctk.CTkFrame(lower_section, fg_color="transparent", corner_radius=0)
        player_cards_frame.grid(row=0, column=1, sticky="nsew")
        player_cards_frame.grid_columnconfigure(0, weight=1)
        player_cards_frame.grid_rowconfigure(0, weight=0)
        player_cards_frame.grid_rowconfigure(1, weight=0)
        player_cards_frame.grid_rowconfigure(2, weight=1)

        self.player_1_info_card = PlayerInfoCard(
            player_cards_frame,
            corner_radius=0,
            fg_color="#F7F7F7",
            border_width=2,
            border_color="black",
        )
        self.player_1_info_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.player_2_info_card = PlayerInfoCard(
            player_cards_frame,
            corner_radius=0,
            fg_color="#F7F7F7",
            border_width=2,
            border_color="black",
        )
        self.player_2_info_card.grid(row=1, column=0, sticky="ew")

        self.player_1_controller = PlayerController(self.player_1_info_card)
        self.player_2_controller = PlayerController(self.player_2_info_card)

        self.tournament_controller = TournamentController(
            self,
            round_controller=self.round_controller,
            match_controller=self.match_controller,
            tournaments_directory=Path("data") / "tournaments",
        )

        # -------- Actions section --------
        self.actions_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.actions_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        for col in range(8):
            self.actions_frame.grid_columnconfigure(col, weight=1)
        self._build_action_buttons()
        self._register_global_tooltip_guards()
        self._refresh_action_buttons_visibility()

    def _build_action_buttons(self):
        self.save_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Save tournament",
            command=lambda: self._run_action_with_autosave(self._on_save_tournament),
        )
        self.load_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Load tournament",
            command=lambda: self._run_action_with_autosave(self._on_load_tournament),
        )
        self.export_button = ctk.CTkButton(
            self.actions_frame,
            text="Export",
            command=lambda: self._run_action_with_autosave(self._on_export_tournament),
        )
        self.start_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Start tournament",
            command=lambda: self._run_action_with_autosave(self._on_start_tournament),
        )
        self.stop_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Stop tournament",
            command=lambda: self._run_action_with_autosave(self._on_stop_tournament),
        )
        self.match_action_button = ctk.CTkButton(
            self.actions_frame,
            text="Start match",
            command=lambda: self._run_action_with_autosave(self._on_match_action_button),
        )
        self.start_round_button = ctk.CTkButton(
            self.actions_frame,
            text="Start round",
            command=lambda: self._run_action_with_autosave(self._on_start_round),
        )
        self.stop_round_button = ctk.CTkButton(
            self.actions_frame,
            text="Stop round",
            command=lambda: self._run_action_with_autosave(self._on_stop_round),
        )

        self._action_buttons = [
            self.save_tournament_button,
            self.load_tournament_button,
            self.export_button,
            self.start_tournament_button,
            self.stop_tournament_button,
            self.match_action_button,
            self.start_round_button,
            self.stop_round_button,
        ]
        for column, button in enumerate(self._action_buttons):
            button.grid(row=0, column=column, padx=4, pady=2, sticky="ew")

        self.create_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Create a tournament",
            command=lambda: self._run_action_with_autosave(self._on_create_tournament),
        )
        self.create_player_button = ctk.CTkButton(
            self.actions_frame,
            text="Create player",
            command=lambda: self._run_action_with_autosave(self._on_create_player),
        )
        self.add_player_to_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Add player to tournament",
            command=lambda: self._run_action_with_autosave(self._on_add_player_to_tournament),
        )
        self.remove_player_from_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Remove player from tournament",
            command=lambda: self._run_action_with_autosave(self._on_remove_player_from_tournament),
        )
        self.create_tournament_button.grid(
            row=1, column=0, columnspan=2, padx=4, pady=(6, 2), sticky="ew"
        )
        self.create_player_button.grid(
            row=1, column=2, columnspan=2, padx=4, pady=(6, 2), sticky="ew"
        )
        self.add_player_to_tournament_button.grid(
            row=1, column=4, columnspan=2, padx=4, pady=(6, 2), sticky="ew"
        )
        self.remove_player_from_tournament_button.grid(
            row=1, column=6, columnspan=2, padx=4, pady=(6, 2), sticky="ew"
        )

        action_buttons_for_tooltips = [
            self.start_tournament_button,
            self.stop_tournament_button,
            self.match_action_button,
            self.start_round_button,
            self.stop_round_button,
            self.create_tournament_button,
            self.create_player_button,
            self.add_player_to_tournament_button,
            self.remove_player_from_tournament_button,
        ]
        for button in action_buttons_for_tooltips:
            self._register_action_tooltip(button)

        self.left_panel.players_tree.bind(
            "<<TreeviewSelect>>",
            lambda _event: self._refresh_action_buttons_visibility(),
            add="+",
        )

    def _refresh_action_buttons_visibility(self):
        self._hide_action_tooltip()
        self._sync_round_status_colors()
        has_active_tournament = self.current_tournament is not None
        selected_round_index = self._selected_round_index
        active_round_index = self._get_active_round_index()
        match_status = self._get_selected_match_status()

        can_start_tournament, start_tournament_reason = self.tournament_controller.can_start_tournament(
            self.current_tournament
        )
        can_stop_tournament, stop_tournament_reason = self.tournament_controller.can_stop_tournament(
            self.current_tournament
        )
        can_start_round, start_round_reason = self.round_controller.can_start_round(
            self.current_tournament,
            selected_round_index,
        )
        can_stop_round, stop_round_reason = self.round_controller.can_stop_round(
            self.current_tournament,
            selected_round_index,
        )
        can_change_match, change_match_reason = self.match_controller.can_change_match(
            self.current_tournament,
            active_round_index,
        )
        can_create_tournament, create_tournament_reason = self.tournament_controller.can_create_tournament(
            self.current_tournament
        )
        can_create_player, create_player_reason = self.players_controller.can_create_player(
            self.current_tournament
        )
        can_add_player, add_player_reason = self.players_controller.can_add_player_to_tournament(
            self.current_tournament
        )
        can_remove_player, remove_player_reason = self.players_controller.can_remove_player_from_tournament(
            self.current_tournament,
            self._get_selected_tournament_player(),
        )

        self._set_button_enabled(
            self.start_tournament_button,
            can_start_tournament,
            disabled_reason=start_tournament_reason,
        )
        self._set_button_enabled(
            self.stop_tournament_button,
            can_stop_tournament,
            disabled_reason=stop_tournament_reason,
        )

        self._set_match_action_button(
            match_status=match_status,
            can_change_match=can_change_match,
            disabled_reason=change_match_reason,
        )
        self._set_button_enabled(
            self.start_round_button,
            can_start_round,
            disabled_reason=start_round_reason,
        )
        self._set_button_enabled(
            self.stop_round_button,
            can_stop_round,
            disabled_reason=stop_round_reason,
        )
        self._set_button_enabled(
            self.create_tournament_button,
            can_create_tournament,
            disabled_reason=create_tournament_reason,
        )
        self._set_button_enabled(
            self.create_player_button,
            can_create_player,
            disabled_reason=create_player_reason,
        )
        self._set_button_enabled(
            self.add_player_to_tournament_button,
            can_add_player,
            disabled_reason=add_player_reason,
        )
        self._set_button_enabled(
            self.remove_player_from_tournament_button,
            can_remove_player,
            disabled_reason=remove_player_reason,
        )
        self._set_button_visibility(
            self.add_player_to_tournament_button,
            has_active_tournament,
        )
        self._set_button_visibility(
            self.remove_player_from_tournament_button,
            has_active_tournament,
        )
        if not has_active_tournament:
            self._button_disabled_reasons[self.add_player_to_tournament_button] = ""
            self._button_disabled_reasons[self.remove_player_from_tournament_button] = ""

    @staticmethod
    def _set_button_visibility(button, should_show):
        if should_show:
            button.grid()
        else:
            button.grid_remove()

    def _set_button_enabled(self, button, enabled, disabled_reason: str = ""):
        button.configure(state=("normal" if enabled else "disabled"))
        if enabled:
            self._button_disabled_reasons[button] = ""
        else:
            self._button_disabled_reasons[button] = disabled_reason or "Action unavailable."

    def _set_match_action_button(
        self,
        match_status,
        can_change_match: bool,
        disabled_reason: str = "",
    ):
        if match_status == "not_started":
            self.match_action_button.configure(
                text="Start match",
                command=lambda: self._run_action_with_autosave(self._on_start_match),
            )
            self._set_button_visibility(self.match_action_button, True)
            self._set_button_enabled(
                self.match_action_button,
                can_change_match,
                disabled_reason=disabled_reason,
            )
            return

        if match_status == "ongoing":
            self.match_action_button.configure(
                text="End match",
                command=lambda: self._run_action_with_autosave(self._on_end_match),
            )
            self._set_button_visibility(self.match_action_button, True)
            self._set_button_enabled(
                self.match_action_button,
                can_change_match,
                disabled_reason=disabled_reason,
            )
            return

        self._set_button_visibility(self.match_action_button, False)
        self._button_disabled_reasons[self.match_action_button] = ""

    def _register_action_tooltip(self, button):
        button.bind("<Enter>", lambda event, btn=button: self._on_action_button_enter(event, btn), add="+")
        button.bind("<Motion>", lambda event: self._on_action_button_motion(event), add="+")
        button.bind("<Leave>", lambda _event: self._hide_action_tooltip(), add="+")
        button.bind("<ButtonPress-1>", lambda _event: self._hide_action_tooltip(), add="+")

    def _register_global_tooltip_guards(self):
        root = self.winfo_toplevel()
        root.bind("<Motion>", lambda _event: self._guard_active_tooltip(), add="+")
        root.bind("<ButtonPress>", lambda _event: self._hide_action_tooltip(), add="+")
        root.bind("<Configure>", lambda _event: self._guard_active_tooltip(), add="+")
        root.bind("<FocusOut>", lambda _event: self._hide_action_tooltip(), add="+")

    def _guard_active_tooltip(self):
        if self._tooltip_window is None or not self._tooltip_window.winfo_exists():
            return

        button = self._tooltip_anchor_button
        if button is None or not button.winfo_exists() or not button.winfo_ismapped():
            self._hide_action_tooltip()
            return

        if str(button.cget("state")).strip().lower() != "disabled":
            self._hide_action_tooltip()
            return

        if not self._is_pointer_over_widget(button):
            self._hide_action_tooltip()
            return

    def _on_action_button_enter(self, event, button):
        if str(button.cget("state")).strip().lower() != "disabled":
            self._hide_action_tooltip()
            return

        reason = self._button_disabled_reasons.get(button, "").strip()
        if not reason:
            self._hide_action_tooltip()
            return

        self._show_action_tooltip(
            event.x_root + 14,
            event.y_root + 14,
            reason,
            anchor_button=button,
        )

    def _on_action_button_motion(self, event):
        if self._tooltip_window is None or not self._tooltip_window.winfo_exists():
            return
        if self._tooltip_anchor_button is not None and event.widget != self._tooltip_anchor_button:
            self._hide_action_tooltip()
            return
        self._tooltip_window.geometry(f"+{event.x_root + 14}+{event.y_root + 14}")

    def _show_action_tooltip(self, x, y, text, anchor_button=None):
        self._hide_action_tooltip()
        self._tooltip_anchor_button = anchor_button
        self._tooltip_window = ctk.CTkToplevel(self.winfo_toplevel())
        self._tooltip_window.overrideredirect(True)
        self._tooltip_window.attributes("-topmost", True)
        self._tooltip_window.geometry(f"+{x}+{y}")
        self._tooltip_label = ctk.CTkLabel(
            self._tooltip_window,
            text=text,
            fg_color="#FDF6E3",
            text_color="black",
            corner_radius=6,
            padx=10,
            pady=6,
            justify="left",
            wraplength=360,
        )
        self._tooltip_label.pack()
        self._schedule_tooltip_hover_check()

    def _schedule_tooltip_hover_check(self):
        if self._tooltip_after_id is not None:
            try:
                self.after_cancel(self._tooltip_after_id)
            except Exception:
                pass
            self._tooltip_after_id = None

        self._tooltip_after_id = self.after(120, self._check_tooltip_hover)

    def _check_tooltip_hover(self):
        self._tooltip_after_id = None
        button = self._tooltip_anchor_button
        if button is None or not button.winfo_exists() or not button.winfo_ismapped():
            self._hide_action_tooltip()
            return

        if str(button.cget("state")).strip().lower() != "disabled":
            self._hide_action_tooltip()
            return

        if not self._is_pointer_over_widget(button):
            self._hide_action_tooltip()
            return

        self._schedule_tooltip_hover_check()

    def _is_pointer_over_widget(self, target_widget) -> bool:
        pointer_x, pointer_y = self.winfo_pointerxy()
        hovered_widget = self.winfo_containing(pointer_x, pointer_y)
        while hovered_widget is not None:
            if hovered_widget == target_widget:
                return True
            hovered_widget = hovered_widget.master
        return False

    def _hide_action_tooltip(self):
        if self._tooltip_after_id is not None:
            try:
                self.after_cancel(self._tooltip_after_id)
            except Exception:
                pass
            self._tooltip_after_id = None

        if self._tooltip_window is not None and self._tooltip_window.winfo_exists():
            self._tooltip_window.destroy()
        self._tooltip_window = None
        self._tooltip_label = None
        self._tooltip_anchor_button = None

    def _initialize_runtime_statuses(self, tournament: Tournament):
        self._selected_round_index = None
        self._selected_match_index = None
        self.tournament_controller.initialize_runtime_state(tournament)

    def _set_active_tournament(
        self,
        tournament: Tournament | None,
        file_path: Path | None = None,
    ):
        self.current_tournament = tournament
        self.current_tournament_file_path = file_path
        self._selected_round_index = None
        self._selected_match_index = None
        self._active_round_index_for_matches = None

        if self.current_tournament is None:
            self.match_controller.populate_view([])
            self.player_1_controller.select_player(None)
            self.player_2_controller.select_player(None)
            self._refresh_action_buttons_visibility()
            return

        self._initialize_runtime_statuses(self.current_tournament)
        self.tournament_controller.populate_view(self.current_tournament)
        if self.current_tournament.rounds:
            self._active_round_index_for_matches = len(self.current_tournament.rounds) - 1
            self.match_controller.populate_from_round(
                self.current_tournament.rounds[self._active_round_index_for_matches]
            )
        else:
            self.match_controller.populate_view([])
        self.player_1_controller.select_player(None)
        self.player_2_controller.select_player(None)
        self._refresh_action_buttons_visibility()

    def _save_tournament(
        self,
        *,
        prompt_path_if_missing: bool,
        show_success_message: bool,
    ) -> bool:
        if self.current_tournament is None:
            messagebox.showerror("Tournament", "No active tournament.")
            return False

        target_file_path = self.current_tournament_file_path
        if target_file_path is None and prompt_path_if_missing:
            selected_path = filedialog.asksaveasfilename(
                title="Save tournament JSON file",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=str(self.tournament_controller.tournaments_directory),
            )
            if not selected_path:
                return False
            target_file_path = Path(selected_path)

        success, message, saved_path = self.tournament_controller.save_tournament_to_json(
            self.current_tournament,
            target_file_path,
        )
        if not success:
            messagebox.showerror("Tournament", message)
            return False

        self.current_tournament_file_path = saved_path
        if show_success_message:
            messagebox.showinfo("Tournament", message)
        return True

    def _run_action_with_autosave(self, action) -> None:
        try:
            action()
        finally:
            self._autosave_tournament()

    def _autosave_tournament(self):
        if self.current_tournament is None or self.current_tournament_file_path is None:
            return
        self._save_tournament(
            prompt_path_if_missing=False,
            show_success_message=False,
        )

    def _get_selected_tournament_player(self):
        if self.current_tournament is None:
            return None

        selection = self.left_panel.players_tree.selection()
        if not selection:
            return None

        selected_item_id = selection[0]
        all_items = self.left_panel.players_tree.get_children("")
        if selected_item_id not in all_items:
            return None

        selected_index = all_items.index(selected_item_id)
        if not 0 <= selected_index < len(self.current_tournament.players):
            return None
        return self.current_tournament.players[selected_index]

    def _get_selected_match_status(self):
        if self._selected_match_index is None:
            return None
        match = self.match_controller.get_match_by_index(self._selected_match_index)
        if match is None:
            return None
        return str(getattr(match, "status", "")).strip().lower()

    def _on_round_selected(self, selected_round_index):
        self._selected_round_index = selected_round_index
        self._selected_match_index = None
        if selected_round_index is not None:
            selected_round = self.round_controller.get_round_by_index(selected_round_index)
            if selected_round is not None:
                self._active_round_index_for_matches = selected_round_index
                self.match_controller.populate_from_round(selected_round)
        self._refresh_action_buttons_visibility()

    def _on_match_selected(self, selected_match_index):
        self._selected_match_index = selected_match_index
        selected_match = self.match_controller.get_match_by_index(selected_match_index)
        if selected_match is None:
            self.player_1_controller.select_player(None)
            self.player_2_controller.select_player(None)
        else:
            self.player_1_controller.select_player(selected_match.player1.player)
            self.player_2_controller.select_player(selected_match.player2.player)
        self._refresh_action_buttons_visibility()

    def _on_save_tournament(self):
        self._save_tournament(
            prompt_path_if_missing=True,
            show_success_message=False,
        )

    def _on_load_tournament(self):
        selected_path = filedialog.askopenfilename(
            title="Select tournament JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(self.tournament_controller.tournaments_directory),
        )
        if not selected_path:
            return

        file_path = Path(selected_path)
        success, message, tournament = self.tournament_controller.load_tournament_from_json(file_path)
        if not success:
            messagebox.showerror("Tournament", message)
            return

        self._set_active_tournament(tournament, file_path=file_path)

    def _on_export_tournament(self):
        print("Export tournament clicked")

    def _on_create_tournament(self):
        can_create, reason = self.tournament_controller.can_create_tournament(
            self.current_tournament
        )
        if not can_create:
            messagebox.showerror(
                "Tournament",
                reason,
            )
            return

        if (
            self.create_tournament_popup is not None
            and self.create_tournament_popup.winfo_exists()
        ):
            self.create_tournament_popup.lift()
            self.create_tournament_popup.focus_force()
            return

        self.create_tournament_popup = CreateTournamentPopup(
            self.winfo_toplevel(),
            on_save_callback=self._save_tournament_from_popup,
        )

    def _on_create_player(self):
        can_create, reason = self.players_controller.can_create_player(
            self.current_tournament
        )
        if not can_create:
            messagebox.showerror(
                "Player",
                reason,
            )
            return

        if self.create_player_popup is not None and self.create_player_popup.winfo_exists():
            self.create_player_popup.lift()
            self.create_player_popup.focus_force()
            return

        self.create_player_popup = CreatePlayerPopup(
            self.winfo_toplevel(),
            on_save_callback=self._save_player_from_popup,
        )

    def _on_add_player_to_tournament(self):
        if self.current_tournament is None:
            messagebox.showerror("Tournament", "No active tournament.")
            return
        can_add, reason = self.players_controller.can_add_player_to_tournament(
            self.current_tournament
        )
        if not can_add:
            messagebox.showerror(
                "Tournament",
                reason,
            )
            return

        selected_paths = filedialog.askopenfilenames(
            title="Select player JSON files",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(self.players_controller.players_directory),
        )
        if not selected_paths:
            return

        imported_count = 0
        failed_imports = []

        for selected_path in selected_paths:
            path_obj = Path(selected_path)
            success, message = self.tournament_controller.add_player_to_tournament(
                self.current_tournament,
                player_file_name=path_obj.name,
                player_file_path=str(path_obj),
            )
            if success:
                imported_count += 1
            else:
                failed_imports.append(f"{path_obj.name}: {message}")

        if imported_count == 0:
            messagebox.showerror("Players", "\n".join(failed_imports))
            return

        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

        if failed_imports:
            messagebox.showwarning(
                "Players",
                (
                    f"Imported {imported_count} player(s).\n\n"
                    "Some files failed:\n"
                    + "\n".join(failed_imports)
                ),
            )

    def _on_remove_player_from_tournament(self):
        selected_player = self._get_selected_tournament_player()
        can_remove, reason = self.players_controller.can_remove_player_from_tournament(
            self.current_tournament,
            selected_player,
        )
        if not can_remove:
            messagebox.showerror("Players", reason)
            return

        success, message = self.tournament_controller.remove_player_from_tournament(
            self.current_tournament,
            selected_player,
        )
        if not success:
            messagebox.showerror("Players", message)
            return

        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _save_player_from_popup(self, player_data):
        first_name = player_data["first_name"]
        last_name = player_data["last_name"]
        date_of_birth = player_data["date_of_birth"]
        ncid = player_data["ncid"].upper()

        player = self.players_controller.create_player(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            national_chess_identifier=ncid,
        )
        if player is None:
            return (
                False,
                "Invalid player data. NCID format must be 2 letters + 5 digits (example: AA12345).",
            )

        base_filename = self._build_player_filename(player)
        filename = self._next_available_player_filename(base_filename)
        self.players_controller.save_player(player, filename)
        return True, ""

    def _save_tournament_from_popup(self, tournament_data):
        success, message, tournament, file_path = self.tournament_controller.create_and_save_tournament(
            tournament_data,
            current_tournament=self.current_tournament,
        )
        if not success:
            return False, message

        self._set_active_tournament(tournament, file_path=file_path)
        return True, ""

    def _build_player_filename(self, player: Player):
        raw_value = f"{player.first_name}_{player.last_name}_{player.national_chess_identifier}"
        sanitized = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_value).strip("_").lower()
        return sanitized or "player"

    def _next_available_player_filename(self, base_filename):
        candidate = base_filename
        suffix = 2
        while (self.players_controller.players_directory / f"{candidate}.json").exists():
            candidate = f"{base_filename}_{suffix}"
            suffix += 1
        return candidate

    def _on_start_tournament(self):
        success, message = self.tournament_controller.start_tournament(self.current_tournament)
        if not success:
            messagebox.showerror("Tournament", message)
            return

        self._selected_round_index = None
        self._selected_match_index = None
        self._active_round_index_for_matches = 0 if self.current_tournament.rounds else None
        self.tournament_controller.populate_view(self.current_tournament)
        if self._active_round_index_for_matches is not None:
            self.match_controller.populate_from_round(
                self.current_tournament.rounds[self._active_round_index_for_matches]
            )
            self.rounds_panel.select_round(self._active_round_index_for_matches)
        self.player_1_controller.select_player(None)
        self.player_2_controller.select_player(None)
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _on_stop_tournament(self):
        success, message = self.tournament_controller.stop_tournament(self.current_tournament)
        if not success:
            messagebox.showerror("Tournament", message)
            return

        self.tournament_controller.populate_view(
            self.current_tournament,
            populate_rounds=False,
            populate_matches_from_current_round=False,
        )
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _on_start_round(self):
        success, message = self.round_controller.start_round(
            self.current_tournament,
            self._selected_round_index,
        )
        if not success:
            messagebox.showerror("Round", message)
            return

        self.tournament_controller.update_tournament_status_from_matches(self.current_tournament)
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _on_stop_round(self):
        success, message = self.round_controller.stop_round(
            self.current_tournament,
            self._selected_round_index,
            on_round_finished=self.tournament_controller.generate_next_round_if_possible,
        )
        if not success:
            messagebox.showerror("Round", message)
            return

        if self.current_tournament is not None:
            self.tournament_controller.populate_view(
                self.current_tournament,
                populate_rounds=True,
                populate_matches_from_current_round=False,
            )
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _on_match_action_button(self):
        match_status = self._get_selected_match_status()
        if match_status == "not_started":
            self._on_start_match()
        elif match_status == "ongoing":
            self._on_end_match()

    def _on_start_match(self):
        if self._selected_match_index is None:
            return

        active_round_index = self._get_active_round_index()
        can_change_match, _ = self.match_controller.can_change_match(
            self.current_tournament,
            active_round_index,
        )
        if not can_change_match:
            return

        started = self.match_controller.start_match(self._selected_match_index)
        if not started:
            return

        self.tournament_controller.update_tournament_status_from_matches(self.current_tournament)
        if self.current_tournament is not None:
            self.tournament_controller.populate_view(
                self.current_tournament,
                populate_rounds=False,
                populate_matches_from_current_round=False,
            )
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _on_end_match(self):
        if self._selected_match_index is None:
            return

        active_round_index = self._get_active_round_index()
        can_change_match, _ = self.match_controller.can_change_match(
            self.current_tournament,
            active_round_index,
        )
        if not can_change_match:
            return

        selected_match = self.match_controller.get_match_by_index(self._selected_match_index)
        if selected_match is None or selected_match.status != "ongoing":
            return

        if self.match_result_popup is not None and self.match_result_popup.winfo_exists():
            self.match_result_popup.lift()
            self.match_result_popup.focus_force()
            return

        player_1_name = self._format_player_name(selected_match.player1.player)
        player_2_name = self._format_player_name(selected_match.player2.player)

        self.match_result_popup = ctk.CTkToplevel(self.winfo_toplevel())
        self.match_result_popup.title("Match Result")
        self.match_result_popup.geometry("560x140")
        self.match_result_popup.resizable(False, False)
        self.match_result_popup.transient(self.winfo_toplevel())
        self.match_result_popup.grab_set()
        self.match_result_popup.protocol("WM_DELETE_WINDOW", self._close_match_result_popup)

        self.match_result_popup.grid_columnconfigure(0, weight=1)
        self.match_result_popup.grid_rowconfigure(0, weight=1)

        buttons_container = ctk.CTkFrame(self.match_result_popup, fg_color="transparent")
        buttons_container.grid(row=0, column=0, padx=12, pady=16, sticky="ew")
        buttons_container.grid_columnconfigure(0, weight=1)
        buttons_container.grid_columnconfigure(1, weight=1)
        buttons_container.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(
            buttons_container,
            text=player_1_name,
            command=lambda: self._run_action_with_autosave(
                lambda: self._finalize_match_result("player1")
            ),
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            buttons_container,
            text="Tie",
            command=lambda: self._run_action_with_autosave(
                lambda: self._finalize_match_result("tie")
            ),
        ).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(
            buttons_container,
            text=player_2_name,
            command=lambda: self._run_action_with_autosave(
                lambda: self._finalize_match_result("player2")
            ),
        ).grid(row=0, column=2, padx=(6, 0), sticky="ew")

        self.match_result_popup.bind("<Escape>", lambda _event: self._close_match_result_popup())

    def _finalize_match_result(self, result: str):
        if self._selected_match_index is None:
            self._close_match_result_popup()
            return

        active_round_index = self._get_active_round_index()
        selected_round = self.round_controller.get_round_by_index(active_round_index)
        selected_match = self.match_controller.get_match_by_index(self._selected_match_index)
        rounds_count_before_sync = (
            len(self.current_tournament.rounds) if self.current_tournament is not None else 0
        )

        finished = self.match_controller.finish_match(
            self._selected_match_index,
            result,
            round_=selected_round,
            tournament=self.current_tournament,
        )
        self._close_match_result_popup()
        if not finished:
            return

        self.tournament_controller.update_pairing_generator_after_match(
            self.current_tournament,
            selected_match,
            result,
        )

        self.tournament_controller.sync_round_status_from_matches(
            self.current_tournament,
            active_round_index,
        )
        self.tournament_controller.update_tournament_status_from_matches(self.current_tournament)

        if self.current_tournament is not None:
            self.left_panel.set_players(self.current_tournament.players)
            rounds_count_after_sync = len(self.current_tournament.rounds)
            moved_to_next_round = rounds_count_after_sync > rounds_count_before_sync
            target_round_index = active_round_index
            if moved_to_next_round:
                target_round_index = rounds_count_after_sync - 1
                self._selected_match_index = None

            self.tournament_controller.populate_view(
                self.current_tournament,
                populate_rounds=True,
                populate_matches_from_current_round=False,
            )

            if target_round_index is not None:
                self._active_round_index_for_matches = target_round_index
                self.rounds_panel.select_round(target_round_index)
                if (
                    not moved_to_next_round
                    and selected_round is not None
                    and self._selected_match_index is not None
                ):
                    self.matches_panel.select_match(self._selected_match_index)

        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _close_match_result_popup(self):
        if self.match_result_popup is not None and self.match_result_popup.winfo_exists():
            self.match_result_popup.grab_release()
            self.match_result_popup.destroy()
        self.match_result_popup = None

    def _get_active_round_index(self):
        if self._selected_round_index is not None:
            return self._selected_round_index
        return self._active_round_index_for_matches

    def _sync_round_status_colors(self):
        if self.current_tournament is None:
            return
        for index, round_ in enumerate(self.current_tournament.rounds):
            self.round_controller.update_round_status(index, round_.status)

    @staticmethod
    def _format_player_name(player):
        first_name = getattr(player, "first_name", "")
        last_name = getattr(player, "last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        return full_name if full_name else str(player)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tournament View")
        self.geometry("1050x760")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        view = TournamentView(self)
        view.grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    app = App()
    app.mainloop()
