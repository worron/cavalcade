# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

from gi.repository import Gtk, Gdk, Gio, GLib
import cavalcade.pixbuf as pixbuf

from cavalcade.logger import logger
from cavalcade.common import set_actions


def bool_to_srt(*values):
	"""Translate list of booleans to string"""
	return ";".join("1" if v else "" for v in values)


# noinspection PyUnusedLocal
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
		self.actions["winstate"] = Gio.SimpleActionGroup()

		ialign_str = bool_to_srt(self.config["image"]["ha"], self.config["image"]["va"])
		ialign_variant = GLib.Variant.new_string(ialign_str)
		ialign_action = Gio.SimpleAction.new_stateful("ialign", ialign_variant.get_type(), ialign_variant)
		ialign_action.connect("change-state", self._on_ialign)
		self.actions["winstate"].add_action(ialign_action)

		hint_variant = GLib.Variant.new_string(self.config["misc"]["hint"].value_nick.upper())
		hint_action = Gio.SimpleAction.new_stateful("hint", hint_variant.get_type(), hint_variant)
		hint_action.connect("change-state", self._on_hint)
		self.actions["winstate"].add_action(hint_action)

		show_image_action = Gio.SimpleAction.new_stateful(
			"image", None, GLib.Variant.new_boolean(self.config["image"]["show"])
		)
		show_image_action.connect("change-state", self._on_show_image)
		self.actions["winstate"].add_action(show_image_action)

		for key, value in self.config["window"].items():
			action = Gio.SimpleAction.new_stateful(key, None, GLib.Variant.new_boolean(value))
			action.connect("change-state", self._on_winstate)
			self.actions["winstate"].add_action(action)

		# signals
		self._mainapp.connect("tag-image-update", self.on_tag_image_update)
		self._mainapp.connect("default-image-update", self.on_default_image_update)

		# cursor control
		self._is_cursor_hidden = False
		self._cursor_hide_timer = None
		self._cursor_hide_timeout = self.config["misc"]["cursor_hide_timeout"] * 1000
		self._launch_cursor_hide_timer()

	@property
	def ready(self):
		return hasattr(self, "window")

	def setup(self):
		"""Init drawing window"""
		self.rebuild_window()
		# fix this
		if not self.config["image"]["show"]:
			self.overlay.remove(self.scrolled)

	def _launch_cursor_hide_timer(self):
		if self._cursor_hide_timer:
			GLib.source_remove(self._cursor_hide_timer)

		self._cursor_hide_timer = GLib.timeout_add(self._cursor_hide_timeout, self._hide_cursor)

	def _hide_cursor(self):
		window = self.window.get_window()

		if window:
			window.set_cursor(Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR))
			self._is_cursor_hidden = True
			self._cursor_hide_timer = None

	def _restore_cursor(self):
		window = self.window.get_window()

		if window:
			cursor = Gdk.Cursor.new_from_name(window.get_display(), 'default')
			window.set_cursor(cursor)
			self._is_cursor_hidden = False

	def _on_motion_notify_event(self, _widget, _event):
		if self._is_cursor_hidden:
			self._restore_cursor()

		self._launch_cursor_hide_timer()

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

	def _on_show_image(self, action, value):
		"""Draw image background or solid paint"""
		action.set_state(value)
		show = value.get_boolean()

		if self.config["image"]["show"] != show:
			self.config["image"]["show"] = show
			if show:
				self.overlay.add(self.scrolled)
				self.rebuild_background()
			else:
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
		"""Resize background image to screen size despite current window size"""
		self.config["window"]["imagebyscreen"] = value
		self.rebuild_background()

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
		return self.screen.get_width(), self.screen.get_height()

	def rebuild_background(self):
		"""Update background according current state"""
		size = self._screen_size() if self.config["window"]["imagebyscreen"] else self.last_size
		if not self.config["image"]["usetag"] or self.tag_image_bytedata is None:
			pb = pixbuf.from_file_at_scale(self.config["image"]["default"], *size)
		else:
			pb = pixbuf.from_bytes_at_scale(self.tag_image_bytedata, *size)
		self.image.set_from_pixbuf(pb)

	# noinspection PyUnusedLocal
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
					self.rebuild_background()

	def set_bg_rgba(self, rgba):
		"""Set window background color"""
		self.window.override_background_color(Gtk.StateFlags.NORMAL, rgba)

	def rebuild_window(self):
		"""
		Recreate main window according current settings.
		This may be useful for update specific window properties.
		"""
		# destroy old window
		if self.ready:
			self.window.remove(self.overlay)
			self._mainapp.remove_window(self.window)
			self.window.destroy()

		# init new
		# noinspection PyAttributeOutsideInit
		self.window = Gtk.ApplicationWindow()
		# noinspection PyAttributeOutsideInit
		self.screen = self.window.get_screen()
		self.window.set_visual(self.screen.get_rgba_visual())
		self._mainapp.add_window(self.window)

		self.window.set_default_size(*self.default_size)

		# set window state according config settings
		for name, value in self.config["window"].items():
			self.set_property(name, value)
		self.window.set_type_hint(self.config["misc"]["hint"])

		# set drawing widget
		self.window.add(self.overlay)

		# signals
		self.window.connect("delete-event", self._mainapp.close)
		self.draw.area.connect("button-press-event", self.on_click)
		self.draw.area.connect('motion-notify-event', self._on_motion_notify_event)
		self.window.connect("check-resize", self._on_size_update)

		self.draw.area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)

		set_actions(self.actions, self.window)

		# show
		self.window.show_all()

	# noinspection PyUnusedLocal
	def on_click(self, widget, event):
		"""Show settings window"""
		# noinspection PyProtectedMember
		if event.type == Gdk.EventType.BUTTON_PRESS:
			self.run_action("settings", "hide")
		elif event.type == Gdk.EventType._2BUTTON_PRESS:
			self.run_action("settings", "show")

	def run_action(self, group, name):
		"""Activate action"""
		action = self.window.get_action_group(group)
		if action is not None:
			action.activate_action(name)

	def set_property(self, name, value):
		"""Set window appearance property"""
		settler = "_set_%s" % name
		if hasattr(self, settler):
			getattr(self, settler)(value)
		else:
			logger.warning("Wrong window property '%s'" % name)

	# noinspection PyUnusedLocal
	def on_tag_image_update(self, sender, bytedata):
		"""New image from mp3 tag"""
		self.tag_image_bytedata = bytedata
		self.rebuild_background()

	# noinspection PyUnusedLocal
	def on_default_image_update(self, sender, file_):
		"""Update default background"""
		self.rebuild_background()
