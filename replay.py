#!/usr/bin/env python3
################################################################################
# Starcraft II Co-op Replay Tool                                               #
#                                                                              #
# Copyright (C) 2020 J.C. Fields (jcfields@jcfields.dev).                      #
#                                                                              #
# Permission is hereby granted, free of charge, to any person obtaining a copy #
# of this software and associated documentation files (the "Software"), to     #
# deal in the Software without restriction, including without limitation the   #
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or  #
# sell copies of the Software, and to permit persons to whom the Software is   #
# furnished to do so, subject to the following conditions:                     #
#                                                                              #
# The above copyright notice and this permission notice shall be included in   #
# all copies or substantial portions of the Software.                          #
#                                                                              #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR   #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,     #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER       #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING      #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS #
# IN THE SOFTWARE.                                                             #
################################################################################

# from standard library
import calendar
import json
import os
import subprocess
import threading
import time
import webbrowser

# GUI toolkit
import wx
from wx.adv import AboutBox

# plotting
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

# Starcraft/MPQ
from mpyq import MPQArchive
import sc2reader

################################################################################
# Global variables                                                             #
################################################################################

# about
TITLE = 'Starcraft II Co-op Replay Tool'
COPYRIGHT = '© 2020 J.C. Fields <jcfields@jcfields.dev>'
WEB_SITE_URL = 'https://github.com/jcfieldsdev/starcraft2-coop-replay-tool'
VERSION = '3.0.0'

MAIN_FRAME_SIZE = (1000, 750)
SUB_FRAME_SIZE = (700, 450)
FILE_EXTENSION = '.SC2Replay'

EVT_RESULT_ID = wx.NewIdRef(count=1)

# minimum game duration to be included in stats views
MINIMUM_LENGTH = 120

# ratio to convert game loops to time
GAME_LOOPS_PER_SECOND = 16

RACES = (
	'Terran', 'Zerg', 'Protoss'
)

DIFFICULTIES = (
	'Casual', 'Normal', 'Hard', 'Brutal',
	'Brutal+1', 'Brutal+2', 'Brutal+3', 'Brutal+4', 'Brutal+5', 'Brutal+6'
)

COMMANDERS = {
	'Raynor':   '#0042ff',
	'Kerrigan': '#ff00ff',
	'Artanis':  '#1ca7ea',
	'Swann':    '#fe8a0e',
	'Zagara':   '#3300bf',
	'Vorazun':  '#540081',
	'Karax':    '#ebe129',
	'Abathur':  '#ebe129',
	'Alarak':   '#400000',
	'Nova':     '#1ca7ea',
	'Stukov':   '#cca6fc',
	'Fenix':    '#fe8a0e',
	'Dehaka':   '#69c7d6',
	'Horner':   '#4a1b47',
	'Tychus':   '#a76942',
	'Zeratul':  '#00a762',
	'Stetmann': '#fe8a0e',
	'Mengsk':   '#661f1f'
}

MAPS = (
	'Chain of Ascension', 'Cradle of Death', 'Dead of Night',
	'Lock & Load', 'Malwarfare', 'Miner Evacuation',
	'Mist Opportunities', 'Oblivion Express', 'Part and Parcel',
	'Rifts to Korhal', 'Scythe of Amon', 'Temple of the Past',
	'The Vermillion Problem', 'Void Launch', 'Void Thrashing'
)

MASTERIES = {
	'Raynor': (
		('Research Cost', 'Drop Pod Speed'),
		('Hyperion Cooldown', 'Banshee Cooldown'),
		('Heal Additional Target', 'Mech Attack Speed')
	),
	'Kerrigan': (
		('Kerrigan Energy Regen', 'Kerrigan Attack Damage'),
		('Combat Unit Vespene Cost', 'Immobilization Wave'),
		('Expeditious Evolutions', 'Ability Damage/Attack Speed')
	),
	'Artanis': (
		('Shield Overcharge', 'Guardian Shell'),
		('Energy Regen/Cooldown', 'Warp Speed'),
		('Chrono Efficiency', 'Spear of Adun Energy')
	),
	'Swann': (
		('Concentrated Beam', 'Combat Drop'),
		('Immortality Protocol', 'Structure Health'),
		('Vespene Drone Cost', 'Laser Drill')
	),
	'Zagara': (
		('Zagara and Queen Regen', 'Zagara Attack Damage'),
		('Intensified Frenzy', 'Zergling Evasion'),
		('Roach Damage/Life', 'Baneling Attack Damage')
	),
	'Vorazun': (
		('Dark Pylon Range', 'Black Hole Duration'),
		('Shadow Guard Duration', 'Time Stop Unit Speed'),
		('Chrono Efficiency', 'Spear of Adun Energy')
	),
	'Karax': (
		('Combat Unit Life/Shields', 'Structure Life/Shields'),
		('Repair Beam Healing', 'Chrono Wave Energy Regen'),
		('Chrono Efficiency', 'Spear of Adun Energy')
	),
	'Abathur': (
		('Toxic Nest Damage', 'Mend Duration'),
		('Symbiote Ability', 'Double Biomass Chance'),
		('Toxic Nest Charges', 'Structure/Evolution Rate')
	),
	'Alarak': (
		('Alarak Attack Damage', 'Combat Unit Attack Speed'),
		('Empower Me Duration', 'Death Fleet Cooldown'),
		('Structure Overcharge', 'Chrono Efficiency')
	),
	'Nova': (
		('Nuke/Holo Decoy Cooldown', 'Airstrike Cost'),
		('Nova Primary Ability', 'Combat Unit Attack Speed'),
		('Nova Energy Regen', 'Unit Life Regen')
	),
	'Stukov': (
		('Volatile Infested Spawn', 'Infest Structure Cooldown'),
		('Aleksander Cooldown', 'Apocalisk Cooldown'),
		('Infested Infantry Duration', 'Mech Attack Speed')
	),
	'Fenix': (
		('Fenix Suit Attack Speed', 'Offline Energy Regen'),
		('Champion Attack Speed', 'Champion Life/Shields'),
		('Chrono Efficiency', 'Extra Starting Supply')
	),
	'Dehaka': (
		('Devour Healing', 'Devour Buff Duration'),
		('Primal Wurm Cooldown', 'Pack Leader Duration'),
		('Gene Mutation Chance', 'Dehaka Attack Speed')
	),
	'Horner': (
		('Strike Fighter AoE', 'Stronger Death Chance'),
		('Significant Other Bonuses', 'Double Salvage Chance'),
		('Air Fleet Travel', 'Mag Mines')
	),
	'Tychus': (
		('Tychus Attack Speed', 'Shredder Grenade Cooldown'),
		('Tri-Outlaw Research', 'Outlaw Availability'),
		('Medivac Pickup Cooldown', 'Odin Cooldown')
	),
	'Zeratul': (
		('Zeratul Attack Speed', 'Combat Unit Attack Speed'),
		('Artifact Fragment Spawn', 'Support Calldown Cooldown'),
		('Legendary Legion Cost', 'Avatar Cooldown')
	),
	'Stetmann': (
		('Upgrade Resource Cost', 'Gary Ability Cooldown'),
		('Stetzone Bonuses', 'Maximum Egonergy Pool'),
		('Stetellite Cooldown', 'Structure Morph Rate')
	),
	'Mengsk': (
		('Laborer/Trooper Support', 'Royal Guard Support'),
		('Terrible Damage', 'Royal Guard Cost'),
		('Starting Mandate', 'Royal Guard XP Gain')
	)
}

PRESTIGES = {
	'Raynor': (
		'Renegade Commander', 'Backwater Marshal',
		'Rough Rider', 'Rebel Raider'
	),
	'Kerrigan': (
		'Queen of Blades', 'Malevolent Matriarch',
		'Folly of Man', 'Desolate Queen'
	),
	'Artanis': (
		'Hierarch of the Daelaam', 'Valorous Inspirator',
		'Nexus Legate', 'Arkship Commandant'
	),
	'Swann': (
		'Chief Engineer', 'Heavy Weapons Specialist',
		'Grease Monkey', 'Payload Director'
	),
	'Zagara': (
		'Swarm Broodmother', 'Scourge Queen',
		'Mother of Constructs', 'Apex Predator'
	),
	'Vorazun': (
		'Matriarch of the Nerazim', 'Spirit of Respite',
		'Withering Siphon', 'Keeper of Shadows'
	),
	'Karax': (
		'Khalai Phase-Smith', 'Architect of War',
		'Templar Apparent', 'Solarite Celestial'
	),
	'Abathur': (
		'Evolution Master', 'Essence Hoarder',
		'Tunneling Horror', 'The Limitless'
	),
	'Alarak': (
		'Tal\'darim Highlord', 'Artificer of Souls',
		'Tyrant Ascendant', 'Shadow of Death'
	),
	'Nova': (
		'Dominion Ghost', 'Soldier of Fortune',
		'Tactical Dispatcher', 'Infiltration Specialist'
	),
	'Stukov': (
		'Infested Admiral', 'Frightful Fleshwelder',
		'Plague Warden', 'Lord of the Horde'
	),
	'Fenix': (
		'Purifier Executor', 'Akhundelar',
		'Network Administrator', 'Unconquered Spirit'
	),
	'Dehaka': (
		'Primal Pack Leader', 'Devouring One',
		'Primal Contender', 'Broodbrother'
	),
	'Horner': (
		'Mercenary Leader and Dominion Admiral', 'Chaotic Power Couple',
		'Wing Commanders', 'Galactic Gunrunners'
	),
	'Tychus': (
		'Legendary Outlaw', 'Technical Recruiter',
		'Lone Wolf', 'Dutiful Dogwalker'
	),
	'Zeratul': (
		'Dark Prelate', 'Anakh Su\'n',
		'Knowledge Seeker', 'Herald of the Void'
	),
	'Stetmann': (
		'Hero Genius (Henius)', 'Signal Savant',
		'Best Buddy', 'Oil Baron'
	),
	'Mengsk': (
		'Emperor of the Dominion', 'Toxic Tyrant',
		'Principal Proletariat', 'Merchant of Death'
	)
}

################################################################################
# MainFrame class                                                              #
################################################################################

class MainFrame(wx.Frame):
	def __init__(self):
		self.config = wx.Config(TITLE)

		width, height = MAIN_FRAME_SIZE
		size = (self.config.ReadInt('width', width),
		        self.config.ReadInt('height', height))

		wx.Frame.__init__(self, None, title=TITLE, size=size)

		self.Bind(wx.EVT_CLOSE, self.close)

		self.panel = MainPanel(self)
		self.create_menu()

	def create_menu(self):
		self.menu_bar = wx.MenuBar()

		menu_file = wx.Menu()
		item_open = menu_file.Append(
			wx.ID_OPEN, '&Open Folder...',
			'Open a folder containing replays'
		)
		item_scan = menu_file.Append(
			wx.ID_ANY, '&Reload',
			'Reloads the current directory'
		)
		menu_file.AppendSeparator()
		item_close = menu_file.AppendRadioItem(
			wx.ID_EXIT, '&Close',
			'Close the program'
		)

		menu_tab = wx.Menu()
		item_files = menu_tab.AppendRadioItem(
			1, '&Files',
			'Switch to Files tab'
		)
		item_commanders = menu_tab.AppendRadioItem(
			2, '&Commanders',
			'Switch to Commanders tab'
		)
		item_maps = menu_tab.AppendRadioItem(
			3, '&Maps',
			'Switch to Maps tab'
		)
		item_win_rate = menu_tab.AppendRadioItem(
			4, '&Win Rate',
			'Switch to Win Rate tab'
		)
		item_time = menu_tab.AppendRadioItem(
			5, '&Time',
			'Switch to Times tab'
		)
		item_apm = menu_tab.AppendRadioItem(
			6, '&APM',
			'Switch to APM tab'
		)

		menu_help = wx.Menu()
		item_web_site = menu_help.Append(
			wx.ID_HELP, 'Visit &Web Site',
			'Visit the program web site'
		)
		item_about = menu_help.Append(
			wx.ID_ABOUT, '&About {}'.format(TITLE),
			'About this program'
		)

		self.Bind(wx.EVT_MENU, self.panel.browse, item_open)
		self.Bind(wx.EVT_MENU, self.panel.scan, item_scan)
		self.Bind(wx.EVT_MENU, self.close, item_close)
		self.Bind(wx.EVT_MENU, self.panel.switch_tab, item_files)
		self.Bind(wx.EVT_MENU, self.panel.switch_tab, item_commanders)
		self.Bind(wx.EVT_MENU, self.panel.switch_tab, item_maps)
		self.Bind(wx.EVT_MENU, self.panel.switch_tab, item_win_rate)
		self.Bind(wx.EVT_MENU, self.panel.switch_tab, item_time)
		self.Bind(wx.EVT_MENU, self.panel.switch_tab, item_apm)
		self.Bind(wx.EVT_MENU, self.open_web_site, item_web_site)
		self.Bind(wx.EVT_MENU, self.about, item_about)

		self.menu_bar.Append(menu_file, '&File')
		self.menu_bar.Append(menu_tab, '&Tab')
		self.menu_bar.Append(menu_help, '&Help')
		self.SetMenuBar(self.menu_bar)

	def write_config(self):
		width, height = self.GetSize().Get() # converts size object to tuple
		self.config.WriteInt('width', width)
		self.config.WriteInt('height', height)

	def open_web_site(self, event=None):
		webbrowser.open(WEB_SITE_URL)

	def about(self, event=None):
		dialog = wx.adv.AboutDialogInfo()
		dialog.SetName(TITLE);
		dialog.SetCopyright(COPYRIGHT)
		dialog.SetVersion(VERSION)

		wx.adv.AboutBox(dialog)

	def close(self, event=None):
		self.write_config()
		self.Destroy()

################################################################################
# MainPanel class                                                              #
################################################################################

class MainPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.parent = parent
		self.replays = Replays(self)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddMany((
			(self.create_dir_sizer(), 0, wx.ALL | wx.EXPAND, 5),
			(self.create_tab_sizer(), 1, wx.ALL | wx.EXPAND, 5)
		))
		self.SetSizer(sizer)

		# reloads current tab after replay scan completes
		self.Connect(-1, -1, EVT_RESULT_ID, self.update_progress)
		self.scan()

	def create_dir_sizer(self):
		self.text_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.text_ctrl.SetValue(self.parent.config.Read('dir', ''))
		self.text_ctrl.Bind(wx.EVT_TEXT_ENTER, self.scan)

		button_browse = wx.Button(self, label='Br&owse...')
		button_browse.Bind(wx.EVT_BUTTON, self.browse)
		button_scan = wx.Button(self, label='&Reload')
		button_scan.Bind(wx.EVT_BUTTON, self.scan)

		self.button_errors = wx.Button(self, label='&Errors')
		self.button_errors.Disable()
		self.button_errors.Bind(wx.EVT_BUTTON, self.show_errors)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(wx.StaticText(self, label='Path:'), 0, wx.CENTER),
			(self.text_ctrl, 1, wx.ALL, 5),
			(button_browse, 0, wx.TOP | wx.BOTTOM | wx.LEFT, 5),
			(button_scan, 0, wx.TOP | wx.BOTTOM | wx.LEFT, 5),
			(self.button_errors, 0, wx.ALL, 5)
		))

		return sizer

	def create_tab_sizer(self):
		self.notebook = wx.Notebook(self)

		files_tab = FilesTab(self.notebook, self.replays)
		commanders_tab = CommandersTab(self.notebook, self.replays)
		maps_tab = MapsTab(self.notebook, self.replays)
		win_rate_tab = WinRateTab(self.notebook, self.replays)
		time_tab = TimeTab(self.notebook, self.replays)
		apm_tab = ApmTab(self.notebook, self.replays)

		self.notebook.AddPage(files_tab, 'Files')
		self.notebook.AddPage(commanders_tab, 'Commanders')
		self.notebook.AddPage(maps_tab, 'Maps')
		self.notebook.AddPage(win_rate_tab, 'Win Rate')
		self.notebook.AddPage(time_tab, 'Time')
		self.notebook.AddPage(apm_tab, 'APM')

		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.reload, self.notebook)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.notebook, 1, wx.EXPAND)

		return sizer

	def switch_tab(self, event):
		self.notebook.SetSelection(event.GetId() - 1)

	def browse(self, event=None):
		dir_dialog = wx.DirDialog(
			self, 'Choose a directory containing replays:',
			style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
		)

		with dir_dialog as dialog:
			if dialog.ShowModal() == wx.ID_OK:
				path = dialog.GetPath()
				self.text_ctrl.SetValue(path)
				self.scan() # reloads current tab

	def reload(self, event=None):
		selected = self.notebook.GetSelection()

		if event is not None:
			# checks associated menu item
			items = self.parent.menu_bar.GetMenu(1).GetMenuItems()
			items[selected].Check()

		# calls reload method for active tab
		self.notebook.GetPage(selected).reload()

	def scan(self, event=None):
		path = self.text_ctrl.GetValue()

		if path != '':
			dirname = os.path.basename(path)

			if os.path.exists(path):
				self.parent.config.Write('dir', path)

				wx.BeginBusyCursor()

				worker = threading.Thread(
					target=self.replays.reload,
					args=(path,)
				)
				worker.start()

				self.progress_dialog = wx.GenericProgressDialog(
					'Scanning replays',
					'Scanning replays in the directory "{}"...'.format(dirname)
				)
				self.progress_dialog.ShowModal()

				wx.EndBusyCursor()
			else:
				wx.MessageBox(
					'The directory "{}" does not exist.'.format(dirname),
					'Error', wx.OK | wx.ICON_ERROR
				)

		if len(errors) > 0:
			self.button_errors.Enable()
		else:
			self.button_errors.Disable()

	def update_progress(self, event):
		if event.complete:
			self.progress_dialog.EndModal(0)
			self.progress_dialog.Destroy()
			self.reload()
		else:
			if event.index < 1:
				self.progress_dialog.SetRange(event.total)

			self.progress_dialog.Update(event.index)

	def show_errors(self, event=None):
		frame = SubFrame(self, ErrorPanel, 'Errors')
		frame.Show()
		frame.Center()

################################################################################
# FilesTab class                                                               #
################################################################################

class FilesTab(wx.Panel):
	def __init__(self, parent, replays):
		wx.Panel.__init__(self, parent)
		self.replays = replays
		self.filtered = []

		self.list_ctrl = self.create_list_ctrl()
		self.info_sizer = self.create_info_sizer()

		player_sizer_flags = wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND
		filter_sizer_flags = wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND
		info_sizer_flags = wx.ALL | wx.EXPAND | wx.RESERVE_SPACE_EVEN_IF_HIDDEN

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.AddMany((
			(self.create_player_sizer(), 0, player_sizer_flags, 5),
			(self.create_filter_sizer(), 0, filter_sizer_flags, 5),
			(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 5),
			(self.info_sizer, 1, info_sizer_flags, 5),
			(self.create_button_sizer(), 0, wx.EXPAND, 5)
		))
		self.sizer.Hide(self.info_sizer)
		self.SetSizer(self.sizer)

	def create_player_sizer(self):
		self.player_choice = wx.Choice(self, choices=())
		self.player_choice.Bind(wx.EVT_CHOICE, self.update)

		commanders = ['(Any commander)']
		commanders.extend(sorted(COMMANDERS.keys()))

		self.commander_choice = wx.Choice(self, choices=commanders)
		self.commander_choice.Bind(wx.EVT_CHOICE, self.update)
		self.commander_choice.SetSelection(0)

		maps = ['(Any map)']
		maps.extend(MAPS)

		self.map_choice = wx.Choice(self, choices=maps)
		self.map_choice.Bind(wx.EVT_CHOICE, self.update)
		self.map_choice.SetSelection(0)

		button_export = wx.Button(self, label='&Save...')
		button_export.Bind(wx.EVT_BUTTON, self.export_csv)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(wx.StaticText(self, label='Player:'), 0, wx.CENTER),
			(self.player_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Commander:'), 0, wx.CENTER),
			(self.commander_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Map:'), 0, wx.CENTER),
			(self.map_choice, 0, wx.ALL, 5)
		))
		sizer.AddStretchSpacer()
		sizer.Add(button_export, 0, wx.ALL, 5)

		return sizer

	def create_filter_sizer(self):
		difficulties = ['(Any difficulty)']
		difficulties.extend(DIFFICULTIES)

		self.difficulty_choice = wx.Choice(self, choices=difficulties)
		self.difficulty_choice.Bind(wx.EVT_CHOICE, self.update)
		self.difficulty_choice.SetSelection(0)

		races = ['(Any race)']
		races.extend(RACES)

		self.enemy_race_choice = wx.Choice(self, choices=races)
		self.enemy_race_choice.Bind(wx.EVT_CHOICE, self.update)
		self.enemy_race_choice.SetSelection(0)

		mutators_choices = ('(Any)', 'Yes', 'No')
		self.mutators_choice = wx.Choice(self, choices=mutators_choices)
		self.mutators_choice.Bind(wx.EVT_CHOICE, self.update)
		self.mutators_choice.SetSelection(0)

		result_choices = ('(Any)', 'Victory', 'Defeat')
		self.result_choice = wx.Choice(self, choices=result_choices)
		self.result_choice.Bind(wx.EVT_CHOICE, self.update)
		self.result_choice.SetSelection(0)

		self.games = wx.StaticText(self, style=wx.ALIGN_RIGHT, size=(100, -1))

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(wx.StaticText(self, label='Difficulty:'), 0, wx.CENTER),
			(self.difficulty_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Enemy Race:'), 0, wx.CENTER),
			(self.enemy_race_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Mutators:'), 0, wx.CENTER),
			(self.mutators_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Result:'), 0, wx.CENTER),
			(self.result_choice, 0, wx.ALL, 5)
		))
		sizer.AddStretchSpacer()
		sizer.Add(self.games, 0, wx.ALL, 5)

		return sizer

	def create_list_ctrl(self):
		element = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

		element.InsertColumn(0, 'Map', width=150)
		element.InsertColumn(1, 'Date', width=200)
		element.InsertColumn(2, 'Length', width=60)
		element.InsertColumn(3, 'Player 1', width=200)
		element.InsertColumn(4, 'Player 2', width=200)
		element.InsertColumn(5, 'Mutators', width=60)
		element.InsertColumn(6, 'Result', width=60)

		element.Bind(wx.EVT_LIST_ITEM_SELECTED, self.list_selected)
		element.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.list_deselected)

		return element

	def create_info_sizer(self):
		sizer = wx.BoxSizer(wx.HORIZONTAL)

		labels = ('map', 'datetime', 'length', 'enemy_race', 'speed', 'version',
		          'region', 'mutators', 'result')
		size = (180, -1)
		self.text = {t: wx.StaticText(self, label='', size=size)
		             for t in labels}

		self.text['map'].SetFont(self.text['map'].GetFont().MakeBold())

		column = wx.FlexGridSizer(cols=2, gap=(5, 5))
		column.AddMany((
			wx.StaticText(self, label='Map:'), self.text['map'],
			wx.StaticText(self, label='Date:'), self.text['datetime'],
			wx.StaticText(self, label='Length:'), self.text['length'],
			wx.StaticText(self, label='Enemy Race:'), self.text['enemy_race'],
			wx.StaticText(self, label='Speed:'), self.text['speed'],
			wx.StaticText(self, label='Version:'), self.text['version'],
			wx.StaticText(self, label='Gateway:'), self.text['region'],
			wx.StaticText(self, label='Mutators:'), self.text['mutators'],
			wx.StaticText(self, label='Result:'), self.text['result']
		))
		sizer.Add(column, 1, wx.ALL | wx.EXPAND, 5)

		players = []

		for n in range(0, 2):
			labels = ('name', 'commander', 'prestige',
			          'level', 'difficulty', 'apm',
			          'label1a', 'label1b', 'label2a',
			          'label2b', 'label3a', 'label3b',
			          'master1a', 'master1b', 'master2a',
			          'master2b', 'master3a', 'master3b')
			player = {}

			for label in labels:
				# sets default size for mastery labels
				width = 200 if label.startswith('label') else -1

				player[label] = wx.StaticText(self, label='', size=(width, -1))

			player['name'].SetFont(player['name'].GetFont().MakeBold())

			players.append(player)

		self.text['players'] = players

		for n in range(0, 2):
			player = self.text['players'][n]

			column = wx.FlexGridSizer(cols=2, gap=(5, 5))
			column.AddMany((
				wx.StaticText(self, label='Name:'), player['name'],
				wx.StaticText(self, label='Commander:'), player['commander'],
				wx.StaticText(self, label='Prestige:'), player['prestige'],
				wx.StaticText(self, label='Level:'), player['level'],
				wx.StaticText(self, label='Difficulty:'), player['difficulty'],
				wx.StaticText(self, label='APM:'), player['apm'],
				player['label1a'], player['master1a'],
				player['label1b'], player['master1b'],
				player['label2a'], player['master2a'],
				player['label2b'], player['master2b'],
				player['label3a'], player['master3a'],
				player['label3b'], player['master3b']
			))
			sizer.Add(column, 2, wx.ALL | wx.EXPAND, 5)

		return sizer

	def create_button_sizer(self):
		self.button_watch = wx.Button(self, label='&Watch Replay')
		self.button_watch.Disable()
		self.button_watch.Bind(wx.EVT_BUTTON, self.watch_replay)

		self.button_delete = wx.Button(self, label='&Delete File')
		self.button_delete.Disable()
		self.button_delete.Bind(wx.EVT_BUTTON, self.delete_file)

		self.button_messages = wx.Button(self, label='&Messages')
		self.button_messages.Disable()
		self.button_messages.Bind(wx.EVT_BUTTON, self.show_messages)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(self.button_watch, 0, wx.ALL, 5),
			(self.button_messages, 0, wx.TOP | wx.BOTTOM, 5)
		))
		sizer.AddStretchSpacer()
		sizer.Add(self.button_delete, 0, wx.ALL, 5)

		return sizer

	def filter(self):
		name, commander, map_ = self.get_player_selected()
		filter_, enemy_race, mutators, result = self.get_filter_selected()

		for replay in self.replays:
			# filters enemy race
			if not enemy_race.startswith('(') \
			and enemy_race != replay['enemy_race']:
				continue

			# filters map
			if not map_.startswith('(') \
			and map_ != replay['map']:
				continue

			# filters mutators
			if not mutators.startswith('(') \
			and (mutators == 'Yes') != replay['mutators']:
				continue

			# filters result
			if not result.startswith('(') \
			and (result == 'Victory') != replay['result']:
				continue

			players = replay.get('players', ())

			# filters difficulty
			if not filter_.startswith('('):
				difficulty = max(
					players[0]['difficulty'],
					players[1]['difficulty']
				)
				brutal_plus = max(
					players[0]['brutal_plus'],
					players[1]['brutal_plus']
				)

				if filter_ != format_difficulty(difficulty, brutal_plus):
					continue

			if len(players) < 2:
				continue

			# filters player and commander
			# both player and commander must match
			for n in range(0, 2):
				any_player = name.startswith('(')

				if not any_player and name != format_name(players[n]['name']):
					continue

				any_commander = commander.startswith('(')

				if filter_ and not any_commander \
				and commander != players[n]['commander']:
					continue

				yield n, replay
				break # only counts map once per game

	def get_player_selected(self):
		player_selected = self.player_choice.GetSelection()
		commander_selected = self.commander_choice.GetSelection()
		map_selected = self.map_choice.GetSelection()

		return (
			self.player_choice.GetString(player_selected),
			self.commander_choice.GetString(commander_selected),
			self.map_choice.GetString(map_selected)
		)

	def get_filter_selected(self):
		difficulty_selected = self.difficulty_choice.GetSelection()
		enemy_race_selected = self.enemy_race_choice.GetSelection()
		mutators_selected = self.mutators_choice.GetSelection()
		result_selected = self.result_choice.GetSelection()

		return (
			self.difficulty_choice.GetString(difficulty_selected),
			self.enemy_race_choice.GetString(enemy_race_selected),
			self.mutators_choice.GetString(mutators_selected),
			self.result_choice.GetString(result_selected)
		)

	def set_players(self):
		choices = {'(Any player)': 2}

		for replay in self.replays:
			players = replay.get('players', ())

			if len(players) < 2:
				continue

			for n in range(0, 2):
				name = format_name(players[n]['name'])
				choices[name] = choices.get(name, 0) + 1

		# filters only players with more than one game saved
		choices = {k: v for k, v in choices.items() if v > 1}
		self.player_choice.SetItems(sorted(choices.keys(), key=str.casefold))
		self.player_choice.SetSelection(0)

	def reload(self):
		self.set_players()
		self.update()

	def update(self, event=None):
		self.list_ctrl.DeleteAllItems()
		self.list_deselected()

		self.filtered.clear()

		for i, (n, replay) in enumerate(self.filter()):
			self.filtered.append(replay)

			players = replay.get('players', ())

			player1 = format_player(players[0]['name'], players[0]['commander'])
			player2 = format_player(players[1]['name'], players[1]['commander'])

			self.list_ctrl.InsertItem(i, replay['map'])
			self.list_ctrl.SetItem(i, 1, format_date(replay['datetime']))
			self.list_ctrl.SetItem(i, 2, format_time(replay['length']))
			self.list_ctrl.SetItem(i, 3, player1)
			self.list_ctrl.SetItem(i, 4, player2)
			self.list_ctrl.SetItem(i, 5, format_boolean(replay['mutators']))
			self.list_ctrl.SetItem(i, 6, format_result(replay['result']))

		length = len(self.filtered)
		self.games.SetLabel('{:d} {}'.format(
			length,
			'game' if length == 1 else 'games'
		))

	def update_info(self, event=None):
		replay = self.get_list_selected()

		if len(replay) == 0:
			return

		players = replay.get('players', ())

		values = { # must escape '&' for StaticText, used for accelerators
			'map':        replay['map'].replace('&', '&&'),
			'datetime':   format_date(replay['datetime']),
			'length':     format_time(replay['length']),
			'enemy_race': replay['enemy_race'],
			'speed':      replay['speed'],
			'version':    replay['version'],
			'region':     format_region(replay['region']),
			'mutators':   format_boolean(replay['mutators']),
			'result':     format_result(replay['result'])
		}

		for key, value in values.items():
			self.text[key].SetLabel(value)

		for n in range(0, 2):
			# default labels for unknown commanders
			mastery_labels = MASTERIES.get(
				players[n]['commander'],
				(('Mastery Set 1a', 'Mastery Set 1b'),
				 ('Mastery Set 2a', 'Mastery Set 2b'),
				 ('Mastery Set 3a', 'Mastery Set 3b'))
			)
			# default values for pre-mastery replays
			mastery_values = players[n].get('mastery', ((0, 0), (0, 0), (0, 0)))

			if len(mastery_labels) < 3:
				continue

			prestige = format_prestige(
				players[n]['commander'],
				players[n]['prestige']
			)
			level = format_level(
				players[n]['level'],
				players[n]['mastery_level']
			)
			difficulty = format_difficulty(
				players[n]['difficulty'],
				players[n]['brutal_plus']
			)

			values = {
				'name':       format_name(players[n]['name']),
				'commander':  players[n]['commander'],
				'prestige':   prestige,
				'level':      level,
				'difficulty': difficulty,
				'apm':        str(players[n]['apm']),
				'label1a':    mastery_labels[0][0] + ':',
				'label1b':    mastery_labels[0][1] + ':',
				'label2a':    mastery_labels[1][0] + ':',
				'label2b':    mastery_labels[1][1] + ':',
				'label3a':    mastery_labels[2][0] + ':',
				'label3b':    mastery_labels[2][1] + ':',
				'master1a':   str(mastery_values[0]),
				'master1b':   str(mastery_values[1]),
				'master2a':   str(mastery_values[2]),
				'master2b':   str(mastery_values[3]),
				'master3a':   str(mastery_values[4]),
				'master3b':   str(mastery_values[5])
			}

			for key, value in values.items():
				self.text['players'][n][key].SetLabel(value)

		self.info_sizer.Layout() # reflows layout

	def watch_replay(self, event=None):
		replay = self.get_list_selected()
		filepath = replay['filepath']
		filename = replay['filename']

		if not os.path.exists(filepath):
			wx.MessageBox(
				'The file "{}" does not exist.'.format(filename),
				'Error', wx.OK | wx.ICON_ERROR
			)

			return

		try:
			if os.name == 'nt': # Windows
				os.startfile(filepath)
			else:
				subprocess.check_call(('open', filepath))
		except Exception as e:
			wx.MessageBox(
				'Could not open the file "{}".'.format(filename),
				'Error', wx.OK | wx.ICON_ERROR
			)
			errors.append((filepath, e, time.localtime()))

	def delete_file(self, event=None):
		replay = self.get_list_selected()
		filepath = replay['filepath']
		filename = replay['filename']

		if not os.path.exists(filepath):
			wx.MessageBox(
				'The file "{}" does not exist.'.format(filename),
				'Error', wx.OK | wx.ICON_ERROR
			)

			return

		result = wx.MessageBox(
			'Are you sure you want to delete the file "{}"?'.format(filename),
			'Confirm Delete', wx.YES_NO | wx.CANCEL | wx.ICON_WARNING
		)

		if result == wx.YES:
			try:
				self.replays.remove_replay(replay)
				os.remove(filepath)
			except Exception as e:
				wx.MessageBox(
					'Could not delete the file "{}".'.format(filename),
					'Error', wx.OK | wx.ICON_ERROR
				)
				errors.append((filepath, e, time.localtime()))

	def show_messages(self, event=None):
		replay = self.get_list_selected()

		frame = SubFrame(self, MessagePanel, 'Messages')
		frame.panel.set_messages(replay['messages'])
		frame.Show()
		frame.Center()

	def get_list_selected(self):
		selected = self.list_ctrl.GetNextSelected(-1)

		if selected >= 0:
			return self.filtered[selected]

		return {}

	def list_selected(self, event=None):
		self.sizer.Show(self.info_sizer)
		self.update_info()

		self.button_delete.Enable()
		self.button_watch.Enable()
		self.button_messages.Enable()

	def list_deselected(self, event=None):
		self.sizer.Hide(self.info_sizer)

		self.button_delete.Disable()
		self.button_watch.Disable()
		self.button_messages.Disable()

	def export_csv(self, event=None):
		header = ('id', 'map', 'player', 'commander', 'level', 'mastery_level',
		          'prestige', 'difficulty', 'victory', 'mutators')

		file_dialog = wx.FileDialog(
			self, 'Save CSV file',
			wildcard='CSV files (*.csv)|*.csv',
			style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
		)

		with file_dialog as dialog:
			if dialog.ShowModal() == wx.ID_CANCEL:
				return

			filepath = dialog.GetPath()

			try:
				with open(filepath, 'w') as file:
					file.write(','.join(header) + '\n' + self.save_csv())
			except Exception as e:
				filename = os.path.basename(filepath)
				wx.MessageBox(
					'Could not write the file "{}".'.format(filename),
					'Error', wx.OK | wx.ICON_ERROR
				)
				errors.append((filepath, e, time.localtime()))

	def prepare_line(self, i, n, replay):
		player = replay['players'][n]
		row = (
			str(i),
			replay['map'],
			player['name'],
			player['commander'],
			str(player['level']),
			str(player['mastery_level']),
			format_prestige(player['commander'], player['prestige']),
			format_difficulty(player['difficulty'], player['brutal_plus']),
			format_boolean(replay['result']),
			format_boolean(replay['mutators'])
		)

		return ','.join(row) + '\n'

	def save_csv(self):
		text = ''

		for i, (n, replay) in enumerate(self.filter()):
			text += self.prepare_line(i, n, replay)

		return text

################################################################################
# ChartTab class                                                               #
################################################################################

class ChartTab(wx.Panel):
	def __init__(self, parent, replays):
		wx.Panel.__init__(self, parent)
		self.replays = replays

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddMany((
			(self.create_filter_sizer(), 0, wx.ALL | wx.EXPAND, 5),
			(self.create_chart_sizer(), 1, wx.ALL | wx.EXPAND, 5)
		))
		self.SetSizer(sizer)

	def create_chart_sizer(self):
		self.chart = PieChart(self, (7, 5.25))

		self.list_ctrl = self.create_list_ctrl()

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(self.chart, 3, wx.ALL | wx.EXPAND, 5),
			(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 5)
		))

		return sizer

	def create_list_ctrl(self):
		element = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

		element.InsertColumn(0, 'Item', width=150)
		element.InsertColumn(1, 'Games', width=50)
		element.InsertColumn(2, 'Percent', width=50)

		return element

	def reload(self):
		self.set_players()
		self.update()

	def update(self, event=None):
		self.set_filter()

		items, total = self.count()
		data = {k: v / total for k, v in items.items()}

		if len(data) > 0: # parallel sorts keys and values by values
			zipped = sorted(zip(data.values(), data.keys()))
			values, labels = zip(*zipped)
		else:
			values = ()
			labels = ()

		self.chart.set_data(labels, values)

		self.list_ctrl.DeleteAllItems()
		length = len(values)

		for n in range(0, length):
			# iterates through lists in reverse (largest values first)
			item = labels[length - n - 1]
			value = values[length - n - 1]

			self.list_ctrl.InsertItem(n, item)
			self.list_ctrl.SetItem(n, 1, str(items[item]))
			self.list_ctrl.SetItem(n, 2, format_percentage(value))

	def get_selected(self):
		selected = self.filter_choice.GetSelection()

		return (
			self.player_choice.GetString(self.player_choice.GetSelection()),
			self.filter_choice.GetString(selected) if selected >= 0 else ''
		)

	def set_players(self):
		choices = {'(Any player)': 2}

		for replay in self.replays:
			players = replay.get('players', ())

			if len(players) < 2:
				continue

			for n in range(0, 2):
				name = format_name(players[n]['name'])
				choices[name] = choices.get(name, 0) + 1

		# filters only players with more than one game saved
		choices = {k: v for k, v in choices.items() if v > 1}
		self.player_choice.SetItems(sorted(choices.keys(), key=str.casefold))

		# selects player with most games by default
		most_played = max(choices.keys(), key=lambda k: choices[k])
		index = self.player_choice.FindString(most_played)
		self.player_choice.SetSelection(index)

################################################################################
# CommandersTab class                                                          #
################################################################################

class CommandersTab(ChartTab):
	def __init__(self, parent, replays):
		ChartTab.__init__(self, parent, replays)

	def create_filter_sizer(self):
		self.player_choice = wx.Choice(self, choices=())
		self.player_choice.Bind(wx.EVT_CHOICE, self.update)

		self.filter_choice = wx.Choice(self, choices=())
		self.filter_choice.Bind(wx.EVT_CHOICE, self.update)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(wx.StaticText(self, label='Player:'), 0, wx.CENTER),
			(self.player_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Map:'), 0, wx.CENTER),
			(self.filter_choice, 0, wx.ALL, 5)
		))

		return sizer

	def filter(self, filter_=True):
		name, map_ = self.get_selected()

		for replay in self.replays:
			# skips games that do not include selected map
			if filter_ and not map_.startswith('(') and map_ != replay['map']:
				continue

			players = replay.get('players', ())

			if len(players) < 2:
				continue

			for n in range(0, 2):
				any_player = name.startswith('(')

				# only counts for all players or selected player
				if any_player or name == format_name(players[n]['name']):
					yield n, replay

					# stops looking after finding player
					# unless looking for all players
					if not any_player:
						break

	def count(self):
		items = {}
		total = 0

		for n, replay in self.filter(filter_=True):
			commander = replay['players'][n]['commander']
			items[commander] = items.get(commander, 0) + 1
			total += 1

		return items, total

	def set_filter(self):
		choices = ['(Any map)']

		for n, replay in self.filter(filter_=False):
			map_ = replay['map']

			if not map_ in choices:
				choices.append(map_)

		if len(self.filter_choice.GetItems()) != len(choices):
			self.filter_choice.SetItems(sorted(choices))
			self.filter_choice.SetSelection(0)

################################################################################
# MapsTab class                                                                #
################################################################################

class MapsTab(ChartTab):
	def __init__(self, parent, replays):
		ChartTab.__init__(self, parent, replays)

	def create_filter_sizer(self):
		self.player_choice = wx.Choice(self, choices=())
		self.player_choice.Bind(wx.EVT_CHOICE, self.update)

		self.filter_choice = wx.Choice(self, choices=())
		self.filter_choice.Bind(wx.EVT_CHOICE, self.update)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(wx.StaticText(self, label='Player:'), 0, wx.CENTER),
			(self.player_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Commander:'), 0, wx.CENTER),
			(self.filter_choice, 0, wx.ALL, 5)
		))

		return sizer

	def filter(self, filter_=True):
		name, commander = self.get_selected()

		for replay in self.replays:
			players = replay.get('players', ())

			if len(players) < 2:
				continue

			for n in range(0, 2):
				any_player = name.startswith('(')

				# only counts for all players or selected player
				if not any_player and name != format_name(players[n]['name']):
					continue

				any_commander = commander.startswith('(')

				# skips games that do not include selected commander
				if filter_ and not any_commander \
				and commander != players[n]['commander']:
					continue

				yield n, replay
				break # only counts map once per game

	def count(self):
		items = {}
		total = 0

		for n, replay in self.filter(filter_=True):
			map_ = replay['map']
			items[map_] = items.get(map_, 0) + 1
			total += 1

		return items, total

	def set_filter(self):
		choices = ['(Any commander)']

		for n, replay in self.filter(filter_=False):
			commander = replay['players'][n]['commander']

			if not commander in choices:
				choices.append(commander)

		if len(self.filter_choice.GetItems()) != len(choices):
			self.filter_choice.SetItems(sorted(choices))
			self.filter_choice.SetSelection(0)

################################################################################
# WinRateTab class                                                             #
################################################################################

class WinRateTab(wx.Panel):
	def __init__(self, parent, replays):
		wx.Panel.__init__(self, parent)
		self.replays = replays

		self.diff_chart = BarChart(self, (10, 2.5))

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddMany((
			(self.diff_chart, 1, wx.ALL | wx.EXPAND, 5),
			(self.create_filter_sizer(), 0, wx.ALL | wx.EXPAND, 5),
			(self.create_chart_sizer(), 1, wx.ALL | wx.EXPAND, 5)
		))
		self.SetSizer(sizer)

	def create_filter_sizer(self):
		difficulties = ['(Any difficulty)']
		difficulties.extend(DIFFICULTIES)

		self.difficulty_choice = wx.Choice(self, choices=difficulties)
		self.difficulty_choice.Bind(wx.EVT_CHOICE, self.update)
		self.difficulty_choice.SetSelection(0)

		races = ['(Any race)']
		races.extend(RACES)

		self.enemy_race_choice = wx.Choice(self, choices=races)
		self.enemy_race_choice.Bind(wx.EVT_CHOICE, self.update)
		self.enemy_race_choice.SetSelection(0)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(wx.StaticText(self, label='Difficulty:'), 0, wx.CENTER),
			(self.difficulty_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Enemy Race:'), 0, wx.CENTER),
			(self.enemy_race_choice, 0, wx.ALL, 5),
		))

		return sizer

	def create_chart_sizer(self):
		self.regular_win_chart = PieChart(self, (3, 2.5))
		self.mutator_win_chart = PieChart(self, (3, 2.5))

		self.list_ctrl = self.create_list_ctrl()

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(self.regular_win_chart, 1, wx.ALL | wx.EXPAND, 5),
			(self.mutator_win_chart, 1, wx.ALL | wx.EXPAND, 5),
			(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 5)
		))

		return sizer

	def create_list_ctrl(self):
		element = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

		element.InsertColumn(0, 'Difficulty', width=85)
		element.InsertColumn(1, 'R. Win', width=50)
		element.InsertColumn(2, 'R. Loss', width=50)
		element.InsertColumn(3, 'M. Win', width=50)
		element.InsertColumn(4, 'M. Loss', width=50)

		return element

	def count(self):
		filter_, enemy_race = self.get_selected()

		regular_games = [0] * 10
		regular_wins = [0] * 10
		regular_total_games = 0
		regular_total_wins = 0

		mutator_games = [0] * 10
		mutator_wins = [0] * 10
		mutator_total_games = 0
		mutator_total_wins = 0

		for replay in self.replays:
			if not enemy_race.startswith('(') \
			and enemy_race != replay['enemy_race']:
				continue

			players = replay.get('players', ())
			difficulty = max(
				players[0]['difficulty'],
				players[1]['difficulty']
			)
			brutal_plus = max(
				players[0]['brutal_plus'],
				players[1]['brutal_plus']
			)
			mutators = replay['mutators']

			if mutators:
				if replay['result']:
					mutator_wins[difficulty - 1 + brutal_plus] += 1

				mutator_games[difficulty - 1 + brutal_plus] += 1
			else:
				if replay['result']:
					regular_wins[difficulty - 1] += 1

				regular_games[difficulty - 1] += 1

			if filter_.startswith('(') \
			or filter_ == format_difficulty(difficulty, brutal_plus):
				if mutators:
					if replay['result']:
						mutator_total_wins += 1

					mutator_total_games += 1
				else:
					if replay['result']:
						regular_total_wins += 1

					regular_total_games += 1

		return {
			'regular_games':    regular_games,
			'mutator_games':    mutator_games,
			'regular_wins':     regular_wins,
			'mutator_wins':     mutator_wins,
			'regular_win_rate': (regular_total_wins,
			                     regular_total_games - regular_total_wins),
			'mutator_win_rate': (mutator_total_wins,
			                     mutator_total_games - mutator_total_wins)
		}

	def get_selected(self):
		difficulty_selected = self.difficulty_choice.GetSelection()
		enemy_race_selected = self.enemy_race_choice.GetSelection()

		return (
			self.difficulty_choice.GetString(difficulty_selected),
			self.enemy_race_choice.GetString(enemy_race_selected)
		)

	def reload(self):
		self.update()

	def update(self, event=None):
		results = self.count()
		labels = ('Win', 'Loss')

		self.diff_chart.set_data2(
			DIFFICULTIES,
			('Regular Games', 'Mutation Games'),
			results['regular_games'],
			results['mutator_games'],
			title='Total Games Played'
		)
		self.regular_win_chart.set_data(
			labels,
			results['regular_win_rate'],
			title='Regular Games'
		)
		self.mutator_win_chart.set_data(
			labels,
			results['mutator_win_rate'],
			title='Mutator Games'
		)

		self.list_ctrl.DeleteAllItems()

		for n in range(0, len(DIFFICULTIES)):
			regular_wins = results['regular_wins']
			regular_games = results['regular_games']
			regular_losses = regular_games[n] - regular_wins[n]

			mutator_wins = results['mutator_wins']
			mutator_games = results['mutator_games']
			mutator_losses = mutator_games[n] - mutator_wins[n]

			self.list_ctrl.InsertItem(n, DIFFICULTIES[n])
			self.list_ctrl.SetItem(n, 1, str(regular_wins[n]))
			self.list_ctrl.SetItem(n, 2, str(regular_losses))
			self.list_ctrl.SetItem(n, 3, str(mutator_wins[n]))
			self.list_ctrl.SetItem(n, 4, str(mutator_losses))

################################################################################
# TimeTab class                                                                #
################################################################################

class TimeTab(wx.Panel):
	def __init__(self, parent, replays):
		wx.Panel.__init__(self, parent)
		self.replays = replays

		self.month_chart = BarChart(self, (10, 2.5))

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddMany((
			(self.month_chart, 1, wx.ALL | wx.EXPAND, 5),
			(self.create_filter_sizer(), 0, wx.ALL | wx.EXPAND, 5),
			(self.create_data_sizer(), 1, wx.ALL | wx.EXPAND, 5)
		))
		self.SetSizer(sizer)

	def create_filter_sizer(self):
		self.year_choice = wx.Choice(self, choices=())
		self.year_choice.Bind(wx.EVT_CHOICE, self.update)

		self.month_choice = wx.Choice(self, choices=())
		self.month_choice.Bind(wx.EVT_CHOICE, self.update)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(wx.StaticText(self, label='Year:'), 0, wx.CENTER),
			(self.year_choice, 0, wx.ALL, 5),
			(wx.StaticText(self, label='Month:'), 0, wx.CENTER),
			(self.month_choice, 0, wx.ALL, 5)
		))

		return sizer

	def create_data_sizer(self):
		self.day_chart = BarChart(self, (3, 2.5))
		self.hour_chart = LineChart(self, (3, 2.5))

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(self.day_chart, 1, wx.ALL | wx.EXPAND, 5),
			(self.hour_chart, 1, wx.ALL | wx.EXPAND, 5),
			(self.create_info_sizer(), 1, wx.ALL | wx.EXPAND, 5)
		))

		return sizer

	def create_info_sizer(self):
		labels = ('time_played', 'average',
		          'min_win', 'max_win',
		          'min_loss', 'max_loss')
		self.text = {t: wx.StaticText(self, label='') for t in labels}

		sizer = wx.GridSizer(cols=2)
		sizer.AddMany((
			wx.StaticText(self, label='Total time played:'),
			self.text['time_played'],
			wx.StaticText(self, label='Average game length:'),
			self.text['average'],
			wx.StaticText(self, label='Fastest win:'), self.text['min_win'],
			wx.StaticText(self, label='Longest win:'), self.text['max_win'],
			wx.StaticText(self, label='Fastest loss:'), self.text['min_loss'],
			wx.StaticText(self, label='Longest loss:'), self.text['max_loss']
		))

		return sizer

	def count(self):
		year, month = self.get_selected()

		months = [0] * 12
		days = [0] * 7
		hours = [0] * 24
		time_played = 0
		min_win = 0
		max_win = 0
		min_loss = 0
		max_loss = 0
		total = 0

		for replay in self.replays:
			date = replay.get('datetime', 0)

			if not year.startswith('(') and year != str(date.tm_year):
				continue

			month_name = calendar.month_name[date.tm_mon]
			# month count not affected by month filter
			months[date.tm_mon - 1] += 1

			if not month.startswith('(') and month != month_name:
				continue

			days[date.tm_wday] += 1
			hours[date.tm_hour] += 1

			length = replay.get('length', 0)
			time_played += length
			total += 1

			if replay['result']:
				if min_win == 0:
					min_win = length

				min_win = min(min_win, length)
				max_win = max(max_win, length)
			else:
				if min_loss == 0:
					min_loss = length

				min_loss = min(min_loss, length)
				max_loss = max(max_loss, length)

		return {
			'months':      months,
			'days':        days,
			'hours':       hours,
			'time_played': time_played,
			'average':     time_played // total if total > 0 else 0,
			'min_win':     min_win,
			'max_win':     max_win,
			'min_loss':    min_loss,
			'max_loss':    max_loss
		}

	def get_selected(self):
		return (
			self.year_choice.GetString(self.year_choice.GetSelection()),
			self.month_choice.GetString(self.month_choice.GetSelection())
		)

	def set_filter(self):
		years = ['(Any year)']
		months = []

		for replay in self.replays:
			date = replay.get('datetime', 0)
			year = str(date.tm_year)
			month = date.tm_mon

			if not year in years:
				years.append(year)

			if not month in months:
				months.append(month)

		self.year_choice.SetItems(sorted(years))
		self.year_choice.SetSelection(0)

		choices = ['(Any month)']
		choices.extend([calendar.month_name[m] for m in sorted(months)])

		self.month_choice.SetItems(choices)
		self.month_choice.SetSelection(0)

	def reload(self):
		self.set_filter()
		self.update()

	def update(self, event=None):
		results = self.count()

		months = [calendar.month_abbr[m]
		          for m in range(1, len(results['months']) + 1)]
		days = [calendar.day_abbr[d] for d in range(0, len(results['days']))]

		# values must be unique
		hours = ['Midnight']
		hours.extend([str(h) + ' AM' for h in range(1, 12)])
		hours.append('Noon')
		hours.extend([str(h) + ' PM' for h in range(1, 12)])

		self.month_chart.set_data(months, results['months'], title='Month')
		self.day_chart.set_data(days, results['days'], title='Day of the Week')
		self.hour_chart.set_data(hours, results['hours'], title='Time of Day')

		self.text['time_played'].SetLabel(format_time(results['time_played']))
		self.text['average'].SetLabel(format_time(results['average']))
		self.text['min_win'].SetLabel(format_time(results['min_win']))
		self.text['max_win'].SetLabel(format_time(results['max_win']))
		self.text['min_loss'].SetLabel(format_time(results['min_loss']))
		self.text['max_loss'].SetLabel(format_time(results['max_loss']))

################################################################################
# ApmTab class                                                                 #
################################################################################

class ApmTab(wx.Panel):
	def __init__(self, parent, replays):
		wx.Panel.__init__(self, parent)
		self.replays = replays

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddMany((
			(self.create_filter_sizer(), 0, wx.ALL | wx.EXPAND, 5),
			(self.create_chart_sizer(), 1, wx.ALL | wx.EXPAND, 5)
		))
		self.SetSizer(sizer)

	def create_filter_sizer(self):
		self.player_choice = wx.Choice(self, choices=())
		self.player_choice.Bind(wx.EVT_CHOICE, self.update)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(wx.StaticText(self, label='Player:'), 0, wx.CENTER),
			(self.player_choice, 0, wx.ALL, 5)
		))

		return sizer

	def create_chart_sizer(self):
		self.chart = BarChart(self, (7, 5.25))

		self.list_ctrl = self.create_list_ctrl()

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddMany((
			(self.chart, 3, wx.ALL | wx.EXPAND, 5),
			(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 5)
		))

		return sizer

	def create_list_ctrl(self):
		element = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

		element.InsertColumn(0, 'Item', width=200)
		element.InsertColumn(1, 'APM', width=50)

		return element

	def filter(self, filter_=True):
		name = self.get_selected()

		for replay in self.replays:
			players = replay.get('players', ())

			if len(players) < 2:
				continue

			for n in range(0, 2):
				any_player = name.startswith('(')

				# only counts for all players or selected player
				if any_player or name == format_name(players[n]['name']):
					yield n, replay

					# stops looking after finding player
					# unless looking for all players
					if not any_player:
						break

	def count(self):
		items = {}
		total = {}

		for n, replay in self.filter(filter_=True):
			commander = replay['players'][n]['commander']
			apm = replay['players'][n]['apm']

			items[commander] = items.get(commander, 0) + apm
			total[commander] = total.get(commander, 0) + 1

		return items, total

	def get_selected(self):
		return self.player_choice.GetString(self.player_choice.GetSelection())

	def reload(self):
		self.set_players()
		self.update()

	def set_players(self):
		choices = {'(Any player)': 2}

		for replay in self.replays:
			players = replay.get('players', ())

			if len(players) < 2:
				continue

			for n in range(0, 2):
				name = format_name(players[n]['name'])
				choices[name] = choices.get(name, 0) + 1

		# filters only players with more than one game saved
		choices = {k: v for k, v in choices.items() if v > 1}
		self.player_choice.SetItems(sorted(choices.keys(), key=str.casefold))

		# selects player with most games by default
		most_played = max(choices.keys(), key=lambda k: choices[k])
		index = self.player_choice.FindString(most_played)
		self.player_choice.SetSelection(index)

	def update(self, event=None):
		items, total = self.count()
		# total values are always greater than 0
		data = {k: int(items[k] / total[k]) for k in items.keys()}
		avg = sum(items.values()) / sum(total.values()) if len(total) > 0 else 0

		if len(data) > 0: # parallel sorts keys and values by values
			zipped = sorted(zip(data.values(), data.keys()))
			values, labels = zip(*zipped)
		else:
			values = ()
			labels = ()

		self.chart.set_datah(labels, values, mean=avg, title='APM by Commander')

		self.list_ctrl.DeleteAllItems()
		length = len(values)

		for n in range(0, length):
			# iterates through lists in reverse (largest values first)
			item = labels[length - n - 1]

			self.list_ctrl.InsertItem(n, item)
			self.list_ctrl.SetItem(n, 1, str(data[item]))

################################################################################
# SubFrame class                                                               #
################################################################################

class SubFrame(wx.Frame):
	def __init__(self, parent, panel, title):
		wx.Frame.__init__(self, parent, title=title, size=SUB_FRAME_SIZE)
		self.panel = panel(self)

	def close(self, event=None):
		self.Destroy()

################################################################################
# SubPanel class                                                               #
################################################################################

class SubPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

		self.list_ctrl = self.create_list_ctrl()
		self.info_sizer = self.create_info_sizer()

		info_sizer_flags = wx.ALL | wx.EXPAND | wx.RESERVE_SPACE_EVEN_IF_HIDDEN

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.AddMany((
			(self.list_ctrl, 3, wx.ALL | wx.EXPAND, 5),
			(self.info_sizer, 1, info_sizer_flags, 5),
			(self.create_button_sizer(parent), 0, wx.EXPAND, 5)
		))
		self.sizer.Hide(self.info_sizer)
		self.SetSizer(self.sizer)

		self.reload()

	def create_button_sizer(self, parent):
		button_close = wx.Button(self, label='&Close')
		button_close.Bind(wx.EVT_BUTTON, parent.close)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.AddStretchSpacer()
		sizer.Add(button_close, 0, wx.ALL, 5)

		return sizer

	def read_item(self, m, n):
		return self.list_ctrl.GetItem(m, n).GetText()

	def list_selected(self, event=None):
		self.sizer.Show(self.info_sizer)
		self.update()

	def list_deselected(self, event=None):
		self.sizer.Hide(self.info_sizer)

################################################################################
# ErrorPanel class                                                             #
################################################################################

class ErrorPanel(SubPanel):
	def __init__(self, parent):
		SubPanel.__init__(self, parent)

	def create_list_ctrl(self):
		element = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

		element.InsertColumn(0, 'File', width=200)
		element.InsertColumn(1, 'Date', width=200)
		element.InsertColumn(2, 'Error', width=250)

		element.Bind(wx.EVT_LIST_ITEM_SELECTED, self.list_selected)
		element.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.list_deselected)

		return element

	def create_info_sizer(self):
		self.text = {}
		self.text['file'] = wx.TextCtrl(self, size=(600, -1))
		self.text['datetime'] = wx.StaticText(self, label='')
		self.text['error'] = wx.StaticText(self, label='')

		sizer = wx.FlexGridSizer(cols=2, gap=(5, 5))
		sizer.AddMany((
			wx.StaticText(self, label='File:'), self.text['file'],
			wx.StaticText(self, label='Date:'), self.text['datetime'],
			wx.StaticText(self, label='Error:'), self.text['error']
		))
		sizer.AddGrowableCol(1, proportion=1)

		return sizer

	def update(self):
		selected = self.list_ctrl.GetNextSelected(-1)

		if selected < 0:
			return

		self.text['file'].SetValue(errors[selected][0])
		self.text['datetime'].SetLabel(self.read_item(selected, 2))
		self.text['error'].SetLabel(self.read_item(selected, 1))

		self.info_sizer.Layout() # reflows layout

	def reload(self):
		for i, error in enumerate(reversed(errors)):
			self.list_ctrl.InsertItem(i, os.path.basename(error[0]))
			self.list_ctrl.SetItem(i, 1, format_date(error[2]))
			self.list_ctrl.SetItem(i, 2, str(error[1]))

################################################################################
# MessagePanel class                                                           #
################################################################################

class MessagePanel(SubPanel):
	def __init__(self, parent):
		SubPanel.__init__(self, parent)

	def create_list_ctrl(self):
		element = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

		element.InsertColumn(0, 'Time', width=60)
		element.InsertColumn(1, 'Player', width=200)
		element.InsertColumn(2, 'Message', width=390)

		element.Bind(wx.EVT_LIST_ITEM_SELECTED, self.list_selected)
		element.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.list_deselected)

		return element

	def create_info_sizer(self):
		self.text = {}
		self.text['time'] = wx.StaticText(self, label='')
		self.text['player'] = wx.StaticText(self, label='')
		self.text['message'] = wx.TextCtrl(self, size=(600, -1))

		sizer = wx.FlexGridSizer(cols=2, gap=(5, 5))
		sizer.AddMany((
			wx.StaticText(self, label='Time:'), self.text['time'],
			wx.StaticText(self, label='Player:'), self.text['player'],
			wx.StaticText(self, label='Message:'), self.text['message']
		))
		sizer.AddGrowableCol(1, proportion=1)

		return sizer

	def update(self):
		selected = self.list_ctrl.GetNextSelected(-1)

		if selected < 0:
			return

		self.text['time'].SetLabel(self.read_item(selected, 0))
		self.text['player'].SetLabel(self.read_item(selected, 1))
		self.text['message'].SetValue(self.read_item(selected, 2))

		self.info_sizer.Layout() # reflows layout

	def reload(self):
		if not hasattr(self, 'messages'):
			return

		for i, message in enumerate(self.messages):
			self.list_ctrl.InsertItem(i, format_time(message['time']))
			self.list_ctrl.SetItem(i, 1, format_name(message['name']))
			self.list_ctrl.SetItem(i, 2, message['message'])

	def set_messages(self, messages):
		self.messages = messages
		self.reload()

################################################################################
# PieChart class                                                               #
################################################################################

class PieChart(wx.Panel):
	def __init__(self, parent, size):
		wx.Panel.__init__(self, parent)
		self.size = size

	def set_data(self, labels, values, title=''):
		self.figure = Figure(figsize=self.size)

		ax = self.figure.add_subplot(1, 1, 1, frame_on=False)
		wedges = ax.pie(values, labels=labels, autopct='%1.1f%%')
		ax.axis('equal') # makes circular

		if title != '':
			ax.set_title(title)

		for wedge in wedges[0]:
			label = wedge.get_label()
			wedge.set_edgecolor('white')

			if label in COMMANDERS: # sets wedge to faction color (if commander)
				wedge.set_facecolor(COMMANDERS[label])

		self.canvas = FigureCanvas(self, -1, self.figure)

################################################################################
# BarChart class                                                               #
################################################################################

class BarChart(wx.Panel):
	def __init__(self, parent, size):
		wx.Panel.__init__(self, parent)
		self.size = size

	def set_data(self, labels, values, title=''): # one bar per tick
		self.figure = Figure(figsize=self.size)

		ax = self.figure.add_subplot(1, 1, 1)
		ax.bar(labels, values)

		if title != '':
			ax.set_title(title)

		self.canvas = FigureCanvas(self, -1, self.figure)

	def set_data2(self, labels, legend, values1, values2, title=''): # two bars
		self.figure = Figure(figsize=self.size)

		width = 0.5
		x = range(0, len(values1))

		ax = self.figure.add_subplot(1, 1, 1)
		ax.bar(x, values1, width=width, label=legend[0])
		ax.bar([w + width for w in x], values2, width=width, label=legend[1])
		ax.set_xticks([w + width / 2 for w in x])
		ax.set_xticklabels(labels)
		ax.legend()

		if title != '':
			ax.set_title(title)

		self.canvas = FigureCanvas(self, -1, self.figure)

	def set_datah(self, labels, values, mean=0, title=''): # horizontal
		self.figure = Figure(figsize=self.size)

		ax = self.figure.add_subplot(1, 1, 1)
		ax.barh(labels, values)

		if title != '':
			ax.set_title(title)

		if mean > 0:
			ax.axvline(mean, color='yellowgreen')
			ax.text(mean + 0.1, 0, 'Average', rotation=270)

		self.canvas = FigureCanvas(self, -1, self.figure)

################################################################################
# LineChart class                                                              #
################################################################################

class LineChart(wx.Panel):
	def __init__(self, parent, size):
		wx.Panel.__init__(self, parent)
		self.size = size

	def set_data(self, labels, values, title=''):
		self.figure = Figure(figsize=self.size)

		ax = self.figure.add_subplot(1, 1, 1)
		ax.plot(labels, values)

		if len(values) > 12:
			for i, label in enumerate(ax.xaxis.get_ticklabels()):
				if i % 6 != 0: # only shows every 6 ticks
					label.set_visible(False)

		if title != '':
			ax.set_title(title)

		self.canvas = FigureCanvas(self, -1, self.figure)

################################################################################
# Replay class                                                                 #
################################################################################

class Replays():
	def __init__(self, parent):
		self.parent = parent

		self.path = ''
		self.list = []

	def __getitem__(self, i):
		return self.list[i]

	def __len__(self):
		return len(self.list)

	def reload(self, path):
		try:
			if self.path == path and len(self.list) > 0: # old data exists
				files_to_add, files_to_remove = self.get_changed_files(path)
				self.remove_files(files_to_remove)
			else:
				self.path = path
				self.list.clear()

				files_to_add = self.get_all_files(path)
		except Exception as e:
			errors.append((path, e, time.localtime()))
			return

		self.add_files(files_to_add)

		# sends event to the UI after all changes complete
		wx.PostEvent(self.parent, ResultEvent(0, 0, complete=True))

	def get_all_files(self, path):
		return [f for f in os.listdir(path) if f.endswith(FILE_EXTENSION)]

	def get_changed_files(self, path):
		files_to_add = []
		files_to_remove = []
		unchanged_files = []

		for replay in self.list:
			filepath = replay['filepath']
			filename = replay['filename']

			if not os.path.exists(filepath): # file no longer exists
				files_to_remove.append(filename)
			elif os.path.getmtime(filepath) != replay['fstime']: # file changed
				files_to_add.append(filename)
				files_to_remove.append(filename)
			else:
				unchanged_files.append(filename)

		for filename in self.get_all_files(path):
			if filename not in unchanged_files: # new file
				files_to_add.append(filename)

		return files_to_add, files_to_remove

	def add_files(self, files):
		index = 0
		total = len(files)

		if total == 0:
			return

		for replay in self.read_replay(files):
			if replay is None:
				continue

			# skips games that are too short
			if replay.get('length', 0) < MINIMUM_LENGTH:
				continue

			self.list.append(replay)

			# sends event to the UI after each item
			# total is not necessarily accurate since some replays are skipped
			wx.PostEvent(self.parent, ResultEvent(index, total, complete=False))
			index += 1

		# sorts with most recent games first
		self.list.sort(key=lambda k: k['datetime'], reverse=True)

	def read_replay(self, files):
		for filename in files:
			filepath = os.path.join(self.path, filename)

			try:
				archive = MPQArchive(filepath)
				meta = json.loads(archive.read_file('replay.gamemetadata.json'))

				replay = sc2reader.load_replay(filepath, load_level=2)
				init_data = replay.raw_data['replay.initData']
				message_events = replay.raw_data['replay.message.events']
			except Exception as e:
				errors.append((filepath, e, time.localtime()))
				continue

			# skips multiplayer/custom games
			if len(replay.players) < 4 \
			or replay.players[0].commander == '' \
			or replay.players[1].commander == '':
				continue

			players = []
			messages = []
			mutators = False
			result = False

			mutators |= init_data['game_description']['has_extension_mod']

			for n in range(0, 2):
				player = replay.players[n]
				enemy = replay.players[n + 2]

				slot = player.slot_data

				# must check these keys, not always present on older games
				brutal_plus = slot.get('brutal_plus_difficulty', 0) or 0
				mastery_level = slot.get('commander_mastery_level', 0) or 0
				masteries = slot.get('commander_mastery_talents', ()) or ()
				prestige = slot.get('selected_commander_prestige', 0) or 0

				# need to check for Brutal+ games separately because they do not
				# use extension mods like mutation and custom games do
				mutators |= brutal_plus
				# victory if either human player wins
				result |= player.result == 'Win'

				players.append({
					'name':          player.name,
					'race':          player.play_race,
					'commander':     player.commander,
					'level':         player.commander_level,
					'mastery_level': mastery_level,
					'prestige':      prestige,
					'difficulty':    enemy.slot_data['difficulty'],
					'brutal_plus':   brutal_plus,
					'mastery':       masteries,
					'apm':           int(meta['Players'][n]['APM'])
				})

			for message in message_events['messages']:
				messages.append({
					'time':    message.frame // GAME_LOOPS_PER_SECOND,
					'name':    replay.players[message.pid].name,
					'message': message.text
				})

			yield {
				'filepath':   filepath,
				'filename':   os.path.basename(filepath),
				'fstime':     os.path.getmtime(filepath),
				'datetime':   time.localtime(replay.unix_timestamp),
				'version':    replay.release_string,
				'region':     replay.region.upper(),
				'length':     replay.frames // GAME_LOOPS_PER_SECOND,
				'speed':      replay.speed,
				'map':        replay.map_name,
				'enemy_race': replay.players[2].play_race,
				'players':    players,
				'mutators':   mutators,
				'result':     result,
				'messages':   messages
			}

	def remove_replay(self, replay):
		self.list.remove(replay)

	def remove_files(self, files):
		if len(files) == 0:
			return

		list_ = []

		for replay in self.list:
			if replay['filename'] not in files:
				list_.append(replay)

		self.list = list_

################################################################################
# ResultEvent class                                                            #
################################################################################

class ResultEvent(wx.PyEvent):
	def __init__(self, index, total, complete=False):
		wx.PyEvent.__init__(self)
		self.index = index
		self.total = total
		self.complete = complete

		self.SetEventType(EVT_RESULT_ID)

################################################################################
# Format functions                                                             #
################################################################################

def format_date(timestamp):
	formatted = ''

	if timestamp is not None:
		if os.name == 'nt': # Windows
			formatted = time.strftime('%b %#d, %Y at %#I:%M:%S %p', timestamp)
		else:
			formatted = time.strftime('%b %-d, %Y at %-I:%M:%S %p', timestamp)

	return formatted

def format_time(length):
	if length >= 60 * 60 * 24:
		d = length // (60 * 60 * 24)
		r = length % (60 * 60 * 24)

		h = r // (60 * 60)
		r = r % (60 * 60)

		m = r // 60
		s = r % 60

		formatted = '{:d} days, {:d}:{:02d}:{:02d}'.format(d, h, m, s)
	elif length >= 60 * 60:
		h = length // (60 * 60)
		r = length % (60 * 60)

		m = r // 60
		s = r % 60

		formatted = '{:d}:{:02d}:{:02d}'.format(h, m, s)
	else:
		formatted = '{:02d}:{:02d}'.format(length // 60, length % 60)

	return formatted

def format_percentage(num):
	return '{:.1f}%'.format(num * 100)

def format_name(name):
	name = name.replace('&lt;', '<')
	name = name.replace('&gt;', '>')
	name = name.replace('<sp/>', ' ')

	return name

def format_player(name, commander):
	return '{} ({})'.format(format_name(name), commander)

def format_level(level, mastery_level):
	if mastery_level == 0:
		formatted = str(level)
	elif mastery_level <= 90:
		formatted = '{:d} (Mastery)'.format(mastery_level)
	else:
		formatted = '{:d} (Ascension)'.format(mastery_level)

	return formatted

def format_prestige(commander, prestige):
	if prestige == 0:
		formatted = 'None'
	elif commander not in PRESTIGES:
		formatted = 'Unknown'
	else:
		formatted = PRESTIGES[commander][prestige]

	return formatted

def format_difficulty(difficulty, brutal_plus):
	if difficulty == 1:
		formatted = 'Casual'
	elif difficulty == 2:
		formatted = 'Normal'
	elif difficulty == 3:
		formatted = 'Hard'
	elif difficulty == 4:
		if brutal_plus > 0:
			formatted = 'Brutal+{:d}'.format(brutal_plus)
		else:
			formatted = 'Brutal'
	else:
		formatted = str(difficulty)

	return formatted

def format_region(region):
	return sc2reader.constants.GATEWAY_CODES.get(region, 'Unknown')

def format_boolean(value):
	return 'Yes' if value else 'No'

def format_result(result):
	return 'Victory' if result else 'Defeat'

################################################################################
# Main function                                                                #
################################################################################

def main():
	app = wx.App(False)

	frame = MainFrame()
	frame.Show()
	frame.Center()

	app.MainLoop()

if __name__ == '__main__':
	errors = []

	main()