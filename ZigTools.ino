/* Created by: Mike Warner
 * Updated on: May 28, 2013
 * Version: 2.0
 */

#include <chibi.h>
boolean listening = false;

void setup()
{
	chibiInit();
	chibiSetChannel(11);
	Serial.begin(57600);
	// 0xBF with 0x00 starts the system
	// use 0xBF with other statuses for debugging
	sendResponse(0xbf, 0x00);
}

void loop() {
	// Check if any data was received from the radio. If so, then handle it.
	if(chibiDataRcvd() == true) {
		int len;
		byte buf[CHB_MAX_PAYLOAD];
		// Get the radio's buffer even if we're sending the data (to serial)
		// or not to clear the radio's buffer
		len = chibiGetData(buf);
		if(listening) {
			// b0 = Received Data Response Code
			Serial.write(0xb0);
			// send the raw data out the serial port in binary format
			Serial.write(buf, len);
			// Send power level of last response
			Serial.write(chibiGetRSSI());
		}
	}
	// Incoming commands
	if(Serial.available() > 1) {
		int data = Serial.read();
		// 0xA2 = change the channel request
		if(data == 0xa2) {
			data = Serial.read();
			if(data >= 11 && data <= 26) {
				// 0x40 = success, 0x43 = radio timeout
				int response = chibiSetChannel(data);
				// Change channel response
				sendResponse(0xb2, response);
			} else {
				sendResponse(0xb2, 0xee);
			}
			// A1 = Send data request
		} else if(data == 0xa1) {
			// stop here for 10ms just incase all the data
			// hasent made it to the input buffer (not sure if needed)
			// at 57600 should take less than 5ms for 128 bytes to arraive
			delay(10);
			// size byte
			int len = Serial.read();
			byte frame[len];
			frame[0] = len;
			// masking the control field is now controlled through the mutator py
			frame[1] = Serial.read(); // & 0xDF;
			// put the rest of the data into the array
			for(int i = 2; i < len; i++) {
				frame[i] = Serial.read();
			}
			// send the frame and get the resonse
			int response = chibiTxRaw(frame);
			sendResponse(0xb1, response);
			// A0 = Toggle send to serial or not
		} else if(data == 0xa0) {
			listening = listening ^ true;
		}
	}
}

// this function is used to get back command responses
void sendResponse(char code, char response) {
	Serial.write(code);
	Serial.write(0x02);
	Serial.write(response);
}
