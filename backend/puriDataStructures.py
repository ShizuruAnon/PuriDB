
class puriImageTag():
	def __init__(self, tagAttribute=None, tagValue=None):
		self.tagAttribute=tagAttribute
		self.tagValue=tagValue

class puriImageInfo():
	def __init__(self, imagePath=None):
		self.imagePath = imagePath
		self.tags = []

	def add_tag(self, tagAttribute, tagValue):
		if (tagAttribute == None):
			tagAttribute = 'tag'
		newTag = puriImageTag(tagAttribute, tagValue)
		self.tags.append(newTag)

	def has_tag_value(self, tagValue, tagAttribute = None):
		if tagAttribute == None:
			for tag in self.tags:
				if tag.tagValue == tagValue:
					return True
		else:
			for tag in self.tags:
				if tag.tagValue == tagValue and tag.tagAttribute == tagAttribute:
					return True
		return False

	def get_all_tags_of_attribute(self, tagAttribute):
		tagList = []
		for tag in self.tags:
			if tag.tagAttribute == tagAttribute:
				tagList.append(tag)
		return tagList

	def get_unique_tag_of_attribute(self, tagAttribute):
		for tag in self.tags:
			if tag.tagAttribute == tagAttribute:
				return tag
		return None

class pixivImageInfo():
	def __init__(self):
		self.type = None
		self.imageId = None
		self.artistId = None
		self.tags = None
		self.imageName = None
		self.artistName = None
		self.numBookmarks = None
		self.imageUrls = []
		self.imageSizes = []
		self.imageDatas = []
		
class pixivSearchOptions:
	def __init__(self, tags=None, titleCaption=False, wildCard=True,
			oldestFirst=True, startDate='', endDate='',
			memberId='', r18Mode=False):
		self.tags = tags
		self.titleCaption = titleCaption
		self.wildCard = wildCard
		self.oldestFirst = oldestFirst
		self.startDate = startDate
		self.endDate = endDate
		self.memberId = memberId
		self.r18Mode = r18Mode

class pixivBrowserOptions:
	def __init__(self):
		self.set_to_default()

	def set_to_default(self):
		# Network Related
		self.proxyAddress = ''
		self.proxy = {'http': self.proxyAddress, 'https': self.proxyAddress, }
		self.useProxy = False
		self.useragent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'
		self.useRobots = True
		self.timeout = 60
		self.retry = 3
		self.retryWait = 5

		# Pixiv Auth Related
		self.username = ''
		self.password = ''
		self.loginCookie = ''
		self.keepSignedIn = 0

		# Pixiv related
		self.dateFormat = ''

		# Debug related 
		self.debugHttp = False
		self.enableDump = True
		self.dumpTagSearchPage = False


		#self.writeConfig