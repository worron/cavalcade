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
			"fg-colorbutton", "zero-spinbutton", "silence-spinbutton", "image-open-button",
			"bg-colorbutton", "padding-spinbutton", "scale-spinbutton", "image-tag-radiobutton", "image-label",
			"image-file-radiobutton", "mainbox", "offset-comboboxtext", "offset-spinbutton", "value-min-scale",
			"saturation-min-scale", "ac-window-spinbutton", "ac-bands-spinbutton", "refresh-autocolor-button",
		)
		super().__init__("visset.glade", elements=elements)

		# image file filter
		self.image_filter = Gtk.FileFilter()
		self.image_filter.set_name("Image files")
		self.image_filter.add_pixbuf_formats()

		# color
		for key in ("fg", "bg"):
			self.gui["%s-colorbutton" % key].set_rgba(self.config["color"][key])
			self.gui["%s-colorbutton" % key].connect("color-set", getattr(self, "on_%s_color_set" % key))

		# graph
		self.gui["scale-spinbutton"].set_adjustment(Gtk.Adjustment(1, 0.5, 5, 0.1, 0, 0))
		self.gui["zero-spinbutton"].set_adjustment(Gtk.Adjustment(1, 0, 50, 1, 0, 0))
		self.gui["silence-spinbutton"].set_adjustment(Gtk.Adjustment(10, 1, 60, 1, 0, 0))
		self.gui["padding-spinbutton"].set_adjustment(Gtk.Adjustment(5, 1, 50, 1, 0, 0))

		for key, value in self.config["draw"].items():
			self.gui["%s-spinbutton" % key].set_value(value)
			self.gui["%s-spinbutton" % key].connect("value-changed", self.on_draw_spinbutton_changed, key)

		# offset
		self.offset_current = None
		self.gui["offset-spinbutton"].set_adjustment(Gtk.Adjustment(5, 0, 1000, 5, 0, 0))

		for offset in ("Left", "Right", "Top", "Bottom"):
			self.gui["offset-comboboxtext"].append_text(offset)
		self.gui["offset-comboboxtext"].connect("changed", self.on_offset_combo_changed)
		self.gui["offset-comboboxtext"].set_active(0)

		self.gui["offset-spinbutton"].connect("value-changed", self.on_offset_spinbutton_changed)

		# image source
		image_rb = "image-tag-radiobutton" if self.config["image"]["usetag"] else "image-file-radiobutton"
		self.gui[image_rb].set_active(True)

		self.gui["image-tag-radiobutton"].connect("notify::active", self.on_image_rbutton_switch, True)
		self.gui["image-file-radiobutton"].connect("notify::active", self.on_image_rbutton_switch, False)

		self.gui["image-open-button"].connect("clicked", self.on_image_open_button_click)
		self.gui["image-label"].set_text("Image: %s" % name_from_file(self.config["image"]["default"]))

		# autocolor settings
		for key in ("saturation", "value"):
			self.gui["%s-min-scale" % key].set_adjustment(Gtk.Adjustment(0.5, 0, 1, 0.01, 0, 0))
			self.gui["%s-min-scale" % key].set_value(self.config["autocolor"]["%s_min" % key])
			self.gui["%s-min-scale" % key].connect("value-changed", self.on_autocolor_scale_changed, key)

		for key in ("window", "bands"):
			self.gui["ac-%s-spinbutton" % key].set_adjustment(Gtk.Adjustment(5, 0, 1000, 1, 0, 0))
			self.gui["ac-%s-spinbutton" % key].set_value(self.config["autocolor"][key])
			self.gui["ac-%s-spinbutton" % key].connect("value-changed", self.on_autocolor_spinbutton_changed, key)

		# misc
		self._mainapp.connect("ac-update", self.on_autocolor_update)
		self.gui["refresh-autocolor-button"].connect("clicked", self.on_autocolor_refresh_clicked)

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
		self.gui["fg-colorbutton"].set_rgba(color)
		self._mainapp.draw.color_update()

	# signal handlers
	def on_autocolor_refresh_clicked(self, *args):
		if self.config["color"]["auto"]:
			self._mainapp.emit("autocolor-refresh", self.config["image"]["usetag"])

	def on_autocolor_spinbutton_changed(self, button, key):
		value = int(button.get_value())
		if key == "window":
			value = min(value, self.config["autocolor"]["bands"])
		self.config["autocolor"][key] = value

	def on_autocolor_scale_changed(self, scale, key):
		self.config["autocolor"]["%s_min" % key] = scale.get_value()

	def on_fg_color_set(self, button):
		key = "autofg" if self.config["color"]["auto"] else "fg"
		self.config["color"][key] = button.get_rgba()
		self._mainapp.draw.color_update()

	def on_bg_color_set(self, button):
		self.config["color"]["bg"] = button.get_rgba()
		if self.config["window"]["bgpaint"]:
			self._mainapp.canvas.set_bg_rgba(self.config["color"]["bg"])

	def on_autocolor_update(self, sender, rgba):
		self.config["color"]["autofg"] = rgba
		if self.config["color"]["auto"]:
			self.gui["fg-colorbutton"].set_rgba(rgba)
			self._mainapp.draw.color_update()

	def on_draw_spinbutton_changed(self, button, key):
		type_ = float if key == "scale" else int
		self.config["draw"][key] = type_(button.get_value())
		if key in ("padding", "zero"):
			self._mainapp.draw.size_update()

	def on_offset_spinbutton_changed(self, button):
		self.config["offset"][self.offset_current] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_offset_combo_changed(self, combo):
		text = combo.get_active_text()
		if text is not None:
			self.offset_current = text.lower()
			self.gui["offset-spinbutton"].set_value(self.config["offset"][self.offset_current])

	def on_image_rbutton_switch(self, button, active, usetag):
		if button.get_active():
			self.config["image"]["usetag"] = usetag
			self._mainapp.canvas._rebuild_background()
			self._mainapp.emit("image-source-switch", usetag)

	def on_image_open_button_click(self, *args):
		is_ok, file_ = gtk_open_file(self.window, self.image_filter)
		if is_ok:
			self.gui["image-label"].set_text("Image: %s" % name_from_file(file_))
			self.config["image"]["default"] = file_
			self._mainapp.emit("default-image-update", file_)
