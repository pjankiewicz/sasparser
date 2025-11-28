"""Macro handlers (%LET, %MACRO, macro calls)."""

from __future__ import annotations
from . import register
from .base import BaseHandler, ParseContext
from ..core.tokens import Token, TokenType
from ..ast.statements import (
    MacroLetStatement,
    MacroDefStatement,
    MacroCallStatement,
    MacroParameter,
)


@register
class MacroLetHandler(BaseHandler):
    """Handler for %LET statements."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.PERCENT_LET}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return tokens[pos].type == TokenType.PERCENT_LET

    def parse(self, ctx: ParseContext) -> tuple[MacroLetStatement, int]:
        """Parse %LET name = value;"""
        pos = ctx.pos + 1  # Skip %LET

        name = ""
        value = ""

        # Get variable name
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
            name = ctx.tokens[pos].value
            pos += 1

        # Skip =
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
            pos += 1

        # Collect value until semicolon
        value_parts: list[str] = []
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            value_parts.append(ctx.tokens[pos].value)
            pos += 1
        value = " ".join(value_parts)

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        # Store in macro_vars
        ctx.macro_vars[name] = value

        return MacroLetStatement(name=name, value=value), pos


@register
class MacroDefHandler(BaseHandler):
    """Handler for %MACRO definitions."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.PERCENT_MACRO}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return tokens[pos].type == TokenType.PERCENT_MACRO

    def parse(self, ctx: ParseContext) -> tuple[MacroDefStatement, int]:
        """Parse %MACRO name(params); body %MEND;"""
        pos = ctx.pos + 1  # Skip %MACRO

        name = ""
        parameters: list[MacroParameter] = []
        body_tokens: list[str] = []

        # Get macro name
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
            name = ctx.tokens[pos].value
            pos += 1

        # Parse parameters if present
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.LPAREN:
            pos += 1  # Skip (
            parameters, pos = self._parse_parameters(ctx, pos)

        # Skip to semicolon after macro declaration
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            pos += 1
        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        # Collect body until %MEND
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.PERCENT_MEND:
            body_tokens.append(ctx.tokens[pos].value)
            pos += 1

        # Skip %MEND
        if pos < len(ctx.tokens):
            pos += 1

        # Skip optional macro name after %MEND
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
            pos += 1

        # Skip semicolon
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
            pos += 1

        body = " ".join(body_tokens)

        return MacroDefStatement(name=name, parameters=parameters, body=body), pos

    def _parse_parameters(
        self, ctx: ParseContext, pos: int
    ) -> tuple[list[MacroParameter], int]:
        """Parse macro parameters."""
        params: list[MacroParameter] = []

        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.RPAREN:
            param_name = ""
            default_value: str | None = None

            if ctx.tokens[pos].type == TokenType.IDENTIFIER:
                param_name = ctx.tokens[pos].value
                pos += 1

                # Check for default value
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                    pos += 1
                    # Collect default value until , or )
                    value_parts: list[str] = []
                    while pos < len(ctx.tokens) and ctx.tokens[pos].type not in {
                        TokenType.COMMA,
                        TokenType.RPAREN,
                    }:
                        value_parts.append(ctx.tokens[pos].value)
                        pos += 1
                    default_value = " ".join(value_parts) if value_parts else None

                params.append(MacroParameter(name=param_name, default_value=default_value))

            # Skip comma
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.COMMA:
                pos += 1
            elif ctx.tokens[pos].type == TokenType.RPAREN:
                break
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip )

        return params, pos


@register
class MacroCallHandler(BaseHandler):
    """Handler for macro invocations (%macroname or %macroname(...))."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.MACRO_CALL}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return tokens[pos].type == TokenType.MACRO_CALL

    def parse(self, ctx: ParseContext) -> tuple[MacroCallStatement, int]:
        """Parse %macroname or %macroname(args)."""
        pos = ctx.pos
        # Macro call value includes the % prefix, strip it
        name = ctx.tokens[pos].value
        if name.startswith("%"):
            name = name[1:]
        pos += 1

        arguments: list[tuple[str | None, str]] = []

        # Check for arguments
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.LPAREN:
            pos += 1
            arguments, pos = self._parse_arguments(ctx, pos)

        return MacroCallStatement(name=name, arguments=arguments), pos

    def _parse_arguments(
        self, ctx: ParseContext, pos: int
    ) -> tuple[list[tuple[str | None, str]], int]:
        """Parse macro call arguments."""
        args: list[tuple[str | None, str]] = []

        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.RPAREN:
            arg_name: str | None = None
            arg_value_parts: list[str] = []

            # Check if this is a named argument (name=value)
            if (
                pos + 1 < len(ctx.tokens)
                and ctx.tokens[pos].type == TokenType.IDENTIFIER
                and ctx.tokens[pos + 1].type == TokenType.EQUALS
            ):
                arg_name = ctx.tokens[pos].value
                pos += 2  # Skip name and =

            # Collect value until , or )
            paren_depth = 0
            while pos < len(ctx.tokens):
                tok = ctx.tokens[pos]
                if tok.type == TokenType.LPAREN:
                    paren_depth += 1
                    arg_value_parts.append(tok.value)
                    pos += 1
                elif tok.type == TokenType.RPAREN:
                    if paren_depth == 0:
                        break
                    paren_depth -= 1
                    arg_value_parts.append(tok.value)
                    pos += 1
                elif tok.type == TokenType.COMMA and paren_depth == 0:
                    pos += 1
                    break
                else:
                    arg_value_parts.append(tok.value)
                    pos += 1

            arg_value = " ".join(arg_value_parts).strip()
            if arg_value or arg_name:
                args.append((arg_name, arg_value))

        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.RPAREN:
            pos += 1  # Skip )

        return args, pos
