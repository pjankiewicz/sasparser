"""Lexer/Tokenizer for SAS source code."""

from typing import Iterator
from .tokens import Token, TokenType
from .errors import LexerError


class Lexer:
    """Tokenizes SAS source code into a stream of tokens."""

    KEYWORDS: dict[str, TokenType] = {
        "data": TokenType.DATA, "set": TokenType.SET, "merge": TokenType.MERGE,
        "by": TokenType.BY, "run": TokenType.RUN, "quit": TokenType.QUIT,
        "proc": TokenType.PROC, "libname": TokenType.LIBNAME,
        "sql": TokenType.SQL, "select": TokenType.SELECT, "from": TokenType.FROM,
        "where": TokenType.WHERE, "join": TokenType.JOIN, "left": TokenType.LEFT,
        "right": TokenType.RIGHT, "inner": TokenType.INNER, "outer": TokenType.OUTER,
        "full": TokenType.FULL, "cross": TokenType.CROSS, "on": TokenType.ON,
        "as": TokenType.AS, "create": TokenType.CREATE, "table": TokenType.TABLE,
        "view": TokenType.VIEW, "insert": TokenType.INSERT, "into": TokenType.INTO,
        "values": TokenType.VALUES, "update": TokenType.UPDATE, "delete": TokenType.DELETE,
        "drop": TokenType.DROP_KW, "group": TokenType.GROUP, "order": TokenType.ORDER,
        "having": TokenType.HAVING, "distinct": TokenType.DISTINCT,
        "asc": TokenType.ASC, "desc": TokenType.DESC, "descending": TokenType.DESCENDING,
        "union": TokenType.UNION, "all": TokenType.ALL, "exists": TokenType.EXISTS,
        "between": TokenType.BETWEEN, "like": TokenType.LIKE, "is": TokenType.IS,
        "null": TokenType.NULL, "case": TokenType.CASE, "when": TokenType.WHEN,
        "if": TokenType.IF, "then": TokenType.THEN, "else": TokenType.ELSE,
        "do": TokenType.DO, "end": TokenType.END, "output": TokenType.OUTPUT,
        "keep": TokenType.KEEP, "retain": TokenType.RETAIN, "to": TokenType.TO,
        "length": TokenType.LENGTH, "format": TokenType.FORMAT,
        "informat": TokenType.INFORMAT, "array": TokenType.ARRAY, "input": TokenType.INPUT,
        "put": TokenType.PUT, "label": TokenType.LABEL, "attrib": TokenType.ATTRIB,
        "rename": TokenType.RENAME,
        "sort": TokenType.SORT, "means": TokenType.MEANS, "summary": TokenType.SUMMARY,
        "freq": TokenType.FREQ, "print": TokenType.PRINT, "contents": TokenType.CONTENTS,
        "var": TokenType.VAR, "class": TokenType.CLASS, "tables": TokenType.TABLES,
        "nodupkey": TokenType.NODUPKEY, "noduprec": TokenType.NODUPREC,
        "out": TokenType.OUT, "obs": TokenType.OBS,
        "options": TokenType.OPTIONS, "title": TokenType.TITLE, "footnote": TokenType.FOOTNOTE,
        "and": TokenType.AND, "or": TokenType.OR, "not": TokenType.NOT, "in": TokenType.IN,
        "eq": TokenType.EQ, "ne": TokenType.NE, "lt": TokenType.LT,
        "gt": TokenType.GT, "le": TokenType.LE, "ge": TokenType.GE,
    }

    SYMBOLS: dict[str, TokenType] = {
        ";": TokenType.SEMICOLON, ",": TokenType.COMMA, ".": TokenType.DOT,
        "(": TokenType.LPAREN, ")": TokenType.RPAREN,
        "{": TokenType.LBRACE, "}": TokenType.RBRACE,
        "[": TokenType.LBRACKET, "]": TokenType.RBRACKET,
        "+": TokenType.PLUS, "-": TokenType.MINUS, "*": TokenType.STAR,
        "/": TokenType.SLASH, "=": TokenType.EQUALS, ":": TokenType.COLON,
        "$": TokenType.DOLLAR, "@": TokenType.AT, "#": TokenType.HASH,
        "^": TokenType.CARET, "~": TokenType.TILDE, "|": TokenType.PIPE,
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source)

    def tokenize(self) -> list[Token]:
        """Tokenize the entire source and return list of tokens."""
        return list(self._scan())

    def _scan(self) -> Iterator[Token]:
        """Generate tokens from source."""
        while self.pos < self.length:
            if self._skip_whitespace():
                continue
            if self._skip_comment():
                continue
            token = self._next_token()
            if token:
                yield token
        yield Token(TokenType.EOF, "", self.line, self.column)

    def _peek(self, offset: int = 0) -> str:
        """Peek at character at current position + offset."""
        pos = self.pos + offset
        return self.source[pos] if pos < self.length else ""

    def _advance(self, count: int = 1) -> str:
        """Advance position and return consumed characters."""
        result = self.source[self.pos:self.pos + count]
        for ch in result:
            if ch == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        self.pos += count
        return result

    def _skip_whitespace(self) -> bool:
        """Skip whitespace characters. Returns True if any were skipped."""
        if self.pos >= self.length or not self.source[self.pos].isspace():
            return False
        while self.pos < self.length and self.source[self.pos].isspace():
            self._advance()
        return True

    def _skip_comment(self) -> bool:
        """Skip comments. Returns True if a comment was skipped."""
        if self.pos >= self.length:
            return False
        # Block comment /* ... */
        if self.source[self.pos:self.pos + 2] == "/*":
            end = self.source.find("*/", self.pos + 2)
            if end == -1:
                end = self.length
            else:
                end += 2
            while self.pos < end:
                self._advance()
            return True
        # Line comment: * at start of statement (after ; or newline or start)
        if self.source[self.pos] == "*":
            # Check if this is start of line comment
            if self.column == 1 or (self.pos > 0 and self.source[self.pos - 1] in ";\n"):
                end = self.source.find(";", self.pos)
                if end == -1:
                    end = self.length
                else:
                    end += 1
                while self.pos < end:
                    self._advance()
                return True
        return False

    def _next_token(self) -> Token | None:
        """Read the next token."""
        if self.pos >= self.length:
            return None

        ch = self.source[self.pos]
        start_line, start_col = self.line, self.column

        # Macro variable: &var or &&var
        if ch == "&":
            return self._read_macro_var(start_line, start_col)

        # Macro keyword: %let, %macro, etc.
        if ch == "%":
            return self._read_macro_keyword(start_line, start_col)

        # String literal
        if ch in ('"', "'"):
            return self._read_string(start_line, start_col)

        # Number
        if ch.isdigit() or (ch == "." and self._peek(1).isdigit()):
            return self._read_number(start_line, start_col)

        # Identifier or keyword
        if ch.isalpha() or ch == "_":
            return self._read_identifier(start_line, start_col)

        # Multi-character operators
        two_char = self.source[self.pos:self.pos + 2]
        if two_char in ("<=", ">=", "<>", "!=", "^=", "~="):
            self._advance(2)
            if two_char in ("<=", "le"):
                return Token(TokenType.LE, two_char, start_line, start_col)
            if two_char in (">=", "ge"):
                return Token(TokenType.GE, two_char, start_line, start_col)
            return Token(TokenType.NE, two_char, start_line, start_col)

        # Single character operators/symbols
        if ch in self.SYMBOLS:
            self._advance()
            return Token(self.SYMBOLS[ch], ch, start_line, start_col)

        # Comparison operators
        if ch == "<":
            self._advance()
            return Token(TokenType.LT, ch, start_line, start_col)
        if ch == ">":
            self._advance()
            return Token(TokenType.GT, ch, start_line, start_col)

        # Unknown character - skip it
        self._advance()
        return Token(TokenType.UNKNOWN, ch, start_line, start_col)

    def _read_identifier(self, line: int, col: int) -> Token:
        """Read an identifier or keyword."""
        start = self.pos
        while self.pos < self.length:
            ch = self.source[self.pos]
            if ch.isalnum() or ch == "_":
                self._advance()
            else:
                break
        value = self.source[start:self.pos]
        token_type = self.KEYWORDS.get(value.lower(), TokenType.IDENTIFIER)
        return Token(token_type, value, line, col)

    def _read_string(self, line: int, col: int) -> Token:
        """Read a string literal."""
        quote = self.source[self.pos]
        self._advance()  # Skip opening quote
        start = self.pos
        while self.pos < self.length:
            ch = self.source[self.pos]
            if ch == quote:
                if self._peek(1) == quote:  # Escaped quote
                    self._advance(2)
                else:
                    break
            else:
                self._advance()
        value = self.source[start:self.pos]
        if self.pos < self.length:
            self._advance()  # Skip closing quote
        # Check for date/time literals
        suffix = self._peek().lower() if self.pos < self.length else ""
        if suffix == "d":
            self._advance()
            return Token(TokenType.DATE_LITERAL, value, line, col)
        if suffix == "t":
            self._advance()
            return Token(TokenType.TIME_LITERAL, value, line, col)
        return Token(TokenType.STRING, value, line, col)

    def _read_number(self, line: int, col: int) -> Token:
        """Read a numeric literal."""
        start = self.pos
        has_dot = False
        while self.pos < self.length:
            ch = self.source[self.pos]
            if ch.isdigit():
                self._advance()
            elif ch == "." and not has_dot:
                has_dot = True
                self._advance()
            elif ch.lower() == "e" and self.pos > start:
                self._advance()
                if self._peek() in "+-":
                    self._advance()
            else:
                break
        value = self.source[start:self.pos]
        return Token(TokenType.NUMBER, value, line, col)

    def _read_macro_var(self, line: int, col: int) -> Token:
        """Read a macro variable reference (&var or &&var)."""
        start = self.pos
        while self.pos < self.length and self.source[self.pos] == "&":
            self._advance()
        # Read the variable name
        while self.pos < self.length:
            ch = self.source[self.pos]
            if ch.isalnum() or ch == "_":
                self._advance()
            else:
                break
        # Optional trailing dot
        if self.pos < self.length and self.source[self.pos] == ".":
            self._advance()
        value = self.source[start:self.pos]
        return Token(TokenType.MACRO_VAR, value, line, col)

    def _read_macro_keyword(self, line: int, col: int) -> Token:
        """Read a macro keyword (%let, %macro, etc.)."""
        self._advance()  # Skip %
        start = self.pos
        while self.pos < self.length:
            ch = self.source[self.pos]
            if ch.isalnum() or ch == "_":
                self._advance()
            else:
                break
        name = self.source[start:self.pos].lower()
        value = "%" + self.source[start:self.pos]

        macro_keywords = {
            "let": TokenType.PERCENT_LET,
            "macro": TokenType.PERCENT_MACRO,
            "mend": TokenType.PERCENT_MEND,
            "if": TokenType.PERCENT_IF,
            "then": TokenType.PERCENT_THEN,
            "else": TokenType.PERCENT_ELSE,
            "do": TokenType.PERCENT_DO,
            "end": TokenType.PERCENT_END,
        }
        token_type = macro_keywords.get(name, TokenType.MACRO_CALL)
        return Token(token_type, value, line, col)
