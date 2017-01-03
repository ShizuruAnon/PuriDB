import sys
import os

# Add Support files to path
sys.path.insert(0, './backend')
sys.path.insert(0, './GUI')

import puriDatabase
import puriDownloader
#import puriThreading
import puriBrowser
import puriGui
import puriDataStructures
import puriCommunication
import wx

def main():

	#puriBrowser.start_browser_manager()
	

	username = 'shizuruanon'
	password = 'tucker22'
	browserOptions = puriDataStructures.puriBrowserOptions()
	browserOptions.username = username
	browserOptions.password = password

	# Initialize Modules
	#database = puriDatabase.get_database('testGuiDownload.db')
	comm = puriCommunication.get_communications()


	# Start Managers
	puriBrowser.start_browser_manager(browserOptions)
	puriDownloader.start_downloader_manager()
	puriDatabase.start_database_manager('testGuiDownload.db')

	# Login
	comm.guiToBrowser.send_message('browser-doLogin')
	
	ex = wx.App()
	puriGui.puriMainFrame(None)
	ex.MainLoop()

if __name__ == '__main__':
	main()