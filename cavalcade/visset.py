# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from cavalcade.common import GuiBase, name_from_file
from cavalcade.common import gtk_open_file
from gi.repository import Gtk, GLib, Gio


class VisualPage(GuiBase):
	"""Settings window"""
	def __init__(self, settings):
		self._mainapp = settings._mainapp
		self.window = settings.gui["window"]
		self.config = settings._mainapp.config
		self.settings = settings

		elements = (
			"fg_colorbutton", "zero_spinbutton", "silence_spinbutton", "image_open_button",
			"bg_colorbutton", "padding_spinbutton", "scale_spinbutton", "top_spinbutton", "bottom_spinbutton",
			"left_spinbutton", "right_spinbutton", "image_tag_rbutton", "imagelabel",
			"image_file_rbutton", "mainbox",
		)
		super().__init__("visset.glade", elements=elements)

		# image file filter
		self.image_filter = Gtk.FileFilter()
		self.image_filter.set_name("Image files")
		self.image_filter.add_pixbuf_formats()

		# color
		for key in ("fg", "bg"):
			self.gui["%s_colorbutton" % key].set_rgba(self.config["color"][key])
			self.gui["%s_colorbutton" % key].connect("color-set", getattr(self, "on_%s_color_set" % key))

		# graph
		for key, value in self.config["draw"].items():
			self.gui["%s_spinbutton" % key].set_value(value)
			self.gui["%s_spinbutton" % key].connect("value-changed", getattr(self, "on_%s_spinbutton_changed" % key))

		# offset
		for key, value in self.config["offset"].items():
			self.gui["%s_spinbutton" % key].set_value(value)
			self.gui["%s_spinbutton" % key].connect("value-changed", self.on_offset_spinbutton_changed, key)

		self.gui["imagelabel"].set_text("Image: %s" % name_from_file(self.config["image"]["default"]))

		image_rb = "image_tag_rbutton" if self.config["image"]["usetag"] else "image_file_rbutton"
		self.gui[image_rb].set_active(True)

		self.gui["image_tag_rbutton"].connect("notify::active", self.on_image_rbutton_switch, True)
		self.gui["image_file_rbutton"].connect("notify::active", self.on_image_rbutton_switch, False)

		self.gui["image_open_button"].connect("clicked", self.on_image_open_button_click)

		# actions
		auto_action = Gio.SimpleAction.new_stateful(
			"autocolor", None, GLib.Variant.new_boolean(self.config["color"]["auto"])
		)
		auto_action.connect("change-state", self.on_autocolor_switch)
		self.settings.actions["settings"].add_action(auto_action)

	# action handlers
	def on_autocolor_switch(self, action, value):
		"""Use color analyzer or user preset"""
		action.set_state(value)
		autocolor = value.get_boolean()
		self.config["color"]["auto"] = autocolor

		color = self.config["color"]["autofg"] if autocolor else self.config["color"]["fg"]
		self.gui["fg_colorbutton"].set_rgba(color)
		self._mainapp.draw.color_update()

	# signal handlers
	def on_fg_color_set(self, button):
		key = "autofg" if self.config["color"]["auto"] else "fg"
		self.config["color"][key] = button.get_rgba()
		self._mainapp.draw.color_update()

	def on_bg_color_set(self, button):
		self.config["color"]["bg"] = button.get_rgba()
		if self.config["window"]["bgpaint"]:
			self._mainapp.canvas.set_bg_rgba(self.config["color"]["bg"])

	def on_scale_spinbutton_changed(self, button):
		self.config["draw"]["scale"] = float(button.get_value())

	def on_padding_spinbutton_changed(self, button):
		self.config["draw"]["padding"] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_zero_spinbutton_changed(self, button):
		self.config["draw"]["zero"] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_silence_spinbutton_changed(self, button):
		self.config["draw"]["silence"] = int(button.get_value())

	def on_offset_spinbutton_changed(self, button, key):
		self.config["offset"][key] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_image_rbutton_switch(self, button, active, usetag):
		if button.get_active():
			self.config["image"]["usetag"] = usetag
			self._mainapp.canvas._rebuild_background()
			self._mainapp.emit("image-source-switch", usetag)

	def on_image_open_button_click(self, *args):
		is_ok, file_ = gtk_open_file(self.window, self.image_filter)
		if is_ok:
			self.gui["imagelabel"].set_text("Image: %s" % name_from_file(file_))
			self.config["image"]["default"] = file_
			self._mainapp.emit("default-image-update", file_)
