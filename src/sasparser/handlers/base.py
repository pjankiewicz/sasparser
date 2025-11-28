"""Base handler class and shared utilities."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..core.tokens import Token, TokenType
from ..core.errors import ParseError

if TYPE_CHECKING:
    from ..ast.base import ASTNode, TableReference, FieldReference


@dataclass
class ParseContext:
    """Shared context for all handlers during parsing."""

    tokens: list[Token]
    pos: int = 0
    macro_vars: dict[str, str] = field(default_factory=dict)
    libraries: dict[str, str] = field(default_factory=dict)


class BaseHandler(ABC):
    """Base class for SAS construct handlers."""

    @staticmethod
    @abstractmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        """Check if this handler can process tokens at position."""
        pass

    @staticmethod
    @abstractmethod
    def trigger_tokens() -> set[TokenType]:
        """Return token types that might trigger this handler."""
        pass

    @abstractmethod
    def parse(self, ctx: ParseContext) -> tuple[ASTNode, int]:
        """Parse the construct and return (AST node, new position)."""
        pass

    # === Helper Methods ===

    def _current(self, ctx: ParseContext) -> Token | None:
        """Get current token."""
        if ctx.pos < len(ctx.tokens):
            return ctx.tokens[ctx.pos]
        return None

    def _peek(self, ctx: ParseContext, offset: int = 1) -> Token | None:
        """Peek at token at offset from current position."""
        pos = ctx.pos + offset
        if 0 <= pos < len(ctx.tokens):
            return ctx.tokens[pos]
        return None

    def _check(self, ctx: ParseContext, *types: TokenType) -> bool:
        """Check if current token is one of the given types."""
        token = self._current(ctx)
        return token is not None and token.type in types

    def _check_keyword(self, ctx: ParseContext, keyword: str) -> bool:
        """Check if current token is a specific keyword (case-insensitive)."""
        token = self._current(ctx)
        return (
            token is not None
            and token.type == TokenType.IDENTIFIER
            and token.value.lower() == keyword.lower()
        )

    def _consume(self, ctx: ParseContext, expected: TokenType) -> tuple[Token, int]:
        """Consume expected token or raise error."""
        token = self._current(ctx)
        if token is None:
            raise ParseError(f"Unexpected end of input, expected {expected.name}")
        if token.type != expected:
            raise ParseError(
                f"Expected {expected.name}, got {token.type.name}",
                token.line,
                token.column,
            )
        return token, ctx.pos + 1

    def _consume_optional(
        self, ctx: ParseContext, token_type: TokenType
    ) -> tuple[Token | None, int]:
        """Consume token if it matches, otherwise return None."""
        if self._check(ctx, token_type):
            return ctx.tokens[ctx.pos], ctx.pos + 1
        return None, ctx.pos

    def _consume_until(
        self, ctx: ParseContext, stop: set[TokenType], include_stop: bool = False
    ) -> tuple[list[Token], int]:
        """Consume tokens until one of the stop tokens is found."""
        tokens = []
        pos = ctx.pos
        while pos < len(ctx.tokens):
            if ctx.tokens[pos].type in stop:
                if include_stop:
                    tokens.append(ctx.tokens[pos])
                    pos += 1
                break
            tokens.append(ctx.tokens[pos])
            pos += 1
        return tokens, pos

    def _skip_to(self, ctx: ParseContext, *types: TokenType) -> int:
        """Skip tokens until one of the given types is found."""
        pos = ctx.pos
        while pos < len(ctx.tokens) and ctx.tokens[pos].type not in types:
            pos += 1
        return pos

    def _is_identifier_like(self, token: Token) -> bool:
        """Check if token can be used as identifier (including keywords)."""
        # In SAS, keywords can often be used as table/column names
        return token.type == TokenType.IDENTIFIER or token.type.name in {
            "OUTPUT", "INPUT", "DATA", "SET", "MERGE", "BY", "WHERE", "IF", "THEN",
            "ELSE", "DO", "END", "KEEP", "DROP_KW", "RETAIN", "FORMAT", "LABEL",
            "SORT", "MEANS", "FREQ", "PRINT", "SQL", "SELECT", "FROM", "JOIN",
            "LEFT", "RIGHT", "INNER", "FULL", "CREATE", "TABLE", "UPDATE", "DELETE",
            "INSERT", "INTO", "GROUP", "ORDER", "HAVING", "AS", "ON", "AND", "OR",
            "NOT", "IN", "OUT", "VAR", "CLASS", "RUN", "QUIT", "OPTIONS", "TITLE",
            "FOOTNOTE", "LIBNAME", "ALL", "DISTINCT", "UNION", "VIEW", "DROP",
            "NULL", "CASE", "WHEN", "BETWEEN", "LIKE", "IS", "EXISTS", "ASC", "DESC",
            "DESCENDING", "SUMMARY", "CONTENTS", "TABLES", "NODUPKEY", "NODUPREC",
            "OBS", "LENGTH", "INFORMAT", "ARRAY", "PUT", "ATTRIB", "RENAME", "TO",
            "VALUES", "CROSS", "OUTER",
        }

    def _parse_table_ref(self, ctx: ParseContext) -> tuple[TableReference, int]:
        """Parse a table reference (library.dataset or just dataset)."""
        from ..ast.base import TableReference

        token = self._current(ctx)
        if token is None or not self._is_identifier_like(token):
            raise ParseError("Expected table name")

        pos = ctx.pos + 1
        name = token.value
        library = None

        # Check for library.dataset
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.DOT:
            pos += 1
            if pos < len(ctx.tokens) and self._is_identifier_like(ctx.tokens[pos]):
                library = name
                name = ctx.tokens[pos].value
                pos += 1

        return TableReference(dataset=name, library=library), pos

    def _parse_field_ref(self, ctx: ParseContext) -> tuple[FieldReference, int]:
        """Parse a field reference (table.field or just field)."""
        from ..ast.base import FieldReference

        token = self._current(ctx)
        if token is None or not self._is_identifier_like(token):
            raise ParseError("Expected field name")

        pos = ctx.pos + 1
        name = token.value
        table_alias = None

        # Check for table.field
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.DOT:
            pos += 1
            if pos < len(ctx.tokens) and self._is_identifier_like(ctx.tokens[pos]):
                table_alias = name
                name = ctx.tokens[pos].value
                pos += 1

        return FieldReference(name=name, table_alias=table_alias), pos

    def _parse_field_list(
        self, ctx: ParseContext, stop: set[TokenType]
    ) -> tuple[list[FieldReference], int]:
        """Parse a list of field references until stop token."""
        from ..ast.base import FieldReference

        fields: list[FieldReference] = []
        pos = ctx.pos

        while pos < len(ctx.tokens) and ctx.tokens[pos].type not in stop:
            if self._is_identifier_like(ctx.tokens[pos]):
                new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                field_ref, pos = self._parse_field_ref(new_ctx)
                fields.append(field_ref)
            elif ctx.tokens[pos].type == TokenType.COMMA:
                pos += 1
            else:
                pos += 1

        return fields, pos
