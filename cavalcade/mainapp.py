# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import gi
import os
import pickle
from gi.repository import Gtk, Gdk, GObject, Gio, GLib

from cavalcade.config import MainConfig, CavaConfig
from cavalcade.drawing import Spectrum
from cavalcade.cava import Cava
from cavalcade.settings import SettingsWindow
from cavalcade.player import Player
from cavalcade.logger import logger
from cavalcade.autocolor import AutoColor
from cavalcade.canvas import Canvas
from cavalcade.common import AttributeDict, set_actions


def import_optional():
	"""Safe module import"""
	success = AttributeDict()
	try:
		gi.require_version('Gst', '1.0')
		from gi.repository import Gst  # noqa: F401
		success.gstreamer = True
	except Exception:
		success.gstreamer = False
		logger.warning("Fail to import Gstreamer module")

	try:
		from PIL import Image  # noqa: F401
		success.pillow = True
	except Exception:
		success.pillow = False
		logger.warning("Fail to import Pillow module")

	return success


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


class MainApp(Gtk.Application):
	"""Main applicaion class"""
	__gsignals__ = {
		"reset-color": (GObject.SIGNAL_RUN_FIRST, None, ()),
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
			log_level = options.lookup_value("debug").get_string() if options.contains("debug") else "DEBUG"
			logger.setLevel(log_level)
			self._do_startup()

		# parse args
		self.adata.load(args)
		if options.contains("restore"):
			self.adata.restore()
		self.adata.send_to_player()

		if options.contains("play"):
			self.settings.run_action("player", "play")

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
		set_actions(self.canvas.actions, self.settings.gui["window"])

		# signals
		self.connect("ac-update", self.on_autocolor_update)
		self.connect("default-image-update", self.on_default_image_update)

		# accelerator
		self.add_accelerator("space", "player.play", None)
		self.add_accelerator("<Control>n", "player.next", None)

		# start work
		self.canvas.setup()
		self.cava.start()

	# signal handlers
	def on_autocolor_update(self, sender, rgba):
		"""New data from color analyzer"""
		self.config["color"]["autofg"] = rgba
		if self.config["color"]["auto"]:
			self.settings.visualpage.gui["fg_colorbutton"].set_rgba(rgba)
			self.draw.color_update()

	def on_click(self, widget, event):
		"""Show settings window"""
		if event.type == Gdk.EventType.BUTTON_PRESS:
			if self.settings.gui["window"].get_property("visible"):
				self.settings.hide()
		elif event.type == Gdk.EventType._2BUTTON_PRESS:
			self.settings.show()

	def on_default_image_update(self, sender, file_):
		"""Update default background"""
		self.canvas._rebuild_background()
		self.emit("reset-color")

	# action handlers
	def close(self, *args):
		"""Application exit"""
		self.quit()
