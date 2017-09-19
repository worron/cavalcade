# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
import pickle

from cavalcade.logger import logger, debuginfo


class Storage:
	"""Base class for saving data between sessions"""
	def __init__(self, mainapp, filename):
		self.path = os.path.expanduser("~/.local/share/cavalcade")
		if not os.path.exists(self.path):
			os.makedirs(self.path)
		self.store = os.path.join(self.path, filename)

		self._mainapp = mainapp


class SavedColors(Storage):
	"""Player session management helper"""
	def __init__(self, mainapp):
		super().__init__(mainapp, "colors")

		if os.path.isfile(self.store):
			with open(self.store, "rb") as fp:
				self.colors = pickle.load(fp)
		else:
			self.colors = {}

		logger.debug("Saved colors: %s", self.colors)

	@debuginfo()
	def add_color(self, file_, color):
		self.colors[file_] = color
		return self.colors

	@debuginfo()
	def delete_color(self, file_):
		if file_ in self.colors:
			del self.colors[file_]
		else:
			logger.warning("Wrong color database key %s" % file_)

	@debuginfo()
	def find_color(self, file_):
		return self.colors.get(file_)

	def save(self):
		"""Save current custom colors"""
		with open(self.store, "wb") as fp:
			pickle.dump(self.colors, fp)
		logger.debug("Saved colors:\n%s", self.colors)


class AudioData(Storage):
	"""Player session management helper"""
	def __init__(self, mainapp):
		super().__init__(mainapp, "audio")

		self.files = []
		self.queue = None
		self.updated = False

	def load(self, args):
		"""Get audio files from command arguments list"""
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
			with open(self.store, "r+b") as fp:
				playdata = {"list": self._mainapp.player.playlist, "queue": self._mainapp.player.playqueue}
				if playdata["list"]:
					logger.debug("File list to save:\n%s" % str(playdata))
					pickle.dump(playdata, fp)

	def restore(self):
		"""Restore playlist from previous session"""
		if os.path.isfile(self.store):
			with open(self.store, "rb") as fp:
				playdata = pickle.load(fp)
		else:
			playdata = None

		if playdata is not None:
			logger.debug("Restore audio files list:\n%s" % str(playdata["list"]))
			self.files = playdata["list"]
			self.queue = playdata["queue"]
			self.updated = True
		else:
			logger.warning("Can't restore previous player session")

	def send_to_player(self):
		"""Update playlist"""
		if self.updated and self._mainapp.imported.gstreamer:
			self._mainapp.player.load_playlist(self.files, self.queue)
			self.updated = False
