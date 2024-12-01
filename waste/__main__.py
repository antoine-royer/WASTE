from fallout.ui import MainHandler

from gi.repository import Gtk


def main():
    # builder
    builder = Gtk.Builder()
    builder.add_from_file('fallout/ui/fallout.glade')
    builder.connect_signals(MainHandler(builder))
    window = builder.get_object('main_window')
    window.connect("destroy", Gtk.main_quit)

    # main loop
    window.show_all()
    Gtk.main()