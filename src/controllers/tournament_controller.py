from datetime import datetime
import json
from pathlib import Path
import re

from src.controllers.pairings_genrator import PairingGenerator
from src.models.matches import Match, Round, Score
from src.models.players import Player
from src.models.tournaments import Tournament
from src.controllers.settings import debug_print


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
        self._pairing_generators: dict[int, PairingGenerator] = {}
        self.tournaments_directory.mkdir(parents=True, exist_ok=True)

    def populate_view(
        self,
        tournament: Tournament,
        populate_rounds: bool = True,
        populate_matches_from_current_round: bool = True,
    ) -> None:
        self._sync_players_total_points(tournament)
        self.tournament_view.tournament_name_label.configure(text=tournament.name)
        self.tournament_view.tournament_venue_label.configure(text=tournament.venue)

        current_round_number = self._current_round_number(tournament)
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

    def initialize_runtime_state(self, tournament: Tournament) -> None:
        """
        Normalize statuses after creating/loading a tournament.
        Round status is inferred if missing, and match status is aligned with round state.
        """
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
        self._initialize_pairing_generator(tournament)

    def can_create_tournament(
        self, current_tournament: Tournament | None
    ) -> tuple[bool, str]:
        return True, ""

    def add_player_to_tournament(
        self,
        tournament: Tournament,
        player_file_name: str,
        player_file_path: str,
    ):
        """Load a Player from JSON file and add it to the given tournament."""
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
            if (
                existing_player.national_chess_identifier
                == player.national_chess_identifier
            ):
                return False, "This player is already in the tournament."

        tournament.players.append(player)
        self._sync_players_total_points(tournament)
        self.tournament_view.left_panel.set_players(tournament.players)
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
        self.tournament_view.left_panel.set_players(tournament.players)
        return True, f"Player '{player.first_name} {player.last_name}' removed."

    def create_and_save_tournament(
        self,
        tournament_data: dict,
        current_tournament: Tournament | None = None,
    ):
        can_create, create_message = self.can_create_tournament(current_tournament)
        if not can_create:
            return False, create_message, None, None

        success, message, tournament = self._create_tournament_from_form_data(tournament_data)
        if not success:
            return False, message, None, None

        file_stem = self._build_tournament_filename(tournament)
        file_stem = self._next_available_tournament_filename(file_stem)
        file_path = self.tournaments_directory / f"{file_stem}.json"
        self._save_tournament_to_json(tournament, file_path)

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
            self._save_tournament_to_json(tournament, resolved_path)
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
            with open(resolved_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            tournament = self._deserialize_tournament(data)
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
            self._initialize_pairing_generator(tournament)
            if self.uses_automatic_pairings(tournament):
                self._generate_next_round_if_possible(tournament)
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
        if tournament is None or match is None:
            return
        pairing_generator = self._pairing_generators.get(id(tournament))
        if pairing_generator is None:
            return
        pairing_generator.update_after_match(
            match.player1.player.national_chess_identifier,
            match.player2.player.national_chess_identifier,
            result,
        )

    def sync_round_status_from_matches(
        self,
        tournament: Tournament | None,
        round_index: int | None,
    ) -> None:
        round_ = self._get_round_by_index(tournament, round_index)
        if round_ is None:
            return
        if not round_.matches:
            return

        debug_print("Syncing round status from matches...")
        debug_print(f"Round '{round_.name}' has {len(round_.matches)} matches.")
        debug_print("Match statuses:")
        for match in round_.matches:
            debug_print(f"  - {match.player1.player} vs {match.player2.player}: {match.status}")
        statuses = [match.status for match in round_.matches]
        # We stop if all matches are finished
        if all(status == "finished" for status in statuses):
            round_.status = "finished"
            if self.uses_automatic_pairings(tournament):
                self._generate_next_round_if_possible(tournament)
        # I dunno how we can have this case but
        # if all matches are not started we set the round as not started
        elif all(status == "not_started" for status in statuses):
            round_.status = "not_started"
        # default case: ongoing
        else:
            round_.status = "ongoing"

    def update_tournament_status_from_matches(self, tournament: Tournament | None) -> None:
        if tournament is None:
            return

        if str(getattr(tournament, "status", "")).strip().lower() == "completed":
            return

        has_any_started_round = any(
            round_.status in {"ongoing", "finished"} for round_ in tournament.rounds
        )
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
        return all(round_.status == "finished" for round_ in tournament.rounds)

    @staticmethod
    def is_tournament_ongoing(tournament: Tournament | None) -> bool:
        if tournament is None:
            return False
        return str(getattr(tournament, "status", "")).strip().lower() == "ongoing"

    @staticmethod
    def uses_automatic_pairings(tournament: Tournament | None) -> bool:
        if tournament is None:
            return True
        return bool(getattr(tournament, "automatic_pairings", True))

    def _create_tournament_from_form_data(self, tournament_data: dict):
        name = tournament_data.get("name", "").strip()
        venue = tournament_data.get("venue", "").strip()
        start_date_raw = tournament_data.get("start_date", "").strip()
        end_date_raw = tournament_data.get("end_date", "").strip()
        number_of_rounds_raw = tournament_data.get("number_of_rounds", "").strip()
        status = tournament_data.get("status", "Preparation").strip().title()
        automatic_pairings = bool(tournament_data.get("automatic_pairings", True))
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
            automatic_pairings=automatic_pairings,
        )
        tournament.status = status
        return True, "", tournament

    def _save_tournament_to_json(self, tournament: Tournament, file_path: Path):
        payload = self._serialize_tournament(tournament)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)

    def _initialize_pairing_generator(self, tournament: Tournament) -> None:
        pairing_generator = PairingGenerator(tournament.players)
        pairing_generator.set_players(tournament.players)
        pairing_generator.current_round = len(tournament.rounds)
        self._pairing_generators[id(tournament)] = pairing_generator

    def _generate_next_round_if_possible(self, tournament: Tournament | None) -> bool:
        if tournament is None:
            return False
        if not self.uses_automatic_pairings(tournament):
            return False

        total_rounds = int(tournament.number_of_rounds)
        if total_rounds <= 0:
            return False
        if len(tournament.rounds) >= total_rounds:
            return False

        if tournament.rounds and tournament.rounds[-1].status != "finished":
            return False

        pairing_generator = self._pairing_generators.get(id(tournament))
        if pairing_generator is None:
            pairing_generator = PairingGenerator(tournament.players)
            self._pairing_generators[id(tournament)] = pairing_generator

        pairing_generator.set_players(tournament.players)
        next_round_number = len(tournament.rounds) + 1
        pairings = pairing_generator.generate_pairings(number_of_round=next_round_number)
        players_by_ncid: dict[str, Player] = {
            player.national_chess_identifier: player for player in tournament.players
        }

        matches: list[Match] = []
        for player_1_ncid, player_2_ncid in pairings:
            player_1 = players_by_ncid.get(player_1_ncid)
            player_2 = players_by_ncid.get(player_2_ncid)
            if player_1 is None or player_2 is None:
                raise ValueError("Generated pairing includes unknown player.")
            matches.append(
                Match(
                    player1=Score(player=player_1, score=0.0),
                    player2=Score(player=player_2, score=0.0),
                    status="not_started",
                )
            )

        tournament.rounds.append(
            Round(
                name=f"Round {next_round_number}",
                matches=matches,
                start_date=tournament.start_date,
                end_date=tournament.end_date,
                status="not_started",
            )
        )
        return True

    def generate_next_round_if_possible(self, tournament: Tournament | None) -> bool:
        return self._generate_next_round_if_possible(tournament)

    def refresh_player_points(self, tournament: Tournament | None) -> None:
        if tournament is None:
            return
        self._sync_players_total_points(tournament)

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
        if len(tournament.rounds) >= int(tournament.number_of_rounds):
            return False, "All rounds have already been created."
        if tournament.rounds and tournament.rounds[-1].status != "finished":
            return False, "Previous round must be finished first."

        normalized_round_name = str(round_name).strip()
        if not normalized_round_name:
            return False, "Round name is required."

        expected_matches = len(tournament.players) // 2
        if len(pairings) != expected_matches:
            return False, f"Expected {expected_matches} matches."

        players_by_ncid = {
            player.national_chess_identifier: player for player in tournament.players
        }

        seen_players: set[str] = set()
        matches: list[Match] = []
        for player_1_ncid, player_2_ncid in pairings:
            if player_1_ncid == player_2_ncid:
                return False, "A player cannot be paired against themselves."
            if player_1_ncid not in players_by_ncid or player_2_ncid not in players_by_ncid:
                return False, "Pairings contain unknown players."
            if player_1_ncid in seen_players or player_2_ncid in seen_players:
                return False, "Each player must appear exactly once."

            seen_players.add(player_1_ncid)
            seen_players.add(player_2_ncid)
            matches.append(
                Match(
                    player1=Score(player=players_by_ncid[player_1_ncid], score=0.0),
                    player2=Score(player=players_by_ncid[player_2_ncid], score=0.0),
                    status="not_started",
                )
            )

        if len(seen_players) != len(tournament.players):
            return False, "Each tournament player must be paired exactly once."

        tournament.rounds.append(
            Round(
                name=normalized_round_name,
                matches=matches,
                start_date=tournament.start_date,
                end_date=tournament.end_date,
                status="not_started",
            )
        )
        return True, ""

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

    def _serialize_tournament(self, tournament: Tournament) -> dict:
        return {
            "name": tournament.name,
            "venue": tournament.venue,
            "start_date": self._format_datetime_for_json(tournament.start_date),
            "end_date": self._format_datetime_for_json(tournament.end_date),
            "number_of_rounds": tournament.number_of_rounds,
            "automatic_pairings": bool(getattr(tournament, "automatic_pairings", True)),
            "status": tournament.status,
            "description": tournament.description,
            "players": [player.to_dict() for player in tournament.players],
            "rounds": [self._serialize_round(round_) for round_ in tournament.rounds],
        }

    def _serialize_round(self, round_: Round) -> dict:
        return {
            "name": round_.name,
            "start_date": self._format_datetime_for_json(round_.start_date),
            "end_date": self._format_datetime_for_json(round_.end_date),
            "status": round_.status,
            "matches": [self._serialize_match(match) for match in round_.matches],
        }

    def _serialize_match(self, match: Match) -> dict:
        return {
            "player1": {
                "player": match.player1.player.to_dict(),
                "score": match.player1.score,
            },
            "player2": {
                "player": match.player2.player.to_dict(),
                "score": match.player2.score,
            },
            "status": match.status,
        }

    def _deserialize_tournament(self, data: dict) -> Tournament:
        name = str(data.get("name", "")).strip()
        venue = str(data.get("venue", "")).strip()
        if not name:
            raise ValueError("Tournament name is missing in JSON.")
        if not venue:
            raise ValueError("Tournament venue is missing in JSON.")

        start_date = self._parse_datetime(data.get("start_date"), "start_date")
        end_date = self._parse_datetime(data.get("end_date"), "end_date")
        if end_date < start_date:
            raise ValueError("Tournament end_date must be after start_date.")

        number_of_rounds = int(data.get("number_of_rounds", 0))
        if number_of_rounds <= 0:
            raise ValueError("number_of_rounds must be a positive integer.")

        players_data = data.get("players", [])
        if not isinstance(players_data, list):
            raise ValueError("players must be a list.")

        players_by_ncid: dict[str, Player] = {}
        players: list[Player] = []
        for raw_player in players_data:
            if not isinstance(raw_player, dict):
                raise ValueError("Each player entry must be an object.")
            player = Player.from_dict(raw_player)
            ncid = player.national_chess_identifier
            if ncid not in players_by_ncid:
                players_by_ncid[ncid] = player
                players.append(player)

        rounds_data = data.get("rounds", [])
        if not isinstance(rounds_data, list):
            raise ValueError("rounds must be a list.")

        rounds: list[Round] = []
        for index, round_data in enumerate(rounds_data, start=1):
            if not isinstance(round_data, dict):
                raise ValueError(f"Round #{index} must be an object.")
            rounds.append(
                self._deserialize_round(
                    round_data=round_data,
                    players=players,
                    players_by_ncid=players_by_ncid,
                )
            )

        tournament = Tournament(
            name=name,
            venue=venue,
            start_date=start_date,
            end_date=end_date,
            description=str(data.get("description", "")),
            players=players,
            rounds=rounds,
            number_of_rounds=number_of_rounds,
            automatic_pairings=bool(data.get("automatic_pairings", True)),
        )
        tournament.status = str(data.get("status", "Preparation")).strip().title()
        return tournament

    def _deserialize_round(
        self,
        *,
        round_data: dict,
        players: list[Player],
        players_by_ncid: dict[str, Player],
    ) -> Round:
        name = str(round_data.get("name", "")).strip()
        if not name:
            raise ValueError("Round name is missing in JSON.")

        start_date = self._parse_datetime(round_data.get("start_date"), "round.start_date")
        end_date = self._parse_datetime(round_data.get("end_date"), "round.end_date")
        status = self._normalize_status(round_data.get("status", "not_started"))

        matches_data = round_data.get("matches", [])
        if not isinstance(matches_data, list):
            raise ValueError("round.matches must be a list.")

        matches: list[Match] = []
        for match_data in matches_data:
            if not isinstance(match_data, dict):
                raise ValueError("Each match entry must be an object.")
            matches.append(
                self._deserialize_match(
                    match_data=match_data,
                    players=players,
                    players_by_ncid=players_by_ncid,
                )
            )

        return Round(
            name=name,
            matches=matches,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )

    def _deserialize_match(
        self,
        *,
        match_data: dict,
        players: list[Player],
        players_by_ncid: dict[str, Player],
    ) -> Match:
        player_1_score_data = match_data.get("player1", {})
        player_2_score_data = match_data.get("player2", {})
        if not isinstance(player_1_score_data, dict) or not isinstance(player_2_score_data, dict):
            raise ValueError("match.player1 and match.player2 must be objects.")

        player_1 = self._resolve_player_reference(
            player_1_score_data.get("player"),
            players,
            players_by_ncid,
        )
        player_2 = self._resolve_player_reference(
            player_2_score_data.get("player"),
            players,
            players_by_ncid,
        )

        player_1_score = float(player_1_score_data.get("score", 0.0))
        player_2_score = float(player_2_score_data.get("score", 0.0))

        return Match(
            player1=Score(player=player_1, score=player_1_score),
            player2=Score(player=player_2, score=player_2_score),
            status=self._normalize_status(match_data.get("status", "not_started")),
        )

    def _resolve_player_reference(
        self,
        player_data: dict | str | None,
        players: list[Player],
        players_by_ncid: dict[str, Player],
    ) -> Player:
        if isinstance(player_data, str):
            existing_player = players_by_ncid.get(player_data)
            if existing_player is None:
                raise ValueError(f"Unknown player identifier '{player_data}' in match.")
            return existing_player

        if not isinstance(player_data, dict):
            raise ValueError("Match player entry must contain a player object or identifier.")

        parsed_player = Player.from_dict(player_data)
        ncid = parsed_player.national_chess_identifier
        existing_player = players_by_ncid.get(ncid)
        if existing_player is not None:
            return existing_player

        players_by_ncid[ncid] = parsed_player
        players.append(parsed_player)
        return parsed_player

    @staticmethod
    def _parse_datetime(value, field_name: str) -> datetime:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string datetime.")

        normalized = value.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
        raise ValueError(f"{field_name} must use format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.")

    @staticmethod
    def _format_datetime_for_json(value) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

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
    def _current_round_number(tournament: Tournament) -> int:
        if not tournament.rounds:
            return 0
        for index, round_ in enumerate(tournament.rounds, start=1):
            if str(getattr(round_, "status", "")).strip().lower() == "ongoing":
                return index
        return 0

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
        totals = {
            player.national_chess_identifier: 0.0
            for player in tournament.players
        }
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
