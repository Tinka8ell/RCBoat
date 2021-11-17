from gpiozero import SourceMixin, CompositeDevice, Motor, Servo, GPIOPinMissing

class Boat(SourceMixin, CompositeDevice):
    """
    Extends :class:`CompositeDevice` to represent a generic tri-motor and rudder (servo) boat.

    This class is constructed with three tuples representing the forward and
    backward pins of the left, right and center controllers respectively.

    :param tuple left:
        A tuple of two (or three) GPIO pins representing the forward and
        backward inputs of the left motor's controller. Use three pins if your
        motor controller requires an enable pin.

    :param tuple right:
        A tuple of two (or three) GPIO pins representing the forward and
        backward inputs of the right motor's controller. Use three pins if your
        motor controller requires an enable pin.

    :param tuple center:
        A tuple of two (or three) GPIO pins representing the forward and
        backward inputs of the center motor's controller. Use three pins if your
        motor controller requires an enable pin.

    :param servo rudder:
        A GPIO pin representing the input of the servo controlling the rudder.

    :param bool pwm:
        If :data:`True` (the default), construct :class:`PWMOutputDevice`
        instances for the motor controller pins, allowing both direction and
        variable speed control. If :data:`False`, construct
        :class:`DigitalOutputDevice` instances, allowing only direction
        control.

    :type pin_factory: Factory or None
    :param pin_factory:
        See :doc:`api_pins` for more information (this is an advanced feature
        which most users can ignore).

    .. attribute:: left_motor

        The :class:`Motor` on the left of the boat.

    .. attribute:: right_motor

        The :class:`Motor` on the right of the boat.

    .. attribute:: center_motor

        The :class:`Motor` in the center of the boat.

    .. attribute:: rudder

        The :class:`Servo` for the rudder of the boat.
    """
    def __init__(self, left=None, right=None, center=None, rudder=None, pwm=True, pin_factory=None, *args):
        # *args is a hack to ensure a useful message is shown when pins are
        # supplied as sequential positional arguments e.g. 2, 3, 4, 5
        if not isinstance(left, tuple) or not isinstance(right, tuple) or not isinstance(center, tuple) or not rudder:
            raise GPIOPinMissing('left, right and center motor pins and rudder servo pin must be given as '
                              'tuples')
        if (args is not None):
            print("Ignoring *args:", *args)
        super(Boat, self).__init__(
            left_motor=Motor(*left, pwm=pwm, pin_factory=pin_factory),
            right_motor=Motor(*right, pwm=pwm, pin_factory=pin_factory),
            center_motor=Motor(*center, pwm=pwm, pin_factory=pin_factory),
            rudder=Servo(rudder, pin_factory=pin_factory),
            _order=('left_motor', 'right_motor', 'center_motor', 'rudder'),
            pin_factory=pin_factory
        )
        # initialise the motors and servo
        self.left_motor.stop()
        self.right_motor.stop()
        self.center_motor.stop()
        self.rudder.mid()
        self._debug = False

    @property
    def value(self):
        """
        Represents the motion of the boat as a tuple of (left_motor_speed,
        right_motor_speed, center_motor_speed, rudder_angle) with ``(0, 0, 0, 0)``
        representing stopped.
        """
        return super(Boat, self).value

    # what if there is bias? - multiplier for left/right/center so none > 1
    # this should be done on the gpioZeroBoat side of things ...
    @value.setter
    def value(self, value):
        self.left_motor.value, self.right_motor.value, self.center_motor.value, self.rudder.value = value
        self.debug("set value:", self.value)

    def forward(self, speed=1, **kwargs):
        """
        Drive the boat forward by running all motors forward.

        :param float speed:
            Speed at which to drive the motors, as a value between 0 (stopped)
            and 1 (full speed). The default is 1.

        :param float curve_left:
            The amount to curve left while moving forwards, by driving the
            left motor at a slower speed. Maximum *curve_left* is 1, the
            default is 0 (no curve). This parameter can only be specified as a
            keyword parameter, and is mutually exclusive with *curve_right*.

        :param float curve_right:
            The amount to curve right while moving forwards, by driving the
            right motor at a slower speed. Maximum *curve_right* is 1, the
            default is 0 (no curve). This parameter can only be specified as a
            keyword parameter, and is mutually exclusive with *curve_left*.
        """
        curve_left = kwargs.pop('curve_left', 0)
        curve_right = kwargs.pop('curve_right', 0)
        if kwargs:
            raise TypeError('unexpected argument %s' % kwargs.popitem()[0])
        if not 0 <= curve_left <= 1:
            raise ValueError('curve_left must be between 0 and 1')
        if not 0 <= curve_right <= 1:
            raise ValueError('curve_right must be between 0 and 1')
        if curve_left != 0 and curve_right != 0:
            raise ValueError("curve_left and curve_right can't be used at "
                           "the same time")
        self.left_motor.forward(speed * (1 - curve_left))
        self.right_motor.forward(speed * (1 - curve_right))
        self.center_motor.forward(speed)
        self.rudder.value = curve_right - curve_left
        self.debug("forward:", self.value)

    def backward(self, speed=1, **kwargs):
        """
        Drive the boat backward by running both motors backward.

        :param float speed:
            Speed at which to drive the motors, as a value between 0 (stopped)
            and 1 (full speed). The default is 1.

        :param float curve_left:
            The amount to curve left while moving backwards, by driving the
            left motor at a slower speed. Maximum *curve_left* is 1, the
            default is 0 (no curve). This parameter can only be specified as a
            keyword parameter, and is mutually exclusive with *curve_right*.

        :param float curve_right:
            The amount to curve right while moving backwards, by driving the
            right motor at a slower speed. Maximum *curve_right* is 1, the
            default is 0 (no curve). This parameter can only be specified as a
            keyword parameter, and is mutually exclusive with *curve_left*.
        """
        curve_left = kwargs.pop('curve_left', 0)
        curve_right = kwargs.pop('curve_right', 0)
        if kwargs:
            raise TypeError('unexpected argument %s' % kwargs.popitem()[0])
        if not 0 <= curve_left <= 1:
            raise ValueError('curve_left must be between 0 and 1')
        if not 0 <= curve_right <= 1:
            raise ValueError('curve_right must be between 0 and 1')
        if curve_left != 0 and curve_right != 0:
            raise ValueError("curve_left and curve_right can't be used at "
                           "the same time")
        self.left_motor.backward(speed * (1 - curve_left))
        self.right_motor.backward(speed * (1 - curve_right))
        self.center_motor.backward(speed)
        self.rudder.value = curve_right - curve_left
        self.debug("backward:", self.value)

    def left(self, speed=1):
        """
        Make the boat turn left by running the right motor forward and left
        motor backward.

        :param float speed:
            Speed at which to drive the motors, as a value between 0 (stopped)
            and 1 (full speed). The default is 1.
        """
        self.right_motor.forward(speed)
        self.left_motor.backward(speed)
        self.center_motor.stop()
        self.rudder.min()
        self.debug("left:", self.value)

    def right(self, speed=1):
        """
        Make the boat turn right by running the left motor forward and right
        motor backward.

        :param float speed:
            Speed at which to drive the motors, as a value between 0 (stopped)
            and 1 (full speed). The default is 1.
        """
        self.left_motor.forward(speed)
        self.right_motor.backward(speed)
        self.center_motor.stop()
        self.rudder.max()
        self.debug("right:", self.value)

    def reverse(self):
        """
        Reverse the boat's current motor directions. If the robot is currently
        running full speed forward, it will run full speed backward. If the
        robot is turning left at half-speed, it will turn right at half-speed.
        If the robot is currently stopped it will remain stopped.
        """
        self.left_motor.reverse()
        self.right_motor.reverse()
        self.center_motor.reverse()
        # don't change rudder
        self.debug("reverse:", self.value)

    def stop(self):
        """
        Stop the boat.
        """
        self.left_motor.stop()
        self.right_motor.stop()
        self.center_motor.stop()
        self.rudder.mid()
        self.debug("stop:", self.value)

    def debugOn(self):
        self._debug = True

    def debugOff(self):
        self._debug = False

    def debug(self, *args):
        if self._debug:
            print(*args)


if __name__ == '__main__':
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory # makes mock available
    from gpiozero.pins.mock import MockPWMPin # to allow PWM
    from time import sleep

    Device.pin_factory = MockFactory(pin_class=MockPWMPin)

    left = (4, 14)
    right = (17, 18)
    center = (21, 22)
    servo = 24
    viewer = Device.pin_factory.pin(left[0])
    test = Boat(left, right, center, servo)
    print("About to start")
    test.debugOn()
    if True:
        test.forward()
        print("viewer:", viewer.state)
        sleep(1)
        test.left()
        print("viewer:", viewer.state)
        sleep(1)
        test.backward()
        print("viewer:", viewer.state)
        sleep(1)
        test.right()
        print("viewer:", viewer.state)
        sleep(1)
        test.value = (.5, -.5, .5, -.5)
        print("viewer:", viewer.state)
        sleep(1)
    test.stop()
    print("viewer:", viewer.state)
    print("Finished")
