# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import io
import threading
import random
import math
import colorsys

from gi.repository import GLib, Gdk, GObject
from collections import namedtuple
from operator import add
from PIL import Image

from cavlib.logger import logger

Point = namedtuple("Point", ("color", "count"))


class Cluster:
	def __init__(self, points, center):
		self.points = points
		self.center = center
		self.diff = 0

	def update(self, points):
		new_center = calculate_center(points)
		self.diff = euclidean(self.center, new_center)
		self.points = points
		self.center = new_center


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
	return Point([(c / sum_count) for c in sum_color], 1)


def euclidean(p1, p2):
	return math.sqrt(sum([(a - b)**2 for a, b in zip(p1.color, p2.color)]))


def selection(clusters, hvr):
	sorted_clusters = sorted(clusters, key = lambda c: len(c.points), reverse=True)
	rgbs = [[c / 255 for c in s.center.color] for s in sorted_clusters]
	for color in rgbs:
		if hvr[0] < colorsys.rgb_to_hsv(*color)[2] < hvr[1]:
			return color
	return rgbs[0]


def kmeans(points, k, min_diff):
	clusters = [Cluster([p], p) for p in random.sample(points, k)]

	while True:
		point_group = [[] for i in range(k)]

		for p in points:
			distance = [euclidean(p, cluster.center) for cluster in clusters]
			idx = distance.index(min(distance))
			point_group[idx].append(p)

		for i, cluster in enumerate(clusters):
			cluster.update(point_group[i])
		diff = max(cluster.diff for claster in clusters)

		if diff < min_diff:
			break

	return clusters


class AutoColor(GObject.GObject):
	__gsignals__ = {"ac-update": (GObject.SIGNAL_RUN_FIRST, None, (object,))}

	def __init__(self, mainapp):
		super().__init__()
		self._mainapp = mainapp
		self.config = mainapp.config
		self.thread = None

	def calculate(self, bytedata, options):
		file_ = io.BytesIO(bytedata)
		img = Image.open(file_)
		img.thumbnail((options["isize"][0], options["isize"][1]))

		points = get_points(img, options)
		clusters = kmeans(points, options["clusters"], options["diff"])
		cv = selection(clusters, options["hvr"])
		GLib.idle_add(self.color_setup, cv)

	def color_setup(self, color_values):
		rgba = Gdk.RGBA(*color_values, self.config["color"]["autofg"].alpha)
		self.emit("ac-update", rgba)

	def color_update(self, data):
		if self.thread is None or not self.thread.isAlive():
			self.thread = threading.Thread(target=self.calculate, args=(data, self.config["aco"]))
			# self.thread.daemon = True
			self.thread.start()
		else:
			logger.error("Autocolor threading error")
