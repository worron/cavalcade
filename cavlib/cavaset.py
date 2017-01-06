# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from cavlib.base import GuiBase
from cavlib.logger import logger

OUTPUT_STYLE = ("mono", "stereo")


class CavaPage(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		elements = (
			"mainbox", "restart_button", "bars_spinbutton", "sensitivity_spinbutton", "framerate_spinbutton",
			"lower_cutoff_freq_spinbutton", "higher_cutoff_freq_spinbutton", "gravity_spinbutton",
			"integral_spinbutton", "ignore_spinbutton", "monstercat_switch", "autosens_switch", "style_combobox",
		)
		super().__init__("cavaset.glade", elements)

		self.gui["restart_button"].connect("clicked", self.on_restart_button_click)
		self.int_sp_buttons = (
			"framerate", "bars", "sensitivity", "higher_cutoff_freq", "lower_cutoff_freq", "ignore"
		)
		self.float_sp_buttons = ("integral", "gravity")
		self.bool_switches = ("monstercat", "autosens")

		for w in self.int_sp_buttons + self.float_sp_buttons:
			self.gui[w + "_spinbutton"].set_value(self._mainapp.cavaconfig[w])

		for w in self.bool_switches:
			self.gui[w + "_switch"].set_active(self._mainapp.cavaconfig[w])

		self.gui["style_combobox"].set_active(OUTPUT_STYLE.index(self._mainapp.cavaconfig["style"]))

	def on_restart_button_click(self, button):
		if self._mainapp.cavaconfig.is_fallback:
			logger.error("This changes not permitted while system config file active.")
			return

		for w in self.int_sp_buttons:
			self._mainapp.cavaconfig[w] = int(self.gui[w + "_spinbutton"].get_value())

		for w in self.float_sp_buttons:
			self._mainapp.cavaconfig[w] = self.gui[w + "_spinbutton"].get_value()

		for w in self.bool_switches:
			self._mainapp.cavaconfig[w] = self.gui[w + "_switch"].get_active()

		self._mainapp.cavaconfig["style"] = self.gui["style_combobox"].get_active_text().lower()

		self._mainapp.cavaconfig.write_data()
		self._mainapp.cava.restart()
		self._mainapp.draw.size_update()
