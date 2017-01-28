#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import sys
import gi
import signal

gi.require_version('Gtk', '3.0')
if __name__ == "__main__":
	sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from gi.repository import Gtk
from argparse import ArgumentParser
from cavalcade.mainapp import MainApp
from cavalcade.logger import logger
from cavalcade.common import AttributeDict


def import_optional():
	"""Safe module import"""
	success = AttributeDict()
	try:
		gi.require_version('Gst', '1.0')
		from gi.repository import Gst  # noqa: F401
		success.gstreamer = True
	except Exception:
		success.gstreamer = False
		logger.warning("Fail to import Gstreamer module")

	try:
		from PIL import Image  # noqa: F401
		success.pillow = True
	except Exception:
		success.pillow = False
		logger.warning("Fail to import Pillow module")

	return success


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
	parser.add_argument(
		"--no-autocolor",
		dest = "nocolor",
		action = "store_true",
		help = "Disable auto color detection function"
	)
	parser.add_argument(
		"--restore",
		dest = "restore",
		action = "store_true",
		help = "Restore previous player session"
	)
	return parser.parse_args()


def run():
	imported = import_optional()
	options = parse_args()

	logger.setLevel(options.log_level)
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	logger.info("Start cavalcade")
	app = MainApp(options, imported)
	exit_status = app.run(sys.argv)
	logger.info("Exit cavalcade")
	sys.exit(exit_status)
	# Gtk.main()


if __name__ == "__main__":
	run()
