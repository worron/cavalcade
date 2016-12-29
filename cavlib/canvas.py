# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

from gi.repository import Gtk, Gdk
import cavlib.pixbuf as pixbuf

from cavlib.config import MainConfig, CavaConfig
from cavlib.drawing import Spectrum
from cavlib.cava import Cava
from cavlib.settings import SettingsWindow
from cavlib.player import Player
from cavlib.logger import logger


class MainApp:
	"""Base app class"""
	def __init__(self, argv):
		# load config
		self.config = MainConfig()
		self.cavaconfig = CavaConfig()

		# init app structure
		self.player = Player()  # gstreamer
		self.draw = Spectrum(self.config, self.cavaconfig)  # graph widget
		self.cava = Cava(self.cavaconfig, self.draw.update)  # cava wrapper
		self.settings = SettingsWindow(self)  # settings window
		self.canvas = Canvas(self, self.config, self.draw)  # main window

		# player
		files = [file_ for file_ in argv[1:] if file_.endswith(".mp3")]
		self.player.load_playlist(*files)
		self.player.play_pause()

		# signals
		self.player.connect("image-update", self.canvas.on_image_update)

		# start spectrum analyzer
		self.cava.start()

	def on_click(self, widget, event):
		"""Show settings window"""
		if event.type == Gdk.EventType._2BUTTON_PRESS:
			self.settings.show()

	def close(self, *args):
		"""Program exit"""
		self.cava.close()
		Gtk.main_quit()


class Canvas:
	"""Helper to work with main window"""
	def __init__(self, mainapp, config, draw_widget):
		self._mainapp = mainapp
		self.config = config
		self.draw = draw_widget

		self.default_size = (1280, 720)  # TODO: Move to config
		self.last_size = (-1, -1)
		self.hint = self.config["hint"]
		self.tag_image_bytedata = None

		# window setup
		self.overlay = Gtk.Overlay()
		self.image = Gtk.Image()
		self.scrolled = Gtk.ScrolledWindow()
		self.scrolled.add(self.image)

		self.overlay.add(self.scrolled)
		self.overlay.add_overlay(self.draw.area)

		self.rebuild_window()

	def set_property(self, name, value):
		settler = "_set_%s" % name
		if hasattr(self, settler):
			getattr(self, settler)(value)
		else:
			logger.warning("Wrong window property '%s'" % name)

	def _set_desktop(self, value):
		# window rebuild needed
		self.config["state"]["desktop"] = value
		self.window.set_type_hint(Gdk.WindowTypeHint.DESKTOP if value else self.hint)

	def _set_maximize(self, value):
		self.config["state"]["maximize"] = value
		action = self.window.maximize if value else self.window.unmaximize
		action()

	def _set_stick(self, value):
		self.config["state"]["stick"] = value
		action = self.window.stick if value else self.window.unstick
		action()

	def _set_below(self, value):
		self.config["state"]["below"] = value
		self.window.set_keep_below(value)

	def _set_byscreen(self, value):
		self.config["state"]["byscreen"] = value
		size = (self.screen.get_width(), self.screen.get_height()) if value else self.default_size
		self.window.move(0, 0)
		self.window.resize(*size)

	def _set_transparent(self, value):
		self.config["state"]["transparent"] = value
		rgba = Gdk.RGBA(0, 0, 0, 0) if value else self.config["color"]["bg"]
		self._set_bg_rgba(rgba)

	def _set_bg_rgba(self, rgba):
		self.window.override_background_color(Gtk.StateFlags.NORMAL, rgba)

	def rebuild_window(self):
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
		for name, value in self.config["state"].items():
			self.set_property(name, value)

		# set drawing widget
		self.window.add(self.overlay)

		# signals
		self.window.connect("delete-event", self._mainapp.close)
		self.draw.area.connect("button-press-event", self._mainapp.on_click)
		self.window.connect("check-resize", self._on_size_update)

		# show
		self.window.show_all()

	def _rebuild_background(self):
		if self.tag_image_bytedata is not None:
			pb = pixbuf.from_bytes_at_scale(self.tag_image_bytedata, *self.last_size)
			self.image.set_from_pixbuf(pb)

	def _on_size_update(self, window):
		size = window.get_size()
		if self.last_size != size:
			self.last_size = size
			self._rebuild_background()

	def on_image_update(self, player, bytedata):
		self.tag_image_bytedata = bytedata
		self._rebuild_background()
