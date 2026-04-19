from src.models.matches import Round
from datetime import datetime
from typing import List
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
                 rounds: List[Round], number_of_rounds: int = 4):
        self.name = name
        self.venue = venue
        self.start_date = start_date
        self.end_date = end_date

        self.number_of_rounds = number_of_rounds
        self.description = description
        self.players = players
        self.rounds = rounds
        self.status = "Not started"  # Possible values: "Not started", "Ongoing", "Completed"


def create_tournament_from_file(file_path: str) -> Tournament:
    # Code to create a Tournament instance from a file (e.g., JSON, CSV)
    pass
