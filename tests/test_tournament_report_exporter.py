from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.exporters.tournament_report_exporter import TournamentReportExporter
from src.models.matches import Match, Round, Score
from src.models.players import Player
from src.models.tournaments import Tournament


class _DummyPlayersController:
    @staticmethod
    def get_all_players():
        return []


class _DummyTournamentController:
    def __init__(self, tournaments_directory: Path) -> None:
        self.tournaments_directory = tournaments_directory


def _build_player(first_name: str, last_name: str, ncid: str) -> Player:
    return Player(
        first_name=first_name,
        last_name=last_name,
        date_of_birth="1990-01-01",
        national_chess_identifier=ncid,
    )


def _build_tournament(status: str) -> Tournament:
    player_1 = _build_player("Alice", "Alpha", "AA00001")
    player_2 = _build_player("Bruno", "Bravo", "AA00002")
    player_3 = _build_player("Claire", "Charlie", "AA00003")
    player_4 = _build_player("David", "Delta", "AA00004")
    players = [player_1, player_2, player_3, player_4]

    round_1 = Round(
        name="Round 1",
        matches=[
            Match(
                player1=Score(player=player_1, score=1.0),
                player2=Score(player=player_4, score=0.0),
                status="finished",
            ),
            Match(
                player1=Score(player=player_2, score=1.0),
                player2=Score(player=player_3, score=0.0),
                status="finished",
            ),
        ],
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 1),
        status="finished",
    )
    round_2 = Round(
        name="Round 2",
        matches=[
            Match(
                player1=Score(player=player_1, score=1.0),
                player2=Score(player=player_2, score=0.0),
                status="finished",
            ),
            Match(
                player1=Score(player=player_3, score=1.0),
                player2=Score(player=player_4, score=0.0),
                status="finished",
            ),
        ],
        start_date=datetime(2026, 4, 2),
        end_date=datetime(2026, 4, 2),
        status="finished",
    )

    tournament = Tournament(
        name="Spring Open",
        venue="Paris",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 7),
        description="Report exporter test",
        players=players,
        rounds=[round_1, round_2],
        number_of_rounds=2,
    )
    tournament.status = status
    return tournament


def test_serialize_tournament_includes_podium_when_completed(tmp_path: Path) -> None:
    exporter = TournamentReportExporter(
        players_controller=_DummyPlayersController(),
        tournament_controller=_DummyTournamentController(tmp_path),
        templates_directory=Path("report_templates"),
        exports_directory=tmp_path,
    )
    tournament = _build_tournament("Completed")

    payload = exporter._serialize_tournament(tournament)

    assert [entry["name"] for entry in payload["podium"]] == [
        "Alice Alpha",
        "Bruno Bravo",
        "Claire Charlie",
    ]
    assert [entry["points"] for entry in payload["podium"]] == ["2", "1", "1"]


def test_serialize_tournament_omits_podium_when_not_completed(tmp_path: Path) -> None:
    exporter = TournamentReportExporter(
        players_controller=_DummyPlayersController(),
        tournament_controller=_DummyTournamentController(tmp_path),
        templates_directory=Path("report_templates"),
        exports_directory=tmp_path,
    )
    tournament = _build_tournament("Ongoing")

    payload = exporter._serialize_tournament(tournament)

    assert payload["podium"] == []
