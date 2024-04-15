import abc
import enum
import typing

try:
    import typing_extensions
except ModuleNotFoundError:
    typing_extensions = typing

Src = typing.TypeVar("Src")
Dst = typing.TypeVar("Dst")
Enum = typing.TypeVar("Enum", bound=enum.Enum)

__all__ = [
    "MemberTranslator", "BoolTranslator", "TypeTranslator", "KeyTranslator", "PropertyTranslator",
    "FStringTranslator"
]


class Error(Exception):
    """
    Translation Error
    """
    pass


class Base(typing.Generic[Src, Dst], abc.ABC):
    """
    Abstract base class for translators.

    Each translator can be converted to a string, and can translate from a source type to a destination type.

    Generics
    --------
    Src: Any
        Source Type
    Dst: Any
        Destination Type.

    Abstract Methods
    ----------------
    __str__
    translate
    """

    @abc.abstractmethod
    def __str__(self) -> str:
        pass

    @abc.abstractmethod
    def translate(self, data: Src) -> Dst:
        """
        Translate the input data.

        Parameters
        ----------
        data: Src
            The source data.

        Returns
        -------
        Dst
            The destination data.
        """
        pass


class Pass(Base[Src, Src], typing.Generic[Src]):
    """
    Concrete translator that returns its input.

    Bound Generics
    --------------
    Dst: Src
    """

    def __str__(self) -> str:
        return "v"

    def translate(self, data: Src) -> Src:
        return data


class Mixin(Base[Src, Dst], typing.Generic[Src, Dst], abc.ABC):
    """
    A 'mixin' class that has an internal translator that it calls and, in some way, mutates the result of.

    Abstract Methods
    ----------------
    __str__

    Attributes
    ----------
    _t: Base[Src, Dst]
        The translator to apply.
    """

    def __init__(self, inner: Base[Src, Dst]):
        self._t = inner

    def translate(self, data: Src) -> Dst:
        return self._t.translate(data)


class IterableMixin(Mixin[Src, Dst], typing.Generic[Src, Dst]):
    """
    Concrete mixin that applies the translation to all elements of an iterable.
    """

    def __str__(self) -> str:
        return f"map({self._t}, v)"

    def translate(self, data: typing.Iterable[Src]) -> typing.Iterable[Dst]:
        """
        Translates the iterable.

        Parameters
        ----------
        data: Iterable[Src]
            The input iterable.

        Yields
        ------
        Dst
            The translated element of the iterable.
        """
        yield from map(self._t.translate, data)


class MemberTranslator(Base[str, Enum], typing.Generic[Enum]):
    """
    An enumeration translator that translates member names to their relevant enumeration value.

    Bound Generics
    --------------
    Dst: Enum

    Generics
    --------
    Enum: enum.Enum
        The enumeration type.

    Attributes
    ----------
    _cls: Type[Enum]
        The enumeration type.
    """

    @property
    def cls(self) -> typing.Type[Enum]:
        """
        Public access to the enumeration type.

        Returns
        -------
        Type[Enum]
            The type of enumeration to validate against.
        """
        return self._cls

    def __init__(self, cls: typing.Type[Enum]):
        self._cls = cls

    def __str__(self) -> str:
        return f"{self._cls}[v]"

    def translate(self, data: str) -> Enum:
        """
        Translates the member name to their relevant enumeration member.

        Parameters
        ----------
        data: str
            The member name.

        Returns
        -------
        Enum
            The corresponding enumeration member.

        Raises
        ------
        Error
            If the member does not exist.
        """
        try:
            return self._cls[data]
        except KeyError:
            raise Error(f"{data!r} is not a valid {self._cls} member") from None


class BoolTranslator(Base[str, bool]):
    """
    A translator that specifically checks for a string being a valid boolean.
    """

    @property
    def cls(self) -> typing.Type[bool]:
        """
        Public access for the class to translate to.

        Returns
        -------
        Type[bool]
            The boolean type.
        """
        return bool

    def __str__(self) -> str:
        return f"{bool}(v)"

    def translate(self, data: str) -> bool:
        """
        Translates the string to a boolean value.

        It has correct handling of 'true' and 'false' instead of how python interprets it (with the empty string being
        the only string that equates to false).

        Parameters
        ----------
        data: str
            The string to translate.

        Returns
        -------
        bool
            The relevant boolean.

        Raises
        ------
        Error
            If the string (converted to lower case) is not a valid boolean string.
        """
        if data.lower() == "false":
            return False
        elif data.lower() == "true":
            return True
        raise Error(f"Invalid boolean string {data!r}")


class TypeTranslator(Base[typing.Any, Dst], typing.Generic[Dst]):
    """
    A generic type translator.

    Bound Generics
    --------------
    Src: Any

    Attributes
    ----------
    _cls: Type[Dst]
        The output type.
    """

    @property
    def cls(self) -> typing.Type[Dst]:
        """
        Public access for the class to translate to.

        Returns
        -------
        Type[Dst]
            The output type.
        """
        return self._cls

    def __init__(self, cls: typing.Type[Dst]):
        self._cls = cls

    def __str__(self) -> str:
        return f"{self._cls}(v)"

    def translate(self, data: typing.Any) -> Dst:
        """
        Attempt to call the output type's constructor on the given data.

        Parameters
        ----------
        data: Any
            The input data to translate.

        Returns
        -------
        Dst
            The translated data instance.

        Raises
        ------
        Error
            If the input data cannot be translated.
        """
        try:
            return self._cls(data)
        except TypeError as err:
            raise Error(f"{data!r} cannot be type-casted to {self._cls} due to {err!r}")


class KeyTranslator(Base[typing.Mapping[Src, Dst], Dst], typing.Generic[Src, Dst]):
    """
    A translator that takes an input mapping and returns the relevant value from the key.

    This translation is essentially `input[_key]`.

    Attributes
    ----------
    _key: Src
        The key to get.
    _out: Type[Dst]
        The output dtype (only present to make sure that the generic is fully typeable)
    """

    @property
    def key(self) -> Src:
        """
        Public access to the key.

        Returns
        -------
        Src
            The key to get from the mapping.
        """
        return self._key

    def __init__(self, key: Src, out_type: typing.Type[Dst]):
        self._key = key
        self._out = out_type

    def __str__(self) -> str:
        if isinstance(self._key, slice):
            key = ":"
            if self._key.start is not None:
                key = f"{self._key.start}{key}"
            if self._key.stop is not None:
                key = f"{key}{self._key.stop}"
            if self._key.step is not None:
                key = f"{key}:{self._key.step}"
        else:
            key = str(self._key)
        return f"v[{key}]"

    def translate(self, data: typing.Mapping[Src, Dst]) -> Dst:
        """
        Grab the key from the input mapping.

        Parameters
        ----------
        data: Mapping[Src, Dst]
            The mapping of keys to values. This doesn't necessarily mean it's a dictionary - a list can be a mapping of
            integers to the contained type (the integer 'keys' are indices).

        Returns
        -------
        Dst
            The value from the key.

        Raises
        ------
        Error
            If the key doesn't exist.
        """
        try:
            return data[self._key]
        except LookupError as err:
            raise Error(f"{data} cannot find {self._key} due to {err!r}")


class PropertyTranslator(Base[Src, Dst], typing.Generic[Src, Dst]):
    """
    Similar to a key translator but this time for properties.

    This means the relevant code is `input._attr`.

    As there is no way to correctly type the generic, it must be specified prior to creation.
    E.G. PropertyTranslator[np.ndarray, tuple[int, ...]]("shape")

    Attributes
    ----------
    _attr: str
        The property name to get.

    Raises
    ------
    ValueError
        If the property name is not an identifier, or is non-public (starts with an underscore).
    """

    @property
    def attribute(self) -> str:
        """
        Public access to the attribute name.

        Returns
        -------
        str
            The property name to get.
        """
        return self._attr

    def __init__(self, prop_name: str):
        self._attr = prop_name
        if not prop_name.isidentifier() or prop_name.startswith("_"):
            raise ValueError(f"Expected a valid, public property. Got {prop_name!r}")

    def __str__(self) -> str:
        return f"v.{self._attr}"

    def translate(self, data: Src) -> Dst:
        """
        Retrieve the attribute from the input object.

        Parameters
        ----------
        data: Src
            The input object.

        Returns
        -------
        Dst
            The output attribute.

        Raises
        ------
        Error
            If the attribute doesn't exist.
        """
        try:
            return getattr(data, self._attr)
        except AttributeError:
            raise Error(f"{data!r} has no attribute {self._attr!r}")


class FStringTranslator(Base[str, str]):
    """
    Translator for formatting strings.

    Bound Generics
    --------------
    Src: str
    Dst: str

    Attributes
    ----------
    _new: str
        The base string to format the input data into.
    _field: str
        The two-character string to act as the format field. This means that any time the field appears, it will get
        substituted with the input data.

    Raises
    ------
    ValueError
        If the field is not 2 characters long.
    """

    def __init__(self, new_form: str, *, replacement="{}"):
        if len(replacement) != 2:
            raise ValueError(f"Expected replacement field to be something that can surround v (such as brackets). "
                             f"Got {replacement!r}")
        self._new = new_form
        self._field = replacement

    def __str__(self) -> str:
        field = f"{self._field[0]}v{self._field[1]}"
        return f"f\"{self._new.replace(self._field, field)}\""

    def translate(self, data: str) -> str:
        """
        Substitute the input string into this object's base string.

        Parameters
        ----------
        data: str
            The format data.

        Returns
        -------
        str
            The formatted string.
        """
        return self._new.replace(self._field, data)


class SubstitutionTranslator(Base[str, str]):
    """
    Acts as the inverse of the `FStringTranslator`.

    Rather than substituting the input into a known string, substitute the known string into the input.

    Bound Generics
    --------------
    Src: str
    Dst: str

    Attributes
    ----------
    _r: str
        The replacement to format into the input data.
    _field: str
        The two-character string to act as the format field. This means that any time the field appears, it will get
        substituted with the input data.

    Raises
    ------
    ValueError
        If the field is not 2 characters long.
    """

    def __init__(self, constant: str, *, replacement="{}"):
        if len(replacement) != 2:
            raise ValueError(f"Expected replacement field to be something that can surround v (such as brackets). "
                             f"Got {replacement!r}")
        self._r = constant
        self._field = replacement

    def __str__(self) -> str:
        return f"v.replace({self._field!r}, {self._r!r})"

    def translate(self, data: str) -> str:
        """
        Substitute this object's base string into the input data.

        Parameters
        ----------
        data: str
            The input data.

        Returns
        -------
        str
            The formatted string.
        """
        return data.replace(self._field, self._r)
