import pygame, ctypes, time, mido, os

outport = mido.open_output("Virtual Port 1")

def set_vibration(controller, left_motor, right_motor):
    vibration = XINPUT_VIBRATION(int(left_motor * 65535), int(right_motor * 65535))
    XInputSetState(controller, ctypes.byref(vibration))

def blinkLight():
    set_vibration(0, 0, 1.0)
    set_vibration(0, 0, 0)

def recieveMidi(ppqnVal):
    return

#for buttons with delta values...
#0 -> 0 (0) no activity
#0 -> 1 (1) hit
#1 -> 1 (3) held
#1 -> 0 (2) release
#buttonDeltas[] contains...
#Lgreen, Lred, Lblue, Mgreen, Mred, Mblue, Rgreen, Rred, Rblue...
#...yellow, start, back, up, down, left, right
def sendMidi(leftPlatterMidiPos, rightPlatterMidiPos, crossfaderMidiPos, knobMidiPos, buttonDeltas):
    if(leftPlatterMidiPos != None):
        msg = mido.Message("control_change", channel = 0, control = 8, value = leftPlatterMidiPos)
        outport.send(msg)
        time.sleep(msg.time)

    if(rightPlatterMidiPos != None):
        msg = mido.Message("control_change", channel = 1, control = 8, value = rightPlatterMidiPos)
        outport.send(msg)
        time.sleep(msg.time)

    if(crossfaderMidiPos != None):
        msg = mido.Message("control_change", channel = 2, control = 8, value = crossfaderMidiPos)
        outport.send(msg)
        time.sleep(msg.time)

    if(knobMidiPos != None):
        msg = mido.Message("control_change", channel = 3, control = 8, value = knobMidiPos)
        outport.send(msg)
        time.sleep(msg.time)

    for i in range(len(buttonDeltas)):
        if buttonDeltas[i] == 0b00: #no activity
            continue
        elif buttonDeltas[i] == 0b01: #hit
            msg = mido.Message("note_on", note = (60 + i))
            print(msg)
            outport.send(msg)
        elif buttonDeltas[i] == 0b11: #held
            continue
        elif buttonDeltas[i] == 0b10: #release
            msg = mido.Message("note_off", note = (60 + i))
            print(msg)
            outport.send(msg)

def getActiveControl(zAxisValue):
    if round(zAxisValue) == 0:
        return "middle"
    elif round(zAxisValue) == -1:
        return "right platter"
    elif round(zAxisValue) == 1:
        return "left platter"

class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [("wLeftMotorSpeed", ctypes.c_ushort),
                ("wRightMotorSpeed", ctypes.c_ushort)]

xinput = ctypes.windll.xinput1_1
XInputSetState = xinput.XInputSetState
XInputSetState.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_VIBRATION)]
XInputSetState.restype = ctypes.c_uint

pygame.init()

pygame.joystick.init()
joystick_count = pygame.joystick.get_count()
if joystick_count > 1:
    print("Expected one controller, found multiple.")
    quit()
elif joystick_count == 0:
    print("Controller not found.")
    quit()

turntable = pygame.joystick.Joystick(0)
turntable.init()
name = turntable.get_name().upper()

if(name != "CONTROLLER (GH5 WIRED DJ)"):
    print("Expected \"CONTROLLER (GH5 WIRED DJ)\" but found \"" + name + "\"")
    time.sleep(1)
    for i in range(3):
        print(".", end = " ", flush = True),
        time.sleep(1)
    print("\nContinuing anyway.")
    time.sleep(1)

pygame.event.pump()

prevCrossfaderMidiPos = int(round(turntable.get_axis(3)/0.015625)) + 63
prevKnobTruePos = (int(round(turntable.get_axis(4)/0.015625)) + 63) % 128
prevKnobMidiPos = 0
prevKnobDelta = 0

prevCrossfaderMidiPos = prevCrossfaderMidiPos = int(round(turntable.get_axis(3)/0.015625)) + 63

#initialize turntable positions to 0
prevRightPlatterMidiPos = 0
prevLeftPlatterMidiPos = 0

prevLGreen = 0
prevLRed = 0
prevLBlue = 0
prevMGreen = 0
prevMRed = 0
prevMBlue = 0
prevRGreen = 0
prevRRed = 0
prevRBlue = 0
prevYellow = 0
prevStart = 0
prevBack = 0
prevUp = 0
prevDown = 0
prevLeft = 0
prevRight = 0

#Time of last known TRUE pulse
#Just determining "green-ness" at this phase; origin of press at differnt phase
greenBuffer = 0.000
redBuffer = 0.000
blueBuffer = 0.000

bufferLength = 0.018

#let's poll the velocity of the turntables just a few times a second
#these will hold times of last poll
rightPlatterBuffer = 0.000
leftPlatterBuffer = 0.000






while True:
    pygame.event.pump()
    currentTime = time.time()

    '''storage for changes in button presses this frame'''
    buttonDeltas = []

    '''check for quit'''
    start = turntable.get_button(7)
    back = turntable.get_button(6)
    if(back == 1 and start == 1):
        os._exit(0)

    '''determine if GRB are pulsing high'''
    green = turntable.get_button(0)
    red = turntable.get_button(1)
    blue = turntable.get_button(2)

    '''validate key releases came from a human'''
    if(green == 0):
        if(currentTime - greenBuffer <= bufferLength):
            green = 1
        else:
            green = 0
    elif(green == 1):
        greenBuffer = time.time()
    if(red == 0):
        if(currentTime - redBuffer <= bufferLength):
            red = 1
        else:
            red = 0
    elif(red == 1):
        redBuffer = time.time()
    if(blue == 0):
        if(currentTime - blueBuffer <= bufferLength):
            blue = 1
        else:
            blue = 0
    elif(blue == 1):
        blueBuffer = time.time()

    '''determine active control for this frame'''
    activeControl = getActiveControl(turntable.get_axis(2))

    '''determine origin of GRB keypresses'''
    LGreen = 0
    LRed = 0
    LBlue = 0
    MGreen = 0
    MRed = 0
    MBlue = 0
    RGreen = 0
    RRed = 0
    RBlue = 0

    if(activeControl == "middle"): #TODO DID THIS WORK?
        if(green):
            MGreen = 1
        if(red):
            MRed = 1
        if(blue):
            MBlue = 1
    elif(activeControl == "left platter"):
        if(green):
            LGreen = 1
        if(red):
            LRed = 1
        if(blue):
            LBlue = 1
    elif(activeControl == "right platter"):
        if(green):
            RGreen = 1
        if(red):
            RRed = 1
        if(blue):
            RBlue = 1

    '''determine yellow/euphoria button keypresses'''
    yellow = turntable.get_button(3)

    '''determine d-pad keypresses'''
    dpadXY = turntable.get_hat(0)
    up = 0
    down = 0
    left = 0
    right = 0
    if dpadXY[1] == 1:
        up = 1
    elif dpadXY[1] == -1:
        down = 1
    if dpadXY[0] == -1:
        left = 1
    elif dpadXY[0] == 1:
        right = 1

    '''append deltas to buttonDeltas list'''


    buttonDeltas.append((prevLGreen << 1) | LGreen)
    buttonDeltas.append((prevLRed << 1) | LRed)
    buttonDeltas.append((prevLBlue << 1) | LBlue)
    buttonDeltas.append((prevMGreen << 1) | MGreen)
    buttonDeltas.append((prevMRed << 1) | MRed)
    buttonDeltas.append((prevMBlue << 1) | MBlue)
    buttonDeltas.append((prevRGreen << 1) | RGreen)
    buttonDeltas.append((prevRRed << 1) | RRed)
    buttonDeltas.append((prevRBlue << 1) | RBlue)
    buttonDeltas.append((prevYellow << 1) | yellow)
    buttonDeltas.append((prevStart << 1) | start)
    buttonDeltas.append((prevBack << 1) | back)
    buttonDeltas.append((prevUp << 1) | up)
    buttonDeltas.append((prevDown << 1) | down)
    buttonDeltas.append((prevLeft << 1) | left)
    buttonDeltas.append((prevRight << 1) | right)

    '''update previous readings'''
    prevLGreen = LGreen
    prevLRed = LRed
    prevLBlue = LBlue
    prevMGreen = MGreen
    prevMRed = MRed
    prevMBlue = MBlue
    prevRGreen = RGreen
    prevRRed = RRed
    prevRBlue = RBlue
    prevYellow = yellow
    prevStart = start
    prevBack = back
    prevUp = up
    prevDown = down
    prevLeft = left
    prevRight = right

    '''approximate platter positions given previous positions and raw velocities'''
    leftPlatterRawVel = int(round(turntable.get_axis(0), 2)/2 * 100)
    rightPlatterRawVel = - int(round(turntable.get_axis(1), 2)/2 * 100)

    if(leftPlatterRawVel == 0 or (time.time() - leftPlatterBuffer < 0.03)):
        leftPlatterMidiPos = None
    else:
        leftPlatterMidiPos = (prevLeftPlatterMidiPos + leftPlatterRawVel) % 128
        prevLeftPlatterMidiPos = leftPlatterMidiPos
        leftPlatterBuffer = time.time()

    if(rightPlatterRawVel == 0 or (time.time() - rightPlatterBuffer < 0.03)):
        rightPlatterMidiPos = None
    else:
        rightPlatterMidiPos = (prevRightPlatterMidiPos + rightPlatterRawVel) % 128
        prevRightPlatterMidiPos = rightPlatterMidiPos
        rightPlatterBuffer = time.time()

    '''calculate knob position, max out at 127, min at 0'''
    knobTruePos = (int(round(turntable.get_axis(4)/0.015625)) + 63) % 128
    if(knobTruePos != prevKnobTruePos):
        knobDelta = knobTruePos - prevKnobTruePos
    else:
        knobDelta = 0

    if(knobDelta >= 64):
        knobDelta = -(128 - knobDelta)
    elif(knobDelta <= -64):
        knobDelta = (knobDelta + 128)

    knobMidiPos = prevKnobMidiPos + knobDelta

    if(knobMidiPos > 127):
        knobMidiPos = 127
    elif(knobMidiPos < 0):
        knobMidiPos = 0

    prevKnobTruePos = knobTruePos
    if(prevKnobMidiPos == knobMidiPos):
        knobMidiPos = None
    else:
        prevKnobMidiPos = knobMidiPos

    '''calculate crossfader position'''
    crossfaderMidiPos = int(round(turntable.get_axis(3)/0.015625)) + 63

    if(crossfaderMidiPos < 0):
        crossfaderMidiPos = 0
    if(crossfaderMidiPos == prevCrossfaderMidiPos):
        crossfaderMidiPos = None
    else:
        prevCrossfaderMidiPos = crossfaderMidiPos

    '''print newest readings'''
    printblock = ("\n\n" + name.upper()
    + "\nleft platter pos: " + (str(leftPlatterMidiPos) if leftPlatterMidiPos != None else str(prevLeftPlatterMidiPos))
    + "\nright platter pos: " + (str(rightPlatterMidiPos) if rightPlatterMidiPos != None else str(prevRightPlatterMidiPos))
    + "\ncrossdafer pos: " + (str(crossfaderMidiPos) if crossfaderMidiPos != None else str(prevCrossfaderMidiPos))
    + "\nknob pos: " + (str(knobMidiPos) if knobMidiPos != None else str(prevKnobMidiPos))
    + "\nactive control: " + activeControl)

    if(activeControl == "middle"):
        printblock += ("\nmiddle green: {}".format(MGreen)
            + "\nmiddle red: {}".format(MRed)
            + "\nmiddle blue: {}".format(MBlue))
    elif(activeControl == "left platter"):
        printblock += ("\nleft green: {}".format(LGreen)
            + "\nleft red: {}".format(LRed)
            + "\nleft blue: {}".format(LBlue))
    elif(activeControl == "right platter"):
        printblock += ("\nright green: {}".format(RGreen)
            + "\nright red: {}".format(RRed)
            + "\nright blue: {}".format(RBlue))

    printblock += ("\nyellow/euphoria: {}".format(yellow)
        + "\nstart: {}".format(start)
        + "\nback: {}".format(back)
        + "\nup: {}".format(up)
        + "\ndown: {}".format(down)
        + "\nleft: {}".format(left)
        + "\nright: {}".format(right))

    #print(printblock, end= "\r", flush = "True")

    '''send midi messages for this frame'''
    sendMidi(leftPlatterMidiPos, rightPlatterMidiPos, crossfaderMidiPos, knobMidiPos, buttonDeltas)
