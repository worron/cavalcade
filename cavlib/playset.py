# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk
from cavlib.base import GuiBase, TreeViewHolder


class PlayerPage(GuiBase):
	"""Settings window"""
	def __init__(self, canvas):
		self._canvas = canvas
		self.playlist_data = {}
		elements = (
			"mainbox", "playbutton", "seekscale", "playlist_treeview",
		)
		super().__init__("playset.glade", elements)

		# playlist view setup
		# column_types = self.base.get_table_types()
		# for index, item in enumerate(self.titles):
		self.treeview = self.gui["playlist_treeview"]
		self.treelock = TreeViewHolder(self.treeview)
		column = Gtk.TreeViewColumn("File", Gtk.CellRendererText(), text=0)
		self.treeview.append_column(column)

		self.store = Gtk.ListStore(str)
		self.treeview.set_model(self.store)

		# signals
		self.gui["playbutton"].connect("clicked", self.on_playbutton_click)
		self._canvas.player.connect("progress", self.on_audio_progress)
		self._canvas.player.connect("playlist-update", self.on_playlist_update)
		self.seek_handler_id = self.gui["seekscale"].connect("value-changed", self.on_seekscale_changed)
		self.gui["playlist_treeview"].connect("row_activated", self.on_track_activated)

	def on_track_activated(self, tree, path, colomn):
		treeiter = self.store.get_iter(path)
		name = self.store[treeiter][0]
		self._canvas.player.load_file(self.playlist_data[name]["file"])
		self._canvas.player.play_pause()

	def on_playlist_update(self, player, pdata):
		self.playlist_data = pdata
		with self.treelock:
			self.store.clear()
			for track in pdata.keys():
				self.store.append([track])

	def on_playbutton_click(self, button):
		self._canvas.player.play_pause()

	def on_seekscale_changed(self, widget):
		perc = self.gui["seekscale"].get_value()
		self._canvas.player.seek(perc)

	def on_audio_progress(self, player, perc):
		with self.gui["seekscale"].handler_block(self.seek_handler_id):
			self.gui["seekscale"].set_value(perc)
