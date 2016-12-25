# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

from gi.repository import Gtk, Gdk

from cavlib.config import MainConfig, CavaConfig
from cavlib.drawing import Spectrum
from cavlib.cava import Cava


class Canvas:
	"""Base window for spectrum display"""
	def __init__(self):

		# init window
		self.window = Gtk.Window()
		self.screen = self.window.get_screen()

		# load config
		self.config = MainConfig()
		self.cavaconfig = CavaConfig()

		# set window state according config settings
		for prop, value in self.config["state"].items():
			setattr(self, prop, value)

		# set window transparent
		self.window.set_visual(self.screen.get_rgba_visual())
		self.window.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0))

		# init drawing widget
		self.draw = Spectrum(self.config, self.cavaconfig)
		self.window.add(self.draw.area)

		# start spectrum analyzer
		self.cava = Cava(self.cavaconfig, self.draw.update)

		# signals
		self.window.connect("delete-event", self.close)
		self.window.connect("check-resize", self.draw.size_update)

		# show window
		self.window.show_all()

	@property
	def desktop(self):
		return self.config["state"]["desktop"]

	@desktop.setter
	def desktop(self, value):
		self.config["state"]["desktop"] = value
		self.window.set_type_hint(Gdk.WindowTypeHint.DESKTOP if value else Gdk.WindowTypeHint.NORMAL)

	@property
	def maximize(self):
		return self.config["state"]["maximize"]

	@maximize.setter
	def maximize(self, value):
		self.config["state"]["maximize"] = value
		action = self.window.maximize if value else self.window.unmaximize
		action()

	def close(self, *args):
		"""Program exit"""
		self.cava.close()
		Gtk.main_quit()
