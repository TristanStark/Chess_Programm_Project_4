import customtkinter as ctk
from datetime import datetime
from pathlib import Path
import re
from tkinter import filedialog, messagebox
from src.controllers.match_controller import MatchController
from src.controllers.player_controller import PlayerController
from src.controllers.players_controller import PlayersController
from src.controllers.round_controller import RoundController
from src.controllers.tournament_controller import TournamentController
from src.models.matches import Match, Round, Score
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
        self._selected_round_index = None
        self._selected_match_index = None
        self._active_round_index_for_matches = None
        self._round_statuses = []
        self.players_controller = PlayersController(Path("data") / "players")
        self.create_player_popup = None
        self.create_tournament_popup = None
        self.match_result_popup = None

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

        # Sample model data to demonstrate MVC wiring.
        caruana = Player("Fabiano", "Caruana", "1992-07-30", "US12345")
        nakamura = Player("Hikaru", "Nakamura", "1987-12-09", "US23456")
        firouzja = Player("Alireza", "Firouzja", "2003-06-18", "FR34567")
        ding = Player("Ding", "Liren", "1992-10-24", "CN45678")
        nepo = Player("Ian", "Nepomniachtchi", "1990-07-14", "RU56789")
        giri = Player("Anish", "Giri", "1994-06-28", "NL67890")

        qualifiers_matches = [
            Match(player1=Score(caruana, 1.0), player2=Score(nakamura, 0.0)),
            Match(player1=Score(firouzja, 0.5), player2=Score(ding, 0.5)),
        ]
        semifinal_matches = [
            Match(player1=Score(nepo, 0.0), player2=Score(giri, 1.0)),
        ]
        final_matches = [
            Match(player1=Score(caruana, 0.5), player2=Score(giri, 0.5)),
        ]

        sample_rounds = [
            Round(
                name="Qualifiers",
                matches=qualifiers_matches,
                start_date=datetime(2026, 5, 1, 9, 0),
                end_date=datetime(2026, 5, 2, 18, 0),
            ),
            Round(
                name="Semi-finals",
                matches=semifinal_matches,
                start_date=datetime(2026, 5, 3, 9, 0),
                end_date=datetime(2026, 5, 3, 18, 0),
            ),
            Round(
                name="Final",
                matches=final_matches,
                start_date=datetime(2026, 5, 4, 14, 0),
                end_date=datetime(2026, 5, 4, 17, 0),
            ),
        ]

        sample_tournament = Tournament(
            name="Grand Masters Open",
            venue="Paris",
            start_date=datetime(2026, 5, 1, 9, 0),
            end_date=datetime(2026, 5, 4, 17, 0),
            description=(
                "International invitational event.\n"
                "Rapid tiebreaks are scheduled in case of equal points."
            ),
            players=[caruana, nakamura, firouzja, ding, nepo, giri],
            rounds=sample_rounds,
            number_of_rounds=4,
        )
        sample_tournament.status = "Preparation"

        self.current_tournament = sample_tournament
        self.tournament_controller.populate_view(self.current_tournament)
        self._initialize_runtime_statuses(self.current_tournament)
        if self.current_tournament.rounds:
            self._active_round_index_for_matches = len(self.current_tournament.rounds) - 1
            self.match_controller.populate_from_round(
                self.current_tournament.rounds[self._active_round_index_for_matches]
            )
        self._refresh_action_buttons_visibility()

    def _build_action_buttons(self):
        self.save_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Save tournament",
            command=self._on_save_tournament,
        )
        self.load_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Load tournament",
            command=self._on_load_tournament,
        )
        self.export_button = ctk.CTkButton(
            self.actions_frame,
            text="Export",
            command=self._on_export_tournament,
        )
        self.start_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Start tournament",
            command=self._on_start_tournament,
        )
        self.stop_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Stop tournament",
            command=self._on_stop_tournament,
        )
        self.match_action_button = ctk.CTkButton(
            self.actions_frame,
            text="Start match",
            command=self._on_match_action_button,
        )
        self.start_round_button = ctk.CTkButton(
            self.actions_frame,
            text="Start round",
            command=self._on_start_round,
        )
        self.stop_round_button = ctk.CTkButton(
            self.actions_frame,
            text="Stop round",
            command=self._on_stop_round,
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
            command=self._on_create_tournament,
        )
        self.create_player_button = ctk.CTkButton(
            self.actions_frame,
            text="Create player",
            command=self._on_create_player,
        )
        self.add_player_to_tournament_button = ctk.CTkButton(
            self.actions_frame,
            text="Add player to tournament",
            command=self._on_add_player_to_tournament,
        )
        self.create_tournament_button.grid(
            row=1, column=0, columnspan=3, padx=4, pady=(6, 2), sticky="ew"
        )
        self.create_player_button.grid(
            row=1, column=3, columnspan=2, padx=4, pady=(6, 2), sticky="ew"
        )
        self.add_player_to_tournament_button.grid(
            row=1, column=5, columnspan=3, padx=4, pady=(6, 2), sticky="ew"
        )

    def _refresh_action_buttons_visibility(self):
        self._sync_round_status_colors()
        tournament_status = ""
        if self.current_tournament is not None:
            tournament_status = str(getattr(self.current_tournament, "status", "")).lower()

        selected_round_status = self._get_selected_round_status()
        active_round_status = self._get_active_round_status()
        match_status = self._get_selected_match_status()
        tournament_is_ongoing = tournament_status == "ongoing"
        selected_round_index = self._selected_round_index

        selected_round_matches_finished = False
        if selected_round_index is not None:
            selected_round_matches_finished = self._are_all_matches_finished_in_round(
                selected_round_index
            )
        previous_rounds_finished = self._are_previous_rounds_finished(selected_round_index)
        all_rounds_finished = self._are_all_rounds_finished()

        self._set_button_enabled(
            self.start_tournament_button, tournament_status == "preparation"
        )
        self._set_button_enabled(
            self.stop_tournament_button,
            tournament_is_ongoing and all_rounds_finished,
        )

        self._set_match_action_button(
            match_status=match_status,
            can_change_match=tournament_is_ongoing and active_round_status == "ongoing",
        )
        self._set_button_enabled(
            self.start_round_button,
            tournament_is_ongoing
            and selected_round_status == "not_started"
            and previous_rounds_finished,
        )
        self._set_button_enabled(
            self.stop_round_button,
            tournament_is_ongoing
            and selected_round_status == "ongoing"
            and selected_round_matches_finished,
        )

    @staticmethod
    def _set_button_visibility(button, should_show):
        if should_show:
            button.grid()
        else:
            button.grid_remove()

    @staticmethod
    def _set_button_enabled(button, enabled):
        button.configure(state=("normal" if enabled else "disabled"))

    def _set_match_action_button(self, match_status, can_change_match: bool):
        if match_status == "not_started":
            self.match_action_button.configure(
                text="Start match", command=self._on_start_match
            )
            self._set_button_visibility(self.match_action_button, True)
            self._set_button_enabled(self.match_action_button, can_change_match)
            return

        if match_status == "ongoing":
            self.match_action_button.configure(
                text="End match", command=self._on_end_match
            )
            self._set_button_visibility(self.match_action_button, True)
            self._set_button_enabled(self.match_action_button, can_change_match)
            return

        self._set_button_visibility(self.match_action_button, False)

    def _initialize_runtime_statuses(self, tournament: Tournament):
        self._selected_round_index = None
        self._selected_match_index = None
        self._round_statuses = []

        for round_ in tournament.rounds:
            round_status = self._infer_round_status(round_)
            self._round_statuses.append(round_status)
            if round_status == "finished":
                default_match_status = "finished"
            else:
                default_match_status = "not_started"

            for match in round_.matches:
                normalized_match_status = str(getattr(match, "status", "")).strip().lower()
                if normalized_match_status not in {"not_started", "ongoing", "finished"}:
                    normalized_match_status = default_match_status
                match.status = normalized_match_status

    @staticmethod
    def _infer_round_status(round_):
        now = datetime.now()
        if isinstance(round_.end_date, datetime) and now > round_.end_date:
            return "finished"
        if isinstance(round_.start_date, datetime) and now < round_.start_date:
            return "not_started"
        return "ongoing"

    def _get_selected_round_status(self):
        if self._selected_round_index is None:
            return None
        if 0 <= self._selected_round_index < len(self._round_statuses):
            return self._round_statuses[self._selected_round_index]
        return None

    def _get_selected_match_status(self):
        if self._selected_match_index is None:
            return None
        match = self.match_controller.get_match_by_index(self._selected_match_index)
        if match is None:
            return None
        return str(getattr(match, "status", "")).strip().lower()

    def _get_active_round_status(self):
        active_round_index = self._get_active_round_index()
        if active_round_index is None:
            return None
        if 0 <= active_round_index < len(self._round_statuses):
            return self._round_statuses[active_round_index]
        return None

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
        print("Save tournament clicked")

    def _on_load_tournament(self):
        print("Load tournament clicked")

    def _on_export_tournament(self):
        print("Export tournament clicked")

    def _on_create_tournament(self):
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

        selected_path = filedialog.askopenfilename(
            title="Select player JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(self.players_controller.players_directory),
        )
        if not selected_path:
            return

        path_obj = Path(selected_path)
        success, message = self.tournament_controller.add_player_to_tournament(
            self.current_tournament,
            player_file_name=path_obj.name,
            player_file_path=str(path_obj),
        )
        if success:
            messagebox.showinfo("Player", message)
        else:
            messagebox.showerror("Player", message)

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
        success, message, tournament = self.tournament_controller.create_and_save_tournament(
            tournament_data
        )
        if not success:
            return False, message

        self.current_tournament = tournament
        self.tournament_controller.populate_view(self.current_tournament)
        self._initialize_runtime_statuses(self.current_tournament)
        self._active_round_index_for_matches = None
        self._selected_round_index = None
        self._selected_match_index = None
        self.player_1_controller.select_player(None)
        self.player_2_controller.select_player(None)
        self._refresh_action_buttons_visibility()
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
        if self.current_tournament is None:
            return
        if str(getattr(self.current_tournament, "status", "")).strip().lower() != "preparation":
            return
        self.current_tournament.status = "Ongoing"
        self.tournament_controller.populate_view(
            self.current_tournament,
            populate_rounds=False,
            populate_matches_from_current_round=False,
        )
        self._refresh_action_buttons_visibility()

    def _on_stop_tournament(self):
        if self.current_tournament is None:
            return

        tournament_status = str(getattr(self.current_tournament, "status", "")).strip().lower()
        if tournament_status != "ongoing":
            return
        if not self._are_all_rounds_finished():
            return

        self.current_tournament.status = "Completed"
        self.tournament_controller.populate_view(
            self.current_tournament,
            populate_rounds=False,
            populate_matches_from_current_round=False,
        )
        self._refresh_action_buttons_visibility()

    def _on_start_round(self):
        if self._selected_round_index is None:
            return
        tournament_status = str(getattr(self.current_tournament, "status", "")).strip().lower()
        if tournament_status != "ongoing":
            return
        if self._get_selected_round_status() != "not_started":
            return
        if not self._are_previous_rounds_finished(self._selected_round_index):
            return
        if 0 <= self._selected_round_index < len(self._round_statuses):
            self._round_statuses[self._selected_round_index] = "ongoing"
        self._refresh_action_buttons_visibility()

    def _on_stop_round(self):
        if self._selected_round_index is None:
            return
        tournament_status = str(getattr(self.current_tournament, "status", "")).strip().lower()
        if tournament_status != "ongoing":
            return
        if self._get_selected_round_status() != "ongoing":
            return
        if not self._are_all_matches_finished_in_round(self._selected_round_index):
            return
        if 0 <= self._selected_round_index < len(self._round_statuses):
            self._round_statuses[self._selected_round_index] = "finished"
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
        tournament_status = str(getattr(self.current_tournament, "status", "")).strip().lower()
        if tournament_status != "ongoing":
            return
        if self._get_active_round_status() != "ongoing":
            return

        started = self.match_controller.start_match(self._selected_match_index)
        if not started:
            return

        active_round_index = self._get_active_round_index()
        if active_round_index is not None and 0 <= active_round_index < len(self._round_statuses):
            self._round_statuses[active_round_index] = "ongoing"
        self._refresh_tournament_status_from_matches()
        if self.current_tournament is not None:
            self.tournament_controller.populate_view(
                self.current_tournament,
                populate_rounds=False,
                populate_matches_from_current_round=False,
            )
        self._refresh_action_buttons_visibility()

    def _on_end_match(self):
        if self._selected_match_index is None:
            return
        tournament_status = str(getattr(self.current_tournament, "status", "")).strip().lower()
        if tournament_status != "ongoing":
            return
        if self._get_active_round_status() != "ongoing":
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
            command=lambda: self._finalize_match_result("player1"),
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            buttons_container,
            text="Tie",
            command=lambda: self._finalize_match_result("tie"),
        ).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(
            buttons_container,
            text=player_2_name,
            command=lambda: self._finalize_match_result("player2"),
        ).grid(row=0, column=2, padx=(6, 0), sticky="ew")

        self.match_result_popup.bind("<Escape>", lambda _event: self._close_match_result_popup())

    def _finalize_match_result(self, result: str):
        if self._selected_match_index is None:
            self._close_match_result_popup()
            return

        active_round_index = self._get_active_round_index()
        selected_round = self.round_controller.get_round_by_index(active_round_index)

        finished = self.match_controller.finish_match(
            self._selected_match_index,
            result,
            round_=selected_round,
            tournament=self.current_tournament,
        )
        self._close_match_result_popup()
        if not finished:
            return

        self._refresh_round_status_from_matches()
        self._refresh_tournament_status_from_matches()

        if selected_round is not None:
            selected_index = self._selected_match_index
            self.match_controller.populate_from_round(selected_round)
            self.matches_panel.select_match(selected_index)

        if self.current_tournament is not None:
            self.left_panel.set_players(self.current_tournament.players)
            self.tournament_controller.populate_view(
                self.current_tournament,
                populate_rounds=False,
                populate_matches_from_current_round=False,
            )

        self._refresh_action_buttons_visibility()

    def _refresh_round_status_from_matches(self):
        active_round_index = self._get_active_round_index()
        if active_round_index is None:
            return
        selected_round = self.round_controller.get_round_by_index(active_round_index)
        if selected_round is None:
            return

        match_statuses = [match.status for match in selected_round.matches]
        if match_statuses and all(status == "finished" for status in match_statuses):
            self._round_statuses[active_round_index] = "finished"
        elif any(status == "ongoing" for status in match_statuses):
            self._round_statuses[active_round_index] = "ongoing"

    def _refresh_tournament_status_from_matches(self):
        if self.current_tournament is None:
            return

        all_matches = [
            match for round_ in self.current_tournament.rounds for match in round_.matches
        ]
        if not all_matches:
            return

        if any(match.status in {"ongoing", "finished"} for match in all_matches):
            self.current_tournament.status = "Ongoing"
        else:
            self.current_tournament.status = "Preparation"

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
        for index, round_status in enumerate(self._round_statuses):
            self.round_controller.update_round_status(index, round_status)

    def _are_all_matches_finished_in_round(self, round_index):
        selected_round = self.round_controller.get_round_by_index(round_index)
        if selected_round is None:
            return False
        if not selected_round.matches:
            return False
        return all(match.status == "finished" for match in selected_round.matches)

    def _are_previous_rounds_finished(self, round_index):
        if round_index is None:
            return False
        if round_index <= 0:
            return True

        for index in range(0, round_index):
            if not (0 <= index < len(self._round_statuses)):
                return False
            if self._round_statuses[index] != "finished":
                return False
        return True

    def _are_all_rounds_finished(self):
        if not self._round_statuses:
            return False
        return all(round_status == "finished" for round_status in self._round_statuses)

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
