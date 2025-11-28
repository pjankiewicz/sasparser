"""LIBNAME and OPTIONS statement handlers."""

from __future__ import annotations
from . import register
from .base import BaseHandler, ParseContext
from ..core.tokens import Token, TokenType
from ..ast.statements import LibnameStatement, OptionsStatement, TitleStatement


@register
class LibnameHandler(BaseHandler):
    """Handler for LIBNAME statements."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.LIBNAME}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return tokens[pos].type == TokenType.LIBNAME

    def parse(self, ctx: ParseContext) -> tuple[LibnameStatement, int]:
        """Parse LIBNAME name [engine] 'path' [options];"""
        pos = ctx.pos + 1  # Skip LIBNAME

        name = ""
        path = ""
        engine: str | None = None
        options: dict[str, str] = {}

        # Get library name
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
            name = ctx.tokens[pos].value
            pos += 1

        # Check for CLEAR keyword (LIBNAME mylib CLEAR;)
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
            if ctx.tokens[pos].value.upper() == "CLEAR":
                pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
                    pos += 1
                ctx.libraries[name] = ""
                return LibnameStatement(name=name, path="", engine="CLEAR"), pos

        # Check for engine (optional identifier before path)
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
            # Could be engine or an option
            potential_engine = ctx.tokens[pos].value.upper()
            if potential_engine in {"ORACLE", "ODBC", "POSTGRES", "MYSQL", "XLSX", "CSV", "JSON"}:
                engine = potential_engine
                pos += 1

        # Get path (string literal)
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.STRING:
            path = ctx.tokens[pos].value
            # Remove surrounding quotes
            if (path.startswith("'") and path.endswith("'")) or (
                path.startswith('"') and path.endswith('"')
            ):
                path = path[1:-1]
            pos += 1

        # Parse remaining options until semicolon
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            tok = ctx.tokens[pos]
            if tok.type == TokenType.IDENTIFIER:
                opt_name = tok.value.upper()
                opt_value = ""
                pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                    pos += 1
                    # Get option value
                    if pos < len(ctx.tokens):
                        if ctx.tokens[pos].type == TokenType.STRING:
                            opt_value = ctx.tokens[pos].value
                            if (opt_value.startswith("'") and opt_value.endswith("'")) or (
                                opt_value.startswith('"') and opt_value.endswith('"')
                            ):
                                opt_value = opt_value[1:-1]
                        else:
                            opt_value = ctx.tokens[pos].value
                        pos += 1
                options[opt_name] = opt_value
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        # Store in libraries
        ctx.libraries[name] = path

        return LibnameStatement(name=name, path=path, engine=engine, options=options), pos


@register
class OptionsHandler(BaseHandler):
    """Handler for OPTIONS statements."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.OPTIONS}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return tokens[pos].type == TokenType.OPTIONS

    def parse(self, ctx: ParseContext) -> tuple[OptionsStatement, int]:
        """Parse OPTIONS opt1 opt2=val2 ...;"""
        pos = ctx.pos + 1  # Skip OPTIONS

        options: dict[str, str | None] = {}

        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            tok = ctx.tokens[pos]
            if tok.type == TokenType.IDENTIFIER:
                opt_name = tok.value.upper()
                opt_value: str | None = None
                pos += 1

                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                    pos += 1
                    if pos < len(ctx.tokens):
                        if ctx.tokens[pos].type == TokenType.STRING:
                            opt_value = ctx.tokens[pos].value
                            if (opt_value.startswith("'") and opt_value.endswith("'")) or (
                                opt_value.startswith('"') and opt_value.endswith('"')
                            ):
                                opt_value = opt_value[1:-1]
                        else:
                            opt_value = ctx.tokens[pos].value
                        pos += 1

                options[opt_name] = opt_value
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        return OptionsStatement(options=options), pos


@register
class TitleHandler(BaseHandler):
    """Handler for TITLE and FOOTNOTE statements."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.TITLE, TokenType.FOOTNOTE}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return tokens[pos].type in {TokenType.TITLE, TokenType.FOOTNOTE}

    def parse(self, ctx: ParseContext) -> tuple[TitleStatement, int]:
        """Parse TITLE[n] 'text'; or FOOTNOTE[n] 'text';"""
        pos = ctx.pos
        is_footnote = ctx.tokens[pos].type == TokenType.FOOTNOTE
        pos += 1

        number: int | None = None
        text = ""

        # Check for title number (TITLE2, TITLE3, etc.)
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.NUMBER:
            try:
                number = int(ctx.tokens[pos].value)
            except ValueError:
                pass
            pos += 1

        # Get title text (string literal)
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.STRING:
            text = ctx.tokens[pos].value
            if (text.startswith("'") and text.endswith("'")) or (
                text.startswith('"') and text.endswith('"')
            ):
                text = text[1:-1]
            pos += 1

        # Skip to semicolon
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            pos += 1
        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        return TitleStatement(text=text, number=number, is_footnote=is_footnote), pos
