# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import struct
import threading
import subprocess

from gi.repository import GLib
from cavlib.logger import logger


class Cava:
	def __init__(self, cavaconfig, handler):
		self.cavaconfig = cavaconfig
		self.path = "/tmp/cava.fifo"
		self.handler = handler
		self.command = ["cava", "-p", self.cavaconfig._file]

		if not os.path.exists(self.path):
			os.mkfifo(self.path)

		logger.debug("Acticate cava stream handler")
		thread = threading.Thread(target=self._read_output)
		thread.daemon = True
		thread.start()

		logger.debug("Launching cava process...")
		try:
			self.process = subprocess.Popen(self.command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			logger.debug("cava successfully launched!")
		except Exception:
			logger.exception("Fail to launch cava")

	def _read_output(self):
		fifo = open(self.path, "rb")
		while True:
			data = fifo.read(2 * 32)
			sample = [i[0] / 65535 for i in struct.iter_unpack("H", data)]
			if sample:
				GLib.idle_add(self.handler, sample)
			else:
				GLib.idle_add(self._on_stop)
				break
		fifo.close()

	def _on_stop(self, ):
		logger.debug("Cava stream handler deactivated")

	def close(self):
		if self.process.poll() is None:
			self.process.kill()
		os.remove(self.path)
