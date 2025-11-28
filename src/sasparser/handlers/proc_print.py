"""PROC PRINT handler."""

from __future__ import annotations
from . import register
from .base import BaseHandler, ParseContext
from ..core.tokens import Token, TokenType
from ..ast.base import FieldReference
from ..ast.data_step import ByField
from ..ast.proc_other import ProcPrint


@register
class ProcPrintHandler(BaseHandler):
    """Handler for PROC PRINT."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.PROC}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return (
            pos + 1 < len(tokens)
            and tokens[pos].type == TokenType.PROC
            and tokens[pos + 1].type == TokenType.PRINT
        )

    def parse(self, ctx: ParseContext) -> tuple[ProcPrint, int]:
        """Parse PROC PRINT."""
        pos = ctx.pos + 2  # Skip PROC PRINT

        input_table = None
        var_fields: list[FieldReference] = []
        by_fields: list[ByField] = []
        obs: int | None = None

        # Parse options until semicolon
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            tok = ctx.tokens[pos]
            if tok.type == TokenType.DATA:
                pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                    pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
                    new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                    input_table, pos = self._parse_table_ref(new_ctx)
            elif tok.type == TokenType.LPAREN:
                # Parse options like (OBS=10)
                pos += 1
                while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.RPAREN:
                    if ctx.tokens[pos].type == TokenType.OBS:
                        pos += 1
                        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                            pos += 1
                        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.NUMBER:
                            try:
                                obs = int(ctx.tokens[pos].value)
                            except ValueError:
                                pass
                            pos += 1
                    else:
                        pos += 1
                if pos < len(ctx.tokens):
                    pos += 1  # Skip )
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        # Parse body statements until RUN
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.RUN:
            tok = ctx.tokens[pos]
            if tok.type == TokenType.VAR:
                pos += 1
                while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
                    if ctx.tokens[pos].type == TokenType.IDENTIFIER:
                        var_fields.append(FieldReference(name=ctx.tokens[pos].value))
                    pos += 1
                if pos < len(ctx.tokens):
                    pos += 1  # Skip semicolon
            elif tok.type == TokenType.BY:
                pos += 1
                while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
                    descending = False
                    if ctx.tokens[pos].type == TokenType.DESCENDING:
                        descending = True
                        pos += 1
                    if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
                        field = FieldReference(name=ctx.tokens[pos].value)
                        by_fields.append(ByField(field=field, descending=descending))
                        pos += 1
                    else:
                        pos += 1
                if pos < len(ctx.tokens):
                    pos += 1  # Skip semicolon
            else:
                # Skip to semicolon
                while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
                    pos += 1
                if pos < len(ctx.tokens):
                    pos += 1

        # Skip RUN;
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.RUN:
            pos += 1
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
                pos += 1

        return ProcPrint(
            input_table=input_table,
            var_fields=var_fields,
            by_fields=by_fields,
            obs=obs,
        ), pos
