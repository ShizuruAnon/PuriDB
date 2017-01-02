import wx
import sys
from puriGuiDownloadPanel import puriDownloadPanel
from puriGuiSearchPanel import puriImageSearchPanel
from puriGuiTagFamilyInfoPanel import tagFamilyInfoPanel

# Import from the backend
sys.path.insert(0, './../backend')
import puriDownloader
import puriDataStructures
import puriBrowser
import puriDatabase

defaultSize = (500, 500)
defaultTitle = 'PuriDB'


class puriMainMenubar(wx.MenuBar):
	def __init__(self, parent, *args, **kwargs):
		super(puriMainMenubar, self).__init__(*args, **kwargs)

		self.parent = parent

		# File menu
		fileMenu = wx.Menu()
		qmi = wx.MenuItem(fileMenu, wx.ID_EXIT, '&Quit\tCtrl+W')
		fileMenu.Append(qmi)
		self.Bind(wx.EVT_MENU, parent.OnQuit, qmi)
		self.Append(fileMenu, '&File')

		# Tab Menu
		dlMenu = wx.Menu()
		downloadTab = wx.MenuItem(dlMenu, wx.ID_ANY, 'Download Tab')
		searchTab = wx.MenuItem(dlMenu, wx.ID_ANY, 'Search Tab')
		dlMenu.Append(downloadTab)
		dlMenu.Append(searchTab)
		self.Bind(wx.EVT_MENU, self.addDownloadTab, downloadTab)
		self.Bind(wx.EVT_MENU, self.addSearchTab, searchTab)
		self.Append(dlMenu, 'Open New Tab')

		parent.SetMenuBar(self)


	def addDownloadTab(self, event):
		self.parent.notebook.addTab('Download Tab')

	def addSearchTab(self, event):
		self.parent.notebook.addTab('Search Tab')


class puriNotebook(wx.Notebook):
	def __init__(self, grandParent):
		self.grandParnet = grandParent
		self.notebookPanel = wx.Panel(grandParent)
		wx.Notebook.__init__(self, self.notebookPanel, id=wx.ID_ANY, style=wx.BK_DEFAULT)

		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnPageChanging)

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self, 1, wx.ALL|wx.EXPAND, 5)
		self.notebookPanel.SetSizer(self.sizer)

		# Start with these tags just because
		self.addTab('Download Tab')
		self.addTab('Search Tab')
		self.addTab('Tag Family Tab')

	def OnPageChanged(self, event):
		old = event.GetOldSelection()
		new = event.GetSelection()
		sel = self.GetSelection()
		print 'OnPageChanged,  old:%d, new:%d, sel:%d\n' % (old, new, sel)
		event.Skip()

	def OnPageChanging(self, event):
		old = event.GetOldSelection()
		new = event.GetSelection()
		sel = self.GetSelection()
		print 'OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel)
		event.Skip()

	def addTab(self, panelType):
		if panelType == 'Download Tab':
			newPanel = puriDownloadPanel(self)
			newLabel = 'Download'
		elif panelType == 'Search Tab':
			newPanel = puriImageSearchPanel(self)
			newLabel = 'Search'
		elif panelType == 'Tag Family Tab':
			newPanel = tagFamilyInfoPanel(self)
			newLabel = 'Tag Family'
		self.AddPage(newPanel, newLabel)
		self.SetSelection(self.GetPageCount() - 1)

class puriMainFrame(wx.Frame):
	_topFrame = None

	def __init__(self, *args, **kwargs):
		super(puriMainFrame, self).__init__(*args, **kwargs) 

		self.mainMenubar = puriMainMenubar(self)
		self.notebook= puriNotebook(self)
		#self.tabbedPanels = puriTabbedPanel(self) 
		#self.downloadPanel = puriDownloadPanel(self)

		self.Layout()
		self.Show()

		self.InitUI()

	def InitUI(self):
		self.SetSize(defaultSize)
		self.SetTitle(defaultTitle)
		self.Centre()
		self.Show(True)

	def OnQuit(self, e):
		self.Close()