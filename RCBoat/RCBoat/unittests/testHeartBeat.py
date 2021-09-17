'''
Created on 28 Jul 2021

@author: Tinka
'''
import unittest
import time
from RCBoat.RadioControlListener import HeartBeat, HeartBeatError

def failFirst():
    fail = True
    # print("failFirst:", fail)
    return fail

FAIL = False

def failSecond():
    global FAIL # starts as False
    fail = FAIL
    FAIL = True # so we fail on second call
    # print("failSecond:", fail)
    return fail

def died():
    # print("Died")
    return

class TestHeartBeat(unittest.TestCase):


    def testHeartBeatException(self):
        heartBeat = HeartBeat(failFirst, period=0.1)
        with self.assertRaises(HeartBeatError, msg="Not set up properly"):
            heartBeat.start()
        pass

    def testHeartBeatOnce(self):
        heartBeat = HeartBeat(failFirst, period=0.1, when_stopped=died)
        start = time.time()
        heartBeat.start() # should take period to end
        heartBeat.join(0.3)
        wait = time.time() - start
        self.assertLess(wait, 0.15, msg="Took too long")
        self.assertGreater(wait, 0.05, msg="Was too quick")
        pass

    def testHeartBeatTwice(self):
        heartBeat = HeartBeat(failSecond, period=0.1)
        heartBeat.whenHealthChanged = died
        start = time.time()
        heartBeat.start() # should take period to end
        heartBeat.join(0.3)
        wait = time.time() - start
        self.assertLess(wait, 0.25, msg="Took too long")
        self.assertGreater(wait, 0.15, msg="Was too quick")
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()