# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os

from collections import OrderedDict
from cavalcade.common import GuiBase, WINDOW_HINTS, name_from_file
from cavalcade.common import gtk_open_file
from gi.repository import Gdk, Gtk, Gio, GLib

CORNERS = (
	("TOP_LEFT", (False, False)),
	("TOP_RIGHT", (True, False)),
	("BOTTOM_LEFT", (False, True)),
	("BOTTOM_RIGHT", (True, True)),
)


class VisualPage(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp, settings_window):
		self._mainapp = mainapp
		self.window = settings_window
		elements = (
			"mainbox", "hint_combobox", "st_imagebyscreen_switch", "fg_colorbutton",
			"bg_colorbutton", "padding_spinbutton", "scale_spinbutton", "top_spinbutton", "bottom_spinbutton",
			"left_spinbutton", "right_spinbutton", "hide_button", "exit_button", "st_image_show_switch",
			"image_file_rbutton", "image_tag_rbutton", "imagelabel", "image_open_button", "corner_combobox",
			"autocolor_switch", "zero_spinbutton", "silence_spinbutton", "winstate-menubutton", "winstate-menu",
		)
		super().__init__("visset.glade", "winstate.ui", elements=elements)

		# set menu buttons
		# TODO: move image setting to ui files
		self.gui["winstate-menubutton"].set_menu_model(self.gui["winstate-menu"])
		self.gui["winstate-menubutton"].set_image(Gtk.Image(icon_name="emblem-system-symbolic"))

		# some gui constants
		self.CORNERS = OrderedDict(
			TOP_LEFT = (False, False),
			TOP_RIGHT = (True, False),
			BOTTOM_LEFT = (False, True),
			BOTTOM_RIGHT = (True, True),
		)

		# image file filter
		self.image_filter = Gtk.FileFilter()
		self.image_filter.set_name("Image files")
		self.image_filter.add_pixbuf_formats()

		# actions
		winstate_actiongroup = Gio.SimpleActionGroup()
		for key, value in self._mainapp.config["window"].items():
			action = Gio.SimpleAction.new_stateful(key, None, GLib.Variant.new_boolean(value))
			action.connect("activate", self.on_winstate)
			winstate_actiongroup.add_action(action)

		self.window.insert_action_group("winstate", winstate_actiongroup)

		# color
		for key, value in self._mainapp.config["color"].items():
			if key in ("fg", "bg"):
				self.gui["%s_colorbutton" % key].set_rgba(value)
				self.gui["%s_colorbutton" % key].connect("color-set", getattr(self, "on_%s_color_set" % key))
			elif key == "auto":
				self.gui["autocolor_switch"].set_active(not value)  # autocolor
				self.gui["autocolor_switch"].connect("notify::active", self.on_autocolor_switch)

		# graph
		for key, value in self._mainapp.config["draw"].items():
			self.gui["%s_spinbutton" % key].set_value(value)
			self.gui["%s_spinbutton" % key].connect("value-changed", getattr(self, "on_%s_spinbutton_changed" % key))

		# offset
		for key, value in self._mainapp.config["offset"].items():
			self.gui["%s_spinbutton" % key].set_value(value)
			self.gui["%s_spinbutton" % key].connect("value-changed", self.on_offset_spinbutton_changed, key)

		# image
		self.gui["st_image_show_switch"].set_active(self._mainapp.config["image"]["show"])
		self.gui["st_image_show_switch"].connect("notify::active", self.on_image_show_switch)

		self.gui["imagelabel"].set_text("Image: %s" % name_from_file(self._mainapp.config["image"]["default"]))

		image_rb = "image_tag_rbutton" if self._mainapp.config["image"]["usetag"] else "image_file_rbutton"
		self.gui[image_rb].set_active(True)

		self.gui["image_tag_rbutton"].connect("notify::active", self.on_image_rbutton_switch, True)
		self.gui["image_file_rbutton"].connect("notify::active", self.on_image_rbutton_switch, False)

		self.gui["image_open_button"].connect("clicked", self.on_image_open_button_click)

		# hint
		for hint in WINDOW_HINTS:
			self.gui["hint_combobox"].append_text(hint)
		self.gui["hint_combobox"].set_active(
			WINDOW_HINTS.index(self._mainapp.config["misc"]["hint"].value_nick.upper())
		)
		self.gui["hint_combobox"].connect("changed", self.on_hint_combo_changed)

		# image alignment
		for corner in self.CORNERS.keys():
			self.gui["corner_combobox"].append_text(corner)

		states = list(self.CORNERS.values())
		current = (self._mainapp.config["image"]["ha"], self._mainapp.config["image"]["va"])
		self.gui["corner_combobox"].set_active(states.index(current))
		self.gui["corner_combobox"].connect("changed", self.on_corner_combo_changed)

	# gui handlers
	def on_winstate(self, action, value):
		value = not action.get_state()  # fix this
		action.set_state(GLib.Variant.new_boolean(value))
		self._mainapp.canvas.set_property(action.get_name(), value)

	def on_fg_color_set(self, button):
		key = "autofg" if self._mainapp.config["color"]["auto"] else "fg"
		self._mainapp.config["color"][key] = button.get_rgba()
		self._mainapp.draw.color_update()

	def on_bg_color_set(self, button):
		self._mainapp.config["color"]["bg"] = button.get_rgba()
		if self._mainapp.config["window"]["bgpaint"]:
			self._mainapp.canvas.set_bg_rgba(self._mainapp.config["color"]["bg"])
		else:
			self.gui["st_bgpaint_switch"].set_active(True)

	def on_autocolor_switch(self, switch, active):
		self._mainapp.on_autocolor_switch(not switch.get_active())

	def on_scale_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["scale"] = float(button.get_value())

	def on_padding_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["padding"] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_zero_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["zero"] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_silence_spinbutton_changed(self, button):
		self._mainapp.config["draw"]["silence"] = int(button.get_value())

	def on_offset_spinbutton_changed(self, button, key):
		self._mainapp.config["offset"][key] = int(button.get_value())
		self._mainapp.draw.size_update()

	def on_hint_combo_changed(self, combo):
		text = combo.get_active_text()
		hint = getattr(Gdk.WindowTypeHint, text)
		self._mainapp.canvas.set_hint(hint)

	def on_corner_combo_changed(self, combo):
		text = combo.get_active_text()
		self._mainapp.config["image"]["ha"], self._mainapp.config["image"]["va"] = self.CORNERS[text]

	def on_image_show_switch(self, switch, active):
		self._mainapp.canvas.show_image(switch.get_active())

	def on_image_rbutton_switch(self, button, active, usetag):
		if button.get_active():
			self._mainapp.config["image"]["usetag"] = usetag
			self._mainapp.canvas._rebuild_background()
			self._mainapp.emit("image-source-switch", usetag)

	def on_image_open_button_click(self, *args):
		is_ok, file_ = gtk_open_file(self.window, self.image_filter)
		if is_ok:
			self.gui["imagelabel"].set_text("Image: %s" % name_from_file(file_))
			self._mainapp.config["image"]["default"] = file_
			self._mainapp.emit("default-image-update", file_)

	# support
	def fg_color_manual_set(self, rgba):
		"""Force set drawing color by user"""
		self.gui["fg_colorbutton"].set_rgba(rgba)
		self._mainapp.draw.color_update()
