import serial, time, requests
import RPi.GPIO as GPIO

# Whatsapp API url and header for messaging, in this case we are using Green API

url = "[url provided by your API service]"
headers = {
    'Content-Type': 'application/json'
}

# Setting the GPIO mode on the Raspberry Pi as "board" mode

GPIO.setmode(GPIO.BOARD)

# Enable serial communication, keep in mind that Bluetooth *MUST* be disabled in order to use RT/TX on Raspberry Pi 3/3B/3B+

port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=1)

# AT Commands to SIM900 for testing and initial setup, \r\n indicates return carriage + new line

def write_and_return(msg,sleep=0.25):		# Decodes automatically with utf8
	command = "port.write(b'" + f"{msg}" + "\\r\\n" + "')"
	eval(command)		# Why are we evaluating a string variable instead of using fstring in order to replace the command to be sent? Why not.
	response = port.read(50)
	print(response.decode('utf-8'))
	time.sleep(float(sleep))		# Sleep time is arbitrary, try tweaking it for maximum performance

write_and_return("AT")		# Checks if connection is OK and if module is alive
write_and_return("AT+CMGF=1")		# Start receiving SMSs
write_and_return("AT+CNMI=2,2,0,0,0")		# Changing SMS receive mode: do not store into card, only into memory and then send it directly to console
write_and_return('AT+CSCS="UCS2"')		# Set SMS decoding mode to UCS2 (support for UTF-16: strange and foreign non-ascii characters)
print("Now entering message receiving mode...")

# Now we proceed to open a file where all the loggin occurs. Primarily for forensic and debugging use, can be disabled at will.

fp = open(file="/home/pi/CHINA_SIM/log.txt",mode="a",encoding="utf-8",buffering=1)		# If run on a raspi, buffering must be set beforehand, otherwise, all text will be buffered into RAM and no file will be written.



while True:
	msg = port.read_until()
	if msg:
		data=dict()
		msg = port.read_until()
		try:
			print(msg)
			header = msg.decode('utf-8').strip().split()[1].split(",")
			data["sender"]=bytes.fromhex(header[0].replace('"','')).decode("utf-16be")
			data["date"]=header[2].replace('"','')
			data["timestamp"]=header[3].replace('"','')
		except:
			fp.write("\nERROR!!")
			fp.write("\n"+str(msg))
		msg = port.read_until()
		try:
			print(msg)
			data["message"]=bytes.fromhex(msg.decode('utf-8')).decode("utf-16be")
		except:
			fp.write("\nERROR!!")
			fp.write("\n"+str(msg))
		fp.write("\n"+str(data))

		aux = []
		for key in data:
			aux.append(key + ":\\t\\t" + data[key])
		info = "\\n".join(aux)
		payload = [insert here message to be sent]
		response = requests.request("POST", url, headers = headers, data = payload.encode('utf-8'))
		try:
			print(response.text.encode('utf-8'))
		except:
			fp.write("\nERROR WHILE SENDING WHATSAPP!!")
