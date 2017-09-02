# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
import gi
from gi.repository import Gtk, Gdk
from cavalcade.logger import logger

WINDOW_HINTS = ("NORMAL", "DIALOG", "SPLASHSCREEN", "DOCK", "DESKTOP")


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


def set_actions(action_pack, widget):
	"""Set actions groups from dictionary to widget"""
	for key, value in action_pack.items():
		widget.insert_action_group(key, value)


def name_from_file(file_):
	"""Extract file name from full path"""
	return os.path.splitext(os.path.basename(file_))[0]


def gtk_open_file(parent, filter_=None):
	"""Gtk open file dialog"""
	dialog = Gtk.FileChooserDialog(
		"Select image file", parent, Gtk.FileChooserAction.OPEN,
		(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
	)

	if filter_ is not None:
		dialog.add_filter(filter_)

	response = dialog.run()
	if response != Gtk.ResponseType.OK:
		is_ok, file_ = False, None
	else:
		is_ok = True
		file_ = dialog.get_filename()

	dialog.destroy()
	return is_ok, file_


class GuiBase:
	"""Base for Gtk widget set created with builder"""
	path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")

	def __init__(self, *files, elements=tuple()):
		self.builder = Gtk.Builder()
		for file_ in files:
			self.builder.add_from_file(os.path.join(self.path, file_))
		self.gui = {element: self.builder.get_object(element) for element in elements}


class AttributeDict(dict):
	"""Dictionary with keys as attributes. Does nothing but easy reading"""
	def __getattr__(self, attr):
		return self[attr]

	def __setattr__(self, attr, value):
		self[attr] = value


class TreeViewHolder:
	"""Disconnect treeview store for rebuild"""
	def __init__(self, treeview):
		self.treeview = treeview

	def __enter__(self):
		self.store = self.treeview.get_model()
		self.treeview.set_model(None)

	def __exit__(self, type_, value, traceback):
		self.treeview.set_model(self.store)


class AccelCheck:
	def __contains__(self, item):
		key, mod = Gtk.accelerator_parse(item)
		return any((key != 0, mod != Gdk.ModifierType(0)))
