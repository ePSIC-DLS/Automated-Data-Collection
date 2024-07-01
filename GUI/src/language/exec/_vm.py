import enum
import functools
import time
import typing
from sys import stderr
from typing import Dict as _dict, List as _list, Optional as _None, Type as _type

from ..form import Lexer, Parser
from ..grammar import OpCodes
from ..utils import Chunk, InstructionPointer, objs, vals, Stack

V = typing.TypeVar("V", bound=vals.Value)


class Status(enum.Enum):
    OK = enum.auto()
    COMPILE_ERROR = enum.auto()
    RUNTIME_ERROR = enum.auto()


class CallFrame:

    @property
    def chunk(self) -> Chunk:
        return self._func.raw

    @property
    def ip(self) -> InstructionPointer:
        return self._ip

    @ip.setter
    def ip(self, value: InstructionPointer):
        self._ip = value

    @property
    def stack(self) -> Stack[vals.Value]:
        return self._slots

    @property
    def name(self) -> vals.String:
        if not self._func.name.raw:
            return vals.String("script")
        return self._func.name

    def __init__(self, fn: objs.Function, ip: InstructionPointer, slots: Stack[vals.Value]):
        self._func = fn
        self._ip = ip
        self._slots = slots


class Interpreter(vals.Interpreter):

    @property
    def stack(self) -> Stack[vals.Value]:
        return self._stack

    @property
    def frames(self) -> _list[CallFrame]:
        return self._frames

    def __init__(self, var_callback: typing.Callable[[str, vals.Value], None] = None,
                 unknown_callback: typing.Callable[[int], None] = None, output: typing.Callable[[str], None] = None,
                 **predefined: vals.Value):

        if unknown_callback is None:
            def _unknown(code: int):
                try:
                    op_code = OpCodes(code).name
                except ValueError:
                    op_code = "unknown"
                raise ValueError(f"Unhandled OpCode {code} (OpCode is {op_code})")

            unknown_callback = _unknown

        if output is None:
            output = functools.partial(print, file=stderr)

        self._frames: _list[CallFrame] = []
        self._count = 0
        self._stack = Stack[vals.Value]()
        self._globals = {vals.String(k): v for k, v in predefined.items()}
        self._errored = False
        self._var = var_callback
        self._unknown = unknown_callback
        self._print = output

    def run(self, code: str) -> Status:
        tokens = list(Lexer(code).run())
        func = Parser(*tokens, output=self._print).run()
        if func is None:
            return Status.COMPILE_ERROR
        self.push(func)
        self.new_frame(func, self._stack)
        return self._run()

    def new_frame(self, fn: objs.Function, vs: Stack["vals.Value"]):
        self._frames.append(CallFrame(fn, InstructionPointer(*fn.raw), vs))
        self._count += 1

    def push(self, val: vals.Value):
        self._stack.push(val)
        if self._frames and self._frames[-1].stack.top != self._stack.top:
            self._frames[-1].stack.push(val)

    def pop(self) -> vals.Value:
        r = self._stack.pop()
        if self._frames and self._frames[-1].stack.top != self._stack.top:
            self._frames[-1].stack.pop()
        return r

    def _run(self) -> Status:
        frame = self._frames[self._count - 1]
        iter_obj: _None[typing.Union[objs.Iterator, objs.NativeIterator]] = None
        iter_count = 0

        def _read_byte() -> int:
            frame.ip.advance()
            return frame.ip.previous()

        def _read_constant(vt: _type[V] = vals.Value) -> V:
            cnstnt = frame.chunk.constant(_read_byte())
            if not isinstance(cnstnt, vt):
                raise TypeError(f"Expected {vt} but got {type(cnstnt)}")
            return cnstnt

        def _unary(fn: typing.Callable[[vals.Value], vals.Value]):
            self.push(fn(self.pop()))

        def _binary(op: str, f1: typing.Callable[[vals.Value, vals.Value], _None[vals.Value]],
                    f2: typing.Callable[[vals.Value, vals.Value], _None[vals.Value]]) -> _None[Status]:
            right = self.pop()
            left = self.pop()
            if (v_ := f1(left, right)) is not None:
                self.push(v_)
            else:
                if (v_ := f2(right, left)) is not None:
                    self.push(v_)
                else:
                    return self._error(f"Unsupported operands for {op} {left.NAME!r} and {right.NAME!r}")

        try:
            skip = False
            instruction_index = 1
            while True:
                if self._errored:
                    return Status.RUNTIME_ERROR
                # self._print(f"{'Executing' if not skip else 'skipping'} instruction #{instruction_index}")
                # frame.chunk.dissassemble_line(frame.ip.at(), "'", self._print)
                # self._print(f"frame stack = {frame.stack}; full stack = {self._stack}")
                code = _read_byte()
                if skip:
                    if code in {OpCodes.DEF_GLOBAL.value, OpCodes.GET_GLOBAL.value, OpCodes.SET_GLOBAL.value,
                                OpCodes.GET_LOCAL.value, OpCodes.SET_LOCAL.value, OpCodes.LOOP.value,
                                OpCodes.FALSEY_JUMP.value, OpCodes.ALWAYS_JUMP.value, OpCodes.CALL.value}:
                        _read_byte()
                    if code == OpCodes.LOOP.value:
                        skip = False
                        _read_byte()  # skip the pop
                        # self._print(f"Executing instruction #{instruction_index}")
                        # frame.chunk.dissassemble_line(frame.ip.at(), "'", self._print)
                        # self._print(f"frame stack = {frame.stack}; full stack = {self._stack}")
                        code = _read_byte()
                    else:
                        continue
                instruction_index += 1
                if code == OpCodes.RETURN.value:
                    result = self.pop()
                    self._count -= 1
                    self._frames.pop()
                    if self._count == 0:
                        self.pop()
                        return Status.OK
                    self._stack.top = frame.stack.bottom
                    self.push(result)
                    frame = self._frames[self._count - 1]
                    if iter_obj is not None:
                        self.pop()
                        skip = True
                elif code == OpCodes.YIELD.value:
                    result = self.pop()
                    self._count -= 1
                    self._frames.pop()
                    if self._count == 0:
                        raise ValueError("Somehow got no frames...")
                    self._stack.top = frame.stack.bottom
                    self.push(result)
                    iter_obj.raw.stack = frame.stack
                    iter_obj.raw.ip = frame.ip
                    frame = self._frames[self._count - 1]
                elif code == OpCodes.CONSTANT.value:
                    self.push(_read_constant())
                elif code == OpCodes.NEGATE.value:
                    # noinspection PyTypeChecker
                    _unary(type(self.stack.peek()).negate)
                elif code == OpCodes.INVERT.value:
                    # noinspection PyTypeChecker
                    _unary(type(self.stack.peek()).invert)
                elif code == OpCodes.POWER.value:
                    # noinspection PyTypeChecker
                    if (result := _binary("exp", type(self.stack.peek(1)).power,
                                          type(self.stack.peek()).r_power)) is not None:
                        return result
                elif code == OpCodes.ADD.value:
                    # noinspection PyTypeChecker
                    if (result := _binary("add", type(self.stack.peek(1)).add,
                                          type(self.stack.peek()).r_add)) is not None:
                        return result
                elif code == OpCodes.SUB.value:
                    # noinspection PyTypeChecker
                    if (result := _binary("subtract", type(self.stack.peek(1)).sub,
                                          type(self.stack.peek()).r_sub)) is not None:
                        return result
                elif code == OpCodes.MIX.value:
                    # noinspection PyTypeChecker
                    if (result := _binary("mix", type(self.stack.peek(1)).mix,
                                          type(self.stack.peek()).r_mix)) is not None:
                        return result
                elif code == OpCodes.EQUAL.value:
                    # noinspection PyTypeChecker
                    if (result := _binary("equality", type(self.stack.peek(1)).equal,
                                          type(self.stack.peek()).equal)) is not None:
                        return result
                elif code == OpCodes.LESS.value:
                    # noinspection PyTypeChecker
                    if (result := _binary("less than", type(self.stack.peek(1)).less,
                                          type(self.stack.peek()).more)) is not None:
                        return result
                elif code == OpCodes.MORE.value:
                    # noinspection PyTypeChecker
                    if (result := _binary("greater than", type(self.stack.peek(1)).more,
                                          type(self.stack.peek()).less)) is not None:
                        return result
                elif code == OpCodes.TRUE.value:
                    self.push(vals.Bool(True))
                elif code == OpCodes.FALSE.value:
                    self.push(vals.Bool(False))
                elif code == OpCodes.NULL.value:
                    self.push(vals.Nil())
                elif code == OpCodes.POP.value:
                    self.pop()
                elif code == OpCodes.PRINT.value:
                    self._print(str(self.stack.peek()))
                elif code == OpCodes.DEF_GLOBAL.value:
                    name = _read_constant(vals.String)
                    self._globals[name] = self.pop()
                elif code == OpCodes.GET_GLOBAL.value:
                    name = _read_constant(vals.String)
                    if (value := self._globals.get(name)) is None:
                        return self._error(f"Undefined variable {name}")
                    self.push(value)
                elif code == OpCodes.SET_GLOBAL.value:
                    name = _read_constant(vals.String)
                    if name not in self._globals:
                        return self._error(f"Undefined variable {name}")
                    self._globals[name] = self.stack.peek()
                    if self._var is not None:
                        self._var(name.raw, self.stack.peek())
                elif code == OpCodes.GET_LOCAL.value:
                    i = _read_byte()
                    self.push(frame.stack[i])
                elif code == OpCodes.SET_LOCAL.value:
                    frame.stack[_read_byte()] = self.stack.peek()
                elif code == OpCodes.LOOP.value:
                    frame.ip.jump(-_read_byte())
                    if iter_obj is not None:
                        self.push(iter_obj)
                elif code == OpCodes.FALSEY_JUMP.value:
                    if not self.stack.peek().is_true():
                        frame.ip.jump(_read_byte())
                    else:
                        frame.ip.jump(1)
                elif code == OpCodes.ALWAYS_JUMP.value:
                    frame.ip.jump(_read_byte())
                elif code == OpCodes.CALL.value:
                    count = _read_byte()
                    obj = self.stack.peek(count)
                    if not obj.call(self, count):
                        return self._error(f"{obj.NAME!r} objects aren't callable.")
                    frame = self._frames[self._count - 1]
                elif code == OpCodes.SLEEP.value:
                    for_ = self.pop()
                    if not isinstance(for_, vals.Number):
                        return self._error(f"{for_!r} is not a number.")
                    time.sleep(for_.raw)
                elif code == OpCodes.ADVANCE.value:
                    obj = self.pop()
                    if isinstance(obj, objs.Iterator):
                        iter_obj = obj
                        self.new_frame(obj.raw, obj.raw.stack)
                        frame = self._frames[self._count - 1]
                        if obj.raw.ip is not None:
                            frame.ip = obj.raw.ip
                    elif isinstance(obj, objs.NativeIterator):
                        iter_obj = obj
                        try:
                            self.push(next(obj.raw))
                            iter_count += 1
                        except StopIteration:
                            for _ in range(iter_count):
                                self.pop()
                            iter_count = 0
                            skip = True
                            iter_obj = None
                    else:
                        return self._error("Can only iterate over iterables")
                elif code == OpCodes.ENUM.value:
                    name = _read_constant(vals.String)
                    self.push(objs.Enum(name))
                elif code == OpCodes.GET_FIELD.value:
                    name = _read_constant(vals.String)
                    inst = self.stack.peek()
                    if not isinstance(inst, (objs.Enum, objs.NativeEnum)):
                        return self._error("Can only read properties from enumerations")
                    try:
                        num = inst.get(name)
                    except (ValueError, KeyError):
                        return self._error(f"{inst} has no property {name}")
                    self.pop()
                    self.push(num)
                elif code == OpCodes.DEF_FIELD.value:
                    name = _read_constant(vals.String)
                    inst = self.stack.peek()
                    if not isinstance(inst, objs.Enum):
                        raise RuntimeError("Something Failed")
                    inst.set(name)
                elif code == OpCodes.DEF_ELEM.value:
                    collection = _read_constant(vals.Array)
                    value = self.stack.pop()
                    collection.add_elem(value)
                else:
                    self._unknown(code)
        except Exception as e:
            return self._error(f"Py-Error '{e!r}'")

    def _error(self, msg: str) -> Status:
        traceback = "; ".join(f"[line {frame.chunk.line(frame.ip.at() - 1)} in {frame.name}]" for frame in self._frames)
        self._print(f"RunTimeError on {traceback}: {msg}")
        self._errored = True
        return Status.RUNTIME_ERROR

    def error(self, msg: str) -> bool:
        self._error(msg)
        return True
