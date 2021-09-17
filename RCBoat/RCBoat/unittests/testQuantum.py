'''
Created on 28 Jul 2021

@author: Tinka
'''
import unittest
from RCBoat.RadioControlListener import quantum


class TestQuantum(unittest.TestCase):
    '''
    quantum(value, maximum, minimum, quanti)
    '''

    def testZeroHandling(self):
        self.assertEqual(7.5, quantum(7.5, 10, 0, 0))
        self.assertEqual(7.5, quantum(7.5, 10.0, 0.0, None))
        self.assertEqual(0, quantum(7.5, 0, 0, 10))
        self.assertEqual(0, quantum(7.5, 10.0, 10.0, 10))
        self.assertEqual(0, quantum(7.5, 10.0, None, 10))
        self.assertEqual(0, quantum(7.5, None, 0.0, 10))
        return

    def testValid(self):
        self.assertEqual(0, quantum(7.0, 10.0, 4.0, 10))
        self.assertEqual(10, quantum(10.0, 10.0, 4.0, 10))
        self.assertEqual(-10, quantum(4.0, 10.0, 4.0, 10))
        self.assertEqual(7, quantum(7.4, 10, -10, 10))
        self.assertEqual(7, quantum(6.6, 10, -10, 10))
        # self.assertEqual(7, quantum(7.5, 10, -10, 10)) # actually rounds up
        self.assertEqual(7, quantum(6.5, 10, -10, 10))
        self.assertEqual(7, quantum(6.6, 10, -10, 10.0))
        self.assertEqual(9, quantum(7376.0, 7638.75, 2546.25, 10))
        self.assertEqual(4, quantum(6110.0, 7632.0, 2544.0, 10))
        self.assertEqual(-5, quantum(3875.0, 7781.25, 2593.75, 10))
        return


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
