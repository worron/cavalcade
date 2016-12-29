# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gio, GLib, GdkPixbuf


def from_bytes(data):
	stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
	pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream)
	return pixbuf


def from_bytes_at_size(data, width, height, aspect=True):
	stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
	pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale(stream, width, height, aspect)
	return pixbuf
