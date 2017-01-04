import wx
import puriGuiCommon
import puriCommunication
import puriEvents
import sys
import locale

class linkedTagsEditorPanel(puriGuiCommon.optionsGridPanel):
	def __init__(self, parent):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, 'Linked Tags Information')

		self.linkedTagsListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT|wx.LC_HRULES)
		self.linkedTagsListCtrl.InsertColumn(0, 'Tag1 Attribute', width=75)
		self.linkedTagsListCtrl.InsertColumn(1, 'Tag1 Value', width=150)
		self.linkedTagsListCtrl.InsertColumn(2, 'Tag2 Attribute', width=75)
		self.linkedTagsListCtrl.InsertColumn(3, 'Tag2 Value', width=150)
		self.grid.Add(self.linkedTagsListCtrl, pos=(0, 0), span=(3, 4), flag=wx.EXPAND|wx.ALIGN_LEFT, border=0)
		
		self.newTagLinksBox = puriGuiCommon.searchTagBox(self, boxTitle='Tags to Link')
		self.grid.Add(self.newTagLinksBox, pos=(3, 0), span=(2, 2), flag=wx.EXPAND|wx.ALIGN_LEFT, border=0)
		
		# Add Tag Relationships
		self.addTagRelationshipsButton = wx.Button(self, label='Add Tag Relationships', size=(100, 25))
		self.grid.Add(self.addTagRelationshipsButton, pos=(3, 2), span=(1, 2), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.addTagRelationshipsButton.Bind(wx.EVT_BUTTON, self.addTagRelationshipsToListBoxs)
		
		# Clear Table
		self.clearTableButton = wx.Button(self, label='Clear Table', size=(100, 25))
		self.grid.Add(self.clearTableButton, pos=(5, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.clearTableButton.Bind(wx.EVT_BUTTON, self.clearTable)# Clear Table
		
		# Get all Tag Relationships
		self.importFromDatabaseButton = wx.Button(self, label='Import From Database', size=(100, 25))
		self.grid.Add(self.importFromDatabaseButton, pos=(5, 2), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.importFromDatabaseButton.Bind(wx.EVT_BUTTON, self.importTagLinks)

		# Add to database
		self.addToDatabaseButton = wx.Button(self, label='Export to Database', size=(100, 25))
		self.grid.Add(self.addToDatabaseButton, pos=(5, 3), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.addToDatabaseButton.Bind(wx.EVT_BUTTON, self.exportTagLinks)# Clear Table
		
		self.Bind(puriEvents.EVT_importTagLinks, self.displayCurrentTagFamilyInfo)
		self.importTagLinks()

		self.grid.AddGrowableCol(0)
		self.grid.AddGrowableRow(0)
		self.refreshPanel()

	def addTagRelationshipsToListBoxs(self, event):
		tags = self.newTagLinksBox.getSearchTags2()
		self.newTagLinksBox.clearListCtrl()
		
		# Sort
		locale.setlocale(locale.LC_ALL, "")
		tags.sort(cmp=locale.strcoll)

		# Make all taglink combos
		newTagLinks = []
		for i in range(0, len(tags)):
			for j in range(i + 1, len(tags)):
				newTagLinks.append(tags[i][0], tags[i][1], tags[j][0], tags[j][1])

		self.addNewTagLinks(self, newTagLinks)
		
	def addNewTagLinks(self, newTagLinks):
		
		# Remove all instances of previously added tags from list
		numAddedTags = self.linkedTagsListCtrl.GetItemCount()
		for i in range(0, numAddedTags):
			tag1Attr = self.linkedTagsListCtrl.GetItemText(i, 0)
			tag1Val = self.linkedTagsListCtrl.GetItemText(i, 1)
			tag2Attr = self.linkedTagsListCtrl.GetItemText(i, 2)
			tag2Val = self.linkedTagsListCtrl.GetItemText(i, 3)
			addedFamInfo = (tag1Attr, tag1Val, tag2Attr, tag1Val)
			try:
				while True:
					newTagLinks.remove(addedFamInfo)
			except ValueError:
				pass

		for i in range(0, len(newTagLinks)):
			index = self.linkedTagsListCtrl.InsertItem(sys.maxint, newTagLinks[i][0])
			self.linkedTagsListCtrl.SetItem(index, 1, newTagLinks[i][1])
			self.linkedTagsListCtrl.SetItem(index, 2, newTagLinks[i][2])
			self.linkedTagsListCtrl.SetItem(index, 3, newTagLinks[i][3])

	def importTagLinks(self, event=None):
		comm = puriCommunication.get_communications()
		comm.guiToDatabase.send_message('gui-importTagLinks', self)
	
	def getTableInfo(self):
		numSearchTags = self.linkedTagsListCtrl.GetItemCount()
		tagsLinks = []
		for i in range(0, numSearchTags):
			tagLink = (self.linkedTagsListCtrl.GetItemText(i, 0), self.linkedTagsListCtrl.GetItemText(i, 1), self.linkedTagsListCtrl.GetItemText(i, 2), self.linkedTagsListCtrl.GetItemText(i, 3))
			tagsLinks.append(tagLink)
		return tagLinks

	def exportTagLinks(self, event=None):
		allTagParentInfo = self.getTableInfo()

		comm = puriCommunication.get_communications()
		comm.guiToDatabase.send_message('gui-exportTagLinks', allTagParentInfo)
	
	def clearTable(self, event=None):
		numTags = self.linkedTagsListCtrl.GetItemCount()
		for i in range(0, numTags):
			self.linkedTagsListCtrl.DeleteItem(0)

	def displayCurrentTagFamilyInfo(self, event):
		#self.clearTable()

		self.tagFamilyAllInfo = event.getValue()
		newTagLinks = []
		for i in range(0, len(self.tagFamilyAllInfo)):
			tag1 = self.tagFamilyAllInfo[i][1]
			tag2 = self.tagFamilyAllInfo[i][2]
			newTagLinks.append((tag1.tagAttribute, tag1.tagValue, tag2.tagAttribute, tag2.tagValue))

		self.addNewTagLinks(newTagLinks)