"""PROC FREQ handler."""

from __future__ import annotations
from . import register
from .base import BaseHandler, ParseContext
from ..core.tokens import Token, TokenType
from ..ast.base import FieldReference
from ..ast.data_step import ByField
from ..ast.proc_other import ProcFreq, TableSpec


@register
class ProcFreqHandler(BaseHandler):
    """Handler for PROC FREQ."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.PROC}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return (
            pos + 1 < len(tokens)
            and tokens[pos].type == TokenType.PROC
            and tokens[pos + 1].type == TokenType.FREQ
        )

    def parse(self, ctx: ParseContext) -> tuple[ProcFreq, int]:
        """Parse PROC FREQ."""
        pos = ctx.pos + 2  # Skip PROC FREQ

        input_table = None
        output_table = None
        tables: list[TableSpec] = []
        by_fields: list[ByField] = []

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
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        # Parse body statements until RUN
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.RUN:
            tok = ctx.tokens[pos]
            if tok.type == TokenType.TABLES:
                pos += 1
                table_spec, pos = self._parse_tables_spec(ctx, pos)
                if table_spec:
                    tables.append(table_spec)
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

        return ProcFreq(
            input_table=input_table,
            output_table=output_table,
            tables=tables,
            by_fields=by_fields,
        ), pos

    def _parse_tables_spec(
        self, ctx: ParseContext, pos: int
    ) -> tuple[TableSpec | None, int]:
        """Parse TABLES specification (field*field)."""
        fields: list[FieldReference] = []

        while pos < len(ctx.tokens):
            tok = ctx.tokens[pos]
            if tok.type == TokenType.SEMICOLON:
                pos += 1
                break
            if tok.type == TokenType.SLASH:
                # Skip table options
                while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
                    pos += 1
                if pos < len(ctx.tokens):
                    pos += 1
                break
            if tok.type == TokenType.IDENTIFIER:
                fields.append(FieldReference(name=tok.value))
                pos += 1
            elif tok.type == TokenType.STAR:
                pos += 1
            else:
                pos += 1

        if fields:
            return TableSpec(fields=fields), pos
        return None, pos
