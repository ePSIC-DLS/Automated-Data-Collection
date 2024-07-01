import typing

from .._base import Base
from .._utils import *
from ... import validation
from typing import Tuple as _tuple

if ONLINE:
    from PyJEM.TEM3 import Stage3
else:
    from ..PyJEM.offline.TEM3 import Stage3

axis = validation.Pipeline.enum(Axis)
driver = validation.Pipeline.enum(Driver)


class Controller(Base):
    """
    Concrete controller for the stage movement.

    Keys
    ----
    axis: Axis (enum validation)
        The current axis being controlled.
    pos: int (stage_pos validation)
        The current position of the stage in the relevant axis.
    tilt: int (stage_tilt validation, undefined for axis=Axis.Z)
        The current tilt angle of the stage in the relevant axis.
    driver: Driver (enum validation)
        The current driver for the stage movement.
    """

    @Key
    def axis(self) -> Axis:
        """
        Public access to the current controlling axis.

        Returns
        -------
        Axis
            The current axis being controlled.
        """
        return self._axis

    @axis.setter
    def axis(self, value: Axis):
        axis.validate(value)
        self._axis = value

    @Key
    def pos(self) -> int:
        """
        Public access to the current stage position.

        Returns
        -------
        int
            The current position of the stage in the relevant axis.
        """
        if self.axis == Axis.X:
            i = 0
        elif self.axis == Axis.Y:
            i = 1
        else:
            i = 2
        return self._controller.GetPos()[i]

    @pos.setter
    def pos(self, value: int):
        validation.examples.stage_pos.validate(value)
        if self.axis == Axis.X:
            self._controller.SetX(value)
        elif self.axis == Axis.Y:
            self._controller.SetY(value)
        else:
            self._controller.SetZ(value)

    @Key
    def tilt(self) -> int:
        """
        Public access to the current stage tilt.

        Returns
        -------
        int
            The current tilt angle of the stage in the relevant axis.

        Raises
        ------
        ValueError
            If the current axis is Z.
        """
        if self.axis == Axis.X:
            i = 3
        elif self.axis == Axis.Y:
            i = 4
        else:
            raise ValueError("No z-axis tilt")
        return self._controller.GetPos()[i]

    @tilt.setter
    def tilt(self, value: int):
        validation.examples.stage_tilt.validate(value)
        if self.axis == Axis.X:
            self._controller.SetTiltXAngle(value)
        elif self.axis == Axis.Y:
            self._controller.SetTiltYAngle(value)
        else:
            raise ValueError("No z-axis tilt")

    @Key
    def driver(self) -> Driver:
        """
        Public access to the stage driver.

        Returns
        -------
        Driver
            The current driver for the stage movement.
        """
        return Driver(self._controller.GetDrvMode())

    @driver.setter
    def driver(self, value: Driver):
        driver.validate(value)
        self._controller.SelDrvMode(value.value)

    def __init__(self, controlling: Axis, active_driver: Driver = None):
        super().__init__("Stage")
        self._controller = Stage3()
        self.axis = controlling
        if active_driver is not None:
            self.driver = active_driver
        _ = self.pos, self.tilt, self.driver  # this will prime the keys with an instance

    def relative_movement(self, by: int):
        """
        Perform a relative movement in the specified axis.

        Parameters
        ----------
        by: int
            The relative offset of the current axis. Will still undergo validation.
        """
        validation.examples.stage_pos.validate(self.pos + by)
        if self.axis == Axis.X:
            self._controller.SetXRel(by)
        elif self.axis == Axis.Y:
            self._controller.SetYRel(by)
        else:
            self._controller.SetZRel(by)

    def relative_tilt(self, by: int):
        """
        Perform a relative tilt in the specified axis.

        Parameters
        ----------
        by: int
            The relative angle of the current axis. Will still undergo validation.

        Raises
        ------
        ValueError
            If the current axis is Z.
        """
        validation.examples.stage_tilt.validate(self.tilt + by)
        if self.axis == Axis.X:
            self._controller.SetTXRel(by)
        elif self.axis == Axis.Y:
            self._controller.SetTYRel(by)
        else:
            raise ValueError("No z-axis tilt")

    def reset(self):
        """
        Reset the stage to the original position.
        """
        self._controller.SetOrg()

    def snake(self, step: _tuple[int, int, int], size: _tuple[int, int, int]) -> typing.Iterator[None]:
        """
        Perform a snake-like movement in all three axes.

        Parameters
        ----------
        step: tuple[int, int, int]
            The amount to step in each axis.
        size: tuple[int, int, int]
            The number of steps in each axis.

        Yields
        ------
        None
            While this is a generator (to allow iteration over each movement) the value should not be used in the loop
            or sequence of next statements as it is not important. The generator is used to try to emulate an
            asynchronous procedure similar to how `asyncio` works.
        """
        old_axis = self.axis
        outer_loop, middle_loop, inner_loop = size
        x_am, y_am, z_am = step
        for z in range(outer_loop):
            y_di = -y_am if z % 2 else y_am
            for y in range(middle_loop):
                x_di = -x_am if (y + z) % 2 else x_am
                for _ in range(inner_loop):
                    self.axis = Axis.X
                    self.relative_movement(x_di)
                    yield None
                self.axis = Axis.Y
                self.relative_movement(y_di)
                yield None
            self.axis = Axis.Z
            self.relative_movement(z_am)
            yield None
        self.axis = old_axis

    def flat_snake(self, step: _tuple[int, int], size: _tuple[int, int]) -> typing.Iterator[None]:
        """
        Perform a snake-like movement in just the x and y axes. This is a shorthand call.

        Parameters
        ----------
        step: tuple[int, int]
            The amount to step in each used axis.
        size: tuple[int, int]
            The number of steps in each used axis.

        Yields
        ------
        None
            Similar to `snake` the value should not be used.
        """
        yield from self.snake((step[0], step[1], 0), (size[0], size[1], 1))

    switch_axis = axis.switch
    switch_driver = driver.switch
    switch_pos = pos.switch
    switch_tilt = tilt.switch
