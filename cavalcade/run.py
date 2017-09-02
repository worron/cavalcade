#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import sys
import gi
import signal

gi.require_version('Gtk', '3.0')
if __name__ == "__main__":
	sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# noinspection PyPep8
from cavalcade.mainapp import MainApp

signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
	app = MainApp()
	exit_status = app.run(sys.argv)
	sys.exit(exit_status)


if __name__ == "__main__":
	run()
