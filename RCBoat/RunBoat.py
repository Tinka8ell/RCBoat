'''
Created on 23 Jul 2021

@author: Tinka
'''

from RCBoat.TestBoat import testBoat
from RCBoat.PWMGenerator import PWMGenerator

if __name__ == '__main__':
    '''
    The raspberry pi pins (taken from outout from pinout with added *'s) are:
    J8:
        3V3  (1) (2)  5V
    **GPIO2  (3) (4)  5V
    **GPIO3  (5) (6)  GND
      GPIO4  (7) (8)  GPIO14
        GND  (9) (10) GPIO15
     GPIO17 (11) (12) GPIO18*
     GPIO27 (13) (14) GND
     GPIO22 (15) (16) GPIO23
        3V3 (17) (18) GPIO24
     GPIO10 (19) (20) GND
      GPIO9 (21) (22) GPIO25
     GPIO11 (23) (24) GPIO8
        GND (25) (26) GPIO7
      GPIO0 (27) (28) GPIO1
      GPIO5 (29) (30) GND
      GPIO6 (31) (32) GPIO12*
    *GPIO13 (33) (34) GND
    *GPIO19 (35) (36) GPIO16
     GPIO26 (37) (38) GPIO20
        GND (39) (40) GPIO21

    As
    ** I2C (for turrets) uses:
    Data:  (GPIO2)
    Clock: (GPIO3)
    and
    * hardware PWM is on pins:
    GPIO12, GPIO13, GPIO18, GPIO19

    Suggest use:
    GPIO14, GPIO15, GPIO18* - use GPIO26
    GPIO5, GPIO6, GPIO13* - use GPIO23
    GPIO20, GPIO26, GPIO19*
    for the H-bridge motors
    and GPIO12* for the servo for the ruder
    So you can make use of the hardware PWM
    and have each motor use 3 pins close to each other

    for testing will use GPIO13 & GPIO18 for the PWMGenerator
    so will need different pins for the motors, but as we are using
    virtual Pins not a problem.
    '''

    # hardware PWM: GPIO12, GPIO13, GPIO18, GPIO19

    PWMA = 18
    PWMB = 13
    PMWC = 12
    PMWD = 19
    TestHarness = False
    if TestHarness:

        print("Running test with pins 13 & 18 connected to pins 4 & 5")
        # showThreads()
        print("Starting test signal on pins 13 & 18")
        # Using default pin factory fir the generator ...
        pmwGenerator = PWMGenerator(PWMB, PWMA) # if using cycle

        # comment out this line to use real pins
        # Device.pin_factory = MockFactory(pin_class=MockPWMPin)

        PWMA = 26
        PWMB = 16

    # for 3-pin motors:
    left = (20, 21, PMWD)
    right = (7, 1, PMWC)
    center = (23, 24, PWMA)

    # other pins
    servo = PWMB

    print("About to start")

    # this starts the boat
    print("Using RadioControlListener listening on 4 & 5")
    rcpins = (
        (4, 1569, 550), # set mid as 1/2 and range as 1/4 away from that
        (5, 1507, 412)  # set mid as 1/2 and range as 1/4 away from that
        )
    # testBoat(left, right, center, servo, rcpins, reactive=True, TestHarness=True) # for testing with reactive ...
    testBoat(left, right, center, servo, rcpins, reactive=False, TestHarness=True) # for testing without reactive ...
