from typing import Protocol, runtime_checkable


@runtime_checkable
class MatchesViewProtocol(Protocol):
    def clear_matches(self) -> None: ...

    def add_match(
        self,
        player_1_name,
        player_1_score,
        player_2_name,
        player_2_score,
        status="not_started",
    ) -> None: ...

    def update_match_status(self, index: int, status: str) -> None: ...


@runtime_checkable
class RoundsViewProtocol(Protocol):
    round_status_label: object

    def clear_rounds(self) -> None: ...

    def add_round_row(self, text, status="not_started", match_status_summary: str = "") -> None: ...

    def update_round_status(self, index: int, status: str, match_status_summary: str = "") -> None: ...


@runtime_checkable
class PlayerInfoViewProtocol(Protocol):
    def set_player_info(self, **kwargs) -> None: ...

    def clear(self) -> None: ...
