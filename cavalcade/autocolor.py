# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import io
import multiprocessing
import colorsys

from gi.repository import GLib, Gdk
from cavalcade.common import AttributeDict
from operator import add
from PIL import Image
from cavalcade.logger import logger


class Clust:
	"""Group of color points"""
	def __init__(self, points = []):
		self.points = []
		self.mass = 0
		for p in points:
			self.add(p)

	def add(self, point):
		"""Add new point to group"""
		self.points.append(point)
		self.mass += point.count

	def get_color(self):
		"""Calculate average color for group"""
		color = [0.0] * 3
		for point in self.points:
			color = map(add, color, [c * point.count for c in point.rgb])
		return [(c / max(self.mass, 1)) for c in color]


def get_points(img, limit):
	"""Tramsform image to pack of color points"""
	points = []
	w, h = img.size
	for count, color in img.getcolors(w * h):
		rgb = [c / 255 for c in color]
		hsv = colorsys.rgb_to_hsv(*rgb)
		if hsv[1] > limit["saturation_min"] and hsv[2] > limit["value_min"]:
			points.append(AttributeDict(rgb=rgb, hsv=hsv, count=count))
	return points


def allocate(points, n=16, window=4):
	"""Split points to groups according there color """
	band = 1 / n
	clusters = [Clust() for i in range(n)]
	for point in points:
		i = int(point.hsv[0] // band)
		clusters[i].add(point)
	clusters_l = clusters + clusters[:window - 1]
	bands = [clusters_l[i:i + window] for i in range(n)]
	rebanded = [Clust(sum([c.points for c in band], [])) for band in bands]
	return rebanded


class AutoColor:
	"""Image color analyzer"""
	def __init__(self, mainapp):
		super().__init__()
		self._mainapp = mainapp
		self.config = mainapp.config
		self.process = None
		self.default = None

		self.pc, self.cc = multiprocessing.Pipe()  # fix this
		self.watcher = None
		self.catcher = self._mainapp.connect("ac-update", self.catch_default_color)
		self._mainapp.handler_block(self.catcher)

		self._mainapp.connect("reset-color", self.reset_default_color)
		self._mainapp.connect("tag-image-update", self.on_image_update)
		self._mainapp.connect("image-source-switch", self.on_image_source_switch)

	def on_image_update(self, sender, bytedata):
		"""New image from mp3 tag"""
		if self.config["image"]["usetag"]:
			self.color_update(bytedata)

	def on_image_source_switch(self, sender, usetag):
		"""Use default background or image from mp3 tag"""
		self.color_update(self._mainapp.canvas.tag_image_bytedata if usetag else None)

	def calculate(self, file_, options, conn):
		"""Find the main color of image"""
		img = Image.open(file_)
		img.thumbnail((options["isize"][0], options["isize"][1]))

		points = get_points(img, options)
		clusters = allocate(points, options["bands"], options["window"])
		selected = max(clusters, key=lambda x: x.mass)
		conn.send(selected.get_color())

	def color_setup(self, conn, flag):
		"""Read data from resent calculation and transform it to rgba color"""
		if flag == GLib.IO_IN:
			color_values = conn.recv()
			rgba = Gdk.RGBA(*color_values, self.config["color"]["autofg"].alpha)
			self._mainapp.emit("ac-update", rgba)
			return True
		else:
			logger.error("Autocolor multiprocessing error: connection was unexpectedy terminated")
			self.watcher = None

	def catch_default_color(self, sender, rgba):
		"""Set new calculated color as default"""
		self.default = rgba
		self._mainapp.handler_block(self.catcher)

	def reset_default_color(self, *args):
		"""Update default color"""
		self.default = None
		self.color_update(None)

	def color_update(self, bytedata):
		"""Launch new calculation process with given image bytedata"""
		if bytedata is None:
			if self.default is None:
				if not self.config["image"]["default"].endswith(".svg"):  # fix this
					file_ = self.config["image"]["default"]
					self._mainapp.handler_unblock(self.catcher)
				else:
					return
			else:
				self.emit("ac-update", self.default)
				return
		else:
			file_ = io.BytesIO(bytedata)

		if self.process is None or not self.process.is_alive():
			if self.watcher is None:
				self.watcher = GLib.io_add_watch(self.pc, GLib.IO_IN | GLib.IO_HUP, self.color_setup)
			self.process = multiprocessing.Process(
				target=self.calculate, args=(file_, self.config["autocolor"], self.cc)
			)
			self.process.start()
		else:
			logger.error("Autocolor threading error: previus process still running, refusing to start new one")
