# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from cavlib.common import GuiBase, WINDOW_HINTS, name_from_file
from gi.repository import Gdk, Gtk

CORNERS = (
	("TOP_LEFT", (False, False)),
	("TOP_RIGHT", (True, False)),
	("BOTTOM_LEFT", (False, True)),
	("BOTTOM_RIGHT", (True, True)),
)


class VisualPage(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp, settings_window):
		self._mainapp = mainapp
		self.window = settings_window
		elements = (
			"mainbox", "st_maximize_switch", "st_below_switch", "hint_combobox", "st_imagebyscreen_switch",
			"st_stick_switch", "st_winbyscreen_switch", "st_bgpaint_switch", "fg_colorbutton", "st_fullscreen_switch",
			"bg_colorbutton", "padding_spinbutton", "scale_spinbutton", "top_spinbutton", "bottom_spinbutton",
			"left_spinbutton", "right_spinbutton", "hide_button", "exit_button", "st_image_show_switch",
			"image_file_rbutton", "image_tag_rbutton", "imagelabel", "image_open_button", "corner_combobox",
			"autocolor_switch", "zero_spinbutton", "silence_spinbutton",
		)
		super().__init__("visset.glade", elements)

		# window state
		for key, value in self._mainapp.config["state"].items():
			self.gui["st_%s_switch" % key].set_active(value)
			self.gui["st_%s_switch" % key].connect("notify::active", self.on_winstate_switch, key)

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

		# misc
		for hint in WINDOW_HINTS:
			self.gui["hint_combobox"].append_text(hint)
		self.gui["hint_combobox"].set_active(WINDOW_HINTS.index(self._mainapp.config["hint"].value_nick.upper()))
		self.gui["hint_combobox"].connect("changed", self.on_hint_combo_changed)

		for corner in CORNERS:
			self.gui["corner_combobox"].append_text(corner[0])
		states = [corner[1] for corner in CORNERS]
		state = (self._mainapp.config["image"]["ha"], self._mainapp.config["image"]["va"])
		self.gui["corner_combobox"].set_active(states.index(state))
		self.gui["corner_combobox"].connect("changed", self.on_corner_combo_changed)

	def fg_color_manual_set(self, rgba):
		self.gui["fg_colorbutton"].set_rgba(rgba)
		self._mainapp.draw.color_update()

	def on_winstate_switch(self, switch, active, key):
		self._mainapp.canvas.set_property(key, switch.get_active())

	def on_fg_color_set(self, button):
		key = "autofg" if self._mainapp.config["color"]["auto"] else "fg"
		self._mainapp.config["color"][key] = button.get_rgba()
		self._mainapp.draw.color_update()

	def on_bg_color_set(self, button):
		self._mainapp.config["color"]["bg"] = button.get_rgba()
		if self._mainapp.config["state"]["bgpaint"]:
			self._mainapp.canvas._set_bg_rgba(self._mainapp.config["color"]["bg"])
		else:
			self.gui["st_bgpaint_switch"].set_active(True)

	def on_autocolor_switch(self, switch, active):
		self._mainapp.autocolor_switch(not switch.get_active())

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

	def on_hint_combo_changed(self, combo):
		text = combo.get_active_text()
		hint = getattr(Gdk.WindowTypeHint, text)
		self._mainapp.canvas.set_hint(hint)

	def on_corner_combo_changed(self, combo):
		text = combo.get_active_text()
		self._mainapp.config["image"]["ha"], self._mainapp.config["image"]["va"] = dict(CORNERS)[text]

	def on_image_show_switch(self, switch, active):
		self._mainapp.canvas.show_image(switch.get_active())

	def on_image_rbutton_switch(self, button, active, usetag):
		if button.get_active():
			self._mainapp.config["image"]["usetag"] = usetag
			self._mainapp.canvas._rebuild_background()

	def on_image_open_button_click(self, *args):
		dialog = Gtk.FileChooserDialog(
			"Select image file", self.window, Gtk.FileChooserAction.OPEN,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
		)

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			file_ = dialog.get_filename()
			self._mainapp.config["image"]["default"] = file_
			self._mainapp.canvas._rebuild_background()
			self.gui["imagelabel"].set_text("Image: %s" % name_from_file(file_))
			if self._mainapp.is_autocolor_enabled:
				self._mainapp.autocolor.default = None
				self._mainapp.autocolor.color_update(None)

		dialog.destroy()
