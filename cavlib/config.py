# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import shutil

from configparser import ConfigParser
from gi.repository import Gdk
from cavlib.logger import logger


class ConfigBase(dict):
	"""Read some setting from ini file"""
	system_paths = (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"),)
	config_path = os.path.expanduser("~/.config/cavalcade")

	def __init__(self, name, data={}):
		self.name = name
		self.update(data)

		# default config file
		for path in self.system_paths:
			candidate = os.path.join(path, self.name)
			if os.path.isfile(candidate):
				self.defconfig = candidate
				break

		# config directory
		if not os.path.exists(self.config_path):
			os.makedirs(self.config_path)

		# user config file
		self._file = os.path.join(self.config_path, self.name)

		if not os.path.isfile(self._file):
			shutil.copyfile(self.defconfig, self._file)
			logger.info("New configuration file was created:\n%s" % self._file)

		# read file data
		self.parser = ConfigParser()
		try:
			self.parser.read(self._file)
			self.read_data()
			logger.debug("User config '%s' successfully loaded." % self.name)
		except Exception:
			logger.exception("Fail to read '%s' user config:" % self.name)
			logger.info("Trying with default config...")
			self.parser.read(self.defconfig)
			self.read_data()
			logger.debug("Default config '%s' successfully loaded." % self.name)

	def read_data(self):
		"""Read setting"""
		pass


class MainConfig(ConfigBase):
	def __init__(self):
		winstate = dict(desktop=False, maximize=False)
		super().__init__("main.ini", dict(state=winstate))

	def read_data(self):
		self["source"] = self.parser.getint("System", "source")
		self["padding"] = self.parser.getint("Draw", "padding")
		self["scale"] = self.parser.getfloat("Draw", "scale")

		for key in ("left", "right", "top", "bottom"):
			self[key + "_offset"] = self.parser.getint("Offset", key)

		# color
		hex_ = self.parser.get("Draw", "rgba").lstrip("#")
		nums = [int(hex_[i:i + 2], 16) / 255.0 for i in range(0, 7, 2)]
		self["rgba"] = Gdk.RGBA(*nums)

		# window state
		for prop in self["state"]:
			self["state"][prop] = self.parser.getboolean("Window", prop)


class CavaConfig(ConfigBase):
	def __init__(self):
		super().__init__("cava.ini")

	def read_data(self):
		self["bars"] = self.parser.getint("general", "bars")
