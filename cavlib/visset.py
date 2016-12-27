# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
# from gi.repository import Gtk
from cavlib.base import GuiBase


class VisualPage(GuiBase):
	"""Settings window"""
	def __init__(self, canvas):
		self.canvas = canvas
		elements = (
			"maingrid", "st_maximize_switch", "st_desktop_switch", "statebox2", "st_below_switch",
			"st_stick_switch", "st_byscreen_switch", "st_transparent_switch", "fg_colorbutton",
			"bg_colorbutton", "padding_spinbutton", "scale_spinbutton", "top_spinbutton", "bottom_spinbutton",
			"left_spinbutton", "right_spinbutton",
		)
		super().__init__("visset.glade", elements)

		# winstate
		for prop, value in self.canvas.config["state"].items():
			self.gui["st_%s_switch" % prop].set_active(value)
			self.gui["st_%s_switch" % prop].connect("notify::active", self.on_winstate_switch, prop)

		# color
		self.gui["fg_colorbutton"].set_rgba(self.canvas.config["foreground"])
		self.gui["fg_colorbutton"].connect("color-set", self.on_fg_color_set)

		self.gui["bg_colorbutton"].set_rgba(self.canvas.config["background"])
		self.gui["bg_colorbutton"].connect("color-set", self.on_bg_color_set)

		# basr
		self.gui["scale_spinbutton"].set_value(self.canvas.config["scale"])
		self.gui["padding_spinbutton"].set_value(self.canvas.config["padding"])

		self.gui["scale_spinbutton"].connect("value-changed", self.on_scale_spinbutton_changed)
		self.gui["padding_spinbutton"].connect("value-changed", self.on_padding_spinbutton_changed)

		# offset
		for w in ("top", "bottom", "right", "left"):
			self.gui[w + "_spinbutton"].set_value(self.canvas.config[w + "_offset"])
			self.gui[w + "_spinbutton"].connect("value-changed", self.on_offset_spinbutton_changed, w)

	def on_winstate_switch(self, switch, active, key):
		setattr(self.canvas, key, switch.get_active())
		if key == "desktop":
			self.canvas._rebuild_window()

	def on_fg_color_set(self, button):
		self.canvas.config["foreground"] = button.get_rgba()

	def on_bg_color_set(self, button):
		self.canvas.config["background"] = button.get_rgba()
		if self.canvas.transparent:
			self.gui["st_transparent_switch"].set_active(False)
		else:
			self.canvas._set_bg_rgba(self.canvas.config["background"])

	def on_scale_spinbutton_changed(self, button):
		self.canvas.config["scale"] = float(button.get_value())

	def on_padding_spinbutton_changed(self, button):
		self.canvas.config["padding"] = int(button.get_value())
		self.canvas.draw.size_update()

	def on_offset_spinbutton_changed(self, button, key):
		self.canvas.config[key + "_offset"] = int(button.get_value())
		self.canvas.draw.size_update()
