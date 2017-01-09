#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import sys
import gi
import signal

gi.require_version('Gtk', '3.0')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gi.repository import Gtk
from argparse import ArgumentParser
from cavlib.mainapp import MainApp
from cavlib.logger import logger


def parse_args():
	parser = ArgumentParser()
	parser.add_argument(
		"-p", "--play",
		action = "store",
		nargs = "*",
		default = [],
		dest = "files",
		help = "Add mp3 files to playlist"
	)
	parser.add_argument(
		"-l", "--log-level",
		default="DEBUG",
		dest="log_level",
		choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
		help="Set log level"
	)
	parser.add_argument(
		"--no-autoplay",
		dest = "noplay",
		action = "store_true",
		help = "Pause audio playing on startup"
	)
	return parser.parse_args()


if __name__ == "__main__":
	options = parse_args()

	logger.setLevel(options.log_level)
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	logger.info("Start cavalcade")
	MainApp(options)
	Gtk.main()
	logger.info("Exit cavalcade")
	exit()
