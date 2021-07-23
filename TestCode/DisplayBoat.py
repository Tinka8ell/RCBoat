# !/usr/bin/python3
# DisplayBoat - boat listener with display
"""
To enable visualisation and so test the control code
a virtual boat was created to react to changes detected.

It also doubles as a threaded environment to allow the other code
to run without immediately terminating after starting.
"""

import cmath
import math
from tkinter import Tk, Toplevel, Frame, Canvas, LAST

from TestCode.BoatListener import BoatListener


def dp2(number):
    return format(number, "03.2f")


class DisplayDevice(Canvas):

    def __init__(self, parent, w, h, bg="blue"):
        Canvas.__init__(self, parent, width=w, height=h, bg=bg,
                        borderwidth=0, highlightthickness=0)
        self.width = w
        self.height = h
        self.parent = parent
        self.makeDisplay()
        return

    def makeDisplay(self):
        return

    def adjust(self, value, item=0):
        # adjust the display to show value for the item
        return


class DisplayMotor(DisplayDevice):

    def makeDisplay(self):
        self.create_rectangle(0, 0, self.width, self.height, fill="brown")
        self.forward = self.create_rectangle(
            0, 0, self.width, self.height // 2, fill="green")
        self.backward = self.create_rectangle(
            0, self.height // 2, self.width, self.height, fill="red")
        return

    def adjust(self, value, item=0):
        element = None
        w = self.width
        h = self.height // 2
        t = 0
        b = 0
        if item == 0:  # forward
            element = self.forward
            b = h
            t = (1 - value) * h
        elif item == 1:  # backward
            element = self.backward
            t = h
            b = (1 + value) * h
        self.coords(element, (0, t, w, b))
        return


class DisplayMotors(DisplayDevice):

    def __init__(self, parent, w, h, number, bg="blue"):
        self.motors = []
        self.number = number
        DisplayDevice.__init__(self, parent, w, h, bg=bg)
        return

    def makeDisplay(self):
        self.create_rectangle(0, 0, self.width, self.height,
                              fill="white", outline="white")
        number = self.number
        w = self.width // (2 * number - 1)
        if number == 1:  # only central motor
            motor = DisplayMotor(self.parent, w, self.height, bg="white")
            self.create_window(
                (self.width // 2, self.height // 2), window=motor)
            self.motors.append(motor)
        elif number == 2:  # only left and right motors
            motor = DisplayMotor(self.parent, w, self.height, bg="white")
            self.create_window(
                ((self.width // 2) - w, self.height // 2), window=motor)
            self.motors.append(motor)  # left
            motor = DisplayMotor(self.parent, w, self.height, bg="white")
            self.create_window(
                ((self.width // 2) + w, self.height // 2), window=motor)
            self.motors.append(motor)  # right
        elif number == 3:  # all three
            motor = DisplayMotor(self.parent, w, self.height, bg="white")
            self.create_window(((self.width // 2) - 2 * w,
                                self.height // 2), window=motor)
            self.motors.append(motor)  # left
            motor = DisplayMotor(self.parent, w, self.height, bg="white")
            self.create_window(((self.width // 2) + 2 * w,
                                self.height // 2), window=motor)
            self.motors.append(motor)  # right
            motor = DisplayMotor(self.parent, w, self.height, bg="white")
            self.create_window(
                (self.width // 2, self.height // 2), window=motor)
            self.motors.append(motor)  # center
        return

    def adjust(self, value, item=0):
        i = item // 2  # 0 - 5 => 0 - 2
        j = item % 2  # 0 - 5 => 0 or 1
        self.motors[i].adjust(value, j)
        return


class DisplayRudder(DisplayDevice):

    def makeDisplay(self):
        w = self.width // 2
        self.create_oval(0, -w, 2 * w, w, fill="white", outline="white")
        l = 3 * w // 4
        self.w = w
        self.l = l
        self.rudder = self.create_line(
            w, 0, w, l, fill="black", width=w // 10, arrow=LAST)
        return

    def adjust(self, value, item=0):
        # ## print("angle (value * 10000): ", int(value * 10000))
        # value for rudder is 5/100 <= value <= 10/100
        self.rudderMin = 0.05
        self.rudderRange = 0.05
        w = self.w
        l = self.l
        offset = value - self.rudderMin
        fraction = (offset) / self.rudderRange  # value 0 - 1
        # angle in radians  pi + pi/4 to pi + 3pi/4
        angle = math.pi * (0.0 + (0.5 - fraction) / 2.0)
        # ## print("rudder: offset =", int(1000*offset)/1000.0,
        # ##       "fraction =", int(100*fraction)/100.0,
        # ##       "angle =", int(100*angle)/100.0)
        cangle = cmath.exp(angle * 1j)
        t = 0
        b = l
        c = w
        center = complex(c, t)  # top center
        coordinates = ((c, t), (c, b))  # top center to bottom center
        new = []
        for x, y in coordinates:
            v = cangle * (complex(x, y) - center) + center
            new.append(int(v.real))
            new.append(int(v.imag))
            # ## print((x, y), "=>", (int(v.real), int(v.imag)))
        self.coords(self.rudder, *tuple(new))
        return




class DisplayBoat(BoatListener):
    '''
    Represent the boat.
    The basic shape is
       a point at the front,
       a fore deck,
       a rear deck,
       an aft section containing 1, 2 or 3 engines and a rudder.
    The requirement is worked out from the related boat object.
    Motors are either:
       one central,
       two side-by-side, or
       two side-by-side with one central.
    '''

    def __init__(self, tk=None):
        # Sort out the graphics basis ...
        if tk:
            self.tk = Toplevel(tk)
        else:
            self.tk = Tk()

        # define model
        self.motorW = 8  # 20
        self.motorL = self.motorW * 12  # 10
        self.rudderL = 1 * self.motorL // 2
        self.rudderW = 2 * self.rudderL
        self.makeDisplay()
        x = 100
        y = 100
        self.tk.geometry(f"+{x}+{y}")

        self.rudderMin = 0.05
        self.rudderMid = 0.075
        self.rudderMax = 0.1
        self.rudderRange = self.rudderMax - self.rudderMin
        return

    def makeDisplay(self):
        # construct display in the "tk" toplevel window
        display = Frame(self.tk, bg="white")
        display.grid(row=1, column=1)
        boatWidth = max(7 * self.motorW, 2 * self.rudderL)
        width = boatWidth + self.motorW * 2
        # boat is triangle (length = width), mid section, engines and rudder
        w = width
        bw2 = boatWidth // 2  # half boatWidth
        c = w // 2  # center line
        t = self.motorW  # top
        s = t  # side gap
        m = t + boatWidth  # top of main section
        a = m + 3 * boatWidth  # top of aft section
        e = a + self.motorL // 2  # center of engines
        b = a + self.motorL  # top of back end
        r = b + bw2 // 2  # center of rudder
        bb = b + bw2  # bottom of the boat
        boatLength = bb - self.motorW
        length = bb + self.motorW
        canvas = Canvas(display, width=width, height=length, bg="blue")
        canvas.grid(row=1, column=1)
        bow = canvas.create_polygon(
            ((c, t), (s, m), (w - s, m)), fill="white", outline="white")
        hull = canvas.create_rectangle(
            ((s, m), (w - s, b)), fill="white", outline="white")
        aft = canvas.create_oval(
            ((s, b - bw2), (w - s, b + bw2)), fill="white", outline="white")
        self.canvas = canvas  # Canvas in which we draw
        self.dims = (s, c, bw2, e, r)  # for added
        return

    def added(self, boat):
        # use boat to discover what we need to know to draw the moving parts...
        self.boat = boat
        # first look at number of engines ...
        self.number = len(boat.motors)

        # set up main dimensions (framework)
        canvas = self.canvas  # where to draw things
        s, c, bw2, e, r = self.dims
        boatWidth = 2 * bw2
        w = 2 * c

        # create aft section, motors and rudder
        number = self.number
        mw = (2 * number - 1) * self.motorW
        self.motors = DisplayMotors(
            canvas, mw, self.motorL, number, bg="white")
        canvas.create_window((c, e), window=self.motors)
        self.rudder = DisplayRudder(canvas, boatWidth, bw2, bg="blue")
        canvas.create_window((c, r), window=self.rudder)

        # make sure all is drawn
        self.tk.update_idletasks()

        # then set default locations
        for i in range(6):
            self.motors.adjust(0, item=i)
        self.rudder.adjust(self.rudderMid)
        return

    def update(self, *values):
        # ## print("update: len", len(values), "values =", values)
        # update display
        number = self.number  # calcualte from actual motors provided!
        for i in range(number * 2):
            self.motors.adjust(values[i], item=i)
        self.rudder.adjust(values[number * 2])
        return


if __name__ == '__main__':
    # for testing
    pass
