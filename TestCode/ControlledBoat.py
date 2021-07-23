# !/usr/bin/python3
"""
ControlledBoat - remote control boat
This is an implementation of the CommsController to allow
a controller object to be linked to a boat object and optionally
have a listener display the status of the boat.
"""

from TestCode.CommsController import CommsController

NAVIGATION = 0
TARGETTING = 1


class ControlledBoat(CommsController):

    def __init__(self, boat=None, controller=None, listener=None):
        # initialise control boat and add any controller
        '''
        # debug info
        print("ControlledBoat:")
        print("boat=", boat)
        print("controller=", controller)
        print("listener=", listener)
        print("super()=", super())
        print("super().__init__=", super().__init__)
        '''
        super().__init__(boat=boat, server=controller)
        '''
        if controller:
           self.addServer(controller)
        '''

        # add in any listener
        self.boatListeners = []
        if listener:
            self.addBoatListener(listener)
        return

    def addBoatListener(self, listener):
        self.boatListeners.append(listener)
        # and then pass back relevant info ...
        listener.added(self.boat)
        return

    def report(self):
        if self.boat and len(self.boatListeners) > 0:
            values = self.boat.report()
            for listener in self.boatListeners:
                # let each listener get the data
                listener.update(*values)
        return

    #
    # Overridden methods ...
    #

    def navigate(self, connectionId, x, y):
        super().navigate(connectionId, x, y)
        # then report oy back up to the boat listeners
        self.report()
        return


if __name__ == '__main__':
    # for testing
    pass
