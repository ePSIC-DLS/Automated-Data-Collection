import abc


class Base(abc.ABC):

    @property
    def controlling(self) -> str:
        return self._name

    @abc.abstractmethod
    def __init__(self, name: str):
        self._name = name
