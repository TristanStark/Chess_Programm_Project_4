from datetime import datetime
from typing import Callable, Iterable

from src.models.matches import Round
from src.models.tournaments import Tournament
from src.controllers.settings import debug_print
from src.controllers.view_contracts import RoundsViewProtocol


class RoundController:
    """Controller responsible for sending Round model data to the rounds view."""

    def __init__(self, rounds_view: RoundsViewProtocol):
        self.rounds_view = rounds_view
        self.rounds: list[Round] = []

    def add_round_to_view(self, round_: Round) -> None:
        """Add one Round model instance to the view."""
        self.rounds_view.add_round_row(
            self._format_round_row(round_),
            status=round_.status,
            match_status_summary=self._format_round_match_status_summary(round_),
        )
        debug_print(f"Adding round to view with status: {round_.status}")

    def populate_view(self, rounds: Iterable[Round], clear_before: bool = True) -> None:
        """Populate the rounds view from an iterable of Round model instances."""
        self.rounds = list(rounds)
        if clear_before:
            self.rounds_view.clear_rounds()

        for round_ in self.rounds:
            self.add_round_to_view(round_)

    def populate_from_tournament(
        self,
        tournament: Tournament,
        clear_before: bool = True,
    ) -> None:
        """Populate the rounds view from a Tournament model instance."""
        self.populate_view(tournament.rounds, clear_before=clear_before)

    def set_status(self, text: str) -> None:
        """Set the status label shown above the rounds list."""
        self.rounds_view.round_status_label.configure(text=text)

    def get_round_by_index(self, index):
        if index is None:
            return None
        if 0 <= index < len(self.rounds):
            return self.rounds[index]
        return None

    def get_round_status(self, index):
        round_ = self.get_round_by_index(index)
        if round_ is None:
            return None
        return round_.status

    def update_round_status(self, index: int, status: str) -> None:
        round_ = self.get_round_by_index(index)
        if round_ is None:
            return

        round_.status = self._normalize_status(status)
        self.rounds_view.update_round_status(
            index,
            round_.status,
            match_status_summary=self._format_round_match_status_summary(round_),
        )

    def can_start_round(
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
            return False, "No round selected."
        if round_.status != "not_started":
            return False, "Round is not in not_started status."
        if not self.are_previous_rounds_finished(tournament, round_index):
            return False, "Previous rounds must be finished first."
        return True, ""

    def start_round(
        self,
        tournament: Tournament | None,
        round_index: int | None,
    ) -> tuple[bool, str]:
        can_start, message = self.can_start_round(tournament, round_index)
        if not can_start:
            return False, message
        round_ = self._get_round_by_index(tournament, round_index)
        round_.status = "ongoing"
        return True, ""

    def can_stop_round(
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
            return False, "No round selected."
        if round_.status != "ongoing":
            return False, "Round must be ongoing."
        if not self.are_all_matches_finished_in_round(round_):
            return False, "All matches in this round must be finished."
        return True, ""

    def stop_round(
        self,
        tournament: Tournament | None,
        round_index: int | None,
        *,
        on_round_finished: Callable[[Tournament | None], bool] | None = None,
    ) -> tuple[bool, str]:
        can_stop, message = self.can_stop_round(tournament, round_index)
        if not can_stop:
            return False, message
        round_ = self._get_round_by_index(tournament, round_index)
        round_.status = "finished"
        if on_round_finished is not None:
            on_round_finished(tournament)
        return True, ""

    @staticmethod
    def are_all_matches_finished_in_round(round_: Round | None) -> bool:
        if round_ is None:
            return False
        if not round_.matches:
            return False
        blocking_statuses = {"not_started", "ongoing", "preparation"}
        for match in round_.matches:
            normalized_status = str(getattr(match, "status", "")).strip().lower()
            if normalized_status in blocking_statuses:
                return False
        return True

    def are_previous_rounds_finished(
        self,
        tournament: Tournament | None,
        round_index: int | None,
    ) -> bool:
        if tournament is None or round_index is None:
            return False
        if round_index <= 0:
            return True
        if not 0 <= round_index < len(tournament.rounds):
            return False

        for index in range(0, round_index):
            if tournament.rounds[index].status != "finished":
                return False
        return True

    def _format_round_row(self, round_: Round) -> str:
        start_text = self._format_datetime(round_.start_date)
        end_text = self._format_datetime(round_.end_date)
        return f"{round_.name} - {start_text} - {end_text}"

    def _format_round_match_status_summary(self, round_: Round) -> str:
        status_counts = {
            "ongoing": 0,
            "not_started": 0,
            "finished": 0,
        }
        for match in getattr(round_, "matches", []):
            normalized_status = self._normalize_status(getattr(match, "status", ""))
            status_counts[normalized_status] += 1

        return (
            f"{status_counts['ongoing']} ongoing, "
            f"{status_counts['not_started']} not started, "
            f"{status_counts['finished']} finished"
        )

    @staticmethod
    def _format_datetime(value) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
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
