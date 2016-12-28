# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
from gi.repository import Gtk


class GuiBase:
	path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")

	def __init__(self, file_, elements):
		builder = Gtk.Builder()
		builder.add_from_file(os.path.join(self.path, file_))
		self.gui = {element: builder.get_object(element) for element in elements}


class TreeViewHolder():
	"""Disconnect treeview store"""
	def __init__(self, treeview):
		self.treeview = treeview

	def __enter__(self):
		self.store = self.treeview.get_model()
		self.treeview.set_model(None)

	def __exit__(self, type, value, traceback):
		self.treeview.set_model(self.store)
