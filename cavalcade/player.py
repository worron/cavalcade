# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import gi
import random
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GLib, GObject, Gio
from cavalcade.logger import logger

Gst.init(None)


# TODO: separate thread?
def image_data_from_message(message):
	"""Get image bytedata from id3 tag message"""
	taglist = message.parse_tag()
	is_ok, sample = taglist.get_sample("image")
	if not is_ok:
		return None

	gstreamer_buffer = sample.get_buffer()
	map_info = gstreamer_buffer.map(Gst.MapFlags.READ)[1]
	data = map_info.data
	gstreamer_buffer.unmap(map_info)
	return data


class Player(GObject.GObject):
	"""Simple gstreamer audio player"""
	__gsignals__ = {
		"progress": (GObject.SIGNAL_RUN_FIRST, None, (int,)),
		"playlist-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
		"queue-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
		"current": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
		"preview-update": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
		"playing": (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
	}

	def __init__(self, mainapp):
		super().__init__()
		self._mainapp = mainapp
		self.config = mainapp.config
		self.playlist = []
		self.playqueue = []
		self.actions = {}

		self.is_image_updated = True
		self.duration = None
		self.timer_id = None
		self._current = None
		self._is_playing = False

		self.player = Gst.ElementFactory.make('playbin', 'player')

		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self._on_message)
		bus.connect("message::tag", self._on_message_tag)

		# this is ugly and should be fixed
		# some fake player object is used to get tag image without playing audio file itself
		self._fake_player = Gst.ElementFactory.make('playbin', 'player')
		bus = self._fake_player.get_bus()
		bus.add_signal_watch()
		bus.connect("message::tag", self._on_fake_message)

		# actions
		self.actions["player"] = Gio.SimpleActionGroup()

		play_action = Gio.SimpleAction.new("play", None)
		play_action.connect("activate", self.play_pause)
		self.actions["player"].add_action(play_action)

		next_action = Gio.SimpleAction.new("next", None)
		next_action.connect("activate", self.play_next)
		self.actions["player"].add_action(next_action)

	@property
	def current(self):
		return self._current

	@current.setter
	def current(self, value):
		self._current = value
		self.emit("current", value)

	@property
	def is_playing(self):
		return self._is_playing

	@is_playing.setter
	def is_playing(self, value):
		if self._is_playing != value:
			self._is_playing = value
			if value:
				self.timer_id = GLib.timeout_add(1000, self._progress)
			else:
				GLib.source_remove(self.timer_id)
			self.emit("playing", value)

	def _progress(self):
		if self.duration is None:
			success, self.duration = self.player.query_duration(Gst.Format.TIME)
			if not success:
				logger.warning("Couldn't fetch song duration")
				self.duration = None
				return True
		success, position = self.player.query_position(Gst.Format.TIME)
		if success:
			self.emit("progress", (position / self.duration * 1000))
		else:
			logger.warning("Couldn't fetch current song position to update slider")
		return True

	# noinspection PyUnusedLocal
	def _on_message(self, bus, message):
		if message.type == Gst.MessageType.EOS:
			self.play_next()  # this one should do all clear
		elif message.type == Gst.MessageType.ERROR:
			self.stop()
			err, debug = message.parse_error()
			logger.error("Playback error %s\n%s" % (err, debug))

	# noinspection PyUnusedLocal
	def _on_message_tag(self, bus, message):
		if not self.is_image_updated:
			self.is_image_updated = True
			data = image_data_from_message(message)
			self._mainapp.emit("tag-image-update", data)

	def load_playlist(self, files, queue=None):
		"""
		Set list of audio files for player.
		Playback queue may be settled as optional argument.
		"""
		self.stop()

		if files:
			self.playlist = files

			self.playqueue = list(queue if queue else files)
			self.emit("playlist-update", self.playlist)
			self.emit("queue-update", self.playqueue)
			self.load_file(random.choice(self.playqueue) if self.config["player"]["shuffle"] else self.playqueue[0])

	def load_file(self, file_):
		"""Set audio file to play"""
		if self.current is not None:
			if self.current in self.playqueue:
				self.playqueue.remove(self.current)
			self.stop()

		self.is_image_updated = False
		self.current = file_
		self.player.set_property('uri', 'file:///' + file_)
		if file_ not in self.playqueue:
			self.playqueue.append(file_)
		self.emit("queue-update", self.playqueue)

	def add_to_queue(self, *files):
		"""Add audio file to playback queue"""
		updated = False
		for file_ in files:
			if file_ not in self.playqueue:
				self.playqueue.append(file_)
				updated = True

		if updated:
			self.emit("queue-update", self.playqueue)

	def remove_from_queue(self, *files):
		"""Remove audio file from playback queue"""
		updated = False
		for file_ in files:
			if file_ in self.playqueue:
				self.playqueue.remove(file_)
				updated = True

		if updated:
			self.emit("queue-update", self.playqueue)

	def seek(self, value):
		"""Playback progress manipulation"""
		if self.duration is not None:
			point = int(self.duration * value / 1000)
			self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, point)

	def stop(self):
		"""Stop playback"""
		self.player.set_state(Gst.State.NULL)
		self.is_playing = False
		self.duration = None
		self.current = None

	# noinspection PyUnusedLocal
	def play_next(self, *args):
		"""Play next audio file in queue"""
		current = self.current
		self.stop()

		if current is None:
			logger.debug("No audio file selected")
		else:
			if current in self.playqueue:
				i = self.playqueue.index(current)
				self.playqueue.remove(current)
			else:
				i = 1
			if self.playqueue:
				if self.config["player"]["shuffle"]:
					self.load_file(random.choice(self.playqueue))
				elif i < len(self.playqueue):
					self.load_file(self.playqueue[i])
				else:
					self.load_file(self.playqueue[0])
				self.play_pause()
			self.emit("queue-update", self.playqueue)  # fix false update if current not in queue

	# noinspection PyUnusedLocal
	def play_pause(self, *args):
		"""Play or pause"""
		if self.current is None:
			logger.debug("No audio file selected")
			return None

		if not self.is_playing:
			self.player.set_state(Gst.State.PLAYING)
			self.is_playing = True
		else:
			self.player.set_state(Gst.State.PAUSED)
			self.is_playing = False

	def set_volume(self, value):
		"""Volume manipulation"""
		self.player.set_property('volume', value)

	def fake_tag_reader(self, file_):
		self._fake_player.set_property('uri', 'file:///' + file_)
		self._fake_player.set_state(Gst.State.PAUSED)

	# noinspection PyUnusedLocal
	def _on_fake_message(self, bus, message):
		data = image_data_from_message(message)
		self.emit("preview-update", data)
		self._fake_player.set_state(Gst.State.NULL)
