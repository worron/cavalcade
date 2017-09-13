# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import io
import multiprocessing
import colorsys

from gi.repository import GLib, Gdk
from cavalcade.common import AttributeDict
from operator import add
from PIL import Image
from cavalcade.logger import logger


def bytes_to_file(bytes_):
	return io.BytesIO(bytes_) if bytes_ is not None else None


class Cluster:
	"""Group of color points"""

	# noinspection PyDefaultArgument
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
	"""Transform image to pack of color points"""
	points = []
	w, h = img.size
	for count, color in img.getcolors(w * h):
		rgb = [c / 255 for c in color]
		hsv = colorsys.rgb_to_hsv(*rgb)
		if hsv[1] > limit["saturation_min"] and hsv[2] > limit["value_min"]:
			points.append(AttributeDict(rgb=rgb, hsv=hsv, count=count))
	return points


def allocate(points, n=16, window=4):
	"""Split points to groups according there color"""
	band = 1 / n
	clusters = [Cluster() for _ in range(n)]
	for point in points:
		i = int(point.hsv[0] // band)
		clusters[i].add(point)
	clusters_l = clusters + clusters[:window - 1]
	bands = [clusters_l[i:i + window] for i in range(n)]
	rebanded = [Cluster(sum([c.points for c in band], [])) for band in bands]
	return rebanded


class AutoColor:
	"""Image color analyzer"""
	def __init__(self, mainapp):
		super().__init__()
		self._mainapp = mainapp
		self.config = mainapp.config
		self.process = None

		self.pc, self.cc = multiprocessing.Pipe()  # fix this
		self.watcher = None

		self._mainapp.connect("tag-image-update", self.on_tag_image_update)
		self._mainapp.connect("default-image-update", self.on_default_image_update)
		self._mainapp.connect("image-source-switch", self.on_image_source_switch)
		self._mainapp.connect("autocolor-refresh", self.on_image_source_switch)

	# noinspection PyUnusedLocal
	def on_tag_image_update(self, sender, bytedata):
		"""New image from mp3 tag"""
		if self.config["image"]["usetag"]:
			# dirty trick
			saved_color = self._mainapp.palette.find_color(self._mainapp.player.current)
			if saved_color is not None:
				rgba = Gdk.RGBA(*saved_color, self.config["color"]["autofg"].alpha)
				self._mainapp.emit("ac-update", rgba)
			else:
				file_ = bytes_to_file(bytedata)
				# noinspection PyTypeChecker
				self.color_update(file_)

	# noinspection PyUnusedLocal
	def on_image_source_switch(self, sender, usetag):
		"""Update color from mp3 tag"""
		if usetag:
			file_ = bytes_to_file(self._mainapp.canvas.tag_image_bytedata)
		else:
			file_ = self.config["image"]["default"]
		self.color_update(file_)

	# noinspection PyUnusedLocal
	def on_default_image_update(self, sender, file_):
		"""Update color from default image"""
		if not self.config["image"]["usetag"]:
			self.color_update(file_)

	@staticmethod
	def calculate(file_, options, conn):
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
			logger.error("Autocolor multiprocessing error: connection was unexpectedly terminated")

	def color_update(self, file_):
		"""Launch new calculation process with given image bytedata"""
		if file_ is None or isinstance(file_, str) and file_.endswith(".svg"):  # fix this
			return

		if self.process is None or not self.process.is_alive():
			if self.watcher is None:
				self.watcher = GLib.io_add_watch(self.pc, GLib.IO_IN | GLib.IO_HUP, self.color_setup)
			self.process = multiprocessing.Process(
				target=self.calculate, args=(file_, self.config["autocolor"], self.cc)
			)
			self.process.start()
		else:
			logger.error("Autocolor threading error: previous process still running, refusing to start new one")
