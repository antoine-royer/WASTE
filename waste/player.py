"""Manage player."""

import json
import os

with open("waste/data/special.json", "r", encoding="utf-8") as datafile:
    SPECIAL = json.load(datafile)

with open("waste/data/origins.json", "r", encoding="utf-8") as datafile:
    ORIGINS = json.load(datafile)

with open("waste/data/skills.json", "r", encoding="utf-8") as datafile:
    SKILLS = json.load(datafile)

with open("waste/data/perks.json", "r", encoding="utf-8") as datafile:
    PERKS = json.load(datafile)


class Player:
    """Player class that handle the interface between files and players in the script."""

    def __init__(self, filename: str, name: str, data: dict, skills: dict, perks: dict):
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
        skills : dict
            The skills of the player: {id: [value (int), tagged (bool)], ...}.
        perks : dict
            The perks of the player: {id: rank (int), ...}.
        """
        self.filename = filename
        self.name = name
        self.data = data
        self.skills = skills
        self.perks = perks

    def __getitem__(self, item: str):
        """Return requested data on player."""
        if item.lower() in SPECIAL.keys():
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
            self.perks = player_data["PERKS"]

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
            "PERKS": self.perks,
        }
        with open(self.filename, "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=8))

    def check_requirements(self, requirements: list):
        """
        Check if the player meet the given requirements.

        Parameters
        ----------
        requirements : list
            The list of requirements to meet like: ["NAME": min_value]. "NAME" can be:
            - a short form of S.P.E.C.I.A.L. ("STR", "PER", "END", "CHA", "INT", "AGI", "LCK")
            - "LVL" : the level of the player
            - "ORIGIN" : the origin of the player
            The min_value is the minimum value, it can also be a list of authorized values.
        """
        return False not in [
            (
                self[requirement_name] in requirement_level
                if isinstance(requirement_level, int)
                else self[requirement_name] >= requirement_level
            )
            for requirement_name, requirement_level in requirements
        ]


def new_player():
    """Create a new player, returns a Player's instance."""
    return Player(
        "",
        "Nouveau Joueur",
        {"LVL": 1, "ORIGIN": -1, "SPECIAL": {key.upper(): 5 for key in SPECIAL.keys()}},
        {},
        {},
    )
