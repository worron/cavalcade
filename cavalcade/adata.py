# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
import pickle

from cavalcade.logger import logger


class AudioData:
	"""Player session managment helper"""
	def __init__(self, mainapp):
		self.path = os.path.expanduser("~/.local/share/cavalcade")
		if not os.path.exists(self.path):
			os.makedirs(self.path)
		self.store = os.path.join(self.path, "store")

		self._mainapp = mainapp
		self.files = []
		self.queue = None
		self.updated = False

	def load(self, args):
		"""Get audio files from command arguments list """
		audio, broken = [], []
		for item in args:
			audio.append(item) if item.endswith(".mp3") else broken.append(item)

		if audio:
			self.files = audio
			self.updated = True
		if broken:
			logger.warning("Can't load this files:\n%s" % "\n".join(broken))

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
