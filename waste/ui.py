"""Handle all the signals from the UI."""

import json
import os

import gi

from waste.player import SKILLS, SPECIAL, Player, new_player

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class MainHandler:
    """Handle all the signals from the UI."""

    def __init__(self, builder):
        """Constructor."""
        self.builder = builder
        self.players = []

        self.on_update_player_clicked()

    def on_add_player_clicked(self, *args):
        """Add a new player."""
        player = new_player()
        player.save_in_file()
        edit_player(player)
        self.players.append(player)
        self.__update_players_grid()

    def on_update_player_clicked(self, *args):
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

        name = self.builder.get_object("player_name")
        name.set_text(player.name)

        lvl = self.builder.get_object("lvl")
        lvl.set_value(player.data["LVL"])

        origins_list = self.builder.get_object("origins_list")
        origins_list.set_active(player.data["ORIGIN"])

        for spin_name in SPECIAL:
            spin = self.builder.get_object(spin_name)
            spin.set_value(self.player.data["SPECIAL"][spin_name.upper()])

        self.__update_skills_grid()

    def on_save_clicked(self, *args):
        """Save the change in the file."""
        name = self.builder.get_object("player_name")
        self.player.name = name.get_text()

        lvl = self.builder.get_object("lvl")
        self.player.data["LVL"] = lvl.get_value_as_int()

        origins_list = self.builder.get_object("origins_list")
        self.player.data["ORIGIN"] = origins_list.get_active()

        for spin_name in ("str", "per", "end", "cha", "int", "agi", "lck"):
            spin = self.builder.get_object(spin_name)
            self.player.data["SPECIAL"][spin_name.upper()] = spin.get_value_as_int()

        self.player.save_in_file()

    def on_discard_clicked(self, *args):
        """Restore the player's data from the file."""
        self.player.restore_from_file()
        self.__init__(self.builder, self.player)

    def on_add_skill_clicked(self, *args):
        """Add an skill to the player."""
        skill_index = self.builder.get_object("skills_list").get_active()

        if not self.player.skills[skill_index][0]:
            self.player.skills[skill_index] = [1, 0]
            self.__update_skills_grid()

    def on_spin_value_changed(self, _, index):
        """Update the player's skill."""
        self.player.skills[index][0] = self.spins_skills[index].get_value_as_int()
        self.__update_skills_grid()

    def on_checkbox_toggled(self, _, index):
        """Toggle the personnal asset."""
        self.player.skills[index][1] = (self.player.skills[index][1] + 1) % 2

    def __update_skills_grid(self):
        """Update the skills list."""
        # Get the skills' grid
        skills_grid = self.builder.get_object("skills_grid")

        # Clean the grid
        for child in skills_grid.get_children():
            skills_grid.remove(child)

        # Display the skills
        self.spins_skills = {}
        for index in range(len(SKILLS)):
            value, personal_asset = self.player.skills[index]
            if value == 0:
                continue

            skill_name = Gtk.Label()
            skill_name.set_markup(SKILLS[index])
            skills_grid.attach(skill_name, 0, index, 1, 1)

            spin = Gtk.SpinButton()
            adjustment = Gtk.Adjustment(upper=10, step_increment=1, page_increment=1)
            spin.set_adjustment(adjustment)
            spin.set_value(value)
            spin.connect("value-changed", self.on_spin_value_changed, index)
            skills_grid.attach(spin, 1, index, 1, 1)
            self.spins_skills[index] = spin

            checkbox = Gtk.CheckButton(label="")
            checkbox.set_active(bool(personal_asset))
            checkbox.connect("toggled", self.on_checkbox_toggled, index)
            skills_grid.attach(checkbox, 2, index, 1, 1)

        skills_grid.show_all()


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
