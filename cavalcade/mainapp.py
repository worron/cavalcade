# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk, GObject, Gio, GLib

from cavalcade.config import MainConfig, CavaConfig
from cavalcade.drawing import Spectrum
from cavalcade.cava import Cava
from cavalcade.settings import SettingsWindow
from cavalcade.player import Player
from cavalcade.logger import logger
from cavalcade.autocolor import AutoColor
from cavalcade.canvas import Canvas
from cavalcade.adata import AudioData
from cavalcade.common import set_actions, import_optional


class MainApp(Gtk.Application):
	"""Main applicaion class"""
	__gsignals__ = {
		"tag-image-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
		"default-image-update": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
		"image-source-switch": (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
		"ac-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
	}

	def __init__(self):
		super().__init__(application_id="com.github.worron.cavalcade", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

		self.add_main_option(
			"play", ord("p"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
			"Start audio playing on launch", None
		)
		self.add_main_option(
			"restore", ord("r"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
			"Restore previous player session", None
		)
		self.add_main_option(
			"debug", ord("d"), GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
			"Set log level", "LOG_LEVEL"
		)

	def do_command_line(self, command_line):
		args = command_line.get_arguments()[1:]
		options = command_line.get_options_dict()

		# startup
		if not hasattr(self, "canvas"):
			# setup logeer
			log_level = options.lookup_value("debug").get_string() if options.contains("debug") else "DEBUG"
			logger.setLevel(log_level)

			# main app launch
			self._do_startup()
			self._parse_args(args, options)

			# some special hadlers on startup
			if not options.contains("play") and self.imported.pillow and self.config["color"]["auto"]:
				self.autocolor.color_update(self.config["image"]["default"])
			return 0

		self._parse_args(args, options)

		return 0

	def do_shutdown(self):
		self.cava.close()
		self.adata.save()

		if not self.config.is_fallback:
			self.config.write_data()
		else:
			logger.warning("User config is not available, all settings changes will be lost")

		logger.info("Exit cavalcade")
		Gtk.Application.do_shutdown(self)

	def _do_startup(self):
		"""
		Main initialization function.
		Use this one to make all setup AFTER command line parsing completed.
		"""
		# check modules
		logger.info("Start cavalcade")
		self.imported = import_optional()

		# load config
		self.config = MainConfig()
		self.cavaconfig = CavaConfig()

		# init app structure
		self.adata = AudioData(self)  # audio files manager
		self.draw = Spectrum(self.config, self.cavaconfig)  # graph widget
		self.cava = Cava(self)  # cava wrapper
		self.settings = SettingsWindow(self)  # settings window
		self.canvas = Canvas(self)  # main window

		# optional image analyzer
		if self.imported.pillow:
			self.autocolor = AutoColor(self)
		else:
			logger.info("Starting without auto color detection function")

		# optional gstreamer player
		if self.imported.gstreamer:
			self.player = Player(self)
			self.settings.add_player_page()
			self.canvas.actions.update(self.player.actions)
		else:
			logger.info("Starting without audio player function")

		# set actions
		quit_action = Gio.SimpleAction.new("quit", None)
		quit_action.connect("activate", self.close)
		self.add_action(quit_action)

		# share actions
		self.canvas.actions.update(self.settings.actions)
		set_actions(self.canvas.actions, self.settings.gui["window"])

		# accelerators
		self.add_accelerator("space", "player.play", None)
		self.add_accelerator("<Control>n", "player.next", None)

		# start work
		self.canvas.setup()
		self.cava.start()

	def _parse_args(self, args, options):
		"""Parse command line arguments """
		self.adata.load(args)
		if options.contains("restore"):
			self.adata.restore()
		self.adata.send_to_player()

		if options.contains("play"):
			self.canvas.run_action("player", "play")

	def close(self, *args):
		"""Application exit"""
		self.quit()
