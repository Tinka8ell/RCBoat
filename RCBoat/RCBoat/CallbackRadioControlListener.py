'''
Created on 28 Jul 2021

@author: Tinka
'''

from threading import Thread
from time import sleep
import math

'''
Only works on a pi with pigpio installed and the deamon running
pip3 install pigpio      # to install
sudo pigpiod             # to start daemon
'''
EXCEPTION = None
try:
    # print("Importing pigpio")
    import pigpio
    # print("Import successful")
except ModuleNotFoundError as e:
    # print("Import failed")
    EXCEPTION = e
if EXCEPTION is not None:
    print("You're either not running on a Pi, or it is not set up.")
    print("Install pigpio with:")
    print("   pip3 install pigpio")
    print("Start pigpio daemon with:")
    print("   sudo pigpiod")
    # raise EXCEPTION


def quantum(value, maximum, minimum, quanti):
    '''
    A Quantum = (MAX - MIN) / (quanti * 2)
    Value = int((value - MIN + (Quantum / 2)) / Quantum) - quanti (i.e. the expected quantum values)
    '''
    if quanti is None:
        quanti = 0
    quanti = int(quanti)  # ensure it is int, not an int as a float
    q = value  # is value if not set quanti
    # print("q", q)
    if quanti != 0:
        q = 0  # if range is zero, return 0 instead of divide by zero
        if maximum is None or minimum is None:
            maximum = minimum = 0  # so unit will also be 0!
        # print("q", q)
        unit = (maximum - minimum) / (quanti * 2.0)
        # print("unit", unit)
        if unit != 0:
            adjusted = (value - minimum + (unit / 2.0))
            # print("adjusted", adjusted)
            units = adjusted / unit
            # print("units", units)
            q = int(units) - quanti
            # print("q", q)
    return q


def dutyCycle(high, period):
    """
    Returns the PWM duty cycle percentage.
    """
    value = 0.0
    if high is not None and period is not None and period != 0:
        value = 100.0 * high / period
    return value


class RadioControlListenerError(Exception):
    """Exception raised for errors in the HeartBeat object.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        super().__init__()
        self.message = message


class RadioControlListener(object):
    '''
    RadioControlListener
    Takes as input:
        a list of pins, mid points and widths
        (optional) quanti - defaults to 10
        (optional) callback (whenValueChanged?)
        (optional) heart beat rate (default 60 bpm)
        Might also consider a "smoothing" size
            - number of last readings to average over ...
    Internally creates
        a list PWMListeners
        a HeartBeatMonitor
    Has a view() method to see the current values of the pins as a list
    Can also set and remove the whenValueChanged callback.
    Can be polled using value(),
    or have the callback invoked whenever there is a change detected.
    Quanti sets the number of increments of values (0 to +/- quanti).
    Default will be 10 giving 21 quantum values from
    MID and 10 steps out to MAX and MIN values.
    Will use the Pulse Width for the basis of the values.
    HeartBeat will poll the PWMListeners to check they are still alive.
    The callback will be triggered from a separate thread
    which will run in a wait loop waiting on a lock.
    This will be to disconnect the callback from the listener threads.
    This lock will be triggered by any callback from the PWMListeners
    and will check that the current value has not already been sent.
    This thread will then call the RadioControlListener callback,
    '''

    def __init__(self, pins,
                 quanti=10,
                 whenValueChanges=None,
                 pollRate=60):
        '''
        Constructor
        '''
        # print("RadioControlListener: Creating with pins =", pins)
        self.whenValueChanges(whenValueChanges)  # call back
        self.whenHealthChanges(None)  # no call back
        self.quanti = quanti  # set to 0 to not use quantum vaulues

        self.listeners = []
        ok = isinstance(pins, tuple)
        if ok:
            for pin in pins:
                ok = ok and isinstance(pin, tuple) and (len(pin) == 3)
        if not ok:
            message = str(self.__class__)
            message += " requires pins as a tuple of pins,"
            message += "\nEach pin consists of a tuple of gpio, midPW and PWrange"
            raise RadioControlListenerError(message)
        for pin in pins:
            gpio, pwMid, pwRange = pin
            self.listeners.append(PWMListener(gpio,
                                              pwMid,
                                              pwRange,
                                              quanti=quanti,
                                              whenValueChanges=self.changeSeen))
        self.lastValue = self.value()

        # Listeners are all set up, now can set up things that may call them
        self.heartBeat = HeartBeat(self.checkPins, when_stopped=self.hasDied, period=60/pollRate)
        self.heartBeat.start()
        return

    def whenValueChanges(self, callback):
        self.whenValueChanged = callback
        # print("RadioControlListener: Set the whenValueChanged callback to", callback)
        return

    def whenHealthChanges(self, callback):
        self.whenHealthChanged = callback
        # print("RadioControlListener: Set the whenHealthChanged callback to", callback)
        return

    def checkPins(self):
        '''
        Called from HeartBeat to check all the pins:
        if any pin has died then it will return died as True
        '''
        died = False
        for listener in self.listeners:
            died = died or listener.check()
        return died

    def value(self):
        '''
        List of current values of the listeners
        '''
        values = []
        for listener in self.listeners:
            values.append(listener.value())
        return values

    def hasDied(self):
        '''
        Called when any some listener is discovered to have died
        to close down all listeners and heart beat and tell user we are dead.
        '''
        # print("RadioControlListener: Oh dear we are dead!")  # something else need to go here!
        for listener in self.listeners:
            listener.whenValueChanged = None
            listener.zero()  # so everything defaults!
        self.heartBeat.whenHealthChanged = None
        if self.whenValueChanged is not None:
            self.whenValueChanged(self.value())
        if self.whenHealthChanged is not None:
            self.whenHealthChanged(self.value())
        return

    def changeSeen(self, value):
        '''
        Change in value of a listener was detected.

        Ignore the value passed as we are only interested in the
        value of all the listeners.
        Get value of all listeners and if changed since last time
        let our listener know the new value.
        '''
        # print("RadioControlListener: Seen a change:",  value)
        value = self.value()
        if value != self.lastValue:
            # print("Check value changed, last:", self.lastValue, ", new:", value)
            self.lastValue = value
            if self.whenValueChanged is not None:
                self.whenValueChanged(value)
        return


class PWMListener(object):
    '''
    PWMListener
    Takes as input
        a gpio pin number
        mid point or PW range
        range of PW from mid point
        (optional) quanti, defaults to 10
        (optional) callback (whenValueChanged?)
    Has a check() method to see if any PWM have been received
    since last call and so confirm that it is still "alive".
    Has a view() method to see the current value of the pin.
    Can also set and remove the whenValueChanged callback.
    Can be polled using value(),
    or have the callback invoked whenever there is a change detected.
    Quanti sets the number of increments of values (0 to +/- quanti).
    Default will be 10 giving 21 quantum values from
    MID and 10 steps out to MAX and MIN values.
    Will use the Pulse Width for the basis of the values.
    Does not use auto ranging, but defaults to given mid point
    and assumes that values lie between mid point +/- width.
    Any value setting the period sets the "alive" state to True.
        We expect this to happen 50 times or more a second.
    Calling check() will return the "isDead" state,
        and then set it to False.
        Won't happen until we start first period.
    Current value is calculated by:
        pwRange = supplied width
        QuantumSize = pwRange / (quanti * 2)
        min = mid point - pwRange
        Value = int((pwValue - min + (QuantumSize / 2)) / Quantum) - quanti
            (i.e. the expected quantum values)
    The callback (whenValueChanged) will be called any time Value is
    different from last time, or maybe if Value has been different
    for a number of values?
    '''

    def __init__(self,
                 gpio,
                 pwMid,
                 pwRange,
                 quanti=10,
                 whenValueChanges=None
                 ):
        '''
        Constructor
        '''
        # print("PWMListener: Creating with pin =", pin, " and DCRange =", DCRange)
        self.whenValueChanges(whenValueChanges)  # call back
        self.quanti = quanti  # set to 0 to not use quantum values
        self.pin = gpio

        # working variables
        self._period = None  # time between change to high in microseconds
        self._high = None  # time between change to high and change to low in microseconds

        self._max = pwMid + pwRange
        self._min = pwMid - pwRange
        self._mid = pwMid
        self._significant = (pwRange / quanti) / 4 # start at a quarter of a quantum

        self._pmax = None
        self._pmin = None

        self.hasStarted = False # so we can detect first period being seen
        self.died = self.hasStarted # can't die before started
        self.last = 0 # start with value of 0 (mid point of any quantum range)

        """
        Instantiate with the Pi and gpio of the PWM signal to monitor.
        """
        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.INPUT)

        self._highTick = None

        self._callback = self.pi.callback(self.pin, pigpio.EITHER_EDGE, self._edgeDetected)

        return

    def _edgeDetected(self, gpio, level, tick):
        '''
        The meat of the service ...

        If level is high, we are starting a pulse,
        and if low then we end the pulse.
        Period is the time (microseconds) between the
        start of this and the last pulses.
        Pulse width is the time (microseconds) between the
        start of this and the end of this pulse.
        Seeing a pulse, means we have been alive since last
        checked and so we are not dead.
        Sanity check says frequency is between 10 Hz and 1 kHz.
        So period is between 100,000 microseconds and 1,000 microseconds.
        '''
        self.died = False # we are definitely alive!
        if level == 1: # start pulse
            if self._highTick is not None: # not the first
                t = pigpio.tickDiff(self._highTick, tick) # microseconds since last pulse
                # check the signal is reasonable (> 10 Hz and < 1kHz)
                if (t < 100000) and (t > 1000):
                    self.hasStarted = True # we have had a cycle
                    self._period = t
            self._highTick = tick
        elif level == 0: # end pulse
            if self._highTick is not None: # we saw the start
                t = pigpio.tickDiff(self._highTick, tick) # microseconds since start of pulse
                if self._high is None:
                    self._high = t # length of the pulse (high)
                    self._lastHigh = t # so we have one!
                else:
                    self._high = t # length of the pulse (high)
                    if self.whenValueChanged is not None: # do we need to check if we should fire?
                        v = self.value()
                        if self.last != v: # has it changed?
                            # print("Seen change: diff =", math.fabs(self._lastHigh - t), ", sig =", self._significant)
                            if math.fabs(self._lastHigh - t) < self._significant: # has it changed significantly?
                                self._lastHigh = t # where we were when we last triggered
                                self.last = v
                            self.whenValueChanged(v) # let the listener know
        return

    def whenValueChanges(self, callback):
        self.whenValueChanged = callback
        # print("PWMListener: Set the whenValueChanged callback to", callback)
        return

    def check(self):
        '''
        Called to check we are alive.
        Returns current value of died,
        but resets it to the same as hasStarted
        '''
        value = self.died # return value
        self.died = self.hasStarted # reset value
        return value

    def value(self):
        # print("PWMListener: Pulse width =", self.pulse_width(), self._pMax(), self._pMin(), self.quanti, self.usePW, file=sys.stderr)
        pw = self.pulse_width()
        # print("Value: ", pw, self._max, self._min, self.quanti)
        if pw > self._max:
            pw = self._max
        if pw < self._min:
            pw = self._min
        value = quantum(pw, self._max, self._min, self.quanti)
        return value

    def zero(self):
        self._period = self.period()
        self._high = self._mid
        if self.whenValueChanged is not None:
            self.whenValueChanged(self.value())
        return

    def frequency(self):
        """
        Returns the last detected PWM frequency.
        """
        value = 0.0
        if self._period is not None:
            value = 1000000.0 / self._period
        return value

    def pulse_width(self):
        """
        Returns the PWM pulse width in microseconds.
        """
        value = self._mid
        if self._high is not None:
            value = self._high
        return value

    def duty_cycle(self):
        """
        Returns the PWM duty cycle percentage.
        """
        return dutyCycle(self._high, self._period)

    def cancel(self):
        """
        Cancels the listener and releases resources.
        """
        self._callback.cancel()
        self.pi.stop()
        return


class HeartBeatError(Exception):
    """Exception raised for errors in the HeartBeat object.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        super().__init__()
        self.message = message
        return


class HeartBeat(Thread):
    '''
    HeartBeat
    Takes as input
        the number of seconds between checks (default to 1 second or 60 bpm)
        the method to call on each beat (do_check)
        (optional) a callback (whenHealthChanged)
    Runs on it's own thread looping:
        waiting for the required number of seconds
        then calling the do_check method
    The loop will end when the do_check method is None.
    If the do check method returns False then
        call the whenHealthChanged method to react to death - (heart stopped)!
    Do we need a second loop waiting for resurrection?
    Or do we expect the caller to create a new HeartBeat?
    '''

    def __init__(self, do_check, period=1, when_stopped=None):
        '''
        Constructor
        '''
        super().__init__()
        self.do_check = do_check
        self.period = period
        self.whenHealthChanged = when_stopped
        return

    def start(self):
        if self.whenHealthChanged is None:
            raise HeartBeatError("Not set up 'whenHealthChanged' callback.")
        super().start()
        return

    def run(self):
        died = False
        while (not died and self.whenHealthChanged is not None):
            sleep(self.period)
            # print("HeartBeat: Calling do_check")
            died = self.do_check()
            # print("HeartBeat: Returned by do_check:", died)
        if self.whenHealthChanged is not None:
            self.whenHealthChanged()
        return


if __name__ == "__main__":
    print("Nothing to run in RadioController.py")
