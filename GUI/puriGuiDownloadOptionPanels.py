import puriGuiCommon
import puriDataStructures
import wx

class pixivTagDownloadOptionPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, 'Pixiv Search Options')
		
		# Start Date Text
		self.startDateText = wx.StaticText(self, -1, label='Start Date:')
		self.grid.Add(self.startDateText, pos=(0, 0), span=(1, 1), flag=wx.ALIGN_LEFT)

		# Start Date TextCtrl
		self.startDateTextCtrl = wx.TextCtrl(self, -1)
		self.grid.Add(self.startDateTextCtrl, pos=(0, 1), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT)

		# End Date Text
		self.endDateText = wx.StaticText(self, -1, label='End Date:')
		self.grid.Add(self.endDateText, pos=(1, 0), span=(1, 1), flag=wx.ALIGN_LEFT)

		# End TextCtrl
		self.endDateTextCtrl = wx.TextCtrl(self, -1)
		self.grid.Add(self.endDateTextCtrl, pos=(1, 1), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT)

		# Search Order
		choices = ['Oldest First', 'Oldest Last', 'Popular First']
		self.searchOrderComboBox = wx.ComboBox(self, choices=choices, style=wx.CB_READONLY)
		self.searchOrderComboBox.SetStringSelection(choices[0])
		self.grid.Add(self.searchOrderComboBox, pos=(2, 0), span=(1, 2), flag=wx.EXPAND|wx.ALIGN_LEFT)

		# r18 toggle
		self.r18Toggle = wx.CheckBox(self, wx.ID_ANY, 'r18 Only')
		self.r18Toggle.SetValue(False)
		self.grid.Add(self.r18Toggle, pos=(3, 0), span=(1, 1), flag=wx.ALIGN_LEFT)

		self.refreshPanel()

	def getSearchOptions(self):
		searchOptions = puriDataStructures.puriDownloadOptions('Pixiv Tags')
		searchOptions.startDate = self.startDateTextCtrl.GetValue()
		searchOptions.endDate = self.endDateTextCtrl.GetValue()
		searchOptions.searchOrder = self.searchOrderComboBox.GetValue()
		r18Only = self.r18Toggle.GetValue()
		if r18Only == False:
			self.rating = 'safe'
		else:
			self.rating = 'explict'
		return searchOptions
