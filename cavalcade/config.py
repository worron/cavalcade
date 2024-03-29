# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import shutil

from configparser import ConfigParser
from gi.repository import Gdk
from cavalcade.logger import logger
from cavalcade.common import AttributeDict, WINDOW_HINTS, AccelCheck

GTK_WINDOW_TYPE_HINTS = [getattr(Gdk.WindowTypeHint, hint) for hint in WINDOW_HINTS]
DEFAULT_WALLPAPER_FILE = "DefaultWallpaper.svg"
accel = AccelCheck()


def str_to_rgba(hex_):
	"""Translate color from hex string to Gdk.RGBA"""
	pure_hex = hex_.lstrip("#")
	nums = [int(pure_hex[i:i + 2], 16) / 255.0 for i in range(0, 7, 2)]
	return Gdk.RGBA(*nums)


def rgba_to_str(rgba):
	"""Translate color from Gdk.RGBA to hex format"""
	return "#%02X%02X%02X%02X" % tuple(int(getattr(rgba, name) * 255) for name in ("red", "green", "blue", "alpha"))


class ConfigBase(dict):
	"""Base for config manager"""
	system_location = (os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),)
	path = os.path.expanduser("~/.config/cavalcade")

	def __init__(self, name, pattern=None):
		super().__init__()
		self.name = name
		self.pattern = pattern if pattern is not None else {}
		self.is_fallback = False

		# read functions
		self.reader = {
			int: lambda section, option: self.parser.getint(section, option),
			bool: lambda section, option: self.parser.getboolean(section, option),
			str: lambda section, option: self.parser.get(section, option),
			float: lambda section, option: self.parser.getfloat(section, option),
			"ilist": lambda section, option: [int(v.strip()) for v in self.parser.get(section, option).split(";")],
			"hint": lambda section, option: getattr(Gdk.WindowTypeHint, self.parser.get(section, option)),
			"accel": lambda section, option: self.parser.get(section, option),
			Gdk.RGBA: lambda section, option: str_to_rgba(self.parser.get(section, option)),
		}

		# write functions
		self.writer = {
			int: lambda value: str(value),
			bool: lambda value: str(int(value)),
			str: lambda value: value,
			float: lambda value: "{:.2f}".format(value),
			"ilist": lambda value: ";".join(str(i) for i in value),
			"hint": lambda value: value.value_nick.upper(),
			"accel": lambda value: value,
			Gdk.RGBA: lambda value: rgba_to_str(value),
		}

		# init
		self._init_config_file()
		self._load_config_file()

	def _init_config_file(self):
		"""Setup user config directory and file"""
		for path in self.system_location:
			candidate = os.path.join(path, self.name)
			if os.path.isfile(candidate):
				self.defconfig = candidate
				break

		if not os.path.exists(self.path):
			os.makedirs(self.path)

		self.file = os.path.join(self.path, self.name)

		if not os.path.isfile(self.file):
			shutil.copyfile(self.defconfig, self.file)
			logger.info("New configuration file was created:\n%s" % self.file)

	def _load_config_file(self):
		"""Read raw config data"""
		self.parser = ConfigParser()
		try:
			self.parser.read(self.file)
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
		"""Transform raw config data to user specified types"""
		for section in self.pattern.keys():
			self[section] = dict()
			for option, pattern in self.pattern[section].items():
				reader = self.reader[pattern.type]
				self[section][option] = reader(section, option)
				if "valid" in pattern and self[section][option] not in pattern.valid:
					raise Exception("Bad value for '%s' in '%s'" % (option, section))

	def write_data(self):
		"""Transform user specified data to raw config parser strings"""
		for section in self.pattern.keys():
			for option, pattern in self.pattern[section].items():
				writer = self.writer[pattern.type]
				self.parser[section][option] = writer(self[section][option])

	def save_data(self):
		"""Save settings to file"""
		with open(self.file, 'w') as configfile:
			self.parser.write(configfile)


class CavaConfig(ConfigBase):
	"""CAVA config manager"""
	def __init__(self):
		super().__init__(
			"cava.ini", dict(
				general = dict(
					bars = AttributeDict(type=int),
					sensitivity = AttributeDict(type=int),
					framerate = AttributeDict(type=int),
					lower_cutoff_freq = AttributeDict(type=int),
					higher_cutoff_freq = AttributeDict(type=int),
					autosens = AttributeDict(type=bool),
				),
				output = dict(
					method = AttributeDict(type=str, valid=["raw"]),
					raw_target = AttributeDict(type=str),
					channels = AttributeDict(type=str),
					bit_format = AttributeDict(type=str, valid=["16bit", "8bit"]),
				),
				smoothing = dict(
					gravity = AttributeDict(type=int),
					integral = AttributeDict(type=int),
					ignore = AttributeDict(type=int),
					monstercat = AttributeDict(type=bool),
				),
			)
		)

	def read_data(self):
		super().read_data()
		self["eq"] = [float(v) for v in self.parser["eq"].values()]

	def write_data(self):
		super().write_data()

		for i, key in enumerate(self.parser["eq"].keys()):
			self.parser["eq"][key] = "{:.2f}".format(self["eq"][i])

		self.save_data()


class MainConfig(ConfigBase):
	"""Main application config manager"""
	def __init__(self):
		super().__init__(
			"main.ini", dict(
				draw = dict(
					padding = AttributeDict(type=int),
					zero = AttributeDict(type=int),
					silence = AttributeDict(type=int),
					scale = AttributeDict(type=float),
				),
				color = dict(
					fg = AttributeDict(type=Gdk.RGBA),
					autofg = AttributeDict(type=Gdk.RGBA),
					bg = AttributeDict(type=Gdk.RGBA),
					auto = AttributeDict(type=bool),
				),
				offset = dict(
					left = AttributeDict(type=int),
					right = AttributeDict(type=int),
					top = AttributeDict(type=int),
					bottom = AttributeDict(type=int),
				),
				window = dict(
					maximize = AttributeDict(type=bool),
					below = AttributeDict(type=bool),
					stick = AttributeDict(type=bool),
					winbyscreen = AttributeDict(type=bool),
					imagebyscreen = AttributeDict(type=bool),
					bgpaint = AttributeDict(type=bool),
					fullscreen = AttributeDict(type=bool),
					skiptaskbar = AttributeDict(type=bool),
				),
				image = dict(
					show = AttributeDict(type=bool),
					usetag = AttributeDict(type=bool),
					va = AttributeDict(type=bool),
					ha = AttributeDict(type=bool),
					default = AttributeDict(type=str)
				),
				autocolor = dict(
					bands = AttributeDict(type=int),
					window = AttributeDict(type=int),
					saturation_min = AttributeDict(type=float),
					value_min = AttributeDict(type=float),
					isize = AttributeDict(type="ilist"),
				),
				player = dict(
					volume = AttributeDict(type=float),
					shuffle = AttributeDict(type=bool),
					showqueue = AttributeDict(type=bool),
				),
				misc = dict(
					hint = AttributeDict(type="hint", valid=GTK_WINDOW_TYPE_HINTS),
					dsize = AttributeDict(type="ilist"),
					cursor_hide_timeout = AttributeDict(type=int),

				),
				keys = dict(
					exit = AttributeDict(type="accel", valid=accel),
					next = AttributeDict(type="accel", valid=accel),
					play = AttributeDict(type="accel", valid=accel),
					show = AttributeDict(type="accel", valid=accel),
					hide = AttributeDict(type="accel", valid=accel),
				),
			)
		)

	def read_data(self):
		super().read_data()
		self._validate_default_bg()

	def _validate_default_bg(self):
		if not self["image"]["default"]:
			logger.info("Default wallpaper not defined, setting config option to fallback value.")
			self._set_fallback_bg()
		elif not os.path.isfile(self["image"]["default"]):
			logger.warning("Default wallpaper file not valid, resetting config option to fallback value.")
			self._set_fallback_bg()

	def _set_fallback_bg(self):
		self["image"]["default"] = os.path.join(os.path.dirname(self.defconfig), DEFAULT_WALLPAPER_FILE)

	def write_data(self):
		super().write_data()
		self.save_data()
