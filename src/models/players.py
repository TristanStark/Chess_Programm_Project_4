from pathlib import Path
import json
from dataclasses import asdict
from src.models.history import MatchHistory
from typing import Dict, Optional, Any, Union


class Player():
    def __init__(self, first_name: str, last_name: str, date_of_birth: str,
                 national_chess_identifier: str, 
                 tournament_history: Optional[Dict[str, MatchHistory]] = None):
        self.first_name: str = first_name
        self.last_name : str = last_name
        self.date_of_birth : str = date_of_birth
        self.national_chess_identifier : str  = national_chess_identifier
        self.tournament_history: Dict[str, MatchHistory] = tournament_history or {}

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.date_of_birth})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "national_chess_identifier": self.national_chess_identifier,
            "tournament_history": {
                tournament_id: (
                    asdict(history_entry)
                    if isinstance(history_entry, MatchHistory)
                    else history_entry
                )
                for tournament_id, history_entry in self.tournament_history.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        required_keys = ("first_name", "last_name", "date_of_birth")
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise KeyError(f"Missing required player fields: {', '.join(missing_keys)}")

        ncid = data.get("national_chess_identifier") or data.get("ncid")
        if ncid is None:
            raise KeyError("Missing required player field: national_chess_identifier")

        raw_history = data.get("tournament_history", {})
        tournament_history: Dict[str, MatchHistory] = {}

        if isinstance(raw_history, dict):
            for tournament_id, entry in raw_history.items():
                if isinstance(entry, MatchHistory):
                    tournament_history[tournament_id] = entry
                    continue
                if isinstance(entry, dict):
                    tournament_history[tournament_id] = MatchHistory(
                        opponent=str(entry.get("opponent", "")),
                        winner=str(entry.get("winner", "")),
                        start_date=str(entry.get("start_date", "")),
                        end_date=str(entry.get("end_date", "")),
                    )

        return cls(
            first_name=str(data["first_name"]),
            last_name=str(data["last_name"]),
            date_of_birth=str(data["date_of_birth"]),
            national_chess_identifier=str(ncid),
            tournament_history=tournament_history,
        )

    def save(self, json_file: Union[Path, str]):
        file_path = Path(json_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls, json_file: Union[Path, str]) -> "Player":
        file_path = Path(json_file)
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return cls.from_dict(data)

    def is_ncid_valid(self):
        # Code to check if the national chess identifier is valid
        valid = len(self.national_chess_identifier) == 7
        valid = valid and self.national_chess_identifier[2:].isdigit()
        valid = valid and self.national_chess_identifier[:2].isalpha()
        return valid

    def check_validity(self):
        # Code to check if the player's data is valid
        if not self.first_name or not self.last_name:
            return False
        if not self.date_of_birth:
            return False
        if not self.national_chess_identifier:
            return False
        if not self.is_ncid_valid():
            return False
        return True
