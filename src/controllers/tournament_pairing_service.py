from __future__ import annotations

from src.controllers.pairings_generator import PairingGenerator
from src.models.matches import Match, Round, Score
from src.models.players import Player
from src.models.tournaments import Tournament


class TournamentPairingService:
    def __init__(self) -> None:
        self._pairing_generators: dict[int, PairingGenerator] = {}

    @staticmethod
    def uses_automatic_pairings(tournament: Tournament | None) -> bool:
        if tournament is None:
            return True
        return bool(getattr(tournament, "automatic_pairings", True))

    def initialize_pairing_generator(self, tournament: Tournament) -> None:
        pairing_generator = PairingGenerator(tournament.players)
        pairing_generator.set_players(tournament.players)
        pairing_generator.current_round = len(tournament.rounds)
        self._pairing_generators[id(tournament)] = pairing_generator

    def update_pairing_generator_after_match(
        self,
        tournament: Tournament | None,
        match: Match | None,
        result: str,
    ) -> None:
        if tournament is None or match is None:
            return
        pairing_generator = self._pairing_generators.get(id(tournament))
        if pairing_generator is None:
            return
        pairing_generator.update_after_match(
            match.player1.player.national_chess_identifier,
            match.player2.player.national_chess_identifier,
            result,
        )

    def generate_next_round_if_possible(self, tournament: Tournament | None) -> bool:
        if tournament is None:
            return False
        if not self.uses_automatic_pairings(tournament):
            return False

        total_rounds = int(tournament.number_of_rounds)
        if total_rounds <= 0:
            return False
        if len(tournament.rounds) >= total_rounds:
            return False

        if tournament.rounds and tournament.rounds[-1].status != "finished":
            return False

        pairing_generator = self._pairing_generators.get(id(tournament))
        if pairing_generator is None:
            pairing_generator = PairingGenerator(tournament.players)
            self._pairing_generators[id(tournament)] = pairing_generator

        pairing_generator.set_players(tournament.players)
        next_round_number = len(tournament.rounds) + 1
        pairings = pairing_generator.generate_pairings(number_of_round=next_round_number)
        players_by_ncid: dict[str, Player] = {
            player.national_chess_identifier: player for player in tournament.players
        }

        matches: list[Match] = []
        for player_1_ncid, player_2_ncid in pairings:
            player_1 = players_by_ncid.get(player_1_ncid)
            player_2 = players_by_ncid.get(player_2_ncid)
            if player_1 is None or player_2 is None:
                raise ValueError("Generated pairing includes unknown player.")
            matches.append(
                Match(
                    player1=Score(player=player_1, score=0.0),
                    player2=Score(player=player_2, score=0.0),
                    status="not_started",
                )
            )

        tournament.rounds.append(
            Round(
                name=f"Round {next_round_number}",
                matches=matches,
                start_date=tournament.start_date,
                end_date=tournament.end_date,
                status="not_started",
            )
        )
        return True

    def create_manual_round(
        self,
        tournament: Tournament | None,
        *,
        round_name: str,
        pairings: list[tuple[str, str]],
    ) -> tuple[bool, str]:
        if tournament is None:
            return False, "No active tournament."
        if len(tournament.rounds) >= int(tournament.number_of_rounds):
            return False, "All rounds have already been created."
        if tournament.rounds and tournament.rounds[-1].status != "finished":
            return False, "Previous round must be finished first."

        normalized_round_name = str(round_name).strip()
        if not normalized_round_name:
            return False, "Round name is required."

        expected_matches = len(tournament.players) // 2
        if len(pairings) != expected_matches:
            return False, f"Expected {expected_matches} matches."

        players_by_ncid = {
            player.national_chess_identifier: player for player in tournament.players
        }

        seen_players: set[str] = set()
        matches: list[Match] = []
        for player_1_ncid, player_2_ncid in pairings:
            if player_1_ncid == player_2_ncid:
                return False, "A player cannot be paired against themselves."
            if player_1_ncid not in players_by_ncid or player_2_ncid not in players_by_ncid:
                return False, "Pairings contain unknown players."
            if player_1_ncid in seen_players or player_2_ncid in seen_players:
                return False, "Each player must appear exactly once."

            seen_players.add(player_1_ncid)
            seen_players.add(player_2_ncid)
            matches.append(
                Match(
                    player1=Score(player=players_by_ncid[player_1_ncid], score=0.0),
                    player2=Score(player=players_by_ncid[player_2_ncid], score=0.0),
                    status="not_started",
                )
            )

        if len(seen_players) != len(tournament.players):
            return False, "Each tournament player must be paired exactly once."

        tournament.rounds.append(
            Round(
                name=normalized_round_name,
                matches=matches,
                start_date=tournament.start_date,
                end_date=tournament.end_date,
                status="not_started",
            )
        )
        return True, ""
