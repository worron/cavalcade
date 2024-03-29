#!/usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

"""
Installation routines.
Install:
$ pip install .
Uninstall:
$ pip uninstall cavalcade
"""

from setuptools import setup
from cavalcade.version import get_current as get_current_version

setup(
	name = "cavalcade",
	version = get_current_version(),
	description = "GUI wrapper for C.A.V.A. utility",
	license = "GPL-3.0-or-later",
	author = "worron",
	author_email = "worrongm@gmail.com",
	url = "https://github.com/worron/cavalcade",
	packages = ["cavalcade", "cavalcade.gui", "cavalcade.data"],
	install_requires = ["setuptools"],
	package_data = {"cavalcade.gui": ["*.glade", "*.ui"], "cavalcade.data": ["*.ini", "*.svg"]},
	entry_points = {
		"console_scripts": ["cavalcade=cavalcade.run:run"],
	},
)
