# -*- coding: utf-8 -*-
import wx
import sys

# Import from the backend
sys.path.insert(0, './../backend')
import puriDownloader
import puriDataStructures
import puriCommunication
import puriEvents
import puriGuiCommon
from puriGuiImageScrollPanel import puriImageScrollPanel
from puriGuiImageScrollPanel import puriImageInfoPanel

class searchStartPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, 'Search Start/Info')

		self.numImagesFound = 0
		self.numImagesDownloaded = 0

		self.imagesFoundTextCtrl = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
		self.imagesFoundTextCtrl.SetValue('Images Found: ' + str(self.numImagesFound))
		self.Bind(puriEvents.EVT_setImagesFound, self.setImagesFound)
		self.grid.Add(self.imagesFoundTextCtrl, pos=(0, 0), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT)

		self.imagesDownloadedTextCtrl = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
		self.imagesDownloadedTextCtrl.SetValue('Images Downloaded: ' + str(self.numImagesDownloaded))
		self.Bind(puriEvents.EVT_setImagesDownloaded, self.setImagesDownloaded)
		self.grid.Add(self.imagesDownloadedTextCtrl, pos=(1, 0), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT)

		# Start Search
		self.startSearchButton = wx.Button(self, label='Start Search')
		self.grid.Add(self.startSearchButton, pos=(2, 0), span=(1, 1), flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM, border=0)
		self.startSearchButton.Bind(wx.EVT_BUTTON, self.onStartSearchButtonPress)

		self.grid.AddGrowableCol(0)

		self.refreshPanel()

	def setImagesFound(self, event):
		self.numImagesFound = event.getValue()
		self.imagesFoundTextCtrl.SetValue('Images Found: ' + str(self.numImagesFound))
		self.refreshPanel()

	def setImagesDownloaded(self, event):
		self.numImagesDownloaded = event.getValue()
		self.imagesDownloadedTextCtrl.SetValue('Images Downloaded: ' + str(self.numImagesDownloaded))
		self.refreshPanel()

	def onStartSearchButtonPress(self, event):
		searchOptions = self.parent.dlOptionsPanel.getOptions()
		searchOptions.tags = self.parent.tagBoxPanel.getSearchTags()
		
		if len(searchOptions.tags) > 0:
			# Search for tags
			comm = puriCommunication.get_communications()
			comm.guiToDownloader.send_message('downloader-tag_search', (searchOptions, self))

class searchOptionsPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, 'Search Options')
		
		# Artist Id Text
		self.artistIdText = wx.StaticText(self, -1, label='Artist Id:')
		self.grid.Add(self.artistIdText, pos=(0, 0), span=(1, 1), flag=wx.ALIGN_LEFT)

		# Artist Id TextCtrl
		self.artistIdTextCtrl = wx.TextCtrl(self, -1)
		self.grid.Add(self.artistIdTextCtrl, pos=(0, 1), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT)
	
		# Start Date Text
		self.startDateText = wx.StaticText(self, -1, label='Start Date:')
		self.grid.Add(self.startDateText, pos=(1, 0), span=(1, 1), flag=wx.ALIGN_LEFT)

		# Start Date TextCtrl
		self.startDateTextCtrl = wx.TextCtrl(self, -1)
		self.grid.Add(self.startDateTextCtrl, pos=(1, 1), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT)

		# End Date Text
		self.endDateText = wx.StaticText(self, -1, label='End Date:')
		self.grid.Add(self.endDateText, pos=(2, 0), span=(1, 1), flag=wx.ALIGN_LEFT)

		# End TextCtrl
		self.endDateTextCtrl = wx.TextCtrl(self, -1)
		self.grid.Add(self.endDateTextCtrl, pos=(2, 1), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT)

		# r18 toggle
		self.r18Toggle = wx.CheckBox(self, wx.ID_ANY, 'r18 Only')
		self.r18Toggle.SetValue(False)
		self.grid.Add(self.r18Toggle, pos=(3, 0), span=(1, 1), flag=wx.ALIGN_LEFT)

		# Oldest First
		self.oldestFirstToggle = wx.CheckBox(self, wx.ID_ANY, 'Oldest First')
		self.oldestFirstToggle.SetValue(False)
		self.grid.Add(self.oldestFirstToggle, pos=(3, 1), span=(1, 1), flag=wx.ALIGN_RIGHT)

		self.refreshPanel()

	def getOptions(self):
		searchOptions = puriDataStructures.pixivSearchOptions()
		searchOptions.memberId = self.artistIdTextCtrl.GetValue()
		searchOptions.oldestFirst = self.oldestFirstToggle.GetValue()
		searchOptions.r18Mode = self.r18Toggle.GetValue()
		searchOptions.startDate = self.startDateTextCtrl.GetValue()
		searchOptions.endDate = self.endDateTextCtrl.GetValue()
		return searchOptions


class downloadMenuPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent, parentSplitter):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, '', parentSplitter)

		# Setup the downloadOptions combobox
		choices = ['Pixiv']
		#choices = ['Pixiv Download by Tags','Pixiv Download by Artist']
		self.downloadOptions = wx.ComboBox(self, choices=choices, style=wx.CB_READONLY)
		self.downloadOptions.SetStringSelection(choices[0])
		self.grid.Add(self.downloadOptions, pos=(0, 0), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_TOP, border=0)

		# Bind Buttons
		# TODO
		#self.Bind(wx.EVT_TEXT, self.setMenu, self.downloadOptions)

		self.setMenu()
		self.grid.AddGrowableCol(0)
		self.SetMinSize((220, 380))
		self.refreshPanel()


	def setMenu(self, event=None):

		'''children = self.grid.GetChildren()
		for i in range(1, len(children)):
			if children[i] != self.dlMenuItem:
				self.grid.Hide(i)
				self.grid.Remove(i)
		'''

		# Add the new one to the grid
		currentDl = self.downloadOptions.GetValue()
		if currentDl == 'Pixiv':
			self.startPanel = searchStartPanel(self)
			self.grid.Add(self.startPanel, pos=(1, 0), span=(1, 1), flag=wx.EXPAND|wx.TOP)
			self.tagBoxPanel = puriGuiCommon.searchTagBox(self)
			self.grid.Add(self.tagBoxPanel, pos=(2, 0), span=(1, 1), flag=wx.EXPAND)
			self.dlOptionsPanel = searchOptionsPanel(self)
			self.grid.Add(self.dlOptionsPanel, pos=(3, 0), span=(1, 1), flag=wx.EXPAND)

class puriDownloadPanel(wx.SplitterWindow):
	def __init__(self, parent, *args, **kwargs):
		self.parent = parent
		super(puriDownloadPanel, self).__init__(parent=parent, *args, **kwargs)

		self.leftPanelSplitter = wx.SplitterWindow(self)
		self.downloadMenuPanel = downloadMenuPanel(self, self.leftPanelSplitter)
		self.imageInfoPanel = puriImageInfoPanel(self, self.leftPanelSplitter)
		self.leftPanelSplitter.SplitHorizontally(self.downloadMenuPanel, self.imageInfoPanel)

		self.imageScrollPanel = puriImageScrollPanel(self, style=wx.SIMPLE_BORDER)
		self.SplitVertically(self.leftPanelSplitter, self.imageScrollPanel)
		self.SetMinimumPaneSize(220)

		#sizer = wx.BoxSizer(wx.VERTICAL)
		#sizer.add(splitter, 1, wx.EXPAND)
		#parent.SetSizer(sizer)
