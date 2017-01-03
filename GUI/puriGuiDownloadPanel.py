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
import puriGuiDownloadOptionPanels
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
		searchOptions = self.parent.downloadOptionPanel.getSearchOptions()
		searchOptions.tags = self.parent.searchTagsPanel.getSearchTags()
		comm = puriCommunication.get_communications()
		
		if (searchOptions.website  == 'Pixiv Tags') and (len(searchOptions.tags) > 0):
			comm.guiToDownloader.send_message('downloader-tag_search', (searchOptions, self))
		elif (searchOptions.website == 'Pixiv Artist') and (searchOptions.artistId != ''):
			print 'artist Search'

class downloadMenuPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent, parentSplitter):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, '', parentSplitter)

		# Start/Download Progress Panel
		self.startPanel = searchStartPanel(self)
		self.grid.Add(self.startPanel, pos=(0, 0), span=(1, 1), flag=wx.EXPAND|wx.TOP)

		# Setup the downloadType combobox
		choices = ['Pixiv Tags', 'Pixiv Artist']
		self.downloadType = wx.ComboBox(self, choices=choices, style=wx.CB_READONLY)
		self.downloadType.SetStringSelection(choices[0])
		self.lastDownloadType = ''
		self.grid.Add(self.downloadType, pos=(1, 0), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_TOP, border=0)

		# Bind Buttons
		# TODO
		self.Bind(wx.EVT_TEXT, self.setMenu, self.downloadType)

		self.setMenu()
		self.grid.AddGrowableCol(0)
		self.SetMinSize((220, 380))
		self.refreshPanel()


	def setMenu(self, event=None):
		# Add the new one to the grid
		currentDownloadType = self.downloadType.GetValue()
		if currentDownloadType != self.lastDownloadType:
			self.lastDownloadType = currentDownloadType
			if len(self.grid.GetChildren()) == 4:
				self.grid.Hide(2)
				self.grid.Hide(3)
				self.grid.Remove(3)
				self.grid.Remove(2)

			if currentDownloadType == 'Pixiv Tags':
				self.searchTagsPanel = puriGuiCommon.searchTagBox(self, size=(150, 120))
				self.stp = self.grid.Add(self.searchTagsPanel, pos=(2, 0), span=(1, 1), flag=wx.EXPAND)
				self.downloadOptionPanel = puriGuiDownloadOptionPanels.pixivTagDownloadOptionPanel(self)
				self.dop = self.grid.Add(self.downloadOptionPanel, pos=(3, 0), span=(1, 1), flag=wx.EXPAND)

			self.refreshPanel()
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
