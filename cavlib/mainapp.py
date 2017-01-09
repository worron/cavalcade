# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk, Gdk

from cavlib.config import MainConfig, CavaConfig
from cavlib.drawing import Spectrum
from cavlib.cava import Cava
from cavlib.settings import SettingsWindow
from cavlib.player import Player
from cavlib.logger import logger
from cavlib.autocolor import AutoColor
from cavlib.canvas import Canvas


class MainApp:
	"""Base app class"""
	def __init__(self, options, imported):
		# load config
		self.config = MainConfig()
		self.cavaconfig = CavaConfig()
		self.is_autocolor_enabled = imported.pillow and not options.nocolor

		# check if audiofiles availible
		files = [file_ for file_ in options.files if file_.endswith(".mp3")]
		self.is_player_enabled = bool(files) and imported.gstreamer

		# init app structure
		if self.is_player_enabled:
			self.player = Player(self.config)  # gstreamer
			self.player.load_playlist(*files)
			self.player.connect("image-update", self.on_image_update)
		else:
			logger.info("Starting without audio player function")

		self.draw = Spectrum(self.config, self.cavaconfig)  # graph widget
		self.cava = Cava(self.cavaconfig, self.draw.update)  # cava wrapper
		self.settings = SettingsWindow(self)  # settings window
		self.canvas = Canvas(self)  # main window

		if self.is_autocolor_enabled:
			self.autocolor = AutoColor(self)  # image analyzer
			self.autocolor.connect("ac-update", self.on_autocolor_update)
		else:
			logger.info("Starting without auto color detection function")

		# start audio playback
		if self.is_player_enabled and not options.noplay:
			self.player.play_pause()

		# start spectrum analyzer
		self.cava.start()

	def autocolor_switch(self, value):
		self.config["color"]["auto"] = value
		color = self.config["color"]["autofg"] if value else self.config["color"]["fg"]
		self.settings.visualpage.fg_color_manual_set(color)

	def on_image_update(self, sender, bytedata):
		self.canvas.on_image_update(bytedata)
		if self.is_autocolor_enabled:
			self.autocolor.color_update(bytedata)

	def on_autocolor_update(self, sender, rgba):
		self.config["color"]["autofg"] = rgba
		if self.config["color"]["auto"]:
			self.settings.visualpage.fg_color_manual_set(rgba)

	def on_click(self, widget, event):
		"""Show settings window"""
		if event.type == Gdk.EventType.BUTTON_PRESS:
			if self.settings.gui["window"].get_property("visible"):
				self.settings.hide()
		elif event.type == Gdk.EventType._2BUTTON_PRESS:
			self.settings.show()

	def close(self, *args):
		"""Program exit"""
		self.cava.close()
		if not self.config.is_fallback:
			self.config.write_data()
		else:
			logger.warning("Application worked with system config file, all settings changes will be lost")
		Gtk.main_quit()
