import serial.tools.list_ports
from serial import Serial
from serial.threaded import ReaderThread, Protocol
from pynput.keyboard import Key, Controller

class SerialReaderProtocol(Protocol):
    def connection_made(self, transport):
        print("Connected, ready to receive data.")
    def data_received(self, data):
        print(len(data))
        print(data)
    def connection_lost(self, exc):
        print("Connection Lost!")

DuoPort = ""

ports = serial.tools.list_ports.comports()
available_ports = []
for p in ports:
   if "VID&00010039_PID&5035" in p.hwid:
       DuoPort = p.name

if DuoPort == "":
    print("No DuoPinball device found. Exiting.")    
    exit()

print("Connecting to",DuoPort)
try:
    DuoCom = serial.Serial(DuoPort, baudrate=9600, timeout=None, bytesize=8, parity='N', stopbits=1, xonxoff=False, rtscts=False, dsrdtr=False)
    print(DuoCom)
except:
    print("Can't connect. Exiting.")
    exit()

#reader = ReaderThread(DuoCom, SerialReaderProtocol)
#reader.start()
    
#Packet structure
#1st and 2nd byte: "0x5A 0xA5" - signature 
#3rd: 01 - button, 02 - plunger
#4th, button: left - 1st bit, right -2nd bit
#4th, plunger: 0..0x3F - position
#5th button: unused?
#5th plunger: 0xFF - fully returned,17 - fully pulled

FlipperState = 0
PlungerState = 0
PlungerPos = 0

keyboard = Controller()

while True:
    data=DuoCom.read(6)
    #print(hex(data[0]),hex(data[1]),hex(data[2]),hex(data[3]),hex(data[4]))
    cs=(data[0]+data[1]+data[2]+data[3]+data[4]+1)&0xFF
    if cs != data[5]:
        print("Ignoring, incorrect checksum.")
    else:

        if data[2] == 1:
        #Flipper action    
            if FlipperState != data[3]:
                FlipperState=data[3]
                if (FlipperState&1):
                    keyboard.press(Key.shift_l)      
                else:
                    keyboard.release(Key.shift_l)      
                if (FlipperState&2):
                    keyboard.press(Key.shift_r)     
                else:
                    keyboard.release(Key.shift_r)
    
        if data[2] == 2:
        #Plunger action
            PlungerPos = data [3]
            if PlungerState == 0:
            #Start moving    
                PlungerState = 1
                keyboard.press(Key.enter)
            else:
                if data[4]&0xFF == 0xFF:
                    PlungerState = 0                    
                    keyboard.release(Key.enter)
DuoCom.close()
