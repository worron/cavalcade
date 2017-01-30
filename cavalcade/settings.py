# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gtk
from cavalcade.visset import VisualPage
from cavalcade.cavaset import CavaPage
from cavalcade.playset import PlayerPage
from cavalcade.common import GuiBase


class SettingsWindow(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		super().__init__("settings.glade", elements=("window", "mainbox"))
		self._mainapp = mainapp
		self.gui["window"].set_keep_above(True)
		self.gui["window"].set_application(mainapp)

		# build stack
		self.stack = Gtk.Stack()
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
		self.stack.set_transition_duration(500)

		# add visual page
		self.visualpage = VisualPage(self._mainapp, self.gui["window"])
		self.stack.add_titled(self.visualpage.gui["mainbox"], "visset", "Visual")

		# add cava page
		self.cavapage = CavaPage(self._mainapp)
		self.stack.add_titled(self.cavapage.gui["mainbox"], "cavaset", "CAVA")

		# setup stack
		stack_switcher = Gtk.StackSwitcher(halign=Gtk.Align.CENTER)
		stack_switcher.set_stack(self.stack)

		self.gui["mainbox"].pack_start(stack_switcher, False, True, 0)
		self.gui["mainbox"].pack_start(self.stack, True, True, 0)

		# signals
		self.gui["window"].connect("delete-event", self.hide)
		self.visualpage.gui["hide_button"].connect("clicked", self.hide)
		self.visualpage.gui["exit_button"].connect("clicked", self._mainapp.close)

	def set_player_page(self):
		"""Optional player page"""
		self.playerpage = PlayerPage(self._mainapp)
		self.stack.add_titled(self.playerpage.gui["mainbox"], "playset", "Player")

	def run_action(self, group, name):
		action = self.gui["window"].get_action_group(group)
		if action is not None:
			action.activate_action(name)

	def show(self, *args):
		"""Show settings winndow"""
		self.gui["window"].show_all()

	def hide(self, *args):
		"""Hide settings winndow"""
		self.gui["window"].hide()
		return True
