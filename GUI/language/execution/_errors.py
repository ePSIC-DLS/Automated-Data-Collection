from ..grammar import tokens as _tokens


class RunTimeError(Exception):
    """
    Exception raised when the interpreter fails.
    """

    def __init__(self, token: _tokens.Token, msg: str):
        super().__init__(f"{msg} at {token.rc_ref}")


class Return(Exception):
    """
    Exception raised when the interpreter interprets a return statement.

    Using an exception allows for stack unwinding.

    Attributes
    ----------
    _value: Any
        The value to return
    """

    @property
    def value(self):
        """
        Public access to the return value.

        Returns
        -------
        Any
            The value to return.
        """
        return self._value

    def __init__(self, value=None):
        self._value = value
        super().__init__(value)


class ResolutionError(Exception):
    """
    Exception raised when the resolver fails.
    """

    def __init__(self, token: _tokens.Token, msg: str):
        super().__init__(f"{msg} at {token.rc_ref}")
