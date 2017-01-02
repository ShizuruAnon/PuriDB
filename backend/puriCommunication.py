from Queue import PriorityQueue
import time
import sys

_comm = None
QUEUE_SIZE = 20
def get_communications():
	global _comm
	if _comm == None:
		_comm = communications()
	return _comm

	
class puriQueue(PriorityQueue):
	def __init__(self):
		PriorityQueue.__init__(self, QUEUE_SIZE)

	def send_message(self, messageType, message = None):
		self.put((time.time(), messageType, message))

	def rec_message(self):
		(time, messageType, message) = self.get()
		return (messageType, message)

	def get_send_time(self):
		if len(self.queue) > 0:
			return self.queue[0][0]
		else:
			return sys.float_info.max


class communications():
	def __init__(self):
		self.guiToDatabase = puriQueue()
		self.guiToBrowser = puriQueue()
		self.guiToDownloader = puriQueue()

		self.downloaderToDatabase = puriQueue()
		self.downloaderToBrowser = puriQueue()
		self.downloaderToGui = puriQueue()

		self.browserToDatabase = puriQueue()
		self.browserToDownloader = puriQueue()
		self.browserToGui = puriQueue()

		self.databaseToBrowser = puriQueue()
		self.databaseToDownloader = puriQueue()
		self.databaseToGui = puriQueue()