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

myEVT_transferTagFamilyInfo = wx.NewEventType()
EVT_transferTagFamilyInfo = wx.PyEventBinder(myEVT_transferTagFamilyInfo, 1)
class transferTagFamilyInfoEvent(wx.PyCommandEvent):
	def __init__ (self, etype, eid, allFamilyInfo):
		wx.PyCommandEvent.__init__(self, etype, eid)
		self.allFamilyInfo = allFamilyInfo

	def getValue(self):
		return self.allFamilyInfo

