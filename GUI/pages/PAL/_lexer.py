import typing
from . import grammar
from ._tokens import validators

Match = typing.TypeVar("Match", bound=grammar.MatchedToken)


class Lexer:
    """
    Class to 'tokenise' PAL source code from a string input.

    PAL source code comes from files with a .GUIAS extension.

    :var str _stream: The source code itself.
    :var Iterator[str] _pointer: A generator from the source code to allow letter-by-letter yielding.
    :var int _i: The current total position in the source code.
    :var int _row: The current line number.
    :var int _col: The current column number.
    :var int _length: The total length of the source code.
    :var bool _accessing: Whether an ACCESS token was parsed.
    """

    @property
    def _curr(self) -> str:
        self._i += 1
        self._col += 1
        return next(self._pointer)

    @property
    def finished(self) -> bool:
        """
        Public access to whether the Lexer has finished tokenising.

        :return: If the current position is larger than (or equal to) the length of the source code.
        """
        return self._i >= self._length

    def __init__(self, code: str):
        self._stream = code
        self._pointer = iter(code)
        self._i, self._row, self._col = 0, 1, -1
        self._length = len(code)
        self._accessing = False

    def run(self) -> typing.Iterator[grammar.Token]:
        """
        Construct an iterator for the tokens generated from the source code.

        :return: A generator yielding each token generated. The final one will always be an EOF token.
        """
        while not self.finished:
            tok = self._scan()
            self._accessing = tok.token_type == grammar.TokenType.ACCESS
            if tok.token_type == grammar.TokenType.EOF:
                break
            yield tok
        yield grammar.Token.eof(self._row)

    def _skip_space(self):
        while True:
            char = self._peek()
            if char == " ":
                self._advance(1)
            elif char == "\n":
                self._advance(1)
                self._row += 1
                self._col = 0
            else:
                return

    def _peek(self, by=1) -> str:
        by -= 1
        if self._i + by >= self._length:
            return ""
        return self._stream[self._i + by]

    def _advance(self, by: int):
        self._i += by
        self._col += by
        for _ in range(by):
            next(self._pointer)

    def _scan(self) -> grammar.Token:
        self._skip_space()
        if self.finished:
            return grammar.Token.eof(self._row)
        char = self._curr
        if char.isalpha():
            return self._build_word(char)
        elif char.isdigit():
            return self._build_number(char)
        elif grammar.SYMBOLS_TYPE.get(char) == grammar.TokenType.FILE:
            return self._build_path(char)
        elif grammar.SYMBOLS_TYPE.get(char) == grammar.TokenType.ENUM:
            return self._build_member(char)
        elif grammar.SYMBOLS_TYPE.get(char) == grammar.TokenType.STR:
            return self._build_str(char)
        return grammar.Token.from_symbol(char, self._row, self._col)

    def _build_word(self, start: str) -> typing.Union[grammar.IdentifierToken, grammar.KeywordToken]:
        letters = [start]
        char = self._peek()
        while not self.finished and (char.isalnum() or char == "_"):
            letters.append(self._curr)
            char = self._peek()
        word = "".join(letters)
        if word in grammar.KEYWORDS_TYPE:
            return grammar.KeywordToken(word, self._row, self._col)
        return grammar.IdentifierToken(word, self._row, self._col, self._accessing)

    def _build_number(self, start: str) -> grammar.NumberToken:
        digits = [start]
        digit = self._peek()
        dot = False
        while not self.finished and (digit.isdigit() or (digit == "." and not dot)):
            if digit == ".":
                dot = True
            digits.append(self._curr)
            digit = self._peek()
        return grammar.NumberToken(float("".join(digits)), self._row, self._col)

    def _build_path(self, speech: str) -> typing.Union[grammar.FileToken, grammar.ErrorToken]:
        return self._build_match(speech, "file path", grammar.FileToken,
                                 lambda char: (char.isalnum() or char in validators.file_path_chars))

    def _build_member(self, quote: str) -> typing.Union[grammar.EnumToken, grammar.ErrorToken]:
        return self._build_match(quote, "enum member", grammar.EnumToken,
                                 lambda char: (char.isalnum() or char == "_"))

    def _build_str(self, start: str) -> typing.Union[grammar.StringToken, grammar.ErrorToken]:
        return self._build_match(start, "string", grammar.StringToken,
                                 lambda char: True)

    def _build_match(self, match: str, context: str, token: typing.Type[Match], valids: typing.Callable[[str], bool]) \
            -> typing.Union[Match, grammar.ErrorToken]:
        path = []
        char = self._peek()
        found_match = False
        while not self.finished and char != match and valids(char):
            path.append(self._curr)
            char = self._peek()
        if char == match:
            found_match = True
        if self.finished or not found_match:
            return grammar.ErrorToken(f"Unterminated {context}", self._row, self._col)
        elif char == match:
            self._advance(1)
        return token("".join(path), self._row, self._col)
