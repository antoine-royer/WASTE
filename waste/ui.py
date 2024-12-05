"""Handle all the signals from the UI."""

import json
import os

import gi

from waste.player import ORIGINS, PERKS, SKILLS, SPECIAL, Player, new_player

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

LVL_NAME = "LVL"
ORIGIN_NAME = "ORIGIN"
DN_INDEX = 54  # Daring Nature index in PERKS list
CN_INDEX = 55  # Cautious Nature index in PERKS list


class MainHandler:
    """Handle all the signals from the UI."""

    def __init__(self, builder):
        """Constructor."""
        self.builder = builder
        self.players = []

        self.on_update_player_clicked()

    def on_add_player_clicked(self, *_):
        """Add a new player."""
        player = new_player()
        player.save_in_file()
        edit_player(player)
        self.players.append(player)
        self.__update_players_grid()

    def on_update_player_clicked(self, *_):
        """Get all the players' file detected and display them all."""
        # Clean the registered players
        self.players = []

        # Add all the files
        for player in os.listdir("waste/players/"):
            with open(f"waste/players/{player}", "r", encoding="utf-8") as file:
                player_data = json.load(file)
                self.players.append(
                    Player(
                        f"waste/players/{player}",
                        player_data["NAME"],
                        {
                            "LVL": player_data["LVL"],
                            "ORIGIN": player_data["ORIGIN"],
                            "SPECIAL": player_data["SPECIAL"],
                        },
                        player_data["SKILLS"],
                        player_data["PERKS"],
                    )
                )

        # Update the players' grid on the UI
        self.__update_players_grid()

    def on_edit_player_clicked(self, _, identifier: int):
        """Edit an existing player."""
        edit_player(self.players[identifier])
        self.__update_players_grid()

    def on_suppr_player_clicked(self, _, identifier: int):
        """
        Delete an existing player. The player's file will not be deleted, but it will be no
        longer displayed.
        """
        self.players.pop(identifier)
        self.__update_players_grid()

    def on_permanent_delete_clicked(self, _, identifier):
        """
        Delete an existing player. The player's file will be deleted too.
        """
        dialog = ConfirmationDialog(self.builder.get_object("main_window"))
        if dialog.run() == Gtk.ResponseType.OK:
            os.remove(self.players[identifier].filename)
            self.players.pop(identifier)
            self.__update_players_grid()

        dialog.destroy()

    def __update_players_grid(self):
        """Update the players' grid with the registered players."""
        # Get the players' grid
        players_grid = self.builder.get_object("players_grid")

        # Clean the grid
        for child in players_grid.get_children():
            players_grid.remove(child)

        # Display the registered players
        for index, player in enumerate(self.players):
            name = Gtk.Label()
            name.set_markup(player.name)
            players_grid.attach(name, 0, index + 1, 1, 1)

            edit = Gtk.Button(label="Modifier", image=Gtk.Image(stock=Gtk.STOCK_EDIT))
            edit.set_always_show_image(True)
            edit.connect("clicked", self.on_edit_player_clicked, index)
            players_grid.attach(edit, 1, index + 1, 1, 1)

            suppr = Gtk.Button(label="Enlever", image=Gtk.Image(stock=Gtk.STOCK_CLEAR))
            suppr.set_always_show_image(True)
            suppr.connect("clicked", self.on_suppr_player_clicked, index)
            players_grid.attach(suppr, 2, index + 1, 1, 1)

            permanent_delete = Gtk.Button(label="Effacer", image=Gtk.Image(stock=Gtk.STOCK_REMOVE))
            permanent_delete.set_always_show_image(True)
            permanent_delete.connect("clicked", self.on_permanent_delete_clicked, index)
            players_grid.attach(permanent_delete, 3, index + 1, 1, 1)

        players_grid.show_all()


class EditHandler:
    """Handle all the signals for the editor window."""

    def __init__(self, builder, player: Player):
        """Constructor method."""
        self.builder = builder
        self.player = player
        self.spins_skills = {}
        self.spins_perks = {}

        name = self.builder.get_object("player_name")
        name.set_text(player.name)

        lvl = self.builder.get_object("lvl")
        lvl.set_value(player.data["LVL"])

        origins_list = self.builder.get_object("origins_list")
        origins_list.remove_all()
        for index, name in enumerate(ORIGINS):
            origins_list.append(str(index), name)
        origins_list.set_active(player.data["ORIGIN"])

        for spin_name in SPECIAL.keys():
            spin = self.builder.get_object(spin_name)
            spin.set_value(self.player.data["SPECIAL"][spin_name.upper()])

        self.__update_skills_grid()
        self.__update_perks_grid()

    def on_save_clicked(self, *_):
        """Save the change in the file."""
        name = self.builder.get_object("player_name")
        self.player.name = name.get_text()

        lvl = self.builder.get_object("lvl")
        self.player.data["LVL"] = lvl.get_value_as_int()

        origins_list = self.builder.get_object("origins_list")
        self.player.data["ORIGIN"] = origins_list.get_active()

        for spin_name in SPECIAL.keys():
            spin = self.builder.get_object(spin_name)
            self.player.data["SPECIAL"][spin_name.upper()] = spin.get_value_as_int()

        self.player.save_in_file()
        self.__init__(self.builder, self.player)

    def on_discard_clicked(self, *_):
        """Restore the player's data from the file."""
        self.player.restore_from_file()
        self.__init__(self.builder, self.player)

    def on_add_skill_clicked(self, *_):
        """Add an skill to the player."""
        if (skill_id := self.builder.get_object("skills_list").get_active_id()) is None:
            return

        if skill_id not in self.player.skills:
            self.player.skills[str(skill_id)] = [1, 0]
            self.__update_skills_grid()

    def on_skill_spin_value_changed(self, _, index):
        """Update the player's skill."""
        if (new_value := self.spins_skills[index].get_value_as_int()) == 0:
            self.player.skills.pop(index)
        else:
            self.player.skills[index][0] = new_value

        self.__update_skills_grid()

    def on_checkbox_toggled(self, _, index):
        """Toggle the personnal asset."""
        self.player.skills[index][1] = (self.player.skills[index][1] + 1) % 2

    def on_add_perk_clicked(self, *_):
        """Add a perk to the player."""
        if (perk_id := self.builder.get_object("perks_list").get_active_id()) is None:
            return

        # Get the current rank for the selected perk
        rank = 0
        if perk_id in self.player.perks:
            rank = self.player.perks[perk_id]

        # Update the player's perk
        self.player.perks[perk_id] = rank + 1
        self.__update_perks_grid()

    def on_suppr_perk_clicked(self, _, index):
        """Removes a rank from the selected perk."""
        self.player.perks[index] -= 1
        if self.player.perks[index] == 0:
            self.player.perks.pop(index)

        self.__update_perks_grid()

    def __update_skills_grid(self):
        """Update the skills list."""
        # Get the skills' grid
        skills_grid = self.builder.get_object("skills_grid")

        skills_list = self.builder.get_object("skills_list")
        skills_list.remove_all()
        for index, skill in enumerate(SKILLS):
            if str(index) not in self.player.skills:
                skills_list.append(str(index), skill)

        # Clean the grid
        for child in skills_grid.get_children():
            skills_grid.remove(child)

        # Display the skills
        self.spins_skills = {}
        for index, (skill_id, value) in enumerate(self.player.skills.items()):
            skill_value, tagged_skill = value

            skill_name = Gtk.Label()
            skill_name.set_markup(SKILLS[int(skill_id)])
            skills_grid.attach(skill_name, 0, index, 1, 1)

            spin = Gtk.SpinButton()
            adjustment = Gtk.Adjustment(upper=6, step_increment=1, page_increment=1)
            spin.set_adjustment(adjustment)
            spin.set_value(skill_value)
            spin.connect("value-changed", self.on_skill_spin_value_changed, skill_id)
            skills_grid.attach(spin, 1, index, 1, 1)
            self.spins_skills[skill_id] = spin

            checkbox = Gtk.CheckButton()
            checkbox.set_active(bool(tagged_skill))
            checkbox.connect("toggled", self.on_checkbox_toggled, skill_id)
            skills_grid.attach(checkbox, 2, index, 1, 1)

        skills_grid.show_all()

    def __update_perks_grid(self):
        """Update the perks list."""
        # Get the perks' grid
        perks_grid = self.builder.get_object("perks_grid")

        # Get and clean the list
        perks_list = self.builder.get_object("perks_list")
        perks_list.remove_all()

        # Update the list
        for index, perk in enumerate(PERKS):
            current_rank = 0
            if str(index) in self.player.perks:
                current_rank = self.player.perks[str(index)]

            if (
                # Rank check
                current_rank < perk["rank"]
                # Conflict between Daring Nature and Cautious Nature
                and not (
                    index in {DN_INDEX, CN_INDEX}
                    and (str(DN_INDEX) in self.player.perks or str(CN_INDEX) in self.player.perks)
                )
                # Requirements check
                and self.player.check_requirements(perk["requirements"][current_rank])
            ):
                perks_list.append(str(index), perk["name"])

        # Clean the grid
        for child in perks_grid.get_children():
            perks_grid.remove(child)

        # Display the perks
        self.spins_perks = {}
        for index, (perk_id, perk_value) in enumerate(self.player.perks.items()):
            perk_name = Gtk.Label()
            perk_name.set_markup("<b>" + PERKS[int(perk_id)]["name"] + f"</b> (Rang {perk_value})")
            perk_name.set_line_wrap(True)
            perks_grid.attach(perk_name, 0, index, 1, 1)

            perk_description = Gtk.Label()
            perk_description.set_markup(PERKS[int(perk_id)]["description"])
            perk_description.set_line_wrap(True)
            perks_grid.attach(perk_description, 1, index, 1, 1)

            suppr = Gtk.Button(label="", image=Gtk.Image(stock=Gtk.STOCK_REMOVE))
            suppr.set_always_show_image(True)
            suppr.connect("clicked", self.on_suppr_perk_clicked, perk_id)
            perks_grid.attach(suppr, 2, index, 1, 1)

        perks_grid.show_all()


class ConfirmationDialog(Gtk.Dialog):
    """Confirmation dialog for permanent deletion of a player."""

    def __init__(self, parent):
        """Constructor method."""
        super().__init__(title="Confirmation de suppression", transient_for=parent, flags=0)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        label = Gtk.Label(
            label=(
                "Êtes-vous sûr de vouloir supprimer ce personnage ?\n"
                "Cette action est irréversible."
            )
        )
        box = self.get_content_area()
        box.add(label)
        self.show_all()


def edit_player(player):
    """Manage to editor to create a new player of edit an existing one."""
    builder = Gtk.Builder()
    builder.add_from_file("waste/ui/edit_player.glade")
    builder.connect_signals(EditHandler(builder, player))

    edit_window = builder.get_object("main_window")
    edit_window.connect("destroy", Gtk.main_quit)

    if player.filename:
        edit_window.set_title(f"Modification de {player.name}")
    else:
        edit_window.set_title("Création d'un nouveau personnage")

    edit_window.show_all()
    Gtk.main()
