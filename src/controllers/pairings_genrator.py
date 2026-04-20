from random import shuffle
from typing import Dict, List, Tuple

from src.models.players import Player


class PairingGenerator:
    def __init__(self, player_list: List[Player]):
        self.player_list: List[Player] = player_list
        self.seen_matches: Dict[Tuple[str, str], int] = {}
        self.player_points: Dict[str, float] = {}
        self.current_round: int = 0
        self._refresh_player_points()

    def set_players(self, player_list: List[Player]) -> None:
        self.player_list = player_list
        self._refresh_player_points()

    @staticmethod
    def _normalize_match_key(player_1_ncid: str, player_2_ncid: str) -> Tuple[str, str]:
        return tuple(sorted((player_1_ncid, player_2_ncid)))

    @staticmethod
    def _is_draw_result(raw_winner: str) -> bool:
        normalized = raw_winner.strip().lower()
        return normalized in {"", "draw", "tie", "equal", "none", "null"}

    def _player_points(self, player: Player) -> float:
        """
        Compute points from tournament history:
        - win: 1 point
        - draw/empty winner: 0.5 point
        - loss: 0 point
        """
        points = 0.0
        player_ncid = player.national_chess_identifier

        for history_entry in player.tournament_history.values():
            winner = str(getattr(history_entry, "winner", "")).strip()
            if self._is_draw_result(winner):
                points += 0.5
            elif winner == player_ncid:
                points += 1.0

        return points

    def _refresh_player_points(self) -> None:
        self.player_points = {
            player.national_chess_identifier: self._player_points(player)
            for player in self.player_list
        }

    def _hydrate_seen_matches_from_history(self) -> None:
        """
        Rebuild already-played matches from players history so rematch prevention
        works after loading persisted data.
        """
        for player in self.player_list:
            player_ncid = player.national_chess_identifier
            for history_entry in player.tournament_history.values():
                opponent = str(getattr(history_entry, "opponent", "")).strip()
                if not opponent:
                    continue
                key = self._normalize_match_key(player_ncid, opponent)
                self.seen_matches[key] = 1

    def update_after_match(
        self,
        player_1_ncid: str,
        player_2_ncid: str,
        result: str,
    ) -> None:
        normalized_result = str(result).strip().lower()
        if normalized_result not in {"player1", "player2", "tie"}:
            return

        self.player_points.setdefault(player_1_ncid, 0.0)
        self.player_points.setdefault(player_2_ncid, 0.0)
        if normalized_result == "player1":
            self.player_points[player_1_ncid] += 1.0
        elif normalized_result == "player2":
            self.player_points[player_2_ncid] += 1.0
        else:
            self.player_points[player_1_ncid] += 0.5
            self.player_points[player_2_ncid] += 0.5

    def generate_random_pairings(self) -> List[Tuple[str, str]]:
        """Generate random pairings for the first round."""
        if len(self.player_list) % 2 != 0:
            raise ValueError("Pairings require an even number of players.")

        items = [player.national_chess_identifier for player in self.player_list]
        shuffle(items)

        new_matches = [(items[i], items[i + 1]) for i in range(0, len(items), 2)]
        for player_1_ncid, player_2_ncid in new_matches:
            key = self._normalize_match_key(player_1_ncid, player_2_ncid)
            self.seen_matches[key] = self.seen_matches.get(key, 0) + 1

        return new_matches

    def generate_pairings(self, number_of_round: int = -1) -> List[Tuple[str, str]]:
        """
        Generate pairings following the project rules:
        - First round is random.
        - Next rounds are based on players points.
        - Players with equal points are shuffled before pairing.
        - Try to avoid rematches.
        """
        if len(self.player_list) % 2 != 0:
            raise ValueError("Pairings require an even number of players.")

        if number_of_round == -1:
            number_of_round = self.current_round + 1
        self.current_round = number_of_round

        # First round is random whether caller uses 0-based or 1-based round numbers.
        if self.current_round <= 1:
            return self.generate_random_pairings()

        self._hydrate_seen_matches_from_history()
        self._refresh_player_points()

        points_by_player: Dict[str, float] = dict(self.player_points)

        grouped_players: Dict[float, List[Player]] = {}
        for player in self.player_list:
            player_points = points_by_player[player.national_chess_identifier]
            grouped_players.setdefault(player_points, []).append(player)

        sorted_points = sorted(grouped_players.keys(), reverse=True)
        ordered_players: List[Player] = []
        for points in sorted_points:
            players_group = grouped_players[points]
            shuffle(players_group)
            ordered_players.extend(players_group)

        pairings: List[Tuple[str, str]] = []
        remaining_players = ordered_players[:]
        while len(remaining_players) >= 2:
            player_1 = remaining_players.pop(0)
            player_1_ncid = player_1.national_chess_identifier

            opponent_index = 0
            for idx, candidate in enumerate(remaining_players):
                key = self._normalize_match_key(
                    player_1_ncid, candidate.national_chess_identifier
                )
                if key not in self.seen_matches:
                    opponent_index = idx
                    break

            player_2 = remaining_players.pop(opponent_index)
            player_2_ncid = player_2.national_chess_identifier
            pairings.append((player_1_ncid, player_2_ncid))

            key = self._normalize_match_key(player_1_ncid, player_2_ncid)
            self.seen_matches[key] = self.seen_matches.get(key, 0) + 1

        return pairings
