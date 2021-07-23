#!/usr/bin/env python

# Read PWM values using PiGPIO

from TestCode.testpwm import reader
import pigpio


class testpgpwm(reader):
    """
    A class to read PWM pulses and calculate their frequency
    and duty cycle.  The frequency is how often the pulse
    happens per second.  The duty cycle is the percentage of
    pulse high time per cycle.
    """

    def __init__(self, gpio, weighting=0.0, pi=None):
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
        if pi is None:
            pi = pigpio.pi()
        self.pi = pi

        self._high_tick = None

        pi.set_mode(gpio, pigpio.INPUT)
        self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)
        return

    def _cbf(self, gpio, level, tick):
        if level == 1:
            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)
                if self._period is not None:
                    self._period = (self._old * self._period) + (self._new * t)
                else:
                    self._period = t
            self._high_tick = tick
        elif level == 0:
            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)
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
        self._cb.cancel()
        self.pi.stop()
        return

