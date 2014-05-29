ZigTools
=====================
Abstract
---------

The zigTools.py script reduces  the complexity in writing additional functionality to communicate with the Freakduino (Arduino based 802.15.4 platform). Features such as initializing the radio, changing channels, sending data and processing that data can be written in just a few lines allowing the user to focus on writing more complex applications without worrying about the low level communications between the radio and computer.

Requirements
----------

#### File Structure

The zigTools.py file should be within the same directory as the Python script you are writing. To import the library, add **import zigTools** to the top of your Python script.

#### Python

The zigTools.py library is dependent on [pySerial](http://pyserial.sourceforge.net/)  which is not included with the standard install of Python. This library has been tested and created for Python 2.7.

#### Arduino Libraries

TODO: Fill in this part about the Arduino sketch and chibiArduino.

API
-----------

#### Initialize Radio
```python
zigTools.initialize(comPort, channel = 11, frameCallback = None, commandCallback = None, comSpeed = 57600)
```
This function attempts to connect to the radio, start the radio listener thread, change the channel to the initial channel and sends a command to the radio to send data if the frameCallback parameter has been defined. 

***comPort*** --- String value of the COM port to be used. Typically in Windows, this is defined as “COM#” and in a Linux environment, this is defined a “/dev/ttyS#” or “/dev/ttyUSB#” where # is a number.

***channel*** --- (Optional) Is an integer between 11 and 26 which represents the channel to start the radio.

***frameCallback*** --- (Optional) Can be set to a user defined callable function. This value will be used as an event handler that will be called each time new data arrives. If this value is not set, the radio will not send any data back to the computer.

***commandCallback*** --- (Optional) Can be set to a user defined callable function. This value will be used as an event handler that will be called each time new radio [command responses](#command-codes) are received.

***comSpeed*** --- (Optional) Is an integer value to set the serial baud rate between the computer and radio. This should never need to be changed, unless the zigTools Arduino sketch is modified to have another value.

-----------

#### Terminate All
```python
zigTools.terminate()
```
This function gracefully stops the radio listener thread, open file handles and the serial object. 

-----------

#### Initialize Output PCAP File
```python
zigTools.initOutPcapFile(aFile)
```
This function is used to open a file handle to a PCAP file where 802.15.4 frames can be saved to. If the file does not exist, a file will be created with all PCAP headers and if the file does exists, the frames will be appended. 

***aFile*** --- Is a string to a file within the file system.

-----------

#### Write Data To PCAP File
```python
zigTools.writeFrameToPcap(aFrame)
```
This function is used to write 802.15.4 data out to the initialized to PCAP file. 

***aFrame*** --- This is a [Frame type object](#frame-object).

-----------

#### Initialize Input PCAP File
```python
zigTools.initInPcapFile(aFile)
```
This function is used to open a file handle to an existing PCAP file which contains 802.15.4 data.

***aFile*** --- Is a string to a file within the file system.

-----------

#### Get Frame Frome PCAP File
```python
zigTools.getFrameFromPcap(index)
```
This function is used to get a frame from the open input file handle.

***index*** --- This is an integer that correlates to the [Wireshark](http://www.wireshark.org/) *No.* field.

***Returns*** --- A [Frame type object](#frame-object).

-----------

#### Send Raw Data
```python
zigTools.sendRawData(aFrame)
```
This function is used to send raw data out to the radio.

***index*** --- This is a [Frame type object](#frame-object).

-----------

#### Get Next Channel
```python
zigTools.getNextChannel(currChannel, upDown)
```
This function is used to get the next integer value when going up or down on available channels. If the beginning or the end of the channel range is reached and the request is to go outside of the range, the resulting channel will be the rolled over channel.

***currChannel*** --- Is an integer value of the starting channel to go up or down from.

***UpDown*** --- Is a string value that can either be a "+" or a "-". By using the "+", one is added to the *curChannel* and if *currChannel* is at the max value, it will roll over and return the value at the start of the range. Inversely, if  "-" is used and the *currChannel* is at the beginning of the range, the return value will be the max value of the range.

***Returns*** --- Next integer value within the valid channel range (11 – 26).

-----------

#### Change Channel
```python
zigTools.changeChannel(aChannel)
```
This function is used to send a command to the radio to change the channel.

***aChannel*** --- Is an integer between 11 and 26.

-----------

#### RSSI To Percent
```python
zigTools.rssiToPercent(aByte)
```
This function is used to change the byte value of the RSSI to a percentage.

***aByte*** --- Is a character byte representing the RSSI.

***Returns*** --- An integer between 0 and 100.

-----------

#### Byte To Integer
```python
zigTools.byteToInt(aByte)
```
This function is used to convert a byte to an integer.

***aByte*** --- Is a character byte representing the RSSI.

***Returns*** --- An integer representation of the byte (0 - 255).

-----------

#### Pretty Hex
```python
zigTools.prettyHex(aString, newLine = 16)
```
This function is used to convert a binary character array to a space delimited Hex string with a new line every 16 bytes by default.

***aString*** --- Is a string of binary data.

***newline*** --- (Optional) Is an integer of when to insert a new line (Defaults to 16)
Returns: A string representation of the binary character array that is space delimited Hex values with a new line every user defined number of bytes.

***Returns*** --- A string representation of the binary character array that is a space delimited Hex values with a new line every user defined number of bytes.

Frame Object
-----------

#### Properties
```python
Frame.frame
```
This property is a raw binary string of the frame including the size byte.

```python
Frame.rssi
```
This property is a byte representing the RSSI of the received frame.

#### Methods
```python
Frame.getSize()
```
This function is used to return an integer representation of the size of the frame.

RadioResponse Object
-----------

#### Properties
```python
RadioResponse.commandCode
```
This property is a byte value of the [command code](command-codes) from the radio.

```python
RadioResponse.responseCode
```
This property is a byte value of the response code associated with a command code.

#### Methods

No methods defined at this time.

Command Codes
-----------
Command codes are the key portion of a key value pair of a radio response. They are used to determine if system command, such as send data and change channel succeed. 

Hex Code  | Definition
--------- | -----
0xB1  | Send Data Response
0xB1  | Change Channel Response (Response code 0xee is an error)
0xBF  | System response (Can be used for Arduino debugging. Response code 0x00 is reserved)


Example
-----------
This example Python script will sniff each channel for 15 seconds before moving on to the next channel. This script will cycle through all the channels once then stop.
```python
import zigTools
import time

def dataEvent(aFrame):
    print "Writing new frame to file."
    zigTools.writeFrameToPcap(aFrame)
    print zigTools.prettyHex(aFrame.frame)
    print "RSSI: ", zigTools.rssiToPercent(aFrame.rssi), “%”

if __name__ == '__main__':
    curChnl = 11
    zigTools.initOutPcapFile("C:\\temp\\test.pcap")
    zigTools.initialize("COM9", curChnl, dataEvent)
    for i in range(16):
        print "Changing Channel to ", curChnl
        time.sleep(15)
        curChnl = zigTools.getNextChannel(curChnl, "+")
        zigTools.changeChannel(curChnl)
        
    zigTools.terminate()
```
