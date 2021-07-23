'''
Created on 23 Jul 2021

@author: Tinka
'''

from threading import Thread
import time, math
from gpiozero import PWMLED

class WavePWM(Thread):
    '''
    classdocs
    '''


    def __init__(self, rudder, motor):
        '''
        Constructor
        '''
        super().__init__()
        self.rudder = PWMLED(pin=rudder, initial_value=0, frequency=100)
        self.motor = PWMLED(pin=motor, initial_value=0, frequency=100)
        self.max = .75
        self.min = .25
        self.mid = (self.max + self.min) / 2
        self.range = self.max - self.min
        return

    def toPWM(self, value):
        '''
        Take input from -1 to +1 and return pwm to match
        '''
        size = value * self.range / 2
        offset = self.mid
        return offset + size

    def run(self):
        self.ok = True
        base = time.time()
        while self.ok:
            theta = (time.time() - base) / 30 # as a fraction of half a minute
            theta *= math.pi * 2
            cos = math.cos(theta)
            sin = math.sin(theta)
            self.rudder.value = self.toPWM(cos)
            self.motor.value = self.toPWM(sin)
            time.sleep(0.1) # try to make it fairly smooth
        return

if __name__ == "__main__":
    signal = WavePWM(13, 18) # send on pins 13, and 18
    signal.start()
    signal.join() # wait till ends - basically forever

