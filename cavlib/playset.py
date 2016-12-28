# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os

from collections import OrderedDict
from gi.repository import Gtk
from cavlib.base import GuiBase, TreeViewHolder


def name_from_file(file_):
	return os.path.splitext(os.path.basename(file_))[0]


class PlayerPage(GuiBase):
	"""Settings window"""
	def __init__(self, canvas):
		self._canvas = canvas
		self.playlist_data = OrderedDict()
		elements = (
			"mainbox", "playbutton", "seekscale", "playlist_treeview",
		)
		super().__init__("playset.glade", elements)

		# playlist view setup
		self.treeview = self.gui["playlist_treeview"]
		self.treelock = TreeViewHolder(self.treeview)
		column = Gtk.TreeViewColumn("File", Gtk.CellRendererText(), text=0)
		self.treeview.append_column(column)

		self.store = Gtk.ListStore(str)
		self.treeview.set_model(self.store)

		# signals
		self.gui["playbutton"].connect("clicked", self.on_playbutton_click)
		self.gui["playlist_treeview"].connect("row_activated", self.on_track_activated)
		self.seek_handler_id = self.gui["seekscale"].connect("value-changed", self.on_seekscale_changed)

		self._canvas.player.connect("progress", self.on_audio_progress)
		self._canvas.player.connect("playlist-update", self.on_playlist_update)
		self._canvas.player.connect("current", self.on_current_change)

	def on_track_activated(self, tree, path, colomn):
		treeiter = self.store.get_iter(path)
		name = self.store[treeiter][0]
		self._canvas.player.load_file(self.playlist_data[name]["file"])
		self._canvas.player.play_pause()

	def on_playlist_update(self, player, plist):
		self.playlist_data = OrderedDict(zip([name_from_file(f) for f in plist], [{"file": f} for f in plist]))
		with self.treelock:
			self.store.clear()
			for track in self.playlist_data.keys():
				self.store.append([track])
		self.treeview.set_cursor(0)

	def on_playbutton_click(self, button):
		self._canvas.player.play_pause()

	def on_seekscale_changed(self, widget):
		perc = self.gui["seekscale"].get_value()
		self._canvas.player.seek(perc)

	def on_audio_progress(self, player, perc):
		with self.gui["seekscale"].handler_block(self.seek_handler_id):
			self.gui["seekscale"].set_value(perc)

	def on_current_change(self, player, current):
		if current is not None:
			i = list(self.playlist_data.keys()).index(name_from_file(current))  # fix this
			self.treeview.set_cursor(i)
