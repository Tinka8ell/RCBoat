'''
Created on 28 Jul 2021

@author: Tinka
'''
import unittest
from RCBoat.RadioControlListener import dutyCycle


class TestDutyCycle(unittest.TestCase):


    def testZeroHandling(self):
        self.assertEqual(0, dutyCycle(None, None))
        self.assertEqual(0, dutyCycle(123, None))
        self.assertEqual(0, dutyCycle(None, 234))
        self.assertEqual(0, dutyCycle(123, 0))
        return

    def testValid(self):
        self.assertEqual(12300/234, dutyCycle(123, 234))
        self.assertEqual(50, dutyCycle(117, 234))
        self.assertEqual(100, dutyCycle(234, 234))
        self.assertEqual(0, dutyCycle(0, 234))
        return

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()