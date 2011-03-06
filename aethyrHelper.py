#!/usr/bin/env python

##########

import os
import re
import shutil
import socket
import sys
import tempfile
import threading
import time
import urllib2

##########

import win32com	
from win32com import client
# psyco broken on py2exe?
# import psyco

##########

def loadStoredDownloadFolder(configFileLocation):
	global downloadFolder
	# check to see if download folder previously configured
	if os.path.exists(configFileLocation):
		with open(configFileLocation, 'r') as config:
			path = config.readline().decode('utf-8')
			print('Previous stored download folder at: %s' % path)
	
		# invalid previous configuration, i.e. folder deleted/removed
		try:
			if os.path.exists(path):
				downloadFolder = path
			else:
				os.remove(configFileLocation)
		# prevent code injection / messing around with .ini file
		except Exception, e:
			print(e)
			os.remove(configFileLocation)

# used to ensure folder/files are created properly
# removes all invalid characters in Windows path
# sets default name to 'Untitled' if filename is blank
# strips off dots off the end (Windows quirk)
def fixFileName(fileName):
	for i in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
		fileName = fileName.replace(i, '_')
	if (len(fileName.strip()) == 0):
		return 'Untitled'
	else:
		return fileName.strip().rstrip('.')

# workaround for lack of iTunes method to grab extension of a song
def determineExtension(filetype):
	extMap = {	'WAV audio file':'.wav',
			'MPEG audio file':'.mp3',
			'Apple Lossless audio file':'.m4a',
			'MPEG-4 audio file':'.m4a',
			'AAC audio file':'.m4a',
			'Purchased AAC audio file':'.m4a'
			# future support for video files
#			'MPEG-4 video file':'.m4v',
#			'Purchased MPEG-4 video file':'.m4v'		
#			'Quicktime movie file':'.mp4'
									}
	try:
		extension = extMap[filetype]
	except KeyError:
		extension = '.mp3'
	return extension

# returns (file handle, string location)
def newTemporaryFile():
	handle, location = tempfile.mkstemp()
	print('Creating temporary file at: %s' % location)
	return os.fdopen(handle, 'wb'), location

# begin waiting for iTunes request
class CapturePacket(threading.Thread):
	def __init__(self, socket):
		threading.Thread.__init__(self)
		self.socket = socket
		self.url = None
		self.packetHeaders = {}

	def run(self):
		while(self.url is None):
			# loop to non-blocking-ly read from socket
			try:
				info = self.socket.recvfrom(65535)[0]
			except Exception:
				continue
			
			# iTunes is up to something
			if (info.find('GET daap://') != -1):
				print('')
				print('Captured Packet:')
				print(info)
				# is it a stream request?
				try:
					url = 'http://' + re.compile('daap://([^/]*/databases.*?) HTTP').search(info).group(1)
				except AttributeError:
					pass
				else:
					self.url = url
					print ('Using URL:               %s' % url)
					
					requestID = (int)(re.compile('Client-DAAP-Request-ID: (.*)').search(info).group(1))
					requestID += 1
					self.packetHeaders['Client-DAAP-Request-ID'] = (str)(requestID)
					print ('Using DAAP Request ID:   %s' % requestID)

					udpPort = re.compile('x-audiocast-udpport: (.*)').search(info).group(1)
					self.packetHeaders['x-audiocast-udpport'] = udpPort
					print ('Using UDP Port:          %s' % udpPort)
					
					# other client is iTunes
					try:
						daapValidation = re.compile('Client-DAAP-Validation: (.*)').search(info).group(1)
						self.packetHeaders['Client-DAAP-Validation'] = daapValidation
						print ('Using DAAP Validation:   %s' % verificationKey)
					# non-iTunes? (currently tested with Firefly'd iTouch)
					except AttributeError:
						try:
							accessIndex = re.compile('Client-DAAP-Access-Index: (.*)').search(info).group(1)
							self.packetHeaders['Client-DAAP-Access-Index'] = accessIndex
							print ('Using DAAP Access Index: %s' % accessIndex)
						except Exception, e:
							print('Exception thrown while copying request: %s' % str(e))

	def kill(self):
		# terminates while loop
		self.url = 0
	
	def getURL(self):
		return self.url

	def getPacketHeaders(self):
		return self.packetHeaders
	
class Download(threading.Thread):
	def __init__(self, url, packetHeaders):
		threading.Thread.__init__(self)
		self.url = url
		self.packetHeaders = packetHeaders
		self.disconnectionError = False
		self.exception = False
			
	def run(self):
		# forge a fake iTunes request
		req = urllib2.Request(self.url)

		for authenticationElement in self.packetHeaders.keys():
			req.add_header(authenticationElement, self.packetHeaders[authenticationElement])
	
		# allows pulling certain chunks of a song...fallback workaround if iTunes actually begins 'streaming'
#		req.add_header('Range', 'bytes=0-5000')
	
		# we create a temporary file first in case we can't read from the file, transfer gets interrupted, etc.
		mp3Buffer, mp3BufferLocation = newTemporaryFile()	
		startTime = time.clock()
	
		# try to download
		try:
			mp3Buffer.write(urllib2.urlopen(req).read())
		# iTunes doesn't like our fake request
		except urllib2.HTTPError, e:
			mp3Buffer.close()
			os.remove(mp3BufferLocation)
			self.exception = True
			print('Exception: ' + str(e))
			print('--------------Wrong Code------------')
		# the other library disconnected
		except socket.error:
			mp3Buffer.close()
			os.remove(mp3BufferLocation)
			self.disconnectionError = True
		# catch-all protection
		except Exception, e:
			mp3Buffer.close()
			os.remove(mp3BufferLocation)
			self.exception = True
			print('Exception: ' + str(e))
		# download successful!
		else:
			mp3Buffer.close()
			
			endTime = time.clock()
			
			self.timeSpent = endTime - startTime
			self.mp3BufferLocation = mp3BufferLocation
		
	def getMp3BufferLocation(self):
		return self.mp3BufferLocation
	
	def getTimeSpent(self):
		return self.timeSpent
	
	def isDisconnectionError(self):
		return self.disconnectionError
	
	def isException(self):
		return self.exception

def updateTotalTime(timeSpent):
	global totalTime
	totalTime += timeSpent

def updateTotalSize(size):
	global totalSize
	totalSize += size

def checkDownloadFolderIntegrity():
	print('Download folder located at: %s' % downloadFolder)
	# creation if it doesn't exist; reset if not allowed
	if os.path.exists(downloadFolder) is False:
		try:
			os.mkdir(downloadFolder)
		except WindowsError:
			resetDefaultFolder()
	isWritableCheck(downloadFolder + 'aethyrConfig.ini')

def isWritableCheck(fileLocation):
	try:
		with open(fileLocation, 'wb') as fileHandle:
			fileHandle.write('asdf')
	except IOError:
		resetDefaultFolder()
	else:
		os.remove(fileLocation)


# reset download folder back to My Documents\Aethyr			
def resetDefaultFolder():
	global downloadFolder
	downloadFolder = myDocs + 'Aethyr\\'
	# delete config file if it exists
	try:
		os.remove(configFileLocation)
	except Exception:
		pass
	# creation
	if os.path.exists(downloadFolder) is False:
		os.mkdir(downloadFolder)

def writeFromBufferToSystem(mp3BufferLocation, downloadFolder, artist, album, title, size, extension):
	artistFolder = downloadFolder + artist
	if os.path.exists(artistFolder) is False:
		os.mkdir(artistFolder)
	albumFolder = artistFolder + '\%s' % album
	if os.path.exists(albumFolder) is False:
		os.mkdir(albumFolder)
		
	shutil.move(mp3BufferLocation, downloadFolder + '%s\%s\%s' % (artist, album, title) + extension)

def printSongInfo(title, artist, album, size, type, extension, downloadNumber, numberOfDownloads):
	print('(%i/%i)' % ((int)(downloadNumber) + 1, numberOfDownloads))
	print('Title:     %s' % title.encode('utf-8'))
	print('Artist:    %s' % artist.encode('utf-8'))
	print('Album:     %s' % album.encode('utf-8'))
	print('Size:      %i' % size)
	print('Type:      %s' % type.encode('utf-8'))
	print('Extension: %s' % extension.encode('utf-8'))
	
def printTotalStats():
	print('\n\n\nTotal Bandwidth:        %s MB' % str(totalSize/1048576.0)[:8])
	print('Total Download Time:    %s seconds' % str(totalTime)[:8])
	if totalTime != 0:
		print('Average Download Speed: %s MB/s' % str(totalSize/(1048576*totalTime))[:8])
	else:
		print('Average Download Speed: 0.000000 MB/s')

def updateFlashWithDownloadInfo(downloadNumber, numberOfSongsToDownload):
	total_bandwidth = str(totalSize/1048576.0)[:STATACCURACY]
	total_time = str(totalTime)[:STATACCURACY]
	
	if totalTime != 0:
		avg_speed = str(totalSize/(1048576*totalTime))[:STATACCURACY]
	else:
		avg_speed = '0.000000'

	# give update status to flash
	try:
		flashConnection.send(DELIMITER.join([str(int(downloadNumber)) + '/' + str(numberOfSongsToDownload), total_bandwidth, total_time, avg_speed, data]))
	except socket.error:
		errorFlashClientFail()
		
def isAlreadyExists(downloadFolder, artist, album, title, extension):
	return os.path.exists('%s%s\%s\%s%s' % (downloadFolder, artist, album, title, extension))
			
def isWrongType(type):
	return (type.find('Protected') != -1 or type.find('Internet') != -1 or type.find('video') != -1)

def processQueue(currentTracks, indicesToDownload):
	print('')
	print(indicesToDownload)
	filesSkipped = False
	disconnectionError = False

	# attempt to reset internal iTunes counter
	iTunes.Play()
	iTunes.Stop()
	
	numberOfSongsToDownload = len(indicesToDownload)
	
	for downloadNumber in range(numberOfSongsToDownload):
		try:
			songIndex = indicesToDownload[downloadNumber]
			currentSong = currentTracks[songIndex]
			
			title = currentSong.Name
			artist = currentSong.Artist
			album = currentSong.Album
			size = currentSong.Size
			type = currentSong.KindAsString
			extension = determineExtension(type)
		except Exception:
			print('Other library disconnected')
			disconnectionError = True
			break

		printSongInfo(title, artist, album, size, type, extension, downloadNumber, numberOfSongsToDownload)
		updateFlashWithDownloadInfo(downloadNumber, numberOfSongsToDownload)
		
		artist = fixFileName(artist)
		album = fixFileName(album)
		title = fixFileName(title)
		
		if(isAlreadyExists(downloadFolder, artist, album, title, extension)):
			print('Already downloaded, skipping!\n')
			continue

		if(isWrongType(type)):
			print('Song is protected or is non-audio, skipping!\n')
			filesSkipped = True
			continue

		# begin waiting
		capture = CapturePacket(iTunesSock)
		capture.start()
		
		# bait it out...
		try:
			currentSong.Play()
		except Exception, e:
			print(str(e))
			print('File missing!\n')
			# flip killswitch for thread
			capture.kill()
			# tell flash something's up
			filesSkipped = True
			continue
			
		# wait until parsing is complete
		capture.join()
			
		# shut up
		iTunes.Stop()

		# wait until download is complete
		downloadThread = Download(capture.getURL(), capture.getPacketHeaders())
		downloadThread.start()
		downloadThread.join()
		
		if (downloadThread.isDisconnectionError()):
			disconnectionError = True
			break
		
		if (downloadThread.isException()):
			filesSkipped = True
			continue
		
		updateTotalTime(downloadThread.getTimeSpent())
		updateTotalSize(size)
		
		writeFromBufferToSystem(downloadThread.getMp3BufferLocation(), downloadFolder, artist, album, title, size, extension)

		# fix internal iTunes song offset to accomadate for fake request
		iTunes.Play()
		iTunes.Stop()
		
		print('')
		printTotalStats()
		
	return filesSkipped, disconnectionError

def errorDisconnection():
	print('Disconnection Error')
	
	# remove library from cache in case it changes
	del(alreadyLoaded[currentLibrary])
	try:
		flashConnection.send('refreshLibraryList' + data)
	except socket.error:
		errorFlashClientFail()

def errorFlashClientFail():
	print('Flash Client Fail')

	# fatal, shutdown
	flashSock.close()
	iTunesSock.close()
	sys.exit()

##########

# disable py2exe log feature by routing stdout/sterr to the special nul file
if hasattr(sys, 'frozen'):
	sys.stdout = open('nul', 'w')
	sys.stderr = open('nul', 'w')

# rebuild cache file for iTunes COM if it doesn't exist
if win32com.client.gencache.is_readonly == True:
	win32com.client.gencache.is_readonly = False
	win32com.client.gencache.Rebuild()

# make a COM object
iTunes = win32com.client.gencache.EnsureDispatch('iTunes.Application')

# psyco optimization
# psyco.full()

# find My Documents
objShell = win32com.client.Dispatch('WScript.Shell')
myDocs = objShell.SpecialFolders('MyDocuments') + '\\'
print('My Documents is located at: %s' % myDocs)

# default downloadFolder is My Documents\Aethyr
downloadFolder = myDocs + 'Aethyr\\'

# config file holding location of download folder
configFileLocation = myDocs + 'aethyr.ini'

loadStoredDownloadFolder(configFileLocation)

totalSize = 0
totalTime = 0

# dictionary for caching libraries
alreadyLoaded = {}

# seperating elements of an array
DELIMITER = '&&&'

# seperating array elements of an array, i.e. different categories
BIGDELIMITER = '$598074$'

#currentLibrary = ""

# port used for all Aethyr comm
PORT = 59807

# numerical accuracy for stats
STATACCURACY = 8

checkDownloadFolderIntegrity()

iTunesSock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
iTunesSock.bind((socket.gethostbyname(socket.gethostname()), 0))
iTunesSock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
iTunesSock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

flashSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
flashSock.bind(('127.0.0.1', PORT))
flashSock.listen(1)

# 60 second connection to flash timeout so aethyrHelper doesn't live forever
flashSock.settimeout(60)

# launch flash frontend
os.startfile(os.path.abspath("aethyrBin.exe"))

# wait for flash to connect
try:
	flashConnection, address = flashSock.accept()
except socket.error, e:
	print('Exception while connecting to Flash: ' + str(e))
	errorFlashClientFail()
	
# remove timeout
flashSock.setblocking(1)
flashConnection.setblocking(1)

# must be non-blocking to utilize threads properly
iTunesSock.setblocking(0)

##########

while(True):
#	print(flashSock.getpeername())

	# why is this 4096?
	data = flashConnection.recv(4096)

	print(data)

	if(data.find('downloadProgress') != -1):
		print('Downloading...')
		
		downSet = [int(x) for x in data[len('downloadProgress' + DELIMITER):-1].split(DELIMITER)]
		filesSkipped, disconnectionError = processQueue(tracks, downSet)
		
		if(disconnectionError):
			errorDisconnection()
		
		total_bandwidth = str(totalSize/1048576.0)[:STATACCURACY]
		total_time = str(totalTime)[:STATACCURACY]
		
		if totalTime != 0:
			avg_speed = str(totalSize/(1048576*totalTime))[:STATACCURACY]
		else:
			avg_speed = '0.000000'

		# give flash update status
		try:
			flashConnection.send(DELIMITER.join([str(len(downSet)) + '/' + str(len(downSet)), total_bandwidth, total_time, avg_speed, 'finishedDownload', data]))
		except socket.error:
			errorFlashClientFail()

		# something didn't download
		if filesSkipped == True:
			try:
				flashConnection.send('protectedFiles' + DELIMITER + data)
			except socket.error:
				errorFlashClientFail()

	if(data.find('getiTunesLibraries') != -1):
		# only add shared libraries
		libraries = [i.Name for i in list(iTunes.Sources) if i.Kind == 7]
#		libraries = [i.Name for i in list(iTunes.Sources)[2:]]

		print(libraries)

		# prepare and send data
		ret = DELIMITER.join(libraries)
		ret = DELIMITER.join([ret, data])
		try:
			flashConnection.send(ret.encode('utf-8'))
		except socket.error:
			errorFlashClientFail()

	if(data.find('changeDownloadDirectory') != -1):
		path = data.split(DELIMITER)[1][:-1] + '\\'
		
		downloadFolder = path.decode('utf-8')

		with open(configFileLocation, 'w') as config:
			config.write(downloadFolder)
			
		checkDownloadFolderIntegrity()

	if(data.find('loadLibrary') != -1):
		# format: loadLibrary<DELIMITER>1
		downloadNumber = int((data.split(DELIMITER)[1])[:-1])
		
		currentLibrary = libraries[downloadNumber]
		print(currentLibrary.encode('utf-8'))
		
		startTime = time.time()
		try:
			# is it cached?
			if (currentLibrary in alreadyLoaded) is False:
				# parse the library
				otherLib = iTunes.Sources.ItemByName(currentLibrary).Playlists(1)
				tracks = list(otherLib.Tracks)
				(titles, artists, albums) = (DELIMITER.join([song.Name for song in tracks]), DELIMITER.join([song.Artist for song in tracks]), DELIMITER.join([song.Album for song in tracks]))
				ret = BIGDELIMITER.join([titles, artists, albums, data])
				alreadyLoaded[currentLibrary] = (ret, tracks)
			else:
				# load from cache
				ret = alreadyLoaded[currentLibrary][0]
				tracks = alreadyLoaded[currentLibrary][1]
		# something messed up somehow
		except AttributeError:
			try:
				flashConnection.send('refreshLibraryList' + data)
			except socket.error:
				errorFlashClientFail()
		# notify flash of completion
		try:
			flashConnection.send(ret.encode('utf-8'))
		except socket.error:
			errorFlashClientFail()
			
		print(time.time() - startTime)
		
	if(data.find('aethyrEXIT') != -1):
		# shutdown time
		flashSock.close()
		iTunesSock.close()
		sys.exit()
