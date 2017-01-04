import wx

myEVT_addImageToScroll = wx.NewEventType()
EVT_addImageToScroll = wx.PyEventBinder(myEVT_addImageToScroll, 1)
class addImageToScrollEvent(wx.PyCommandEvent):
	def __init__ (self, etype, eid, imageInfo):
		wx.PyCommandEvent.__init__(self, etype, eid)
		self.imageInfo = imageInfo

	def get_image_info(self):
		return self.imageInfo


myEVT_setImagesFound = wx.NewEventType()
EVT_setImagesFound = wx.PyEventBinder(myEVT_setImagesFound, 1)
class setImagesFoundEvent(wx.PyCommandEvent):
	def __init__ (self, etype, eid, numImagesFound):
		wx.PyCommandEvent.__init__(self, etype, eid)
		self.numImagesFound = numImagesFound

	def getValue(self):
		return self.numImagesFound

myEVT_setImagesDownloaded = wx.NewEventType()
EVT_setImagesDownloaded = wx.PyEventBinder(myEVT_setImagesDownloaded, 1)
class setImagesDownloadedEvent(wx.PyCommandEvent):
	def __init__ (self, etype, eid, numImagesDownloaded):
		wx.PyCommandEvent.__init__(self, etype, eid)
		self.numImagesDownloaded = numImagesDownloaded

	def getValue(self):
		return self.numImagesDownloaded

myEVT_importTagLinks = wx.NewEventType()
EVT_importTagLinks = wx.PyEventBinder(myEVT_importTagLinks, 1)
class importTagLinksEvent(wx.PyCommandEvent):
	def __init__ (self, etype, eid, allTagLinks):
		wx.PyCommandEvent.__init__(self, etype, eid)
		self.allTagLinks = allTagLinks

	def getValue(self):
		return self.allTagLinks

