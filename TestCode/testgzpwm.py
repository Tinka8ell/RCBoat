#!/usr/bin/env python

# Read PWM values using GPIOZero

import time

from gpiozero import Device, DigitalInputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

from TestCode.testpwm import reader

Device.pin_factory = PiGPIOFactory()  # use PiGPIO under the covers!


def microseconds():
    """
    Get the time in microseconds
    """
    return time.time() * 1000000.0


class testgzpwm(reader):
    """
    A class to read PWM pulses and calculate their frequency
    and duty cycle.  The frequency is how often the pulse
    happens per second.  The duty cycle is the percentage of
    pulse high time per cycle.
    """

    def __init__(self, gpio, weighting=0.0):
        """
        Optionally a weighting may be specified.  This is a number
        between 0 and 1 and indicates how much the old reading
        affects the new reading.  It defaults to 0 which means
        the old reading has no effect.  This may be used to
        smooth the data.
        """
        super().__init__(gpio, weighting=weighting)
        """
        Instantiate with the Pi and gpio of the PWM signal
        to monitor.
        """
        self.pin = DigitalInputDevice(pin=gpio)

        self._high_time = None

        self.pin.when_activated = self._up
        self.pin.when_deactivated = self._down
        return

    def _up(self):
        if self._high_time is not None:
            t = microseconds() - self._high_time
            if self._period is not None:
                self._period = (self._old * self._period) + (self._new * t)
            else:
                self._period = t
        self._high_time = microseconds()
        return

    def _down(self):
        if self._high_time is not None:
            t = microseconds() - self._high_time
            if self._high is not None:
                self._high = (self._old * self._high) + (self._new * t)
            else:
                self._high = t
        return

    def cancel(self):
        """
        Cancels the reader and releases resources.
        """
        super().cancel()
        self.pin.when_activated = None
        self.pin.when_deactivated = None
        self.pin.close()
        return

