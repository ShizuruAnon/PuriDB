import wx
import sys
import os

sys.path.insert(0, './../backend')
import puriDatabase
import puriCommunication
import puriEvents
import puriGuiCommon
from puriGuiImageScrollPanel import puriImageScrollPanel
from puriGuiImageScrollPanel import puriImageInfoPanel

class searchStartPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, 'Search Start/Info')

		self.numImagesFound = 0

		self.imagesFoundTextCtrl = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
		self.imagesFoundTextCtrl.SetValue('Images Found: ' + str(self.numImagesFound))
		self.Bind(puriEvents.EVT_setImagesFound, self.setImagesFound)
		self.grid.Add(self.imagesFoundTextCtrl, pos=(0, 0), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT)

		# Start Search
		self.startSearchButton = wx.Button(self, label='Start Search')
		self.grid.Add(self.startSearchButton, pos=(1, 0), span=(1, 1), flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM, border=0)
		self.startSearchButton.Bind(wx.EVT_BUTTON, self.onStartSearchButtonPress)

		self.grid.AddGrowableCol(0)

		self.refreshPanel()

	def setImagesFound(self, event):
		self.numImagesFound = event.getValue()
		self.imagesFoundTextCtrl.SetValue('Images Found: ' + str(self.numImagesFound))
		self.refreshPanel()

	def onStartSearchButtonPress(self, event):
		tags = self.parent.tagBoxPanel.getSearchTags()
		if len(tags) > 0:
			comm = puriCommunication.get_communications()
			self.parent.parent.imageScrollPanel.clearImages()
			comm.guiToDatabase.send_message('database-localImageSearchByTags', (tags, self.parent))
			self.parent.Bind(puriEvents.EVT_addImageToScroll, self.parent.parent.imageScrollPanel.onAddImageToScrollEvent)


class searchMenuPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent, parentSplitter):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, '', parentSplitter)

		# Setup the searchOptions combobox
		choices = ['Local Image Search']
		self.searchOptions = wx.ComboBox(self, choices=choices, style=wx.CB_READONLY, name='searchOptions')
		self.searchOptions.SetStringSelection(choices[0])
		self.grid.Add(self.searchOptions, pos=(0, 0), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_CENTER|wx.ALIGN_TOP|wx.ALIGN_BOTTOM, border=15)

		# Bind Buttons
		#self.Bind(wx.EVT_TEXT, self.setSearchMenuOptions, self.searchOptions)
		
		self.setSearchMenuOptions()

		# Add growable rows
		self.grid.AddGrowableCol(0)

		self.SetMinSize((220, 320))
		self.refreshPanel()

	def setSearchMenuOptions(self, event=None):

		# Remove the current one if it on it
		'''
		if self.searchMenuItem != None:
			children = self.searchMenuGrid.GetChildren()
			for i in range(0, len(children)):
				if children[i] == self.searchMenuItem:
					self.searchMenuGrid.Hide(i)
					self.searchMenuGrid.Remove(i)
		'''

		# Add the new one to the grid
		currentSearch = self.searchOptions.GetValue()
		if currentSearch == 'Local Image Search':
			self.startPanel = searchStartPanel(self)
			self.grid.Add(self.startPanel, pos=(1, 0), span=(1, 1), flag=wx.EXPAND)
			self.tagBoxPanel = puriGuiCommon.searchTagBox(self)
			self.grid.Add(self.tagBoxPanel, pos=(2, 0), span=(1, 1), flag=wx.EXPAND)

class puriImageSearchPanel(wx.SplitterWindow):
	def __init__(self, parent, *args, **kwargs):
		self.parent = parent
		super(puriImageSearchPanel, self).__init__(parent=parent, *args, **kwargs)

		# Left panel
		self.leftPanelSplitter = wx.SplitterWindow(self)
		self.searchMenuPanel = searchMenuPanel(self, self.leftPanelSplitter)
		self.imageInfoPanel = puriImageInfoPanel(self, self.leftPanelSplitter)
		self.leftPanelSplitter.SplitHorizontally(self.searchMenuPanel, self.imageInfoPanel)

		# Right panel
		self.imageScrollPanel = puriImageScrollPanel(self, style=wx.SIMPLE_BORDER)
		self.SplitVertically(self.leftPanelSplitter, self.imageScrollPanel)

		self.SetMinimumPaneSize(220)
