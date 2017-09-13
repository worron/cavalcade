# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from gi.repository import Gio
from cavalcade.visualpage import VisualPage
from cavalcade.cavapage import CavaPage
from cavalcade.playerpage import PlayerPage
from cavalcade.common import GuiBase


class SettingsWindow(GuiBase):
	"""Settings window"""
	def __init__(self, mainapp):
		elements = (
			"window", "headerbar", "winstate-menubutton", "stackswitcher", "app-menu", "stack", "winstate-menu",
			"app-menubutton",
		)
		super().__init__("settings.ui", "appmenu.ui", "winstate.ui", elements=elements)

		self.actions = {}
		self._mainapp = mainapp
		self.gui["window"].set_keep_above(True)
		self.gui["window"].set_application(mainapp)
		self.actions["settings"] = Gio.SimpleActionGroup()

		# add visual page
		self.visualpage = VisualPage(self._mainapp, self)
		self.gui["stack"].add_titled(self.visualpage.gui["mainbox"], "visset", "Visual")

		# add cava page
		self.cavapage = CavaPage(self._mainapp)
		self.gui["stack"].add_titled(self.cavapage.gui["mainbox"], "cavaset", "CAVA")

		# setup menu buttons
		self.gui["winstate-menubutton"].set_menu_model(self.gui["winstate-menu"])
		self.gui["app-menubutton"].set_menu_model(self.gui["app-menu"])

		# actions
		hide_action = Gio.SimpleAction.new("hide", None)
		hide_action.connect("activate", self.hide)
		self.actions["settings"].add_action(hide_action)

		show_action = Gio.SimpleAction.new("show", None)
		show_action.connect("activate", self.show)
		self.actions["settings"].add_action(show_action)

		# signals
		self.gui["window"].connect("delete-event", self.hide)

	def add_player_page(self):
		"""Optional player page"""
		# noinspection PyAttributeOutsideInit
		self.playerpage = PlayerPage(self._mainapp)
		self.gui["stack"].add_titled(self.playerpage.gui["mainbox"], "playset", "Player")

	# noinspection PyUnusedLocal
	def show(self, *args):
		"""Show settings window"""
		self.gui["window"].show_all()

	# noinspection PyUnusedLocal
	def hide(self, *args):
		"""Hide settings window"""
		self.gui["window"].hide()
		return True
