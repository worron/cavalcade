# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import cavlib.pixbuf as pixbuf

from gi.repository import Gtk
from cavlib.common import GuiBase, TreeViewHolder, name_from_file

LIST_IMAGES = (Gtk.Image(stock=Gtk.STOCK_ADD), Gtk.Image(stock=Gtk.STOCK_GO_FORWARD))
QUEUE_IMAGES = (Gtk.Image(stock=Gtk.STOCK_REMOVE), Gtk.Image(stock=Gtk.STOCK_CLEAR))


class PlayerPage(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self.current = None
		self.playlist = []
		self.playqueue = []

		elements = (
			"mainbox", "playbutton", "seekscale", "playlist_treeview", "playlist_selection", "preview_image",
			"volumebutton", "list_search_entry", "queue_rbutton", "list_rbutton", "solo_action_button",
			"mass_action_button", "playtoolbar",
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

		self.store = Gtk.ListStore(int, str, str)
		self.storefilter = self.store.filter_new()
		self.storefilter.set_visible_func(self.playlist_filter_func)
		self.search_text = None

		self.treeview.set_model(self.storefilter)

		# list view button
		self.gui["list_rbutton"].set_active(True)

		self.gui["queue_rbutton"].connect("notify::active", self.on_listview_rbutton_switch, True)
		self.gui["list_rbutton"].connect("notify::active", self.on_listview_rbutton_switch, False)

		# list action buttons
		self.set_button_images()
		self.gui["playbutton"].set_icon_name(Gtk.STOCK_MEDIA_PLAY)

		# signals
		self.gui["playbutton"].connect("clicked", self.on_playbutton_click)
		self.gui["mass_action_button"].connect("clicked", self.on_mass_button_click)
		self.gui["solo_action_button"].connect("clicked", self.on_solo_button_click)
		self.gui["playlist_treeview"].connect("row_activated", self.on_track_activated)
		self.gui["volumebutton"].connect("value-changed", self.on_volumebuton_changed)
		self.gui['list_search_entry'].connect("activate", self.on_search_active)
		self.gui['list_search_entry'].connect("icon-release", self.on_search_reset)
		self.seek_handler_id = self.gui["seekscale"].connect("value-changed", self.on_seekscale_changed)
		self.sel_handler_id = self.gui['playlist_selection'].connect("changed", self.on_track_selection_changed)

		self._mainapp.player.connect("progress", self.on_audio_progress)
		self._mainapp.player.connect("playlist-update", self.on_playlist_update)
		self._mainapp.player.connect("queue-update", self.on_playqueue_update)
		self._mainapp.player.connect("current", self.on_current_change)
		self._mainapp.player.connect("preview-update", self.on_preview_update)
		self._mainapp.player.connect("playing", self.on_playstate_update)

		# gui setup
		self.gui["volumebutton"].set_value(self._mainapp.config["player"]["volume"])

	def set_button_images(self):
		images = QUEUE_IMAGES if self._mainapp.config["player"]["showqueue"] else LIST_IMAGES
		for i, button_name in enumerate(("solo_action_button", "mass_action_button")):
			self.gui[button_name].set_image(images[i])

	def playlist_filter_func(self, model, treeiter, data):
		if not self.search_text:
			return True
		else:
			return self.search_text.lower() in model[treeiter][1].lower()

	def get_filtered_files(self):
		return [row[2] for row in self.storefilter]

	def hilight_current(self):
		files = self.get_filtered_files()
		if self.current in files:
			index = files.index(self.current)
			self.treeview.set_cursor(index)
		else:
			self.gui["playlist_selection"].unselect_all()

	def refilter_by_search(self):
		self.search_text = self.gui['list_search_entry'].get_text()
		with self.gui["playlist_selection"].handler_block(self.sel_handler_id):
			self.storefilter.refilter()
			self.gui["playlist_selection"].unselect_all()

	def rebuild_store(self, data):
		with self.treelock:
			self.store.clear()
			for i, file_ in enumerate(data):
				self.store.append([i, name_from_file(file_), file_])
		self.hilight_current()

	def on_track_activated(self, tree, path, colomn):
		treeiter = self.storefilter.get_iter(path)
		file_ = self.storefilter[treeiter][2]
		self._mainapp.player.load_file(file_)
		self._mainapp.player.play_pause()

	def on_playlist_update(self, player, plist):
		self.playlist = plist
		if not self._mainapp.config["player"]["showqueue"]:
			self.rebuild_store(plist)

	def on_playqueue_update(self, player, pqueue):
		self.playqueue = pqueue
		if self._mainapp.config["player"]["showqueue"]:
			self.rebuild_store(pqueue)

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

	def on_search_active(self, *args):
		self.refilter_by_search()
		self.hilight_current()

	def on_search_reset(self, *args):
		self.gui['list_search_entry'].set_text("")
		self.on_search_active()

	def on_listview_rbutton_switch(self, button, active, showqueue):
		if button.get_active():
			self._mainapp.config["player"]["showqueue"] = showqueue
			self.gui['list_search_entry'].set_text("")
			self.refilter_by_search()
			data = self.playqueue if showqueue else self.playlist
			self.rebuild_store(data)
			self.set_button_images()

	def on_solo_button_click(self, *args):
		model, sel = self.gui["playlist_selection"].get_selected()
		if sel is not None:
			file_ = model[sel][2]
			if self._mainapp.config["player"]["showqueue"]:
				self._mainapp.player.remove_from_queue(file_)
			else:
				self._mainapp.player.add_to_queue(file_)

	def on_mass_button_click(self, *args):
		files = self.get_filtered_files()
		if self._mainapp.config["player"]["showqueue"]:
			self._mainapp.player.remove_from_queue(*files)
		else:
			self._mainapp.player.add_to_queue(*files)

	def on_playstate_update(self, player, value):
		self.gui["playbutton"].set_visible(False)  # Fix this
		self.gui["playbutton"].set_icon_name(Gtk.STOCK_MEDIA_PAUSE if value else Gtk.STOCK_MEDIA_PLAY)
		self.gui["playbutton"].set_visible(True)
