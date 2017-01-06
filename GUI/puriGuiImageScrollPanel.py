import wx
import os
import sys
import subprocess

sys.path.insert(0, './../backend')
#import puriDatabase

from wx.lib.scrolledpanel import ScrolledPanel
import puriEvents
import puriGuiCommon
'''
import pygtk
pygtk.require('2.0')
import gtk
'''

thumbnailHeight = 200
thumbnailWidth = 200


class puriThumbnail(wx.Panel):
	def __init__(self, parent, imageInfo):
		wx.Panel.__init__(self, parent, size=(thumbnailHeight, thumbnailWidth), style=wx.SIMPLE_BORDER)
		self.parent = parent
		self.imageInfo = imageInfo

		self.fullImage = wx.Image(imageInfo.imagePath, wx.BITMAP_TYPE_ANY)
		#pdb.set_trace()

		self.thumbnailImage = self.resizeImage(self.fullImage)
		thumbnailBitmap = wx.BitmapFromImage(self.thumbnailImage)
		self.thumbnailStaticBitmap = wx.StaticBitmap(self, -1, thumbnailBitmap)
		#self.thumbnailStaticBitmap.Hide()
		#self.thumbnailStaticBitmap.Create(self, -1, thumbnailBitmap)
		#self.thumbnailStaticBitmap.Create(self, -1, fullBitmap)

		self.vSizer = wx.BoxSizer(wx.VERTICAL)
		self.vSizer.SetMinSize((thumbnailWidth, thumbnailHeight))
		self.vSizer.Add(self.thumbnailStaticBitmap, flag=wx.ALIGN_CENTER)
		self.SetSizer(self.vSizer)
		#self.thumbnailStaticBitmap.Show()
		#self.Show()
		#self.Refresh()

		self.thumbnailStaticBitmap.Bind(wx.EVT_LEFT_UP, self.onLeftClick)
		self.Bind(wx.EVT_LEFT_UP, self.onLeftClick)

		self.popupmenu = wx.Menu()
		item = self.popupmenu.Append(-1, 'ShareX Upload')
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnShowPopUp)
		self.Bind(wx.EVT_MENU, self.sharex_upload, item)

	def copyImageIntoClipboard(self):
		clipboard = gtk.clipboard_get()
		img = gtk.Image()
		img.set_from_file(self.imageInfo.imagePath)
		clipboard.set_image(img.get_pixbuf())
		clipboard.store()

	def OnShowPopUp(self, event):
		pos = event.GetPosition()
		pos = self.ScreenToClient(pos)
		self.PopupMenu(self.popupmenu, pos)

	def sharex_upload(self, event):
		subprocess.call(['C:\\Program Files\\ShareX\\ShareX.exe', self.imageInfo.imagePath])

	def onLeftClick(self, event):
		print 'buttonPress for %s' % (self.imageInfo.imagePath)
		import pdb
		#pdb.set_trace()
		# TODO not working

		self.parent.parent.imageInfoPanel.displayImageInfo(self.imageInfo)
		self.BackgroundColor = wx.BLUE

	def resizeImage(self, image):
		oldWidth = image.GetWidth()
		oldHeight = image.GetHeight()
		widthRatio = oldWidth / float(thumbnailWidth)
		heightRatio = oldHeight / float(thumbnailHeight)

		if widthRatio > heightRatio:
			newWidth = thumbnailWidth
			newHeight = thumbnailHeight * oldHeight / oldWidth
		else:
			newHeight = thumbnailHeight
			newWidth = thumbnailWidth* oldWidth / oldHeight
		return image.Scale(newWidth, newHeight, wx.IMAGE_QUALITY_HIGH)


class puriImageScrollPanel(ScrolledPanel):
	def __init__(self, parent, *args, **kwargs):
		ScrolledPanel.__init__(self, parent, *args, **kwargs)
		self.parent = parent
		self.thumbnails = []
		self.numImages = 0
		self.thumbnailGrid = None
		self.Bind(puriEvents.EVT_addImageToScroll, self.onAddImageToScrollEvent)
		self.clearImages()
		self.Bind(wx.EVT_SIZE, self.onPanelResize)
		self.SetupScrolling()


	def addImage(self, imageInfo):
		(extra, extension) = os.path.splitext(imageInfo.imagePath)

		if extension != '.zip':
			self.thumbnails.append(puriThumbnail(self, imageInfo))
			numImages = len(self.thumbnailGrid.GetChildren())
			print numImages
			xpos = numImages / self.numImagesInRow
			ypos = numImages % self.numImagesInRow
			self.thumbnailGrid.Add(self.thumbnails[numImages], pos=(xpos, ypos), border=10)
			self.thumbnails[numImages].Show()
			self.thumbnails[numImages].Refresh()
			self.Show()
			self.Layout()
			self.Refresh()
			#self.Reload()
			self.numImages += 1

	def addImages(self, images):

		print 'numImagesAdded=%d' % (len(images))
		for i in range(0, len(images)):
			self.addImage(images[i])
			

	def clearImages(self):
		if self.thumbnailGrid == None:
			self.thumbnailGrid = wx.GridBagSizer(0, 0)
			self.SetSizer(self.thumbnailGrid)
		else:
			for i in range(0, len(self.thumbnailGrid.GetChildren())):
				self.thumbnailGrid.Hide(0)
				self.thumbnailGrid.Remove(0)
		self.thumbnails = []
		self.numImages = 0
		self.numImagesInRow = self.GetSize()[0] / thumbnailWidth
		if self.numImagesInRow == 0:
			self.numImagesInRow = 1


	def repositionImages(self):
		for i in range(0, len(self.thumbnailGrid.GetChildren())):
			self.thumbnailGrid.Hide(0)
			self.thumbnailGrid.Remove(0)
		print 'numImages=%d' % (self.numImages)
		for i in range(0, self.numImages):
			xpos = i / self.numImagesInRow
			ypos = i % self.numImagesInRow
			self.thumbnailGrid.Add(self.thumbnails[i], pos=(xpos, ypos), border=10)
			self.thumbnails[i].Show()
		#for i in range(0, self.numImages):
		#	print 'imageId=%d\timagePath=%s' % (self.thumbnails[i].imageInfo.imageId, self.thumbnails[i].imageInfo.imagePath)
	

	def onAddImageToScrollEvent(self, event):
		imageInfo = event.get_image_info()
		self.addImage(imageInfo)

	def onPanelResize(self, event):
		oldImagesInRow = self.numImagesInRow
		self.numImagesInRow = self.GetSize()[0] / thumbnailWidth
		if self.numImagesInRow == 0:
			self.numImagesInRow = 1
		if oldImagesInRow != self.numImagesInRow:
			self.repositionImages()


class puriImageInfoPanel(puriGuiCommon.optionsGridPanel):
	#def __init__(self, parent, imageSearchPanel):
	def __init__(self, parent, parentSplitter):
		puriGuiCommon.optionsGridPanel.__init__(self, parent, 'Selected Image Tags', parentSplitter)
		
		# image tags listbox
		self.imageTagsListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT|wx.LC_HRULES)
		self.imageTagsListCtrl.InsertColumn(0, 'TagAttr', width=75)
		self.imageTagsListCtrl.InsertColumn(1, 'TagVal', width=150)
		self.grid.Add(self.imageTagsListCtrl, pos=(0, 0), span=(1, 1), flag=wx.EXPAND|wx.ALIGN_LEFT, border=0)
	
		self.grid.AddGrowableCol(0)
		self.grid.AddGrowableRow(0)
		self.refreshPanel()

	def displayImageInfo(self, imageInfo):
		numTags = self.imageTagsListCtrl.GetItemCount()
		for i in range(0, numTags):
			self.imageTagsListCtrl.DeleteItem(0)

		for i in range(0, len(imageInfo.tags)):
			index = self.imageTagsListCtrl.InsertStringItem(sys.maxint, imageInfo.tags[i].tagAttribute)
			self.imageTagsListCtrl.SetStringItem(index, 1, imageInfo.tags[i].tagValue)