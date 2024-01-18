"""
Function to facilitate stage control
"""

import typing

from . import __online__

if __online__:
    from .PyJEM.TEM3 import Stage3
else:
    from .PyJEM.offline.TEM3 import Stage3
from ._controller import ControllerBase, validators
from ._enums import *


class Controller(ControllerBase):
    """
    Concrete subclass to control the stage.

    Keys:
        * driver (Driver): The current stage driver
        * motor_pos (tuple[int, int, int]): The current stage motor position
        * piezo_pos (tuple[int, int], read-only): The current stage piezo position
        * tilt (tuple[int, int]): The current tilt of the stage motor
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            driver=validators.Pipeline.enum(Driver),
            motor_pos=validators.Pipeline.int_iterable(3) + validators.Pipeline(
                validators.Step(validators.IterableMixinValidator(validators.RangeValidator(int(-1e5), int(1e5)))),
            ),
            tilt=validators.xmpls.two_elem_int + validators.Pipeline(
                validators.Step(validators.IterableMixinValidator(validators.RangeValidator(-90, 90)))
            )
        )

    def __init__(self, driver: Driver, *, offset: tuple[int, int] = None):
        self._controller = Stage3()
        super().__init__(
            "stage",
            driver=(lambda: Driver(self._controller.GetDrvMode()), self._change_driver),
            motor_pos=(self._read_pos, self._write_pos),
            piezo_pos=(lambda: tuple(self._controller.GetPiezoPosi()), None),
            tilt=(self._read_tilt, self._write_tilt)
        )
        self["driver"] = driver
        if offset is not None:
            self["motor_pos"] = offset

    def _read_pos(self) -> tuple[int, int, int]:
        ans = self._controller.GetPos()
        return ans[0], ans[1], ans[2]

    def _write_pos(self, axis: tuple[int, int, int]):
        self._controller.SetPosition(axis[0], axis[1])
        self._controller.SetZ(axis[2])

    def _read_tilt(self) -> tuple[int, int]:
        ans = self._controller.GetPos()
        return ans[3], ans[4]

    def _write_tilt(self, xy: tuple[int, int]):
        self._controller.SetTiltXAngle(xy[0])
        self._controller.SetTiltYAngle(xy[1])

    def _change_driver(self, driver: Driver):
        if not isinstance(driver, Driver):
            raise TypeError("Expected a driver")
        self._controller.SelDrvMode(driver.value)

    def move_axis(self, axis: Axis, amount: int, *, mode=Shift.RELATIVE):
        """
        Move the stage along the specified axis.

        :param axis: The axis(es) to move the stage about.
        :param amount: The amount of shift.
        :param mode: Whether to move by that amount or move to that amount.
        """
        if amount < -1e5 or amount > 1e5:
            raise ValueError("Amount out of range")
        for test, relative, absolute in ((Axis.X, self._controller.SetXRel, self._controller.SetX),
                                         (Axis.Y, self._controller.SetYRel, self._controller.SetY),
                                         (Axis.Z, self._controller.SetZRel, self._controller.SetZ)):
            if axis & test:
                if mode == Shift.RELATIVE:
                    relative(amount)
                else:
                    absolute(amount)

    def reset(self):
        """
        Reset the stage to original position.
        """
        self._controller.SetOrg()

    def snake(self, x_step: int, y_step: int, z_step: int, size: tuple[int, int, int]) -> typing.Iterator[None]:
        """
        Implement a single-threaded asynchronous snake-like movement (using generators to simulate co-routines).

        Will exhaust x-movements, then move y once before exhausting x again. When y is exhausted, z is moved once.
        This process is repeated until z is exhausted.

        Examples::

            stage = Controller()
            movement = stage.snake(5, 5, 5, (3, 3, 3)) #no movement
            # execute something
            next(movement) # 1 x-movement
            # execute something
            next(movement) # another x-movement

            stage = Controller()
            for _ in stage.snake(3, 2, 1, (2, 2, 2)):
                # execute something

        When using a for-loop approach, it will execute one x-movement **before** entering the for-loop.
        :param x_step: The size of each x-movement.
        :param y_step: The size of each y-movement.
        :param z_step: The size of each z-movement.
        :param size: The number of movements to do in each axis. Assumes (x, y, z) notation.
        :return: A generator that yields None each time. Values shouldn't be saved from this generator.
        """
        for z in range(size[2]):
            y_direction = -y_step if z % 2 else y_step
            for y in range(size[1]):
                x_direction = -x_step if (z + y) % 2 else x_step
                for _ in range(size[0]):
                    yield self.move_axis(Axis.X, x_direction)
                yield self.move_axis(Axis.Y, y_direction)
            yield self.move_axis(Axis.Z, z_step)

    def snake_2D(self, x_step: int, y_step: int, size: tuple[int, int]) -> typing.Iterator[None]:
        """
        Shortcut to simulate a snake-like movement in two-dimensional space.

        Same as calling self.snake(x_step, y_step, 0, (size[0], size[1], 1)).
        :param x_step: The horizontal step.
        :param y_step: The vertical step.
        :param size: The number of steps to take in each axis. Assumes cartesian convention.
        :return: A generator that yields None. Values shouldn't be extracted from this generator.
        """
        yield from self.snake(x_step, y_step, 0, (size[0], size[1], 1))
