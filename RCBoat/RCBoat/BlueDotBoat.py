# !/usr/bin/python3
# BlueDotBoat - remote control boat with Blue Dot
# to use this need to:
# sudo pip3 install bluedot

from gpiozero import Device

from bluedot import BlueDot, BlueDotPosition, BlueDotSwipe, BlueDotRotation
from RCBoat.GpioZeroBoat import Boat
import sys


class BlueDotBoat(Boat):

    def __init__(self, left=None, right=None, center=None, rudder=None, pwm=True, pin_factory=None, *args):
        Boat.__init__(self, left=left, right=right, center=center, rudder=rudder, pwm=pwm, pin_factory=pin_factory, *args)

        # these will be for first (or only) connection and control boat movement
        #  we could add code to control turrets, streaming video, etc on subsequent connects
        self.bd = BlueDot() # open up and wait for connections
        self.bd.when_client_connects = self.client_connects
        self.bd.when_client_disconnects = self.client_disconnects
        self.bd.when_moved = self.moved
        self.bd.when_pressed = self.pressed
        self.bd.when_released = self.released
        # self.bd.when_double_pressed = self.double_pressed
        # self.bd.when_rotated = self.rotated
        # self.bd.when_swiped = self.swiped

        # set the default modifiers to balance motors and servo
        self.thrustDelta = 1.0 # may need to be adjusted by servo range
        self.leftDelta = 1.0 # <= 1.0 so no pin given more that 1
        self.rightDelta = 1.0 # <= 1.0 so no pin given more that 1
        self.centerDelta = 1.0 # <= 1.0 so no pin given more that 1

        # for now make sure nothing is happening,
        # but in future may ad some diagnostics tests, e.g. servo travel
        self.toServo = 1.0 # need to define / calculate conversion from +/- 1.0 to servo max/min
        self.stop()
        return

    def client_connects(self):
        print("client_connects")
        self.bd.square=True
        self.bd.color ="green"
        # in future this will allow us to get a second connection for other options
        return

    def client_disconnects(self):
        print("client_disconnects")
        self.stop() # stop motors
        # for now we just terminate, but this should have some recovery logic.
        self.bd.stop() # stop listener
        sys.exit()
        return

    def moved(self, pos):
        self.pressed(pos)
        return

    def pressed(self, pos):
        '''
        Adjust motor and rudder acording to the position reported by BlueDot.

        Whether pressed and held, or moved take the position
        on the Green Square as forward / backward, left / right jpystick.
        0.0 < y <= 1.0 - amount of forward thrust
        0.0 > x >= -1.0 - amount of backward thrust
        0.0 < x <= 1.0 - amount of right turn
        0.0 > x >= -1.0 - amount of left turn
        All three motors will give an average of the forward or backward throttle,
        but the left and right motors will be modified by a delta based on the amount of turn.
        As the thrust of each motor is max'd out at 1.0,
        the delta has a cut off when one motor reaches full throttle.
        The ratio between turn and thrust delta should be adjustable / defineable.
            self.thrustDelta will define this, default is 1
        The ration of thrust to actual power of the motors should also be
        adjustable / defineable to balance any natural imperfections.
            self.leftDelta, self.rightDelta (and possibly) self.centerDelta covers this.
        '''
        x, y = pos.x, pos.y # -1.0 <= x, y <= 1.0
        left, right, center = y, y, y # straight ahead
        rudder = x # (x + 1) / 2
        if x < 0: # turn left
            if y < 0: # going backward
                cap = 1.0 + y # max amount we change by
                delta = - min(-x * self.thrustDelta, cap)
            else: # going forwards
                cap = 1.0 - y # max amount we change by
                delta = min(-x * self.thrustDelta, cap)
            left -= delta
            right += delta
        else: # turn right
            if y < 0: # going backward
                cap = 1.0 + y # max amount we change by
                delta = - min(x * self.thrustDelta, cap)
            else: # going forwards
                cap = 1.0 - y # max amount we change by
                delta = min(x * self.thrustDelta, cap)
            left += delta
            right -= delta
        # print("Setting LRC+:", int(100*left), int(100*right), int(100*center), int(100*rudder))
        left *= self.leftDelta
        right *= self.rightDelta
        center *= self.centerDelta
        rudder *= self.toServo
        # print("Actual LRC+:", int(100*left), int(100*right), int(100*center), int(100*rudder))
        self.value = (left, right, center, rudder)
        return

    def released(self, pos):
        '''
        Stop motor and center the rudder release reported by BlueDot.

        If you let go we stop doing anything.
        '''
        print("Released at:", pos)
        self.stop()
        return

    # the rest of this code is for debug only of extra functions ...

    def double_pressed(self, pos):
        print("double_pressed:\t", *self.show(pos))
        return

    def rotated(self, pos):
        print("rotated:\t", *self.show(pos))
        return

    def swiped(self, pos):
        print("swiped:\t", *self.show(pos))
        return

    def show(self, pos):
        show = (None, )
        if isinstance(pos, BlueDotPosition):
            x = int(pos.x * 1000)
            y = int(pos.y * 1000)
            xy = f"pos = ({x}, {y})"
            angle = int(pos.angle)
            a = f"a = {angle}"
            d = int(pos.distance * 1000)
            r = f"r = {d}"
            if not self.last:
                self.last = pos.time
            time = (self.last - pos.time) # int(* 1000)
            self.last = pos.time
            t = f"t = {time}"
            tmb = f"tmb = {pos.top}/{pos.middle}/{pos.bottom}"
            lmr = f"lcr = {pos.left}/{pos.middle}/{pos.right}"
            show = xy, a, r, t, tmb, lmr
        elif isinstance(pos, BlueDotSwipe):
            v = f"swipe = {pos.valid}"
            angle = int(pos.angle)
            a = f"a = {angle}"
            d = int(pos.distance * 1000)
            r = f"d = {d}"
            speed = int(pos.speed * 1000)
            s = f"s = {speed}"
            ud = f"ud = {pos.up}/{pos.down}"
            lr = f"lr = {pos.left}/{pos.right}"
            show = v, a, r, s, ud, lr
        elif isinstance(pos, BlueDotRotation):
            v = f"rotate = {pos.valid}"
            value = f"value = {pos.value}"
            a = f"anti = {pos.anti_clockwise}"
            c = f"clock = {pos.clockwise}"
            show = v, value, a, c
        return show


'''
the following is for testing only ...
'''
from time import sleep, time
from threading import Thread

class Listener(Thread):
    def __init__(self, *gpios):
        Thread.__init__(self)
        self.pins = []
        self.last = [time()]
        for gpio in gpios:
            self.pins.append(Device.pin_factory.pin(gpio))
            self.last.append(0)
        self.ok = True
        return

    def stop(self):
        print("Stopping listener")
        self.ok = False
        return

    def run(self):
        print("Starting listener")
        while self.ok:
            self.debug()
            sleep(0.1)
        print("Listener stopped")
        return

    def debug(self):
        line = ">>>"
        last = [time()]
        diff =  int((last[0] - self.last[0]) * 100)
        line += f" {diff}:"
        same = True
        i = 1
        for pin in self.pins:
            value = pin.state
            if isinstance(value, bool):
                value = 100 * int(value)
            elif isinstance(value, float):
                value = int(value * 100.0)
            last. append(value)
            same = same and (self.last[i] == value)
            line += " " + str(value)
            i += 1
        if not same:
            self.last = last
            print(line)
        return


if __name__ == '__main__':
    from gpiozero.pins.mock import MockFactory # makes mock available
    from gpiozero.pins.mock import MockPWMPin # to allow PWM

    Device.pin_factory = MockFactory(pin_class=MockPWMPin)

    left = (4, 14)
    right = (17, 18)
    center = (21, 22)
    servo = 24
    test = BlueDotBoat(left, right, center, servo)
    # test.debugOn()
    gpios = (*left, *right, *center, servo)
    listener = Listener(*gpios)
    print("About to start")
    listener.start()
    text = input("Wait Till Finished")
    print("received:", text)
    listener.stop()
    listener.join()
    test.stop()
