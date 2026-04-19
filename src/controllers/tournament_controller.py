from datetime import datetime
import json
from pathlib import Path
import re

from src.models.players import Player
from src.models.tournaments import Tournament


class TournamentController:
    """Controller responsible for sending Tournament model data to the full view."""

    def __init__(
        self,
        tournament_view,
        round_controller=None,
        match_controller=None,
        tournaments_directory: Path | None = None,
    ):
        self.tournament_view = tournament_view
        self.round_controller = round_controller
        self.match_controller = match_controller
        self.tournaments_directory = tournaments_directory or Path("data") / "tournaments"
        self.tournaments_directory.mkdir(parents=True, exist_ok=True)

    def populate_view(
        self,
        tournament: Tournament,
        populate_rounds: bool = True,
        populate_matches_from_current_round: bool = True,
    ) -> None:
        self.tournament_view.tournament_name_label.configure(text=tournament.name)
        self.tournament_view.tournament_venue_label.configure(text=tournament.venue)

        current_round_number = len(tournament.rounds) if tournament.rounds else 0
        self.tournament_view.left_panel.set_tournament_infos(
            status=tournament.status,
            start_date=self._format_datetime(tournament.start_date),
            end_date=self._format_datetime(tournament.end_date),
            number_of_rounds=tournament.number_of_rounds,
            current_round=f"{current_round_number}/{tournament.number_of_rounds}",
        )
        self.tournament_view.left_panel.set_players(tournament.players)
        self.tournament_view.left_panel.set_description(tournament.description)

        if populate_rounds and self.round_controller is not None:
            self.round_controller.populate_from_tournament(tournament)

        if populate_matches_from_current_round and self.match_controller is not None:
            if tournament.rounds:
                self.match_controller.populate_from_round(tournament.rounds[-1])
            else:
                self.match_controller.populate_view([])

    def add_player_to_tournament(
        self,
        tournament: Tournament,
        player_file_name: str,
        player_file_path: str,
    ):
        """Load a Player from JSON file and add it to the given tournament."""
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
            if (
                existing_player.national_chess_identifier
                == player.national_chess_identifier
            ):
                return False, "This player is already in the tournament."

        tournament.players.append(player)
        self.tournament_view.left_panel.set_players(tournament.players)
        return True, f"Player '{player.first_name} {player.last_name}' added."

    def create_and_save_tournament(self, tournament_data: dict):
        success, message, tournament = self._create_tournament_from_form_data(tournament_data)
        if not success:
            return False, message, None

        file_stem = self._build_tournament_filename(tournament)
        file_stem = self._next_available_tournament_filename(file_stem)
        file_path = self.tournaments_directory / f"{file_stem}.json"
        self._save_tournament_to_json(tournament, file_path)

        return True, f"Tournament saved in '{file_path.name}'.", tournament

    def _create_tournament_from_form_data(self, tournament_data: dict):
        name = tournament_data.get("name", "").strip()
        venue = tournament_data.get("venue", "").strip()
        start_date_raw = tournament_data.get("start_date", "").strip()
        end_date_raw = tournament_data.get("end_date", "").strip()
        number_of_rounds_raw = tournament_data.get("number_of_rounds", "").strip()
        status = tournament_data.get("status", "Preparation").strip().title()
        description = tournament_data.get("description", "").strip()

        if not name:
            return False, "Tournament name is required.", None
        if not venue:
            return False, "Tournament venue is required.", None

        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_raw, "%Y-%m-%d")
        except ValueError:
            return False, "Dates must use format YYYY-MM-DD.", None

        if end_date < start_date:
            return False, "End date must be greater than or equal to start date.", None

        try:
            number_of_rounds = int(number_of_rounds_raw)
        except ValueError:
            return False, "Number of rounds must be an integer.", None

        if number_of_rounds <= 0:
            return False, "Number of rounds must be greater than 0.", None

        if status not in {"Preparation", "Ongoing", "Completed"}:
            return False, "Status must be Preparation, Ongoing, or Completed.", None

        tournament = Tournament(
            name=name,
            venue=venue,
            start_date=start_date,
            end_date=end_date,
            description=description,
            players=[],
            rounds=[],
            number_of_rounds=number_of_rounds,
        )
        tournament.status = status
        return True, "", tournament

    def _save_tournament_to_json(self, tournament: Tournament, file_path: Path):
        payload = {
            "name": tournament.name,
            "venue": tournament.venue,
            "start_date": tournament.start_date.strftime("%Y-%m-%d"),
            "end_date": tournament.end_date.strftime("%Y-%m-%d"),
            "number_of_rounds": tournament.number_of_rounds,
            "status": tournament.status,
            "description": tournament.description,
            "players": [],
            "rounds": [],
        }
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)

    def _build_tournament_filename(self, tournament: Tournament):
        raw = f"{tournament.name}_{tournament.start_date.strftime('%Y%m%d')}"
        sanitized = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_").lower()
        return sanitized or "tournament"

    def _next_available_tournament_filename(self, base_filename):
        candidate = base_filename
        suffix = 2
        while (self.tournaments_directory / f"{candidate}.json").exists():
            candidate = f"{base_filename}_{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def _format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        return str(value)

        