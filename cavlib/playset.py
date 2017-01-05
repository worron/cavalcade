# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import cavlib.pixbuf as pixbuf

from gi.repository import Gtk
from cavlib.base import GuiBase, TreeViewHolder, name_from_file


class PlayerPage(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self.current = None

		elements = (
			"mainbox", "playbutton", "seekscale", "playlist_treeview", "playlist_selection", "preview_image",
			"volumebutton", "list_search_entry",
		)
		super().__init__("playset.glade", elements)

		# get preview wigget height
		pz = self.gui["preview_image"].get_preferred_size()[1]
		self.preview_size = pz.height - 2

		# playlist view setup
		self.treeview = self.gui["playlist_treeview"]
		self.treelock = TreeViewHolder(self.treeview)
		for i, title in enumerate(("Index", "Name", "File")):
			column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
			self.treeview.append_column(column)
			if i != 1:
				column.set_visible(False)

		self.store = dict(playlist=Gtk.ListStore(int, str, str))
		self.storefilter = dict(playlist=self.store["playlist"].filter_new())
		self.storefilter["playlist"].set_visible_func(self.playlist_filter_func)
		self.search_text = None

		self.treeview.set_model(self.storefilter["playlist"])

		# signals
		self.gui["playbutton"].connect("clicked", self.on_playbutton_click)
		self.gui["playlist_treeview"].connect("row_activated", self.on_track_activated)
		self.gui["volumebutton"].connect("value-changed", self.on_volumebuton_changed)
		self.gui['list_search_entry'].connect("activate", self.on_search_active)
		# self.gui['list_search_entry'].connect("icon-release", self.on_search_active)
		self.seek_handler_id = self.gui["seekscale"].connect("value-changed", self.on_seekscale_changed)
		self.sel_handler_id = self.gui['playlist_selection'].connect("changed", self.on_track_selection_changed)

		self._mainapp.player.connect("progress", self.on_audio_progress)
		self._mainapp.player.connect("playlist-update", self.on_playlist_update)
		self._mainapp.player.connect("current", self.on_current_change)
		self._mainapp.player.connect("preview-update", self.on_preview_update)

		# gui setup
		self.gui["volumebutton"].set_value(self._mainapp.config["player"]["volume"])

	def playlist_filter_func(self, model, treeiter, data):
		if not self.search_text:
			return True
		else:
			return self.search_text.lower() in model[treeiter][1].lower()

	def hilight_current(self):
		files = [row[2] for row in self.storefilter["playlist"]]
		if self.current in files:
			index = files.index(self.current)
			self.treeview.set_cursor(index)
		else:
			self.gui["playlist_selection"].unselect_all()

	def on_track_activated(self, tree, path, colomn):
		treeiter = self.storefilter["playlist"].get_iter(path)
		file_ = self.storefilter["playlist"][treeiter][2]
		self._mainapp.player.load_file(file_)
		self._mainapp.player.play_pause()

	def on_playlist_update(self, player, plist):
		with self.treelock:
			self.store["playlist"].clear()
			for i, file_ in enumerate(plist):
				self.store["playlist"].append([i, name_from_file(file_), file_])

	def on_playbutton_click(self, button):
		self._mainapp.player.play_pause()

	def on_seekscale_changed(self, widget):
		value = self.gui["seekscale"].get_value()
		self._mainapp.player.seek(value)

	def on_volumebuton_changed(self, widget, value):
		self._mainapp.config["player"]["volume"] = value
		self._mainapp.player.set_volume(value)

	def on_audio_progress(self, player, value):
		with self.gui["seekscale"].handler_block(self.seek_handler_id):
			self.gui["seekscale"].set_value(value)

	def on_current_change(self, player, current):
		self.current = current
		if current is not None:
			self.hilight_current()

	def on_track_selection_changed(self, selection):
		model, sel = selection.get_selected()
		if sel is not None:
			file_ = model[sel][2]
			self._mainapp.player._fake_tag_reader(file_)

	def on_preview_update(self, player, bytedata):
		pb = pixbuf.from_bytes_at_scale(bytedata, -1, self.preview_size)
		self.gui["preview_image"].set_from_pixbuf(pb)

	def on_search_active(self, entry, *args):
		self.search_text = entry.get_text()
		with self.gui["playlist_selection"].handler_block(self.sel_handler_id):
			self.storefilter["playlist"].refilter()
			self.gui["playlist_selection"].unselect_all()
		self.hilight_current()
