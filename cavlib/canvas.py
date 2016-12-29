# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

from gi.repository import Gtk, Gdk
import cavlib.pixbuf as pixbuf

from cavlib.config import MainConfig, CavaConfig
from cavlib.drawing import Spectrum
from cavlib.cava import Cava
from cavlib.settings import SettingsWindow
from cavlib.player import Player


class Canvas:
	"""Base window for spectrum display"""
	def __init__(self, argv):

		# load config
		self.config = MainConfig()
		self.cavaconfig = CavaConfig()

		self.default_size = (1280, 720)  # TODO: Move to config
		self.hint = self.config["hint"]

		# init app structure
		self.player = Player(self)  # gstreamer
		self.draw = Spectrum(self.config, self.cavaconfig)  # graph widget
		self.cava = Cava(self.cavaconfig, self.draw.update)  # cava wrapper
		self.settings = SettingsWindow(self)  # settings window

		# window setup
		self.overlay = Gtk.Overlay()
		self.image = Gtk.Image()
		self.overlay.add(self.image)
		self.overlay.add_overlay(self.draw.area)

		self._rebuild_window()  # graph window

		# player
		files = [file_ for file_ in argv[1:] if file_.endswith(".mp3")]
		self.player.load_playlist(*files)
		self.player.play_pause()

		# signals
		self.player.connect("image-update", self.on_image_update)

		# start spectrum analyzer
		self.cava.start()

	@property
	def desktop(self):
		return self.config["state"]["desktop"]

	@desktop.setter
	def desktop(self, value):
		# window rebuild needed
		self.config["state"]["desktop"] = value
		self.window.set_type_hint(Gdk.WindowTypeHint.DESKTOP if value else self.hint)

	@property
	def maximize(self):
		return self.config["state"]["maximize"]

	@maximize.setter
	def maximize(self, value):
		self.config["state"]["maximize"] = value
		action = self.window.maximize if value else self.window.unmaximize
		action()

	@property
	def stick(self):
		return self.config["state"]["stick"]

	@stick.setter
	def stick(self, value):
		self.config["state"]["stick"] = value
		action = self.window.stick if value else self.window.unstick
		action()

	@property
	def below(self):
		return self.config["state"]["below"]

	@below.setter
	def below(self, value):
		self.config["state"]["below"] = value
		self.window.set_keep_below(value)

	@property
	def byscreen(self):
		return self.config["state"]["byscreen"]

	@byscreen.setter
	def byscreen(self, value):
		self.config["state"]["byscreen"] = value
		size = (self.screen.get_width(), self.screen.get_height()) if value else self.default_size
		self.window.move(0, 0)
		self.window.resize(*size)

	@property
	def transparent(self):
		return self.config["state"]["transparent"]

	@transparent.setter
	def transparent(self, value):
		self.config["state"]["transparent"] = value
		rgba = Gdk.RGBA(0, 0, 0, 0) if value else self.config["background"]
		self._set_bg_rgba(rgba)

	def _set_bg_rgba(self, rgba):
		self.window.override_background_color(Gtk.StateFlags.NORMAL, rgba)

	def _rebuild_window(self):
		# destroy old window
		if hasattr(self, "window"):
			self.window.remove(self.overlay)
			self.window.destroy()

		# init new
		self.window = Gtk.Window()
		self.screen = self.window.get_screen()
		self.window.set_visual(self.screen.get_rgba_visual())

		self.window.set_default_size(*self.default_size)

		# set window state according config settings
		for prop, value in self.config["state"].items():
			setattr(self, prop, value)

		# set drawing widget
		self.window.add(self.overlay)

		# signals
		self.window.connect("delete-event", self.close)
		self.draw.area.connect("button-press-event", self.on_click)

		# show
		self.window.show_all()

	def on_image_update(self, player, bytedata):
		pb = pixbuf.from_bytes(bytedata)
		self.image.set_from_pixbuf(pb)

	def on_click(self, widget, event):
		"""Show settings window"""
		if event.type == Gdk.EventType._2BUTTON_PRESS:
			self.settings.show()

	def close(self, *args):
		"""Program exit"""
		self.cava.close()
		Gtk.main_quit()
