# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

from gi.repository import Gtk, Gdk, Gio, GLib
import cavalcade.pixbuf as pixbuf

from cavalcade.logger import logger
from cavalcade.common import set_actions


def bool_to_srt(*values):
	"""Translate list of booleans to string"""
	return ";".join("1" if v else "" for v in values)


class Canvas:
	"""Main window manager"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self.config = mainapp.config
		self.draw = mainapp.draw

		self.default_size = self.config["misc"]["dsize"]
		self.last_size = (-1, -1)
		self.tag_image_bytedata = None
		self.actions = {}

		# window setup
		self.overlay = Gtk.Overlay()
		self.image = Gtk.Image()
		self.scrolled = Gtk.ScrolledWindow()
		self.scrolled.add(self.image)

		self.overlay.add(self.scrolled)
		self.overlay.add_overlay(self.draw.area)

		self.va = self.scrolled.get_vadjustment()
		self.ha = self.scrolled.get_hadjustment()

		# actions
		winstate_action_group = Gio.SimpleActionGroup()

		ialign_str = bool_to_srt(self.config["image"]["ha"], self.config["image"]["va"])
		ialign_variant = GLib.Variant.new_string(ialign_str)
		ialign_action = Gio.SimpleAction.new_stateful("ialign", ialign_variant.get_type(), ialign_variant)
		ialign_action.connect("change-state", self._on_ialign)
		winstate_action_group.add_action(ialign_action)

		hint_variant = GLib.Variant.new_string(self.config["misc"]["hint"].value_nick.upper())
		hint_action = Gio.SimpleAction.new_stateful("hint", hint_variant.get_type(), hint_variant)
		hint_action.connect("change-state", self._on_hint)
		winstate_action_group.add_action(hint_action)

		for key, value in self.config["window"].items():
			action = Gio.SimpleAction.new_stateful(key, None, GLib.Variant.new_boolean(value))
			action.connect("change-state", self._on_winstate)
			winstate_action_group.add_action(action)

		self.actions["winstate"] = winstate_action_group

		# build setup
		self.rebuild_window()
		# fix this
		if not self.config["image"]["show"]:
			self.overlay.remove(self.scrolled)

		# signals
		self.overlay.connect("key-press-event", self._on_key_press)
		self._mainapp.connect("tag-image-update", self.on_image_update)

	# action handlers
	def _on_ialign(self, action, value):
		action.set_state(value)
		state = [bool(s) for s in value.get_string().split(";")]
		self.config["image"]["ha"], self.config["image"]["va"] = state

	def _on_winstate(self, action, value):
		action.set_state(value)
		self.set_property(action.get_name(), value.get_boolean())

	def _on_hint(self, action, value):
		"""Set window type  hint"""
		action.set_state(value)
		self.config["misc"]["hint"] = getattr(Gdk.WindowTypeHint, value.get_string())
		self.rebuild_window()

	def _on_key_press(self, widget, event):
		if self._mainapp.adata.enabled:  # fix this
			if event.keyval == Gdk.KEY_space:
				self._mainapp.player.play_pause()
			elif event.keyval == Gdk.KEY_Right:
				self._mainapp.player.play_next()

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
		"""Resize backgroung image to screen size despite current window size"""
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

		set_actions(self.actions, self.window)

		# show
		self.window.show_all()

	def set_property(self, name, value):
		"""Set window appearance property"""
		settler = "_set_%s" % name
		if hasattr(self, settler):
			getattr(self, settler)(value)
		else:
			logger.warning("Wrong window property '%s'" % name)

	def show_image(self, value):
		"""Draw image background or solid paint"""
		if self.config["image"]["show"] != value:
			self.config["image"]["show"] = value
			if value:
				self.overlay.add(self.scrolled)
				self._rebuild_background()
			else:
				self.overlay.remove(self.scrolled)

	def on_image_update(self, sender, bytedata):
		"""New image from mp3 tag"""
		self.tag_image_bytedata = bytedata
		self._rebuild_background()
