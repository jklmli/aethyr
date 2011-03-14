import os
import shutil

#####

import Helper

#####

def loadStoredDownloadFolder(configFileLocation):
	# check to see if download folder previously configured
	if os.path.exists(configFileLocation):
		with open(configFileLocation, 'r') as config:
			path = config.readline().decode('utf-8')
			print('Previous stored download folder at: %s' % path)

		# invalid previous configuration, i.e. folder deleted/removed
		try:
			if os.path.exists(path):
					return path
			else:
					os.remove(configFileLocation)
		# prevent code injection / messing around with .ini file
		except Exception, e:
			print(e)
			os.remove(configFileLocation)

# reset download folder back to My Documents\Aethyr
def resetDefaultDownloadFolder(myDocs, configFileLocation):
	downloadFolder = myDocs + 'Aethyr\\'
	# delete config file if it exists
	try:
		os.remove(configFileLocation)
	except Exception:
		pass
	# creation
	if os.path.exists(downloadFolder) is False:
		os.mkdir(downloadFolder)
	return downloadFolder

#####

class Download:
	def __init__(self, iTunesSong, downloadNumber,
							 numberOfSongsToDownload, downloadFolder):
		self.downloadNumber = downloadNumber
		self.numberOfSongsToDownload = numberOfSongsToDownload
		self.downloadFolder = downloadFolder
		self.title = iTunesSong.Name
		self.artist = iTunesSong.Artist
		self.album = iTunesSong.Album
		self.size = iTunesSong.Size
		self.type = iTunesSong.KindAsString
		self.extension = Helper.determineExtension(type)

	def printSongInfo(self):
		print('(%i/%i)' % ((int)(self.downloadNumber) + 1,
								 self.numberOfSongsToDownload))
		print('Title:     %s' % self.title.encode('utf-8'))
		print('Artist:    %s' % self.artist.encode('utf-8'))
		print('Album:     %s' % self.album.encode('utf-8'))
		print('Size:      %i' % self.size)
		print('Type:      %s' % self.type.encode('utf-8'))
		print('Extension: %s' % self.extension.encode('utf-8'))

	def printTotalStats(self, totalSize, totalTime):
		print('\n\n\nTotal Bandwidth: %s MB' % str(totalSize/1048576.0)[:8])
		print('Total Download Time: %s seconds' % str(totalTime)[:8])
		if totalTime != 0:
			print('Average Download Speed: %s MB/s' %
								str(totalSize/(1048576*totalTime))[:8])
		else:
			print('Average Download Speed: 0.000000 MB/s')

	def isAlreadyExists(self):
		return os.path.exists('%s%s\%s\%s%s' %
				(self.downloadFolder, self.artist, self.album,
				 self.title, self.extension))

	def isWrongType(self):
		return (self.type.find('Protected') != -1 or
				self.type.find('Internet') != -1 or
				self.type.find('video') != -1 or
				self.type.find('QuickTime') != -1)

	def writeFromTempToDownloadFolder(self, mp3BufferLocation):
		artistFolder = self.downloadFolder + self.artist
		if os.path.exists(artistFolder) is False:
			os.mkdir(artistFolder)
		albumFolder = artistFolder + '\%s' % self.album
		if os.path.exists(albumFolder) is False:
			os.mkdir(albumFolder)

		shutil.move(mp3BufferLocation, self.downloadFolder +
						'%s\%s\%s' % (self.artist, self.album, self.title) +
						self.extension)
