"""Public API for controllers package."""

from .match_controller import MatchController
from .pairings_generator import PairingGenerator
from .player_controller import PlayerController
from .players_controller import PlayersController
from .round_controller import RoundController
from .settings import debug_print, is_debug, set_debug, toggle_debug
from .tournament_controller import TournamentController
from .tournament_pairing_service import TournamentPairingService
from .tournament_persistence_service import TournamentPersistenceService
from .view_contracts import MatchesViewProtocol, PlayerInfoViewProtocol, RoundsViewProtocol

__all__ = [
    "MatchController",
    "MatchesViewProtocol",
    "PairingGenerator",
    "PlayerController",
    "PlayerInfoViewProtocol",
    "PlayersController",
    "RoundController",
    "RoundsViewProtocol",
    "TournamentController",
    "TournamentPairingService",
    "TournamentPersistenceService",
    "debug_print",
    "is_debug",
    "set_debug",
    "toggle_debug",
]
