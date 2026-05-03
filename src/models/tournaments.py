import json
from datetime import datetime
from pathlib import Path
from typing import List

from src.models.matches import Match, Round, Score
from src.models.players import Player

"""
TOURNAMENT ATTRIBUTES
Each tournament should hold at least the following information:
- A name
- A venue
- A start and end date
- A number of rounds; set the default value to 4.
- A number corresponding to the current round being played OR A list of round
instances.
- A list of registered players OR A list of indices corresponding to the player
instances stored in memory.
- A description for general text remarks by the tournament manager.
"""


class Tournament:
    def __init__(self, name: str, venue: str, start_date: datetime,
                 end_date: datetime, description: str, players: List[Player],
                 rounds: List[Round], number_of_rounds: int = 4,
                 automatic_pairings: bool = True):
        self.name = name
        self.venue = venue
        self.start_date = start_date
        self.end_date = end_date

        self.number_of_rounds = number_of_rounds
        self.automatic_pairings = bool(automatic_pairings)
        self.description = description
        self.players = players
        self.rounds = rounds
        self.status = "Not started"  # Possible values: "Not started", "Ongoing", "Completed"


def create_tournament_from_file(file_path: str) -> Tournament:
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    players = [Player.from_dict(player_data) for player_data in payload.get("players", [])]
    players_by_ncid = {
        player.national_chess_identifier: player
        for player in players
    }

    rounds: List[Round] = []
    for index, round_data in enumerate(payload.get("rounds", []), start=1):
        matches: List[Match] = []
        for match_data in round_data.get("matches", []):
            player_1_data = match_data.get("player1", {}).get("player", {})
            player_2_data = match_data.get("player2", {}).get("player", {})

            player_1 = players_by_ncid.get(player_1_data.get("national_chess_identifier"))
            player_2 = players_by_ncid.get(player_2_data.get("national_chess_identifier"))
            if player_1 is None or player_2 is None:
                raise ValueError(f"Unknown player reference in round #{index}.")

            matches.append(
                Match(
                    player1=Score(player_1, float(match_data.get("player1", {}).get("score", 0.0))),
                    player2=Score(player_2, float(match_data.get("player2", {}).get("score", 0.0))),
                    status=str(match_data.get("status", "not_started")),
                )
            )

        rounds.append(
            Round(
                name=str(round_data.get("name", f"Round {index}")),
                matches=matches,
                start_date=datetime.strptime(str(round_data["start_date"]), "%Y-%m-%d %H:%M:%S"),
                end_date=datetime.strptime(str(round_data["end_date"]), "%Y-%m-%d %H:%M:%S"),
                status=str(round_data.get("status", "not_started")),
            )
        )

    tournament = Tournament(
        name=str(payload["name"]),
        venue=str(payload["venue"]),
        start_date=datetime.strptime(str(payload["start_date"]), "%Y-%m-%d %H:%M:%S"),
        end_date=datetime.strptime(str(payload["end_date"]), "%Y-%m-%d %H:%M:%S"),
        description=str(payload.get("description", "")),
        players=players,
        rounds=rounds,
        number_of_rounds=int(payload.get("number_of_rounds", 4)),
        automatic_pairings=bool(payload.get("automatic_pairings", True)),
    )
    tournament.status = str(payload.get("status", "Not started"))
    return tournament
