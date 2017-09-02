# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from cavalcade.common import GuiBase
from cavalcade.logger import logger
from gi.repository import Gtk
from cavalcade.common import AttributeDict


class CavaPage(GuiBase):
	"""CAVA setting page"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		elements = (
			"mainbox", "restart_button", "bars_spinbutton", "sensitivity_spinbutton", "framerate_spinbutton",
			"lower_cutoff_freq_spinbutton", "higher_cutoff_freq_spinbutton", "gravity_spinbutton",
			"integral_spinbutton", "ignore_spinbutton", "monstercat_switch", "autosens_switch", "style_combobox",
			"eq_treeview",
		)
		super().__init__("cavapage.glade", elements=elements)

		# set gui data
		self.gui["bars_spinbutton"].set_adjustment(Gtk.Adjustment(20, 20, 64, 1, 0, 0))
		self.gui["framerate_spinbutton"].set_adjustment(Gtk.Adjustment(30, 12, 60, 1, 0, 0))
		self.gui["sensitivity_spinbutton"].set_adjustment(Gtk.Adjustment(50, 10, 200, 5, 0, 0))
		self.gui["ignore_spinbutton"].set_adjustment(Gtk.Adjustment(0, 0, 50, 1, 0, 0))
		self.gui["gravity_spinbutton"].set_adjustment(Gtk.Adjustment(1, 0, 20, 0.5, 0, 0))
		self.gui["integral_spinbutton"].set_adjustment(Gtk.Adjustment(0.5, 0, 0.99, 0.01, 0, 0))
		self.gui["higher_cutoff_freq_spinbutton"].set_adjustment(Gtk.Adjustment(50, 50, 20000, 10, 0, 0))
		self.gui["lower_cutoff_freq_spinbutton"].set_adjustment(Gtk.Adjustment(50, 50, 20000, 10, 0, 0))

		# some gui constants
		self.OUTPUT_STYLE = ("mono", "stereo")
		self.EQ_STORE = AttributeDict(LABEL=0, VALUE=1)

		# setup base elements
		self.gui["restart_button"].connect("clicked", self.on_restart_button_click)
		self.int_sp_buttons = (
			("general", "framerate"), ("general", "bars"), ("general", "sensitivity"),
			("general", "higher_cutoff_freq"), ("general", "lower_cutoff_freq"), ("smoothing", "ignore")
		)
		self.float_sp_buttons = (("smoothing", "integral"), ("smoothing", "gravity"))
		self.bool_switches = (("smoothing", "monstercat"), ("general", "autosens"))

		for section, key in self.int_sp_buttons + self.float_sp_buttons:
			self.gui[key + "_spinbutton"].set_value(self._mainapp.cavaconfig[section][key])

		for section, key in self.bool_switches:
			self.gui[key + "_switch"].set_active(self._mainapp.cavaconfig[section][key])

		self.gui["style_combobox"].set_active(self.OUTPUT_STYLE.index(self._mainapp.cavaconfig["output"]["style"]))

		# setup equalizer
		self.eq_store = Gtk.ListStore(str, float)
		self.gui['renderer_spin'] = Gtk.CellRendererSpin(
			digits=2, editable=True, adjustment=Gtk.Adjustment(1, 0.1, 1, 0.1, 0, 0)
		)
		self.gui['renderer_spin'].connect("edited", self.on_eq_edited)

		column1 = Gtk.TreeViewColumn("Frequency Bands", Gtk.CellRendererText(), text=self.EQ_STORE.LABEL)
		column1.set_expand(True)
		column2 = Gtk.TreeViewColumn("Value", self.gui['renderer_spin'], text=self.EQ_STORE.VALUE)
		column2.set_min_width(200)

		self.gui['eq_treeview'].append_column(column1)
		self.gui['eq_treeview'].append_column(column2)
		self.gui['eq_treeview'].set_model(self.eq_store)

		for i, value in enumerate(self._mainapp.cavaconfig["eq"]):
			self.eq_store.append(["Frequency band %d" % (i + 1), value])

	# gui handlers
	# noinspection PyUnusedLocal
	def on_restart_button_click(self, button):
		if self._mainapp.cavaconfig.is_fallback:
			logger.error("This changes not permitted while system config file active.")
			return

		# read settings from widgets
		for section, key in self.int_sp_buttons:
			self._mainapp.cavaconfig[section][key] = int(self.gui[key + "_spinbutton"].get_value())

		for section, key in self.float_sp_buttons:
			self._mainapp.cavaconfig[section][key] = self.gui[key + "_spinbutton"].get_value()

		for section, key in self.bool_switches:
			self._mainapp.cavaconfig[section][key] = self.gui[key + "_switch"].get_active()

		self._mainapp.cavaconfig["output"]["style"] = self.gui["style_combobox"].get_active_text().lower()
		self._mainapp.cavaconfig["eq"] = [line[self.EQ_STORE.VALUE] for line in self.eq_store]

		# update settings with current data
		self._mainapp.cavaconfig.write_data()
		self._mainapp.cava.restart()
		self._mainapp.draw.size_update()

	# noinspection PyUnusedLocal
	def on_eq_edited(self, widget, path, text):
		self.eq_store[path][self.EQ_STORE.VALUE] = float(text)
