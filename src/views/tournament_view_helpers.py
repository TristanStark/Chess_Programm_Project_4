from pathlib import Path
import re


def build_player_filename(first_name: str, last_name: str, ncid: str) -> str:
    raw_value = f"{first_name}_{last_name}_{ncid}"
    sanitized = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_value).strip("_").lower()
    return sanitized or "player"


def next_available_player_filename(players_directory: Path, base_filename: str) -> str:
    candidate = base_filename
    suffix = 2
    while (players_directory / f"{candidate}.json").exists():
        candidate = f"{base_filename}_{suffix}"
        suffix += 1
    return candidate


def format_player_option_label(player) -> str:
    first_name = getattr(player, "first_name", "")
    last_name = getattr(player, "last_name", "")
    ncid = getattr(player, "national_chess_identifier", "")
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return f"{full_name} [{ncid}]"
    return str(player)


def format_player_name(player) -> str:
    first_name = getattr(player, "first_name", "")
    last_name = getattr(player, "last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    return full_name if full_name else str(player)
