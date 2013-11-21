'''
Created on May 28, 2013
@author: Mike Warner

 ZigTools.py is a framework for the freakduino which provides comparable 
 functionality to the killerbee framework
    Copyright (C) 2013  Mike Warner

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>
'''

import serial
import time
import os
import struct
import math
import threading

''' Global Variables '''
__zigOutFile__ = None
__zigInFile__ = None
__zigSerial__ = None
__zigListen__ = False

''' Helper Methods '''
def rssiToPercent(aByte):
    return round(byteToInt(aByte) / 84.0 * 100.0, 0)

def byteToInt(aByte):
    return int(aByte.encode('hex'), 16)

def __isCallable__(aCallback):
    return aCallback != None and callable(aCallback)

def prettyHex(aString, newLine = 16):
    size = len(aString)
    output = ""
    for i in range(size):
        output += aString[i:i+1].encode("hex") + " "
        if (i + 1) % newLine == 0 and i != 0 and newLine > 0:
            output += "\n"
            
    return str.strip(output)

''' Class Definitions '''
class Frame:
    def __init__(self, aFrame, aRssi = 0):
        self.frame = aFrame
        self.rssi = aRssi
    def getSize(self):
        return byteToInt(self.frame[0, 1])
        
class RadioResponse:
    def __init__(self, aCommandCode, aResponseCode):
        self.commandCode = aCommandCode
        self.responseCode = aResponseCode

        
class __RadioListener__(threading.Thread):
    def __init__(self, aFrameCallback, aCommandCallback):
        threading.Thread.__init__(self)
        self.frameCallback = aFrameCallback
        self.commandCallback = aCommandCallback
        
    def run(self):
        global __zigListen__
        global __zigSerial__
        
        while __zigListen__:
            # Not sure if I need this, but doesn't hurt
            time.sleep(.005)
            size = __zigSerial__.inWaiting()
            if  size > 0:
                response = __zigSerial__.read(1)
                frameSize = __zigSerial__.read(1)
                # New data from the radio
                if response == '\xb0':
                    frame = __zigSerial__.read(byteToInt(frameSize))
                    if __isCallable__(self.frameCallback):
                        self.frameCallback(Frame(frameSize + frame[:-1], frame[-1:]))
                # Send data response or change channel response or system response
                elif response == '\xb1' or response == '\xb2' or response == '\xbf':
                    data = __zigSerial__.read(1)
                    if __isCallable__(self.commandCallback):
                        self.commandCallback(RadioResponse(response, data))
                else:
                    print "Unknown Response: " + prettyHex(response)
                    print "Frame Size: ", byteToInt(frameSize) , " (" + prettyHex(frameSize) + ")"
                    print "Size of buffer: ", size
                    print "Data in buffer: "
                    data = __zigSerial__.read(size - 2)
                    print prettyHex(data)
                    print "Raw Data in Buf: "
                    print data
                    print "Quitting Radio Listener thread!"
                    __zigListen__ = False

''' Output PCAP file functions '''
def initOutPcapFile(aFile):
    global __zigOutFile__
    exists = os.path.isfile(aFile)
    try:
        __zigOutFile__ = open(aFile, "ab", 0)
        if exists:
            return 
    except Exception, e:
        print "Failed to open", aFile
        print e
        exit()
    # Write magic number
    __zigOutFile__.write('\xd4\xc3\xb2\xa1')
    # Write major version
    __zigOutFile__.write('\x02\x00')
    # Write minor version
    __zigOutFile__.write('\x04\x00')
    # Write time sec since epoch
    __zigOutFile__.write(struct.pack('<I', round(time.time())))
    # Write accuracy of time
    __zigOutFile__.write('\x00\x00\x00\x00')
    # Write max len of data
    __zigOutFile__.write('\xff\xff\x00\x00')
    # Write data link type (802.15.4)
    __zigOutFile__.write('\xc3\x00\x00\x00')
        
def writeFrameToPcap(aFrame):
    global __zigOutFile__
    if __zigOutFile__ == None:
        return False
    
    frame = aFrame.frame
    aTime = time.time()
    sec = math.floor(aTime)
    mic = round((aTime - sec) * 1000000)
    # Write out sec and microsec in 4 byte little endian
    __zigOutFile__.write(struct.pack('<I', sec))
    __zigOutFile__.write(struct.pack('<I', mic))
    
    frameLen = int(frame[0:1].encode('hex'), 16)
    # Write frame length - len headed
    __zigOutFile__.write(struct.pack('<I', frameLen - 1))
    # Write out the actual frame len
    __zigOutFile__.write(struct.pack('<I', frameLen))
    # Write out frame without len
    __zigOutFile__.write(frame[1:])

''' Initialize In PCAP file '''
def initInPcapFile(aFile):
    global __zigInFile__
    try:
        __zigInFile__ = open(aFile, "rb")
    except Exception, e:
        print "Failed to open input file: " + e

def getFrameFromPcap(index):
    global __zigInFile__
    if __zigInFile__ == None:
        return False
    frameCount = 1
    frame = ""
    try:
        # move the file pointer back to the top of the file
        __zigInFile__.seek(0)
        # we dont care about the pcap header
        temp = __zigInFile__.read(20)
        # lets just check to make sure the pcap file is the correct 
        # data link type (802.15.4)
        temp = __zigInFile__.read(4)
        if(temp == '\xc3\x00\x00\x00'):
            while temp:
                # dont care about the frame time
                temp = __zigInFile__.read(8)
                # get size saved in file
                # read the first byte since its in little endian and the size is 
                # never > 127
                size = int(__zigInFile__.read(1).encode("hex"), 16)
                # the last 3 bytes of the size (unused)
                temp = __zigInFile__.read(3)
                # get actual size of frame
                actualSize = int(__zigInFile__.read(1).encode("hex"), 16)
                # last 3 bytes of the size (unused)
                temp = __zigInFile__.read(3)
                # get the payload
                data = __zigInFile__.read(size)
                if(index == frameCount):
                    frame = chr(actualSize) + data
                    break
                # increment the frameCount to know what pcap record we're on
                frameCount += 1
    
        else:
            print "PCAP file is of the wrong data link type (not 802.15.4)"
            frame = False
    
    except:
        print "Frame at index " + str(index) + " could not be found"
        frame = False
        
    return Frame(frame)


''' Change channel functions '''
def getNextChannel(currChannel, upDown):
    if upDown == "+":
        if currChannel == 26:
            return 11
        else:
            return (currChannel + 1)
    
    if upDown == "-":
        if(currChannel == 11):
            return 26
        else:
            return (currChannel - 1)
    
    return (currChannel, 11)[currChannel >= 11 and currChannel <= 26]

def changeChannel(aChannel):
    global __zigSerial__
    if __zigSerial__ == None:
        return False
    
    if aChannel >= 11 and aChannel <= 26:
        ba = "\xa2" + chr(aChannel)
        __zigSerial__.write(ba)
        return True
    else: 
        False
        
''' Send data to radio functions '''
def sendRawData(aFrame):
    global __zigSerial__
    if __zigSerial__ == None:
        return False
    # if the aFrame is false from not being found in getFrameFromPcap
    if not aFrame.frame:
        return False
    # send data request
    ba = "\xa1" + aFrame.frame
    __zigSerial__.write(ba)   

''' Start and Stop functions '''
def initialize(comPort, channel = 11, frameCallback = None, commandCallback = None, comSpeed = 57600):
    global __zigSerial__
    global __zigListen__
    
    if __zigListen__:
        print "Listener already initialized."
        return
    
    # if the frameCallback and radioCommandCall are callable
    try:
        __zigSerial__ = serial.Serial(comPort, comSpeed, 8, 'N', 1)
    except serial.serialutil.SerialException, e:
        print e
        exit()
    
    now = time.clock()
    while now > time.clock() - 5:
        time.sleep(.05)
        size = __zigSerial__.inWaiting()
        if  size > 1:
            # if the response is 0xbf
            if __zigSerial__.read(1) == "\xbf":
                # we dont care about the size so get it off of the serial queue
                __zigSerial__.read(1)
                # and if the next char is 0x00
                if __zigSerial__.read(1) == "\x00":
                    __zigListen__ = True
                    thread1 = __RadioListener__(frameCallback, commandCallback)
                    thread1.start()
                    # and if there is a frameCallback
                    if __isCallable__(frameCallback):
                        # tell the radio to start sending frames
                        __zigSerial__.write("\xa0")
                    changeChannel(channel)
                    break
    # never got a response back from the radio. No sense in continuing                    
    if not __zigListen__:
        print "Failed to connect to device!"
        terminate()
        exit()
                
def terminate():
    global __zigListen__
    global __zigSerial__
    global __zigOutFile__
    global __zigInFile__
    
    __zigListen__ = False
    # Give some time for the tread to end gracefully
    time.sleep(.05)
    if __zigSerial__ != None:
        __zigSerial__.close()
    if __zigOutFile__ != None:
        __zigOutFile__.close()
    if __zigInFile__ != None:
        __zigInFile__.close()
