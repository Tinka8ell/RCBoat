'''
Created on 11 Nov 2021

@author: Tinka
'''

from RCBoat.RadioControlListener import RadioControlListener
from time import sleep


class RadioControlListenerReactive(RadioControlListener):

    def run(self):
        '''
        print("RCListener started")
        interval = 17 # every 1.7 seconds?
        count = interval
        '''
        while self.ok:
            sleep(self.period)
            health = self.checkPins()
            value = self.value()
            '''
            if self.name == "Main":
                print(self.name, "health =", health, "value =", value)
            '''
            changed = False
            healthChanged = False
            for i in range(len(value)):
                healthChanged = healthChanged or (self.health[i] != health[i])
                self.health[i] = health[i]
                change = int(value[i] - self.lastValue[i])
                '''
                if self.name == "Main" and i == 0:
                    print("health =", health[i], "value =", value[i], "change =", change)
                '''
                if not health[i]: # this listener is dead!
                    change = - self.lastValue[i] # centre the stick
                elif self.smoothing > 0 and change != 0: # limit rate of change
                    if change > 0:
                        change = max(change, self.smoothing)
                    if change < 0:
                        change = min(change, -self.smoothing)
                if change != 0:
                    changed = True
                    self.lastValue[i] += change
            if changed:
                # print(self.name, "Changed:", self.lastValue)
                if self.whenValueChanged is not None:
                    self.whenValueChanged(self.lastValue)
            if healthChanged:
                if self.whenHealthChanged is not None:
                    self.whenHealthChanged(self.health)
            '''
            count -= 1
            if count < 0:
                print("Current listener value:", self.lastValue)
                self.debugValue()
                count = interval
            '''
        print(self.name, "heart beat stopped")
        return



if __name__ == "__main__":
    print("Nothing to run in RadioControllerReactive.py")
