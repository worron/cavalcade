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
from cavalcade.adata import AudioData, SavedColors
from cavalcade.common import set_actions, import_optional


class MainApp(Gtk.Application):
	"""Main application class"""
	__gsignals__ = {
		"tag-image-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
		"default-image-update": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
		"image-source-switch": (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
		"autocolor-refresh": (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
		"ac-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
	}

	def __init__(self):
		super().__init__(application_id="com.github.worron.cavalcade", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

		self.add_main_option(
			"play", ord("p"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
			"Start audio playing on launch", None
		)
		self.add_main_option(
			"version", ord("v"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
			"Show application version", None
		)
		self.add_main_option(
			"restore", ord("r"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
			"Restore previous player session", None
		)
		self.add_main_option(
			"quit", ord("q"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
			"Exit program", None
		)
		# this is fake one, real log level set on script launch (see run.py)
		self.add_main_option(
			"log-level", ord("l"), GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
			"Set log level", "LOG_LEVEL"
		)

		self.connect("handle-local-options", self._on_handle_local_options)

	def do_activate(self):
		if not hasattr(self, "canvas"):
			self._do_startup()

		self.canvas.window.present()

	def do_command_line(self, command_line):
		args = command_line.get_arguments()[1:]
		options = command_line.get_options_dict()

		# show version and exit
		if options.contains("version"):
			return 0

		# main app launch
		self.activate()
		self._parse_args(args, options)

		# some special handlers on startup
		if not options.contains("play") and self.imported.pillow and self.config["color"]["auto"]:
			self.autocolor.color_update(self.config["image"]["default"])

		return 0

	def do_shutdown(self):
		if hasattr(self, "canvas"):
			self.cava.close()
			self.adata.save()
			self.palette.save()

			if not self.config.is_fallback:
				self.config.write_data()
			else:
				logger.warning("User config is not available, all settings changes will be lost")

		logger.info("Exit cavalcade")
		Gtk.Application.do_shutdown(self)

	def _do_startup(self):
		"""Main initialization function"""
		# check modules
		logger.info("Start cavalcade")
		self.imported = import_optional()

		# load config
		self.config = MainConfig()
		self.cavaconfig = CavaConfig()

		# init app structure
		self.adata = AudioData(self)  # audio files manager
		self.palette = SavedColors(self)  # custom colors list
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
		self.add_accelerator(self.config["keys"]["play"], "player.play", None)
		self.add_accelerator(self.config["keys"]["next"], "player.next", None)
		self.add_accelerator(self.config["keys"]["exit"], "app.quit", None)
		self.add_accelerator(self.config["keys"]["show"], "settings.show", None)
		self.add_accelerator(self.config["keys"]["hide"], "settings.hide", None)

		# start work
		self.canvas.setup()
		self.cava.start()

	# noinspection PyMethodMayBeStatic
	def _on_handle_local_options(self, _, options):
		"""GUI handler"""
		if options.contains("version"):
			print("version")
		return -1

	def _parse_args(self, args, options):
		"""Parse command line arguments"""
		self.adata.load(args)
		if options.contains("restore"):
			self.adata.restore()
		self.adata.send_to_player()

		if options.contains("play"):
			self.canvas.run_action("player", "play")

		if options.contains("quit"):
			self.close()

	# noinspection PyUnusedLocal
	def close(self, *args):
		"""Application exit"""
		self.quit()
