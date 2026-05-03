from datetime import datetime
from typing import Iterable

from src.models.history import MatchHistory
from src.models.matches import Match, Round
from src.models.tournaments import Tournament
from src.controllers.view_contracts import MatchesViewProtocol


class MatchController:
    """Controller responsible for sending Match model data to the matches view."""

    def __init__(self, matches_view: MatchesViewProtocol):
        self.matches_view = matches_view
        self.matches: list[Match] = []

    def add_match_to_view(self, match: Match) -> None:
        """Add one Match model instance to the view."""
        player_1_name = self._format_player_name(match.player1.player)
        player_2_name = self._format_player_name(match.player2.player)
        player_1_score = self._format_score(match.player1.score)
        player_2_score = self._format_score(match.player2.score)

        self.matches_view.add_match(
            player_1_name=player_1_name,
            player_1_score=player_1_score,
            player_2_name=player_2_name,
            player_2_score=player_2_score,
            status=match.status,
        )

    def populate_view(self, matches: Iterable[Match], clear_before: bool = True) -> None:
        """Populate the matches view from a list/iterable of Match model instances."""
        self.matches = list(matches)
        if clear_before:
            self.matches_view.clear_matches()

        for match in self.matches:
            self.add_match_to_view(match)

    def populate_from_round(self, round_: Round, clear_before: bool = True) -> None:
        """Populate the view from a Round model instance."""
        self.populate_view(round_.matches, clear_before=clear_before)

    def get_match_by_index(self, index):
        if index is None:
            return None
        if 0 <= index < len(self.matches):
            return self.matches[index]
        return None

    def set_match_status(self, index: int, status: str) -> bool:
        match = self.get_match_by_index(index)
        if match is None:
            return False

        normalized_status = self._normalize_status(status)
        match.status = normalized_status
        self.matches_view.update_match_status(index, normalized_status)
        return True

    def start_match(self, index: int) -> bool:
        match = self.get_match_by_index(index)
        if match is None or match.status != "not_started":
            return False
        return self.set_match_status(index, "ongoing")

    def can_change_match(
        self,
        tournament: Tournament | None,
        round_index: int | None,
    ) -> tuple[bool, str]:
        if tournament is None:
            return False, "No active tournament."
        if not self._is_tournament_ongoing(tournament):
            return False, "Tournament must be ongoing."
        round_ = self._get_round_by_index(tournament, round_index)
        if round_ is None:
            return False, "No active round selected."
        if round_.status != "ongoing":
            return False, "Round must be ongoing."
        return True, ""

    def finish_match(
        self,
        index: int,
        result: str,
        *,
        round_: Round | None = None,
        tournament: Tournament | None = None,
    ) -> bool:
        """
        Close a match and apply points/history updates.
        `result` values: "player1", "tie", "player2"
        """
        match = self.get_match_by_index(index)
        if match is None or match.status != "ongoing":
            return False

        normalized_result = str(result).strip().lower()
        if normalized_result not in {"player1", "tie", "player2"}:
            return False

        if normalized_result == "player1":
            match.player1.score = 1.0
            match.player2.score = 0.0
            winner = match.player1.player.national_chess_identifier
        elif normalized_result == "player2":
            match.player1.score = 0.0
            match.player2.score = 1.0
            winner = match.player2.player.national_chess_identifier
        else:
            match.player1.score = 0.5
            match.player2.score = 0.5
            winner = "draw"

        self._append_match_history(index, match, winner, round_)
        self.set_match_status(index, "finished")
        return True

    def _append_match_history(
        self,
        index: int,
        match: Match,
        winner: str,
        round_: Round | None,
    ) -> None:
        player_1 = match.player1.player
        player_2 = match.player2.player

        round_name = "round"
        start_date = datetime.now()
        if round_ is not None:
            round_name = getattr(round_, "name", round_name) or round_name
            start_date = getattr(round_, "start_date", start_date)
        end_date = datetime.now()

        history_key = (
            f"{round_name}_{index + 1}_"
            f"{player_1.national_chess_identifier}_{player_2.national_chess_identifier}"
        )

        player_1.tournament_history[history_key] = MatchHistory(
            opponent=player_2.national_chess_identifier,
            winner=winner,
            start_date=self._format_datetime(start_date),
            end_date=self._format_datetime(end_date),
        )
        player_2.tournament_history[history_key] = MatchHistory(
            opponent=player_1.national_chess_identifier,
            winner=winner,
            start_date=self._format_datetime(start_date),
            end_date=self._format_datetime(end_date),
        )

    @staticmethod
    def _format_player_name(player) -> str:
        first_name = getattr(player, "first_name", "")
        last_name = getattr(player, "last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        return full_name if full_name else str(player)

    @staticmethod
    def _format_score(score: float):
        if isinstance(score, (int, float)) and float(score).is_integer():
            return int(score)
        return score

    @staticmethod
    def _format_datetime(value) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

    @staticmethod
    def _normalize_status(status: str) -> str:
        normalized = str(status).strip().lower()
        if normalized not in {"not_started", "ongoing", "finished"}:
            return "not_started"
        return normalized

    @staticmethod
    def _is_tournament_ongoing(tournament: Tournament | None) -> bool:
        if tournament is None:
            return False
        return str(getattr(tournament, "status", "")).strip().lower() == "ongoing"

    @staticmethod
    def _get_round_by_index(tournament: Tournament | None, round_index: int | None):
        if tournament is None or round_index is None:
            return None
        if not 0 <= round_index < len(tournament.rounds):
            return None
        return tournament.rounds[round_index]
