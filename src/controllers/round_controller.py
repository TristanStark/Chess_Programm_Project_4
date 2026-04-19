from datetime import datetime
from typing import Iterable

from src.models.matches import Round
from src.models.tournaments import Tournament
from src.views.rounds_view import TournamentRoundsPanel


class RoundController:
    """Controller responsible for sending Round model data to the rounds view."""

    def __init__(self, rounds_view: TournamentRoundsPanel):
        self.rounds_view = rounds_view
        self.rounds: list[Round] = []
        self.round_statuses: list[str] = []

    def add_round_to_view(self, round_: Round, status: str = "not_started") -> None:
        """Add one Round model instance to the view."""
        self.rounds_view.add_round_row(self._format_round_row(round_), status=status)

    def populate_view(
        self,
        rounds: Iterable[Round],
        clear_before: bool = True,
        round_statuses: list[str] | None = None,
    ) -> None:
        """Populate the rounds view from an iterable of Round model instances."""
        self.rounds = list(rounds)
        if round_statuses is None:
            self.round_statuses = ["not_started" for _ in self.rounds]
        else:
            self.round_statuses = list(round_statuses)
            if len(self.round_statuses) < len(self.rounds):
                self.round_statuses.extend(
                    ["not_started" for _ in range(len(self.rounds) - len(self.round_statuses))]
                )
            elif len(self.round_statuses) > len(self.rounds):
                self.round_statuses = self.round_statuses[: len(self.rounds)]

        if clear_before:
            self.rounds_view.clear_rounds()

        for index, round_ in enumerate(self.rounds):
            self.add_round_to_view(round_, status=self.round_statuses[index])

    def populate_from_tournament(
        self,
        tournament: Tournament,
        clear_before: bool = True,
        round_statuses: list[str] | None = None,
    ) -> None:
        """Populate the rounds view from a Tournament model instance."""
        self.populate_view(
            tournament.rounds,
            clear_before=clear_before,
            round_statuses=round_statuses,
        )

    def set_status(self, text: str) -> None:
        """Set the status label shown above the rounds list."""
        self.rounds_view.round_status_label.configure(text=text)

    def get_round_by_index(self, index):
        if index is None:
            return None
        if 0 <= index < len(self.rounds):
            return self.rounds[index]
        return None

    def update_round_status(self, index: int, status: str) -> None:
        if not 0 <= index < len(self.round_statuses):
            return

        normalized_status = self._normalize_status(status)
        self.round_statuses[index] = normalized_status
        self.rounds_view.update_round_status(index, normalized_status)

    def _format_round_row(self, round_: Round) -> str:
        start_text = self._format_datetime(round_.start_date)
        end_text = self._format_datetime(round_.end_date)
        return f"{round_.name} - {start_text} - {end_text}"

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
