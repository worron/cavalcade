# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import shutil

from configparser import ConfigParser
from gi.repository import Gdk
from cavlib.logger import logger
from cavlib.base import WINDOW_HINTS


def hex_rgba(hex_):
	"""Transform html color to gtk rgba"""
	purehex = hex_.lstrip("#")
	nums = [int(purehex[i:i + 2], 16) / 255.0 for i in range(0, 7, 2)]
	return Gdk.RGBA(*nums)


def num_to_str(value):
	if isinstance(value, int):
		return str(value)
	elif isinstance(value, float):
		return "{:.2f}".format(value)


def bool_to_str(value):
	return str(int(value))


def rgba_to_str(rgba):
	"""Translate color from Gdk.RGBA to html hex format"""
	return "#%02X%02X%02X%02X" % tuple(int(getattr(rgba, name) * 255) for name in ("red", "green", "blue", "alpha"))


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
		super().__init__("main.ini", dict(state={}, draw = {}, offset = {}, color = {}, image={}, acl = {}))

	def read_data(self):
		# graph
		for key in ("padding", "zero", "silence"):
			self["draw"][key] = self.parser.getint("Draw", key)
		self["draw"]["scale"] = self.parser.getfloat("Draw", "scale")

		# offset
		for key in ("left", "right", "top", "bottom"):
			self["offset"][key] = self.parser.getint("Offset", key)

		# color
		for key in ("bg", "fg", "autofg"):
			self["color"][key] = hex_rgba(self.parser.get("Color", key))
		self["color"]["auto"] = self.parser.getboolean("Color", "auto")

		# autocolor
		for key in ("black", "white", "gray"):
			self["acl"][key] = self.parser.getint("ACL", key)

		# window state
		for key in ("maximize", "below", "stick", "winbyscreen", "bgpaint", "imagebyscreen", "fullscreen"):
			self["state"][key] = self.parser.getboolean("Window", key)

		# image
		for key in ("va", "ha", "usetag", "show"):
			self["image"][key] = self.parser.getboolean("Image", key)

		image = self.parser.get("Image", "default")
		if not image:
			self["image"]["default"] = os.path.join(os.path.dirname(self.defconfig), "DefaultWallpaper.svg")
		elif not os.path.isfile(image):
			raise Exception("Wrong default image value")
		else:
			self["image"]["default"] = image

		# misc
		hint = self.parser.get("Misc", "hint")
		if hint in WINDOW_HINTS:
			self["hint"] = getattr(Gdk.WindowTypeHint, hint)
		else:
			raise Exception("Wrong window type hint '%s'" % hint)

	def write_data(self):
		# nums
		for section in ("Draw", "Offset"):
			for key, value in self[section.lower()].items():
				self.parser[section][key] = num_to_str(value)

		# bools
		for key, value in self["state"].items():
			self.parser["Window"][key] = bool_to_str(value)

		for key, value in self["image"].items():
			if key != "default":
				self.parser["Image"][key] = bool_to_str(value)

		self.parser["Color"]["auto"] = bool_to_str(self["color"]["auto"])

		# colors
		for key, value in self["color"].items():
			if key not in ("auto", "autofg"):
				self.parser["Color"][key] = rgba_to_str(value)

		# misc
		self.parser["Image"]["default"] = self["image"]["default"]
		self.parser["Misc"]["hint"] = self["hint"].value_nick.upper()

		with open(self._file, 'w') as configfile:
			self.parser.write(configfile)


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
