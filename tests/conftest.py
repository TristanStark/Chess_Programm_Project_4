from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pytest

from src.models.players import Player
from src.models.tournaments import Tournament


class DummyPlayerInfoView:
    def __init__(self) -> None:
        self.payload: dict[str, str] | None = None
        self.was_cleared = False

    def set_player_info(self, **kwargs) -> None:
        self.payload = dict(kwargs)
        self.was_cleared = False

    def clear(self) -> None:
        self.payload = None
        self.was_cleared = True


class DummyMatchesView:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def clear_matches(self) -> None:
        self.rows = []

    def add_match(
        self,
        player_1_name,
        player_1_score,
        player_2_name,
        player_2_score,
        status="not_started",
    ) -> None:
        self.rows.append(
            {
                "player_1_name": player_1_name,
                "player_1_score": player_1_score,
                "player_2_name": player_2_name,
                "player_2_score": player_2_score,
                "status": status,
            }
        )

    def update_match_status(self, index: int, status: str) -> None:
        self.rows[index]["status"] = status


class DummyLabel:
    def __init__(self) -> None:
        self.text = ""

    def configure(self, *, text) -> None:
        self.text = str(text)


class DummyRoundsView:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.round_status_label = DummyLabel()

    def clear_rounds(self) -> None:
        self.rows = []

    def add_round_row(self, text, status="not_started", match_status_summary: str = "") -> None:
        self.rows.append({"text": text, "status": status})

    def update_round_status(
        self,
        index: int,
        status: str,
        match_status_summary: str = "",
    ) -> None:
        self.rows[index]["status"] = status


@dataclass
class DummyLeftPanel:
    infos: dict = field(default_factory=dict)
    players: list[Player] = field(default_factory=list)
    description: str = ""

    def set_tournament_infos(self, **kwargs) -> None:
        self.infos = dict(kwargs)

    def set_players(self, players: list[Player]) -> None:
        self.players = list(players)

    def set_description(self, description: str) -> None:
        self.description = str(description)


class DummyTitleLabel:
    def __init__(self) -> None:
        self.text = ""

    def configure(self, *, text) -> None:
        self.text = str(text)


class DummyTournamentView:
    def __init__(self) -> None:
        self.tournament_name_label = DummyTitleLabel()
        self.tournament_venue_label = DummyTitleLabel()
        self.left_panel = DummyLeftPanel()


def build_player(index: int) -> Player:
    return Player(
        first_name=f"First{index}",
        last_name=f"Last{index}",
        date_of_birth="1990-01-01",
        national_chess_identifier=f"AA{index:05d}",
    )


@pytest.fixture
def four_players() -> list[Player]:
    return [build_player(i) for i in range(1, 5)]


@pytest.fixture
def dummy_matches_view() -> DummyMatchesView:
    return DummyMatchesView()


@pytest.fixture
def dummy_player_info_view() -> DummyPlayerInfoView:
    return DummyPlayerInfoView()


@pytest.fixture
def dummy_rounds_view() -> DummyRoundsView:
    return DummyRoundsView()


@pytest.fixture
def dummy_tournament_view() -> DummyTournamentView:
    return DummyTournamentView()


@pytest.fixture
def tournament_with_four_players(four_players: list[Player]) -> Tournament:
    tournament = Tournament(
        name="Spring Open",
        venue="Paris",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 7),
        description="Integration test tournament",
        players=four_players,
        rounds=[],
        number_of_rounds=2,
    )
    tournament.status = "Preparation"
    return tournament
