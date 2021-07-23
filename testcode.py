'''
Created on 23 Jul 2021

@author: Tinka
'''

from TestCode.testpwm import testpwm

if __name__ == "__main__":

    print("First test - PiGPIO")

    from TestCode.testpgpwm import testpgpwm as pigpioreader
    testpwm("pigpio-test", pigpioreader)

    print("Second test - GPIOZero")

    from TestCode.testgzpwm import testgzpwm as gpiozeroreader
    testpwm("gpiozero-test", gpiozeroreader)

    print("All tests complete")
