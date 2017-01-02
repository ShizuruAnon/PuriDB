
import os
import hashlib
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Unicode, Table, create_engine
from sqlalchemy.schema import Sequence, ForeignKey
from sqlalchemy.orm import sessionmaker, mapper
import puriDataStructures
import puriEvents
import threading
import puriCommunication
import sys
import wx
imagePathSize = 512
tagAttributeSize = 256
tagStringSize = 256

_database = None

# Classes to interact with the database
###############################################
baseDatabaseClass = declarative_base()

class imageTagPairEntry(baseDatabaseClass):
	__tablename__ = 'imageTagPairTable'

	imageTagPairId = Column(Integer, Sequence('imageTagId'), primary_key=True)
	tagId = Column(Integer, nullable=False)
	imageId = Column(Integer, nullable=False)
	#imagePath = Column(Unicode(imagePathSize), nullable=False)

class tagEntry(baseDatabaseClass):
	__tablename__ = 'tagTable'

	tagId = Column(Integer, Sequence('tagSequenceId'), primary_key=True)
	tagAttribute = Column(Unicode(tagAttributeSize), nullable=False)
	tagValue = Column(Unicode(tagStringSize), nullable=False)
	#parentTagId = Column(Integer, nullable=False)
	#childTagId = Column(Integer, nullable=False)

class tagFamilyInfoEntry(baseDatabaseClass):
	__tablename__ = 'tagFamilyInfoTable'

	tagFamilyInfoId = Column(Integer, Sequence('tagFamilyInfoSequenceId'), primary_key=True)
	parentTagId = Column(Integer, nullable=False)
	childTagId = Column(Integer, nullable=False)

###############################################
_database_manager = None
_database = None
def start_database_manager(databasePath):
	global _database_manager
	if _database_manager == None:
		_database_manager = puriDatabaseManager(databasePath)
		_database_manager.start()

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
			if sender == '':
				pass
			elif messageType == 'downloader-addPixivImageToDatabase':
				self.database.addPixivImageToDatabase(message)
			elif messageType == 'database-localImageSearchByTags':
				ret = self.database.localImageSearchByTags(message)
				#self.sendResponse(sender, messageType, ret)
			elif messageType == 'gui-getAllTagFamilyInfo':
				self.database.getAllTagFamilyInfo(message)
			elif messageType == 'gui-addTagParents':
				self.database.addTagParents(message)


	def get_next_command(self):
		sender = ''
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

# Return the database
def get_puri_database(databasePath=None):
	global _database

	if _database == None:
		if databasePath == None:
			print 'No database path specified'
			exit()
		_database = database(databasePath)
	return _database


# Database class to interact with the database
class database:
	def __init__ (self, databasePath):
		self.databasePath = databasePath
		self.engine = create_engine('sqlite:///' + self.databasePath, echo=False)
		self.metadata = baseDatabaseClass.metadata
		self.metadata.create_all(self.engine)
		self.SessionClass = sessionmaker(bind=self.engine)
		self.session = self.SessionClass()


	# Find path to write file to disk
	# + Make this path
	def makeImagePath(self, newImageInfo, i):
		# Create folder to write the image to

		picsFolder = os.getcwd() + u'/pics/'
		if not os.path.exists(picsFolder):
			os.makedirs(picsFolder)

		# Create the filename to write the file to
		if newImageInfo.type != 'ugoira':
			fName = picsFolder + str(newImageInfo.imageId) + '_' + str(i) + '.png'
		else:
			fName = picsFolder + str(newImageInfo.imageId) + '_' + str(i) + '.zip'

		return fName


	# Write an image to the disk
	def writeImageToDisk(self, newImageInfo, i):
		fName =  self.makeImagePath(newImageInfo, i)

		# Write the file
		f = file(fName, 'wb+', 4096)
		f.write(newImageInfo.imageDatas[i])
		f.close()

		return fName


	# Make a hash string of the file
	def getFileHash(self, data):
		m = hashlib.md5()
		m.update(data)
		hashString = m.hexdigest()
		return unicode(hashString, 'utf8')


	def addPixivImageToDatabase(self, message):
		newImageInfo = message[0]
		searchGui = message[1]

		# Write all images (for a manga) to the database
		for i in range(len(newImageInfo.imageDatas)):

			# Write the image to the disk, get the path
			imagePath = self.writeImageToDisk(newImageInfo, i)

			# Get the hash of the file
			imageHash = self.getFileHash(newImageInfo.imageDatas[i])

			# Check if the file is already in the database
			imageId = self.isFileInDatabase(imageHash)
			if imageId == 0:
				# Add Tags to the db
				tagIds = []
				tagIds.append(self.addTagEntry(u'image_path', imagePath))
				tagIds.append(self.addTagEntry(u'image_hash', imageHash))
				tagIds.append(self.addTagEntry(u'pixiv_id', newImageInfo.imageId))
				tagIds.append(self.addTagEntry(u'artist_id', newImageInfo.artistId))
				tagIds.append(self.addTagEntry(u'image_name', newImageInfo.imageName))
				tagIds.append(self.addTagEntry(u'artist_name', newImageInfo.artistName))
				tagIds.append(self.addTagEntry(u'bookmarks', newImageInfo.numBookmarks))
				for tag in newImageInfo.tags:
					tagIds.append(self.addTagEntry(u'tag', tag))

				# Add the imageTagPairs to the database
				imageId = self.addImageTagPairEntry(0, tagIds[0])
				for i in range(1, len(tagIds)):
					self.addImageTagPairEntry(imageId, tagIds[i])

			imageInfo = self.get_image_info(imageId)

			evt = puriEvents.addImageToScrollEvent(puriEvents.myEVT_addImageToScroll, -1, imageInfo)
			wx.PostEvent(searchGui.parent.parent.imageScrollPanel, evt)


	def isFileInDatabase(self, imageHash):

		tagId = self.findTagId(u'image_hash', imageHash)
		imageTagPair = self.session.query(imageTagPairEntry).\
			filter_by(tagId=tagId).\
			first()
		if imageTagPair == None:
			return 0
		else:
			return imageTagPair.imageId

		return imageId


	def addTagEntry(self, tagAttribute, tagValue):
		# Ensure tag isn't already in database
		tagId = self.findTagId(tagAttribute, tagValue)

		# Insert tag if no tag already
		if tagId == -1:
			newTagEntry = tagEntry(tagAttribute=tagAttribute, tagValue=tagValue)
			self.session.add(newTagEntry)
			self.session.commit()
			tagId = self.findTagId(tagAttribute, tagValue)
		return tagId


	def findTagId(self, tagAttribute, tagValue):
		tag = self.session.query(tagEntry).\
				filter_by(tagAttribute=tagAttribute).\
				filter_by(tagValue=tagValue).\
				first()
		if tag == None:
			return -1
		else:
			return tag.tagId
	
	def findTagFamilyInfoId(self, childTagId, parentTagId):
		tagFamilyInfo = self.session.query(tagFamilyInfoEntry).\
				filter_by(childTagId=childTagId).\
				filter_by(parentTagId=parentTagId).\
				first()
		if tagFamilyInfo == None:
			return -1
		else:
			return tagFamilyInfo.tagFamilyInfoId

	def addTagParent(self, childTagAttribute, childTagValue, parentTagAttribute, parentTagValue):
		childTagId = self.addTagEntry(childTagAttribute, childTagValue)
		parentTagId = self.addTagEntry(parentTagAttribute, parentTagValue)

		tagFamilyId = self.findTagFamilyInfoId(childTagId, parentTagId)
		if tagFamilyId == -1:
			tagFamilyInfo = tagFamilyInfoEntry(parentTagId=parentTagId, childTagId=childTagId)
			self.session.add(tagFamilyInfo)
			self.session.commit()
			tagFamilyId = self.findTagFamilyInfoId(childTagId, parentTagId)
		return tagFamilyId

	def addTagParents(self, message):
		tagParentList = message
		for i in range(0, len(tagParentList)):
			self.addTagParent(tagParentList[i][0], tagParentList[i][1], tagParentList[i][2], tagParentList[i][3])

	def getAllTagFamilyInfo(self, message):
		sendbackGui = message
		allFamilyInfo = self.session.query(tagFamilyInfoEntry).all()

		allInfo = []
		for familyInfo in allFamilyInfo:
			childInfo = self.session.query(tagEntry).\
					filter_by(tagId=familyInfo.childTagId).\
					first()
			parentInfo = self.session.query(tagEntry).\
					filter_by(tagId=familyInfo.parentTagId).\
					first()
			allInfo.append((familyInfo, childInfo, parentInfo))

		evt = puriEvents.transferTagFamilyInfoEvent(puriEvents.myEVT_transferTagFamilyInfo, -1, allInfo)
		wx.PostEvent(sendbackGui, evt)

	def findImageTagPairEntryId(self, imageId, tagId):
		imageTagPair = self.session.query(imageTagPairEntry).\
				filter_by(imageId=imageId).\
				filter_by(tagId=tagId).\
				first()

		if imageTagPair == None:
			return -1
		elif imageTagPair.imageId == 0:
			imageTagPair.imageId = imageTagPair.imageTagPairId
			self.session.commit()

		return imageTagPair.imageId


	def addImageTagPairEntry(self, imageId, tagId):
		imageTagPair = imageTagPairEntry(imageId=imageId, tagId=tagId)
		self.session.add(imageTagPair)
		self.session.commit()
		imageId = self.findImageTagPairEntryId(imageId, tagId)
		return imageId

	def getTagParents(self, tag):
		tagId = self.findTagId(tag.tagAttribute, tag.tagValue)
		familyInfo = self.session.query(tagFamilyInfoEntry).\
			filter_by(childTagId=tagId).\
			all()
		parentTags = []
		for i in range(0, len(familyInfo)):
			tag = self.session.query(tagEntry).\
				filter_by(tagId=familyInfo[i].parentTagId).\
				first()
			if tag != None:
				parentTags.append(tag)
		return parentTags


	def getAllTagParents(self, imageInfo):
		# Get the first level parents
		tagParents = []
		for i in range(0, len(imageInfo.tags)):
			parents = self.getTagParents(imageInfo.tags[i])
			if len(parents) > 0:
				for j in range(0, len(parents)):
					tagParents.append(parents[j])

		while len(tagParents) > 0:
			# Remove Redundant Tags
			for i in range(0, len(imageInfo.tags)):
				try:
					while True:
						tagParents.remove(imageInfo.tags[i])
				except ValueError:
					pass

			# Add Tags
			for i in range(0, len(tagParents)):
				imageInfo.tags.append(tagParents[i])

			# Search for new Tags
			newTagParents = []
			for i in range(0, len(tagParents)):
				parents = self.getTagParents(tagParents[i])
				if len(parents) > 0:
					for j in range(0, len(parents)):
						newTagParents.append(parents[j])
				
			tagParents = newTagParents


	def get_image_info(self, imageId):
		imageTagPairs = self.session.query(imageTagPairEntry).\
				filter_by(imageId=imageId).\
				all()

		imageInfo = puriDataStructures.puriImageInfo()
		for imageTagPair in imageTagPairs:
			tag = self.session.query(tagEntry).\
					filter_by(tagId=imageTagPair.tagId).\
					first()
			imageInfo.add_tag(tag.tagAttribute, tag.tagValue)

		imageInfo.imagePath = imageInfo.get_unique_tag_of_attribute('image_path').tagValue
		self.getAllTagParents(imageInfo)

		return imageInfo

	def localImageSearchByTags(self, message):
		(searchTags, searchGui) = message
		
		# Parse the tagList
		searchTagPairs = []
		for searchTag in searchTags:
			t = searchTag.split(':')
			L = len(t)
			if L == 1:
				tagPair = (None, t[0])
			elif L == 2:
				tagPair = t
			else:
				print (t)
				exit()
			searchTagPairs.append(tagPair)

		# Find the tag Entries for the searchTags
		tagIds = []
		for searchTagPair in searchTagPairs:
			query = self.session.query(tagEntry).\
					filter_by(tagValue=searchTagPair[1])
			if searchTagPair[0] != None:
				query = query.filter_by(tagAttribute=searchTagPair[0])
			searchResult = query.first()
			if searchResult != None:
				tagIds.append(searchResult.tagId)

		# For each tag, find images that have the tag
		queryResults = []
		for tagId in tagIds:
			queryResult = self.session.query(imageTagPairEntry).\
					filter_by(tagId=tagId).\
					all()
			if queryResult != None:
				queryResults.append(queryResult)


		successfulImageIds = []
		if len(queryResults) > 0:
			for i in range(0, len(queryResults[0])):
				inAllLists = 'yes'
				imageId1 = queryResults[0][i].imageId
				for j in range(1, len(queryResults)):
					temp = 'no'
					for k in range(0, len(queryResults[j])):
						if  imageId1 == queryResults[j][k].imageId:
							temp = 'yes'
							break
					if temp == 'no':
						inAllLists = 'no'
						break
				if inAllLists == 'yes':
					successfulImageIds.append(imageId1)
			
			#imageInfos = []
			for successfulImageId in successfulImageIds:
				imageInfo = self.get_image_info(successfulImageId)
				evt = puriEvents.addImageToScrollEvent(puriEvents.myEVT_addImageToScroll, -1, imageInfo)
				wx.PostEvent(searchGui, evt)
		#return imageInfos
