# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gio, GLib, GdkPixbuf


def from_bytes(data):
	stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
	pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream)
	return pixbuf
