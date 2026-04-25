from src.controllers.player_controller import PlayerController
from src.models.players import Player


def test_select_player_populates_player_info_view(dummy_player_info_view) -> None:
    controller = PlayerController(dummy_player_info_view)
    player = Player("Jane", "Doe", "1990-10-11", "AB12345")

    controller.select_player(player)

    assert controller.get_selected_player() is player
    assert dummy_player_info_view.payload == {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-10-11",
        "ncid": "AB12345",
        "total_points": "0",
    }


def test_select_player_by_index_with_invalid_index_clears_view(
    dummy_player_info_view,
) -> None:
    controller = PlayerController(dummy_player_info_view)
    players = [Player("Jane", "Doe", "1990-10-11", "AB12345")]

    selected = controller.select_player_by_index(players, 3)

    assert selected is None
    assert controller.get_selected_player() is None
    assert dummy_player_info_view.was_cleared is True
