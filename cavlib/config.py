# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import shutil

from configparser import ConfigParser
from gi.repository import Gdk
from cavlib.logger import logger
from cavlib.base import WINDOW_HINTS


def hex_rgba(hex_):
	"""Transform html color to gtk rgba"""
	nums = [int(hex_[i:i + 2], 16) / 255.0 for i in range(0, 7, 2)]
	return Gdk.RGBA(*nums)


class ConfigBase(dict):
	"""Read some setting from ini file"""
	system_paths = (os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),)
	config_path = os.path.expanduser("~/.config/cavalcade")

	def __init__(self, name, data={}):
		self.name = name
		self.update(data)
		self.is_fallback = False

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
			self.is_fallback = True
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
		super().__init__("main.ini", dict(state={}, draw = {}, offset = {}, color = {}, image={}))

	def read_data(self):
		# graph
		self["draw"]["padding"] = self.parser.getint("Draw", "padding")
		self["draw"]["scale"] = self.parser.getfloat("Draw", "scale")

		# offset
		for key in ("left", "right", "top", "bottom"):
			self["offset"][key] = self.parser.getint("Offset", key)

		# color
		for key in ("bg", "fg"):
			self["color"][key] = hex_rgba(self.parser.get("Color", key).lstrip("#"))

		# window state
		for key in ("maximize", "below", "stick", "winbyscreen", "transparent", "imagebyscreen"):
			self["state"][key] = self.parser.getboolean("Window", key)

		# image
		self["image"]["show"] = self.parser.getboolean("Image", "show")
		self["image"]["usetag"] = self.parser.getboolean("Image", "usetag")

		image = self.parser.get("Image", "default")
		if not image:
			self["image"]["default"] = os.path.join(os.path.dirname(self.defconfig), "default.svg")
		elif not os.path.isfile(image):
			raise Exception("Wrong default image value")

		# misc
		hint = self.parser.get("Misc", "hint")
		if hint in WINDOW_HINTS:
			self["hint"] = getattr(Gdk.WindowTypeHint, hint)
		else:
			raise Exception("Wrong window type hint '%s'" % hint)


class CavaConfig(ConfigBase):
	def __init__(self):
		self.valid = dict(
			method = ["raw"]
		)
		super().__init__("cava.ini")

	def read_data(self):
		for gw in ("framerate", "bars", "sensitivity"):
			self[gw] = self.parser.getint("general", gw)

		for ow in ("raw_target", "method"):
			self[ow] = self.parser.get("output", ow)

		self["gravity"] = self.parser.getint("smoothing", "gravity")

		for key, valid_values in self.valid.items():
			if self[key] not in valid_values:
				raise Exception("Bad value for '%s' option" % key)

	def write_data(self):
		for section, ini_data in self.parser.items():
			for key in (option for option in ini_data.keys() if option in self.keys()):
				self.parser[section][key] = str(self[key])

		with open(self._file, 'w') as configfile:
			self.parser.write(configfile)
