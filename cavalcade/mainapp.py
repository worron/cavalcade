# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
import pickle
from gi.repository import Gtk, Gdk, GObject

from cavalcade.config import MainConfig, CavaConfig
from cavalcade.drawing import Spectrum
from cavalcade.cava import Cava
from cavalcade.settings import SettingsWindow
from cavalcade.player import Player
from cavalcade.logger import logger
from cavalcade.autocolor import AutoColor
from cavalcade.canvas import Canvas


class AudioData:
	"""Player session managment helper"""
	def __init__(self, mainapp, options, imported):
		self._mainapp = mainapp
		self.store = os.path.join(self._mainapp.config.path, "store")

		self.files = [file_ for file_ in options.files if file_.endswith(".mp3")]
		self.queue = None

		if options.restore:
			playdata = self.restore()
			if playdata is not None:
				self.files = playdata["list"]
				self.queue = playdata["queue"]
			else:
				logger.warning("Cann't restore previous player session")

		self.enabled = self.files and imported.gstreamer

	def save(self):
		"""Save current playlist"""
		if self.enabled:
			with open(self.store, "wb") as fp:
				playdata = {"list": self._mainapp.player.playlist, "queue": self._mainapp.player.playqueue}
				pickle.dump(playdata, fp)

	def restore(self):
		"""Restore playlist from previous session"""
		if os.path.isfile(self.store):
			with open(self.store, "rb") as fp:
				playdata = pickle.load(fp)
		else:
			playdata = None
		return playdata


class MainApp(Gtk.Application):
	"""Main applicaion class"""
	__gsignals__ = {
		"reset-color": (GObject.SIGNAL_RUN_FIRST, None, ()),
		"tag-image-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
		"default-image-update": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
		"image-source-switch": (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
		"ac-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
	}

	def __init__(self, options, imported):
		# super().__init__(flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, application_id="com.github.worron.clipflap")
		super().__init__(application_id="com.github.worron.cavalcade")

		self.options = options
		self.imported = imported
		self._started = False

	def do_startup(self):
		Gtk.Application.do_startup(self)

		# load config
		self.config = MainConfig()
		self.cavaconfig = CavaConfig()

		# init app structure
		self.adata = AudioData(self, self.options, self.imported)  # audio files manager
		self.draw = Spectrum(self.config, self.cavaconfig)  # graph widget
		self.cava = Cava(self)  # cava wrapper
		self.settings = SettingsWindow(self)  # settings window
		self.canvas = Canvas(self)  # main windo

		# optional image analyzer
		if self.imported.pillow and not self.options.nocolor:
			self.autocolor = AutoColor(self)
		else:
			logger.info("Starting without auto color detection function")

		# optional gstreamer player
		if self.adata.enabled:
			self.player = Player(self)
			self.settings.set_player_page()

			self.player.load_playlist(self.adata.files, self.adata.queue)
			if not self.options.noplay:
				self.player.play_pause()
			else:
				self.emit("reset-color")
		else:
			logger.info("Starting without audio player function")

		# signals
		self.connect("ac-update", self.on_autocolor_update)
		self.connect("default-image-update", self.on_default_image_update)

	def do_activate(self):
		if not self._started:
			self.cava.start()
			self._started = True

	def do_shutdown(self):
		self.cava.close()
		self.adata.save()

		if not self.config.is_fallback:
			self.config.write_data()
		else:
			logger.warning("Application worked with system config file, all settings changes will be lost")

		Gtk.Application.do_shutdown(self)

	def on_autocolor_switch(self, value):
		"""Use color analyzer or user preset"""
		self.config["color"]["auto"] = value
		color = self.config["color"]["autofg"] if value else self.config["color"]["fg"]
		self.settings.visualpage.fg_color_manual_set(color)

	def on_autocolor_update(self, sender, rgba):
		"""New data from color analyzer"""
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

	def on_default_image_update(self, sender, file_):
		"""Update default background"""
		self.canvas._rebuild_background()
		self.emit("reset-color")

	def close(self, *args):
		"""Application exit"""
		self.quit()
