"""DATA step handler."""

from __future__ import annotations
from . import register
from .base import BaseHandler, ParseContext
from ..core.tokens import Token, TokenType
from ..ast.base import TableReference, FieldReference, DatasetOptions
from ..ast.data_step import (
    DataStep, SetStatement, MergeStatement, ByStatement, ByField,
    WhereStatement, IfStatement, AssignmentStatement, KeepStatement,
    DropStatement, OutputStatement, DataStepStatement,
)
from ..ast.expressions import Expression, FieldExpression, Literal, BinaryExpression


@register
class DataStepHandler(BaseHandler):
    """Handler for DATA step parsing."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.DATA}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return pos < len(tokens) and tokens[pos].type == TokenType.DATA

    def parse(self, ctx: ParseContext) -> tuple[DataStep, int]:
        """Parse a DATA step."""
        pos = ctx.pos + 1  # Skip DATA keyword

        # Parse output table(s)
        output_tables: list[TableReference] = []
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            if self._is_identifier_like(ctx.tokens[pos]):
                new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                table, pos = self._parse_table_ref(new_ctx)
                output_tables.append(table)
            elif ctx.tokens[pos].type == TokenType.COMMA:
                pos += 1
            elif ctx.tokens[pos].type == TokenType.LPAREN:
                # Skip dataset options
                pos = self._skip_dataset_options(ctx.tokens, pos)
            else:
                pos += 1

        # Skip semicolon
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
            pos += 1

        # Parse body statements
        statements: list[DataStepStatement] = []
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.RUN:
            new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
            stmt, pos = self._parse_data_statement(new_ctx)
            if stmt:
                statements.append(stmt)

        # Skip RUN;
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.RUN:
            pos += 1
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
                pos += 1

        return DataStep(output_tables=output_tables, statements=statements), pos

    def _skip_dataset_options(self, tokens: list[Token], pos: int) -> int:
        """Skip dataset options in parentheses."""
        if tokens[pos].type != TokenType.LPAREN:
            return pos
        depth = 1
        pos += 1
        while pos < len(tokens) and depth > 0:
            if tokens[pos].type == TokenType.LPAREN:
                depth += 1
            elif tokens[pos].type == TokenType.RPAREN:
                depth -= 1
            pos += 1
        return pos

    def _parse_data_statement(
        self, ctx: ParseContext
    ) -> tuple[DataStepStatement | None, int]:
        """Parse a single DATA step statement."""
        token = ctx.tokens[ctx.pos]

        if token.type == TokenType.SET:
            return self._parse_set(ctx)
        elif token.type == TokenType.MERGE:
            return self._parse_merge(ctx)
        elif token.type == TokenType.BY:
            return self._parse_by(ctx)
        elif token.type == TokenType.WHERE:
            return self._parse_where(ctx)
        elif token.type == TokenType.IF:
            return self._parse_if(ctx)
        elif token.type == TokenType.KEEP:
            return self._parse_keep(ctx)
        elif token.type == TokenType.DROP_KW:
            return self._parse_drop(ctx)
        elif token.type == TokenType.OUTPUT:
            return self._parse_output(ctx)
        elif token.type == TokenType.IDENTIFIER:
            # Check for assignment (field = expr)
            if ctx.pos + 1 < len(ctx.tokens):
                next_tok = ctx.tokens[ctx.pos + 1]
                if next_tok.type == TokenType.EQUALS:
                    return self._parse_assignment(ctx)
            # Skip to semicolon
            return self._skip_statement(ctx)
        else:
            return self._skip_statement(ctx)

    def _skip_statement(
        self, ctx: ParseContext
    ) -> tuple[DataStepStatement | None, int]:
        """Skip to next semicolon."""
        pos = ctx.pos
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            pos += 1
        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon
        return None, pos

    def _parse_set(self, ctx: ParseContext) -> tuple[SetStatement, int]:
        """Parse SET statement."""
        pos = ctx.pos + 1  # Skip SET
        tables: list[TableReference] = []

        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            if self._is_identifier_like(ctx.tokens[pos]):
                new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                table, pos = self._parse_table_ref(new_ctx)
                tables.append(table)
            elif ctx.tokens[pos].type == TokenType.LPAREN:
                pos = self._skip_dataset_options(ctx.tokens, pos)
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        return SetStatement(tables=tables), pos

    def _parse_merge(self, ctx: ParseContext) -> tuple[MergeStatement, int]:
        """Parse MERGE statement."""
        pos = ctx.pos + 1  # Skip MERGE
        tables: list[TableReference] = []

        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            if self._is_identifier_like(ctx.tokens[pos]):
                new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                table, pos = self._parse_table_ref(new_ctx)
                tables.append(table)
            elif ctx.tokens[pos].type == TokenType.LPAREN:
                pos = self._skip_dataset_options(ctx.tokens, pos)
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        return MergeStatement(tables=tables), pos

    def _parse_by(self, ctx: ParseContext) -> tuple[ByStatement, int]:
        """Parse BY statement."""
        pos = ctx.pos + 1  # Skip BY
        fields: list[ByField] = []

        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            descending = False
            if ctx.tokens[pos].type == TokenType.DESCENDING:
                descending = True
                pos += 1
            if pos < len(ctx.tokens) and self._is_identifier_like(ctx.tokens[pos]):
                new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                field_ref, pos = self._parse_field_ref(new_ctx)
                fields.append(ByField(field=field_ref, descending=descending))
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        return ByStatement(fields=fields), pos

    def _parse_where(self, ctx: ParseContext) -> tuple[WhereStatement, int]:
        """Parse WHERE statement."""
        pos = ctx.pos + 1  # Skip WHERE
        expr, pos = self._parse_expression_until(ctx.tokens, pos, {TokenType.SEMICOLON})
        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon
        return WhereStatement(condition=expr), pos

    def _parse_if(self, ctx: ParseContext) -> tuple[IfStatement, int]:
        """Parse IF statement."""
        pos = ctx.pos + 1  # Skip IF

        # Parse condition until THEN
        condition, pos = self._parse_expression_until(
            ctx.tokens, pos, {TokenType.THEN}
        )
        if pos < len(ctx.tokens):
            pos += 1  # Skip THEN

        # Parse then statements
        then_stmts: list[DataStepStatement] = []
        while pos < len(ctx.tokens):
            tok = ctx.tokens[pos]
            if tok.type in {TokenType.ELSE, TokenType.RUN}:
                break
            if tok.type == TokenType.SEMICOLON:
                pos += 1
                break
            new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
            stmt, pos = self._parse_data_statement(new_ctx)
            if stmt:
                then_stmts.append(stmt)
                break  # Simple IF handles single statement

        # Check for ELSE
        else_stmts: list[DataStepStatement] | None = None
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.ELSE:
            pos += 1
            else_stmts = []
            new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
            stmt, pos = self._parse_data_statement(new_ctx)
            if stmt:
                else_stmts.append(stmt)

        return IfStatement(
            condition=condition, then_statements=then_stmts, else_statements=else_stmts
        ), pos

    def _parse_keep(self, ctx: ParseContext) -> tuple[KeepStatement, int]:
        """Parse KEEP statement."""
        pos = ctx.pos + 1  # Skip KEEP
        new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
        fields, pos = self._parse_field_list(new_ctx, {TokenType.SEMICOLON})
        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon
        return KeepStatement(fields=fields), pos

    def _parse_drop(self, ctx: ParseContext) -> tuple[DropStatement, int]:
        """Parse DROP statement."""
        pos = ctx.pos + 1  # Skip DROP
        new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
        fields, pos = self._parse_field_list(new_ctx, {TokenType.SEMICOLON})
        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon
        return DropStatement(fields=fields), pos

    def _parse_output(self, ctx: ParseContext) -> tuple[OutputStatement, int]:
        """Parse OUTPUT statement."""
        pos = ctx.pos + 1  # Skip OUTPUT
        dataset: TableReference | None = None

        if pos < len(ctx.tokens) and self._is_identifier_like(ctx.tokens[pos]):
            new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
            dataset, pos = self._parse_table_ref(new_ctx)

        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
            pos += 1

        return OutputStatement(dataset=dataset), pos

    def _parse_assignment(self, ctx: ParseContext) -> tuple[AssignmentStatement, int]:
        """Parse assignment statement (field = expr)."""
        new_ctx = ParseContext(ctx.tokens, ctx.pos, ctx.macro_vars, ctx.libraries)
        target, pos = self._parse_field_ref(new_ctx)
        pos += 1  # Skip =
        expr, pos = self._parse_expression_until(ctx.tokens, pos, {TokenType.SEMICOLON})
        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon
        return AssignmentStatement(target=target, expression=expr), pos

    def _parse_expression_until(
        self, tokens: list[Token], pos: int, stop: set[TokenType]
    ) -> tuple[Expression, int]:
        """Parse expression until stop token (simplified)."""
        expr_tokens: list[Token] = []
        while pos < len(tokens) and tokens[pos].type not in stop:
            expr_tokens.append(tokens[pos])
            pos += 1

        # Build simple expression from tokens
        if not expr_tokens:
            return Literal(value="", literal_type="string"), pos

        # Simple case: single field or literal
        if len(expr_tokens) == 1:
            tok = expr_tokens[0]
            if tok.type == TokenType.IDENTIFIER:
                return FieldExpression(field=FieldReference(name=tok.value)), pos
            elif tok.type == TokenType.NUMBER:
                return Literal(value=tok.value, literal_type="number"), pos
            elif tok.type == TokenType.STRING:
                return Literal(value=tok.value, literal_type="string"), pos

        # Build compound expression (simplified)
        return self._build_expression(expr_tokens), pos

    def _build_expression(self, tokens: list[Token]) -> Expression:
        """Build expression from tokens (simplified parser)."""
        # This is a simplified expression builder
        # For now, just extract field references
        fields: list[FieldReference] = []
        for tok in tokens:
            if tok.type == TokenType.IDENTIFIER:
                fields.append(FieldReference(name=tok.value))

        if len(fields) == 1:
            return FieldExpression(field=fields[0])

        # Return a placeholder binary expression
        if len(fields) >= 2:
            left = FieldExpression(field=fields[0])
            right = FieldExpression(field=fields[1])
            return BinaryExpression(left=left, operator="?", right=right)

        return Literal(value="<expression>", literal_type="string")
