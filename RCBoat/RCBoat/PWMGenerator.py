'''
Created on 23 Jul 2021

@author: Tinka
'''

import time, math
from gpiozero import PWMLED
from threading import Thread

class PWMGenerator():
    '''
    Simple base class to generate PWM output on 2 ports.
    The idea being to simulate the signals from receiver ports
    controlled by an RC controller.

    From data received:
    Motor:
    1095
    1400 - 1510
    1920
    average = 1507.5
    width = 412.5

    Rudder:
    1010
    1560
    2020
    average = 1515
    width = 505
    but mid rudder is 1560 so
    width = 550 or 460!

    Period = 1,000,000 / 50 = 20,000
    Use defaults of  maxDC = 2020/20000, minDC = 1010/20000
    '''

    def __init__(self, rudder, motor, maxDC=2020/20000, minDC=1010/20000, name="PWMGenerator"):
        '''
        Constructor takes two ports simulating the
        "rudder" and the "motor" signals.
        '''
        print("Initialising Thread object, name =", name)
        self.name = name
        self._thread = Thread(target=self.run, name=name)
        print("Initialising rest of this object")
        frequency = 50
        self.rudder = PWMLED(pin=rudder, initial_value=0, frequency=frequency)
        self.motor = PWMLED(pin=motor, initial_value=0, frequency=frequency)
        self.max = maxDC
        self.min = minDC
        self.ok = True
        period = 1000000 / frequency
        width = period * maxDC
        print("PWMGenerator: maxDC =", maxDC, "period =", period, "maxPW = ", width)
        width = period * minDC
        print("PWMGenerator: minDC =", minDC, "period =", period, "maxPW = ", width)
        self._thread.start()
        return

    def toPWM(self, value, maximum, minimum):
        '''
        Take input from -1 to +1 and return pwm to match
        '''
        offset = (maximum + minimum) / 2
        width = maximum - minimum
        size = value * width / 2
        return offset + size

    def run(self):
        base = time.time()
        '''
        print("PWMGenerator started")
        interval = 17 # every 1.7 seconds
        count = interval
        '''
        while self.ok:
            seconds = (time.time() - base)
            cycle = seconds / 60 # as a fraction of a minute
            theta = cycle * math.pi * 2
            cos = math.cos(theta)
            sin = math.sin(theta)
            self.rudder.value = self.toPWM(cos, self.max, self.min)
            self.motor.value = self.toPWM(sin, self.max, self.min)
            '''
            count -= 1
            if count < 0:
                print("Current generator values: rudder =", self.rudder.value*1000, cos,
                      ",motor =", self.motor.value*1000, sin)
                count = interval
            '''
            time.sleep(0.1) # try to make it fairly smooth
        return

    def cancel(self, timeout=None):
        print("Stopping", self.name)
        self.ok = False
        self.join(timeout)
        print(self.name, "Stopped")
        return

    def join(self, timeout=None):
        self._thread.join(timeout)
        return

if __name__ == "__main__":
    signal = PWMGenerator(13, 18) # send on pins 13, and 18
    signal.join() # wait till ends - basically forever

