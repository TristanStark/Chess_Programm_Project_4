from src.models.history import MatchHistory
from src.models.players import Player


def test_player_ncid_validation_accepts_expected_pattern() -> None:
    player = Player("Jane", "Doe", "1990-10-11", "AB12345")
    assert player.is_ncid_valid() is True
    assert player.check_validity() is True


def test_player_ncid_validation_rejects_invalid_pattern() -> None:
    player = Player("Jane", "Doe", "1990-10-11", "A123456")
    assert player.is_ncid_valid() is False
    assert player.check_validity() is False


def test_player_from_dict_supports_ncid_alias_and_history_deserialization() -> None:
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-10-11",
        "ncid": "AB12345",
        "tournament_history": {
            "round_1": {
                "opponent": "CD54321",
                "winner": "AB12345",
                "start_date": "2026-04-01 10:00:00",
                "end_date": "2026-04-01 10:30:00",
            }
        },
    }

    player = Player.from_dict(payload)

    assert player.national_chess_identifier == "AB12345"
    assert "round_1" in player.tournament_history
    assert isinstance(player.tournament_history["round_1"], MatchHistory)
    assert player.tournament_history["round_1"].winner == "AB12345"


def test_player_save_and_load_roundtrip(tmp_path) -> None:
    player = Player("Jane", "Doe", "1990-10-11", "AB12345")
    target = tmp_path / "players" / "jane.json"

    player.save(target)
    loaded = Player.load(target)

    assert loaded.to_dict() == player.to_dict()
