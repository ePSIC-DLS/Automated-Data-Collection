from typing import (Generic as _Gen, Type as _Type, Iterator as _Next, Any as _Any)
import enum as _enum
from ._constants import _TS, _TD1, _Enum
from ._translators import *
from ._validators import *
from ._validators import _Error as _VError

__all__ = ["Step", "Pipeline", "Branch"]


class Step(Validator[_TD1], Translator[_TS, _TD1], _Gen[_TS, _TD1]):
    """
    Single stage in the validation pipeline. Can represent a permanent or temporary translation.

    :var Validator[_TD1] _v: The internal validator.
    :var Translator[_TS, _TD1] _t: The internal translator.
    :var bool _temp: Whether this stage is a temporary translator.
    """

    @property
    def temporary(self) -> bool:
        """
        Public access to the permanent status of the stage.

        :return: Whether this stage is a temporary translator.
        """
        return self._temp

    def __init__(self, v: Validator[_TD1], t: Translator[_TS, _TD1] = None, *, temporary_translation=False):
        self._v = v
        self._t = t
        self._temp = temporary_translation

    def __getattr__(self, item: str):
        try:
            return getattr(self._v, item)
        except AttributeError:
            return getattr(self._t, item)

    def __str__(self) -> str:
        trans = f" => '{self._t}'" if self._t is not None else ""
        return f"(v{trans} -> {self._v})"

    def validate(self, ans: _TD1) -> None:
        """
        Validate the data based on the constraint in the stage. Will transform the data first.

        :param ans: The data to validate.
        :raises _Error: If the data is not valid.
        """
        if isinstance(self._v, TrueValidator):
            return
        self._v.validate(self.translate(ans))

    def translate(self, ans: _TS) -> _TD1:
        """
        Translate the data based on the translation in the stage.

        Will return the input if no translation is provided.
        :param ans: The data to translate.
        :return: The translated data.
        """
        if self._t is None:
            return ans
        return self._t.translate(ans)

    @classmethod
    def pure_translator(cls, translator: Translator[_TS, _TD1]) -> "Step[_TS,_TD1]":
        """
        Alternate constructor to have a stage that is only a translator, with no validation.

        :param translator: The translator to apply.
        :return: The stage in the pipeline.
        """
        return cls(TrueValidator(), translator)

    @classmethod
    def type(cls, output: _Type[_TD1], v: Validator[_TD1] = TrueValidator()) -> "Step[_TS,_TD1]":
        """
        Alternate constructor to have a stage that translates into a specific output type, with optional validation.

        :param output: The output type.
        :param v: The validator to apply.
        :return: The stage in the pipeline.
        """
        return cls(v, TypeTranslator(output))

    @classmethod
    def percentage(cls, start=0.0, end=1.0, bounds=Include.LOW | Include.HIGH) -> "Step[_TS, float]":
        """
        Alternate constructor to have a stage for a percentage range of values.

        :param start: The start point (should be between 0 and end).
        :param end: The end point (should be between start and 1)
        :param bounds: The inclusive bounds of the validator.
        :return: The stage in the pipeline.
        """
        if not 0.0 <= start < end <= 1.0:
            raise ValueError(f"Expected start ({start}) to be between 0 and the end ({end}). "
                             f"Also expected end to be between the start and 1.")
        return cls.type(float, RangeValidator(start, end, bounds))


class Pipeline(Validator, Translator):
    """
    A pipeline representing a complete check of all types and data ranges for a single piece of data.

    :var tuple[Step, ...] _pipe: The individual stages.
    """

    def __init__(self, *stages: Step):
        self._pipe = stages

    def __getattr__(self, item: str):
        for vt in self._pipe:
            try:
                return getattr(vt, item)
            except AttributeError:
                continue
        raise AttributeError(f"No step in pipeline has attribute {item}")

    def __str__(self) -> str:
        string = []
        prev = None
        for i, vt in enumerate(self._pipe):
            if i == 0:
                string.append(str(vt))
            else:
                string.append(f" {'=>' if not (prev or vt).temporary else '&'} {vt}")
            prev = vt
        return f"<{''.join(string)}>"

    def __iter__(self) -> _Next[Step]:
        yield from self._pipe

    def __add__(self, other: "Pipeline") -> "Pipeline":
        """
        A non-commutative operation to add two pipelines together in their particular order.

        :param other: The other pipeline to add to the end of this one.
        :return: A new pipeline with the steps from both.
        """
        if not isinstance(other, Pipeline):
            return NotImplemented
        return Pipeline(*self, *other)

    def validate(self, ans: _Any) -> None:
        """
        Validate the data based on every constraint in the pipeline.

        After the validation, if it is not a temporary stage, the data will be translated prior to moving to the next
        stage.
        :param ans: The data to validate.
        :raises _Error: If the data fails any of the constraints.
        """
        for vt in self._pipe:
            vt.validate(ans)
            if not vt.temporary:
                ans = vt.translate(ans)

    def translate(self, ans: _Any) -> _Any:
        """
        Translate the data based on every translation in the pipeline.

        Will skip temporary stages.
        :param ans: The data to translate.
        :return: The final translated data.
        """
        for vt in self._pipe:
            if vt.temporary:
                continue
            ans = vt.translate(ans)
        return ans

    @staticmethod
    def strict_int() -> "Pipeline":
        """
        Alternate constructor to force data to be an integer, but using validation to ensure no data loss.

        :return: The pipeline transforming data into an integer losslessly.
        """
        return Pipeline(
            Step.type(float, StrictIntValidator()),
            Step.type(int)
        )

    @staticmethod
    def bound_int(further: Validator[int]) -> "Pipeline":
        """
        Alternate constructor to add further validation to an integer.

        :param further: The further validation to apply.
        :return: A strict integer pipeline extended with the provided validation.
        """
        return Pipeline.strict_int() + Pipeline(Step(further))

    @staticmethod
    def enum(members: _Type[_Enum]) -> "Pipeline":
        """
        Alternate constructor to validate the data as an enum member - regardless of prior type.

        :param members: The enum class to use.
        :return: The pipeline.
        """
        enum_name = Branch(Step(StrictTypeValidator(_enum.Enum)),
                           Step.pure_translator(PropertyTranslator("name")),
                           Step.pure_translator(FStringTranslator("\'{}\'")), safety=TypeTranslator(str))
        from_name = Pipeline.prefixed_str("\'") + Pipeline(Step.pure_translator(EnumTranslator(members)))
        return enum_name + from_name

    @staticmethod
    def prefixed_str(match: str) -> "Pipeline":
        """
        Alternate constructor to check for a string that has the prefix at the starting and ending positions.

        :param match: The prefix to check for.
        :return: The pipeline.
        """
        if len(match) != 1:
            raise ValueError(f"Expected match to be a single character")
        return Pipeline(
            Step.type(str),
            Step(ValueValidator(match), PositionTranslator(0), temporary_translation=True),
            Step(ValueValidator(match), PositionTranslator(-1), temporary_translation=True),
            Step.pure_translator(PositionTranslator(slice(1, -1)))
        )

    @staticmethod
    def integer_percentage(start=0.0, end=1.0, bounds=Include.LOW | Include.HIGH) -> "Pipeline":
        """
        Alternate constructor to form a percentage checker that makes sure the result is an integer within 1 - 100.

        :param start: The minimum percentage.
        :param end: The maximum percentage.
        :param bounds: The inclusivity.
        :return: The pipeline.
        """
        return Pipeline(Step.percentage(start, end, bounds),
                        Step.pure_translator(BinaryTranslator(BinaryOperator.MULTIPLY, 100))
                        ) + Pipeline.strict_int()

    @staticmethod
    def static_iterable(size: int, inner_type: type) -> "Pipeline":
        """
        Alternate constructor to validate an iterable of static type and length.

        To use this for integers, use the 'int_iterable' method instead.
        :param size: The size of the iterable.
        :param inner_type: The inner type of the iterable.
        :return: The pipeline.
        """
        return Pipeline(Step(ValueValidator(size), SizeTranslator(), temporary_translation=True),
                        Step.pure_translator(IterableMixinTranslator(TypeTranslator(inner_type))),
                        Step.type(tuple))

    @staticmethod
    def int_iterable(size: int) -> "Pipeline":
        """
        Alternate constructor to validate an iterable of static size filled with integers.

        :param size: The size of the iterable.
        :return: The pipeline.
        """
        return Pipeline(Step(ValueValidator(size), SizeTranslator(), temporary_translation=True),
                        Step(IterableMixinValidator(StrictIntValidator()),
                             IterableMixinTranslator(TypeTranslator(float))),
                        Step.pure_translator(IterableMixinTranslator(TypeTranslator(int))),
                        Step.type(tuple))


class Branch(Pipeline):
    """
    Special form of a pipeline that can rewind its progress.

    Useful for when the **whole** pipeline is a temporary step and only applicable if it passes.
    """

    def __init__(self, *stages: Step, safety: Translator):
        super().__init__(*stages)
        self._safe = safety

    def __iter__(self) -> _Next[Step]:
        yield Step(self, self)

    def __str__(self) -> str:
        return f"Try: [{super().__str__()}]"

    def validate(self, ans: _Any):
        try:
            super().validate(ans)
        except _VError:
            return
