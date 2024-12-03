"""Manage player."""

import json
import os

SPECIAL = ("str", "per", "end", "cha", "int", "agi", "lck")
SKILLS = (
    "Armes à énergie",
    "Armes de corps à corps",
    "Armes légères",
    "Armes lourdes",
    "Athlétisme",
    "Crochetage",
    "Discours",
    "Discrétion",
    "Explosifs",
    "Mains nues",
    "Médecine",
    "Pilotage",
    "Projectiles",
    "Réparation",
    "Science",
    "Survie",
    "Troc",
)


class Player:
    """Player class that handle the interface between files and players in the script."""

    def __init__(self, filename: str, name: str, data: dict, skills: list):
        """
        Constructor method.

        Parameters
        ----------
        filename : str
            The path and name of the save file.
        name : str
            The name of the player.
        data : dict
            The dictionnary that contains the data of the player as:

                {
                    "LVL": player_level,  # (int)
                    "ORIGIN": player_origin,  # (int)
                    "SPECIAL": player_special  # (dict)
                }
        """
        self.filename = filename
        self.name = name
        self.data = data
        self.skills = skills

    def __getitem__(self, item: str):
        """Return requested data on player."""
        if item.lower() in SPECIAL:
            return self.data["SPECIAL"][item]
        return self.data[item]

    def restore_from_file(self):
        """Overwrite the Player's instance with the content of the reference file for the player."""
        with open(self.filename, "r", encoding="utf-8") as file:
            player_data = json.load(file)
            self.name = player_data["NAME"]
            self.data = {
                "LVL": player_data["LVL"],
                "ORIGIN": player_data["ORIGIN"],
                "SPECIAL": player_data["SPECIAL"],
            }
            self.skills = player_data["SKILLS"]

    def save_in_file(self):
        """Save the player's data into its file."""
        if not self.filename:
            self.filename = f"waste/players/player_{len(os.listdir("waste/players/")) + 1}.json"

        data = {
            "NAME": self.name,
            "LVL": self.data["LVL"],
            "ORIGIN": self.data["ORIGIN"],
            "SPECIAL": self.data["SPECIAL"],
            "SKILLS": self.skills,
        }
        with open(self.filename, "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=8))


def new_player():
    """Create a new player, returns a Player's instance."""
    return Player(
        "",
        "Nouveau Joueur",
        {"LVL": 1, "ORIGIN": -1, "SPECIAL": {key.upper(): 5 for key in SPECIAL}},
        [[0, 0] for _ in range(len(SKILLS))],
    )
