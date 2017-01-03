# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

from gi.repository import Gtk, Gdk
import cavlib.pixbuf as pixbuf

from cavlib.config import MainConfig, CavaConfig
from cavlib.drawing import Spectrum
from cavlib.cava import Cava
from cavlib.settings import SettingsWindow
from cavlib.player import Player
from cavlib.logger import logger
from cavlib.autocolor import AutoColor


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
		self.autocolor = AutoColor(self)  # image analyzer

		# player
		files = [file_ for file_ in argv[1:] if file_.endswith(".mp3")]
		self.player.load_playlist(*files)
		self.player.play_pause()

		# signals
		self.player.connect("image-update", self.on_image_update)
		self.autocolor.connect("ac-update", self.on_autocolor_update)

		# start spectrum analyzer
		self.cava.start()

	def autocolor_switch(self, value):
		self.config["color"]["auto"] = value
		color = self.config["color"]["autofg"] if value else self.config["color"]["fg"]
		self.settings.visualpage.fg_color_manual_set(color)

	def on_image_update(self, sender, bytedata):
		self.canvas.on_image_update(bytedata)
		self.autocolor.color_update(bytedata)

	def on_autocolor_update(self, sender, rgba):
		self.config["color"]["autofg"] = rgba
		if self.config["color"]["auto"]:
			self.settings.visualpage.fg_color_manual_set(rgba)

	def on_click(self, widget, event):
		"""Show settings window"""
		if event.type == Gdk.EventType.BUTTON_PRESS:
			if self.settings.gui["window"].get_property("visible"):
				self.settings.hide()
		elif event.type == Gdk.EventType._2BUTTON_PRESS:
			self.settings.show()

	def close(self, *args):
		"""Program exit"""
		self.cava.close()
		if not self.config.is_fallback:
			self.config.write_data()
		else:
			logger.warning("Application worked with system config file, all settings changes will be lost")
		Gtk.main_quit()


class Canvas:
	"""Helper to work with main window"""
	def __init__(self, mainapp, config, draw_widget):
		self._mainapp = mainapp
		self.config = config
		self.draw = draw_widget

		self.default_size = (1280, 720)  # TODO: Move to config
		self.last_size = (-1, -1)
		self.tag_image_bytedata = None

		# window setup
		self.overlay = Gtk.Overlay()
		self.image = Gtk.Image()
		self.scrolled = Gtk.ScrolledWindow()
		self.scrolled.add(self.image)

		self.overlay.add(self.scrolled)
		self.overlay.add_overlay(self.draw.area)

		self.va = self.scrolled.get_vadjustment()
		self.ha = self.scrolled.get_hadjustment()

		self.rebuild_window()
		# fix this
		if not self.config["image"]["show"]:
			self.overlay.remove(self.scrolled)

	def set_property(self, name, value):
		settler = "_set_%s" % name
		if hasattr(self, settler):
			getattr(self, settler)(value)
		else:
			logger.warning("Wrong window property '%s'" % name)

	def show_image(self, value):
		if self.config["image"]["show"] != value:
			self.config["image"]["show"] = value
			if value:
				self.overlay.add(self.scrolled)
				self._rebuild_background()
			else:
				self.overlay.remove(self.scrolled)

	def set_hint(self, value):
		self.config["hint"] = value
		self.rebuild_window()

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

	def _set_winbyscreen(self, value):
		self.config["state"]["winbyscreen"] = value
		size = self._screen_size() if value else self.default_size
		self.window.move(0, 0)
		self.window.resize(*size)

	def _set_imagebyscreen(self, value):
		self.config["state"]["imagebyscreen"] = value
		self._rebuild_background()

		if self.config["image"]["va"]:
			self.va.set_upper(self.screen.get_height())
			self.va.set_value(self.screen.get_height())
		if self.config["image"]["ha"]:
			self.ha.set_upper(self.screen.get_width())
			self.ha.set_value(self.screen.get_width())

	def _set_bgpaint(self, value):
		self.config["state"]["bgpaint"] = value
		rgba = self.config["color"]["bg"] if value else Gdk.RGBA(0, 0, 0, 0)
		self._set_bg_rgba(rgba)

	def _set_fullscreen(self, value):
		self.config["state"]["fullscreen"] = value
		action = self.window.fullscreen if value else self.window.unfullscreen
		action()

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
		self.window.set_type_hint(self.config["hint"])

		# set drawing widget
		self.window.add(self.overlay)

		# signals
		self.window.connect("delete-event", self._mainapp.close)
		self.draw.area.connect("button-press-event", self._mainapp.on_click)
		self.window.connect("check-resize", self._on_size_update)

		# show
		self.window.show_all()

	def _screen_size(self):
		return (self.screen.get_width(), self.screen.get_height())

	def _rebuild_background(self):
		size = self._screen_size() if self.config["state"]["imagebyscreen"] else self.last_size
		if not self.config["image"]["usetag"] or self.tag_image_bytedata is None:
			pb = pixbuf.from_file_at_scale(self.config["image"]["default"], *size)
		else:
			pb = pixbuf.from_bytes_at_scale(self.tag_image_bytedata, *size)
		self.image.set_from_pixbuf(pb)

	def _on_size_update(self, *args):
		size = self.window.get_size()
		if self.last_size != size:
			self.last_size = size
			if self.config["image"]["show"]:
				if self.config["state"]["imagebyscreen"]:
					self.va.set_value(self.screen.get_height() if self.config["image"]["va"] else 0)
					self.ha.set_value(self.screen.get_width() if self.config["image"]["ha"] else 0)
				else:
					self._rebuild_background()

	def on_image_update(self, bytedata):
		self.tag_image_bytedata = bytedata
		self._rebuild_background()
