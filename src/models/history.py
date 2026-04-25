from dataclasses import dataclass


@dataclass
class MatchHistory:
    opponent: str
    winner: str
    start_date: str
    end_date: str
