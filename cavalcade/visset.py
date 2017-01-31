# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from cavalcade.common import GuiBase, name_from_file
from cavalcade.common import gtk_open_file
from gi.repository import Gtk


class VisualPage(GuiBase):
	"""Settings window"""
	def __init__(self, settings):
		self._mainapp = settings._mainapp
		self.window = settings.gui["window"]
		elements = (
			"fg_colorbutton", "zero_spinbutton", "silence_spinbutton", "image_open_button", "autocolor_switch",
			"bg_colorbutton", "padding_spinbutton", "scale_spinbutton", "top_spinbutton", "bottom_spinbutton",
			"left_spinbutton", "right_spinbutton", "st_image_show_switch", "image_tag_rbutton", "imagelabel",
			"image_file_rbutton", "mainbox",
		)
		super().__init__("visset.glade", elements=elements)

		# image file filter
		self.image_filter = Gtk.FileFilter()
		self.image_filter.set_name("Image files")
		self.image_filter.add_pixbuf_formats()

		# color
		for key, value in self._mainapp.config["color"].items():
			if key in ("fg", "bg"):
				self.gui["%s_colorbutton" % key].set_rgba(value)
				self.gui["%s_colorbutton" % key].connect("color-set", getattr(self, "on_%s_color_set" % key))
			elif key == "auto":
				self.gui["autocolor_switch"].set_active(not value)  # autocolor
				self.gui["autocolor_switch"].connect("notify::active", self.on_autocolor_switch)

		# graph
		for key, value in self._mainapp.config["draw"].items():
			self.gui["%s_spinbutton" % key].set_value(value)
			self.gui["%s_spinbutton" % key].connect("value-changed", getattr(self, "on_%s_spinbutton_changed" % key))

		# offset
		for key, value in self._mainapp.config["offset"].items():
			self.gui["%s_spinbutton" % key].set_value(value)
			self.gui["%s_spinbutton" % key].connect("value-changed", self.on_offset_spinbutton_changed, key)

		# image
		self.gui["st_image_show_switch"].set_active(self._mainapp.config["image"]["show"])
		self.gui["st_image_show_switch"].connect("notify::active", self.on_image_show_switch)

		self.gui["imagelabel"].set_text("Image: %s" % name_from_file(self._mainapp.config["image"]["default"]))

		image_rb = "image_tag_rbutton" if self._mainapp.config["image"]["usetag"] else "image_file_rbutton"
		self.gui[image_rb].set_active(True)

		self.gui["image_tag_rbutton"].connect("notify::active", self.on_image_rbutton_switch, True)
		self.gui["image_file_rbutton"].connect("notify::active", self.on_image_rbutton_switch, False)

		self.gui["image_open_button"].connect("clicked", self.on_image_open_button_click)

	def on_fg_color_set(self, button):
		key = "autofg" if self._mainapp.config["color"]["auto"] else "fg"
		self._mainapp.config["color"][key] = button.get_rgba()
		self._mainapp.draw.color_update()

	def on_bg_color_set(self, button):
		self._mainapp.config["color"]["bg"] = button.get_rgba()
		if self._mainapp.config["window"]["bgpaint"]:
			self._mainapp.canvas.set_bg_rgba(self._mainapp.config["color"]["bg"])
		else:
			self.gui["st_bgpaint_switch"].set_active(True)

	def on_autocolor_switch(self, switch, active):
		self._mainapp.on_autocolor_switch(not switch.get_active())

	def on_scale_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["scale"] = float(button.get_value())

	def on_padding_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["padding"] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_zero_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["zero"] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_silence_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["silence"] = int(button.get_value())

	def on_offset_spinbutton_changed(self, button, key):
		self._mainapp.config["offset"][key] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_image_show_switch(self, switch, active):
		self._mainapp.canvas.show_image(switch.get_active())

	def on_image_rbutton_switch(self, button, active, usetag):
		if button.get_active():
			self._mainapp.config["image"]["usetag"] = usetag
			self._mainapp.canvas._rebuild_background()
			self._mainapp.emit("image-source-switch", usetag)

	def on_image_open_button_click(self, *args):
		is_ok, file_ = gtk_open_file(self.window.gui["window"], self.image_filter)
		if is_ok:
			self.gui["imagelabel"].set_text("Image: %s" % name_from_file(file_))
			self._mainapp.config["image"]["default"] = file_
			self._mainapp.emit("default-image-update", file_)

	# support
	def fg_color_manual_set(self, rgba):
		"""Force set drawing color by user"""
		self.gui["fg_colorbutton"].set_rgba(rgba)
		self._mainapp.draw.color_update()
