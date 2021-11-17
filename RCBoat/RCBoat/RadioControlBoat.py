# !/usr/bin/python3
# RadioControlBoat - remote control boat with input from RC listener
# to use this need to:

from gpiozero import Device
from RCBoat.RadioControlListenerPeriodic import RadioControlListenerPeriodic
from RCBoat.RadioControlListenerReactive import RadioControlListenerReactive
from RCBoat.GpioZeroBoat import Boat


class RadioControlBoat(Boat):

    def __init__(self,
                 left=None, right=None, center=None,
                 rudder=None, pwm=True, pin_factory=None,
                 rcpins=None, quanti=10, pollRate=10,
                 reactive=False, *args):
        Boat.__init__(self,
                      left=left, right=right, center=center,
                      rudder=rudder, pwm=pwm, pin_factory=pin_factory,
                      *args)

        # Create RC Listener
        self.whenChanges(None) # call back on changes
        self.quanti=quanti # so we have the range of values returned
        if reactive:
            self.rcListener = RadioControlListenerReactive(rcpins,
                     quanti=quanti,
                     whenValueChanges=self.valueChanged,
                     whenHealthChanges=self.healthChanged,
                     pollRate=pollRate)
        else: # use periodic ...
            self.rcListener = RadioControlListenerPeriodic(rcpins,
                     quanti=quanti,
                     whenValueChanges=self.valueChanged,
                     whenHealthChanges=self.healthChanged,
                     pollRate=pollRate)

        # set the default modifiers to balance motors and servo
        self.thrustDelta = 1.0 # may need to be adjusted by servo range
        self.leftDelta = 1.0 # <= 1.0 so no pin given more that 1
        self.rightDelta = 1.0 # <= 1.0 so no pin given more that 1
        self.centerDelta = 1.0 # <= 1.0 so no pin given more that 1

        # for now make sure nothing is happening,
        # but in future may ad some diagnostics tests, e.g. servo travel
        self.toServo = 1.0 # need to define / calculate conversion from +/- 1.0 to servo max/min
        self.stop()
        self.rcListener.start()
        return

    def whenChanges(self, callback):
        self.changed = callback
        return

    def valueChanged(self, lastValue):
        '''
        A change in the RC values was flagged.
        lastValue is a list of then current values: [x, y]

        0.0 < y <= 1.0 - amount of forward thrust
        0.0 > y >= -1.0 - amount of backward thrust
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
        if self.changed is not None:
            self.changed(lastValue) # pass change to caller
        # print("valueChanged", lastValue)
        x, y = lastValue # 0 <= x, y <= 2 * quanti
        # Convert to -1.0 <= x, y <= 1.0
        q = self.quanti
        x = (x - q) / q
        y = (y - q) / q
        center = y # straight ahead
        rudder = x # (x + 1) / 2
        '''
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
        '''
        delta = x * self.thrustDelta
        if y < 0:
            delta = -delta # invert if going backwards
        left = y + delta
        right = y - delta
        # make sure we don't exceed limits
        left = min(1.0, left)
        right = min(1.0, right)
        center = min(1.0, center)
        rudder = min(1.0, rudder)
        left = max(-1.0, left)
        right = max(-1.0, right)
        center = max(-1.0, center)
        rudder = max(-1.0, rudder)
        # print("Setting LRC+:", int(100*left), int(100*right), int(100*center), int(100*rudder))
        left *= self.leftDelta
        right *= self.rightDelta
        center *= self.centerDelta
        rudder *= self.toServo
        # print("Actual LRC+:", int(100*left), int(100*right), int(100*center), int(100*rudder))
        self.value = (left, right, center, rudder)
        return

    def healthChanged(self, health):
        '''
        If any pin shows not working stop doing anything.
        '''
        print("health changed to:", health)
        ok = True
        for alive in health:
            ok = ok and alive
        if not ok:
            self.stop()
        return

    def cancel(self):
        self.rcListener.stop()


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

def runBoat(left, right, center, servo, rcpins):
    print("Not yet implemented!")
    return


if __name__ == '__main__':
    runBoat(None, None, None, None, None)