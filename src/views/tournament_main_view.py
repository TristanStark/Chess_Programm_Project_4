import customtkinter as ctk
from pathlib import Path
from tkinter import Menu, filedialog, messagebox
from src.controllers.match_controller import MatchController
from src.controllers.player_controller import PlayerController
from src.controllers.players_controller import PlayersController
from src.controllers.round_controller import RoundController
from src.controllers.tournament_controller import TournamentController
from src.models.tournaments import Tournament
from src.controllers.settings import debug_print, is_debug, toggle_debug
from src.views.player_info_card_view import PlayerInfoCard
from src.views.create_player_popup_view import CreatePlayerPopup
from src.views.tournament_view import TournamentInfoPanel
from src.views.create_tournament_popup_view import CreateTournamentPopup
from src.views.create_round_popup_view import CreateRoundPopup
from src.views.rename_round_popup_view import RenameRoundPopup
from src.views.rounds_view import TournamentRoundsPanel
from src.views.matches_view import TournamentMatchesPanel
from src.views.export_report_popup_view import ExportReportPopup
from src.views.tournament_match_actions_mixin import TournamentMatchActionsMixin
from src.views.tournament_view_helpers import (
    build_player_filename,
    format_player_option_label,
    next_available_player_filename,
)
from src.exporters.tournament_report_exporter import TournamentReportExporter, ReportOption

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class TournamentView(TournamentMatchActionsMixin, ctk.CTkFrame):
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
        self.create_round_popup = None
        self.rename_round_popup = None
        self.match_result_popup = None
        self.export_report_popup = None
        self._menu_items = {}

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
            tournaments_directory=Path("data") / "tournaments",
        )
        self.report_exporter = TournamentReportExporter(
            players_controller=self.players_controller,
            tournament_controller=self.tournament_controller,
            templates_directory=Path("report_templates"),
            exports_directory=Path("exports"),
        )
        self._build_menu_bar()
        self._refresh_action_buttons_visibility()

    def _build_menu_bar(self):
        root = self.winfo_toplevel()
        self.menu_bar = Menu(root)
        self.tournaments_menu = Menu(self.menu_bar, tearoff=0)
        self.round_menu = Menu(self.menu_bar, tearoff=0)
        self.match_menu = Menu(self.menu_bar, tearoff=0)
        self.settings_menu = Menu(self.menu_bar, tearoff=0)

        self.menu_bar.add_cascade(label="Tournaments", menu=self.tournaments_menu)
        self.menu_bar.add_cascade(label="Round", menu=self.round_menu)
        self.menu_bar.add_cascade(label="Match", menu=self.match_menu)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)

        self._add_menu_item(
            self.tournaments_menu,
            key="create_tournament",
            label="Create tournament",
            command=lambda: self._run_action_with_autosave(self._on_create_tournament),
        )
        self._add_menu_item(
            self.tournaments_menu,
            key="save_tournament",
            label="Save tournament",
            command=lambda: self._run_action_with_autosave(self._on_save_tournament),
        )
        self._add_menu_item(
            self.tournaments_menu,
            key="load_tournament",
            label="Load tournament",
            command=lambda: self._run_action_with_autosave(self._on_load_tournament),
        )
        self._add_menu_item(
            self.tournaments_menu,
            key="export_tournament",
            label="Export",
            command=lambda: self._run_action_with_autosave(self._on_export_tournament),
        )
        self.tournaments_menu.add_separator()
        self._add_menu_item(
            self.tournaments_menu,
            key="start_tournament",
            label="Start tournament",
            command=lambda: self._run_action_with_autosave(self._on_start_tournament),
        )
        self._add_menu_item(
            self.tournaments_menu,
            key="stop_tournament",
            label="Stop tournament",
            command=lambda: self._run_action_with_autosave(self._on_stop_tournament),
        )
        self.tournaments_menu.add_separator()
        self._add_menu_item(
            self.tournaments_menu,
            key="create_player",
            label="Create player",
            command=lambda: self._run_action_with_autosave(self._on_create_player),
        )
        self._add_menu_item(
            self.tournaments_menu,
            key="add_player",
            label="Add player to tournament",
            command=lambda: self._run_action_with_autosave(self._on_add_player_to_tournament),
        )
        self._add_menu_item(
            self.tournaments_menu,
            key="remove_player",
            label="Remove player from tournament",
            command=lambda: self._run_action_with_autosave(self._on_remove_player_from_tournament),
        )

        self._add_menu_item(
            self.round_menu,
            key="start_round",
            label="Start round",
            command=lambda: self._run_action_with_autosave(self._on_start_round),
        )
        self._add_menu_item(
            self.round_menu,
            key="stop_round",
            label="Stop round",
            command=lambda: self._run_action_with_autosave(self._on_stop_round),
        )
        self._add_menu_item(
            self.round_menu,
            key="rename_round",
            label="Rename selected round",
            command=lambda: self._run_action_with_autosave(self._on_rename_round),
        )

        self._add_menu_item(
            self.match_menu,
            key="match_action",
            label="Start match",
            command=lambda: self._run_action_with_autosave(self._on_match_action_button),
        )
        self._add_menu_item(
            self.settings_menu,
            key="toggle_debug",
            label="Toggle debug (OFF)",
            command=self._on_toggle_debug,
        )
        self._refresh_debug_menu_item_label()

        root.configure(menu=self.menu_bar)

        self.left_panel.players_tree.bind(
            "<<TreeviewSelect>>",
            lambda _event: self._refresh_action_buttons_visibility(),
            add="+",
        )

    def _add_menu_item(self, menu: Menu, key: str, label: str, command):
        menu.add_command(label=label, command=command)
        self._menu_items[key] = {
            "menu": menu,
            "index": menu.index("end"),
        }

    def _set_menu_item_enabled(self, key: str, enabled: bool):
        menu_item = self._menu_items[key]
        menu_item["menu"].entryconfigure(
            menu_item["index"],
            state=("normal" if enabled else "disabled"),
        )

    def _set_menu_item_label(self, key: str, label: str):
        menu_item = self._menu_items[key]
        menu_item["menu"].entryconfigure(menu_item["index"], label=label)

    def _refresh_debug_menu_item_label(self):
        debug_state = "ON" if is_debug() else "OFF"
        self._set_menu_item_label("toggle_debug", f"Toggle debug ({debug_state})")

    def _on_toggle_debug(self):
        debug_enabled = toggle_debug()
        self._refresh_debug_menu_item_label()
        debug_print(f"Debug mode is now {'ON' if debug_enabled else 'OFF'}")

    def _set_match_action_menu_item(
        self,
        match_status,
        can_change_match: bool,
    ):
        if match_status == "not_started":
            self._set_menu_item_label("match_action", "Start match")
            self._set_menu_item_enabled("match_action", can_change_match)
            return

        if match_status == "ongoing":
            self._set_menu_item_label("match_action", "End match")
            self._set_menu_item_enabled("match_action", can_change_match)
            return

        self._set_menu_item_label("match_action", "Match action unavailable")
        self._set_menu_item_enabled("match_action", False)

    def _refresh_action_buttons_visibility(self):
        self._sync_round_status_colors()
        has_active_tournament = self.current_tournament is not None
        selected_round_index = self._selected_round_index
        active_round_index = self._get_active_round_index()
        match_status = self._get_selected_match_status()

        can_start_tournament, _ = self.tournament_controller.can_start_tournament(
            self.current_tournament
        )
        can_stop_tournament, _ = self.tournament_controller.can_stop_tournament(
            self.current_tournament
        )
        can_start_round, _ = self.round_controller.can_start_round(
            self.current_tournament,
            selected_round_index,
        )
        can_stop_round, _ = self.round_controller.can_stop_round(
            self.current_tournament,
            selected_round_index,
        )
        can_change_match, _ = self.match_controller.can_change_match(
            self.current_tournament,
            active_round_index,
        )
        can_create_tournament, _ = self.tournament_controller.can_create_tournament(
            self.current_tournament
        )
        can_create_player, _ = self.players_controller.can_create_player(
            self.current_tournament
        )
        can_add_player, _ = self.players_controller.can_add_player_to_tournament(
            self.current_tournament
        )
        can_remove_player, _ = self.players_controller.can_remove_player_from_tournament(
            self.current_tournament,
            self._get_selected_tournament_player(),
        )
        can_rename_round = (
            self.current_tournament is not None
            and self._selected_round_index is not None
            and self.round_controller.get_round_by_index(self._selected_round_index) is not None
        )

        self._set_menu_item_enabled("start_tournament", can_start_tournament)
        self._set_menu_item_enabled("stop_tournament", can_stop_tournament)

        self._set_match_action_menu_item(
            match_status=match_status,
            can_change_match=can_change_match,
        )
        self._set_menu_item_enabled("start_round", can_start_round)
        self._set_menu_item_enabled("stop_round", can_stop_round)
        self._set_menu_item_enabled("rename_round", can_rename_round)
        self._set_menu_item_enabled("create_tournament", can_create_tournament)
        self._set_menu_item_enabled("create_player", can_create_player)
        self._set_menu_item_enabled("add_player", has_active_tournament and can_add_player)
        self._set_menu_item_enabled("remove_player", has_active_tournament and can_remove_player)

    def _render_tournament(
        self,
        tournament: Tournament,
        *,
        populate_rounds: bool = True,
        populate_matches_from_current_round: bool = True,
    ) -> None:
        view_data = self.tournament_controller.build_view_data(tournament)
        self.tournament_name_label.configure(text=view_data["name"])
        self.tournament_venue_label.configure(text=view_data["venue"])
        self.left_panel.set_tournament_infos(**view_data["infos"])
        self.left_panel.set_players(view_data["players"])
        self.left_panel.set_description(view_data["description"])

        if populate_rounds:
            self.round_controller.populate_from_tournament(tournament)

        if populate_matches_from_current_round:
            if tournament.rounds:
                self.match_controller.populate_from_round(tournament.rounds[-1])
            else:
                self.match_controller.populate_view([])

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
        self._render_tournament(self.current_tournament)
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
        selected_indices = self.matches_panel.get_selected_match_indices()
        if not selected_indices:
            if self._selected_match_index is None:
                return None
            selected_indices = [self._selected_match_index]

        statuses = []
        for index in selected_indices:
            match = self.match_controller.get_match_by_index(index)
            if match is None:
                continue
            statuses.append(str(getattr(match, "status", "")).strip().lower())

        if not statuses:
            return None
        unique_statuses = set(statuses)
        if len(unique_statuses) == 1:
            return statuses[0]
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
            self.player_1_controller.select_player(
                selected_match.player1.player,
                total_points=self.tournament_controller.compute_player_total_points(
                    self.current_tournament,
                    selected_match.player1.player,
                ),
            )
            self.player_2_controller.select_player(
                selected_match.player2.player,
                total_points=self.tournament_controller.compute_player_total_points(
                    self.current_tournament,
                    selected_match.player2.player,
                ),
            )
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
        if self.export_report_popup is not None and self.export_report_popup.winfo_exists():
            self.export_report_popup.lift()
            self.export_report_popup.focus_force()
            return

        self.export_report_popup = ExportReportPopup(
            self.winfo_toplevel(),
            report_options=self.report_exporter.get_report_options(),
            on_export_callback=self._export_selected_report,
        )

    def _export_selected_report(self, report_option: ReportOption) -> tuple[bool, str]:
        selected_tournament = self.current_tournament
        if report_option.requires_tournament and selected_tournament is None:
            selected_path = filedialog.askopenfilename(
                title="Select tournament JSON file to export",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=str(self.tournament_controller.tournaments_directory),
            )
            if not selected_path:
                return (
                    False,
                    "Please select a tournament file for this report.",
                )

            success, message, selected_tournament = self.tournament_controller.load_tournament_from_json(
                Path(selected_path)
            )
            if not success:
                return False, message

        default_output_path = self.report_exporter.build_default_output_path(
            report_option,
            selected_tournament=selected_tournament,
        )
        destination_path = filedialog.asksaveasfilename(
            title="Save HTML report",
            defaultextension=".html",
            initialfile=default_output_path.name,
            initialdir=str(default_output_path.parent),
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
        )
        if not destination_path:
            return False, "Export cancelled."

        success, message, exported_path = self.report_exporter.export_report(
            report_option=report_option,
            output_path=Path(destination_path),
            selected_tournament=selected_tournament,
        )
        if not success:
            return False, message

        if exported_path is not None:
            messagebox.showinfo("Export", f"Report exported to:\n{exported_path}")
        return True, message

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

        self._render_tournament(
            self.current_tournament,
            populate_rounds=False,
            populate_matches_from_current_round=False,
        )
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

        self._render_tournament(
            self.current_tournament,
            populate_rounds=False,
            populate_matches_from_current_round=False,
        )
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

        base_filename = build_player_filename(
            player.first_name,
            player.last_name,
            player.national_chess_identifier,
        )
        filename = next_available_player_filename(
            self.players_controller.players_directory,
            base_filename,
        )
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

    def _on_start_tournament(self):
        success, message = self.tournament_controller.start_tournament(self.current_tournament)
        if not success:
            messagebox.showerror("Tournament", message)
            return

        self._selected_round_index = None
        self._selected_match_index = None
        self._active_round_index_for_matches = 0 if self.current_tournament.rounds else None
        self._render_tournament(self.current_tournament)
        if self._active_round_index_for_matches is not None:
            self.match_controller.populate_from_round(
                self.current_tournament.rounds[self._active_round_index_for_matches]
            )
            self.rounds_panel.select_round(self._active_round_index_for_matches)
        elif not self.tournament_controller.uses_automatic_pairings(self.current_tournament):
            self._prompt_manual_round_creation_if_possible()
        self.player_1_controller.select_player(None)
        self.player_2_controller.select_player(None)
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _on_stop_tournament(self):
        success, message = self.tournament_controller.stop_tournament(self.current_tournament)
        if not success:
            messagebox.showerror("Tournament", message)
            return

        self._render_tournament(
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
        on_round_finished_callback = (
            self.tournament_controller.generate_next_round_if_possible
            if self.tournament_controller.uses_automatic_pairings(self.current_tournament)
            else None
        )
        success, message = self.round_controller.stop_round(
            self.current_tournament,
            self._selected_round_index,
            on_round_finished=on_round_finished_callback,
        )
        if not success:
            messagebox.showerror("Round", message)
            return

        self._handle_round_finished()
        if self.current_tournament is not None:
            self._render_tournament(
                self.current_tournament,
                populate_rounds=True,
                populate_matches_from_current_round=False,
            )
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()

    def _sync_round_status_colors(self):
        if self.current_tournament is None:
            return
        for index, round_ in enumerate(self.current_tournament.rounds):
            self.round_controller.update_round_status(index, round_.status)

    def _handle_round_finished(self):
        if self.current_tournament is None:
            return
        if not self.current_tournament.rounds:
            return
        if self.current_tournament.rounds[-1].status != "finished":
            return

        if self.tournament_controller.uses_automatic_pairings(self.current_tournament):
            created_new_round = self.tournament_controller.generate_next_round_if_possible(
                self.current_tournament
            )
            if created_new_round:
                return

        can_stop, _ = self.tournament_controller.can_stop_tournament(self.current_tournament)
        if can_stop:
            self.tournament_controller.stop_tournament(self.current_tournament)
            return

        self._prompt_manual_round_creation_if_possible()

    def _prompt_manual_round_creation_if_possible(self):
        if self.current_tournament is None:
            return
        if self.tournament_controller.uses_automatic_pairings(self.current_tournament):
            return
        if len(self.current_tournament.rounds) >= int(self.current_tournament.number_of_rounds):
            return
        if (
            self.current_tournament.rounds
            and self.current_tournament.rounds[-1].status != "finished"
        ):
            return

        if self.create_round_popup is not None and self.create_round_popup.winfo_exists():
            self.create_round_popup.lift()
            self.create_round_popup.focus_force()
            return

        round_number = len(self.current_tournament.rounds) + 1
        self.create_round_popup = CreateRoundPopup(
            self.winfo_toplevel(),
            players=self.current_tournament.players,
            round_number=round_number,
            on_save_callback=self._save_manual_round_from_popup,
        )

    def _save_manual_round_from_popup(self, round_data):
        if self.current_tournament is None:
            return False, "No active tournament."

        players_by_label = {
            format_player_option_label(player): player.national_chess_identifier
            for player in self.current_tournament.players
        }
        resolved_pairings = []
        for pairing in round_data.get("pairings", []):
            player_1_label = pairing.get("player_1_label", "")
            player_2_label = pairing.get("player_2_label", "")
            player_1_ncid = players_by_label.get(player_1_label)
            player_2_ncid = players_by_label.get(player_2_label)
            if player_1_ncid is None or player_2_ncid is None:
                return False, "Invalid player selected in pairings."
            resolved_pairings.append((player_1_ncid, player_2_ncid))

        success, message = self.tournament_controller.create_manual_round(
            self.current_tournament,
            round_name=round_data.get("name", ""),
            pairings=resolved_pairings,
        )
        if not success:
            return False, message

        self._render_tournament(
            self.current_tournament,
            populate_rounds=True,
            populate_matches_from_current_round=False,
        )
        new_round_index = len(self.current_tournament.rounds) - 1
        self._active_round_index_for_matches = new_round_index
        self.rounds_panel.select_round(new_round_index)
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()
        return True, ""

    def _on_rename_round(self):
        if self.current_tournament is None:
            messagebox.showerror("Round", "No active tournament.")
            return
        if self._selected_round_index is None:
            messagebox.showerror("Round", "No round selected.")
            return

        selected_round = self.round_controller.get_round_by_index(self._selected_round_index)
        if selected_round is None:
            messagebox.showerror("Round", "No round selected.")
            return

        if self.rename_round_popup is not None and self.rename_round_popup.winfo_exists():
            self.rename_round_popup.lift()
            self.rename_round_popup.focus_force()
            return

        self.rename_round_popup = RenameRoundPopup(
            self.winfo_toplevel(),
            initial_name=selected_round.name,
            on_save_callback=self._save_round_rename_from_popup,
        )

    def _save_round_rename_from_popup(self, new_name: str):
        success, message = self.tournament_controller.rename_round(
            self.current_tournament,
            self._selected_round_index,
            new_name,
        )
        if not success:
            return False, message

        self._render_tournament(
            self.current_tournament,
            populate_rounds=True,
            populate_matches_from_current_round=False,
        )
        if self._selected_round_index is not None:
            self.rounds_panel.select_round(self._selected_round_index)
        self._autosave_tournament()
        self._refresh_action_buttons_visibility()
        return True, ""
