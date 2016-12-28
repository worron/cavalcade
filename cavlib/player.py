#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GLib, GObject
from cavlib.logger import logger

Gst.init(None)


class Player(GObject.GObject):
	__gsignals__ = {
		"progress": (GObject.SIGNAL_RUN_FIRST, None, (int,)),
		"playlist-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
		"current": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
	}

	def __init__(self, canvas):
		super().__init__()
		self._canvas = canvas
		self.playlist = []
		self.playqueue = []

		self.is_playing = False
		self.is_image_updated = True
		self.duration = None
		self._current = None

		self.player = Gst.ElementFactory.make('playbin', 'player')

		# sink = Gst.ElementFactory.make('directsoundsink', 'sink')
		# self.player.set_property('audio-sink', sink)

		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self._on_message)
		bus.connect("message::tag", self._on_message_tag)
		# bus.enable_sync_message_emission()

	@property
	def current(self):
		return self._current

	@current.setter
	def current(self, value):
		self._current = value
		self.emit("current", value)

	def _progress(self):
		if not self.is_playing:
			return False  # cancel timeout
		else:
			if self.duration is None:
				success, self.duration = self.player.query_duration(Gst.Format.TIME)
				if not success:
					logger.warning("Couldn't fetch song duration")
					self.duration = None
			success, position = self.player.query_position(Gst.Format.PERCENT)
			if success:
				self.emit("progress", int(position / 10000))
			else:
				logger.warning("Couldn't fetch current song position to update slider")
		return True

	def _on_message(self, bus, message):
		if message.type == Gst.MessageType.EOS:
			self.play_next(self.current)  # this one should do all clear
		elif message.type == Gst.MessageType.ERROR:
			self.stop()
			err, debug = message.parse_error()
			logger.error("Playback error %s\n%s" % (err, debug))

	def _on_message_tag(self, bus, message):
		if not self.is_image_updated:
			self.is_image_updated = True
			taglist = message.parse_tag()

			sample = taglist.get_sample("image").sample
			mapinfo = sample.get_buffer().map_range(0, -1, Gst.MapFlags.READ)[1]
			self._canvas.update_image(mapinfo.data)

	def load_playlist(self, *files):
		self.playlist = files
		self.playqueue = list(self.playlist)
		if files:
			self.load_file(files[0])
			self.emit("playlist-update", self.playlist)

	def load_file(self, file_):
		if self.is_playing:
			self.stop()

		self.is_image_updated = False
		self.current = file_
		self.player.set_property('uri', 'file:///' + file_)
		if file_ not in self.playqueue:
			self.playqueue.append(file_)

	def seek(self, perc):
		if self.duration is not None:
			point = int(self.duration * perc / 100)
			self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, point)

	def stop(self):
		self.player.set_state(Gst.State.NULL)
		self.is_playing = False
		self.duration = None
		self.current = None

	def play_next(self, current):
		self.stop()
		if current is None:
			logger.debug("No audio file selected")
		else:
			ni = self.playqueue.index(current) + 1
			if ni < len(self.playqueue):
				nf = self.playqueue[ni]
				self.playqueue.remove(current)
				self.load_file(nf)
				self.play_pause()

	def play_pause(self):
		if self.current is None:
			logger.debug("No audio file selected")
			return None

		if not self.is_playing:
			self.player.set_state(Gst.State.PLAYING)
			self.is_playing = True
			GLib.timeout_add(1000, self._progress)
		else:
			self.player.set_state(Gst.State.PAUSED)
			self.is_playing = False
