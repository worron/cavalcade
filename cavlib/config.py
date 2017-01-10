# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import shutil

from configparser import ConfigParser
from gi.repository import Gdk
from cavlib.logger import logger
from cavlib.common import AttributeDict, WINDOW_HINTS

HINTS = [getattr(Gdk.WindowTypeHint, hint) for hint in WINDOW_HINTS]


def str_to_rgba(hex_):
	"""Transform html color to gtk rgba"""
	purehex = hex_.lstrip("#")
	nums = [int(purehex[i:i + 2], 16) / 255.0 for i in range(0, 7, 2)]
	return Gdk.RGBA(*nums)


def rgba_to_str(rgba):
	"""Translate color from Gdk.RGBA to html hex format"""
	return "#%02X%02X%02X%02X" % tuple(int(getattr(rgba, name) * 255) for name in ("red", "green", "blue", "alpha"))


class ConfigBase(dict):
	"""Read some setting from ini file"""
	system_location = (os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),)
	config_path = os.path.expanduser("~/.config/cavalcade")

	def __init__(self, name, pattern={}):
		self.name = name
		self.pattern = pattern
		self.is_fallback = False

		# read functions
		self.reader = {
			int: lambda section, option: self.parser.getint(section, option),
			bool: lambda section, option: self.parser.getboolean(section, option),
			str: lambda section, option: self.parser.get(section, option),
			float: lambda section, option: self.parser.getfloat(section, option),
			"ilist": lambda section, option: [int(v.strip()) for v in self.parser.get(section, option).split(";")],
			"hint": lambda section, option: getattr(Gdk.WindowTypeHint, self.parser.get(section, option)),
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
			Gdk.RGBA: lambda value: rgba_to_str(value),
		}

		# init
		self._init_config_file()
		self._load_config_file()

	def _init_config_file(self):
		"""Set user config directory and file"""
		for path in self.system_location:
			candidate = os.path.join(path, self.name)
			if os.path.isfile(candidate):
				self.defconfig = candidate
				break

		if not os.path.exists(self.config_path):
			os.makedirs(self.config_path)

		self._file = os.path.join(self.config_path, self.name)

		if not os.path.isfile(self._file):
			shutil.copyfile(self.defconfig, self._file)
			logger.info("New configuration file was created:\n%s" % self._file)

	def _load_config_file(self):
		"""Read raw config data"""
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
		"""Read settings"""
		for section in self.pattern.keys():
			self[section] = dict()
			for option, pattern in self.pattern[section].items():
				reader = self.reader[pattern.type]
				self[section][option] = reader(section, option)
				if "valid" in pattern and self[section][option] not in pattern.valid:
					raise Exception("Bad value for '%s' in '%s'" % (option, section))

	def write_data(self):
		"""Read settings"""
		for section in self.pattern.keys():
			for option, pattern in self.pattern[section].items():
				writer = self.writer[pattern.type]
				self.parser[section][option] = writer(self[section][option])

	def save_data(self):
		"""Save settings to file"""
		with open(self._file, 'w') as configfile:
			self.parser.write(configfile)


class CavaConfig(ConfigBase):
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
					style = AttributeDict(type=str),
				),
				smoothing = dict(
					gravity = AttributeDict(type=float),
					integral = AttributeDict(type=float),
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
				),
				image = dict(
					show = AttributeDict(type=bool),
					usetag = AttributeDict(type=bool),
					va = AttributeDict(type=bool),
					ha = AttributeDict(type=bool),
					default = AttributeDict(type=str)
				),
				aco = dict(
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
					hint = AttributeDict(type="hint", valid=HINTS)
				),
			)
		)

	def read_data(self):
		super().read_data()

		if not self["image"]["default"]:
			self["image"]["default"] = os.path.join(os.path.dirname(self.defconfig), "DefaultWallpaper.svg")
		elif not os.path.isfile(self["image"]["default"]):
			raise Exception("Wrong default image file")

	def write_data(self):
		super().write_data()
		self.save_data()
