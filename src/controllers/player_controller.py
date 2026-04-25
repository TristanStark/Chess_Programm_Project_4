from typing import Optional, Sequence

from src.models.players import Player
from src.views.player_info_card_view import PlayerInfoCard


class PlayerController:
    """Controller responsible for binding a selected Player to PlayerInfoCard view."""

    def __init__(self, player_view: PlayerInfoCard):
        self.player_view = player_view
        self._selected_player: Optional[Player] = None

    def select_player(self, player: Optional[Player], total_points: float | None = None) -> None:
        """Populate the view with a Player model, or clear it when None."""
        self._selected_player = player
        if player is None:
            self.player_view.clear()
            return

        if total_points is None:
            total_points = self._extract_player_points(player)

        self.player_view.set_player_info(
            first_name=player.first_name,
            last_name=player.last_name,
            date_of_birth=player.date_of_birth,
            ncid=player.national_chess_identifier,
            total_points=self._format_points(total_points),
        )

    def select_player_by_index(
        self, players: Sequence[Player], selected_index: Optional[int]
    ) -> Optional[Player]:
        """Select one player from a players collection and populate the view."""
        if selected_index is None:
            self.select_player(None)
            return None
        if not 0 <= selected_index < len(players):
            self.select_player(None)
            return None

        selected_player = players[selected_index]
        self.select_player(selected_player)
        return selected_player

    def get_selected_player(self) -> Optional[Player]:
        return self._selected_player

    @staticmethod
    def _extract_player_points(player: Player) -> float:
        if hasattr(player, "total_points"):
            return float(getattr(player, "total_points"))
        if hasattr(player, "_total_points"):
            return float(getattr(player, "_total_points"))
        return 0.0

    @staticmethod
    def _format_points(points: float) -> str:
        value = float(points)
        if value.is_integer():
            return str(int(value))
        return f"{value:.1f}"
