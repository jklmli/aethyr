#!/usr/bin/env python

##########

import os
import re
import shutil
import socket
import sys
import tempfile
from threading import Thread
import time
import urllib2

##########

import win32com	
from win32com import client
import psyco

##########

# disable py2exe log feature by routing stdout/sterr to the special nul file
#if hasattr(sys, 'frozen'):
#	sys.stdout = open('nul', 'w')
#	sys.stderr = open('nul', 'w')

# rebuild cache file for iTunes COM if it doesn't exist
if win32com.client.gencache.is_readonly == True:
	win32com.client.gencache.is_readonly = False
	win32com.client.gencache.Rebuild()

# make a COM object
iTunes = win32com.client.gencache.EnsureDispatch('iTunes.Application')

# psyco optimization
psyco.full()

# find My Documents
objShell = win32com.client.Dispatch('WScript.Shell')
myDocs = objShell.SpecialFolders('MyDocuments') + '\\'
print(myDocs)

# default downloadFolder is My Documents\Aethyr
downloadFolder = myDocs + 'Aethyr\\'

# check to see if download folder previously configured
if os.path.exists(myDocs + 'aethyr.ini'):
	config = open(myDocs + 'aethyr.ini', 'r')
	path = config.readline().decode('utf-8')
	print(path)
	config.close()

	# invalid previous configuration, i.e. folder deleted/removed
	try:
		if os.path.exists(path):
			downloadFolder = path
		else:
			os.remove(myDocs + 'aethyr.ini')
	# prevent code injection / messing around with .ini file
	except Exception:
		os.remove(myDocs + 'aethyr.ini')
		
print(downloadFolder)

totalSize = 0
totalTime = 0

# flag for successful song parse
isFound = False

# flag for specific iTunes exception during download
protectedFiles = False

# dictionary for caching libraries
alreadyLoaded = {}

# seperating elements of an array
delimiter = '&&&'

# seperating array elements of an array, i.e. different categories
bigDelimiter = '$598074$'

#currentLibrary = ""

# port used for all Aethyr comm
PORT = 59807

##########

# used to ensure folder/files are created properly
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
	print(extension)
	return extension

# returns (file handle, string location)
def newTemporaryFile():
	handle, location = tempfile.mkstemp()
	print(location)
	return os.fdopen(handle, 'wb'), location

# begin waiting for iTunes request
def capture(downloadFolder, artist, album, title, size, extension):
	global isFound
	global protectedFiles
	global totalTime
	global totalSize

	isFound = False
	
	while(isFound is False):
		# loop to non-blocking-ly read from socket
		try:
			info = iTunesSock.recvfrom(4096)[0]
		except Exception:
			continue
			
		# iTunes is up to something
		if (info.find('daap') != -1):
			print(info)
			# is it a stream request?
			try:
				url = 'http://' + re.compile('daap://([^/]*/databases.*?) HTTP').search(info).group(1)
				print url
			except AttributeError:
				pass
			else:
				# found song, terminate loop after this completion
				isFound = True

				# the only two parts iTunes cares about
				code = re.compile('Client-DAAP-Validation: (.*)').search(info).group(1)
				idd = (int)(re.compile('Client-DAAP-Request-ID: (.*)').search(info).group(1)) + 1
				
				print code
				print idd

				# forge a fake iTunes request
				req = urllib2.Request(url)
				req.add_header('Client-DAAP-Validation', code)
				req.add_header('Client-DAAP-Request-ID', (str)(idd))

				# allows pulling certain chunks of a song...fallback workaround if iTunes actually begins 'streaming'
#				req.add_header('Range', 'bytes=0-5000')

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
					print(e)
					print('--------------Wrong Code------------')
					break
				# the other library disconnected
				except socket.error:
					mp3Buffer.close()
					os.remove(mp3BufferLocation)
					eventDisconnection()
					break
				# catch-all protection
				except Exception, e:
					mp3Buffer.close()
					os.remove(mp3BufferLocation)
					protectedFiles = True
					print('Exception: ' + str(e))
					break
				# download successful!
				else:
					mp3Buffer.close()
					
					endTime = time.clock()
					totalTime += endTime - startTime
					totalSize += size
					
					artistFolder = downloadFolder + artist
					if os.path.exists(artistFolder) is False:
						os.mkdir(artistFolder)
					albumFolder = artistFolder + '\%s' % album
					if os.path.exists(albumFolder) is False:
						os.mkdir(albumFolder)
						
					shutil.move(mp3BufferLocation, downloadFolder + '%s\%s\%s' % (artist, album, title) + extension)

def cleanTmp():
	print(downloadFolder)
	# creation if it doesn't exist; reset if not allowed
	if os.path.exists(downloadFolder) is False:
		try:
			os.mkdir(downloadFolder)
		except WindowsError:
			resetDefaultFolder()
	isWritableCheck(downloadFolder + 'aethyrConfig.ini')

def isWritableCheck(document):
	try:
		tmpFile = open(document, 'wb')
		tmpFile.write('asdf')
	except IOError:
		resetDefaultFolder()
	else:
		tmpFile.close()
		os.remove(document)


# reset download folder back to My Documents\Aethyr			
def resetDefaultFolder():
	global downloadFolder
	downloadFolder = myDocs + 'Aethyr\\'
	# delete config file if it exists
	try:
		os.remove(myDocs + 'aethyr.ini')
	except Exception:
		pass
	# creation
	if os.path.exists(downloadFolder) is False:
		os.mkdir(downloadFolder)
	
def download(results, indexList):
	global isFound
	global protectedFiles
	
	print('')
	print(indexList)
	protectedFiles = False

	# attempt to reset internal iTunes counter
	iTunes.Play()
	iTunes.Stop()
	
	for index in range(len(indexList)):
		try:
			title = results[indexList[index]].Name
			artist = results[indexList[index]].Artist
			album = results[indexList[index]].Album
			size = results[indexList[index]].Size
			filetype = results[indexList[index]].KindAsString
			extension = determineExtension(filetype)
		except Exception:
			print('Other library disconnected')
			eventDisconnection()
			break
			
		print(filetype)
		print('(%i/%i)' % ((int)(index) + 1, len(indexList)))

		total_bandwidth = str(totalSize/1048576.0)[:8]
		total_time = str(totalTime)[:8]
		
		if totalTime != 0:
			avg_speed = str(totalSize/(1048576*totalTime))[:8]
		else:
			avg_speed = '0.000000'

		# give update status to flash
		try:
			conn.send(delimiter.join([str(int(index)) + '/' + str(len(downSet)), total_bandwidth, total_time, avg_speed, data]))
		except socket.error:
			flashClientFail()
			
		index = indexList[index]

		print('Title:  %s' % title.encode('utf-8'))
		print('Artist: %s' % artist.encode('utf-8'))
		print('Album:  %s' % album.encode('utf-8'))
		print('Size:   %i' % size)
		print('Type:   %s' % filetype.encode('utf-8'))

		artist = fixFileName(artist)
		album = fixFileName(album)
		title = fixFileName(title)
		
		if(os.path.exists(downloadFolder + '%s\%s\%s' % (artist, album, title) + extension)):
			print('Already downloaded, skipping!\n')
			continue

		if(filetype.find('Protected') != -1 or filetype.find('Internet') != -1 or filetype.find('video') != -1):
			print('Song is protected or is non-audio, skipping!\n')
			protectedFiles = True
			continue

		# begin waiting
		download = Thread(target=capture, args=(downloadFolder, artist, album, title, size, extension))
		download.start()

		# bait it out...
		try:
			results[index].Play()
		except Exception, e:
			print(str(e))
			print('File missing!\n')
			# flip killswitch for thread
			isFound = True
			# tell flash something's up
			protectedFiles = True
			continue
			
		# wait until parsing is complete
		while isFound is False:
			pass
			
		# shut up
		iTunes.Stop()

		# wait until download is complete
		download.join()

		# fix internal iTunes song offset to accomadate for fake request
		iTunes.Play()
		iTunes.Stop()
			
	print('\n\n\nTotal Bandwidth:        %s MB' % str(totalSize/1048576.0)[:8])
	print('Total Download Time:    %s seconds' % str(totalTime)[:8])
	if totalTime != 0:
		print('Average Download Speed: %s MB/s' % str(totalSize/(1048576*totalTime))[:8])
	else:
		print('Average Download Speed: 0.000000 MB/s')

def eventDisconnection():
	print('Disconnection Error')
	
	# remove library from cache in case it changes
	del(alreadyLoaded[currentLibrary])
	try:
		conn.send('refreshLibraryList' + data)
	except socket.error:
		flashClientFail()

def flashClientFail():
	print('Flash Client Fail')

	# fatal, shutdown
	flashSock.close()
	iTunesSock.close()
	sys.exit()

##########

cleanTmp()

iTunesSock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
iTunesSock.bind((socket.gethostbyname(socket.gethostname()), 0))
iTunesSock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
iTunesSock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

flashSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
flashSock.bind(('127.0.0.1', PORT))
flashSock.listen(1)
flashSock.settimeout(60)

# launch flash frontend
#os.startfile(os.path.abspath("aethyrBin.exe"))

# wait for flash to connect
try:
	conn, addr = flashSock.accept()
except socket.error, e:
	print('Exception: ' + str(e))
	flashClientFail()
	
# remove timeout
flashSock.setblocking(1)
conn.setblocking(1)

# must be non-blocking to utilize threads properly
iTunesSock.setblocking(0)

##########

while(True):
#	print(flashSock.getpeername())

	# why is this 4096?
	data = conn.recv(4096)

	print(data)

	if(data.find('downloadProgress') != -1):
		print('Downloading...')
		
		downSet = [int(x) for x in data[len('downloadProgress' + delimiter):-1].split(delimiter)]
		download(tracks, downSet)
		
		total_bandwidth = str(totalSize/1048576.0)[:8]
		total_time = str(totalTime)[:8]
		
		if totalTime != 0:
			avg_speed = str(totalSize/(1048576*totalTime))[:8]
		else:
			avg_speed = '0.000000'

		# give flash update status
		try:
			conn.send(delimiter.join([str(len(downSet)) + '/' + str(len(downSet)), total_bandwidth, total_time, avg_speed, 'finishedDownload', data]))
		except socket.error:
			flashClientFail()

		# something didn't download
		if protectedFiles == True:
			try:
				conn.send('protectedFiles' + delimiter + data)
			except socket.error:
				flashClientFail()

	if(data.find('getiTunesLibraries') != -1):
		# only add shared libraries
		libraries = [i.Name for i in list(iTunes.Sources) if i.Kind == 7]
#		libraries = [i.Name for i in list(iTunes.Sources)[2:]]

		print(libraries)

		# prepare and send data
		ret = delimiter.join(libraries)
		ret = delimiter.join([ret, data])
		try:
			conn.send(ret.encode('utf-8'))
		except socket.error:
			flashClientFail()

	if(data.find('changeDownloadDirectory') != -1):
		path = data.split(delimiter)[1][:-1] + '\\'
		# attempt to store to .ini file
		try:
			config = open(myDocs + 'aethyr.ini', 'w')
			config.write(path)
			config.close()
		except Exception:
			pass
		
		downloadFolder = path.decode('utf-8')
		print(downloadFolder)
		
		cleanTmp()

	if(data.find('loadLibrary') != -1):
		# format: loadLibrary<delimiter>1
		index = int((data.split(delimiter)[1])[:-1])
		
		currentLibrary = libraries[index]
		print(currentLibrary.encode('utf-8'))
		
		startTime = time.time()
		try:
			# is it cached?
			if (currentLibrary in alreadyLoaded) is False:
				# parse the library
				otherLib = iTunes.Sources.ItemByName(currentLibrary).Playlists(1)
				tracks = list(otherLib.Tracks)
				(titles, artists, albums) = (delimiter.join([song.Name for song in tracks]), delimiter.join([song.Artist for song in tracks]), delimiter.join([song.Album for song in tracks]))
				ret = bigDelimiter.join([titles, artists, albums, data])
				alreadyLoaded[currentLibrary] = (ret, tracks)
			else:
				# load from cache
				ret = alreadyLoaded[currentLibrary][0]
				tracks = alreadyLoaded[currentLibrary][1]
		# something messed up somehow
		except AttributeError:
			try:
				conn.send('refreshLibraryList' + data)
			except socket.error:
				flashClientFail()
		# notify flash of completion
		try:
			conn.send(ret.encode('utf-8'))
		except socket.error:
			flashClientFail()
			
		print(time.time() - startTime)
		
	if(data.find('aethyrEXIT') != -1):
		# shutdown time
		flashSock.close()
		iTunesSock.close()
		sys.exit()
