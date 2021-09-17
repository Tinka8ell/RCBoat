'''
Created on 23 Jul 2021

@author: Tinka
'''

from RCBoat.RadioControlListener import RadioControlListener
from RCBoat.PWMGenerator import PWMGenerator
from RCBoat.BlueDotPWMGenerator import BlueDotPWMGenerator
from threading import Lock, enumerate
import time
from time import sleep

def showThreads():
    threads = enumerate()
    count = len(threads)
    print("Currently", count, "threads.")
    for thread in threads:
        print("Thread:", thread.name, "is alive:", thread.is_alive())
    return

if __name__ == "__main__":
    '''
    From data received:
    Motor:
    1095
    1400 - 1510
    1920
    average = 1507.5
    width = 412.5

    Rudder:
    1010
    1560
    2020
    average = 1515
    width = 505
    but mid rudder is 1560 so
    width = 550 or 460!
    '''

    print("Running test with pins 13 & 18 connected to pins 4 & 5")
    # showThreads()
    print("Starting test signal on pins 13 & 18")
    pmwGenerator = PWMGenerator(13, 18) # if using cycle
    # wGenerator = BlueDotPWMGenerator(13, 18) # if using BlueDot

    print("Just loading RadioControlListener listening on 4 & 5")
    rcListen = RadioControlListener(
        (
            (4, 1569, 550), # set mid as 1/2 and range as 1/4 away from that
            (5, 1507, 412)  # set mid as 1/2 and range as 1/4 away from that
            ),
            smoothing=1,
            name="Main"
        )
    print("Just loading RadioControlListener 100 listening on 21 & 22")
    rcListen100 = RadioControlListener(
        (
            (21, 1569, 550), # set mid as 1/2 and range as 1/4 away from that
            (22, 1507, 412)  # set mid as 1/2 and range as 1/4 away from that
            ),
            smoothing=0,
            quanti=10,
            name="Secondary"
        )
    # showThreads()

    _lock = Lock()
    _lock.acquire()
    messages = []
    start = time.time()
    last = [0] * 4

    def onHealthChange(health):
        print("Seen health change:", health)
        return

    def onHealthChange100(health):
        print("Seen health change (100):", health)
        return

    def onChange(value):
        message = str(int((time.time() - start) * 1000))
        for i in range(len(value)):
            last[i] = value[i]
        for item in last:
            message += ", " + str(item)
        messages.append(message)
        # print(message)
        return

    def onChange100(value):
        message = str(int((time.time() - start) * 1000))
        for i in range(len(value)):
            last[i + len(value)] = value[i]
        for item in last:
            message += ", " + str(item)
        messages.append(message)
        return

    rcListen.whenValueChanges(onChange)
    rcListen.whenHealthChanges(onHealthChange)
    rcListen100.whenValueChanges(onChange100)
    rcListen100.whenHealthChanges(onHealthChange100)
    print("All set up")
    sleep(1)

    print("Start main")
    rcListen.start()
    # showThreads()
    # sleep(1)

    print("Start secondary")
    rcListen100.start()
    # showThreads()

    # _lock.acquire() # wait for death

    # Wait for keyboard input
    # input("Press return to stop")

    # wait 1/2 minute
    print("Waiting 1/2 a minute")
    sleep(30)

    print("Run complete")

    with open("testData.txt", "w") as f:
        for message in messages:
            print(message, file=f)
            print(message)

    # showThreads()
    print("Stopping RadioControlListeners")
    rcListen.stop()
    rcListen100.stop()
    print("All stopped!")

    showThreads()

    print("Stopping generator")
    pmwGenerator.cancel()
    print("Waiting generator")
    pmwGenerator.join()
    print("Shut down")

    showThreads()
