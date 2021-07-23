#!/usr/bin/env python

# Read PWM values using PiGPIO

import time


class reader:
    """
    A class to read PWM pulses and calculate their frequency
    and duty cycle.  The frequency is how often the pulse
    happens per second.  The duty cycle is the percentage of
    pulse high time per cycle.
    """

    def __init__(self, gpio, weighting=0.0):
        """
        Common set up.

        Optionally a weighting may be specified.  This is a number
        between 0 and 1 and indicates how much the old reading
        affects the new reading.  It defaults to 0 which means
        the old reading has no effect.  This may be used to
        smooth the data.
        """
        self.gpio = gpio
        if weighting < 0.0:
            weighting = 0.0
        elif weighting > 0.99:
            weighting = 0.99
        self._new = 1.0 - weighting  # Weighting for new reading.
        self._old = weighting  # Weighting for old reading.

        self._period = None  # time between change to high in microseconds
        self._high = None  # time between change to high and change to low in microseconds

        return

    def frequency(self):
        """
        Returns the PWM frequency.
        """
        value = 0.0
        if self._period is not None:
            value = 1000000.0 / self._period
        return value

    def pulse_width(self):
        """
        Returns the PWM pulse width in microseconds.
        """
        value = 0.0
        if self._high is not None:
            value = self._high
        return value

    def duty_cycle(self):
        """
        Returns the PWM duty cycle percentage.
        """
        value = 0.0
        if self._high is not None:
            value = 100.0 * self._high / self._period
        return value

    def cancel(self):
        """
        Cancels the reader and releases resources.
        """
        return


RUN_TIME = 60.0
SAMPLE_TIME = 0.5


def testpwm(name, reader):

    rudder_GPIO = 4  # connected to 13 (driven by test harness)
    motor_GPIO = 5  # connected to 18 (driven by test harness)

    rp = reader(rudder_GPIO)
    mp = reader(motor_GPIO)

    recordings = []
    input(f"Waiting to start test: {name} - press enter")  # don't care what is typed before enter
    start = time.time()
    now = start
    print(f"RUN_TIME = {RUN_TIME}, SAMPLE_TIME = {SAMPLE_TIME}")
    print(f"Starting test {name}: time = {now}")
    while (now - start) < RUN_TIME:
        time.sleep(SAMPLE_TIME)
        now = time.time()
        rf = rp.frequency()
        mf = mp.frequency()
        rpw = int(rp.pulse_width() + 0.5)  # round to nearest int
        mpw = int(mp.pulse_width() + 0.5)  # round to nearest int
        rdc = rp.duty_cycle()
        mdc = mp.duty_cycle()
        recordings.append((now, rf, rpw, rdc, mf, mpw, mdc))

    rp.cancel()
    mp.cancel()
    print(f"Finished test {name}: time = {now}. took {now-start}")

    with open(name + '.txt', 'w') as fd:
        # print("time, rf, rpw, rdc, mf, mpw, mdc")
        print("time, rf, rpw, rdc, mf, mpw, mdc", file=fd)
        for now, rf, rpw, rdc, mf, mpw, mdc in recordings:
            # print(f"{now}, {rf}, {rpw}, {rdc}, {mf}, {mpw}, {mdc}")
            print(f"{now}, {rf}, {rpw}, {rdc}, {mf}, {mpw}, {mdc}", file=fd)

    print(f"{name}: All done")


if __name__ == "__main__":

    print("First test - PiGPIO")

    from TestCode.testpgpwm import testpgpwm as pigpioreader
    testpwm("pigpio-test", pigpioreader)

    print("Second test - GPIOZero")

    from TestCode.testgzpwm import testgzpwm as gpiozeroreader
    testpwm("gpiozero-test", gpiozeroreader)

    print("All tests complete")
