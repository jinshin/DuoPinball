#Python DuoPinball controller driver for Windows PC
#Idea and some code taken from https://csdprojects.co.uk/winapps
#I had no idea it's a simply COM port :)

import serial.tools.list_ports
from serial import Serial
from pynput.keyboard import Key, Controller
import vgamepad as vg

#Config part start
#Keyboard emulation
EmulateKeyboard = True
LeftFlipper = "z"
#LeftFlipper = Key.shift_r
RightFlipper = "/"
#RightFlipper = Key.shift_r
Plunger = Key.space
#Plunger = Key.enter

#Gamepad emulation
#You need ViGEmBus for that
#Right stick down hardcoded to fine control plunger movement.
#Works ok
EmulateGamepad = True
LeftFlipperG = vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER
RightFlipperG = vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER
PlungerG = vg.XUSB_BUTTON.XUSB_GAMEPAD_A
#Alternate Plunger movement detection
AltPos = True
#Config part end

DuoPort = ""

ports = serial.tools.list_ports.comports()
available_ports = []
for p in ports:
   if "VID&00010039_PID&5035" in p.hwid:
       DuoPort = p.name

if DuoPort == "":
    print("No DuoPinball device found. Exiting.")    
    exit()

print("Connecting to",DuoPort,"...")
try:
    DuoCom = serial.Serial(DuoPort, baudrate=9600, timeout=5*57)
    print("Connected. Have fun!")
except:
    print("Can't connect. Exiting.")
    exit()
    
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

LeftFlipperState = 0
RightFlipperState = 0
PrevLeftFlipperState = 0
PrevRightFlipperState = 0

if EmulateKeyboard:
    keyboard = Controller()
else:
    keyboard = 0

if EmulateGamepad:
    try:
        gamepad = vg.VX360Gamepad()
    except:
        print("Install ViGEmBus if you plan to emulate X360 gamepad")
        gamepad = 0   

while True: 
    data=DuoCom.read(6)
    #print(hex(data[0]),hex(data[1]),hex(data[2]),hex(data[3]),hex(data[4]))
    #print(len(data))
    if (len(data) == 0):
        input("Press any button on controller and press Enter to reconnect.")
        try:
            DuoCom.close()
            print("Connecting...")
            DuoCom = serial.Serial(DuoPort, baudrate=9600, timeout=5*57)
            print("Connected.")
            data=DuoCom.read(6)
            #Well here's a possible problem, will throw an exeption
            #if no key is pressed after new connect
            #but why would that happen?
        except:
            print("Can't connect. Exiting.")
            exit()
        
    cs=(data[0]+data[1]+data[2]+data[3]+data[4]+1)&0xFF
    if cs != data[5]:
        print("Ignoring data, incorrect checksum.")
        DuoCom.close()
        print("Reconnecting...")
        DuoCom = serial.Serial(DuoPort, baudrate=9600, timeout=5*57)
        print("Connected.")
        data=DuoCom.read(6)
    else:
        if data[2] == 1:
        #Flipper action    
            if FlipperState != data[3]:
                FlipperState=data[3]
                
                LeftFlipperState=FlipperState&1
                RightFlipperState=FlipperState>>1&1
                
                if LeftFlipperState != PrevLeftFlipperState:
                    PrevLeftFlipperState = LeftFlipperState
                    if LeftFlipperState:
                        if keyboard:
                            keyboard.press(LeftFlipper)
                        if gamepad:
                            gamepad.press_button(LeftFlipperG)
                            gamepad.update()
                    else:
                        if keyboard:
                            keyboard.release(LeftFlipper)
                        if gamepad:
                            gamepad.release_button(LeftFlipperG)
                            gamepad.update()
                
                if RightFlipperState != PrevRightFlipperState:
                    PrevRightFlipperState = RightFlipperState
                    if RightFlipperState:
                        if keyboard:
                            keyboard.press(RightFlipper)
                        if gamepad:
                            gamepad.press_button(RightFlipperG)
                            gamepad.update()
                    else:
                        if keyboard:
                            keyboard.release(RightFlipper)
                        if gamepad:
                            gamepad.release_button(RightFlipperG)
                            gamepad.update()
                            
            #print(FlipperState,LeftFlipperState,RightFlipperState)  
    
        if data[2] == 2:
        #Plunger action
            if not AltPos:
                PlungerPos = 0 - float(data[3])/60
            else:      
                PlungerPos = -1 + float(data[4]-28)/256                         
            if PlungerPos < -1:
                PlungerPos = -1
            #print(PlungerPos,data[3],data[4])        
            if gamepad:
                gamepad.right_joystick_float(0,PlungerPos)
                gamepad.update() 
            if PlungerState == 0:
            #Start moving    
                PlungerState = 1
                if keyboard:
                    keyboard.press(Plunger)
                if gamepad:
                    gamepad.press_button(PlungerG)
                    gamepad.update()
            if data[4]&0xFF == 0xFF:
                PlungerState = 0
                PlungerPos = 0
                if keyboard:
                    keyboard.release(Plunger)
                if gamepad:
                    gamepad.release_button(PlungerG)
                    gamepad.right_joystick_float(0,PlungerPos)
                    gamepad.update()
DuoCom.close()
