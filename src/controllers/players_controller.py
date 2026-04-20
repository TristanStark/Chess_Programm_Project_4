from pathlib import Path
from src.models.players import Player
from typing import List, Optional
from src.models.tournaments import Tournament


class PlayersController:
    """
    Controller class for managing Player objects, adhering to the MVC pattern.
    It handles the business logic and mediates between the view (if one existed)
    and the model (Player).
    """

    def __init__(self, players_directory: Path):
        """
        Initializes the controller with the directory where player data is stored.

        :param players_directory: The directory path to store/load player JSON files.
        """
        self.players_directory = players_directory
        # Ensure the directory exists
        self.players_directory.mkdir(parents=True, exist_ok=True)

    def can_create_player(
        self,
        current_tournament: Tournament | None,
    ) -> tuple[bool, str]:
        if self._is_tournament_ongoing(current_tournament):
            return False, "Cannot create a player while tournament is ongoing."
        return True, ""

    def can_add_player_to_tournament(
        self,
        tournament: Tournament | None,
    ) -> tuple[bool, str]:
        if tournament is None:
            return False, "No active tournament."
        if self._is_tournament_ongoing(tournament):
            return False, "Cannot add a player while tournament is ongoing."
        return True, ""

    def can_remove_player_from_tournament(
        self,
        tournament: Tournament | None,
        player: Player | None,
    ) -> tuple[bool, str]:
        if tournament is None:
            return False, "No active tournament."
        if self._is_tournament_ongoing(tournament):
            return False, "Cannot remove a player while tournament is ongoing."
        if not tournament.players:
            return False, "No player in the tournament."
        if player is None:
            return False, "No player selected."
        return True, ""

    def create_player(self, first_name: str, last_name: str,
                      date_of_birth: str,
                      national_chess_identifier: str) -> Optional[Player]:
        """
        Creates a new Player instance and validates it.

        :param first_name: The first name of the player.
        :param last_name: The last name of the player.
        :param date_of_birth: The date of birth of the player (string).
        :param national_chess_identifier: The unique national chess identifier.
        :return: A Player object if valid, otherwise None.
        """
        player = Player(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            national_chess_identifier=national_chess_identifier
        )

        if player.check_validity():
            print(f"Successfully created valid player: {player}")
            return player
        else:
            print("Error: Provided player data is invalid.")
            return None

    def save_player(self, player: Player, filename: str) -> Path:
        """
        Saves a validated Player object to a JSON file within the players directory.

        :param player: The Player object to save.
        :param filename: The desired filename for the JSON output.
        :return: The Path object to the saved file.
        :raises ValueError: If the player is invalid before saving.
        """
        if not player.check_validity():
            raise ValueError("Cannot save player: Player data is invalid.")

        file_path = self.players_directory / f"{filename}.json"
        player.save(file_path)
        print(f"Player successfully saved to {file_path}")
        return file_path

    def load_player(self, filename: str) -> Optional[Player]:
        """
        Loads a Player object from a specified JSON file.

        :param filename: The name of the file (without extension).
        :return: The loaded Player object, or None if the file does not exist.
        """
        file_path = self.players_directory / f"{filename}.json"
        if not file_path.exists():
            print(f"Error: Player file not found at {file_path}")
            return None

        try:
            player = Player.load(file_path)
            print(f"Player successfully loaded from {file_path}")
            return player
        except Exception as e:
            print(f"Error loading player from {file_path}: {e}")
            return None

    def get_all_players(self) -> List[Player]:
        """
        Loads all player objects from the players directory.

        :return: A list of Player objects.
        """
        player_files = list(self.players_directory.glob("*.json"))
        players: List[Player] = []
        for file_path in player_files:
            # Extract filename without extension for cleaner reporting/usage
            filename = file_path.stem
            player = self.load_player(filename)
            if player:
                players.append(player)
        return players

    @staticmethod
    def _is_tournament_ongoing(tournament: Tournament | None) -> bool:
        if tournament is None:
            return False
        return str(getattr(tournament, "status", "")).strip().lower() == "ongoing"


# Example usage (can be removed or moved to a dedicated test file)
if __name__ == '__main__':
    # Setup: Create a dummy directory for testing
    test_dir = Path("test_player_data")
    test_dir.mkdir(exist_ok=True)

    controller = PlayersController(players_directory=test_dir)

    # 1. Test Creation
    valid_player = controller.create_player(
        first_name="Magnus",
        last_name="Carlsen",
        date_of_birth="1992-03-30",
        national_chess_identifier="ENG123456"  # Assuming this format check passes for demo
    )

    if valid_player:
        # 2. Test Saving
        try:
            saved_path = controller.save_player(valid_player, "magnus_carlsen")
            print(f"Saved path check: {saved_path}")
        except ValueError as e:
            print(f"Saving failed: {e}")

        # 3. Test Loading
        loaded_player = controller.load_player("magnus_carlsen")
        if loaded_player:
            print(f"Verification: Loaded player name is {loaded_player}")

    # Clean up (optional)
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    print("\nCleanup complete.")
