from datetime import datetime

from src.controllers.round_controller import RoundController
from src.models.matches import Match, Round, Score
from src.models.players import Player
from src.models.tournaments import Tournament


def _build_match(status: str) -> Match:
    player_1 = Player("A", "One", "1990-01-01", "AA00001")
    player_2 = Player("B", "Two", "1990-01-01", "AA00002")
    return Match(
        player1=Score(player=player_1, score=0.0),
        player2=Score(player=player_2, score=0.0),
        status=status,
    )


def _build_round(name: str, status: str, match_status: str = "not_started") -> Round:
    return Round(
        name=name,
        matches=[_build_match(match_status)],
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 1),
        status=status,
    )


class DummyLabel:
    def __init__(self) -> None:
        self.text = ""

    def configure(self, *, text) -> None:
        self.text = str(text)


class DummyRoundsView:
    def __init__(self) -> None:
        self.round_status_label = DummyLabel()
        self.rows = []

    def add_round_row(self, text, status="not_started", match_status_summary: str = "") -> None:
        self.rows.append({"text": text, "status": status})

    def clear_rounds(self) -> None:
        self.rows = []

    def update_round_status(self, index, status, match_status_summary: str = "") -> None:
        self.rows[index]["status"] = status


def test_start_round_requires_previous_rounds_finished() -> None:
    controller = RoundController(DummyRoundsView())
    tournament = Tournament(
        name="T",
        venue="V",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 2),
        description="desc",
        players=[],
        rounds=[
            _build_round("Round 1", status="ongoing"),
            _build_round("Round 2", status="not_started"),
        ],
        number_of_rounds=2,
    )
    tournament.status = "Ongoing"

    can_start, message = controller.can_start_round(tournament, 1)
    assert can_start is False
    assert message == "Previous rounds must be finished first."


def test_stop_round_requires_all_matches_finished() -> None:
    controller = RoundController(DummyRoundsView())
    round_1 = _build_round("Round 1", status="ongoing", match_status="ongoing")
    tournament = Tournament(
        name="T",
        venue="V",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 2),
        description="desc",
        players=[],
        rounds=[round_1],
        number_of_rounds=1,
    )
    tournament.status = "Ongoing"

    can_stop, message = controller.can_stop_round(tournament, 0)
    assert can_stop is False
    assert message == "All matches in this round must be finished."
