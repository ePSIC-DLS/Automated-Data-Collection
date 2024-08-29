import abc


class Base(abc.ABC):
    """
    Abstract base class to represent a base component controller.

    Abstract Methods
    ----------------
    __init__

    Attributes
    ----------
    _name: str
        The component's name.
    """

    @property
    def controlling(self) -> str:
        """
        Public access to the controlling component.

        Returns
        -------
        str
            The component's name.
        """
        return self._name

    @abc.abstractmethod
    def __init__(self, name: str):
        self._name = name
