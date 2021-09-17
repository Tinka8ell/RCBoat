'''
Created on 4 Aug 2021

@author: Tinka
'''
from RCBoat.PWMGenerator import PWMGenerator
from bluedot import BlueDot
from threading import Lock

class BlueDotPWMGenerator(PWMGenerator):
    '''
    Extend the PWM simulator to use inputs from
    a BlueDot controller.  With x simulating the
    rudder output and y the motor output.
    '''

    def __init__(self, rudder, motor, maxDC=0.75, minDC=0.25): # should these be 0.075 and 0.025?
        '''
        Allow for single port definitions, or tuples
        providing port and max and min duty cycles.
        '''
        self.max = maxDC
        self.min = minDC
        self.maxRudder = self.max
        self.minRudder = self.min
        if isinstance(rudder, tuple):
            self.maxRudder = rudder[1]
            self.minRudder = rudder[2]
            rudder = rudder[0]
        self.maxMotor = self.max
        self.minMotor = self.min
        if isinstance(motor, tuple):
            self.maxMotor = motor[1]
            self.minMotor = motor[2]
            motor = motor[0]
        self._lock = Lock()
        self.bd = None
        super().__init__(rudder, motor, self.max, self.min)
        return

    def run(self):
        while self.ok:
            try:
                self.bd = BlueDot()
                print("Waiting for BlueDot connection")
                self.bd.wait_for_connection()
                print("BlueDot connected")
                self._lock.acquire() # make sure we are locked
                # connected so setup listener call backs
                self.bd.when_disconnected = self.disconnect # so we can get unlocked
                self.bd.when_double_pressed = self.press
                self.bd.when_pressed = self.press
                self.bd.when_released = self.lift
                self.bd.when_moved = self.press
                print("Waiting for disconnect")
                self._lock.acquire() # wait until released by disconnect
                print("BlueDot disconnected")
            except:
                self.bd = None
        return

    def pwm(self, x, y):
        self.rudder.value = self.toPWM(x, self.maxRudder, self.minRudder)
        self.motor.value = self.toPWM(y, self.maxRudder, self.minMotor)
        return

    def disconnect(self):
        self._lock.release() # so run can continue
        return

    def lift(self, pos):
        # let motor stay where it was, but rudder return to mid
        y = pos.y # rudder to 0
        self.pwm(0, y)
        return

    def press(self, pos):
        x, y = pos.x, pos.y
        self.pwm(x, y)
        return

    def cancel(self, timeout=None):
        super().cancel(timeout=0.1) # might not stop thread if waiting for disconnect
        if self.bd is not None:
            if self.bd.is_connected():
                self.disconnect() # leave internal loop
            self.bd = None
        self.join(timeout)
        return



if __name__ == "__main__":
    signal = BlueDotPWMGenerator(13, 18) # send on pins 13, and 18
    signal.join() # wait till ends - basically forever
