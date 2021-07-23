# !/usr/bin/python3
"""
Blue Dot Test PWM.

It was created to simulate the RC controller's PWM signals using BlueDot.
It was hacked from the original Boat Controller logic written to control
a model boat using the BlueDot control mechanism.
Details are listed below.
"""


from TestCode.BdController import BdServer
from TestCode.ControlledBoat import ControlledBoat
from TestCode.DisplayBoat import DisplayBoat
from TestCode.GpioZeroBoat import GPIOZeroBoat

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
    GPIO14, GPIO15, GPIO18*
    GPIO5, GPIO6, GPIO13*
    GPIO20, GPIO26, GPIO19*
    for the H-bridge motors
    and GPIO12* for the servo for the ruder
    So you can make use of the hardware PWM
    and have each motor use 3 pins close to each other
'''


if __name__ == '__main__':
    # for 3-pin motors:
    left = (20, 21, 19)
    right = (7, 1, 12)
    center = (23, 24, 18) # only using the centre PWM for testing RC

    # other pins
    servo = 13 # only other pin being used for testing

    print("Virtual Boat about to start")
    # create and also start the boat:
    # old version: boat = BlueDotBoat(left, right, center, servo)
    boat = GPIOZeroBoat(left, right, center, servo)
    # GPIOZeroBoat is just the boat with no controller ...

    # add a blue dot controller, that knows about double clicking to swap function
    bdController = BdServer()

    displayBoat = DisplayBoat()
    # create a test boat with controller
    test = ControlledBoat(
        boat=boat, listener=displayBoat, controller=bdController)

    tk = displayBoat.tk
    tk.mainloop()
    test.shutdown()
    print("Boat stopped")

