# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import cavalcade.pixbuf as pixbuf

from gi.repository import Gtk, Pango
from cavalcade.common import GuiBase, TreeViewHolder, name_from_file, AttributeDict


class PlayerPage(GuiBase):
	"""Player setting page"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self.preview = None
		self.current = None
		self.playlist = []
		self.playqueue = []

		elements = (
			"mainbox", "play-button", "seek-scale", "playlist-treeview", "playlist-selection", "preview-image",
			"volumebutton", "list-searchentry", "queue-radiobutton", "list-radiobutton", "solo-action-button",
			"mass-action-button", "shuffle-button",
		)
		super().__init__("playerpage.glade", elements=elements)

		# some gui constants
		self.TRACK_STORE = AttributeDict(INDEX=0, NAME=1, FILE=2)
		self.PLAY_BUTTON_DATA = {
			False: Gtk.Image(icon_name="media-playback-start-symbolic"),
			True: Gtk.Image(icon_name="media-playback-pause-symbolic")
		}
		self.ACTION_BUTTON_DATA = dict(
			list = AttributeDict(
				images = (Gtk.Image(icon_name="list-add-symbolic"), Gtk.Image(icon_name="send-to-symbolic")),
				tooltip = ("Add track to playback queue.", "Add all to playback queue.")
			),
			queue = AttributeDict(
				images = (Gtk.Image(icon_name="list-remove-symbolic"), Gtk.Image(icon_name="list-remove-all-symbolic")),
				tooltip = ("Remove track from playback queue.", "Clear playback queue.")
			)
		)

		# get preview widget height
		pz = self.gui["preview-image"].get_preferred_size()[1]
		self.preview_size = pz.height - 2
		self.update_default_preview()

		# playlist view setup
		self.treeview = self.gui["playlist-treeview"]
		self.treelock = TreeViewHolder(self.treeview)
		for i, title in enumerate(("Index", "Name", "File")):
			column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(ellipsize=Pango.EllipsizeMode.END), text=i)
			self.treeview.append_column(column)
			if i != self.TRACK_STORE.NAME:
				column.set_visible(False)

		self.store = Gtk.ListStore(int, str, str)
		self.store_filter = self.store.filter_new()
		self.store_filter.set_visible_func(self.playlist_filter_func)
		self.search_text = None

		self.treeview.set_model(self.store_filter)

		# list view button
		list_radio_button = "queue-radiobutton" if self._mainapp.config["player"]["showqueue"] else "list-radiobutton"
		self.gui[list_radio_button].set_active(True)

		self.gui["queue-radiobutton"].connect("notify::active", self.on_listview_radio_button_switch, True)
		self.gui["list-radiobutton"].connect("notify::active", self.on_listview_radio_button_switch, False)

		# list action buttons
		self.set_button_images()
		self.gui["play-button"].set_image(self.PLAY_BUTTON_DATA[False])

		# signals
		self.gui["play-button"].connect("clicked", self.on_playbutton_click)
		self.gui["mass-action-button"].connect("clicked", self.on_mass_button_click)
		self.gui["solo-action-button"].connect("clicked", self.on_solo_button_click)
		self.gui["playlist-treeview"].connect("row_activated", self.on_track_activated)
		self.gui["volumebutton"].connect("value-changed", self.on_volumebuton_changed)
		self.gui["list-searchentry"].connect("activate", self.on_search_active)
		self.gui["list-searchentry"].connect("icon-release", self.on_search_reset)
		self.gui["shuffle-button"].connect("toggled", self.on_shuffle_button_toggle)
		self.seek_handler_id = self.gui["seek-scale"].connect("value-changed", self.on_seekscale_changed)
		self.sel_handler_id = self.gui["playlist-selection"].connect("changed", self.on_track_selection_changed)

		self._mainapp.player.connect("progress", self.on_audio_progress)
		self._mainapp.player.connect("playlist-update", self.on_playlist_update)
		self._mainapp.player.connect("queue-update", self.on_playqueue_update)
		self._mainapp.player.connect("current", self.on_current_change)
		self._mainapp.player.connect("preview-update", self.on_preview_update)
		self._mainapp.player.connect("playing", self.on_play_state_update)

		self._mainapp.connect("default-image-update", self.update_default_preview)

		# gui setup
		self.gui["volumebutton"].set_value(self._mainapp.config["player"]["volume"])
		self.gui["shuffle-button"].set_active(self._mainapp.config["player"]["shuffle"])

	# support
	def on_shuffle_button_toggle(self, button):
		self._mainapp.config["player"]["shuffle"] = button.get_active()

	# noinspection PyUnusedLocal
	def update_default_preview(self, *args):
		self.preview = pixbuf.from_file_at_scale(self._mainapp.config["image"]["default"], -1, self.preview_size)

	def set_button_images(self):
		"""Update action buttons images according current state"""
		data = self.ACTION_BUTTON_DATA["queue" if self._mainapp.config["player"]["showqueue"] else "list"]
		for i, button_name in enumerate(("solo-action-button", "mass-action-button")):
			self.gui[button_name].set_image(data.images[i])
			self.gui[button_name].set_tooltip_text(data.tooltip[i])

	# noinspection PyUnusedLocal
	def playlist_filter_func(self, model, treeiter, data):
		"""Function to filter current track list by search text"""
		if not self.search_text:
			return True
		else:
			return self.search_text.lower() in model[treeiter][self.TRACK_STORE.NAME].lower()

	def get_filtered_files(self):
		"""Get list of files considering search filter"""
		return [row[self.TRACK_STORE.FILE] for row in self.store_filter]

	def highlight_current(self):
		"""Select current playing track if available"""
		files = self.get_filtered_files()
		if self.current in files:
			index = files.index(self.current)
			self.treeview.set_cursor(index)
		else:
			self.gui["playlist-selection"].unselect_all()

	def filter_by_search(self):
		"""Filter current track list by search text"""
		self.search_text = self.gui["list-searchentry"].get_text()
		with self.gui["playlist-selection"].handler_block(self.sel_handler_id):
			self.store_filter.refilter()
			self.gui["playlist-selection"].unselect_all()

	def rebuild_store(self, data):
		"""Update audio track store"""
		with self.treelock:
			self.store.clear()
			for i, file_ in enumerate(data):
				self.store.append([i, name_from_file(file_), file_])
		self.highlight_current()

	# gui handlers
	# noinspection PyUnusedLocal,PyUnusedLocal
	def on_track_activated(self, tree, path, column):
		treeiter = self.store_filter.get_iter(path)
		file_ = self.store_filter[treeiter][self.TRACK_STORE.FILE]
		self._mainapp.player.load_file(file_)
		self._mainapp.player.play_pause()

	# noinspection PyUnusedLocal
	def on_playlist_update(self, player, plist):
		self.playlist = plist
		if not self._mainapp.config["player"]["showqueue"]:
			self.rebuild_store(plist)

	# noinspection PyUnusedLocal
	def on_playqueue_update(self, player, play_queue):
		self.playqueue = play_queue
		if self._mainapp.config["player"]["showqueue"]:
			self.rebuild_store(play_queue)

	# noinspection PyUnusedLocal
	def on_playbutton_click(self, button):
		self._mainapp.player.play_pause()

	# noinspection PyUnusedLocal
	def on_seekscale_changed(self, widget):
		value = self.gui["seek-scale"].get_value()
		self._mainapp.player.seek(value)

	# noinspection PyUnusedLocal
	def on_volumebuton_changed(self, widget, value):
		self._mainapp.config["player"]["volume"] = value
		self._mainapp.player.set_volume(value)

	# noinspection PyUnusedLocal
	def on_audio_progress(self, player, value):
		with self.gui["seek-scale"].handler_block(self.seek_handler_id):
			self.gui["seek-scale"].set_value(value)

	# noinspection PyUnusedLocal
	def on_current_change(self, player, current):
		self.current = current
		if current is not None:
			self.gui["play-button"].set_tooltip_text("Playing: %s" % name_from_file(current))
			self.highlight_current()
		else:
			self.gui["play-button"].set_tooltip_text("Playing: none")

	def on_track_selection_changed(self, selection):
		model, sel = selection.get_selected()
		if sel is not None:
			file_ = model[sel][self.TRACK_STORE.FILE]
			self._mainapp.player.fake_tag_reader(file_)

	# noinspection PyUnusedLocal
	def on_preview_update(self, player, bytedata):
		pb = pixbuf.from_bytes_at_scale(bytedata, -1, self.preview_size) if bytedata is not None else self.preview
		self.gui["preview-image"].set_from_pixbuf(pb)

	# noinspection PyUnusedLocal
	def on_search_active(self, *args):
		self.filter_by_search()
		self.highlight_current()

	# noinspection PyUnusedLocal
	def on_search_reset(self, *args):
		self.gui["list-searchentry"].set_text("")
		self.on_search_active()

	# noinspection PyUnusedLocal
	def on_listview_radio_button_switch(self, button, active, showqueue):
		if button.get_active():
			self._mainapp.config["player"]["showqueue"] = showqueue
			self.gui["list-searchentry"].set_text("")
			self.filter_by_search()
			data = self.playqueue if showqueue else self.playlist
			self.rebuild_store(data)
			self.set_button_images()

	# noinspection PyUnusedLocal
	def on_solo_button_click(self, *args):
		model, sel = self.gui["playlist-selection"].get_selected()
		if sel is not None:
			file_ = model[sel][self.TRACK_STORE.FILE]
			if self._mainapp.config["player"]["showqueue"]:
				self._mainapp.player.remove_from_queue(file_)
			else:
				self._mainapp.player.add_to_queue(file_)

	# noinspection PyUnusedLocal
	def on_mass_button_click(self, *args):
		files = self.get_filtered_files()
		if self._mainapp.config["player"]["showqueue"]:
			self._mainapp.player.remove_from_queue(*files)
		else:
			self._mainapp.player.add_to_queue(*files)

	# noinspection PyUnusedLocal
	def on_play_state_update(self, player, value):
		self.gui["play-button"].set_image(self.PLAY_BUTTON_DATA[value])
