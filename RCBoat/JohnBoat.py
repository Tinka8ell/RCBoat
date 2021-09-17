# !/usr/bin/python3
"""
JohnBoat is the main implementation of remote control boat with Blue Dot.

It was created to match the spec for John's model boat.
Details are listed below.
"""

from gpiozero import LED

from RCBoat.ControlledBoat import ControlledBoat
from RCBoat.DisplayBoat import DisplayBoat
from RCBoat.GpioZeroBoat import GPIOZeroBoat
from RCBoat.RadioControlListener import RadioControlListener
from RCBoat.CommsController import CommsServer, CommsReceiver, CommsListener
from threading import Thread, Lock

class RCController(CommsServer):

    def __init__(self, rcListener):
        self.rcListener = rcListener
        return

    '''
    These methods must be overwritten
    '''

    def makeReceiver(self):
        # make a receiver object using self.setup
        # print("CommServer.makeReceiver()")
        return RCCommsReceiver(self.rcListener)

    def makeListener(self, connection):
        # make a CommsListener object from connection info
        # this can also reset self.receiver to cause a new one to start
        listener = None
        if connection:
            # do we need controller here?
            listener = RCCommsListener(connection, controller=self.controller)
        return listener
    

class RCCommsReceiver(CommsReceiver):

    def __init__(self, setup=None):
        # print("CommsReceiver")
        if setup:
            self.setup(setup)
        return

    def setup(self, setup):
        self.rcListener = setup
        self.lock = Lock()
        return

    def accept(self):
        self.lock.acquire()
        return self.rcListener

    def close(self):
        self.lock.release()
        return


class RCCommsListener(CommsListener):
    '''
    Listener is a threaded device to listen for messages.

    Listener is started with a receiver and a defined controller object.
    '''

    def __init__(self, connection, controller=None):
        super().__init__(connection, controller)
        return

    #
    # these should be overridden
    #

    def makeReceiver(self, connection):
        # turn a connection into the receiver
        return MessageReceiver(setup=connection)

    def execute(self, message):
        # should be overridden
        x = 1
        y = -1
        if message[0].lower() == "p":
            self.controller.press(self.connectionId, x, y)
        elif message[0].lower() == "m":
            self.controller.move(self.connectionId, x, y)
        elif message[0].lower() == "l":
            self.controller.lift(self.connectionId, x, y)
        elif message[0].lower() == "d":
            self.controller.double(self.connectionId, x, y)
        elif message[0].lower() == "c":
            self.receiver.close()
        elif message[0].lower() == "e":
            raise Exception("Disconnected by exception")
        return
    



if __name__ == '__main__':
    from RCBoat.PWMGenerator import PWMGenerator
    '''
    The raspberry pi pins (taken from outout from pinout with added *'s) are:
    J8:
        3V3  (1) (2)  5V
    **GPIO2  (3) (4)  5V
    **GPIO3  (5) (6)  GND
      GPIO4  (7) (8)  GPIO14
        GND  (9) (10) GPIO15
     GPIO17 (11) (12) GPIO18*
     GPIO27 (13) (14) GND
     GPIO22 (15) (16) GPIO23
        3V3 (17) (18) GPIO24
     GPIO10 (19) (20) GND
      GPIO9 (21) (22) GPIO25
     GPIO11 (23) (24) GPIO8
        GND (25) (26) GPIO7
      GPIO0 (27) (28) GPIO1
      GPIO5 (29) (30) GND
      GPIO6 (31) (32) GPIO12*
    *GPIO13 (33) (34) GND
    *GPIO19 (35) (36) GPIO16
     GPIO26 (37) (38) GPIO20
        GND (39) (40) GPIO21

    As
    ** I2C (for turrets) uses:
    Data:  (GPIO2)
    Clock: (GPIO3)
    and
    * hardware PWM is on pins:
    GPIO12, GPIO13, GPIO18, GPIO19

    Suggest use:
    GPIO14, GPIO15, GPIO18* - use GPIO26
    GPIO5, GPIO6, GPIO13* - use GPIO23
    GPIO20, GPIO26, GPIO19*
    for the H-bridge motors
    and GPIO12* for the servo for the ruder
    So you can make use of the hardware PWM
    and have each motor use 3 pins close to each other

    for testing will use GPIO13 & GPIO18 for the PWMGenerator
    so will need different pins for the motors, but as we are using
    virtual Pins not a problem.
    '''
    TestHarness =  True

    PWMA = 18
    PWMB = 13
    if TestHarness:
        PWMA = 26
        PWMB = 23

        print("Running test with pins 13 & 18 connected to pins 4 & 5")
        # showThreads()
        print("Starting test signal on pins 13 & 18")
        pmwGenerator = PWMGenerator(13, 18) # if using cycle
        # wGenerator = BlueDotPWMGenerator(13, 18) # if using BlueDot

    print("Just loading RadioControlListener listening on 4 & 5")
    rcListener = RadioControlListener(
        (
            (4, 1569, 550), # set mid as 1/2 and range as 1/4 away from that
            (5, 1507, 412)  # set mid as 1/2 and range as 1/4 away from that
            ),
            smoothing=1,
            name="Main"
        )


    noDisplay = False  # True # if don't want a visualisation ...

    # for 3-pin motors:
    left = (20, 21, 19)
    right = (7, 1, 12)
    center = (23, 24, PWMA)

    # other pins
    servo = PWMB
    switchPin = 16  # used for pi on indicator

    guns = None
    '''
    Turrets are not supported as they cannot be controlled

    # Turret controls
    expandor2 = 0  # should be 1 if 2 expanders ...
    # smaller rear facing port turret - 2nd expander, PortA, ls Nible (from 0 to 8)
    g1a = Turret(8, (expandor2, 0, 0))
    # smaller rear facing starboard turret - 2nd expander, PortB, ls Nible (from 0 to 8)
    g1b = Turret(8, (expandor2, 1, 0))
    g2 = Turret(8, (0, 0, 0))    # port pair - PortA, ls Nible (from 0 to 8)
    # starboard pair - PortB, ls Nible (from 0 to 8)
    g3 = Turret(8, (0, 1, 0))
    guns = (g1a, g1b, g2, g3)
    '''

    print("Boat about to start")
    # create and also start the boat:
    boat = GPIOZeroBoat(left, right, center, servo,
                        gun=guns)  # boat with added turrets
    # GPIOZeroBoat is just the boat with no controller ...

    controller = RCController(rcListener)


    if noDisplay:
        # create a test boat with controller
        test = ControlledBoat(boat=boat, controller=controller)
    else:
        displayBoat = DisplayBoat()
        # create a test boat with controller
        test = ControlledBoat(
            boat=boat, listener=displayBoat, controller=controller)

    # create a switch
    switch = LED(switchPin)
    # and turn it on
    switch.on()
    print(f"Switch on pin {switchPin}?")

    if noDisplay:
        # wait for input (which should never come)
        text = input("Wait Till Finished")
        print("received:", text)
        # stop the boat
        boat.stop()
    else:
        tk = displayBoat.tk
        tk.mainloop()
        test.shutdown()
    print("Boat stopped")

    # turn switch off
    switch.off()
    print(f"Switch off pin {switchPin}?")
