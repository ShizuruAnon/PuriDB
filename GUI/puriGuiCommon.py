import wx
import sys


class optionsGridPanel(wx.Panel):
	def __init__(self, parent, text, actualParent=None):
		if actualParent != None:
			wx.Panel.__init__(self, actualParent, wx.ID_ANY)
		else:
			wx.Panel.__init__(self, parent, wx.ID_ANY)
		
		# Set parent
		self.parent = parent

		self.box = wx.StaticBox(self, wx.ID_ANY, text)
		self.boxSizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)
		self.grid = wx.GridBagSizer(0, 0)
		self.boxSizer.Add(self.grid, 10, wx.ALL|wx.CENTER|wx.EXPAND, 0)
		self.SetSizer(self.boxSizer)
		self.Refresh()
		self.Layout()
		self.Show()

	def refreshPanel(self):
		self.Refresh()
		self.Layout()
		self.Show()

class searchTagBox(optionsGridPanel):
	def __init__(self, parent, boxTitle='Search Tags'):
		optionsGridPanel.__init__(self, parent, boxTitle)
		
		# Added Tags List
		self.addedTagsListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT|wx.LC_HRULES)
		self.addedTagsListCtrl.InsertColumn(0, 'TagAttr', width=50)
		self.addedTagsListCtrl.InsertColumn(1, 'TagVal', width=90)
		self.grid.Add(self.addedTagsListCtrl, pos=(0, 0), span=(3, 1), flag=wx.EXPAND|wx.ALIGN_LEFT, border=0)

		# New Tags
		self.newTags = wx.TextCtrl(self, -1, style=wx.TE_PROCESS_ENTER,)
		self.grid.Add(self.newTags, pos=(3, 0), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT, border=0)
		self.newTags.Bind(wx.EVT_TEXT_ENTER, self.addTagsToListBox)

		# Add Tag
		self.addTagButton = wx.Button(self, label='Add Tag', size=(60, 25))
		self.grid.Add(self.addTagButton, pos=(3, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP, border=0)
		self.addTagButton.Bind(wx.EVT_BUTTON, self.addTagsToListBox)

		# Up Selection
		self.upButton = wx.Button(self, label='^', size=(60, 25))
		self.grid.Add(self.upButton, pos=(0, 1), span=(1, 1), flag=wx.ALIGN_RIGHT, border=0)

		# Delete Tag
		self.deleteButton = wx.Button(self, label='X', size=(60, 25))
		self.grid.Add(self.deleteButton, pos=(1, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM, border=0)
		self.deleteButton.Bind(wx.EVT_BUTTON, self.onDeleteButtonPress)

		# Down Selection
		self.downButton = wx.Button(self, label='v', size=(60, 25))
		self.grid.Add(self.downButton, pos=(2, 1), span=(1, 1), flag=wx.ALIGN_RIGHT, border=0)

		self.grid.AddGrowableCol(0)
		self.refreshPanel()

	def getSearchTags(self):
		numSearchTags = self.addedTagsListCtrl.GetItemCount()
		tags = []
		for i in range(0, numSearchTags):
			tags.append(self.addedTagsListCtrl.GetItemText(i, 1))
		return tags

	def getSearchTags2(self):
		numSearchTags = self.addedTagsListCtrl.GetItemCount()
		tags = []
		for i in range(0, numSearchTags):
			tags.append((self.addedTagsListCtrl.GetItemText(i, 0), self.addedTagsListCtrl.GetItemText(i, 1)))
		return tags


	def onDeleteButtonPress(self, event):
		numSelItems = self.addedTagsListCtrl.GetSelectedItemCount()
		print 'numSelItems %s' % (numSelItems)
		for i in range(0, numSelItems):
			idx = self.addedTagsListCtrl.GetNextSelected(-1)
			self.addedTagsListCtrl.DeleteItem(idx)

	def clearListCtrl(self):
		numItems = self.addedTagsListCtrl.GetItemCount()
		for i in range(0, numItems):
			self.addedTagsListCtrl.DeleteItem(0)

	def addTagsToListBox(self, event):
		# Get all tags from box
		newTagStrings = self.newTags.GetValue()
		newTagStrings = newTagStrings.split()
		self.newTags.Clear()

		# Split the tag Attribute and Value
		newTags = []
		for i in range(0, len(newTagStrings)):
			tag = newTagStrings[i].split(':')
			if len(tag) == 1:
				tagAttr ='tag'
				tagVal = tag[0]
			elif len(tag) == 2:
				tagAttr = tag[0]
				tagVal = tag[1]
			newTags.append((tagAttr, tagVal))

		# Remove all instances of previously added tags from list
		numAddedTags = self.addedTagsListCtrl.GetItemCount()
		for i in range(0, numAddedTags):
			addedAttr = self.addedTagsListCtrl.GetItemText(i, 0)
			addedVal = self.addedTagsListCtrl.GetItemText(i, 1)
			addedTag = (addedAttr, addedVal)
			try:
				while True:
					newTags.remove(addedTag)
			except ValueError:
				pass

		# Add Items to the listBox if they exist
		for i in range(0, len(newTags)):
			index = self.addedTagsListCtrl.InsertItem(sys.maxint, newTags[i][0])
			self.addedTagsListCtrl.SetItem(index, 1, newTags[i][1])