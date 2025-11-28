"""Token types and Token dataclass for SAS lexer."""

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """All token types recognized by the SAS lexer."""

    # Core keywords
    DATA = auto()
    SET = auto()
    MERGE = auto()
    BY = auto()
    RUN = auto()
    QUIT = auto()
    PROC = auto()
    LIBNAME = auto()

    # SQL keywords
    SQL = auto()
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    JOIN = auto()
    LEFT = auto()
    RIGHT = auto()
    INNER = auto()
    OUTER = auto()
    FULL = auto()
    CROSS = auto()
    ON = auto()
    AS = auto()
    CREATE = auto()
    TABLE = auto()
    VIEW = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    UPDATE = auto()
    DELETE = auto()
    DROP = auto()
    GROUP = auto()
    ORDER = auto()
    HAVING = auto()
    DISTINCT = auto()
    ASC = auto()
    DESC = auto()
    UNION = auto()
    ALL = auto()
    EXISTS = auto()
    BETWEEN = auto()
    LIKE = auto()
    IS = auto()
    NULL = auto()
    CASE = auto()
    WHEN = auto()
    ELSE_KW = auto()
    DESCENDING = auto()

    # DATA step keywords
    IF = auto()
    THEN = auto()
    ELSE = auto()
    DO = auto()
    END = auto()
    OUTPUT = auto()
    KEEP = auto()
    DROP_KW = auto()
    RETAIN = auto()
    LENGTH = auto()
    FORMAT = auto()
    INFORMAT = auto()
    ARRAY = auto()
    INPUT = auto()
    PUT = auto()
    LABEL = auto()
    ATTRIB = auto()
    RENAME = auto()
    TO = auto()

    # PROC keywords
    SORT = auto()
    MEANS = auto()
    SUMMARY = auto()
    FREQ = auto()
    PRINT = auto()
    CONTENTS = auto()
    VAR = auto()
    CLASS = auto()
    TABLES = auto()
    NODUPKEY = auto()
    NODUPREC = auto()
    OUT = auto()
    OBS = auto()

    # Global statements
    OPTIONS = auto()
    TITLE = auto()
    FOOTNOTE = auto()

    # Macro tokens
    MACRO_VAR = auto()
    PERCENT_LET = auto()
    PERCENT_MACRO = auto()
    PERCENT_MEND = auto()
    PERCENT_IF = auto()
    PERCENT_THEN = auto()
    PERCENT_ELSE = auto()
    PERCENT_DO = auto()
    PERCENT_END = auto()
    MACRO_CALL = auto()

    # Identifiers and literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    DATE_LITERAL = auto()
    TIME_LITERAL = auto()
    DATETIME_LITERAL = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQUALS = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    EQ = auto()
    CARET = auto()
    TILDE = auto()
    PIPE = auto()
    AMPERSAND = auto()

    # Delimiters
    DOT = auto()
    SEMICOLON = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COLON = auto()
    DOLLAR = auto()
    AT = auto()
    HASH = auto()

    # Special
    EOF = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class Token:
    """A token produced by the lexer."""

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"
