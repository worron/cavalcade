# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

from gi.repository import Gtk, Gdk
import cavlib.pixbuf as pixbuf

from cavlib.logger import logger


class Canvas:
	"""Main window manager"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self.config = mainapp.config
		self.draw = mainapp.draw

		self.default_size = self.config["misc"]["dsize"]
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

	# Base window properties
	def _set_maximize(self, value):
		self.config["window"]["maximize"] = value
		action = self.window.maximize if value else self.window.unmaximize
		action()

	def _set_stick(self, value):
		self.config["window"]["stick"] = value
		action = self.window.stick if value else self.window.unstick
		action()

	def _set_below(self, value):
		self.config["window"]["below"] = value
		self.window.set_keep_below(value)

	def _set_skiptaskbar(self, value):
		self.config["window"]["skiptaskbar"] = value
		self.window.set_skip_taskbar_hint(value)

	def _set_winbyscreen(self, value):
		self.config["window"]["winbyscreen"] = value
		size = self._screen_size() if value else self.default_size
		self.window.move(0, 0)
		self.window.resize(*size)

	def _set_fullscreen(self, value):
		self.config["window"]["fullscreen"] = value
		action = self.window.fullscreen if value else self.window.unfullscreen
		action()

	def _set_imagebyscreen(self, value):
		"""Resize backgrong image to screen size despite current window size"""
		self.config["window"]["imagebyscreen"] = value
		self._rebuild_background()

		if self.config["image"]["va"]:
			self.va.set_upper(self.screen.get_height())
			self.va.set_value(self.screen.get_height())
		if self.config["image"]["ha"]:
			self.ha.set_upper(self.screen.get_width())
			self.ha.set_value(self.screen.get_width())

	def _set_bgpaint(self, value):
		"""Use solid color or transparent background"""
		self.config["window"]["bgpaint"] = value
		rgba = self.config["color"]["bg"] if value else Gdk.RGBA(0, 0, 0, 0)
		self.set_bg_rgba(rgba)

	def _screen_size(self):
		"""Get current screen size"""
		return (self.screen.get_width(), self.screen.get_height())

	def _rebuild_background(self):
		"""Update backgrond according currrent state"""
		size = self._screen_size() if self.config["window"]["imagebyscreen"] else self.last_size
		if not self.config["image"]["usetag"] or self.tag_image_bytedata is None:
			pb = pixbuf.from_file_at_scale(self.config["image"]["default"], *size)
		else:
			pb = pixbuf.from_bytes_at_scale(self.tag_image_bytedata, *size)
		self.image.set_from_pixbuf(pb)

	def _on_size_update(self, *args):
		"""Update window state on size changes"""
		size = self.window.get_size()
		if self.last_size != size:
			self.last_size = size
			if self.config["image"]["show"]:
				if self.config["window"]["imagebyscreen"]:
					self.va.set_value(self.screen.get_height() if self.config["image"]["va"] else 0)
					self.ha.set_value(self.screen.get_width() if self.config["image"]["ha"] else 0)
				else:
					self._rebuild_background()

	def set_bg_rgba(self, rgba):
		"""Set window background color"""
		self.window.override_background_color(Gtk.StateFlags.NORMAL, rgba)

	def rebuild_window(self):
		"""
		Recreate main window according current settings.
		This may be useful for update specific window properties.
		"""
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
		for name, value in self.config["window"].items():
			self.set_property(name, value)
		self.window.set_type_hint(self.config["misc"]["hint"])

		# set drawing widget
		self.window.add(self.overlay)

		# signals
		self.window.connect("delete-event", self._mainapp.close)
		self.draw.area.connect("button-press-event", self._mainapp.on_click)
		self.window.connect("check-resize", self._on_size_update)

		# show
		self.window.show_all()

	def set_property(self, name, value):
		"""Set window appearance property"""
		settler = "_set_%s" % name
		if hasattr(self, settler):
			getattr(self, settler)(value)
		else:
			logger.warning("Wrong window property '%s'" % name)

	def set_hint(self, value):
		"""Set window type  hint"""
		self.config["misc"]["hint"] = value
		self.rebuild_window()

	def show_image(self, value):
		"""Draw image background or solid paint"""
		if self.config["image"]["show"] != value:
			self.config["image"]["show"] = value
			if value:
				self.overlay.add(self.scrolled)
				self._rebuild_background()
			else:
				self.overlay.remove(self.scrolled)

	def update_image(self, bytedata):
		"""New image from mp3 tag"""
		self.tag_image_bytedata = bytedata
		self._rebuild_background()
