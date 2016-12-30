# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import cavlib.pixbuf as pixbuf

from collections import OrderedDict
from gi.repository import Gtk
from cavlib.base import GuiBase, TreeViewHolder, name_from_file


class PlayerPage(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self.playlist_data = OrderedDict()
		elements = (
			"mainbox", "playbutton", "seekscale", "playlist_treeview", "playlist_selection", "preview_image",
		)
		super().__init__("playset.glade", elements)

		# get preview wigget height
		pz = self.gui["preview_image"].get_preferred_size()[1]
		self.preview_size = pz.height - 2

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
		self.gui['playlist_selection'].connect("changed", self.on_track_selection_changed)
		self.seek_handler_id = self.gui["seekscale"].connect("value-changed", self.on_seekscale_changed)

		self._mainapp.player.connect("progress", self.on_audio_progress)
		self._mainapp.player.connect("playlist-update", self.on_playlist_update)
		self._mainapp.player.connect("current", self.on_current_change)
		self._mainapp.player.connect("preview-update", self.on_preview_update)

	def on_track_activated(self, tree, path, colomn):
		treeiter = self.store.get_iter(path)
		name = self.store[treeiter][0]
		self._mainapp.player.load_file(self.playlist_data[name]["file"])
		self._mainapp.player.play_pause()

	def on_playlist_update(self, player, plist):
		self.playlist_data = OrderedDict(zip([name_from_file(f) for f in plist], [{"file": f} for f in plist]))
		with self.treelock:
			self.store.clear()
			for track in self.playlist_data.keys():
				self.store.append([track])
		self.treeview.set_cursor(0)

	def on_playbutton_click(self, button):
		self._mainapp.player.play_pause()

	def on_seekscale_changed(self, widget):
		value = self.gui["seekscale"].get_value()
		self._mainapp.player.seek(value)

	def on_audio_progress(self, player, value):
		with self.gui["seekscale"].handler_block(self.seek_handler_id):
			self.gui["seekscale"].set_value(value)

	def on_current_change(self, player, current):
		if current is not None:
			i = list(self.playlist_data.keys()).index(name_from_file(current))  # fix this
			self.treeview.set_cursor(i)

	def on_track_selection_changed(self, selection):
		model, sel = selection.get_selected()
		if sel is not None:
			file_ = self.playlist_data[model[sel][0]]["file"]
			self._mainapp.player._fake_tag_reader(file_)

	def on_preview_update(self, player, bytedata):
		pb = pixbuf.from_bytes_at_scale(bytedata, -1, self.preview_size)
		self.gui["preview_image"].set_from_pixbuf(pb)
