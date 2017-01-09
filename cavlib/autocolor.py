# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import io
import multiprocessing
import colorsys

from gi.repository import GLib, Gdk, GObject
from collections import namedtuple
from operator import add
from PIL import Image

from cavlib.logger import logger

Point = namedtuple("Point", ("rgb", "hsv", "count"))


class Clust:
	def __init__(self, points = []):
		self.points = []
		self.mass = 1
		for p in points:
			self.add(p)

	def add(self, point):
		self.points.append(point)
		self.mass += point.count

	def get_color(self):
		color = [0.0] * 3
		for point in self.points:
			color = map(add, color, [c * point.count for c in point.rgb])
		return [(c / self.mass) for c in color]


def get_points(img, limit):
	points = []
	w, h = img.size
	for count, color in img.getcolors(w * h):
		rgb = [c / 255 for c in color]
		hsv = colorsys.rgb_to_hsv(*rgb)
		if hsv[1] > limit["sv_min"][0] and hsv[2] > limit["sv_min"][1]:
			points.append(Point(rgb, hsv, count))
	return points


def allocate(points, n=16, window=4):
	band = 1 / n
	clusters = [Clust() for i in range(n)]
	for point in points:
		i = int(point.hsv[0] // band)
		clusters[i].add(point)
	clusters_l = clusters + clusters[:window - 1]
	bands = [clusters_l[i:i + window] for i in range(n)]
	rebanded = [Clust(sum([c.points for c in band], [])) for band in bands]
	return rebanded


class AutoColor(GObject.GObject):
	__gsignals__ = {"ac-update": (GObject.SIGNAL_RUN_FIRST, None, (object,))}

	def __init__(self, mainapp):
		super().__init__()
		self._mainapp = mainapp
		self.config = mainapp.config
		self.process = None
		self.default = None

		self.pc, self.cc = multiprocessing.Pipe()  # fix this
		self.watcher = None
		self.catcher = self.connect("ac-update", self.catch_default_color)
		self.handler_block(self.catcher)

	def calculate(self, file_, options, conn):
		img = Image.open(file_)
		img.thumbnail((options["isize"][0], options["isize"][1]))

		points = get_points(img, options)
		clusters = allocate(points, options["bands"], options["window"])
		selected = max(clusters, key=lambda x: x.mass)
		conn.send(selected.get_color())

	def color_setup(self, conn, flag):
		if flag == GLib.IO_IN:
			color_values = conn.recv()
			rgba = Gdk.RGBA(*color_values, self.config["color"]["autofg"].alpha)
			self.emit("ac-update", rgba)
			return True
		else:
			logger.error("Autocolor multiprocessing error: connection was unexpectedy terminated")
			self.watcher = None

	def catch_default_color(self, sender, rgba):
		self.default = rgba
		self.handler_block(self.catcher)

	def color_update(self, data):
		if data is None:
			if self.default is None:
				file_ = self.config["image"]["default"]
				self.handler_unblock(self.catcher)
			else:
				self.emit("ac-update", self.default)
				return
		else:
			file_ = io.BytesIO(data)

		if self.process is None or not self.process.is_alive():
			if self.watcher is None:
				self.watcher = GLib.io_add_watch(self.pc, GLib.IO_IN | GLib.IO_HUP, self.color_setup)
			self.process = multiprocessing.Process(target=self.calculate, args=(file_, self.config["aco"], self.cc))
			self.process.start()
		else:
			logger.error("Autocolor threading error: previus process still running, refusing to start new one")
