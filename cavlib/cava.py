# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import struct
import threading
import subprocess

from gi.repository import GLib
from cavlib.logger import logger


class Cava:
	NONE = 0
	RUNNING = 1
	RESTARTING = 2
	CLOSING = 3

	def __init__(self, cavaconfig, handler):
		self.cavaconfig = cavaconfig
		self.path = self.cavaconfig["output"]["raw_target"]
		self.data_handler = handler
		self.command = ["cava", "-p", self.cavaconfig._file]
		self.state = self.NONE

		self.env = dict(os.environ)
		# self.env["LC_ALL"] = "en_US.UTF-8"

		if not os.path.exists(self.path):
			os.mkfifo(self.path)

	def _run_process(self):
		logger.debug("Launching cava process...")
		try:
			self.process = subprocess.Popen(
				self.command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=self.env
			)
			logger.debug("cava successfully launched!")
			self.state = self.RUNNING
		except Exception:
			logger.exception("Fail to launch cava")

	def _start_reader_thread(self):
		logger.debug("Acticate cava stream handler")
		self.thread = threading.Thread(target=self._read_output)
		self.thread.daemon = True
		self.thread.start()

	def _read_output(self):
		fifo = open(self.path, "rb")
		while True:
			data = fifo.read(2 * self.cavaconfig["general"]["bars"])
			sample = [i[0] / 65535 for i in struct.iter_unpack("H", data)]
			if sample:
				GLib.idle_add(self.data_handler, sample)
			else:
				break
		fifo.close()
		GLib.idle_add(self._on_stop)

	def _on_stop(self, ):
		logger.debug("Cava stream handler deactivated")
		if self.state == self.RESTARTING:
			if not self.thread.isAlive():
				self.start()
			else:
				logger.error("Can't restart cava, old hadler still alive")
		elif self.state == self.RUNNING:
			self.state = self.NONE
			logger.error("Cava process was unexpectedy terminated.")

	def start(self):
		self._start_reader_thread()
		self._run_process()

	def restart(self):
		if self.state == self.RUNNING:
			logger.debug("Restarting cava process (normal mode) ...")
			self.state = self.RESTARTING
			if self.process.poll() is None:
				self.process.kill()
		elif self.state == self.NONE:
			logger.warning("Restarting cava process (after crash) ...")
			self.start()

	def close(self):
		self.state = self.CLOSING
		if self.process.poll() is None:
			self.process.kill()
		os.remove(self.path)
