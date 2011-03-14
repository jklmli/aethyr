import os
import sys
import tempfile
import urllib2
import _winreg

#####

updateURL = 'http://www.aethyrjb.com/version.txt'

#####

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
				'Purchased AAC audio file':'.m4a',
				# future support for video files
#            	'MPEG-4 video file':'.m4v',
#           	 'Purchased MPEG-4 video file':'.m4v'
				'QuickTime movie file':'.mp4'
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

def isFolderIntegrityOK(downloadFolder):
	print('Download folder located at: %s' % downloadFolder)
	# creation if it doesn't exist; reset if not allowed
	if os.path.exists(downloadFolder) is False:
		try:
			os.mkdir(downloadFolder)
		except WindowsError:
			#resetDefaultDownloadFolder()
			return False
	return isFileWritable(downloadFolder + 'aethyrConfig.ini')

def isFileWritable(fileLocation):
	try:
		with open(fileLocation, 'wb') as fileHandle:
			fileHandle.write('asdf')
	except IOError:
		#resetDefaultDownloadFolder()
		return False
	else:
		os.remove(fileLocation)
		return True

def changeDownloadDirectory(path, configFileLocation):
	with open(configFileLocation, 'w') as config:
		config.write(path)

	return isFolderIntegrityOK(path)

def shutdown(flashSock, iTunesSock):
	flashSock.close()
	iTunesSock.close()
	sys.exit()

def getiTunesLibraries(sources):
	# only add shared libraries
	libraries = [i.Name for i in list(sources) if i.Kind == 7]
#	libraries = [i.Name for i in list(sources)[2:]]
	print('Refreshed list of libraries: %s' % str(libraries))
	return libraries

def isNeedUpdate():
	registry = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
	aethyrKey = _winreg.OpenKey(registry, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Aethyr')
	currentVersion = _winreg.QueryValueEx(aethyrKey, 'DisplayVersion')[0].strip()
	try:
		serverVersion = urllib2.urlopen(updateURL).read().strip()
		print('Current version is: %s' % currentVersion)
		print('Server version is: %s' % serverVersion)
		return (serverVersion > currentVersion)
	except urllib2.HTTPError:
		return False
