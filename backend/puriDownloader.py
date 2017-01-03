import os

import pdb
import json
import shutil
#import imageInfo
import zipfile
import sys
import urllib

from bs4 import BeautifulSoup

#import puriDatabase
#import puriBrowser
sys.path.insert(0, './../GUI')
import puriCommunication
import pixiv_support
import threading
import wx
import puriEvents


_downloader_manager = None
_downloader = None
def start_downloader_manager():
	global _downloader_manager
	if _downloader_manager == None:
		_downloader_manager = puriDownloaderManager()
		_downloader_manager.start()

class puriDownloaderManager(threading.Thread):
	def __init__(self):
		#self.parent = parent
		threading.Thread.__init__(self)
		self.comm = puriCommunication.get_communications()
		self.loggedIn = False

	def run(self):
		self.downloader = get_puri_downloader()
		while True:
			(sender, messageType, message) = self.get_next_command()
			if sender == '':
				pass
			elif messageType == 'downloader-tag_search':
				ret = self.downloader.tag_search(message)
				self.sendResponse(sender, messageType, ret)
			elif messageType == 'downloader-download_images':
				self.downloader.download_images(message)

	def get_next_command(self):
		sender = ''
		while sender == '':
			browserTime = self.comm.browserToDownloader.get_send_time()
			databaseTime = self.comm.databaseToDownloader.get_send_time()
			guiTime = self.comm.guiToDownloader.get_send_time()
			if (browserTime < databaseTime) and (browserTime < guiTime):
				(messageType, message) = self.comm.browserToDownloader.rec_message()
				sender = 'downloader'
			elif (databaseTime < guiTime):
				(messageType, message) = self.comm.databaseToDownloader.rec_message()
				sender = 'database'
			elif (guiTime != sys.float_info.max):
				(messageType, message) = self.comm.guiToDownloader.rec_message()
				sender = 'gui'
		return (sender, messageType, message)


	def sendResponse(self, dest, messageType, message):
		if dest == 'browser':
			self.comm.downloaderToBrowser.send_message(messageType, message)
		elif dest == 'database':
			self.comm.downloaderToDatabase.send_message(messageType, message)
		elif dest == 'gui':
			self.comm.downloaderToGui.send_message(messageType, message)

def get_puri_downloader():
	global _downloader
	if _downloader == None:
		_downloader = pixiv_image_searcher()
	return _downloader

class pixiv_image_searcher:
	def __init__(self):
		self.website = 'pixiv'
		#self.browser = puriBrowser.getBrowser()
		self.comm = puriCommunication.get_communications()
	
	# Seach from a bunch of tags
	def tag_search(self, message):
		import pdb
		pdb.set_trace()
		searchOptions = message[0]
		self.caller = message[1]
		# Initialize Variables
		continueSearch = True
		page = 0
		responceList = []
		self.imageInfoToDownload = []

		# Search Until no more images are found
		while continueSearch:
			page += 1 # To the next page

			# Generate the Url, open it, then parse it for results
			searchUrl = self.generate_tag_url(page, searchOptions)

			self.comm.downloaderToBrowser.send_message('browser-open', searchUrl)
			messageType, responce = self.comm.browserToDownloader.rec_message()

			pageImageInfo = pixiv_support.parse_tags(responce, searchOptions)

			# Get the URLs and size
			for i in range(0, len(pageImageInfo)):
				self.get_image_url(pageImageInfo[i])
				#pageImageInfo[i] = self.get_images_size(pageImageInfo[i])


			# Add to list of responces from the different pages if there, if not exit
			if len(pageImageInfo) == 0:
				continueSearch = False

			evt = puriEvents.setImagesFoundEvent(puriEvents.myEVT_setImagesFound, -1, len(self.imageInfoToDownload))
			wx.PostEvent(self.caller, evt)

		self.download_images()
		#return (responceList, allImageInfo)

	def encode_unicode_tags(self, tags):
		searchString = ''
		for tag in tags:
			if not tag.startswith('%'):
				tag = tag.encode('utf8')
				tag = urllib.quote_plus(tag)
			searchString += '%20' + tag
		return searchString

	def generate_tag_url(self, page, searchOptions):
		if searchOptions.website == 'Pixiv Tags':
			tags = self.encode_unicode_tags(searchOptions.tags)

			dateParam = ''
			if searchOptions.startDate is not u'':
				dateParam += '&scd=' + searchOptions.startDate
			if searchOptions.endDate is not u'':
				dateParam += '&ecd=' + searchOptions.endDate
			
			url  = 'http://www.pixiv.net/search.php?s_mode=s_tag&p=' + str(page) + '&word=' + tags + dateParam
			
			if searchOptions.rating == 'explicit':
				url += '&r18=1'

			if searchOptions.searchOrder == 'Oldest First':
				url += '&order=date'
			elif searchOptions.searchOrder == 'Oldest Last':
				url += '&order=date_d'
			elif searchOptions.searchOrder == 'Popular First':
				url += '&order=popular_d'
		return url


	# Get the size of the images 
	def get_image_size(self, imageInfo):
		image_type = imageInfo.get_value('image_type')
		if image_type == 'pixiv_mange':
			image_id = imageInfo.get_value('pixiv_manga_id')
		else:
			image_id = imageInfo.get_value('image_id')

		# Make referer link 
		referer = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + image_id
		
		# Create Request
		url = imageInfo.get_value('image_url')
		request = pixiv_support.create_custom_request(url, referer, head=True)
			
		# Send Request and get responce
		self.comm.downloaderToBrowser.send_message('browser-open_novisit', request)
		messageType, responce = self.comm.browserToDownloader.rec_message()
		size = int(responce.info()['Content-Length'])
		imageInfo.add_tag('image_size', size)


	# Get the direct URL of each image
	def get_image_url(self, imageInfo):

		imageType = imageInfo.get_value('image_type')
		imageId = imageInfo.get_value('image_id')
		
		# Get the URL for just a regular image
		if imageType == 'pixiv_image':
			# Create the url for the page the image is on
			postPageUrl = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id='
			postPageUrl += imageId

			# Send request to the page and get the responce
			self.comm.downloaderToBrowser.send_message('browser-open', postPageUrl)
			messageType, responce = self.comm.browserToDownloader.rec_message()

			# Parse the responce to get the image
			soup = BeautifulSoup(responce, 'html.parser')
			result = soup.find('img', {'class':'original-image'})
			
			# Add the url to the list
			imageInfo.add_tag('image_url', result['data-src'])

			self.imageInfoToDownload.append(imageInfo)
			
		# Get the URL for a series of images in a manga post
		elif imageType == 'pixiv_manga':
			imageId = imageInfo.get_value('image_id')
			imageInfo.add_tag('pixiv_manga_id', imageId)
			imageInfo.remove_tag('image_id', imageId)

			# Create the url for the page the image is on
			postPageUrl = 'http://www.pixiv.net/member_illust.php?mode=manga&illust_id='
			postPageUrl += imageId

			# Send request to the page and get the responce
			self.comm.downloaderToBrowser.send_message('browser-open', postPageUrl)
			messageType, responce = self.comm.browserToDownloader.rec_message()

			# Parse the responce to get the images
			soup = BeautifulSoup(responce, 'html.parser')
			imageHtmls = soup.findAll('img', {'data-filter':"manga-image"})
			for i in range(0, len(imageHtmls)):
				tempInfo = imageInfo
				tempInfo.add_tag('image_id', imageId + '_' + str(i))
				tempInfo.add_tag('image_url', imageHtmls[i]['data-src'])
				self.imageInfoToDownload.append(tempInfo)


		# Get the URL for a ugoira image
		elif imageType == 'pixiv_ugoira':

			# Create the url for the page the image is on
			postPageUrl = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id='
			postPageUrl += imageInfo.imageId

			# Send the request to the page and get the responce
			self.comm.downloaderToBrowser.send_message('browser-open', postPageUrl)
			messageType, responce = self.comm.browserToDownloader.rec_message()

			# Parse the request for the url (and also the ugoira data)
			soup = BeautifulSoup(responce, 'html.parser')
			scripts = soup.findAll('script')
			for scr in scripts:
				if scr.text.startswith("pixiv.context.illustId"):
					lines = scr.text.split(";")
					for line in lines:
						if line.startswith("pixiv.context.ugokuIllustFullscreenData"):
							ugoiraData = line.split("=", 2)[1].strip()
							js = json.loads(ugoiraData)
							url = js['src']
							break

			# Add the image to the url list and add the data to the data as well
			imageInfo.add_tag('image_url', url)
			imageInfo.add_tag('ugoira_data', ugoiraData)
			self.imageInfoToDownload.append(imageInfo)


	# Download all the images in the list
	def download_images(self):

		# Get the database
		#database = puriDatabase.get_database()
		count = 0
		# Download all images in list
		for imageInfo in self.imageInfoToDownload:

			if imageInfo.get_value('image_type') == 'pixiv_manga':
				imageId = imageInfo.get_value('pixiv_manga_id')
			else:
				imageId = imageInfo.get_value('image_id')

			# Create the referer
			referer = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + imageId
			
			# Request the image and get the result
			url = imageInfo.get_value('image_url')
			request = pixiv_support.create_custom_request(url, referer)

			self.comm.downloaderToBrowser.send_message('browser-open_novisit', request)
			messageType, downloadingImage = self.comm.browserToDownloader.rec_message()

			# Wait for image to be fully downloaded
			downloadedSize = 0

			# Continue until image is fully downloaded
			self.get_image_size(imageInfo)
			imageSize = imageInfo.get_value('image_size')
			while (downloadedSize < imageSize):

				# Go to back of image and tell position
				downloadingImage.seek(0, 2)
				downloadedSize = downloadingImage.tell()

			# Go back to the front of the image
			downloadingImage.seek(0, 0)

			# Add image to the queue
			imageInfo.imageData = downloadingImage.read()

			# Add the image to the database
			self.comm.downloaderToDatabase.send_message('downloader-addPixivImageToDatabase', (imageInfo, self.caller))
			count += 1
			evt = puriEvents.setImagesDownloadedEvent(puriEvents.myEVT_setImagesDownloaded, -1, count)
			wx.PostEvent(self.caller, evt)