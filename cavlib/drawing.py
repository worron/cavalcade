# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk, Gdk


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
		self.color = None

		self.area = Gtk.DrawingArea()
		self.area.connect("draw", self.redraw)
		self.area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

		self.sizes = AttributeDict()
		self.sizes.area = AttributeDict()
		self.sizes.bar = AttributeDict()

		self.area.connect("configure-event", self.size_update)
		self.color_update()

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
		cr.set_source_rgba(*self.color)

		dx = self.config["offset"]["left"]
		for i, value in enumerate(self.audio_sample):
			width = self.sizes.bar.width + int(i < self.sizes.wcpi)
			height = self.sizes.bar.height * min(self.config["draw"]["scale"] * value, 1)
			cr.rectangle(dx, self.sizes.area.height, width, - height)
			dx += width + self.sizes.padding
		cr.fill()

	def size_update(self, *args):
		"""Update drawing geometry"""
		self.sizes.number = self.cavaconfig["bars"]
		self.sizes.padding = self.config["draw"]["padding"]

		self.sizes.area.width = self.area.get_allocated_width() - self.config["offset"]["right"]
		self.sizes.area.height = self.area.get_allocated_height() - self.config["offset"]["bottom"]

		tw = (self.sizes.area.width - self.config["offset"]["left"]) - self.sizes.padding * (self.sizes.number - 1)
		self.sizes.bar.width = max(int(tw / self.sizes.number), 1)
		self.sizes.bar.height = self.sizes.area.height - self.config["offset"]["top"]
		self.sizes.wcpi = tw % self.sizes.number  # width correnction point index

	def color_update(self):
		self.color = self.config["color"]["autofg"] if self.config["color"]["auto"] else self.config["color"]["fg"]
