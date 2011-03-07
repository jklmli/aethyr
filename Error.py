import socket
import sys

#####

import Helper

#####

def disconnection(alreadyLoaded, currentLibrary, 
                  flashConnection, flashSock, iTunesSock):
    print('Disconnection Error')
    # remove library from cache in case it changes
    #del(alreadyLoaded[currentLibrary])
    try:
        flashConnection.send('refreshLibraryList')
    except socket.error:
        flashClientFail()

def flashClientFail(flashSock, iTunesSock):
    print('Flash Client Fail')

    Helper.shutdown(flashSock, iTunesSock)
