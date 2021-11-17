# !/usr/bin/python3
# TestBoat - remote control boat with Blue Dot
# to use this need to:
# sudo pip3 install bluedot

from gpiozero import Device

from RCBoat.RadioControlBoat import RadioControlBoat
from tkinter import Tk, Frame, Canvas, LAST, Label, E, W

from RCBoat.PWMGenerator import PWMGenerator

import cmath, math

# these imports for mock
# from gpiozero.pins.mock import MockFactory # makes mock available
# from gpiozero.pins.mock import MockPWMPin # to allow PWM


class TestBoat(RadioControlBoat):

    def __init__(self,
                 left=None, right=None, center=None,
                 rudder=None,
                 rcpins=None, quanti=10, pollRate=10,
                 reactive=False,
                 *args):
        RadioControlBoat.__init__(self,
                                  left=left, right=right, center=center,
                                  rudder=rudder, pwm=True,
                                  rcpins=rcpins, quanti=quanti, pollRate=pollRate,
                                  reactive=reactive,
                                  *args)
        self.motorW = 20
        self.motorL = 200
        self.rudderL = self.motorL
        self.rudderW = 2 * self.rudderL
        self.items = self.makeDisplay()
        x = 200
        y = 200
        self.tk.geometry(f"+{x}+{y}")
        print("items:", self.items)
        gpios = (*left, *right, *center, rudder)
        self.pins = []
        self.last = []
        for gpio in gpios:
            pin = Device.pin_factory.pin(gpio)
            pin.value = 0.5
            self.pins.append(pin)
            self.last.append(0.0)
        self.rudderMin = 0.05
        self.rudderMid = 0.075
        self.rudderMax = 0.1
        self.rudderRange = 0.05
        self.testI = 1
        self.rudder.min()

        # for callback ...
        self.lMax = None
        self.lMin = None
        self.rMax = None
        self.rMin = None

        # start screen update
        # self.tk.after(1000, self.test) # listen every 1 secs
        self.tk.after(100, self.listen) # listen every 0.1 secs
        return

    def test(self):
        # rudder values
        rudderPin = self.pins[-1]
        if self.testI == 0:
            self.rudderMax = rudderPin.value
            self.rudderRange = self.rudderMax - self.rudderMin
            print("rudder", self.rudder, type(self.rudder))
            print("min", self.rudderMin, "mid", self.rudderMid, "max", self.rudderMax,
                   "range", self.rudderRange, "av", (self.rudderMax + self.rudderMin) / 2)
            self.rudder.min()
        elif self.testI == 1:
            self.rudderMin = rudderPin.value
            self.rudder.mid()
        elif self.testI == 2:
            self.rudderMid = rudderPin.value
            self.rudder.max()
        self.testI += 1
        if self.testI > 2:
            self.testI = 0
        self.tk.after(1000, self.test) # listen every 1 secs
        return

    def tidy(self):
        # here if Tk window stops
        self.cancel() # stop the boat too
        self.tk.destroy()

    def makeDisplay(self):
        ### construct display
        tk = Tk()
        frame = Frame(tk)
        frame.grid(row=1, column=1)
        box = Frame(frame)
        box.grid(row=0, column=1)
        left = Label(box, text="Left")
        left.grid(row=1, column=1, sticky=(E, W))
        right = Label(box, text="Right")
        right.grid(row=1, column=2, sticky=(E, W))
        self.left = left
        self.right = right
        # make frame subframe from now ...
        frame = Frame(frame, bg="white")
        frame.grid(row=1, column=1)
        width = max(7 * self.motorW, self.rudderW) + self.motorW * 2
        height = self.motorL + self.rudderL + self.motorW
        print("Canvas:", (width, height))
        # blue sea
        canvas = Canvas(frame, width=width, height=height, bg="blue")
        canvas.grid(row=1, column=1)
        # white boat
        canvas.create_oval(width // 2 - self.rudderL, self.motorL - self.rudderL, width // 2 + self.rudderL, self.motorL + self.rudderL, fill="white", outline="white")
        canvas.create_rectangle(width // 2 - self.rudderL, 0, width // 2 + self.rudderL, self.motorL, fill="white", outline="white")
        self.canvas = canvas

        # forward motor:
        lx, ly = (width - 5 * self.motorW) // 2, 0
        lfv, lbv = self.makeMotor(canvas, lx, ly)
        cx, cy =  (width - self.motorW) // 2, 0
        cfv, cbv = self.makeMotor(canvas, cx, cy)
        rx, ry = (width + 3 * self.motorW) // 2, 0
        rfv, rbv = self.makeMotor(canvas, rx, ry)
        rux, ruy = (width - self.rudderW) // 2, self.motorL
        ruv = self.makeRudder(canvas, rux, ruy)
        self.tk = tk
        tk.protocol("WM_DELETE_WINDOW", self.tidy) # ensure we tidy up
        return ((lfv, lx, ly, 'f'), (lbv, lx, ly, 'b'), (None, lx, ly, 'p'),
                  (rfv, rx, ry, 'f'), (rbv, rx, ry, 'b'), (None, rx, ry, 'p'),
                  (cfv, cx, cy, 'f'), (cbv, cx, cy, 'b'), (None, cx, cy, 'p'),
                  (ruv, rux, ruy, 'r'))

    def makeMotor(self, canvas, x, y):
        ### construct motor
        canvas.create_rectangle(x, y, x + self.motorW, y + self.motorL, fill="brown")
        forward = canvas.create_rectangle(x, y, x + self.motorW, y + self.motorL // 2, fill="green")
        backward = canvas.create_rectangle(x, y + self.motorL // 2, x + self.motorW, y + self.motorL, fill="red")
        return (forward, backward)

    def makeRudder(self, canvas, x, y):
        ### construct rudder
        line = canvas.create_line(x + self.rudderW // 2, y, x + self.rudderW // 2, y + self.rudderL, fill="black", width=5, arrow=LAST)
        return line

    def adjust(self, item, x, y, itemType, pin):
        # print("adjust:", item, (x, y), itemType, int(pin * 100))
        if itemType == 'f': # motor forward pin
            f = pin * self.motorL // 2
            b = y + self.motorL // 2
            t = b - f
            self.canvas.coords(item, (x, t, x + self.motorW, b))
        elif itemType == 'b': # motor backward pin
            r = pin * self.motorL // 2
            t = y + self.motorL // 2
            b = t + r
            self.canvas.coords(item, (x, t, x + self.motorW, b))
        elif itemType == 'r': # rudder pin
            # print("angle (pin * 10000): ", int(pin * 10000))
            # pin for rudder is 5/100 <= pin <= 10/100
            # print("adjust:", item, (x, y), itemType, int(pin * 1000)/1000.0)
            offset = pin - self.rudderMin
            fraction = (offset) / self.rudderRange # value 0 - 1
            angle = math.pi * (0.0 + (0.5 - fraction) / 2.0) # angle in radians  pi + pi/4 to pi + 3pi/4
            # print("rudder: offset =", int(1000*offset)/1000.0, "fraction =", int(100*fraction)/100.0, "angle =", int(100*angle)/100.0)
            cangle = cmath.exp(angle*1j)
            t = y
            b = t + self.rudderL
            c = x + self.rudderW // 2
            center = complex(c, t) # top center
            coordinates = ((c, t), (c, b)) # top center to bottom center
            new = []
            for x, y in coordinates:
                v = cangle * (complex(x, y) - center) + center
                new.append(int(v.real))
                new.append(int(v.imag))
                # print((x, y), "=>", (int(v.real), int(v.imag)))
            self.canvas.coords(item, *tuple(new))
        elif itemType == 'p': # pwm pin
            # ignore for now
            # print("PWM:", pin)
            pass
        else:
            print("unknown item:", itemType)
        return

    def listen(self):
        # update display
        last = []
        same = True
        for i in range(len(self.pins)):
            value = self.pins[i].state
            # print(i, self.pins[i], value, type(value))
            if isinstance(value, bool):
                value = int(value)
            same = same and (value == self.last[i])
            last.append(value)
        if not same:
            for i in range(len(self.pins)):
                self.adjust(*self.items[i], last[i])
            self.last = last
        self.tk.after(100, self.listen) # listen every 0.1 secs
        return

    def showChange(self, lastValue):
        left, right = lastValue
        if self.lMin is None:
            self.lMin = left
        if self.lMax is None:
            self.lMax = left
        if self.rMin is None:
            self.rMin = right
        if self.rMax is None:
            self.rMax = right
        self.lMin = min(self.lMin, left)
        self.lMax = max(self.lMax, left)
        self.rMin = min(self.rMin, right)
        self.rMax = max(self.rMax, right)
        text = "rudder: " + str(self.lMin) + " < " + str(left) + " < " + str(self.lMax) + "  ...  "
        self.left.configure(text=text)
        text = "  ...  motor: " + str(self.rMin) + " < " + str(right) + " < " + str(self.rMax)
        self.right.configure(text=text)
        return


def testBoat(left, right, center, servo, rcpins, reactive=False, TestHarness=False):
    viewBoat(None, None, None, None, None, reactive=reactive, TestHarness= TestHarness)
    return


def viewBoat(left, right, center, servo, rcpins, reactive=False, TestHarness=False):
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

    # hardware PWM: GPIO12, GPIO13, GPIO18, GPIO19

    PWMA = 18
    PWMB = 13
    PMWC = 12
    PMWD = 19
    if TestHarness:

        print("Running test with pins 13 & 18 connected to pins 4 & 5")
        # showThreads()
        print("Starting test signal on pins 13 & 18")
        # Using default pin factory fir the generator ...
        pmwGenerator = PWMGenerator(PWMB, PWMA) # if using cycle

        # comment out this line to use real pins
        # Device.pin_factory = MockFactory(pin_class=MockPWMPin)

        PWMA = 26
        PWMB = 16

    # for 3-pin motors:
    left = (20, 21, PMWD)
    right = (7, 1, PMWC)
    center = (23, 24, PWMA)

    # other pins
    servo = PWMB

    print("About to start")

    # this starts the boat
    print("Using RadioControlListener listening on 4 & 5")
    rcpins = (
        (4, 1569, 550), # set mid as 1/2 and range as 1/4 away from that
        (5, 1507, 412)  # set mid as 1/2 and range as 1/4 away from that
        )
    test = TestBoat(left, right, center, servo, rcpins=rcpins, reactive=reactive)
    test.whenChanges(test.showChange)
    test.tk.mainloop()

    # comment out these lines that shut down debug
    print("Now Finished")
    if TestHarness:
        pmwGenerator.cancel()
    test.stop()
    return

def showChange(lastValue):
    print(lastValue)
    return

if __name__ == '__main__':
    pass
