# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from cavlib.base import GuiBase
from cavlib.logger import logger
from gi.repository import Gtk

OUTPUT_STYLE = ("mono", "stereo")


class CavaPage(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		elements = (
			"mainbox", "restart_button", "bars_spinbutton", "sensitivity_spinbutton", "framerate_spinbutton",
			"lower_cutoff_freq_spinbutton", "higher_cutoff_freq_spinbutton", "gravity_spinbutton",
			"integral_spinbutton", "ignore_spinbutton", "monstercat_switch", "autosens_switch", "style_combobox",
			"eq_treeview",
		)
		super().__init__("cavaset.glade", elements)

		# setup base elements
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

		# setup equalizer
		self.eq_store = Gtk.ListStore(str, float)
		self.gui['renderer_spin'] = Gtk.CellRendererSpin(
			digits=2, editable=True, adjustment=Gtk.Adjustment(1, 0.1, 1, 0.1, 0, 0)
		)
		self.gui['renderer_spin'].connect("edited", self.on_eq_edited)

		column1 = Gtk.TreeViewColumn("Frequency Bands", Gtk.CellRendererText(), text=0)
		column1.set_expand(True)
		column2 = Gtk.TreeViewColumn("Value", self.gui['renderer_spin'], text=1)
		column2.set_min_width(200)
		self.gui['eq_treeview'].append_column(column1)
		self.gui['eq_treeview'].append_column(column2)
		self.gui['eq_treeview'].set_model(self.eq_store)

		for i, value in enumerate(self._mainapp.cavaconfig["eq"]):
			self.eq_store.append(["Frequency band %d" % (i + 1), value])

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

		self._mainapp.cavaconfig["eq"] = [line[1] for line in self.eq_store]

		self._mainapp.cavaconfig.write_data()
		self._mainapp.cava.restart()
		self._mainapp.draw.size_update()

	def on_eq_edited(self, widget, path, text):
		self.eq_store[path][1] = float(text)
