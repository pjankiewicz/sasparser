"""PROC SORT handler."""

from __future__ import annotations
from . import register
from .base import BaseHandler, ParseContext
from ..core.tokens import Token, TokenType
from ..ast.base import FieldReference
from ..ast.data_step import ByField
from ..ast.proc_other import ProcSort


@register
class ProcSortHandler(BaseHandler):
    """Handler for PROC SORT."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.PROC}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return (
            pos + 1 < len(tokens)
            and tokens[pos].type == TokenType.PROC
            and tokens[pos + 1].type == TokenType.SORT
        )

    def parse(self, ctx: ParseContext) -> tuple[ProcSort, int]:
        """Parse PROC SORT."""
        pos = ctx.pos + 2  # Skip PROC SORT

        input_table = None
        output_table = None
        nodupkey = False
        noduprec = False
        options: dict[str, str] = {}

        # Parse options until semicolon
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            tok = ctx.tokens[pos]
            if tok.type == TokenType.DATA:
                pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                    pos += 1
                if pos < len(ctx.tokens) and self._is_identifier_like(ctx.tokens[pos]):
                    new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                    input_table, pos = self._parse_table_ref(new_ctx)
            elif tok.type == TokenType.OUT:
                pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                    pos += 1
                if pos < len(ctx.tokens) and self._is_identifier_like(ctx.tokens[pos]):
                    new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                    output_table, pos = self._parse_table_ref(new_ctx)
            elif tok.type == TokenType.NODUPKEY:
                nodupkey = True
                pos += 1
            elif tok.type == TokenType.NODUPREC:
                noduprec = True
                pos += 1
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        # Parse BY statement
        by_fields: list[ByField] = []
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.BY:
            pos += 1
            while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
                descending = False
                if ctx.tokens[pos].type == TokenType.DESCENDING:
                    descending = True
                    pos += 1
                if pos < len(ctx.tokens) and self._is_identifier_like(ctx.tokens[pos]):
                    field = FieldReference(name=ctx.tokens[pos].value)
                    by_fields.append(ByField(field=field, descending=descending))
                    pos += 1
                else:
                    pos += 1
            if pos < len(ctx.tokens):
                pos += 1  # Skip semicolon

        # Skip to RUN;
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.RUN:
            pos += 1
        if pos < len(ctx.tokens):
            pos += 1  # Skip RUN
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
                pos += 1

        return ProcSort(
            input_table=input_table,
            output_table=output_table,
            by_fields=by_fields,
            nodupkey=nodupkey,
            noduprec=noduprec,
            options=options,
        ), pos
