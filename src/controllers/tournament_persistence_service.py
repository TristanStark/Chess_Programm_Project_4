from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from src.models.matches import Match, Round, Score
from src.models.players import Player
from src.models.tournaments import Tournament


class TournamentPersistenceService:
    def __init__(self, tournaments_directory: Path | None = None) -> None:
        self.tournaments_directory = tournaments_directory or Path("data") / "tournaments"
        self.tournaments_directory.mkdir(parents=True, exist_ok=True)

    def create_tournament_from_form_data(self, tournament_data: dict):
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

    def build_tournament_filename(self, tournament: Tournament) -> str:
        raw = f"{tournament.name}_{tournament.start_date.strftime('%Y%m%d')}"
        sanitized = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_").lower()
        return sanitized or "tournament"

    def next_available_tournament_filename(self, base_filename: str) -> str:
        candidate = base_filename
        suffix = 2
        while (self.tournaments_directory / f"{candidate}.json").exists():
            candidate = f"{base_filename}_{suffix}"
            suffix += 1
        return candidate

    def save_tournament_to_json(self, tournament: Tournament, file_path: Path) -> None:
        payload = self._serialize_tournament(tournament)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)

    def load_tournament_from_json(self, file_path: Path | str) -> Tournament:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return self._deserialize_tournament(data)

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

    @staticmethod
    def _serialize_match(match: Match) -> dict:
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

    @staticmethod
    def _resolve_player_reference(
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

    @staticmethod
    def _normalize_status(status: str) -> str:
        normalized = str(status).strip().lower()
        if normalized not in {"not_started", "ongoing", "finished"}:
            return "not_started"
        return normalized
