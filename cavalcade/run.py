#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import re
import sys
import gi
import signal

gi.require_version('Gtk', '3.0')
if __name__ == "__main__":
	sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

signal.signal(signal.SIGINT, signal.SIG_DFL)


def set_log_level(args):
	# noinspection PyPep8
	from cavalcade.logger import logger

	level = re.search("log-level=(\w+)", str(args))
	try:
		logger.setLevel(level.group(1))
	except Exception:
		logger.setLevel("WARNING")


def run():
	set_log_level(sys.argv)

	# noinspection PyPep8
	from cavalcade.mainapp import MainApp

	app = MainApp()
	exit_status = app.run(sys.argv)
	sys.exit(exit_status)


if __name__ == "__main__":
	run()
