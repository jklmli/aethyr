import os
import socket
import sys
import time

##########

import win32com	
from win32com import client

##########

import CapturePacket
import Download
import Error
import ForgePacket
import Helper

##########

def sendToFlash(message):
    try:
        flashConnection.send(message.encode('utf-8'))
    except socket.error:
        Error.flashClientFail(flashSock, iTunesSock)

def updateTotalTime(timeSpent):
	global totalTime
	totalTime += timeSpent

def updateTotalSize(size):
	global totalSize
	totalSize += size

def updateFlashWithDownloadInfo(downloadNumber, numberOfSongsToDownload):
	totalBandwidthTruncated = str(totalSize/1048576.0)[:STATACCURACY]
	totalTimeTruncated = str(totalTime)[:STATACCURACY]
	
	if totalTime != 0:
		averageSpeedTruncated = str(totalSize/(1048576*totalTime))[:STATACCURACY]
	else:
		averageSpeedTruncated = '0.000000'

	# give update status to flash
	sendToFlash(DELIMITER.join([
				str(int(downloadNumber)) + '/' + str(numberOfSongsToDownload),
				totalBandwidthTruncated, totalTimeTruncated, averageSpeedTruncated, data
		]))

def processQueue(currentTracks, indicesToDownload):
	print('')
	print(indicesToDownload)
	filesSkipped = False
	disconnectionError = False
	
	numberOfSongsToDownload = len(indicesToDownload)
	
	for downloadNumber in range(numberOfSongsToDownload):
		
		try:
			songIndex = indicesToDownload[downloadNumber]
			currentSong = currentTracks[songIndex]
			currentDownload = Download.Download(currentSong, downloadNumber, 
										numberOfSongsToDownload, downloadFolder)
		except Exception, e:
			print(str(e))
			print('Other library disconnected')
			disconnectionError = True
			break

		currentDownload.printSongInfo()
		updateFlashWithDownloadInfo(downloadNumber, numberOfSongsToDownload)
		
		currentDownload.artist = Helper.fixFileName(currentDownload.artist)
		currentDownload.album = Helper.fixFileName(currentDownload.album)
		currentDownload.title = Helper.fixFileName(currentDownload.title)
		
		if(currentDownload.isAlreadyExists()):
			print('Already downloaded, skipping!\n')
			continue

		if(currentDownload.isWrongType()):
			print('Song is protected or is non-audio, skipping!\n')
			filesSkipped = True
			continue

		# reset internal iTunes counter
		currentSong.Play()
		iTunes.Stop()
		
		# begin waiting
		capture = CapturePacket.CapturePacket(iTunesSock)
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

		# wait until currentDownload is complete
		downloadThread = ForgePacket.ForgePacket(capture.getURL(), 
									 capture.getPacketHeaders())
		downloadThread.start()
		downloadThread.join()
		
		if (downloadThread.isDisconnectionError()):
			disconnectionError = True
			break
		
		if (downloadThread.isException()):
			filesSkipped = True
			continue
		
		updateTotalTime(downloadThread.getTimeSpent())
		updateTotalSize(currentDownload.size)
		
		currentDownload.writeFromTempToDownloadFolder(downloadThread.getMp3BufferLocation())

		# fix internal iTunes song offset to accomadate for fake request
		iTunes.Play()
		iTunes.Stop()
		
		print('')
		currentDownload.printTotalStats(totalSize, totalTime)
		
	return filesSkipped, disconnectionError

##########

# disable py2exe log feature by routing stdout/sterr to the special nul file
if hasattr(sys, 'frozen'):
	sys.stdout = open('nul', 'w')
	sys.stderr = open('error.log', 'a')

# rebuild cache file for iTunes COM if it doesn't exist
if win32com.client.gencache.is_readonly == True:
	win32com.client.gencache.is_readonly = False
	win32com.client.gencache.Rebuild()

# make a COM object
iTunes = win32com.client.gencache.EnsureDispatch('iTunes.Application')

# find My Documents
objShell = win32com.client.Dispatch('WScript.Shell')
myDocs = objShell.SpecialFolders('MyDocuments') + '\\'
print('My Documents is located at: %s' % myDocs)

# default downloadFolder is My Documents\Aethyr
downloadFolder = myDocs + 'Aethyr\\'

# config file holding location of download folder
configFileLocation = myDocs + 'aethyr.ini'

storedLocation = Download.loadStoredDownloadFolder(configFileLocation)

if (storedLocation is not None):
	downloadFolder = storedLocation
	
if (not Helper.isFolderIntegrityOK(downloadFolder)):
	downloadFolder = Download.resetDefaultDownloadFolder(myDocs, configFileLocation)

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
if hasattr(sys, 'frozen'):
	os.startfile(os.path.abspath("AethyrBin.exe"))

# wait for flash to connect
try:
	flashConnection, address = flashSock.accept()
except socket.error, e:
	print('Exception while connecting to Flash: ' + str(e))
	Error.flashClientFail(flashSock, iTunesSock)
	
# remove timeout
flashSock.setblocking(1)
flashConnection.setblocking(1)

# must be non-blocking to utilize threads properly
iTunesSock.setblocking(0)

if (Helper.isNeedUpdate()):
	sendToFlash('needToUpdateClient' + DELIMITER)

##########

while(True):
#	print(flashSock.getpeername())

	# why is this 4096?
	try:
		data = flashConnection.recv(4096)
	except socket.error:
		Error.flashClientFail(flashSock, iTunesSock)

	print('Command from Flash: %s' % data)

	if(data.find('downloadProgress') != -1):
		print('Downloading...')
		
		downSet = [int(x) for x in 
				data[len('downloadProgress' + DELIMITER):-1].split(DELIMITER)]
		
		filesSkipped, disconnectionError = processQueue(tracks, downSet)
		
		if(disconnectionError):
			Error.disconnection(alreadyLoaded, currentLibrary, 
							flashConnection, flashSock, iTunesSock)
		
		totalBandwidthTruncated = str(totalSize/1048576.0)[:STATACCURACY]
		totalTimeTruncated = str(totalTime)[:STATACCURACY]
		
		if totalTime != 0:
			averageSpeedTruncated = str(totalSize/(1048576*totalTime))[:STATACCURACY]
		else:
			averageSpeedTruncated = '0.000000'

		sendToFlash(DELIMITER.join([str(len(downSet)) + '/' + str(len(downSet)), 
								totalBandwidthTruncated, totalTimeTruncated,
								averageSpeedTruncated, 'finishedDownload', data]))

		# something didn't download
		if (filesSkipped == True):
			sendToFlash('filesMissing')

	if (data.find('getiTunesLibraries') != -1):
		libraries = Helper.getiTunesLibraries(iTunes.Sources)
		# prepare and send data
		allLibrariesSerialized = DELIMITER.join(libraries)
		allLibrariesSerialized = DELIMITER.join([allLibrariesSerialized, data])
		sendToFlash(allLibrariesSerialized)

	if (data.find('changeDownloadDirectory') != -1):
		path = data.split(DELIMITER)[1][:-1] + '\\'
		path = path.decode('utf-8')

		downloadFolder = Helper.changeDownloadDirectory(path, configFileLocation)

	if(data.find('loadLibrary') != -1):
		# format: loadLibrary<DELIMITER>1
		downloadNumber = int((data.split(DELIMITER)[1])[:-1])
		currentLibrary = libraries[downloadNumber]
		
		print('Library loaded: %s' % currentLibrary.encode('utf-8'))
		
		startTime = time.time()
		try:
			# is it cached?
			if (currentLibrary not in alreadyLoaded):
				# parse the library
				otherLib = iTunes.Sources.ItemByName(currentLibrary).Playlists(1)
				tracks = list(otherLib.Tracks)
				
				(titles, artists, albums) = (
					DELIMITER.join([song.Name for song in tracks]), 
					DELIMITER.join([song.Artist for song in tracks]), 
					DELIMITER.join([song.Album for song in tracks])
				)
				
				currentLibrarySerialized = BIGDELIMITER.join([titles, artists, albums, data])
				alreadyLoaded[currentLibrary] = (currentLibrarySerialized, tracks)
			else:
				# load from cache
				currentLibrarySerialized = alreadyLoaded[currentLibrary][0]
				tracks = alreadyLoaded[currentLibrary][1]
		# something messed up somehow
		except AttributeError:
			sendToFlash('refreshLibraryList')
		# notify flash of completion
		else:
			sendToFlash(currentLibrarySerialized)
			
		print('Library loading time: %s' % (time.time() - startTime))
		
	if(data.find('aethyrEXIT') != -1):
		Helper.shutdown(flashSock, iTunesSock)
