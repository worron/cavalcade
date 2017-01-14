# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk
from cavalcade.visset import VisualPage
from cavalcade.cavaset import CavaPage
from cavalcade.playset import PlayerPage
from cavalcade.common import GuiBase


class SettingsWindow(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		super().__init__("settings.glade", ("window", "mainbox"))
		self.gui["window"].set_keep_above(True)

		# build stack
		stack = Gtk.Stack()
		stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
		stack.set_transition_duration(500)

		# add visual page
		self.visualpage = VisualPage(mainapp, self.gui["window"])
		stack.add_titled(self.visualpage.gui["mainbox"], "visset", "Visual")

		# add cava page
		self.cavapage = CavaPage(mainapp)
		stack.add_titled(self.cavapage.gui["mainbox"], "cavaset", "CAVA")

		# add player page
		if mainapp.is_player_enabled:
			self.playerpage = PlayerPage(mainapp)
			stack.add_titled(self.playerpage.gui["mainbox"], "playset", "Player")

		# setup stack
		stack_switcher = Gtk.StackSwitcher(halign=Gtk.Align.CENTER)
		stack_switcher.set_stack(stack)

		self.gui["mainbox"].pack_start(stack_switcher, False, True, 0)
		self.gui["mainbox"].pack_start(stack, True, True, 0)

		# signals
		self.gui["window"].connect("delete-event", self.hide)
		self.visualpage.gui["hide_button"].connect("clicked", self.hide)
		self.visualpage.gui["exit_button"].connect("clicked", mainapp.close)

	def show(self, *args):
		"""Show settings winndow"""
		self.gui["window"].show_all()

	def hide(self, *args):
		"""Hide settings winndow"""
		self.gui["window"].hide()
		return True
