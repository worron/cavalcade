#!/usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

"""
Installation routines.
Install:
$ python3 setup.py install --record log.txt
Uninstall:
$ cat log.txt | xargs rm -rf
"""

from setuptools import setup

setup(
	name="cavalcade",
	version="0.6.dev1",
	description="GUI wrapper for C.A.V.A. utility",
	LICENSE = "GPL",
	author="worron",
	author_email="worrongm@gmail.com",
	url="https://github.com/worron/cavalcade",
	packages=["cavalcade", 'cavalcade.gui', 'cavalcade.data'],
	install_requires = ["setuptools"],
	package_data = {"cavalcade.gui": ["*.glade"], "cavalcade.data": ["*.ini", "*.svg"]},
	entry_points = {
		"console_scripts": ["cavalcade=cavalcade.run:run"],
	},
)
