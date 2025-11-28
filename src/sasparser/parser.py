"""Main SAS parser module."""

from __future__ import annotations
from dataclasses import dataclass, field
from .core.lexer import Lexer
from .core.tokens import Token
from .core.errors import ParseError
from .ast.base import ASTNode
from .handlers import HandlerRegistry
from .handlers.base import ParseContext


@dataclass
class ParseResult:
    """Result of parsing SAS code.

    Contains the AST nodes, any errors encountered, and metadata
    collected during parsing.
    """

    statements: list[ASTNode] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)
    tokens: list[Token] = field(default_factory=list)
    macro_vars: dict[str, str] = field(default_factory=dict)
    libraries: dict[str, str] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        """Check if there were any parsing errors."""
        return len(self.errors) > 0

    @property
    def is_valid(self) -> bool:
        """Check if parsing completed without errors."""
        return not self.has_errors


class SASParser:
    """Main parser for SAS code.

    Converts SAS source code into an Abstract Syntax Tree (AST)
    that can be analyzed with visitors or processed programmatically.

    Example:
        parser = SASParser()
        result = parser.parse(sas_code)
        for stmt in result.statements:
            print(stmt)
    """

    def __init__(self, *, recover_from_errors: bool = True) -> None:
        """Initialize parser.

        Args:
            recover_from_errors: If True, attempt to continue parsing
                after encountering errors. If False, raise on first error.
        """
        self.recover_from_errors = recover_from_errors

    def parse(self, source: str) -> ParseResult:
        """Parse SAS source code.

        Args:
            source: SAS source code to parse.

        Returns:
            ParseResult containing AST statements and any errors.
        """
        result = ParseResult()

        # Tokenize
        lexer = Lexer(source)
        try:
            result.tokens = lexer.tokenize()
        except ParseError as e:
            result.errors.append(e)
            if not self.recover_from_errors:
                return result

        if not result.tokens:
            return result

        # Parse
        result.macro_vars = {}
        result.libraries = {}
        pos = 0

        while pos < len(result.tokens):
            try:
                stmt, pos = self._parse_statement(
                    result.tokens, pos, result.macro_vars, result.libraries
                )
                if stmt:
                    result.statements.append(stmt)
            except ParseError as e:
                result.errors.append(e)
                if not self.recover_from_errors:
                    break
                # Skip to next semicolon to recover
                pos = self._skip_to_semicolon(result.tokens, pos)

        return result

    def parse_file(self, filepath: str) -> ParseResult:
        """Parse a SAS file.

        Args:
            filepath: Path to the SAS file.

        Returns:
            ParseResult containing AST statements and any errors.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        return self.parse(source)

    def _parse_statement(
        self,
        tokens: list[Token],
        pos: int,
        macro_vars: dict[str, str],
        libraries: dict[str, str],
    ) -> tuple[ASTNode | None, int]:
        """Parse a single statement starting at pos."""
        if pos >= len(tokens):
            return None, pos

        ctx = ParseContext(
            tokens=tokens,
            pos=pos,
            macro_vars=macro_vars,
            libraries=libraries,
        )

        # Find appropriate handler
        handler = HandlerRegistry.find_handler(tokens, pos)
        if handler:
            return handler.parse(ctx)

        # No handler found - skip to semicolon
        return None, self._skip_to_semicolon(tokens, pos)

    def _skip_to_semicolon(self, tokens: list[Token], pos: int) -> int:
        """Skip tokens until after the next semicolon."""
        from .core.tokens import TokenType

        while pos < len(tokens) and tokens[pos].type != TokenType.SEMICOLON:
            pos += 1
        if pos < len(tokens):
            pos += 1  # Skip the semicolon
        return pos


def parse(source: str) -> ParseResult:
    """Convenience function to parse SAS code.

    Args:
        source: SAS source code to parse.

    Returns:
        ParseResult containing AST statements and any errors.

    Example:
        result = sasparser.parse("DATA out; SET in; RUN;")
        print(result.statements)
    """
    return SASParser().parse(source)


def parse_file(filepath: str) -> ParseResult:
    """Convenience function to parse a SAS file.

    Args:
        filepath: Path to the SAS file.

    Returns:
        ParseResult containing AST statements and any errors.
    """
    return SASParser().parse_file(filepath)
