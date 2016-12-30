# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from cavlib.base import GuiBase, WINDOW_HINTS
from gi.repository import Gdk


class VisualPage(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		elements = (
			"mainbox", "st_maximize_switch", "st_below_switch", "hint_combobox", "st_imagebyscreen_switch",
			"st_stick_switch", "st_winbyscreen_switch", "st_transparent_switch", "fg_colorbutton",
			"bg_colorbutton", "padding_spinbutton", "scale_spinbutton", "top_spinbutton", "bottom_spinbutton",
			"left_spinbutton", "right_spinbutton", "hide_button", "exit_button", "st_image_show_switch",
			"st_image_usetag_switch",
		)
		super().__init__("visset.glade", elements)

		# window state
		for key, value in self._mainapp.config["state"].items():
			self.gui["st_%s_switch" % key].set_active(value)
			self.gui["st_%s_switch" % key].connect("notify::active", self.on_winstate_switch, key)

		# color
		for key, value in self._mainapp.config["color"].items():
			self.gui["%s_colorbutton" % key].set_rgba(value)
			self.gui["%s_colorbutton" % key].connect("color-set", getattr(self, "on_%s_color_set" % key))

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

		self.gui["st_image_usetag_switch"].set_active(self._mainapp.config["image"]["usetag"])
		self.gui["st_image_usetag_switch"].connect("notify::active", self.on_image_usetag_switch)

		# misc
		for hint in WINDOW_HINTS:
			self.gui["hint_combobox"].append_text(hint)
		self.gui["hint_combobox"].set_active(WINDOW_HINTS.index(self._mainapp.config["hint"].value_nick.upper()))
		self.gui["hint_combobox"].connect("changed", self.on_hint_combo_changed)

	def on_winstate_switch(self, switch, active, key):
		self._mainapp.canvas.set_property(key, switch.get_active())

	def on_fg_color_set(self, button):
		self._mainapp.config["color"]["fg"] = button.get_rgba()

	def on_bg_color_set(self, button):
		self._mainapp.config["color"]["bg"] = button.get_rgba()
		if self._mainapp.config["state"]["transparent"]:
			self.gui["st_transparent_switch"].set_active(False)
		else:
			self._mainapp.canvas._set_bg_rgba(self._mainapp.config["color"]["bg"])

	def on_scale_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["scale"] = float(button.get_value())

	def on_padding_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["padding"] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_offset_spinbutton_changed(self, button, key):
		self._mainapp.config["offset"][key] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_hint_combo_changed(self, combo):
		text = combo.get_active_text()
		hint = getattr(Gdk.WindowTypeHint, text)
		self._mainapp.canvas.set_hint(hint)

	def on_image_show_switch(self, switch, active):
		self._mainapp.canvas.show_image(switch.get_active())

	def on_image_usetag_switch(self, switch, active):
		self._mainapp.config["image"]["usetag"] = switch.get_active()
		self._mainapp.canvas._rebuild_background()
