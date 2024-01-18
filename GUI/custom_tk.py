"""
Module for custom tkinter objects such as custom spinboxes, setting controls, and popups
"""
from __future__ import annotations

import abc
import tkinter as tk
from tkinter import ttk

from utils import *


class Spinbox(tk.Spinbox):
    """
    Custom spinbox widget, with certain values fixed and forced validation
    """

    def __init__(self, master=..., *, bg=..., fg=..., font=..., increment: float,
                 textvariable: tk.DoubleVar | tk.IntVar, values: typing.Union[typing.Iterable[float], LazyLinSpace],
                 dtype: type):
        if dtype not in (int, float):
            raise TypeError("Dtype can only be numerical")
        vals: dict[str, typing.Any] = {}
        if isinstance(values, LazyLinSpace):
            b = values.bounds
            vals.update(from_=b[0] + (increment * (not values.do_start)), to=b[1] - (increment * (not values.do_end)))
        else:
            vals.update(values=list(map(str, values)))
        if bg is not ...:
            vals["bg"] = bg
        if fg is not ...:
            vals["fg"] = fg
        if font is not ...:
            vals["font"] = font
        if master is not ...:
            vals["master"] = master

        self._values = values
        self._var = textvariable
        self._type = dtype
        self._i = increment
        initial = self._var.get()
        if initial == "" or all(v == " " for v in str(initial)):
            initial = "0"
        super().__init__(increment=increment, justify=tk.CENTER, textvariable=self._var, **vals)
        self._var.set(initial)
        self.after(50, self._bounds)

    def _bounds(self):
        if isinstance(self._values, DynamicLazyLinSpace):
            f, t = self._values.bounds
            self.config(from_=f + (self._i * (not self._values.do_start)), to=t - (self._i * (not self._values.do_end)))
            self.after(50, self._bounds)

    def _is_num(self) -> bool:
        value = self._var.get()
        if value == "" or all(v == " " for v in str(value)):
            value = "0"
        try:
            value = float(value)
            return value in self._values
        except ValueError:
            return False

    def _is_null(self) -> bool:
        self._var.set(self._type())
        return True

    def validate(self) -> bool:
        """
        Run validation
        :return: Whether the validation was successful
        """
        if not self._is_num():
            return not self._is_null()
        return True


class AdvancedSetting(abc.ABC):
    """
    Class to represent an advanced setting group with an overall name, and a name and description for each control

    :var _main_frame tkinter.LabelFrame: The surrounding frame for the group
    :var _frames: list[tkinter.Frame]: The list of frames for each control
    """

    @property
    @abc.abstractmethod
    def descriptions(self) -> typing.Iterable[str]:
        """
        Descriptions of each control
        :return: An iterable for the descriptions of every setting in the group
        """
        pass

    @abc.abstractmethod
    def __init__(self, window: tk.Toplevel, name: str, *descriptions: str,
                 anchor: typing.Literal["nw", "n", "ne", "en", "e", "es", "se", "s", "sw", "ws", "w", "wn", ""] = tk.N):
        if anchor:
            self._main_frame = tk.LabelFrame(window, text=name, font=("Consolas", 12, "bold"), labelanchor=anchor)
        else:
            self._main_frame = tk.Frame(window)
        self._frames = [tk.Frame(self._main_frame) for _ in descriptions]
        self._main_frame.pack(fill=tk.X, pady=5, ipady=5)
        for frame, desc in zip(self._frames, descriptions):
            frame.pack(fill=tk.X)
            tk.Label(frame, text=desc.title(), font=("Consolas", 10, "underline")).pack(side=tk.LEFT)
        self._help()

    def _help(self):
        """
        Pack the description label
        """
        for frame, desc in zip(self._frames, self.descriptions):
            tk.Label(frame, text=f"({desc})", font=("Consolas", 8)).pack(side=tk.LEFT)


class SingleControlSetting(AdvancedSetting):
    """
    Class to represent a setting with a single control
    :var _desc str: The description
    """

    @property
    def descriptions(self) -> typing.Iterable[str]:
        yield self._desc

    def __init__(self, window: tk.Toplevel, name: str, description: str, widget: typing.Type[tk.Widget], mod="size",
                 anchor: typing.Literal["nw", "n", "ne", "en", "e", "es", "se", "s", "sw", "ws", "w", "wn", ""] = tk.N,
                 decorate=True, **kwargs):
        self._desc = description
        super().__init__(window, f"{name.title()} {'Settings' if decorate else ''}",
                         f"{name.title()} {mod.title()}", anchor=anchor)
        widget(self._frames[0], **kwargs).pack(side=tk.RIGHT)


class DependantControlSetting(AdvancedSetting):
    """
    Class to represent a group of settings dependent on a list
    :var _desc Iterable[str]: The descriptions for each of the controls.
    :var _decider tkinter.ttk.Combobox: The widget for the list of options.
    :var _widgets: list[tkinter.Widget]: The list of widgets to control
    :var _mapping dict[str, Iterable[int]]: The option values to which widgets it should enable
    """

    @property
    def descriptions(self) -> typing.Iterable[str]:
        yield from self._desc

    def __init__(self, window: tk.Toplevel, name: str, names: typing.Iterable[str], descriptions: typing.Iterable[str],
                 decider: dict, widgets: typing.Iterable[tuple[typing.Type[tk.Widget], dict]],
                 mapping: dict[str, typing.Iterable[int]], decorate=True,
                 anchor: typing.Literal["nw", "n", "ne", "en", "e", "es", "se", "s", "sw", "ws", "w", "wn", ""] = tk.N,
                 **kwargs):
        self._desc = descriptions
        super().__init__(window, f"{name.title()} {'Settings' if decorate else ''}",
                         *map(str.title, names), anchor=anchor)
        self._decider = ttk.Combobox(self._frames[0], **{**kwargs, **decider})
        self._decider.bind("<<ComboboxSelected>>", self._select)
        self._decider.pack(side=tk.RIGHT)
        self._widgets = []
        for i, (widget, options) in enumerate(widgets, 1):
            wid = widget(self._frames[i], **{**kwargs, **options})
            wid.pack(side=tk.RIGHT)
            self._widgets.append(wid)
        self._mapping = mapping
        self._select({})

    def _select(self, event):
        """
        Control what happens to the widgets when an option is selected
        :param event: The event object obtained from switching options
        """
        for widget in self._widgets:
            widget.config(state=tk.DISABLED)
        choice = self._decider.get()
        config = self._mapping.get(choice)
        if config is None:
            return
        for widget_choice in config:
            self._widgets[widget_choice].config(state=tk.NORMAL)


class GroupedSetting(AdvancedSetting):
    """
    A class to represent a group of groups.
    :var _settings list[AdvancedSetting]: The settings created
    """

    @property
    def descriptions(self) -> typing.Iterable[str]:
        yield from map(lambda set_: set_.descriptions, self._settings)

    def __init__(self, window: tk.Toplevel, name: str,
                 settings: typing.Iterable[tuple[typing.Type[AdvancedSetting], dict]]):
        super().__init__(window, name)
        self._frames = [tk.Frame(self._main_frame) for _, options in settings]
        self._settings = [setting(self._frames[i], **options, anchor=tk.W if setting != SingleControlSetting else "",
                                  decorate=False)
                          for i, (setting, options) in enumerate(settings)]
        for f in self._frames:
            f.pack(fill=tk.X)


@tk_singleton
class Popup:
    """
    A popup window that will mark when it's closed
    """

    def __init__(self, window: tk.Tk, closed: tk.IntVar, *settings: tuple[typing.Type[AdvancedSetting], dict[str]]):
        self._window = tk.Toplevel(window)
        closed.set(0)
        self._window.resizable(False, False)
        self._window.protocol("WM_DELETE_WINDOW", lambda: (closed.set(1), self._window.destroy()))
        for cls, kwargs in settings:
            cls(self._window, **kwargs)

    def lift(self):
        self._window.lift()
