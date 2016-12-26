# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
# from gi.repository import Gtk
from cavlib.base import GuiBase


class VisualPage(GuiBase):
	"""Settings window"""
	def __init__(self, canvas):
		self.canvas = canvas
		elements = (
			"maingrid", "st_maximixe_switch", "st_desktop_switch", "statebox2", "st_below_switch",
			"st_stick_switch", "st_byscreen_switch", "st_transparent_switch",
		)
		super().__init__("visset.glade", elements)

		self.gui["st_desktop_switch"].connect("notify::active", self.on_st_desktop_switch)
		self.gui["st_maximixe_switch"].connect("notify::active", self.on_st_maximize_switch)
		self.gui["st_below_switch"].connect("notify::active", self.on_st_below_switch)
		self.gui["st_stick_switch"].connect("notify::active", self.on_st_stick_switch)
		self.gui["st_byscreen_switch"].connect("notify::active", self.on_st_byscreen_switch)
		self.gui["st_transparent_switch"].connect("notify::active", self.on_st_transparent_switch)

	def on_st_desktop_switch(self, switch, *args):
		self.canvas.desktop = switch.get_active()
		self.canvas._rebuild_window()

	def on_st_maximize_switch(self, switch, *args):
		self.canvas.maximize = switch.get_active()

	def on_st_below_switch(self, switch, *args):
		self.canvas.below = switch.get_active()

	def on_st_stick_switch(self, switch, *args):
		self.canvas.stick = switch.get_active()

	def on_st_byscreen_switch(self, switch, *args):
		self.canvas.byscreen = switch.get_active()

	def on_st_transparent_switch(self, switch, *args):
		self.canvas.transparent = switch.get_active()
