"""Error classes for the SAS parser."""


class SASParserError(Exception):
    """Base exception for all SAS parser errors."""

    def __init__(self, message: str, line: int | None = None, column: int | None = None):
        self.line = line
        self.column = column
        if line is not None and column is not None:
            message = f"{message} at line {line}, column {column}"
        elif line is not None:
            message = f"{message} at line {line}"
        super().__init__(message)


class LexerError(SASParserError):
    """Error during tokenization."""

    pass


class ParseError(SASParserError):
    """Error during parsing."""

    pass


class UnexpectedTokenError(ParseError):
    """Unexpected token encountered during parsing."""

    def __init__(
        self,
        expected: str,
        got: str,
        line: int | None = None,
        column: int | None = None,
    ):
        message = f"Expected {expected}, got {got}"
        super().__init__(message, line, column)
        self.expected = expected
        self.got = got
