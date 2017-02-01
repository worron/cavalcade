# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
import pickle
# from gi.repository import Gtk, GObject, Gio, GLib

# from cavalcade.config import MainConfig, CavaConfig
# from cavalcade.drawing import Spectrum
# from cavalcade.cava import Cava
# from cavalcade.settings import SettingsWindow
# from cavalcade.player import Player
from cavalcade.logger import logger
# from cavalcade.autocolor import AutoColor
# from cavalcade.canvas import Canvas
# from cavalcade.common import set_actions, import_optional


class AudioData:
	"""Player session managment helper"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self.store = os.path.join(self._mainapp.config.path, "store")
		self.files = []
		self.queue = None
		self.updated = False

	def load(self, args):
		"""Get audio files from command arguments list """
		audio = [file_ for file_ in args if file_.endswith(".mp3")]
		if audio:
			self.files = audio
			self.updated = True

	def save(self):
		"""Save current playlist"""
		if self._mainapp.imported.gstreamer:
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

		if playdata is not None:
			self.files = playdata["list"]
			self.queue = playdata["queue"]
			self.updated = True
		else:
			logger.warning("Cann't restore previous player session")

	def send_to_player(self):
		"""Update playlist"""
		if self.updated and self._mainapp.imported.gstreamer:
			self._mainapp.player.load_playlist(self.files, self.queue)
			self.updated = False
