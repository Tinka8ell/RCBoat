'''
Created on 28 Jul 2021

@author: Tinka
'''

from threading import Thread
from time import sleep
import sys

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


class RadioControlListener(object):
    '''
    RadioControlListener
    Takes as input:
        a list of Pins
        (optional) callback (whenValueChanged?)
        (optional) weighting
        (optional) quanti
        Might also consider a "smoothing" size
            - number of last readings to average over ...
    Internally creates
        a list PWMListeners
        a HeartBeatMonitor
    Has a view() method to see the current values of the pins
    (List, Tuple or Dict?).
    Can also set and remove the whenValueChanged callback.
    Can be polled using value(), or the callback can be called whenever there is a change detected.
    Quanti sets the number of increments of values.
    Default will be 10 giving 21 quanum values from
    MID and 10 steps out to MAX and MIN values.
    Possibly use the quantum values from - quanti to + quanti
    as the values for value?
    Do we need to be able to select PW or DC (PW / Period)
    as the base for the returned values?
    HeartBeat will poll the PWMListeners to check they are still alive.
    A separate thread will run in a wait loop waiting on a lock.
    The lock will be triggered by any callabacks from the PWMListeners.
    This thread will then call the RadioControlListener callback,
    so as to decouple the interrupts from any work done when values change.
    '''

    def __init__(self, pins,
                 whenValueChanges=None,
                 weighting=0.0,
                 quanti=10,
                 smoothingSize=0,
                 usePW=True):
        '''
        Constructor
        '''
        # print("RadioControlListener: Creating with pins =", pins)
        self.whenValueChanges(whenValueChanges)  # call back
        self.whenHealthChanges(None)  # no call back
        self.quanti = quanti  # set to 0 to not use quantum vaulues
        self.usePW = usePW  # if we decide not to use duty cycle for value()
        # two alternative smoothing ideas:
        self.weighting = weighting
        self.smoothingSize = smoothingSize

        self.listeners = []
        if not isinstance(pins, tuple):
            raise Exception(str(self.__class__) + " requires pins as a tuple of gpio pin numbers")
        for pin in pins:
            if isinstance(pin, tuple):
                self.listeners.append(PWMListener(pin[0],
                                                  whenValueChanges=self.changeSeen,
                                                  quanti=quanti,
                                                  weighting=weighting,
                                                  smoothingSize=smoothingSize,
                                                  usePW=usePW,
                                                  DCRange=pin[1:]))
            else:
                self.listeners.append(PWMListener(pin,
                                                  whenValueChanges=self.changeSeen,
                                                  quanti=quanti,
                                                  weighting=weighting,
                                                  smoothingSize=smoothingSize,
                                                  usePW=usePW))
        self.heartBeat = HeartBeat(self.checkPins, when_stopped=self.hasDied)  # use default 60 bpm?
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
        this call back will check all the pins
        if any pin has died then it will return died as True
        '''
        died = False
        for listener in self.listeners:
            died = died or listener.check()
        return died

    def value(self):
        values = []
        for listener in self.listeners:
            values.append(listener.value())
        return values

    def hasDied(self):
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
        # print("RadioControlListener: Seen a change:",  value)
        if self.whenValueChanged is not None:
            self.whenValueChanged(self.value())
        return


class PWMListener(object):
    '''
    PWMListener
    Takes as input
        a Pin
        (optional) callback (whenValueChanged?)
        (optional) weighting
        (optional) quanti
        (optional) usePW (default to False) to indicate
            if the base values should be from PW instead of DC
        Might also consider a "smoothing" size -
            number of last readings to average over ...
    Has a check() method to see if any PWM have been received
    since last call and so confirm that it is still "alive".
    Has a view() method to see the current value of the pin.
    Can also set and remove the whenValueChanged callback.
    Can be polled using value(), or the callback can be called
    whenever there is a change detected.
    Quanti sets the number of increments of values.
    Default will be 10 giving 21 quanum values from MID
    and 10 steps out to MAX and MIN values.
    Possibly use the quantum values from - quanti to + quanti
    as the values for value?
    Works like the existing reader code, except it is auto ranging:
        First value obtained is considered MID and MAX and MIN are
            set to small differences above and below MID.
        Any values received greater than MAX become MAX and
            ditto for values below MIN.
    Any value setting the period sets the "alive" state to True.
        We expect this to happen 50 times or more a second.
    Calling check() will return the "alive" state,
        and then set it to False.
    Current value is calculated by:
        Quantum = (MAX - MIN) / (quanti * 2)
        Value = int((value - MIN + (Quantum / 2)) / Quantum) - quanti
            (i.e. the expected quantum values)
    The callback (whenValueChanged) will be called any time Value is
    different from last time, or maybe if Value has been different
    for a number of values?
    '''

    def __init__(self, pin,
                 whenValueChanges=None,
                 weighting=0.0,
                 quanti=10,
                 smoothingSize=0,
                 DCRange=None,  # range if provided is tuple of (mid, radius)
                 usePW=True  # seems more consistent than DC
                 ):
        '''
        Constructor
        '''
        # print("PWMListener: Creating with pin =", pin, " and DCRange =", DCRange)
        self.whenValueChanges(whenValueChanges)  # call back
        self.quanti = quanti  # set to 0 to not use quantum values
        self.usePW = usePW  # if we decide not to use duty cycle for value()
        self.pin = pin

        # two alternative smoothing ideas:
        if weighting < 0.0:
            weighting = 0.0
        elif weighting > 0.99:
            weighting = 0.99
        self._new = 1.0 - weighting  # Weighting for new reading.
        self._old = weighting  # Weighting for old reading.

        self.smoothingSize = smoothingSize

        # working variables
        self._period = None  # time between change to high in microseconds
        self._high = None  # time between change to high and change to low in microseconds

        self._max = None
        self._min = None

        self._pmax = None
        self._pmin = None

        self._midDC = None
        self._radiusDC = None
        if DCRange is not None:
            self._midDC = DCRange[0]
            self._radiusDC = DCRange[1]

        self.hasStarted = True
        self.died = self.hasStarted
        self.last = 0 # start with value of 0
        """
        Instantiate with the Pi and gpio of the PWM signal to monitor.
        """
        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.INPUT)

        self._highTick = None
        self.seenHigh = False
        self.seenLow = False

        self._callback = self.pi.callback(pin, pigpio.EITHER_EDGE, self._edgeDetected)

        return

    def whenValueChanges(self, callback):
        self.whenValueChanged = callback
        # print("PWMListener: Set the whenValueChanged callback to", callback)
        return

    def check(self):
        #print("PWMListener: In check() for pin:", self.pin)
        #print("   Pulse width =", self.pulse_width(), self._pMax(), self._pMin(), self.quanti, self.usePW)
        #print("   value =", self.value())
        #print("   seenHigh =", self.seenHigh)
        #print("   seenLow =", self.seenLow)
        #print("   hasStarted =", self.hasStarted)
        value = self.died
        self.died = self.hasStarted
        return value

    def frequency(self):
        """
        Returns the PWM frequency.
        """
        value = 0.0
        if self._period is not None:
            value = 1000000.0 / self._period
        return value

    def period(self):
        return (self._pMax() + self._pMin()) / 2

    def _pMax(self):
        value = self._pmax
        if self._pmax is None:
            value = 0
        return value

    def _pMin(self):
        value = self._pmin
        if self._pmin is None:
            value = 0
        return value

    def _Max(self):
        value = self._max
        if self._max is None:
            value = 0
        return value

    def _Min(self):
        value = self._min
        if self._min is None:
            value = 0
        return value

    def value(self):
        value = 0
        if self.usePW:
            # print("PWMListener: Pulse width =", self.pulse_width(), self._pMax(), self._pMin(), self.quanti, self.usePW, file=sys.stderr)
            value = quantum(self.pulse_width(), self._pMax(), self._pMin(), self.quanti)
        else:
            period = self.period()
            maximum = dutyCycle(self._Max(), period)
            minimum = dutyCycle(self._Min(), period)
            value = quantum(self.duty_cycle(), maximum, minimum, self.quanti)
        return value

    def zero(self):
        self._period = self.period()
        self._high = (self._Max() + self._Min()) / 2
        if self.whenValueChanged is not None:
            self.whenValueChanged(self.value())
        return

    def pulse_width(self):
        """
        Returns the PWM pulse width in microseconds.
        """
        value = 0.0
        if self._high is not None:
            value = self._high
        else:
            print("pulse_width() - _high =", self._high)
        return value

    def duty_cycle(self):
        """
        Returns the PWM duty cycle percentage.
        """
        return dutyCycle(self._high, self._period)

    def _edgeDetected(self, gpio, level, tick):
        self.died = False
        if level == 1:
            self.seenHigh = True
            if self._highTick is not None:
                t = pigpio.tickDiff(self._highTick, tick)
                # check the signal is reasonable (> 10 Hz and < 1kHz)
                # 1 Hz => 1,000,000 microseconds, Hz = 1,000,000/t
                if (t < 100000) and (t > 1000):
                    # check the signal is reasonable (> 10 Hz and < 1kHz)
                    self.hasStarted = False # we have had a cycle
                    if self._period is not None:
                        self._period = (self._old * self._period) + (self._new * t)
                    else:
                        self._period = t
                    if (self._midDC is not None) and (self._radiusDC is not None):
                        self._pmax = (self._midDC + self._radiusDC) * t
                        self._pmin = (self._midDC - self._radiusDC) * t
                '''
                else:
                    print("t =", t)
                '''
            self._highTick = tick
        elif level == 0:
            self.seenLow = True
            if self._highTick is not None:
                t = pigpio.tickDiff(self._highTick, tick)
                if self._high is not None:
                    self._high = (self._old * self._high) + (self._new * t)
                else:
                    self._high = t
                if self.whenValueChanged is not None:
                    v = self.value()
                    if self.last != v:
                        self.last = v
                        self.whenValueChanged(self.last)
        return

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
        self.message = message


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
