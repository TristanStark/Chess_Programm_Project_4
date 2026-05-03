from datetime import datetime
from pathlib import Path

from src.controllers.settings import debug_print
from src.controllers.tournament_pairing_service import TournamentPairingService
from src.controllers.tournament_persistence_service import TournamentPersistenceService
from src.models.matches import Match
from src.models.players import Player
from src.models.tournaments import Tournament


class TournamentController:
    """Controller orchestrating tournament domain services for the UI layer."""

    def __init__(
        self,
        tournament_view=None,
        round_controller=None,
        match_controller=None,
        tournaments_directory: Path | None = None,
    ):
        self.tournaments_directory = tournaments_directory or Path("data") / "tournaments"
        self.persistence_service = TournamentPersistenceService(self.tournaments_directory)
        self.pairing_service = TournamentPairingService()

    def build_view_data(self, tournament: Tournament) -> dict:
        self._sync_players_total_points(tournament)
        current_round_number = self._current_round_number(tournament)
        return {
            "name": tournament.name,
            "venue": tournament.venue,
            "players": tournament.players,
            "description": tournament.description,
            "infos": {
                "status": tournament.status,
                "start_date": self._format_datetime(tournament.start_date),
                "end_date": self._format_datetime(tournament.end_date),
                "number_of_rounds": tournament.number_of_rounds,
                "current_round": f"{current_round_number}/{tournament.number_of_rounds}",
            },
        }

    def initialize_runtime_state(self, tournament: Tournament) -> None:
        for round_ in tournament.rounds:
            normalized_round_status = self._normalize_status(getattr(round_, "status", ""))
            if normalized_round_status == "not_started" and not getattr(round_, "status", ""):
                normalized_round_status = self._infer_round_status(round_)
            round_.status = normalized_round_status

            default_match_status = "finished" if round_.status == "finished" else "not_started"
            for match in round_.matches:
                normalized_match_status = self._normalize_status(getattr(match, "status", ""))
                if normalized_match_status == "not_started" and not getattr(match, "status", ""):
                    normalized_match_status = default_match_status
                match.status = normalized_match_status
        self.pairing_service.initialize_pairing_generator(tournament)

    def can_create_tournament(
        self,
        current_tournament: Tournament | None,
    ) -> tuple[bool, str]:
        return True, ""

    def add_player_to_tournament(
        self,
        tournament: Tournament,
        player_file_name: str,
        player_file_path: str,
    ):
        if tournament is None:
            return False, "No active tournament."
        if self.is_tournament_ongoing(tournament):
            return False, "Cannot add a player while tournament is ongoing."

        file_path = Path(player_file_path)
        if not file_path.exists():
            return False, f"Player file not found: {player_file_name}"
        if file_path.suffix.lower() != ".json":
            return False, "Selected file is not a JSON file."

        try:
            player = Player.load(file_path)
        except Exception as exc:
            return False, f"Failed to load player file '{player_file_name}': {exc}"

        for existing_player in tournament.players:
            if existing_player.national_chess_identifier == player.national_chess_identifier:
                return False, "This player is already in the tournament."

        tournament.players.append(player)
        self._sync_players_total_points(tournament)
        return True, f"Player '{player.first_name} {player.last_name}' added."

    def remove_player_from_tournament(
        self,
        tournament: Tournament | None,
        player: Player | None,
    ) -> tuple[bool, str]:
        if tournament is None:
            return False, "No active tournament."
        if self.is_tournament_ongoing(tournament):
            return False, "Cannot remove a player while tournament is ongoing."
        if not tournament.players:
            return False, "No player in the tournament."
        if player is None:
            return False, "No player selected."

        ncid = player.national_chess_identifier
        updated_players = [
            existing_player
            for existing_player in tournament.players
            if existing_player.national_chess_identifier != ncid
        ]
        if len(updated_players) == len(tournament.players):
            return False, "Selected player is not in the tournament."

        tournament.players = updated_players
        self._sync_players_total_points(tournament)
        return True, f"Player '{player.first_name} {player.last_name}' removed."

    def create_and_save_tournament(
        self,
        tournament_data: dict,
        current_tournament: Tournament | None = None,
    ):
        can_create, create_message = self.can_create_tournament(current_tournament)
        if not can_create:
            return False, create_message, None, None

        success, message, tournament = self.persistence_service.create_tournament_from_form_data(
            tournament_data
        )
        if not success:
            return False, message, None, None

        file_stem = self.persistence_service.build_tournament_filename(tournament)
        file_stem = self.persistence_service.next_available_tournament_filename(file_stem)
        file_path = self.tournaments_directory / f"{file_stem}.json"
        self.persistence_service.save_tournament_to_json(tournament, file_path)

        return True, f"Tournament saved in '{file_path.name}'.", tournament, file_path

    def save_tournament_to_json(
        self,
        tournament: Tournament | None,
        file_path: Path | str | None,
    ) -> tuple[bool, str, Path | None]:
        if tournament is None:
            return False, "No active tournament.", None
        if file_path is None:
            return False, "No destination file selected.", None

        resolved_path = Path(file_path)
        if resolved_path.suffix.lower() != ".json":
            resolved_path = resolved_path.with_suffix(".json")

        try:
            self.persistence_service.save_tournament_to_json(tournament, resolved_path)
        except Exception as exc:
            return False, f"Failed to save tournament: {exc}", None

        return True, f"Tournament saved in '{resolved_path.name}'.", resolved_path

    def load_tournament_from_json(
        self,
        file_path: Path | str,
    ) -> tuple[bool, str, Tournament | None]:
        resolved_path = Path(file_path)
        if not resolved_path.exists():
            return False, f"Tournament file not found: {resolved_path}", None
        if resolved_path.suffix.lower() != ".json":
            return False, "Selected file is not a JSON file.", None

        try:
            tournament = self.persistence_service.load_tournament_from_json(resolved_path)
            self.initialize_runtime_state(tournament)
        except Exception as exc:
            return False, f"Failed to load tournament: {exc}", None

        return True, "", tournament

    def can_start_tournament(self, tournament: Tournament | None) -> tuple[bool, str]:
        if tournament is None:
            return False, "No active tournament."

        tournament_status = str(getattr(tournament, "status", "")).strip().lower()
        if tournament_status != "preparation":
            return False, "Tournament must be in Preparation status."

        players_count = len(tournament.players)
        if players_count == 0:
            return False, "Tournament must have players before starting."
        if players_count % 2 != 0:
            return False, "Number of players must be even."

        expected_players_count = 2 ** int(tournament.number_of_rounds)
        if players_count != expected_players_count:
            return (
                False,
                f"Number of players must be exactly 2^number_of_rounds ({expected_players_count}).",
            )

        return True, ""

    def start_tournament(self, tournament: Tournament | None) -> tuple[bool, str]:
        can_start, message = self.can_start_tournament(tournament)
        if not can_start:
            return False, message

        try:
            tournament.rounds = []
            self.pairing_service.initialize_pairing_generator(tournament)
            if self.uses_automatic_pairings(tournament):
                self.pairing_service.generate_next_round_if_possible(tournament)
        except Exception as exc:
            return False, f"Failed to generate rounds: {exc}"

        tournament.status = "Ongoing"
        return True, ""

    def can_stop_tournament(self, tournament: Tournament | None) -> tuple[bool, str]:
        if tournament is None:
            return False, "No active tournament."
        if not self.is_tournament_ongoing(tournament):
            return False, "Tournament must be ongoing."
        if not self.are_all_rounds_finished(tournament):
            return False, "All rounds must be finished first."
        return True, ""

    def stop_tournament(self, tournament: Tournament | None) -> tuple[bool, str]:
        can_stop, message = self.can_stop_tournament(tournament)
        if not can_stop:
            return False, message
        tournament.status = "Completed"
        return True, ""

    def update_pairing_generator_after_match(
        self,
        tournament: Tournament | None,
        match: Match | None,
        result: str,
    ) -> None:
        self.pairing_service.update_pairing_generator_after_match(tournament, match, result)

    def sync_round_status_from_matches(
        self,
        tournament: Tournament | None,
        round_index: int | None,
    ) -> None:
        round_ = self._get_round_by_index(tournament, round_index)
        if round_ is None or not round_.matches:
            return

        debug_print("Syncing round status from matches...")
        debug_print(f"Round '{round_.name}' has {len(round_.matches)} matches.")
        debug_print("Match statuses:")
        for match in round_.matches:
            debug_print(f"  - {match.player1.player} vs {match.player2.player}: {match.status}")
        statuses = [match.status for match in round_.matches]
        if all(status == "finished" for status in statuses):
            round_.status = "finished"
            if self.uses_automatic_pairings(tournament):
                self.pairing_service.generate_next_round_if_possible(tournament)
        elif all(status == "not_started" for status in statuses):
            round_.status = "not_started"
        else:
            round_.status = "ongoing"
        self.update_tournament_status_from_matches(tournament)

    def update_tournament_status_from_matches(self, tournament: Tournament | None) -> None:
        if tournament is None:
            return

        if str(getattr(tournament, "status", "")).strip().lower() == "completed":
            return

        if self.are_all_rounds_finished(tournament):
            tournament.status = "Completed"
            return

        has_any_started_round = any(round_.status in {"ongoing", "finished"} for round_ in tournament.rounds)
        has_any_started_match = any(
            match.status in {"ongoing", "finished"}
            for round_ in tournament.rounds
            for match in round_.matches
        )

        if has_any_started_round or has_any_started_match:
            tournament.status = "Ongoing"
        else:
            tournament.status = "Preparation"

    def are_all_rounds_finished(self, tournament: Tournament | None) -> bool:
        if tournament is None:
            return False
        if not tournament.rounds:
            return False
        total_rounds = int(getattr(tournament, "number_of_rounds", 0) or 0)
        if total_rounds <= 0:
            return False
        if len(tournament.rounds) < total_rounds:
            return False
        return all(round_.status == "finished" for round_ in tournament.rounds)

    @staticmethod
    def is_tournament_ongoing(tournament: Tournament | None) -> bool:
        if tournament is None:
            return False
        return str(getattr(tournament, "status", "")).strip().lower() == "ongoing"

    def uses_automatic_pairings(self, tournament: Tournament | None) -> bool:
        return self.pairing_service.uses_automatic_pairings(tournament)

    def generate_next_round_if_possible(self, tournament: Tournament | None) -> bool:
        return self.pairing_service.generate_next_round_if_possible(tournament)

    def refresh_player_points(self, tournament: Tournament | None) -> None:
        if tournament is None:
            return
        self._sync_players_total_points(tournament)

    def compute_player_total_points(
        self,
        tournament: Tournament | None,
        player: Player | None,
    ) -> float:
        if tournament is None or player is None:
            return 0.0
        totals = self._compute_total_points_by_player(tournament)
        return float(totals.get(player.national_chess_identifier, 0.0))

    def create_manual_round(
        self,
        tournament: Tournament | None,
        *,
        round_name: str,
        pairings: list[tuple[str, str]],
    ) -> tuple[bool, str]:
        if tournament is None:
            return False, "No active tournament."
        if not self.is_tournament_ongoing(tournament):
            return False, "Tournament must be ongoing."
        return self.pairing_service.create_manual_round(
            tournament,
            round_name=round_name,
            pairings=pairings,
        )

    def rename_round(
        self,
        tournament: Tournament | None,
        round_index: int | None,
        new_name: str,
    ) -> tuple[bool, str]:
        round_ = self._get_round_by_index(tournament, round_index)
        if round_ is None:
            return False, "No round selected."
        normalized_name = str(new_name).strip()
        if not normalized_name:
            return False, "Round name is required."
        round_.name = normalized_name
        return True, ""

    @staticmethod
    def _current_round_number(tournament: Tournament) -> int:
        if not tournament.rounds:
            return 0
        normalized_statuses = [
            str(getattr(round_, "status", "")).strip().lower()
            for round_ in tournament.rounds
        ]

        for index, status in enumerate(normalized_statuses, start=1):
            if status == "ongoing":
                return index

        for index, status in enumerate(normalized_statuses, start=1):
            if status == "not_started":
                return index

        finished_rounds_count = sum(1 for status in normalized_statuses if status == "finished")
        if finished_rounds_count <= 0:
            return 0

        total_rounds = int(getattr(tournament, "number_of_rounds", 0) or 0)
        if total_rounds <= 0:
            return finished_rounds_count + 1
        return min(finished_rounds_count + 1, total_rounds)

    @staticmethod
    def _infer_round_status(round_) -> str:
        now = datetime.now()
        if isinstance(round_.end_date, datetime) and now > round_.end_date:
            return "finished"
        if isinstance(round_.start_date, datetime) and now < round_.start_date:
            return "not_started"
        return "ongoing"

    @staticmethod
    def _normalize_status(status: str) -> str:
        normalized = str(status).strip().lower()
        if normalized not in {"not_started", "ongoing", "finished"}:
            return "not_started"
        return normalized

    @staticmethod
    def _get_round_by_index(tournament: Tournament | None, round_index: int | None):
        if tournament is None or round_index is None:
            return None
        if not 0 <= round_index < len(tournament.rounds):
            return None
        return tournament.rounds[round_index]

    @staticmethod
    def _format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        return str(value)

    @staticmethod
    def _compute_total_points_by_player(tournament: Tournament) -> dict[str, float]:
        totals = {player.national_chess_identifier: 0.0 for player in tournament.players}
        for round_ in tournament.rounds:
            for match in round_.matches:
                player_1_ncid = match.player1.player.national_chess_identifier
                player_2_ncid = match.player2.player.national_chess_identifier
                totals[player_1_ncid] = totals.get(player_1_ncid, 0.0) + float(match.player1.score)
                totals[player_2_ncid] = totals.get(player_2_ncid, 0.0) + float(match.player2.score)
        return totals

    def _sync_players_total_points(self, tournament: Tournament) -> None:
        totals = self._compute_total_points_by_player(tournament)
        for player in tournament.players:
            player.total_points = float(totals.get(player.national_chess_identifier, 0.0))
