import os
import threading
import time
import urllib2
import socket

#####

import Helper

#####

class ForgePacket(threading.Thread):
	def __init__(self, url, packetHeaders):
		threading.Thread.__init__(self)
		self.url = url
		self.packetHeaders = packetHeaders
		self.disconnectionError = False
		self.exception = False
		self.timeSpent = 0
		self.mp3BufferLocation = ''

	def run(self):
		# forge a fake iTunes request
		req = urllib2.Request(self.url)

		for authenticationElement in self.packetHeaders.keys():
			req.add_header(	authenticationElement,
						 	self.packetHeaders[authenticationElement])

		# allows pulling certain chunks of a song...fallback workaround
		# if iTunes actually begins 'streaming'
#		req.add_header('Range', 'bytes=0-5000')

		# we create a temporary file first in case we can't read from the
		# file, transfer gets interrupted, etc.
		mp3Buffer, mp3BufferLocation = Helper.newTemporaryFile()
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
