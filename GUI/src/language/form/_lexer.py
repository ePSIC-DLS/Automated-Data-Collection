import typing
from .. import grammar


class Lexer:
    """
    Class to represent the transformation from a source string to a series of tokens.

    Attributes
    ----------
    _stream: str
        The raw source string.
    _pointer: Iterator[str]
        An iterator to the string, allowing for character by character extraction.
    _i: int
        The character position within the string. This is an absolute position.
    _row: int
        The row (line) number of the current token. Increments with every newline character.
    _col: int
        The column number of the current token. Reset every newline character.
    _length: int
        The length of the source string.
    """

    @property
    def _curr(self) -> str:
        self._i += 1
        self._col += 1
        try:
            return next(self._pointer)
        except StopIteration:
            return ""

    @property
    def finished(self) -> bool:
        """
        Determine whether the lexer has finished scanning.

        Returns
        -------
        bool
            Whether the index has reached the length.
        """
        return self._i >= self._length

    def __init__(self, code: str):
        self._stream = code
        self._pointer = iter(code)
        self._i, self._row, self._col = 0, 1, -1
        self._length = len(code)

    def run(self) -> typing.Iterator[grammar.Token]:
        """
        Kicks off the lexer, telling it to begin scanning.

        As this is an iterator, it allows for token-by-token extraction by repeatedly calling `next`.

        Yields
        ------
        Token
            The first matching token from the current characters in the string.
        """
        while not self.finished:
            token = self._scan()
            yield token
            if token.token_type == grammar.TokenType.EOF:
                break
        else:
            yield grammar.Token.eof(self._row)

    def _scan(self) -> grammar.Token:
        result = self._skip_space()
        if result is not None:
            return result
        char = self._curr
        if char.isalpha() or char == "_":
            return self._word(char)
        elif char.isdigit():
            return self._num(char)
        elif grammar.SYMBOLS_TYPE.get(char) == grammar.TokenType.STRING:
            return self._string(grammar.TYPE_SYMBOLS[grammar.TokenType.STRING])
        elif grammar.SYMBOLS_TYPE.get(char) == grammar.TokenType.PATH:
            return self._path()
        elif grammar.SYMBOLS_TYPE.get(char + self._peek().lower()) == grammar.TokenType.HEX:
            self._advance(1)
            return self._base(grammar.HexToken, *"0123456789abcdef")
        elif grammar.SYMBOLS_TYPE.get(char + self._peek().lower()) == grammar.TokenType.BIN:
            self._advance(1)
            return self._base(grammar.BinToken, "0", "1")
        valid_strs = []
        next_char = self._peek()
        if next_char != "":
            valid_strs.append((f"{char}{next_char}", 1))
        next_next_char = self._peek(2)
        if next_next_char != "":
            valid_strs.append((f"{char}{next_char}{next_next_char}", 2))
        for string, skip in valid_strs[::-1]:
            if string in grammar.SYMBOLS_TYPE:
                self._advance(skip)
                return grammar.Token.from_symbol(string, self._row, self._col)
        return grammar.Token.from_symbol(char, self._row, self._col)

    def _skip_space(self) -> typing.Optional[grammar.Token]:
        token: typing.Optional[grammar.Token] = None
        while True:
            char = self._peek()
            if char == " ":
                self._advance(1)
            elif char == "\n":
                self._advance(1)
                token = grammar.Token.from_symbol(char, self._row, self._col)
                self._row += 1
                self._col = 0
            elif char == "\t":
                self._advance(4)
            else:
                return token

    def _peek(self, by=1) -> str:
        i = self._i + by - 1
        if i >= self._length:
            return ""
        return self._stream[i]

    def _advance(self, by: int):
        self._i += by
        self._col += by
        for _ in range(by):
            next(self._pointer)

    def _word(self, start: str) -> typing.Union[grammar.IdentifierToken, grammar.KeywordToken]:
        letters = [start]
        char = self._peek()
        while not self.finished and (char.isalnum() or char == "_"):
            letters.append(self._curr)
            char = self._peek()
        word = "".join(letters)
        if word in grammar.KEYWORDS_TYPE:
            token = grammar.KeywordToken(word, self._row, self._col)
        else:
            token = grammar.IdentifierToken(word, self._row, self._col)
        return token

    def _num(self, start: str) -> grammar.NumToken:
        digits = [start]
        digit = self._peek()
        dot = False
        while not self.finished and (digit.isdigit() or (digit == "." and not dot)):
            if digit == ".":
                dot = True
            digits.append(self._curr)
            digit = self._peek()
        return grammar.NumToken(float("".join(digits)), self._row, self._col)

    def _base(self, __init__: typing.Callable[[str, int, int], grammar.BaseNumToken],
              *allowed: str) -> typing.Union[grammar.BaseNumToken, grammar.ErrorToken]:
        allowed = set(x.lower() for x in allowed)
        digits = []
        digit = self._peek()
        while not self.finished and (digit.lower() in allowed):
            digits.append(self._curr)
            digit = self._peek()
        if not digits:
            return grammar.ErrorToken("Expected numerical literal", self._row, self._col)
        return __init__("".join(digits), self._row, self._col)

    def _string(self, match: str) -> typing.Union[grammar.StringToken, grammar.ErrorToken]:
        letters = []
        char = self._peek()
        found_match = False
        while not self.finished and char != match:
            letters.append(self._curr)
            char = self._peek()
        if char == match:
            found_match = True
        if self.finished or not found_match:
            return grammar.ErrorToken("Unterminated string", self._row, self._col)
        elif char == match:
            self._advance(1)
        return grammar.StringToken("".join(letters), self._row, self._col)

    def _path(self) -> grammar.PathToken:
        str_token = self._string(grammar.TYPE_SYMBOLS[grammar.TokenType.PATH])
        return grammar.PathToken(str_token.raw, self._row, self._col)
