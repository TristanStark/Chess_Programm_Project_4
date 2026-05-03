from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.exporters.report_renderer import ReportRenderer


@dataclass(frozen=True)
class ReportOption:
    report_id: str
    label: str
    template_name: str
    requires_tournament: bool = False


class TournamentReportExporter:
    REPORT_OPTIONS: tuple[ReportOption, ...] = (
        ReportOption(
            report_id="players_alphabetical",
            label="The list of all players, sorted alphabetically",
            template_name="player_list_report_template.html",
        ),
        ReportOption(
            report_id="all_tournaments",
            label="The list of all tournaments",
            template_name="tournament_list_report_template.html",
        ),
        ReportOption(
            report_id="selected_tournament_name_dates",
            label="The name and dates of a given tournament",
            template_name="selected_tournament_name_dates_report_template.html",
            requires_tournament=True,
        ),
        ReportOption(
            report_id="selected_tournament_players",
            label="The list of players participating in the tournament, sorted alphabetically",
            template_name="selected_tournament_players_report_template.html",
            requires_tournament=True,
        ),
        ReportOption(
            report_id="selected_tournament_rounds_matches",
            label="The list of all rounds in the tournament and all matches in the round",
            template_name="selected_tournament_rounds_matches_report_template.html",
            requires_tournament=True,
        ),
    )

    def __init__(
        self,
        *,
        players_controller,
        tournament_controller,
        templates_directory: Path | str,
        exports_directory: Path | str,
    ) -> None:
        self.players_controller = players_controller
        self.tournament_controller = tournament_controller
        self.templates_directory = Path(templates_directory)
        self.exports_directory = Path(exports_directory)
        self.renderer = ReportRenderer(self.templates_directory)
        self.exports_directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_report_options(cls) -> tuple[ReportOption, ...]:
        return cls.REPORT_OPTIONS

    @classmethod
    def get_report_option_by_id(cls, report_id: str) -> ReportOption | None:
        for option in cls.REPORT_OPTIONS:
            if option.report_id == report_id:
                return option
        return None

    def build_default_output_path(self, report_option: ReportOption, selected_tournament=None) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = report_option.report_id
        if selected_tournament is not None:
            tournament_name = self._safe_fragment(getattr(selected_tournament, "name", "tournament"))
            base_name = f"{base_name}_{tournament_name}"
        return self.exports_directory / f"{base_name}_{timestamp}.html"

    def export_report(
        self,
        *,
        report_option: ReportOption,
        output_path: Path | str,
        selected_tournament=None,
    ) -> tuple[bool, str, Path | None]:
        if report_option.requires_tournament and selected_tournament is None:
            return False, "A tournament selection is required for this report.", None

        try:
            all_players = self._load_all_players()
            tournaments = self._load_all_tournaments()
            selected_players = self._load_selected_players(selected_tournament)

            context = {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "page_title": report_option.label,
                "report_title": report_option.label,
                "players": all_players,
                "all_players": all_players,
                "tournaments": tournaments,
                "total_players": sum(len(tournament.get("players", [])) for tournament in tournaments),
                "total_rounds": sum(int(tournament.get("number_of_rounds", 0)) for tournament in tournaments),
                "selected_tournament": (
                    self._serialize_tournament(selected_tournament) if selected_tournament else None
                ),
                "selected_players": selected_players,
            }

            rendered_html = self.renderer.render(report_option.template_name, context)
            destination = Path(output_path)
            if destination.suffix.lower() != ".html":
                destination = destination.with_suffix(".html")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(rendered_html, encoding="utf-8")
            return True, f"Report exported to '{destination.name}'.", destination
        except Exception as exc:
            return False, f"Failed to export report: {exc}", None

    def _load_all_players(self) -> list[dict]:
        players = self.players_controller.get_all_players()
        players.sort(key=lambda player: (
            str(getattr(player, "last_name", "")).lower(),
            str(getattr(player, "first_name", "")).lower(),
        ))
        return [self._serialize_player(player) for player in players]

    def _load_all_tournaments(self) -> list[dict]:
        tournaments: list[dict] = []
        for file_path in sorted(self.tournament_controller.tournaments_directory.glob("*.json")):
            success, _message, tournament = self.tournament_controller.load_tournament_from_json(file_path)
            if not success or tournament is None:
                continue
            tournaments.append(self._serialize_tournament(tournament))

        tournaments.sort(key=lambda tournament: (
            str(tournament.get("name", "")).lower(),
            str(tournament.get("start_date", "")),
        ))
        return tournaments

    def _load_selected_players(self, selected_tournament) -> list[dict]:
        if selected_tournament is None:
            return []
        players = list(getattr(selected_tournament, "players", []))
        players.sort(key=lambda player: (
            str(getattr(player, "last_name", "")).lower(),
            str(getattr(player, "first_name", "")).lower(),
        ))
        return [self._serialize_player(player) for player in players]

    def _serialize_tournament(self, tournament) -> dict:
        tournament_players = list(getattr(tournament, "players", []))
        rounds = [self._serialize_round(round_) for round_ in getattr(tournament, "rounds", [])]
        points_by_player = self._compute_total_points_by_player(getattr(tournament, "rounds", []))
        status = str(getattr(tournament, "status", ""))
        serialized_players = [
            self._serialize_player(
                player,
                total_points=points_by_player.get(getattr(player, "national_chess_identifier", ""), 0.0),
            )
            for player in tournament_players
        ]
        return {
            "name": str(getattr(tournament, "name", "")),
            "venue": str(getattr(tournament, "venue", "")),
            "start_date": self._format_date(getattr(tournament, "start_date", "")),
            "end_date": self._format_date(getattr(tournament, "end_date", "")),
            "number_of_rounds": int(getattr(tournament, "number_of_rounds", 0) or 0),
            "status": status,
            "description": str(getattr(tournament, "description", "")),
            "players": serialized_players,
            "podium": self._build_podium(
                players=tournament_players,
                points_by_player=points_by_player,
                status=status,
            ),
            "rounds": rounds,
            "match_count": sum(len(round_data["matches"]) for round_data in rounds),
        }

    def _serialize_round(self, round_) -> dict:
        return {
            "name": str(getattr(round_, "name", "")),
            "start_date": self._format_date(getattr(round_, "start_date", "")),
            "end_date": self._format_date(getattr(round_, "end_date", "")),
            "status": str(getattr(round_, "status", "")),
            "matches": [self._serialize_match(match) for match in getattr(round_, "matches", [])],
        }

    def _serialize_match(self, match) -> dict:
        return {
            "player1": {
                "player": self._serialize_player(getattr(getattr(match, "player1", None), "player", None)),
                "score": float(getattr(getattr(match, "player1", None), "score", 0.0)),
            },
            "player2": {
                "player": self._serialize_player(getattr(getattr(match, "player2", None), "player", None)),
                "score": float(getattr(getattr(match, "player2", None), "score", 0.0)),
            },
            "status": str(getattr(match, "status", "")),
        }

    @staticmethod
    def _serialize_player(player, total_points: float | None = None) -> dict:
        if player is None:
            return {
                "first_name": "",
                "last_name": "",
                "date_of_birth": "",
                "national_chess_identifier": "",
                "total_points": 0.0,
            }
        payload = {
            "first_name": str(getattr(player, "first_name", "")),
            "last_name": str(getattr(player, "last_name", "")),
            "date_of_birth": str(getattr(player, "date_of_birth", "")),
            "national_chess_identifier": str(getattr(player, "national_chess_identifier", "")),
        }
        if total_points is not None:
            payload["total_points"] = float(total_points)
        return payload

    def _compute_total_points_by_player(self, rounds) -> dict[str, float]:
        totals: dict[str, float] = {}
        for round_ in rounds:
            for match in getattr(round_, "matches", []):
                player_1 = getattr(getattr(match, "player1", None), "player", None)
                player_2 = getattr(getattr(match, "player2", None), "player", None)
                player_1_ncid = str(getattr(player_1, "national_chess_identifier", ""))
                player_2_ncid = str(getattr(player_2, "national_chess_identifier", ""))
                player_1_score = float(getattr(getattr(match, "player1", None), "score", 0.0))
                player_2_score = float(getattr(getattr(match, "player2", None), "score", 0.0))
                if player_1_ncid:
                    totals[player_1_ncid] = totals.get(player_1_ncid, 0.0) + player_1_score
                if player_2_ncid:
                    totals[player_2_ncid] = totals.get(player_2_ncid, 0.0) + player_2_score
        return totals

    def _build_podium(
        self,
        *,
        players,
        points_by_player: dict[str, float],
        status: str,
    ) -> list[dict]:
        if str(status).strip().lower() != "completed":
            return []

        ordered_players = sorted(
            players,
            key=lambda player: (
                -float(points_by_player.get(getattr(player, "national_chess_identifier", ""), 0.0)),
                str(getattr(player, "last_name", "")).lower(),
                str(getattr(player, "first_name", "")).lower(),
                str(getattr(player, "national_chess_identifier", "")).lower(),
            ),
        )

        podium: list[dict] = []
        for place in (1, 2, 3):
            index = place - 1
            if index >= len(ordered_players):
                break
            player = ordered_players[index]
            ncid = str(getattr(player, "national_chess_identifier", ""))
            points = float(points_by_player.get(ncid, 0.0))
            first_name = str(getattr(player, "first_name", "")).strip()
            last_name = str(getattr(player, "last_name", "")).strip()
            display_name = f"{first_name} {last_name}".strip() or ncid
            podium.append(
                {
                    "place": place,
                    "name": display_name,
                    "points": self._format_points(points),
                }
            )
        return podium

    @staticmethod
    def _format_date(value) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        return str(value)

    @staticmethod
    def _safe_fragment(value: str) -> str:
        safe = "".join(character if character.isalnum() else "_" for character in value).strip("_")
        return safe.lower() or "tournament"

    @staticmethod
    def _format_points(points: float) -> str:
        points_value = float(points)
        if points_value.is_integer():
            return str(int(points_value))
        return f"{points_value:.1f}"
