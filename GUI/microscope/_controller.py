"""
Module to create a base controller for specific microscope hardware.
"""

import abc
import typing
from modular_qt import validators

MappedGetter: typing.TypeAlias = typing.Callable[[], typing.Any]
MappedSetter: typing.TypeAlias = typing.Callable[[typing.Any], None]


class Singleton(abc.ABCMeta):
    """
    Metaclass for representing a singleton – a class that only ever has one instance.

    Useful for microscope hardware to prevent multiple instantiations and overwriting of settings.
    """
    _instance: typing.Self = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

    def get_instance(cls) -> typing.Self:
        """
        Convenience method for getting a pre-created instance of a singleton.

        Only useful when the instance is guaranteed to have been created.
        :return: The pre-created instance.
        :raises KeyError: If the singleton hasn't yet been created.
        """
        if cls._instance is None:
            raise KeyError("Singleton has not been instantiated")
        return cls._instance


class ControllerBase(abc.ABC, metaclass=Singleton):
    """
    Abstract base singleton to represent a controller for some hardware in the microscope.

    Has a series of keys that can be set and retrieved.
    Results are cached for fast execution.
    """

    @property
    def controller(self) -> str:
        """
        Find the name of the hardware this controller controls.

        :return: The hardware name.
        """
        return self._hardware[:self._hardware.find(" ")]

    @abc.abstractmethod
    def __init__(self, name: str, **mapping: tuple[MappedGetter, typing.Optional[MappedSetter]]):
        self._mapping = mapping
        self._cache: dict[str, typing.Any] = {}
        self._hardware = f"{name} controller"

    def __getitem__(self, item: str) -> typing.Any:
        """
        Retrieves a specific key from the cache. If not in the cache, will retrieve it from the microscope first.

        :param item: The key to retrieve.
        :return: The value of the key. For type details, see 'help(type(self))'
        :raises TypeError: If the key isn't a string.
        :raises KeyError: If the key doesn't exist.
        """
        if not isinstance(item, str):
            raise TypeError("Expected item to be a string")
        if item not in self._cache:
            getter = self._mapping.get(item)
            if getter is None:
                raise KeyError(f"{self._hardware} has no key {item!r}")
            self._cache[item] = getter[0]()
        return self._cache[item]

    def __setitem__(self, item: str, value: typing.Any):
        """
        Changes a specific key from the microscope. Will remove the key from the cache.

        :param item: The key to retrieve.
        :param value: The new value of the key. For type details, see 'help(type(self))'
        :raises TypeError: If the key isn't a string.
        :raises KeyError: If the key doesn't exist.
        :raises ValueError: If the value isn't correct.
        :raises AttributeError: If the key can't be set.
        """
        if not isinstance(item, str):
            raise TypeError("Expected item to be a string")
        self._cache.pop(item, None)
        setter = self._mapping.get(item, (0, 0))[1]
        if setter == 0:
            raise KeyError(f"{self._hardware} has no key {item!r}")
        elif setter is None:
            raise AttributeError(f"Cannot set property {item!r}")
        self.validators()[item].validate(value)
        setter(value)

    @staticmethod
    @abc.abstractmethod
    def validators() -> dict[str, validators.Pipeline]:
        """
        Find the validators associated with this controller.

        These will ensure any passed values are validated prior to setting.
        :return: A dictionary of key name to validator.
        """
        pass

    def keys(self) -> typing.Iterator[str]:
        """
        Method to produce an iterator of possible keys for this controller.

        :return: An iterator of strings for each key in the controller's control.
        """
        yield from self._mapping.keys()

    def wipe(self):
        """
        Method to clear the cache of the hardware controller.
        """
        self._cache.clear()
