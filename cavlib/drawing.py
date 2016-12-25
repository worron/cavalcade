# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk


class AttributeDict(dict):
	"""Dictionary with keys as attributes. Does nothing but easy reading."""
	def __getattr__(self, attr):
		return self[attr]

	def __setattr__(self, attr, value):
		self[attr] = value


class Spectrum:
	"""Spectrum drawning"""
	def __init__(self, config, cavaconfig):
		self.silence_value = 0
		self.config = config
		self.cavaconfig = cavaconfig
		self.audio_sample = []

		self.area = Gtk.DrawingArea()
		self.area.connect("draw", self.redraw)

		self.sizes = AttributeDict()
		self.sizes.area = AttributeDict()
		self.sizes.bar = AttributeDict()

	def is_silence(self, value):
		"""Check if volume level critically low during last iterations"""
		self.silence_value = 0 if value > 0 else self.silence_value + 1
		return self.silence_value > 10

	def update(self, data):
		"""Audio data processing"""
		self.audio_sample = data
		if not self.is_silence(self.audio_sample[0]):
			self.area.queue_draw()

	def redraw(self, widget, cr):
		"""Draw spectrum graph"""
		cr.set_source_rgba(*self.config["rgba"])

		dx = self.config["left_offset"]
		for i, value in enumerate(self.audio_sample):
			width = self.sizes.bar.width + int(i < self.sizes.wcpi)
			height = self.sizes.bar.height * min(self.config["scale"] * value, 1)
			cr.rectangle(dx, self.sizes.area.height, width, - height)
			dx += width + self.sizes.padding
		cr.fill()

	def size_update(self, *args):
		"""Update drawing geometry"""
		self.sizes.number = self.cavaconfig["bars"]
		self.sizes.padding = self.config["padding"]

		self.sizes.area.width = self.area.get_allocated_width() - self.config["right_offset"]
		self.sizes.area.height = self.area.get_allocated_height() - self.config["bottom_offset"]

		tw = (self.sizes.area.width - self.config["left_offset"]) - self.sizes.padding * (self.sizes.number - 1)
		self.sizes.bar.width = max(int(tw / self.sizes.number), 1)
		self.sizes.bar.height = self.sizes.area.height - self.config["top_offset"]
		self.sizes.wcpi = tw % self.sizes.number  # width correnction point index
