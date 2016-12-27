# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from cavlib.base import GuiBase
from cavlib.logger import logger


class CavaPage(GuiBase):
	"""Settings window"""
	def __init__(self, canvas):
		self.canvas = canvas
		elements = (
			"mainbox", "restart_button", "bars_spinbutton", "sensitivity_spinbutton", "framerate_spinbutton",
		)
		super().__init__("cavaset.glade", elements)

		self.gui["restart_button"].connect("clicked", self.on_restart_button_click)
		self.sp_buttons = ("bars", "sensitivity", "framerate")

		for w in self.sp_buttons:
			self.gui[w + "_spinbutton"].set_value(self.canvas.cavaconfig[w])

	def on_restart_button_click(self, button):
		if self.canvas.cavaconfig.is_fallback:
			logger.error("This changes not permitted while system config file active.")
			return

		for w in self.sp_buttons:
			self.canvas.cavaconfig[w] = int(self.gui[w + "_spinbutton"].get_value())

		self.canvas.cavaconfig.write_data()
		self.canvas.cava.restart()
		self.canvas.draw.size_update()
