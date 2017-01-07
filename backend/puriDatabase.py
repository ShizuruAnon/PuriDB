
import os
import hashlib
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Unicode, Table, create_engine, or_
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
	#tag2Id = Column(Integer, nullable=False)
	#tag1Id = Column(Integer, nullable=False)

class tagLinkEntry(baseDatabaseClass):
	__tablename__ = 'tagLinkTable'

	tagLinkId = Column(Integer, Sequence('tagLinkSequenceId'), primary_key=True)
	tag1Id = Column(Integer, nullable=False)
	tag2Id = Column(Integer, nullable=False)

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

		# Write the file
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


	def addPixivImageToDatabase(self, message):

		newImageInfo = message[0]
		searchGui = message[1]

		# Write the image to the disk, get the path
		imagePath = self.writeImageToDisk(newImageInfo)

		# Get the hash of the file
		imageHash = self.getFileHash(newImageInfo.imageData)

		# Check if the file is already in the database
		imageId = self.isFileInDatabase(imageHash)
		if imageId == 0:
			# Add Tags to the db
			tagIds = []
			tagIds.append(self.addTagEntry(u'image_path', imagePath))
			tagIds.append(self.addTagEntry(u'image_hash', imageHash))
			for tag in newImageInfo.tags:
				tagIds.append(self.addTagEntry(tag.tagAttribute, tag.tagValue))

			# Add the imageTagPairs to the database
			imageId = self.addImageTagPairEntry(0, tagIds[0])
			for i in range(1, len(tagIds)):
				self.addImageTagPairEntry(imageId, tagIds[i])

		imageInfo = self.get_image_info(imageId)

		evt = puriEvents.addImageToScrollEvent(puriEvents.myEVT_addImageToScroll, -1, imageInfo)
		wx.PostEvent(searchGui.parent.parent.imageScrollPanel, evt)
		self.session.commit()

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
			tagId = self.findTagId(tagAttribute, tagValue)
			#self.session.commit()
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
	
	def findTagLinkId(self, tag1Id, tag2Id):
		tagLink = self.session.query(tagLinkEntry).\
				filter_by(tag1Id=tag1Id).\
				filter_by(tag2Id=tag2Id).\
				first()
		if tagLink == None:
			return -1
		else:
			return tagLink.tagLinkId

	def addTagLink(self, tag1Attribute, tag1Value, tag2Attribute, tag2Value):
		tag1Id = self.addTagEntry(tag1Attribute, tag1Value)
		tag2Id = self.addTagEntry(tag2Attribute, tag2Value)

		tagLinkId = self.findTagLinkId(tag1Id, tag2Id)
		if tagLinkId == -1:
			tagLink = tagLinkEntry(tag1Id=tag1Id, tag2Id=tag2Id)
			self.session.add(tagLink)
			#self.session.commit()
			tagLinkId = self.findTagLinkId(tag1Id, tag1Id)
		return tagLinkId

	def exportTagLinks(self, message):
		allTagLinks = message
		for i in range(0, len(allTagLinks)):
			self.addTagLink(allTagLinks[i][0], allTagLinks[i][1], allTagLinks[i][2], allTagLinks[i][3])
		self.session.commit()

	def importTagLinks(self, message):
		sendbackGui = message
		allTagLinks = self.session.query(tagLinkEntry).all()

		allLinkPairs = []
		for tagLink in allTagLinks:
			tag1 = self.session.query(tagEntry).\
					filter_by(tagId=tagLink.tag1Id).\
					first()
			tag2 = self.session.query(tagEntry).\
					filter_by(tagId=tagLink.tag2Id).\
					first()

			t1 = puriDataStructures.puriImageTag(tag1.tagAttribute, tag1.tagValue)
			t2 = puriDataStructures.puriImageTag(tag2.tagAttribute, tag2.tagValue)
			allLinkPairs.append((t1, t2))

		evt = puriEvents.importTagLinksEvent(puriEvents.myEVT_importTagLinks, -1, allLinkPairs)
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
			#self.session.commit()

		return imageTagPair.imageId


	def addImageTagPairEntry(self, imageId, tagId):
		imageTagPair = imageTagPairEntry(imageId=imageId, tagId=tagId)
		self.session.add(imageTagPair)
		#self.session.commit()
		imageId = self.findImageTagPairEntryId(imageId, tagId)
		return imageId

	def getLinkedTags(self, tag):
		tagId = self.findTagId(tag.tagAttribute, tag.tagValue)
		allLinkedTagInfo = self.session.query(tagLinkEntry).\
			filter(or_(tagLinkEntry.tag1Id==tagId, tagLinkEntry.tag2Id==tagId)).\
			all()

		linkedTags = []
		for i in range(0, len(allLinkedTagInfo)):
			linkInfo = allLinkedTagInfo[i]
			if linkInfo.tag1Id == tagId:
				queryWithId = linkInfo.tag2Id
			else:
				queryWithId = linkInfo.tag1Id
			tag = self.session.query(tagEntry).\
				filter_by(tagId=queryWithId).\
				first()
			if tag != None:
				t = puriDataStructures.puriImageTag(tag.tagAttribute, tag.tagValue)
				linkedTags.append(t)
		return linkedTags


	def getAllTagLinks(self, imageInfo):

		# Get the first level links
		linkedTags = []
		for i in range(0, len(imageInfo.tags)):
			linkedTags += self.getLinkedTags(imageInfo.tags[i])

		loop = 0
		while len(linkedTags) > 0:
			loop += 1
			print 'LOOP - KYON KUN DENWA - %d' % (loop)
			if loop > 100:
				import pdb
				pdb.set_trace()
			# Remove Redundant Tags
			for tag in imageInfo.tags:
				linkedTags = [linkedTag for linkedTag in linkedTags if (tag.tagAttribute != linkedTag.tagAttribute or tag.tagValue != linkedTag.tagValue)]

			# Add Tags
			imageInfo.tags += linkedTags

			# Search for new Tags
			newLinkedTags = []
			for i in range(0, len(linkedTags)):
				newLinkedTags += self.getLinkedTags(linkedTags[i])
			linkedTags = newLinkedTags


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

		imageInfo.imagePath = imageInfo.get_value('image_path')
		self.getAllTagLinks(imageInfo)

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
		self.session.commit()

