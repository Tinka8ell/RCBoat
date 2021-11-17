'''
Created on 11 Nov 2021

@author: Tinka
'''

from RCBoat.RadioControlListener import RadioControlListener
from time import sleep
import numpy as np

SPAN = 20 # using 20 periods at 50 Hz then gives values every 0.4 seconds
DEBUG_SPAN = 1000

class RadioControlListenerPeriodic(RadioControlListener):

    def run(self):
        '''
        Capture values over a SPAN number of periods.
        Respond with values averaged over the count every SPAN periods.
        '''
        numValues = len(self.listeners) # number of values read each time
        allValues = np.zeros([numValues, SPAN])
        ticks = 0
        dticks = 0
        while self.ok:
            sleep(self.period)
            health = self.checkPins()
            value = self.value()
            # process values and health
            healthChanged = False
            for i in range(numValues):
                healthChanged = healthChanged or (self.health[i] != health[i])
                self.health[i] = health[i]
                if not health[i]: # this listener is dead!
                    value[i] = 0 # centre the stick
                allValues[i, ticks] = value[i]
            if healthChanged:
                if self.whenHealthChanged is not None:
                    self.whenHealthChanged(self.health)
            # repeat ...
            ticks += 1
            if ticks >= SPAN:
                # send the average values and reset to repeat
                averageValue = allValues.mean(1).tolist()
                if self.whenValueChanged is not None:
                    self.whenValueChanged(averageValue)
                ticks = 0
                allValues = np.zeros([numValues, SPAN])
            dticks += 1
            if dticks >= DEBUG_SPAN:
                dticks = 0
                self.debugValue()
        print(self.name, "heart beat stopped")
        return



if __name__ == "__main__":
    print("Nothing to run in RadioControllerPeriodic.py")
