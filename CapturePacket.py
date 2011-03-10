import re
import socket
import threading

#####

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
                info = self.socket.recvfrom(4096)[0]
            except Exception:
                continue
            # iTunes is up to something
            if (info.find('GET daap://') != -1):
                print('')
                print('Captured Packet:')
                print(info[40:])
                # is it a stream request?
                try:
                    url = 'http://' + re.compile('daap://([^/]*/databases.*?) HTTP').search(info).group(1)
                except AttributeError:
                    pass
                else:
                    self.url = url
                    print ('Using URL: %s' % url)
                    
                    requestID = (int)(re.compile('Client-DAAP-Request-ID: (.*)').search(info).group(1))
                    requestID += 1
                    self.packetHeaders['Client-DAAP-Request-ID'] = (str)(requestID)
                    print ('Using DAAP Request ID: %s' % requestID)

#                   udpPort = re.compile('x-audiocast-udpport: (.*)').search(info).group(1)
#                   self.packetHeaders['x-audiocast-udpport'] = udpPort
#                   print ('Using UDP Port: %s' % udpPort)
                    
                    # other client is iTunes
                    try:
                        daapValidation = re.compile('Client-DAAP-Validation: (.*)').search(info).group(1)
                        self.packetHeaders['Client-DAAP-Validation'] = daapValidation
                        print ('Using DAAP Validation: %s' % daapValidation)
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
    
