# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
from gi.repository import Gtk

WINDOW_HINTS = ("NORMAL", "DIALOG", "SPLASHSCREEN", "DOCK", "DESKTOP")


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

	def __init__(self, *files, elements=[]):
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


class TreeViewHolder():
	"""Disconnect treeview store for rebiuld"""
	def __init__(self, treeview):
		self.treeview = treeview

	def __enter__(self):
		self.store = self.treeview.get_model()
		self.treeview.set_model(None)

	def __exit__(self, type, value, traceback):
		self.treeview.set_model(self.store)
