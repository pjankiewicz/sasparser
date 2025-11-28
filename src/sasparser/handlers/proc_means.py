"""PROC MEANS/SUMMARY handler."""

from __future__ import annotations
from . import register
from .base import BaseHandler, ParseContext
from ..core.tokens import Token, TokenType
from ..ast.base import FieldReference
from ..ast.data_step import ByField
from ..ast.proc_other import ProcMeans


@register
class ProcMeansHandler(BaseHandler):
    """Handler for PROC MEANS/SUMMARY."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.PROC}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return (
            pos + 1 < len(tokens)
            and tokens[pos].type == TokenType.PROC
            and tokens[pos + 1].type in {TokenType.MEANS, TokenType.SUMMARY}
        )

    def parse(self, ctx: ParseContext) -> tuple[ProcMeans, int]:
        """Parse PROC MEANS/SUMMARY."""
        pos = ctx.pos + 1  # Skip PROC
        is_summary = ctx.tokens[pos].type == TokenType.SUMMARY
        pos += 1  # Skip MEANS/SUMMARY

        input_table = None
        output_table = None
        statistics: list[str] = []
        var_fields: list[FieldReference] = []
        class_fields: list[FieldReference] = []
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
            elif tok.type == TokenType.IDENTIFIER:
                # Could be a statistic keyword
                stat = tok.value.upper()
                if stat in {"N", "MEAN", "STD", "MIN", "MAX", "SUM", "MEDIAN", "NMISS"}:
                    statistics.append(stat)
                pos += 1
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        # Parse body statements until RUN
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.RUN:
            tok = ctx.tokens[pos]
            if tok.type == TokenType.VAR:
                pos += 1
                fields, pos = self._parse_field_list_until_semicolon(ctx, pos)
                var_fields.extend(fields)
            elif tok.type == TokenType.CLASS:
                pos += 1
                fields, pos = self._parse_field_list_until_semicolon(ctx, pos)
                class_fields.extend(fields)
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
            elif tok.type == TokenType.OUTPUT:
                pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.OUT:
                    pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                    pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
                    new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                    output_table, pos = self._parse_table_ref(new_ctx)
                # Skip to semicolon
                while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
                    pos += 1
                if pos < len(ctx.tokens):
                    pos += 1
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

        return ProcMeans(
            input_table=input_table,
            output_table=output_table,
            var_fields=var_fields,
            class_fields=class_fields,
            by_fields=by_fields,
            statistics=statistics,
            is_summary=is_summary,
        ), pos

    def _parse_field_list_until_semicolon(
        self, ctx: ParseContext, pos: int
    ) -> tuple[list[FieldReference], int]:
        """Parse fields until semicolon."""
        fields: list[FieldReference] = []
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            if ctx.tokens[pos].type == TokenType.IDENTIFIER:
                fields.append(FieldReference(name=ctx.tokens[pos].value))
            pos += 1
        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon
        return fields, pos
