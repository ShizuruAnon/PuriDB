import wx
import puriGuiCommon
import puriCommunication
import puriEvents
import sys

class tagFamilyInfoPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, 'Tag Family Info')

		self.tagListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT|wx.LC_HRULES)
		self.tagListCtrl.InsertColumn(0, 'Child Attribute', width=100)
		self.tagListCtrl.InsertColumn(1, 'Child Value', width=200)
		self.tagListCtrl.InsertColumn(2, 'Parent Attribute', width=100)
		self.tagListCtrl.InsertColumn(3, 'Parent Value', width=200)
		self.grid.Add(self.tagListCtrl, pos=(0, 0), span=(1, 4), flag=wx.EXPAND|wx.ALIGN_LEFT, border=0)
		
		self.childTagBox = puriGuiCommon.searchTagBox(self, 'New Child Tags')
		self.grid.Add(self.childTagBox, pos=(1, 0), span=(1, 2), flag=wx.EXPAND|wx.ALIGN_LEFT, border=0)
		self.parentTagBox = puriGuiCommon.searchTagBox(self, 'New Parent Tags')
		self.grid.Add(self.parentTagBox, pos=(1, 2), span=(1, 2), flag=wx.EXPAND|wx.ALIGN_LEFT, border=0)
		
		# Add Tag Relationships
		self.addTagRelationshipsButton = wx.Button(self, label='Add Tag Relationships', size=(150, 25))
		self.grid.Add(self.addTagRelationshipsButton, pos=(2, 0), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.addTagRelationshipsButton.Bind(wx.EVT_BUTTON, self.addTagRelationshipsToListBoxs)
		
		# Clear Table
		self.clearTableButton = wx.Button(self, label='Clear Table', size=(150, 25))
		self.grid.Add(self.clearTableButton, pos=(2, 3), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.clearTableButton.Bind(wx.EVT_BUTTON, self.clearTable)# Clear Table
		
		# Get all Tag Relationships
		self.importFromDatabaseButton = wx.Button(self, label='Import From Database', size=(150, 25))
		self.grid.Add(self.importFromDatabaseButton, pos=(2, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.importFromDatabaseButton.Bind(wx.EVT_BUTTON, self.requestCurrentTagFamilyInfo)

		# Add to database
		self.addToDatabaseButton = wx.Button(self, label='Add to Database', size=(150, 25))
		self.grid.Add(self.addToDatabaseButton, pos=(2, 2), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.addToDatabaseButton.Bind(wx.EVT_BUTTON, self.sendParentTags)# Clear Table
		
		self.Bind(puriEvents.EVT_transferTagFamilyInfo, self.displayCurrentTagFamilyInfo)
		self.requestCurrentTagFamilyInfo()

		self.grid.AddGrowableCol(0)
		self.grid.AddGrowableRow(0)
		self.refreshPanel()

	def addTagRelationshipsToListBoxs(self, event):
		newChildTags = self.childTagBox.getSearchTags2()
		newParentTags = self.parentTagBox.getSearchTags2()

		self.childTagBox.clearListCtrl()
		self.parentTagBox.clearListCtrl()
		
		# Make all combos
		newCombos = []
		for newChildTag in newChildTags:
			for newParentTag in newParentTags:
				newCombos.append((newChildTag[0], newChildTag[1], newParentTag[0], newParentTag[1]))

		self.addCombos(newCombos)

		
	def addCombos(self, newCombos):
		
		# Remove all instances of previously added tags from list
		numAddedTags = self.tagListCtrl.GetItemCount()
		for i in range(0, numAddedTags):
			addedChildAttr = self.tagListCtrl.GetItemText(i, 0)
			addedChildVal = self.tagListCtrl.GetItemText(i, 1)
			addedParentAttr = self.tagListCtrl.GetItemText(i, 2)
			addedParentVal = self.tagListCtrl.GetItemText(i, 3)
			addedFamInfo = (addedChildAttr, addedChildVal, addedParentAttr, addedParentVal)
			try:
				while True:
					newCombos.remove(addedFamInfo)
			except ValueError:
				pass

		for i in range(0, len(newCombos)):
			index = self.tagListCtrl.InsertItem(sys.maxint, newCombos[i][0])
			self.tagListCtrl.SetItem(index, 1, newCombos[i][1])
			self.tagListCtrl.SetItem(index, 2, newCombos[i][2])
			self.tagListCtrl.SetItem(index, 3, newCombos[i][3])

	def requestCurrentTagFamilyInfo(self, event=None):
		comm = puriCommunication.get_communications()
		comm.guiToDatabase.send_message('gui-getAllTagFamilyInfo', self)
	
	def getTableInfo(self):
		numSearchTags = self.tagListCtrl.GetItemCount()
		tags = []
		for i in range(0, numSearchTags):
			tagParent = (self.tagListCtrl.GetItemText(i, 0), self.tagListCtrl.GetItemText(i, 1), self.tagListCtrl.GetItemText(i, 2), self.tagListCtrl.GetItemText(i, 3))
			tags.append(tagParent)
		return tags

	def sendParentTags(self, event=None):
		allTagParentInfo = self.getTableInfo()

		comm = puriCommunication.get_communications()
		comm.guiToDatabase.send_message('gui-addTagParents', allTagParentInfo)
	
	def clearTable(self, event=None):
		numTags = self.tagListCtrl.GetItemCount()
		for i in range(0, numTags):
			self.tagListCtrl.DeleteItem(0)

	def displayCurrentTagFamilyInfo(self, event):
		#self.clearTable()

		self.tagFamilyAllInfo = event.getValue()
		newCombos = []
		for i in range(0, len(self.tagFamilyAllInfo)):
			famInfo = self.tagFamilyAllInfo[i][0]
			childInfo = self.tagFamilyAllInfo[i][1]
			parentInfo = self.tagFamilyAllInfo[i][2]
			newCombos.append((childInfo.tagAttribute, childInfo.tagValue, parentInfo.tagAttribute, parentInfo.tagValue))

		print 'adding from database'
		self.addCombos(newCombos)