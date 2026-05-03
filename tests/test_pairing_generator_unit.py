from src.controllers.pairings_generator import PairingGenerator
from src.models.history import MatchHistory
from src.models.players import Player


def _player(ncid: str) -> Player:
    return Player("F", "L", "1990-01-01", ncid)


def test_generate_pairings_raises_with_odd_number_of_players() -> None:
    generator = PairingGenerator([_player("AA00001"), _player("AA00002"), _player("AA00003")])
    try:
        generator.generate_pairings(number_of_round=1)
        assert False, "Expected ValueError for odd number of players"
    except ValueError as exc:
        assert "even number of players" in str(exc)


def test_update_after_match_updates_points_for_each_result_type() -> None:
    generator = PairingGenerator([_player("AA00001"), _player("AA00002")])

    generator.update_after_match("AA00001", "AA00002", "player1")
    assert generator.player_points["AA00001"] == 1.0
    assert generator.player_points["AA00002"] == 0.0

    generator.update_after_match("AA00001", "AA00002", "tie")
    assert generator.player_points["AA00001"] == 1.5
    assert generator.player_points["AA00002"] == 0.5

    generator.update_after_match("AA00001", "AA00002", "player2")
    assert generator.player_points["AA00001"] == 1.5
    assert generator.player_points["AA00002"] == 1.5


def test_generate_pairings_avoids_seen_rematch_when_possible(monkeypatch) -> None:
    players = [_player("AA00001"), _player("AA00002"), _player("AA00003"), _player("AA00004")]
    players[0].tournament_history["r1m1"] = MatchHistory(
        opponent="AA00002",
        winner="AA00001",
        start_date="2026-04-01 10:00:00",
        end_date="2026-04-01 10:30:00",
    )
    players[1].tournament_history["r1m1"] = MatchHistory(
        opponent="AA00001",
        winner="AA00001",
        start_date="2026-04-01 10:00:00",
        end_date="2026-04-01 10:30:00",
    )

    # Keep ordering deterministic for this test.
    monkeypatch.setattr("src.controllers.pairings_generator.shuffle", lambda values: None)

    generator = PairingGenerator(players)
    pairings = generator.generate_pairings(number_of_round=2)
    normalized = {tuple(sorted(pairing)) for pairing in pairings}

    assert ("AA00001", "AA00002") not in normalized
    assert len(normalized) == 2
