# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gio, GLib, GdkPixbuf


def from_bytes(data):
	"""Build Gdk pixbuf from bytedata"""
	stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
	pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream)
	return pixbuf


def from_bytes_at_scale(data, width, height, aspect=True):
	"""Build Gdk pixbuf from bytedata with scaling"""
	stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
	pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale(stream, width, height, aspect)
	return pixbuf


def from_file_at_scale(file_, width, height, aspect=True):
	"""Build Gdk pixbuf from file with scaling"""
	pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(file_, width, height, aspect)
	return pixbuf
