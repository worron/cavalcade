# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import io
import threading

from gi.repository import GLib, Gdk, GObject
from collections import namedtuple
from operator import add
from PIL import Image
from cavlib.logger import logger

Point = namedtuple("Point", ("color", "count"))


def get_points(img, limit):
	points = []
	w, h = img.size
	for count, color in img.getcolors(w * h):
		m = sum(color) / 3
		if (
			any(abs(c - m) > limit["gray"] for c in color)
			and not all(c < limit["black"] for c in color)
			and not all(c > limit["white"] for c in color)
		):
			points.append(Point(color, count))
	return points


def calculate_center(points):
	sum_color = [0.0] * 3
	sum_count = 0
	for point in points:
		sum_count += point.count
		sum_color = map(add, sum_color, [c * point.count for c in point.color])
	return [(c / sum_count) for c in sum_color]


class AutoColor(GObject.GObject):
	__gsignals__ = {"ac-update": (GObject.SIGNAL_RUN_FIRST, None, (object,))}

	def __init__(self, mainapp):
		super().__init__()
		self._mainapp = mainapp
		self.config = mainapp.config
		self.thread = None
		# self.last = None

	def calculate(self, bytedata, limits):
		file_ = io.BytesIO(bytedata)
		img = Image.open(file_)
		img.thumbnail((160, 90))  # TODO: move to config

		points = get_points(img, limits)
		cv = [c / 255 for c in calculate_center(points)]
		GLib.idle_add(self.color_setup, cv)

	def color_setup(self, color_values):
		rgba = Gdk.RGBA(*color_values, self.config["color"]["autofg"].alpha)
		# self.last = rgba
		self.emit("ac-update", rgba)

	def color_update(self, data):
		if self.thread is None or not self.thread.isAlive():
			self.thread = threading.Thread(target=self.calculate, args=(data, self.config["acl"]))
			# self.thread.daemon = True
			self.thread.start()
		else:
			logger.error("Autocolor threading error")
