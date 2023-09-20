import serial, time, requests
import RPi.GPIO as GPIO

# Whatsapp API url and header for messaging, in this case we are using Green API.

url = "[url provided by your API service]"
headers = {
    'Content-Type': 'application/json'
}

# Setting the GPIO mode on the Raspberry Pi as "board" mode.

GPIO.setmode(GPIO.BOARD)

# Enable serial communication, keep in mind that Bluetooth *MUST* be disabled in order to use RT/TX on Raspberry Pi 3/3B/3B+.

port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=1)		# Working with lower baudrates is proven to raise more errors.

# AT Commands to SIM900 for testing and initial setup, \r\n indicates return carriage + new line.

def write_and_return(msg,sleep=0.25):		# Decodes automatically with utf8.
	command = "port.write(b'" + f"{msg}" + "\\r\\n" + "')"
	eval(command)		# Why are we evaluating a string variable instead of using fstring in order to replace the command to be sent? Why not.
	response = port.read(50)
	print(response.decode('utf-8'))
	time.sleep(float(sleep))		# Sleep time is arbitrary, try tweaking it for maximum performance.

write_and_return("AT")		# Checks if connection is OK and if module is alive.
write_and_return("AT+CMGF=1")		# Start receiving SMSs.
write_and_return("AT+CNMI=2,2,0,0,0")		# Changing SMS receive mode: do not store into card, only into memory and then send it directly to console.
write_and_return('AT+CSCS="UCS2"')		# Set SMS decoding mode to UCS2 (support for UTF-16: strange and foreign non-ascii characters).
print("Now entering message receiving mode...")

# Now we proceed to open a file where all the loggin occurs. Primarily for forensic and debugging use, can be disabled at will.

fp = open(file="/home/pi/CHINA_SIM/log.txt",mode="a",encoding="utf-8",buffering=1)		# If run on a raspi, buffering must be set beforehand, otherwise, all text will be buffered into RAM and no file will be written.

# Start loop, and if any bit is received, start the decoding phase

while True:
	msg = port.read_until()
	if msg:
		data=dict()		# Start a dictionary, where the keys are going to be "sender", "date", "timestamp" and "message", following the serial response structure.
		msg = port.read_until()
		try:
			print(msg)		# Printing to console as debug, not really necessary.
			header = msg.decode('utf-8').strip().split()[1].split(",")		# The message is received as a binary string b'AF06', so we first decode it from binary to ascii characters, and clear up the formatting.
			data["sender"]=bytes.fromhex(header[0].replace('"','')).decode("utf-16be")		# After we get the string and decode it from binary to ascii, we decode again and convert from hexadecimal notation to
			data["date"]=header[2].replace('"','')							# printable characters using the UTF-16 Big Endian codec.
			data["timestamp"]=header[3].replace('"','')						# As a side note, "be" *MUST* be specified explicitly, otherwise, the program won't decode the message correctly.
		except:
			fp.write("\nERROR!!")		# In case any decoding fails, it prints to log and displays ERROR message.
			fp.write("\n"+str(msg))
		msg = port.read_until()
		try:
			print(msg)		# If everything works, it will also print decoded message to log.
			data["message"]=bytes.fromhex(msg.decode('utf-8')).decode("utf-16be")		# Fist decoding is for the sender's identity, second decoding (this one) is for the body of the message.
		except:
			fp.write("\nERROR!!")		# In case any decoding fails, it prints to log and displays ERROR message.
			fp.write("\n"+str(msg))
		fp.write("\n"+str(data))

		# Formatting the message we are going to be sending on Whatsapp. Can be customized to the client's needs.
		
		aux = []
		for key in data:
			aux.append(key + ":\\t\\t" + data[key])
		info = "\\n".join(aux)
		payload = "[insert here message to be sent]"		# In my case I have the keys and the values of the dictionary formatted and printed: "{\r\n\t\"chatId\": \"xxxx@g.us\",\r\n\t\"message\": \"' + f"{info}" + '\"\r\n}"
		response = requests.request("POST", url, headers = headers, data = payload.encode('utf-8'))
		try:
			print(response.text.encode('utf-8'))		# If sending successfully, print into terminal the respose from cURL.
		except:
			fp.write("\nERROR WHILE SENDING WHATSAPP!!")		# If sending fails, write it to log.
