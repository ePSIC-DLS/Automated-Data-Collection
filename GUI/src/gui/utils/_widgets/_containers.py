import typing
from typing import List as _list, Tuple as _tuple

import math
from PyQt5 import QtCore as core, QtGui as gui, QtWidgets as widgets

from ._base import Forwarder
from .._enums import *

W = typing.TypeVar("W", bound=widgets.QWidget)

__all__ = ["LabelledWidget", "DoubleLabelledWidget", "OrderedGroup"]


class LabelledWidget(widgets.QWidget, typing.Generic[W], metaclass=Forwarder):
    """
    A container widget that provides a label for the contained widget. This label can be in prefix or suffix.

    Generics
    --------
    W: widgets.QWidget
        The widget contained.

    Attributes
    ----------
    _label: widgets.QLabel
        The label of the contained widget.
    _widget: W
        The widget contained by this container.
    """

    @property
    def label(self) -> widgets.QLabel:
        """
        Public access to the underlying label.

        Returns
        -------
        widgets.QLabel
            The label of the contained widget.
        """
        return self._label

    @property
    def focus(self) -> W:
        """
        Public access to the underlying widget.

        Returns
        -------
        W
            The contained widget.
        """
        return self._widget

    def __init__(self, context: str, widget: W, order: LabelOrder):
        super().__init__()
        layout = widgets.QHBoxLayout()
        self.setLayout(layout)
        self._label = widgets.QLabel(context)
        self._widget = widget
        if order == LabelOrder.PREFIX:
            layout.addWidget(self._label)
        layout.addWidget(self._widget)
        if order == LabelOrder.SUFFIX:
            layout.addWidget(self._label)


class DoubleLabelledWidget(widgets.QWidget, typing.Generic[W], metaclass=Forwarder):
    """
    A widget that has a double label - one for name and one for description.

    Generics
    --------
    W: widgets.QWidget
        The widget to contain.

    Attributes
    ----------
    _widget: LabelledWidget[LabelledWidget[W]]
        The contained widget. It is already double-labelled.

    Parameters
    ----------
    name: str
        The name of the widget.
    widget: W
        The widget to contain.
    desc: str
        The description of the widget.
    name_pos: LabelOrder
        The position of the name.
    desc_pos: LabelOrder
        The position of the description.

    Raises
    ------
    ValueError
        If the name and description are on the same side.
    """

    def __init__(self, name: str, widget: W, desc: str, *, name_pos=LabelOrder.PREFIX, desc_pos=LabelOrder.SUFFIX):
        if name_pos == desc_pos:
            raise ValueError(f"Must have different name and desc positions")
        super().__init__()
        desc = LabelledWidget(f"({desc})", widget, desc_pos)
        self._widget = LabelledWidget(name, desc, name_pos)
        layout = widgets.QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self._widget)


class OrderedGroup(widgets.QWidget, typing.Generic[W]):
    """
    A widget that represents a group of widgets with a particular order.

    These widgets can be re-ordered, and are displayed in a vertical orientation. To help view them, they can be
    scrolled through

    Generics
    --------
    W: widgets.QWidget
        The type of inner widget that can be ordered.

    Signals
    -------
    orderChanged: int, int
        Emitted when the order of two widgets is changed.

    Events
    ------
    mousePress
        Handle pressing on a member to re-order it.
    mouseRelease
        Handles re-ordering members based on stored index and current index.
    wheel
        Handle scrolling through the members.

    Attributes
    ----------
    DISPLAY: int
        The amount of displayed widgets (default is 15).

    _layout: widgets.QGridLayout
        The layout of the widget. Will add all the widgets in order and redraw when needed.
    _members: list[W]
        The members of this widget. Is a list to allow re-ordering, clearing, and adding.
    _labels: list[QLabel]
        The labels generated alongside the widgets.
    _show: int
        The start index to show the widgets from.
    _scrolled: int
        The amount of scroll. This needs to reach a fixed value of 120 (the standard scroll unit for mice) to allow for
        the viewport to move, therefore high precision devices will need to scroll more to reach the same result.
    _stored: int | None
        The index of the widget to reorder.
    """
    DISPLAY = 15

    orderChanged = core.pyqtSignal(int, int)

    def __init__(self, *members: W):
        super().__init__()
        self._layout = widgets.QGridLayout()
        self._members = list(members)
        self._labels: _list[widgets.QLabel] = []
        self._show = self._scrolled = 0
        self._stored: typing.Optional[int] = None
        self._draw()
        self.setLayout(self._layout)

    def get_members(self) -> _tuple[W, ...]:
        """
        Get all the members as an immutable data structure.

        Returns
        -------
        tuple[W, ...]
            The members of the widget.
        """
        return tuple(self._members)

    def clear_members(self):
        """
        Wipe all members, completely clearing the widget.
        """
        self._members.clear()
        self._draw()

    def add_member(self, new: W):
        """
        Add a new member to the list.

        This allows for dynamic collections.

        Parameters
        ----------
        new: W
            The new member to be added to the group.
        """
        self._members.append(new)
        self._draw()

    def configure_members(self, get: typing.Callable[[W], object], set_: typing.Callable[[W, object], None], *settings):
        if (exp := len(self._members)) != (acc := len(settings)):
            raise ValueError(f"Expected {exp} elements")
        values = set(map(get, self._members))
        if any(v not in values for v in settings) or len(set(settings)) != acc:
            raise ValueError(f"Expected all values to be unique and in {values}")
        for member, var in zip(self._members, settings):
            set_(member, var)

    def mousePressEvent(self, a0: gui.QMouseEvent):
        """
        Handle clicking on the widget.

        This will store the index of the clicked widget.

        Parameters
        ----------
        a0: gui.QMouseEvent
            The event that caused this callback.
        """
        for i, (label, member) in enumerate(zip(self._labels, self._members[self._show:self._show + self.DISPLAY]),
                                            self._show):
            if member.geometry().contains(a0.pos(), True) or label.geometry().contains(a0.pos(), True):
                self._stored = i
                break

    def mouseReleaseEvent(self, a0: gui.QMouseEvent):
        """
        Handle releasing the mouse on the widget.

        This will swap the stored index with the widget under the mouse cursor.

        Parameters
        ----------
        a0: gui.QMouseEvent
            The event that caused this callback.
        """
        if self._stored is None:
            return a0.accept()
        for i, (label, member) in enumerate(zip(self._labels, self._members[self._show:self._show + self.DISPLAY]),
                                            self._show):
            if member.geometry().contains(a0.pos(), True) or label.geometry().contains(a0.pos(), True):
                self._members[self._stored], self._members[i] = self._members[i], self._members[self._stored]
                self._draw()
                self.orderChanged.emit(self._stored, i)
                break

    def wheelEvent(self, a0: gui.QWheelEvent):
        """
        Handle scroll wheel events.

        This will shift the view such that different widgets are available.

        Parameters
        ----------
        a0: gui.QWheelEvent
            The wheel event that caused this callback.
        """
        y = a0.angleDelta().y()
        self._scrolled += abs(y)
        if self._scrolled >= 120:
            self._scrolled -= 120
            if self._show == 0 and y > 0:
                return a0.accept()
            elif self._show + self.DISPLAY >= len(self._members) and y < 0:
                return a0.accept()
            self._show -= int(math.copysign(1, y))
            self._draw()

    def _draw(self):
        while (item := self._layout.takeAt(0)) is not None:
            self._layout.removeItem(item)
            item.widget().hide()
        self._labels = []
        for i, member in enumerate(self._members, 1):
            j = i - 1
            if j < self._show:
                continue
            elif j > self._show + self.DISPLAY:
                break
            self._labels.append(widgets.QLabel(f"#{i}:"))
            self._layout.addWidget(self._labels[-1], j, 0)
            self._layout.addWidget(member, j, 1)
            member.show()
