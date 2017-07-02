
class puriTag():
    def __init__(self, attr, val):
        self.attr = attr
        self.val = val

class puriImageInfo():
    def __init__(self, path=None, imHash=None, tags=None):
        self.path = path
        self.hash = imHash
        self.tags = tags

    def add_tag(self, tagAttr, tagVal):
        if (tagAttr == None):
            tagAttr = u'tag'
        newTag = puriTag(tagAttr, tagVal)
        if self.tags == None:
            self.tags = [newTag]
        else:
            self.tags.append(newTag)

    def has_tag_value(self, tagVal, tagAttr = None):
        if len(self.tags) == 0:
            return False
        if tagAttr == None:
            val = any(tag.val == tagVal for tag in self.tags)
        else:
            val = any(tag.val == tagVal and tag.attr == tagAttr for tag in self.tags)
        return val
    
    def get_all_tags_of_attribute(self, tagAttr):
        return [x for x in self.tags if x.attr == tagAttr]

    def get_value(self, tagAttr):
        for tag in self.tags:
            if tag.attr == tagAttr:
                return tag.val
        return None


    def remove_tag(self, tagAttr, tagVal):
            self.tags = [tag for tag in self.tags if (tag.attr != tagAttr or tag.val != tagVal)]

class puriDownloadOptions:
    def __init__(self, website, tags=[],
                    searchOrder='', startDate='', endDate='',
                    artistId='', artistName='', rating=''):
        self.website = website
        self.tags = tags
        self.searchOrder = searchOrder
        self.startDate = startDate
        self.endDate = endDate
        self.artistId = artistId
        self.artistName = artistName
        self.rating = rating


class puriBrowserOptions:
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
