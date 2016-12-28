# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk
from cavlib.visset import VisualPage
from cavlib.cavaset import CavaPage
from cavlib.playset import PlayerPage
from cavlib.base import GuiBase


class SettingsWindow(GuiBase):
	"""Settings window"""
	def __init__(self, canvas):
		super().__init__("settings.glade", ("window", "mainbox"))

		# build stack
		stack = Gtk.Stack()
		stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
		stack.set_transition_duration(500)

		self.visualpage = VisualPage(canvas)
		stack.add_titled(self.visualpage.gui["maingrid"], "visset", "Visual")

		self.cavapage = CavaPage(canvas)
		stack.add_titled(self.cavapage.gui["mainbox"], "cavaset", "CAVA")

		self.playerpage = PlayerPage(canvas)
		stack.add_titled(self.playerpage.gui["mainbox"], "playset", "Player")

		stack_switcher = Gtk.StackSwitcher(halign=Gtk.Align.CENTER)
		stack_switcher.set_stack(stack)

		self.gui["mainbox"].pack_start(stack_switcher, False, True, 0)
		self.gui["mainbox"].pack_start(stack, True, True, 0)

		# signals
		self.gui["window"].connect("delete-event", self.hide)

	def show(self, *args):
		self.gui["window"].show_all()

	def hide(self, *args):
		self.gui["window"].hide()
		return True
