from dataclasses import dataclass
from src.models.players import Player
from datetime import datetime
from typing import List


"""
At the end of the match, players get points based on their results:
- The winner gets 1 point.
- The loser gets 0 points.
- Each player gets 0.5 points if the match ends in a tie.
"""


@dataclass
class Score:
    player: Player
    score: float  # Since whe can have 0.5 points we cannot use int ):


@dataclass
class Match:
    player1: Score
    player2: Score
    status: str = "not_started"

    def __post_init__(self) -> None:
        normalized = str(self.status).strip().lower()
        if normalized not in {"not_started", "ongoing", "finished"}:
            normalized = "not_started"
        self.status = normalized


@dataclass
class Round:
    name: str
    matches: List[Match]
    start_date: datetime
    end_date: datetime
