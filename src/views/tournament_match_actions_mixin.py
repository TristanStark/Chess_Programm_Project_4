import customtkinter as ctk

from src.views.tournament_view_helpers import format_player_name


class TournamentMatchActionsMixin:
    def _on_match_action_button(self):
        match_status = self._get_selected_match_status()
        if match_status == "not_started":
            self._on_start_match()
        elif match_status == "ongoing":
            self._on_end_match()

    def _on_start_match(self):
        selected_indices = self.matches_panel.get_selected_match_indices()
        if not selected_indices and self._selected_match_index is not None:
            selected_indices = [self._selected_match_index]
        if not selected_indices:
            return

        active_round_index = self._get_active_round_index()
        can_change_match, _ = self.match_controller.can_change_match(
            self.current_tournament,
            active_round_index,
        )
        if not can_change_match:
            return

        started = False
        for match_index in selected_indices:
            match = self.match_controller.get_match_by_index(match_index)
            if match is None or match.status != "not_started":
                continue
            started = self.match_controller.start_match(match_index) or started
        if not started:
            return

        self.tournament_controller.update_tournament_status_from_matches(self.current_tournament)
        if self.current_tournament is not None:
            self._render_tournament(
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

        player_1_name = format_player_name(selected_match.player1.player)
        player_2_name = format_player_name(selected_match.player2.player)

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
        self._handle_round_finished()
        self.tournament_controller.update_tournament_status_from_matches(self.current_tournament)

        if self.current_tournament is not None:
            self.tournament_controller.refresh_player_points(self.current_tournament)
            self.left_panel.set_players(self.current_tournament.players)
            rounds_count_after_sync = len(self.current_tournament.rounds)
            moved_to_next_round = rounds_count_after_sync > rounds_count_before_sync
            target_round_index = active_round_index
            if moved_to_next_round:
                target_round_index = rounds_count_after_sync - 1
                self._selected_match_index = None

            self._render_tournament(
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
