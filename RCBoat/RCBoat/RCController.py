# !/usr/bin/python3
# BdController - BlueDot controller
"""
An implementation of CommsController using the BlueDot interface.
"""

import sys

from RCBoat.CommsController import CommsServer, CommsListener, CommsReceiver, MessageReceiver
from RCBoat.RadioControlListener import RadioControlListener
from threading import Thread, Lock


# no class RCController()
class RCServer(CommsServer):
    '''
    This would be a server for links, but we only have one!

    It will listen on a receiver and wait for connections.
    All new connections are used to create Listeners
    which are passed to controller (connected()) for acceptance or rejection.
    And new receiver created to wait for another connection.
    Server accepts listeners by calling startup() passing the connection id.
    Server can then close a connection, calling shutdown() on it.
    Children should override:
       makeReceiver(self)- returns a CommsReceiver using self.setup
          CommsReciever waits for connections on accept()
          returning the connection data
       makeListener(connection)- returns a CommsListener using connection and self.controller
    '''

    '''
    These methods must be overwritten
    '''

    def makeReceiver(self):
        # receiver object is what?
        return RCReceiver()

    def makeListener(self, connection):
        # make a RCListener object from connection info - which is what?
        # We can only have one!
        listener = None
        if connection:
            try:
                listener = RCCommsListener(
                    connection, controller=self.controller)  # need controller?
            except Exception as e:
                print(e)
                print(sys.exc_info())
            self.receiver = None
        return listener


class RCReceiver(CommsReceiver):

    def setup(self, setup):
        self.rcListener = setup
        return

    def accept(self):
        #some sort of wait?
        return self.rcListener

    def close(self):
        self.rcListener.stop()
        return


class RCCommsListener(CommsListener):
    '''
    Listener is a threaded device to listen for messages.

    Listener is started with a receiver
    (BlueDot object that has been connected)
    and a defined server object.
    '''

    def makeReceiver(self, connection):
        # turn a connection (a BlueDot) into the receiver
        return RCMessageReceiver(setup=connection)

    def startup(self, connectionId, controller):
        self.lock = Lock()
        # Get the lock so run will wait on it
        self.lock.acuire()
        self.receiver.rcListener.whenValueChanges(self.valueChanged)
        super().startup(connectionId, controller)
        return

    def run(self):
        # Get the lock again, will wait until released elsewhere!
        self.lock.acuire()
        if self.controller:
            self.controller.disconnected(self.connectionId)
        return

    def stop(self):
        # Release the lock so we can end.  Who calls this?
        self.lock.release()
        return

    def valueChanged(self, values):
        x, y = values
        self.controller.move(self.connectionId, x, y)
        return


class RCMessageReceiver(MessageReceiver):

    def setup(self, setup):
        self.rcListener = setup
        return

    def getMessage(self):
        return None

    def close(self):
        self.rcListener.stop()
        return


# no class RCConnection()


if __name__ == '__main__':
    # for testing
    print("server1:")
    server1 = CommsServer(None)
    print("controller:")
    controller = CommsController(server=server1)
    print("server2:")
    server2 = CommsServer(None)
    controller.addServer(server2)
