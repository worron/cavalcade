# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
import pickle
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
	"""Main applicaion class"""
	def __init__(self, options, imported):
		# load config
		self.config = MainConfig()
		self.cavaconfig = CavaConfig()

		self.is_autocolor_enabled = imported.pillow and not options.nocolor
		self.playstore = os.path.join(self.config.path, "store")
		self.playdata = None

		# check if audiofiles available
		files = [file_ for file_ in options.files if file_.endswith(".mp3")]
		if options.restore:
			self.playdata = self.restore_playdata()
			if self.playdata is not None:
				files = self.playdata["list"]
			else:
				logger.warning("Cann't restore previous player session")

		self.is_player_enabled = bool(files) and imported.gstreamer
		self.restore_playdata()

		# init app structure
		if self.is_player_enabled:
			self.player = Player(self.config)  # gstreamer
			self.player.connect("image-update", self.on_image_update)
		else:
			logger.info("Starting without audio player function")

		self.draw = Spectrum(self.config, self.cavaconfig)  # graph widget
		self.cava = Cava(self)  # cava wrapper
		self.settings = SettingsWindow(self)  # settings window
		self.canvas = Canvas(self)  # main windo

		if self.is_autocolor_enabled:
			self.autocolor = AutoColor(self)  # image analyzer
			self.autocolor.connect("ac-update", self.on_autocolor_update)
		else:
			logger.info("Starting without auto color detection function")

		# start audio playback
		if self.is_player_enabled:
			queue = self.playdata["queue"] if (options.restore and self.playstore is not None) else None
			self.player.load_playlist(files, queue)
			if not options.noplay:
				self.player.play_pause()
			elif self.is_autocolor_enabled:
				self.autocolor.reset_default_color()

		# start spectrum analyzer
		self.cava.start()

	def on_image_source_switch(self, usetag):
		"""Use default background or image from mp3 tag"""
		self.config["image"]["usetag"] = usetag
		self.canvas._rebuild_background()
		if self.is_autocolor_enabled and self.config["color"]["auto"]:
			self.autocolor.color_update(self.canvas.tag_image_bytedata if usetag else None)

	def on_autocolor_switch(self, value):
		"""Use color analyzer or user preset"""
		self.config["color"]["auto"] = value
		color = self.config["color"]["autofg"] if value else self.config["color"]["fg"]
		self.settings.visualpage.fg_color_manual_set(color)

	def on_image_update(self, sender, bytedata):
		"""New image from mp3 tag"""
		self.canvas.update_image(bytedata)
		if self.is_autocolor_enabled:
			self.autocolor.color_update(bytedata if self.config["image"]["usetag"] else None)

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

	def default_image_update(self, file_):
		"""Set new default background """
		self.config["image"]["default"] = file_
		self.canvas._rebuild_background()
		if self.is_autocolor_enabled:
			self.autocolor.reset_default_color()

	def save_playdata(self):
		"""Save current playlist"""
		if self.is_player_enabled:
			playdata = {"list": self.player.playlist, "queue": self.player.playqueue}
			with open(self.playstore, "wb") as fp:
				pickle.dump(playdata, fp)

	def restore_playdata(self):
		"""Restore playlist from previous session"""
		if os.path.isfile(self.playstore):
			with open(self.playstore, "rb") as fp:
				playdata = pickle.load(fp)
		else:
			playdata = None
		return playdata

	def close(self, *args):
		"""Application exit"""
		self.cava.close()
		self.save_playdata()
		if not self.config.is_fallback:
			self.config.write_data()
		else:
			logger.warning("Application worked with system config file, all settings changes will be lost")
		Gtk.main_quit()
