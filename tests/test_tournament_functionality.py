from __future__ import annotations

from src.controllers.match_controller import MatchController
from src.controllers.round_controller import RoundController
from src.controllers.tournament_controller import TournamentController
from src.models.matches import Round


def _complete_all_matches_for_round(
    *,
    match_controller: MatchController,
    tournament_controller: TournamentController,
    tournament,
    round_index: int,
) -> None:
    current_round = tournament.rounds[round_index]
    match_controller.populate_from_round(current_round)
    for match_index in range(len(current_round.matches)):
        started = match_controller.start_match(match_index)
        assert started is True

        finished = match_controller.finish_match(
            match_index,
            result="player1",
            round_=current_round,
            tournament=tournament,
        )
        assert finished is True

        match = current_round.matches[match_index]
        tournament_controller.update_pairing_generator_after_match(
            tournament=tournament,
            match=match,
            result="player1",
        )

    tournament_controller.sync_round_status_from_matches(tournament, round_index)


def test_tournament_full_flow_generates_rounds_and_completes(
    tournament_with_four_players,
    dummy_matches_view,
    dummy_rounds_view,
    dummy_tournament_view,
) -> None:
    match_controller = MatchController(dummy_matches_view)
    round_controller = RoundController(dummy_rounds_view)
    tournament_controller = TournamentController(
        tournament_view=dummy_tournament_view,
        round_controller=round_controller,
        match_controller=match_controller,
    )

    started, message = tournament_controller.start_tournament(tournament_with_four_players)
    assert started is True, message
    assert tournament_with_four_players.status == "Ongoing"
    assert len(tournament_with_four_players.rounds) == 1
    assert len(tournament_with_four_players.rounds[0].matches) == 2

    _complete_all_matches_for_round(
        match_controller=match_controller,
        tournament_controller=tournament_controller,
        tournament=tournament_with_four_players,
        round_index=0,
    )
    assert tournament_with_four_players.rounds[0].status == "finished"
    assert len(tournament_with_four_players.rounds) == 2

    _complete_all_matches_for_round(
        match_controller=match_controller,
        tournament_controller=tournament_controller,
        tournament=tournament_with_four_players,
        round_index=1,
    )
    assert tournament_with_four_players.rounds[1].status == "finished"
    assert tournament_with_four_players.status == "Completed"


def test_create_save_and_reload_tournament_json_roundtrip(
    tmp_path,
    tournament_with_four_players,
    dummy_tournament_view,
) -> None:
    tournaments_dir = tmp_path / "tournaments"
    controller = TournamentController(
        tournament_view=dummy_tournament_view,
        tournaments_directory=tournaments_dir,
    )

    save_path = tournaments_dir / "sample_tournament.json"
    ok, msg, written_path = controller.save_tournament_to_json(
        tournament_with_four_players, save_path
    )
    assert ok is True, msg
    assert written_path is not None
    assert written_path.exists()

    loaded_ok, loaded_msg, loaded_tournament = controller.load_tournament_from_json(
        written_path
    )
    assert loaded_ok is True, loaded_msg
    assert loaded_tournament is not None
    assert loaded_tournament.name == tournament_with_four_players.name
    assert len(loaded_tournament.players) == len(tournament_with_four_players.players)


def test_tournament_is_not_completed_before_configured_round_count(
    tournament_with_four_players,
    dummy_tournament_view,
) -> None:
    controller = TournamentController(tournament_view=dummy_tournament_view)
    tournament_with_four_players.status = "Ongoing"

    tournament_with_four_players.rounds = [
        Round(
            name="Round 1",
            matches=[],
            start_date=tournament_with_four_players.start_date,
            end_date=tournament_with_four_players.end_date,
            status="finished",
        ),
    ]

    controller.update_tournament_status_from_matches(tournament_with_four_players)
    assert tournament_with_four_players.status == "Ongoing"


def test_current_round_prefers_first_not_started_round(
    tournament_with_four_players,
    dummy_tournament_view,
) -> None:
    controller = TournamentController(tournament_view=dummy_tournament_view)
    tournament_with_four_players.number_of_rounds = 4
    tournament_with_four_players.rounds = [
        Round(
            name="Round 1",
            matches=[],
            start_date=tournament_with_four_players.start_date,
            end_date=tournament_with_four_players.end_date,
            status="finished",
        ),
        Round(
            name="Round 2",
            matches=[],
            start_date=tournament_with_four_players.start_date,
            end_date=tournament_with_four_players.end_date,
            status="finished",
        ),
        Round(
            name="Round 3",
            matches=[],
            start_date=tournament_with_four_players.start_date,
            end_date=tournament_with_four_players.end_date,
            status="not_started",
        ),
    ]

    view_data = controller.build_view_data(tournament_with_four_players)
    assert view_data["infos"]["current_round"] == "3/4"
