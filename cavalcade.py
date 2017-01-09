#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import sys
import gi
import signal

gi.require_version('Gtk', '3.0')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gi.repository import Gtk
from cavlib.mainapp import MainApp
from cavlib.logger import logger


if __name__ == "__main__":
	logger.setLevel("DEBUG")  # TODO: add CLI args
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	logger.info("Start cavalcade")
	MainApp(sys.argv)
	Gtk.main()
	logger.info("Exit cavalcade")
	exit()
