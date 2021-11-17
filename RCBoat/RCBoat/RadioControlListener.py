'''
Created on 28 Jul 2021

@author: Tinka
'''

from threading import Thread
from time import sleep

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
        # value = min(maximum, value)
        # value = max(minimum, value)
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
        (optional) poll rate (default 10 Hz)
    Internally creates
        a list PWMListeners
    Has a view() method to see the current values of the pins as a list
    with an optional quanti parameter.
    Can also set and remove the whenValueChanged callback.
    Can be polled using value(),
    or have the callback invoked whenever there is a change detected.
    Quanti sets the number of increments of values (0 to +/- quanti).
    Default will be 10 giving 21 quantum values from
    MID and 10 steps out to MAX and MIN values.
    Will use the Pulse Width for the basis of the values.
    It will poll the PWMListeners to get their current values and
    check they are still alive.
    '''

    def __init__(self, pins,
                 quanti=10,
                 whenValueChanges=None,
                 whenHealthChanges=None,
                 pollRate=10,
                 name="RCListener",
                 smoothing=None):
        '''
        Constructor
        '''
        # print("RadioControlListener: Creating with pins =", pins)
        self.whenValueChanges(whenValueChanges)  # call back
        self.whenHealthChanges(whenHealthChanges)  # call back
        self.quanti = quanti  # set to 0 to not use quantum values
        self.name = name
        self.smoothing = smoothing;
        if smoothing is None: # default to 1/10 of quanti
            self.smoothing = quanti / 10;

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
            # listeners is a list of tuples: listener object, maximum and minimum sizes
            lName = name + " - " + str(gpio)
            self.listeners.append((PWMListener(gpio, lName), pwMid + pwRange, pwMid - pwRange))
        self.lastValue = self.value()
        self.health = self.checkPins()

        # Listeners are all set up, now can set up things that may call them
        self.period = 1 / pollRate # gap between polls in seconds
        # print("Creating thread")
        self.heartBeat = Thread(target=self.run, name=self.name)
        # print("Setup complete")
        for listener, maximum, minimum in self.listeners:
            prefix = "listener(None):"
            if listener is not None:
                prefix = "listener(" + listener.name + "):"
            print(prefix, "max =", maximum, ", min=", minimum)
        return

    def start(self):
        # print("Starting thread")
        self.ok = True
        self.heartBeat.start()
        return

    def run(self):
        '''
        Place code to run periodically here.
        Return values via the whenValueChanged callback.
        Return health changes through the whenHealthChanged callback.
        Loop until self.ok is false ...
        '''
        while self.ok:
            sleep(self.period)
            print("RadioControlListener not yet implemented!")
            self.ok = False # end early!
        print(self.name, "heart beat stopped")
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
        Called to check all the pins:
        '''
        health = []
        for listener in self.listeners:
            health.append(listener[0].check())
        return health

    def value(self):
        '''
        List of current values of the listeners
        '''
        values = []
        for listener, maximum, minimum in self.listeners:
            value = listener.value()
            if value > 0: # a real value
                values.append(quantum(value, maximum, minimum, self.quanti))
            else: # make it the middle
                values.append(0)
        return values

    def debugValue(self):
        '''
        List of current values of the listeners
        '''
        for listener, maximum, minimum in self.listeners:
            name = listener.name
            value = listener.value()
            mx, mn = listener.debugValue()
            print(name, "Value =", value, ", q=", quantum(value, maximum, minimum, self.quanti),
                  "max =", maximum, " / ", mx, "min =", minimum, " / ", mn)
        return

    def stop(self):
        '''
        Called to shut down everything.
        '''
        print("Stopping", self.name)
        self.ok = False # trigger stop of thread
        if self.heartBeat.is_alive():
            try:
                self.heartBeat.join(self.period * 2) # wait till stopped (no longer than period)
            except Exception as e:
                print("Exception waiting for thread to end:")
                print(e)
        for listener in self.listeners:
            listener[0].stop()
        self.whenHealthChanges(None)
        if self.whenValueChanged is not None:
            self.whenValueChanged([0] * len(self.listeners))
        if self.whenHealthChanged is not None:
            self.whenHealthChanged([False] * len(self.listeners))
        print(self.name, "Stopped")
        if self.heartBeat.is_alive():
            print(self.name, "heart beat is still alive!")
        return


class PWMListener(object):
    '''
    PWMListener
    Takes as input
        a gpio pin number
    Has a check() method to see if any PWM have been received
    since last call and so confirm that it is still "alive".
    Has a view() method to see the current value of the pin.
    Is be polled using value().
    Will use the Pulse Width for the basis of the values.
    Any value setting the period sets the "alive" state to True.
        We expect this to happen 50 times or more a second.
    Calling check() will return the "isDead" state,
        and then set it to False.
        Won't happen until we start first period.
    Current value is Pulse Width
    '''

    def __init__(self, gpio, name="No Name"):
        '''
        Constructor
        '''
        # print("PWMListener: Creating with pin =", pin)
        self.pin = gpio
        self.name = name

        # working variables
        self._period = None  # time between change to high in microseconds
        self._high = None  # time between change to high and change to low in microseconds

        self.died = False # can't die before started

        """
        Instantiate with the Pi and gpio of the PWM signal to monitor.
        """
        self._highTick = None
        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.INPUT)
        self._callback = self.pi.callback(self.pin, pigpio.EITHER_EDGE, self._edgeDetected)
        self._debugMax = None
        self._debugMin = None
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
        t = self.getSafeTime(tick)
        if level == 1: # start pulse
            self.died = (t is None) # whether we are alive or not
            self._period = t # length of cycle or None
            self._highTick = tick
        elif level == 0: # end pulse
            self._high = t # length of the pulse (high) or None
        return

    def getSafeTime(self, tick):
        t = None # not safe!
        if self._highTick is not None: # not the first
            t = pigpio.tickDiff(self._highTick, tick) # microseconds since last pulse
            # check the signal is reasonable (> 10 Hz and < 1kHz)
            if (t > 100000) or (t < 1000):
                t = None # not safe!
        return t

    def check(self):
        '''
        Called to check we are alive.
        Returns current value of died.
        '''
        value = self.died # return value
        self.died = False # reset value
        return not value

    def value(self):
        return self.pulse_width()

    def debugValue(self):
        return self._debugMax, self._debugMin

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
        value = 0
        if self._high is not None:
            value = self._high
        if value > 0:
            if self._debugMax is None:
                self._debugMax = value
            if self._debugMax < value:
                self._debugMax = value
            if self._debugMin is None:
                self._debugMin = value
            if self._debugMin > value:
                self._debugMin = value
        return value

    def duty_cycle(self):
        """
        Returns the PWM duty cycle percentage.
        """
        value = 0.0
        if self.high is not None and self.period is not None and self.period != 0:
            value = 100.0 * self.high / self.period
        return value

    def stop(self):
        """
        Cancels the listener and releases resources.
        """
        print("Stopping listener", self.name)
        self._callback.cancel()
        self.pi.stop()
        return


if __name__ == "__main__":
    print("Nothing to run in RadioController.py")
