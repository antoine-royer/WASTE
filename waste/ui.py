"""Handle all the signals from the UI."""

import json
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

SPECIAL = ("str", "per", "end", "cha", "int", "agi", "lck")
ABILITIES = (
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

    def __init__(self, filename, name, special, abilities):
        """Constructor method."""
        self.filename = filename
        self.name = name
        self.special = special
        self.abilities = abilities

    def restore_from_file(self):
        """Overwrite the Player's instance with the content of the reference file for the player."""
        with open(self.filename, "r", encoding="utf-8") as file:
            player_data = json.load(file)
            self.name = player_data["name"]
            self.special = player_data["SPECIAL"]
            self.abilities = player_data["abilities"]

    def save_in_file(self):
        """Save the player's data into its file."""
        if not self.filename:
            name = self.name.lower().replace(" ", "_")
            self.filename = f"waste/players/{name}.json"

        data = {"name": self.name, "SPECIAL": self.special, "abilities": self.abilities}
        with open(self.filename, "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=8))


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
                        player_data["name"],
                        player_data["SPECIAL"],
                        player_data["abilities"],
                    )
                )

        # Update the players' grid on the UI
        self.__update_players_grid()

    def on_edit_player_clicked(self, _, identifier):
        """Edit an existing player."""
        edit_player(self.players[identifier])
        self.__update_players_grid()

    def on_suppr_player_clicked(self, _, identifier):
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

        self.spins_abilities = []
        for index in range(len(ABILITIES)):
            self.spins_abilities.append(Gtk.SpinButton())
            adjustment = Gtk.Adjustment(upper=10, step_increment=1, page_increment=1)
            self.spins_abilities[index].set_adjustment(adjustment)
            self.spins_abilities[-1].set_value(self.player.abilities[index][0])
            self.spins_abilities[-1].connect("value-changed", self.on_spin_value_changed, index)

        name = self.builder.get_object("player_name")
        name.set_text(player.name)

        for spin_name in SPECIAL:
            spin = self.builder.get_object(spin_name)
            spin.set_value(self.player.special[spin_name.upper()])

        self.__update_abilities_grid()

    def on_save_clicked(self, *args):
        """Save the change in the file."""
        name = self.builder.get_object("player_name")
        self.player.name = name.get_text()

        for spin_name in ("str", "per", "end", "cha", "int", "agi", "lck"):
            spin = self.builder.get_object(spin_name)
            self.player.special[spin_name.upper()] = spin.get_value_as_int()

        self.player.save_in_file()
        self.__update_abilities_grid()

    def on_discard_clicked(self, *args):
        """Restore the player's data from the file."""
        if not self.player.filename:
            dialog = Gtk.MessageDialog(
                transient_for=self.builder.get_object("main_window"),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CANCEL,
                text="Fichier introuvable",
            )
            dialog.format_secondary_text(
                f"Le fichier pour le joueur '{self.player.name}' n'existe pas, vous devez suivre "
                f"ces deux étapes :\n1. renseigner un nom pour le joueur\n2. valider les "
                f"changements."
            )
            dialog.run()
            dialog.destroy()

        else:
            self.player.restore_from_file()
            self.__init__(self.builder, self.player)

    def on_add_ability_clicked(self, *args):
        """Add an ability to the player."""
        ability = self.builder.get_object("abilities_list").get_active_text()
        ability_index = ABILITIES.index(ability)

        if not self.player.abilities[ability_index][0]:
            self.player.abilities[ability_index] = [1, 0]
            self.__update_abilities_grid()

    def on_spin_value_changed(self, _, index):
        """Update the player's ability."""
        self.player.abilities[index][0] = self.spins_abilities[index].get_value_as_int()

    def on_checkbox_toggled(self, _, index):
        """Toggle the personnal asset."""
        self.player.abilities[index][1] = (self.player.abilities[index][1] + 1) % 2

    def __update_abilities_grid(self):
        """Update the abilities list."""
        # Get the abilities' grid
        abilities_grid = self.builder.get_object("abilities_grid")

        # Clean the grid
        for child in abilities_grid.get_children():
            abilities_grid.remove(child)

        # Display the abilities
        for index, spin in enumerate(self.spins_abilities):
            value, personal_asset = self.player.abilities[index]
            if value == 0:
                continue

            ability_name = Gtk.Label()
            ability_name.set_markup(ABILITIES[index])
            abilities_grid.attach(ability_name, 0, index + 1, 1, 1)

            spin.set_value(value)
            abilities_grid.attach(spin, 1, index + 1, 1, 1)

            checkbox = Gtk.CheckButton(label="")
            checkbox.set_active(bool(personal_asset))
            checkbox.connect("toggled", self.on_checkbox_toggled, index)
            abilities_grid.attach(checkbox, 2, index + 1, 1, 1)

        abilities_grid.show_all()


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


def new_player():
    """Create a new player, returns a Player's instance."""
    return Player(
        "",
        "Nouveau Joueur",
        {key.upper(): 5 for key in SPECIAL},
        [[0, 0] for _ in range(len(ABILITIES))],
    )


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
