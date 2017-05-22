import io
import os
import wx
import sys
import threading
import hashlib
import puriCommunication
import puriEvents
from puriDataStructures import puriTag
from puriDataStructures import puriImageInfo
_database_manager = None
_database = None
def start_database_manager(databasePath):
    global _database_manager
    if _database_manager == None:
        _database_manager = puriDatabaseManager(databasePath)
        _database_manager.start()

# Return the database
def get_puri_database(databasePath=None):
    global _database

    if _database == None:
        if databasePath == None:
            print 'No database path specified'
            exit()
        _database = database(databasePath)
    return _database

class puriDatabaseManager(threading.Thread):
    def __init__(self, databasePath):
        #self.parent = parent
        threading.Thread.__init__(self)
        self.comm = puriCommunication.get_communications()
        self.databasePath = databasePath
        self.loggedIn = False

    def run(self):
        self.database = get_puri_database(self.databasePath)
        while True:
            (sender, messageType, message) = self.get_next_command()
            if sender == u'': 
                pass
            else:
                if messageType == 'downloader-addPixivImageToDatabase':
                    self.database.addPixivImageToDatabase(message)
                elif messageType == 'database-localImageSearchByTags':
                    ret = self.database.localImageSearchByTags(message)
                    #self.sendResponse(sender, messageType, ret)
                elif messageType == 'gui-importTagLinks':
                    self.database.importTagLinks(message)
                elif messageType == 'gui-exportTagLinks':
                    self.database.exportTagLinks(message)

    def get_next_command(self):
        sender = u''
        while sender == '': 
            browserTime = self.comm.browserToDatabase.get_send_time()
            downloaderTime = self.comm.downloaderToDatabase.get_send_time()
            guiTime = self.comm.guiToDatabase.get_send_time()
            if (browserTime < downloaderTime) and (browserTime < guiTime):
                (messageType, message) = self.comm.browserToDatabase.rec_message()
                sender = 'browser'
            elif (downloaderTime < guiTime):
                (messageType, message) = self.comm.downloaderToDatabase.rec_message()
                sender = 'downloader'
            elif (guiTime != sys.float_info.max):
                (messageType, message) = self.comm.guiToDatabase.rec_message()
                sender = 'gui'
        return (sender, messageType, message)


    def sendResponse(self, dest, messageType, message):
        if dest == 'browser':
            self.comm.databaseToBrowser.send_message(messageType, message)
        elif dest == 'downloader':
            self.comm.databaseToDownloader.send_message(messageType, message)
        elif dest == 'gui':
            self.comm.databaseToGui.send_message(messageType, message)

class database:
    def __init__(self, databaseFolder):
        self.databasePath = databaseFolder
        self.loadDatabase()
    
    def loadImageDbFile(self):
        path = self.databasePath + 'imageInfo.db'
        imageInfo = []
        if os.path.exists(path):
            with open(path, 'r') as f:
                lines = f.readlines()
                for i in range(0, len(lines), 3):
                    path = lines[i]
                    imHash = lines[i+1]
                    tags = lines[i+2].split(',')
                    tags = [x.split('::') for x in tags]
                    tags = [puriTag(x[0], x[1]) for x in tags]
                    imageInfo.append(puriImageInfo(path, imHash, tags))
        return imageInfo

    def writeImageDbFile(self):
        path = self.databasePath + 'imageInfo.db'
        s = u''
        if not os.path.exists(self.databasePath):
            os.mkdir(self.databasePath)
        for imageInfo in self.imageInfos:
            s += imageInfo.path + u'\n'
            s += imageInfo.hash + u'\n'
            for tag in imageInfo.tags:
                s += '%s::%s,' % (tag.attr, tag.val)
            s += u'\n'
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(s)

    def loadTagDbFile(self):
        path = self.databasePath + 'tags.db'
        tags = []
        if os.path.exists(path):
            with open(path, 'r') as f:
                lines = f.readlines()
                tags = [x.split('::') for x in lines]
                tags = [puriTag(x[0], x[1]) for x in tags]
        return tags

    def writeTagDbFile(self):
        path = self.databasePath + 'tags.db'
        s = u''
        if not os.path.exists(self.databasePath):
            os.mkdir(self.databasePath)
        for tag in self.tags:
            s += u'%s::%s\n' % (tag.attr, tag.val)
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(s)

    def loadDatabase(self):
        self.tags = self.loadTagDbFile()
        self.imageInfos = self.loadImageDbFile()

    def writeDatabase(self):
        self.writeImageDbFile()
        self.writeTagDbFile()

    # Find path to write file to disk
    # + Make this path
    def makeImagePath(self, newImageInfo):
        # Create folder to write the image to
        picsFolder = os.getcwd() + u'/pics/'
        if not os.path.exists(picsFolder):
            os.makedirs(picsFolder)

        # Create the filename to write the file to
        imageId = newImageInfo.get_value('image_id')
        filename, extension = os.path.splitext(newImageInfo.get_value('image_url'))
        fName = picsFolder + imageId + extension

        return fName


    # Write an image to the disk
    def writeImageToDisk(self, newImageInfo):
        fName =  self.makeImagePath(newImageInfo,)
        f = file(fName, 'wb+', 4096)
        f.write(newImageInfo.imageData)
        f.close()
        return fName
    
    # Make a hash string of the file
    def getFileHash(self, data):
        m = hashlib.md5()
        m.update(data)
        hashString = m.hexdigest()
        return unicode(hashString, 'utf8')

    def addTag(self, tag):
        if len(self.tags) == 0 or not all (x for x in self.tags if tag.attr==x.attr and tag.val==x.val):
            self.tags.append(tag)

    def getImageInfo(self, imHash=None, path=None):
        possImg = []
        if imHash != None:
            possImg = [x for x in self.imageInfos if x.hash == imHash]
        elif path != None:
            possImg = [x for x in self.imageInfos if x.path == path]
        if len(possImg) == 0:
            return False
        else:
            return possImg[0]


    def addPixivImageToDatabase(self, message):
        (newImageInfo, searchGui) = message

        import pdb
        pdb.set_trace()
        
        imHash = self.getFileHash(newImageInfo.imageData)
        imageInDatabase = self.getImageInfo(imHash=imHash)
        if imageInDatabase==False:
             
            imPath = self.writeImageToDisk(newImageInfo)
            
            # Add Tags to the db
            for tag in newImageInfo.tags:
                self.addTag(tag)
            
            imageInDatabase = puriImageInfo(path=imPath, imHash=imHash, tags=newImageInfo.tags)
            del(newImageInfo)
            self.imageInfos.append(imageInDatabase)
            self.writeDatabase()

        evt = puriEvents.addImageToScrollEvent(puriEvents.myEVT_addImageToScroll, -1, imageInDatabase)
        wx.PostEvent(searchGui.parent.parent.imageScrollPanel, evt)
        
    def localImageSearchByTags(self, message):
        (searchTags, searchGui) = message

        # Parse the tagList
        searchTags = [x.split('::') for x in searchTags]
        searchTags = [puriTag(None, x[0]) if len(x) == 1 else puriTag(x[0], x[1]) for x in searchTags]

        # Add in other tags that are linked
        # TODO
        searchTagSets = [[x] for x in searchTags]

        # Get list of images that fit each tag
        imageSets = []
        for searchTagSet in searchTagSets:
            imageSet = set()
            for tag in searchTagSet:
                if tag.attr == u'tag':
                    imageSet |= set([x for x in self.imageInfos if x.val == tag.val])
                else:
                    imageSet |= set([x for x in self.imageInfos if x.attr == tag.attr and x.val == tag.val])
            imageSets.append(list(imageSet))
        
        # Find images common to each set
        images = imageSets[0]
        for i in range(1, len(imageSets)):
            images &= imageSets[i]
        images = list(images)

        for image in images:
            evt = puriEvents.addImageToScrollEvent(puriEvents.myEVT_addImageToScroll, -1, imageInfo)
            wx.PostEvent(searchGui, evt)


