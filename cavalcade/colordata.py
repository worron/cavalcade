# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk, Pango, GdkPixbuf
from cavalcade.common import GuiBase, TreeViewHolder, AttributeDict

# TODO: make color list update on every new color added?


class ColorsWindow(GuiBase):
	"""User saved color list window"""
	def __init__(self, mainapp):
		elements = (
			"window", "colors-treeview", "colors-searchentry", "colors-selection", "color-delete-button"
		)
		super().__init__("colors.glade", elements=elements)

		self._mainapp = mainapp
		self.search_text = None

		# some gui constants
		self.COLOR_STORE = AttributeDict(INDEX=0, FILE=1, COLOR=2, ICON=3)
		self.PB = AttributeDict(bits=8, width=64, height=16, column_width = 88)

		# colors view setup
		self.treeview = self.gui["colors-treeview"]
		self.treelock = TreeViewHolder(self.treeview)
		for i, title in enumerate(("Index", "File", "Color", "Icon")):
			if i != self.COLOR_STORE.ICON:
				column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(ellipsize=Pango.EllipsizeMode.START), text=i)
				column.set_resizable(True)
				column.set_expand(True)
			else:
				column = Gtk.TreeViewColumn(title, Gtk.CellRendererPixbuf(width=self.PB.column_width), pixbuf=i)
			self.treeview.append_column(column)
			if i in (self.COLOR_STORE.INDEX, self.COLOR_STORE.COLOR):
				column.set_visible(False)

		self.store = Gtk.ListStore(int, str, str, GdkPixbuf.Pixbuf)
		self.store_filter = self.store.filter_new()
		self.store_filter.set_visible_func(self.colors_filter_func)
		self.search_text = None

		self.treeview.set_model(self.store_filter)

		# accelerators
		self.accelerators = Gtk.AccelGroup()
		self.gui["window"].add_accel_group(self.accelerators)
		self.accelerators.connect(*Gtk.accelerator_parse("Escape"), Gtk.AccelFlags.VISIBLE, self.hide)

		# signals
		self.gui["window"].connect("delete-event", self.hide)
		self.gui["colors-searchentry"].connect("activate", self.on_search_active)
		self.gui["colors-searchentry"].connect("icon-release", self.on_search_reset)
		self.gui["color-delete-button"].connect("clicked", self.on_color_delete_button_click)

	def rebuild_store(self, data):
		"""Update colors store"""
		with self.treelock:
			self.store.clear()
			for i, (file_, color) in enumerate(data.items()):
				pixbuf = GdkPixbuf.Pixbuf.new(
					GdkPixbuf.Colorspace.RGB, False,
					self.PB.bits, self.PB.width, self.PB.height
				)
				pixbuf.fill(int("%02X%02X%02XFF" % tuple(int(i*255) for i in color), 16))  # fix this
				self.store.append([i, file_, "%.2f %.2f %.2f" % color, pixbuf])

	# noinspection PyUnusedLocal
	def colors_filter_func(self, model, treeiter, data):
		"""Function to filter current color list by search text"""
		if not self.search_text:
			return True
		else:
			return self.search_text.lower() in model[treeiter][self.COLOR_STORE.FILE].lower()

	# GUI handlers
	# noinspection PyUnusedLocal
	def on_search_active(self, *args):
		self.search_text = self.gui["colors-searchentry"].get_text()
		self.store_filter.refilter()

	# noinspection PyUnusedLocal
	def on_search_reset(self, *args):
		self.gui["colors-searchentry"].set_text("")
		self.on_search_active()

	# noinspection PyUnusedLocal
	def on_color_delete_button_click(self, *args):
		model, sel = self.gui["colors-selection"].get_selected()
		if sel is not None:
			file_ = model[sel][self.COLOR_STORE.FILE]
			self._mainapp.palette.delete_color(file_)
			self.rebuild_store(self._mainapp.palette.colors)

	# noinspection PyUnusedLocal
	def hide(self, *args):
		"""Hide colors window"""
		self.gui["window"].hide()
		return True

	# noinspection PyUnusedLocal
	def show(self, *args):
		"""Show colors window"""
		self.rebuild_store(self._mainapp.palette.colors)
		self.gui["window"].show_all()
