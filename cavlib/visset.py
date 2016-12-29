# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
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

		# window state
		for key, value in self.canvas.config["state"].items():
			self.gui["st_%s_switch" % key].set_active(value)
			self.gui["st_%s_switch" % key].connect("notify::active", self.on_winstate_switch, key)

		# color
		for key, value in self.canvas.config["color"].items():
			self.gui["%s_colorbutton" % key].set_rgba(value)
			self.gui["%s_colorbutton" % key].connect("color-set", getattr(self, "on_%s_color_set" % key))

		# graph
		for key, value in self.canvas.config["draw"].items():
			self.gui["%s_spinbutton" % key].set_value(value)
			self.gui["%s_spinbutton" % key].connect("value-changed", getattr(self, "on_%s_spinbutton_changed" % key))

		# offset
		for key, value in self.canvas.config["offset"].items():
			self.gui["%s_spinbutton" % key].set_value(value)
			self.gui["%s_spinbutton" % key].connect("value-changed", self.on_offset_spinbutton_changed, key)

	def on_winstate_switch(self, switch, active, key):
		setattr(self.canvas, key, switch.get_active())
		if key == "desktop":
			self.canvas._rebuild_window()

	def on_fg_color_set(self, button):
		self.canvas.config["color"]["fg"] = button.get_rgba()

	def on_bg_color_set(self, button):
		self.canvas.config["color"]["bg"] = button.get_rgba()
		if self.canvas.transparent:
			self.gui["st_transparent_switch"].set_active(False)
		else:
			self.canvas._set_bg_rgba(self.canvas.config["color"]["bg"])

	def on_scale_spinbutton_changed(self, button):
		self.canvas.config["draw"]["scale"] = float(button.get_value())

	def on_padding_spinbutton_changed(self, button):
		self.canvas.config["draw"]["padding"] = int(button.get_value())
		self.canvas.draw.size_update()

	def on_offset_spinbutton_changed(self, button, key):
		self.canvas.config["offset"][key] = int(button.get_value())
		self.canvas.draw.size_update()
